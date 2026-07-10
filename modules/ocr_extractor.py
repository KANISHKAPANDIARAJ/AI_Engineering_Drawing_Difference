"""
modules/ocr_extractor.py

Extracts text (dimension labels, annotations, callouts) from the "before"
and "after" crop of each changed region, so a report can say what a label
actually changed to/from -- not just that a region changed.

Requires the Tesseract OCR binary to be installed separately from
pytesseract (pip install pytesseract only installs the Python wrapper).
Windows installer: https://github.com/UB-Mannheim/tesseract/wiki
"""

from __future__ import annotations

from typing import List, Dict, Any

import cv2
import numpy as np

try:
    import pytesseract
except ImportError:  # pragma: no cover
    pytesseract = None

from config import ProjectConfig
from utils.logger import get_logger


class OCRExtractor:
    def __init__(self):
        self.logger = get_logger(__name__)

        if pytesseract is None:
            self.logger.warning(
                "pytesseract is not installed (pip install pytesseract). "
                "OCR extraction will be skipped."
            )
        elif getattr(ProjectConfig, "TESSERACT_CMD", None):
            # Only needed on Windows / when tesseract isn't on PATH.
            pytesseract.pytesseract.tesseract_cmd = ProjectConfig.TESSERACT_CMD

    # -------------------------
    # Availability check
    # -------------------------
    def _available(self) -> bool:
        if pytesseract is None:
            return False

        try:
            pytesseract.get_tesseract_version()
            return True
        except Exception as e:
            self.logger.warning(
                f"Tesseract binary not found/callable ({e}). "
                "OCR extraction will be skipped for this run."
            )
            return False

    # -------------------------
    # Crop a region with padding, clipped to image bounds
    # -------------------------
    def _crop(self, image: np.ndarray, box: Dict[str, int]) -> np.ndarray:
        h, w = image.shape[:2]
        pad = ProjectConfig.OCR_PADDING

        x1 = max(box["x"] - pad, 0)
        y1 = max(box["y"] - pad, 0)
        x2 = min(box["x"] + box["w"] + pad, w)
        y2 = min(box["y"] + box["h"] + pad, h)

        return image[y1:y2, x1:x2]

    # -------------------------
    # Preprocess a crop for OCR
    # -------------------------
    def _preprocess(self, crop: np.ndarray) -> np.ndarray:
        if crop.size == 0:
            return crop

        # Convert float images (normalized to 0-1 range) to uint8
        if crop.dtype in [np.float32, np.float64]:
            crop = (crop * 255.0).clip(0, 255).astype(np.uint8)

        if len(crop.shape) == 3:
            crop = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)

        # Dimension labels are usually small in the full drawing --
        # upscale before OCR, Tesseract is unreliable on tiny text.
        factor = ProjectConfig.OCR_UPSCALE_FACTOR
        crop = cv2.resize(
            crop, None, fx=factor, fy=factor, interpolation=cv2.INTER_CUBIC
        )

        # Clean binarization tends to help Tesseract on line-drawing text
        # more than grayscale input.
        crop = cv2.GaussianBlur(crop, (3, 3), 0)
        _, crop = cv2.threshold(
            crop, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
        )

        return crop

    # -------------------------
    # Run Tesseract on one preprocessed crop
    # -------------------------
    def _ocr(self, crop: np.ndarray) -> str:
        if crop.size == 0:
            return ""

        config = (
            f"--psm {ProjectConfig.OCR_PSM_MODE} "
            f"-c tessedit_char_whitelist={ProjectConfig.OCR_CHAR_WHITELIST}"
        )

        try:
            text = pytesseract.image_to_string(crop, config=config)
            return text.strip()
        except Exception as e:
            self.logger.warning(f"OCR failed on a region: {e}")
            return ""

    # -------------------------
    # Map a box to standard grid coordinates
    # -------------------------
    def _map_to_grid(self, box: Dict[str, int], img_w: int, img_h: int) -> str:
        grid_rows = getattr(ProjectConfig, "GRID_ROWS", ["A", "B", "C", "D", "E", "F", "G", "H"])
        grid_cols = getattr(ProjectConfig, "GRID_COLUMNS", ["1", "2", "3", "4", "5", "6", "7", "8"])

        # Center coordinates of the bounding box
        cx = box["x"] + box["w"] / 2.0
        cy = box["y"] + box["h"] / 2.0

        col_width = img_w / len(grid_cols)
        row_height = img_h / len(grid_rows)

        col_idx = int(cx / col_width)
        row_idx = int(cy / row_height)

        # Clamp indexes to valid ranges
        col_idx = max(0, min(col_idx, len(grid_cols) - 1))
        row_idx = max(0, min(row_idx, len(grid_rows) - 1))

        return f"{grid_rows[row_idx]}{grid_cols[col_idx]}"

    # -------------------------
    # Extract before/after text for every region
    # -------------------------
    def extract_all(
        self,
        img1: np.ndarray,
        img2: np.ndarray,
        boxes: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:

        if not boxes:
            return boxes

        # Determine dimensions for grid mapping
        h, w = img1.shape[:2]

        if not self._available():
            for box in boxes:
                box["grid"] = self._map_to_grid(box, w, h)
                box["before_text"] = None
                box["after_text"] = None
                box["text_changed"] = None
            return boxes

        self.logger.info(f"Running OCR on {len(boxes)} region(s)")

        for box in boxes:
            box["grid"] = self._map_to_grid(box, w, h)
            crop1 = self._preprocess(self._crop(img1, box))
            crop2 = self._preprocess(self._crop(img2, box))

            before_text = self._ocr(crop1)
            after_text = self._ocr(crop2)

            box["before_text"] = before_text or None
            box["after_text"] = after_text or None

            # Normalize for comparison: case/whitespace shouldn't count
            # as a "change" on their own.
            norm_before = " ".join(before_text.split()).lower()
            norm_after = " ".join(after_text.split()).lower()
            box["text_changed"] = norm_before != norm_after

        self.logger.info("OCR extraction completed")

        return boxes