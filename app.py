from flask import Flask, request, jsonify, render_template, send_from_directory
import json
from datetime import datetime
from pathlib import Path

from config import ProjectConfig

from utils.file_handler import (
    validate_file,
    save_upload,
    create_folders,
    delete_temporary_files
)

from modules.preprocess import ImagePreprocessor
from modules.compare import ImageComparator
from modules.visualization import ImageVisualizer
from modules.summary import SummaryGenerator
from modules.report_generator import ReportGenerator
from modules.ocr_extractor import OCRExtractor
from modules.llm_analyzer import LLMAnalyzer
from utils.logger import get_logger


# -------------------------
# Initialize Flask
# -------------------------
app = Flask(__name__)
app.config["SECRET_KEY"] = ProjectConfig.SECRET_KEY

logger = get_logger(__name__)

create_folders()


# -------------------------
# Modules
# -------------------------
preprocessor = ImagePreprocessor()
comparator = ImageComparator()
visualizer = ImageVisualizer()
summarizer = SummaryGenerator()
reporter = ReportGenerator()
ocr_extractor = OCRExtractor()
llm_analyzer = LLMAnalyzer()


# -------------------------
# Home
# -------------------------
@app.route("/")
def index():
    return render_template("index.html")


# -------------------------
# Serve outputs
# -------------------------
# This route is the ONLY place in the whole app that understands the
# "/outputs/" URL prefix. Every path returned by /process is relative
# to ProjectConfig.OUTPUTS_DIR (e.g. "highlighted/boxes.png",
# "reports/report.json") and never includes "outputs/" itself.
@app.route("/outputs/<path:filename>")
def serve_outputs(filename):
    # Reports should force a download (Content-Disposition: attachment).
    # Images (highlighted/*) should keep rendering inline in <img> tags.
    as_attachment = filename.startswith("reports/")
    return send_from_directory(
        ProjectConfig.OUTPUTS_DIR,
        filename,
        as_attachment=as_attachment
    )

# -------------------------
# Report page (print-to-PDF)
# -------------------------
TYPE_COLORS = {
    "Added": "#10B981",
    "Removed": "#EF4444",
    "Modified": "#F59E0B",
    "Geometry Change": "#6366F1",
    "Annotation": "#3B82F6",
    "Unknown": "#9CA3AF",
}

@app.route("/report")
def view_report():
    """Render a browser-printable report for the last processed comparison."""
    cache_path = ProjectConfig.OUTPUTS_DIR / "last_result.json"
    if not cache_path.exists():
        return "<h3 style='font-family:sans-serif;padding:40px'>No comparison run yet. Please upload drawings first.</h3>", 404

    try:
        with open(cache_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        return f"<pre>Error reading cached result: {e}</pre>", 500

    summary    = data.get("summary", {})
    regions    = data.get("regions", [])
    llm_report = data.get("llm_report", "")
    viz        = data.get("visualizations", [])

    ssim = float(summary.get("ssim_score", 0))
    sev  = (summary.get("severity") or "UNKNOWN").upper()

    # Attach display color to each region
    for r in regions:
        r["color"] = TYPE_COLORS.get(r.get("change_type", "Unknown"), "#9CA3AF")

    # Find boxes image
    boxes_image = ""
    for f in viz:
        if "boxes" in f:
            boxes_image = "/outputs/" + f
            break

    return render_template(
        "report.html",
        report_id        = datetime.now().strftime("CMP-%Y%m%d-%H%M"),
        generated_date   = datetime.now().strftime("%d %b %Y, %I:%M %p"),
        ssim_score       = round(ssim, 4),
        similarity_pct   = round(ssim * 100, 1),
        total_regions    = summary.get("total_regions", 0),
        severity         = sev.capitalize(),
        severity_class   = "sev-" + sev.lower() if sev.lower() in ("high","medium","low") else "",
        severity_sub     = ("Engineering Validation Required" if sev == "HIGH"
                            else "Review Recommended" if sev == "MEDIUM"
                            else "Minor Changes Detected"),
        percentage_change= summary.get("percentage_change", 0),
        regions          = regions,
        llm_report       = llm_report,
        boxes_image      = boxes_image,
    )


# -------------------------
# Main pipeline
# -------------------------
@app.route("/process", methods=["POST"])
def process_images():

    file1_path = None
    file2_path = None

    try:
        logger.info("Pipeline started")

        # ---------------- VALIDATION ----------------
        if "file1" not in request.files or "file2" not in request.files:
            return jsonify({"error": "Two files required"}), 400

        file1 = request.files["file1"]
        file2 = request.files["file2"]

        if file1.filename == "" or file2.filename == "":
            return jsonify({"error": "Empty filename"}), 400

        # ---------------- SAVE ----------------
        file1_path = save_upload(file1, ProjectConfig.TEMP_UPLOAD_DIR)
        file2_path = save_upload(file2, ProjectConfig.TEMP_UPLOAD_DIR)

        logger.info(f"Saved files: {file1_path}, {file2_path}")

        # ---------------- VALIDATE ----------------
        if not validate_file(file1_path) or not validate_file(file2_path):
            return jsonify({"error": "Invalid file type"}), 400

        # ---------------- PREPROCESS ----------------
        img1, img2 = preprocessor.prepare_images(str(file1_path), str(file2_path))

        # ---------------- COMPARE ----------------
        diff_mask, boxes, stats = comparator.compare(img1, img2)

        # ---------------- OCR ----------------
        boxes = ocr_extractor.extract_all(img1, img2, boxes)

        # ---------------- LLM ANALYSIS ----------------
        llm_report = llm_analyzer.generate_report(stats, boxes)

        # ---------------- SUMMARY ----------------
        summary = summarizer.generate_summary(
            diff_mask,
            boxes,
            stats.get("ssim_score")
        )

        # ---------------- VISUALIZATION ----------------
        viz_paths = visualizer.generate_visualizations(
            img1,
            img2,
            diff_mask,
            boxes
        )

        # Paths relative to ProjectConfig.OUTPUTS_DIR only.
        # Do NOT prefix with "outputs/" here — the /outputs/<path:filename>
        # route already owns that prefix. Prefixing it here is what caused
        # the "/outputs/outputs/..." duplication bug.
        viz_files = [
            f"highlighted/{Path(p).name}"
            for p in viz_paths
        ]

        # ---------------- REPORTS ----------------
        reports = reporter.generate_report(
            str(file1_path),
            str(file2_path),
            summary,
            boxes,
            llm_report=llm_report
        )

        # Same rule: relative to OUTPUTS_DIR, no "outputs/" prefix.
        clean_reports = {
            "txt_report": f"reports/{Path(reports['txt_report']).name}",
            "json_report": f"reports/{Path(reports['json_report']).name}"
        }
        if llm_report:
            clean_reports["md_report"] = "reports/llm_report.md"

        logger.info("Pipeline completed successfully")

        result_payload = {
            "summary": summary,
            "statistics": stats,
            "visualizations": viz_files,
            "reports": clean_reports,
            "llm_report": llm_report,
            "regions": boxes
        }

        # Cache result so the /report page can read it
        try:
            cache_path = ProjectConfig.OUTPUTS_DIR / "last_result.json"
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(result_payload, f, indent=2, default=str)
        except Exception as cache_err:
            logger.warning(f"Could not cache result: {cache_err}")

        return jsonify(result_payload)

    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        return jsonify({"error": str(e)}), 500

    finally:
        try:
            delete_temporary_files()
        except Exception as cleanup_error:
            logger.warning(f"Cleanup failed: {cleanup_error}")


# -------------------------
# Run app
# -------------------------
if __name__ == "__main__":
    logger.info("Starting Flask app")

    app.run(
        host=ProjectConfig.HOST,
        port=ProjectConfig.PORT,
        debug=ProjectConfig.DEBUG
    )