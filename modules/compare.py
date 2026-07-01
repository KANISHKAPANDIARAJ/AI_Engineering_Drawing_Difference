from typing import Tuple, List, Dict, Any
import cv2
import numpy as np

from skimage.metrics import structural_similarity as ssim
from utils.logger import get_logger


class ImageComparator:
    def __init__(self):
        self.logger = get_logger(__name__)

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

            return score, diff

        except Exception as e:
            self.logger.error(f"SSIM computation failed: {e}")
            raise

    # -------------------------
    # Thresholding
    # -------------------------
    def threshold_diff(self, diff: np.ndarray):
        try:
            self.logger.info("Applying thresholding")

            _, thresh = cv2.threshold(
                diff,
                0,
                255,
                cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU
            )

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

            kernel = np.ones((5, 5), np.uint8)

            cleaned = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)
            cleaned = cv2.morphologyEx(cleaned, cv2.MORPH_OPEN, kernel, iterations=1)

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

            boxes = []

            for cnt in contours:
                x, y, w, h = cv2.boundingRect(cnt)

                if w < 5 or h < 5:
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

            return {
                "diff_pixel_count": total_diff_pixels,
                "num_regions": num_regions,
                "average_region_area": float(avg_area),
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
            score, diff = self.compute_ssim(img1, img2)

            # 2. Threshold
            thresh = self.threshold_diff(diff)

            # 3. Morphology
            cleaned = self.morph_cleanup(thresh)

            # 4. Contours
            boxes = self.extract_contours(cleaned)

            # 5. Statistics
            stats = self.compute_statistics(cleaned, boxes)
            stats["ssim_score"] = float(score)

            self.logger.info(
                f"Comparison done | SSIM={score:.4f} | Regions={len(boxes)}"
            )

            return cleaned, boxes, stats

        except Exception as e:
            self.logger.error(f"Comparison pipeline failed: {e}")
            raise