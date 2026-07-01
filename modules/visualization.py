from typing import List, Dict
from pathlib import Path
import cv2
import numpy as np

from config import ProjectConfig
from utils.logger import get_logger


class ImageVisualizer:
    def __init__(self):
        self.logger = get_logger(__name__)

        self.output_dir = Path(ProjectConfig.HIGHLIGHTED_OUTPUT_DIR)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    # -------------------------
    # Utility: ensure uint8
    # -------------------------
    def _to_uint8(self, image: np.ndarray) -> np.ndarray:
        if image.dtype != np.uint8:
            image = (image * 255).clip(0, 255).astype(np.uint8)
        return image

    # -------------------------
    # Draw bounding boxes
    # -------------------------
    def draw_boxes(
        self,
        image: np.ndarray,
        boxes: List[Dict[str, int]],
    ) -> np.ndarray:

        try:
            self.logger.info("Drawing bounding boxes")

            output = image.copy()

            for b in boxes:
                x, y, w, h = b["x"], b["y"], b["w"], b["h"]

                cv2.rectangle(
                    output,
                    (x, y),
                    (x + w, y + h),
                    ProjectConfig.BOUNDING_BOX_COLOR,
                    ProjectConfig.BOUNDING_BOX_THICKNESS,
                )

            return output

        except Exception as e:
            self.logger.error(f"Box drawing failed: {e}")
            raise

    # -------------------------
    # Heatmap generation (FIXED)
    # -------------------------
    def create_heatmap(self, diff_mask: np.ndarray) -> np.ndarray:

        try:
            self.logger.info("Creating heatmap")

            # Ensure grayscale
            if len(diff_mask.shape) == 3:
                diff_mask = cv2.cvtColor(diff_mask, cv2.COLOR_BGR2GRAY)

            # Ensure uint8 range
            if diff_mask.dtype != np.uint8:
                diff_mask = (diff_mask * 255).clip(0, 255).astype(np.uint8)

            heatmap = cv2.applyColorMap(diff_mask, cv2.COLORMAP_JET)

            return heatmap

        except Exception as e:
            self.logger.error(f"Heatmap generation failed: {e}")
            raise

    # -------------------------
    # Overlay differences
    # -------------------------
    def overlay_diff(
        self,
        image: np.ndarray,
        diff_mask: np.ndarray,
    ) -> np.ndarray:

        try:
            self.logger.info("Creating overlay")

            base = image.copy()

            if len(base.shape) == 2:
                base = cv2.cvtColor(base, cv2.COLOR_GRAY2BGR)

            if diff_mask.shape[:2] != base.shape[:2]:
                diff_mask = cv2.resize(diff_mask, (base.shape[1], base.shape[0]))

            heatmap = self.create_heatmap(diff_mask)

            # FIX: ensure both images same dtype
            base = self._to_uint8(base)
            heatmap = self._to_uint8(heatmap)

            overlay = cv2.addWeighted(base, 0.6, heatmap, 0.4, 0)

            return overlay

        except Exception as e:
            self.logger.error(f"Overlay failed: {e}")
            raise

    # -------------------------
    # Side-by-side comparison
    # -------------------------
    def side_by_side(
        self,
        img1: np.ndarray,
        img2: np.ndarray,
    ) -> np.ndarray:

        try:
            self.logger.info("Creating side-by-side comparison")

            h = max(img1.shape[0], img2.shape[0])

            def resize(img):
                if img.shape[0] != h:
                    ratio = h / img.shape[0]
                    w = int(img.shape[1] * ratio)
                    return cv2.resize(img, (w, h))
                return img

            img1 = resize(img1)
            img2 = resize(img2)

            if len(img1.shape) == 2:
                img1 = cv2.cvtColor(img1, cv2.COLOR_GRAY2BGR)
            if len(img2.shape) == 2:
                img2 = cv2.cvtColor(img2, cv2.COLOR_GRAY2BGR)

            return np.hstack((img1, img2))

        except Exception as e:
            self.logger.error(f"Side-by-side creation failed: {e}")
            raise

    # -------------------------
    # Save image safely
    # -------------------------
    def save_image(self, image: np.ndarray, name: str) -> str:

        try:
            path = self.output_dir / name

            image = self._to_uint8(image)

            success = cv2.imwrite(str(path), image)

            if not success:
                raise RuntimeError(f"Failed to save image: {path}")

            self.logger.info(f"Saved image: {path}")

            return str(path)

        except Exception as e:
            self.logger.error(f"Save failed: {e}")
            raise

    # -------------------------
    # Full pipeline
    # -------------------------
    def generate_visualizations(
        self,
        img1: np.ndarray,
        img2: np.ndarray,
        diff_mask: np.ndarray,
        boxes: List[Dict[str, int]],
    ) -> List[str]:

        try:
            self.logger.info("Generating visualizations")

            outputs = []

            # 1. Bounding boxes
            boxed = self.draw_boxes(img1, boxes)
            outputs.append(self.save_image(boxed, "boxes.png"))

            # 2. Heatmap
            heatmap = self.create_heatmap(diff_mask)
            outputs.append(self.save_image(heatmap, "heatmap.png"))

            # 3. Overlay
            overlay = self.overlay_diff(img1, diff_mask)
            outputs.append(self.save_image(overlay, "overlay.png"))

            # 4. Side-by-side
            side = self.side_by_side(img1, img2)
            outputs.append(self.save_image(side, "side_by_side.png"))

            self.logger.info("Visualization pipeline completed successfully")

            return outputs

        except Exception as e:
            self.logger.error(f"Visualization pipeline failed: {e}")
            raise