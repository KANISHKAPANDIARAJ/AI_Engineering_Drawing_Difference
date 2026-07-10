from typing import Dict, List, Any
from pathlib import Path
import json
from datetime import datetime

from utils.logger import get_logger


class ReportGenerator:
    def __init__(self, output_dir: str = "outputs/reports"):
        self.logger = get_logger(__name__)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    # -------------------------
    # Main entry point
    # -------------------------
    def generate_report(
        self,
        file1: str,
        file2: str,
        summary: Dict[str, Any],
        boxes: List[Dict[str, int]],
        llm_report: str = None,
    ) -> Dict[str, str]:

        try:
            self.logger.info("Generating reports (TXT + JSON)")

            timestamp = datetime.utcnow().isoformat()

            report_data = {
                "generated_at": timestamp,
                "file_1": file1,
                "file_2": file2,
                "summary": summary,
                "changed_regions": boxes,
                "llm_report": llm_report
            }

            txt_path = self._generate_txt_report(report_data)
            json_path = self._generate_json_report(report_data)

            if llm_report:
                md_path = self.output_dir / "llm_report.md"
                with open(md_path, "w", encoding="utf-8") as f:
                    f.write(llm_report)
                self.logger.info(f"Saved separate LLM markdown report to {md_path}")

            self.logger.info("Report generation completed")

            return {
                "txt_report": txt_path,
                "json_report": json_path
            }

        except Exception as e:
            self.logger.error(f"Report generation failed: {e}")
            raise

    # -------------------------
    # TXT Report (Human readable)
    # -------------------------
    def _generate_txt_report(self, data: Dict[str, Any]) -> str:

        path = self.output_dir / "report.txt"

        summary = data["summary"]
        boxes = data["changed_regions"]

        lines = []

        lines.append("======================================")
        lines.append("ENGINEERING DRAWING DIFFERENCE REPORT")
        lines.append("======================================\n")

        lines.append(f"Generated At: {data['generated_at']}\n")

        lines.append("INPUT FILES")
        lines.append(f"File 1: {data['file_1']}")
        lines.append(f"File 2: {data['file_2']}\n")

        lines.append("SUMMARY STATISTICS")
        lines.append(f"SSIM Score: {summary.get('ssim_score')}")
        lines.append(f"Total Pixels: {summary.get('total_pixels')}")
        lines.append(f"Changed Pixels: {summary.get('changed_pixels')}")
        lines.append(f"Percentage Change: {summary.get('percentage_change')}%")
        lines.append(f"Total Regions: {summary.get('total_regions')}")
        lines.append(f"Largest Region Area: {summary.get('largest_region_area')}")
        lines.append(f"Smallest Region Area: {summary.get('smallest_region_area')}")
        lines.append(f"Average Region Area: {summary.get('average_region_area')}")
        lines.append(f"Severity: {summary.get('severity')}")

        # Added / Removed / Modified breakdown -- only shown if the
        # summary actually carries it (keeps this backward compatible
        # with older summary dicts that don't have the key).
        counts = summary.get("change_type_counts")
        if counts:
            lines.append(
                f"Change Breakdown: {counts.get('Added', 0)} Added, "
                f"{counts.get('Removed', 0)} Removed, "
                f"{counts.get('Modified', 0)} Modified"
            )

        lines.append("")

        lines.append("FINAL CONCLUSION")
        lines.append(summary.get("conclusion", ""))

        lines.append("\nCHANGED REGIONS (Bounding Boxes)")
        if not boxes:
            lines.append("No significant regions detected.")
        else:
            for i, b in enumerate(boxes, 1):
                change_type = b.get("change_type")
                type_tag = f" [{change_type}]" if change_type else ""
                grid_tag = f" [Grid {b['grid']}]" if "grid" in b else ""

                line = (
                    f"Region {i}{type_tag}{grid_tag}: "
                    f"x={b['x']}, y={b['y']}, w={b['w']}, h={b['h']}"
                )

                # Ink-density readout is a nice sanity check when
                # reviewing why something got classified a certain way,
                # but only include it if present.
                if "ink_before" in b and "ink_after" in b:
                    line += (
                        f" (ink: {b['ink_before']:.3f} -> {b['ink_after']:.3f})"
                    )

                if "before_text" in b or "after_text" in b:
                    before_str = f"'{b['before_text']}'" if b.get("before_text") else "[No text/empty]"
                    after_str = f"'{b['after_text']}'" if b.get("after_text") else "[No text/empty]"
                    line += f" | OCR: {before_str} -> {after_str}"

                lines.append(line)

        if data.get("llm_report"):
            lines.append("\n======================================")
            lines.append("AI-GENERATED ENGINEERING ANALYSIS")
            lines.append("======================================\n")
            lines.append(data["llm_report"])

        lines.append("\n======================================")

        content = "\n".join(lines)

        with open(path, "w", encoding="utf-8") as f:
            f.write(content)

        return str(path)

    # -------------------------
    # JSON Report (Machine readable)
    # -------------------------
    def _generate_json_report(self, data: Dict[str, Any]) -> str:

        path = self.output_dir / "report.json"

        # boxes already carry change_type / ink_before / ink_after
        # (set by ImageComparator.classify_regions), so they flow
        # through into the JSON report with no extra work needed here.
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

        return str(path)