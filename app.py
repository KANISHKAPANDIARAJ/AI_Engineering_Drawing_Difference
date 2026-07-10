from flask import Flask, request, jsonify, render_template, send_from_directory
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

        return jsonify({
            "summary": summary,
            "statistics": stats,
            "visualizations": viz_files,
            "reports": clean_reports,
            "llm_report": llm_report,
            "regions": boxes
        })

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