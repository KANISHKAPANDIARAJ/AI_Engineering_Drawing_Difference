from typing import Tuple, List, Dict, Any
import cv2
import numpy as np

from skimage.metrics import structural_similarity as ssim
from config import ProjectConfig
from utils.logger import get_logger


class ImageComparator:
    def __init__(self):
        self.logger = get_logger(__name__)

    # -------------------------
    # Utility: ensure uint8 0-255
    # -------------------------
    def _to_uint8(self, image: np.ndarray) -> np.ndarray:
        if image.dtype != np.uint8:
            return (image * 255).clip(0, 255).astype(np.uint8)
        return image

    # -------------------------
    # SSIM + difference map (FIXED)
    # -------------------------
    def compute_ssim(self, img1: np.ndarray, img2: np.ndarray):
        try:
            self.logger.info("Computing SSIM")

            if len(img1.shape) == 3:
                gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
                gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)
            else:
                gray1 = img1
                gray2 = img2

            # -----------------------------
            # FIX: handle float vs uint8 images
            # -----------------------------
            if gray1.dtype in [np.float32, np.float64]:
                data_range = 1.0
            else:
                data_range = 255

            score, diff = ssim(
                gray1,
                gray2,
                full=True,
                data_range=data_range
            )

            # Safe scaling of diff map
            diff = np.clip(diff * 255, 0, 255).astype(np.uint8)

            # uint8 grayscale copies, reused later for Added/Removed/
            # Modified classification (ink-density comparison per region).
            gray1_u8 = self._to_uint8(gray1)
            gray2_u8 = self._to_uint8(gray2)

            return score, diff, gray1_u8, gray2_u8

        except Exception as e:
            self.logger.error(f"SSIM computation failed: {e}")
            raise

    # -------------------------
    # Thresholding
    # -------------------------
    def threshold_diff(self, diff: np.ndarray):
        try:
            self.logger.info("Applying thresholding")

            # Otsu picks a statistically "optimal" split point, but on
            # documents that are 95%+ identical it can end up very
            # permissive and flag minor anti-aliasing / PDF rendering
            # noise as "changed" pixels. We combine Otsu with a fixed
            # floor (MIN_DIFF_INTENSITY) so a pixel only counts as
            # changed if it's BOTH a statistical outlier AND genuinely
            # dissimilar in magnitude.
            _, otsu_mask = cv2.threshold(
                diff,
                0,
                255,
                cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU
            )

            _, floor_mask = cv2.threshold(
                diff,
                ProjectConfig.MIN_DIFF_INTENSITY,
                255,
                cv2.THRESH_BINARY_INV
            )

            thresh = cv2.bitwise_and(otsu_mask, floor_mask)

            return thresh

        except Exception as e:
            self.logger.error(f"Thresholding failed: {e}")
            raise

    # -------------------------
    # Morphological operations
    # -------------------------
    def morph_cleanup(self, mask: np.ndarray):
        try:
            self.logger.info("Applying morphological operations")

            kernel = np.ones(ProjectConfig.MORPH_KERNEL_SIZE, np.uint8)

            # Close first: bridges small gaps so fragments of the SAME
            # real change (e.g. all the edges of one arrow) merge into a
            # single region instead of producing a dozen tiny ones.
            cleaned = cv2.morphologyEx(
                mask, cv2.MORPH_CLOSE, kernel,
                iterations=ProjectConfig.MORPH_ITERATIONS
            )

            # Open second: erases whatever speckle noise is left over
            # (isolated 1-2px anti-aliasing artifacts).
            cleaned = cv2.morphologyEx(
                cleaned, cv2.MORPH_OPEN, kernel,
                iterations=1
            )

            return cleaned

        except Exception as e:
            self.logger.error(f"Morphology failed: {e}")
            raise

    # -------------------------
    # Contours + bounding boxes
    # -------------------------
    def extract_contours(self, mask: np.ndarray):
        try:
            self.logger.info("Extracting contours")

            contours, _ = cv2.findContours(
                mask,
                cv2.RETR_EXTERNAL,
                cv2.CHAIN_APPROX_SIMPLE
            )

            total_area = mask.shape[0] * mask.shape[1]
            max_area = total_area * ProjectConfig.MAX_CONTOUR_AREA_RATIO

            boxes = []

            for cnt in contours:
                x, y, w, h = cv2.boundingRect(cnt)
                area = w * h
                aspect = max(w, h) / max(min(w, h), 1)

                # Drop tiny specks: anti-aliasing, sub-pixel PDF
                # rendering noise, single stray pixels.
                if area < ProjectConfig.MIN_CONTOUR_AREA:
                    continue

                # Drop horizontal or vertical border lines (outer frame/title grids)
                # spanning more than 85% of the drawing sheet's width or height.
                if (w > 0.85 * mask.shape[1] and h < 0.1 * mask.shape[0]) or \
                   (h > 0.85 * mask.shape[0] and w < 0.1 * mask.shape[1]):
                    self.logger.warning(
                        f"Discarding border-like region ({w}x{h}, aspect={aspect:.1f}) "
                        "- likely drawing frame/grid lines, not a real revision"
                    )
                    continue

                # Drop suspiciously huge regions. Real engineering
                # revisions are localized -- a region covering a big
                # chunk of the page is almost always leftover
                # misalignment, not an intentional design change.
                if area > max_area:
                    self.logger.warning(
                        f"Discarding oversized region ({w}x{h}, area={area}) "
                        "- likely a residual alignment artifact, not a "
                        "real difference"
                    )
                    continue

                # Drop very thin, very long slivers -- these are almost
                # always line-thickness variation or a hairline
                # rendering shift, not a real revision. Large slivers
                # (e.g. a genuinely added/removed long line) are still
                # allowed through via the area exemption below.
                if (
                    aspect > ProjectConfig.MAX_CONTOUR_ASPECT_RATIO
                    and area < ProjectConfig.MIN_CONTOUR_AREA * 5
                ):
                    continue

                boxes.append({
                    "x": int(x),
                    "y": int(y),
                    "w": int(w),
                    "h": int(h)
                })

            return boxes

        except Exception as e:
            self.logger.error(f"Contour extraction failed: {e}")
            raise

    # -------------------------
    # Ink density of a crop (fraction of dark / non-blank pixels)
    # -------------------------
    def _ink_ratio(self, crop: np.ndarray) -> float:
        if crop.size == 0:
            return 0.0

        dark_pixels = np.sum(crop < ProjectConfig.INK_PIXEL_THRESHOLD)
        return float(dark_pixels) / crop.size

    # -------------------------
    # Added / Removed / Modified classification
    # -------------------------
    def classify_regions(
        self,
        boxes: List[Dict[str, int]],
        gray1: np.ndarray,
        gray2: np.ndarray,
    ) -> List[Dict[str, Any]]:
        try:
            self.logger.info("Classifying change type per region")

            h, w = gray1.shape[:2]
            empty_floor = ProjectConfig.EMPTY_REGION_INK_RATIO

            for b in boxes:
                x, y, bw, bh = b["x"], b["y"], b["w"], b["h"]

                # Clamp to image bounds -- defensive, boxes should
                # already be in-bounds but crops must never go negative
                # or past the edge.
                x2 = min(x + bw, w)
                y2 = min(y + bh, h)

                crop1 = gray1[y:y2, x:x2]
                crop2 = gray2[y:y2, x:x2]

                ink_before = self._ink_ratio(crop1)
                ink_after = self._ink_ratio(crop2)

                was_empty = ink_before < empty_floor
                is_empty = ink_after < empty_floor

                if was_empty and not is_empty:
                    change_type = "Added"
                elif not was_empty and is_empty:
                    change_type = "Removed"
                else:
                    change_type = "Modified"

                b["change_type"] = change_type
                b["ink_before"] = round(ink_before, 4)
                b["ink_after"] = round(ink_after, 4)

            return boxes

        except Exception as e:
            self.logger.error(f"Region classification failed: {e}")
            raise

    # -------------------------
    # Statistics
    # -------------------------
    def compute_statistics(self, mask: np.ndarray, boxes: List[Dict[str, int]]):
        try:
            self.logger.info("Computing statistics")

            total_diff_pixels = int(np.sum(mask > 0))
            num_regions = len(boxes)

            avg_area = 0.0
            if num_regions > 0:
                avg_area = sum(b["w"] * b["h"] for b in boxes) / num_regions

            change_type_counts = {"Added": 0, "Removed": 0, "Modified": 0}
            for b in boxes:
                ct = b.get("change_type")
                if ct in change_type_counts:
                    change_type_counts[ct] += 1

            return {
                "diff_pixel_count": total_diff_pixels,
                "num_regions": num_regions,
                "average_region_area": float(avg_area),
                "change_type_counts": change_type_counts,
            }

        except Exception as e:
            self.logger.error(f"Statistics computation failed: {e}")
            raise

    # -------------------------
    # Full pipeline
    # -------------------------
    def compare(
        self,
        img1: np.ndarray,
        img2: np.ndarray
    ) -> Tuple[np.ndarray, List[Dict[str, int]], Dict[str, Any]]:

        try:
            self.logger.info("Starting image comparison pipeline")

            # 1. SSIM
            score, diff, gray1_u8, gray2_u8 = self.compute_ssim(img1, img2)

            # 2. Threshold
            thresh = self.threshold_diff(diff)

            # 3. Morphology
            cleaned = self.morph_cleanup(thresh)

            # 4. Contours
            boxes = self.extract_contours(cleaned)

            # 5. Classify each region as Added / Removed / Modified
            boxes = self.classify_regions(boxes, gray1_u8, gray2_u8)

            # 6. Statistics
            stats = self.compute_statistics(cleaned, boxes)
            stats["ssim_score"] = float(score)

            self.logger.info(
                f"Comparison done | SSIM={score:.4f} | Regions={len(boxes)} | "
                f"Breakdown={stats['change_type_counts']}"
            )

            return cleaned, boxes, stats

        except Exception as e:
            self.logger.error(f"Comparison pipeline failed: {e}")
            raise