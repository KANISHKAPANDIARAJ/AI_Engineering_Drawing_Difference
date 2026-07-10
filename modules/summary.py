from typing import List, Dict, Any
import numpy as np
from datetime import datetime

from utils.logger import get_logger


class SummaryGenerator:
    def __init__(self):
        self.logger = get_logger(__name__)

    # -------------------------
    # Main summary pipeline
    # -------------------------
    def generate_summary(
        self,
        diff_mask: np.ndarray,
        boxes: List[Dict[str, int]],
        ssim_score: float = None
    ) -> Dict[str, Any]:

        try:
            self.logger.info("Generating engineering drawing summary")

            total_pixels = diff_mask.shape[0] * diff_mask.shape[1]
            changed_pixels = int(np.sum(diff_mask > 0))
            percent_change = (changed_pixels / total_pixels) * 100

            # -------------------------
            # Region statistics
            # -------------------------
            region_stats = self._compute_region_statistics(boxes)

            # -------------------------
            # Severity (rule-based, interpretable)
            # -------------------------
            severity = self._calculate_severity(
                percent_change,
                region_stats["total_regions"],
                ssim_score
            )

            # -------------------------
            # Domain-specific conclusion
            # -------------------------
            conclusion = self._generate_conclusion(
                severity,
                percent_change,
                region_stats,
                ssim_score
            )

            summary = {
                "generated_at": datetime.utcnow().isoformat(),

                "total_pixels": int(total_pixels),
                "changed_pixels": int(changed_pixels),
                "percentage_change": round(percent_change, 2),

                "total_regions": region_stats["total_regions"],
                "largest_region_area": region_stats["largest_region_area"],
                "smallest_region_area": region_stats["smallest_region_area"],
                "average_region_area": region_stats["average_region_area"],
                "total_changed_area": region_stats["total_area"],

                # Added / Removed / Modified breakdown, derived from each
                # region's "change_type" field (set by ImageComparator's
                # ink-density classification). Falls back to all zeros if
                # boxes weren't classified (keeps this backward compatible).
                "change_type_counts": region_stats["change_type_counts"],

                "ssim_score": round(ssim_score, 4) if ssim_score is not None else None,

                "severity": severity,
                "conclusion": conclusion
            }

            self.logger.info("Summary generation completed successfully")

            return summary

        except Exception as e:
            self.logger.error(f"Summary generation failed: {e}")
            raise

    # -------------------------
    # Region statistics
    # -------------------------
    def _compute_region_statistics(self, boxes: List[Dict[str, int]]) -> Dict[str, Any]:

        empty_counts = {"Added": 0, "Removed": 0, "Modified": 0}

        if not boxes:
            return {
                "total_regions": 0,
                "largest_region_area": 0,
                "smallest_region_area": 0,
                "average_region_area": 0,
                "total_area": 0,
                "change_type_counts": empty_counts,
            }

        areas = [b["w"] * b["h"] for b in boxes]

        change_type_counts = dict(empty_counts)
        for b in boxes:
            ct = b.get("change_type")
            if ct in change_type_counts:
                change_type_counts[ct] += 1

        return {
            "total_regions": len(boxes),
            "largest_region_area": int(max(areas)),
            "smallest_region_area": int(min(areas)),
            "average_region_area": float(np.mean(areas)),
            "total_area": int(np.sum(areas)),
            "change_type_counts": change_type_counts,
        }

    # -------------------------
    # Severity logic (interpretable thresholds)
    # -------------------------
    def _calculate_severity(
        self,
        percent_change: float,
        regions: int,
        ssim_score: float
    ) -> str:

        ssim_impact = 0
        if ssim_score is not None:
            ssim_impact = (1 - ssim_score) * 100

        # Clear rule-based classification
        if percent_change < 1 and regions <= 2 and ssim_impact < 2:
            return "LOW"

        elif percent_change < 5 and regions <= 10:
            return "MEDIUM"

        elif percent_change < 15 and regions <= 25:
            return "HIGH"

        else:
            return "CRITICAL"

    # -------------------------
    # Engineering-style explanation
    # -------------------------
    def _generate_conclusion(
        self,
        severity: str,
        percent_change: float,
        region_stats: Dict[str, Any],
        ssim_score: float
    ) -> str:

        regions = region_stats["total_regions"]
        counts = region_stats.get("change_type_counts", {})

        base = (
            f"{regions} revision region(s) detected. "
            f"Approximately {percent_change:.2f}% of the drawing differs from the reference. "
        )

        if ssim_score is not None:
            base += f"SSIM similarity score is {ssim_score:.4f}. "

        # Only mention the breakdown if at least one region was actually
        # classified -- keeps the sentence out of older-style calls where
        # boxes don't carry a change_type.
        if any(counts.values()):
            base += (
                f"Breakdown: {counts.get('Added', 0)} added, "
                f"{counts.get('Removed', 0)} removed, "
                f"{counts.get('Modified', 0)} modified. "
            )

        if severity == "LOW":
            return base + (
                "These changes are minor and likely represent non-critical annotations or small adjustments."
            )

        elif severity == "MEDIUM":
            return base + (
                "Moderate engineering revisions detected. Review is recommended for affected components."
            )

        elif severity == "HIGH":
            return base + (
                "Significant structural or annotation changes detected. Engineering validation required."
            )

        else:
            return base + (
                "Critical modifications detected. Major design revisions present and require immediate review."
            )