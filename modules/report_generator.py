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
    ) -> Dict[str, str]:

        try:
            self.logger.info("Generating reports (TXT + JSON)")

            timestamp = datetime.utcnow().isoformat()

            report_data = {
                "generated_at": timestamp,
                "file_1": file1,
                "file_2": file2,
                "summary": summary,
                "changed_regions": boxes
            }

            txt_path = self._generate_txt_report(report_data)
            json_path = self._generate_json_report(report_data)

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
        lines.append(f"Severity: {summary.get('severity')}\n")

        lines.append("FINAL CONCLUSION")
        lines.append(summary.get("conclusion", ""))

        lines.append("\nCHANGED REGIONS (Bounding Boxes)")
        if not boxes:
            lines.append("No significant regions detected.")
        else:
            for i, b in enumerate(boxes, 1):
                lines.append(
                    f"Region {i}: x={b['x']}, y={b['y']}, w={b['w']}, h={b['h']}"
                )

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

        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

        return str(path)