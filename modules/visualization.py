from typing import List, Dict, Tuple
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
    # Draw a single numbered, color-coded box onto an image (in place)
    # -------------------------
    def _draw_single_box(
        self,
        image: np.ndarray,
        box: Dict[str, int],
        idx: int,
        color: Tuple[int, int, int],
    ) -> None:

        x, y, w, h = box["x"], box["y"], box["w"], box["h"]

        cv2.rectangle(
            image,
            (x, y),
            (x + w, y + h),
            color,
            ProjectConfig.BOUNDING_BOX_THICKNESS,
        )

        label = str(idx)
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.6
        thickness = 2

        (text_w, text_h), baseline = cv2.getTextSize(
            label, font, font_scale, thickness
        )

        tag_y2 = max(y, text_h + baseline + 6)
        tag_y1 = tag_y2 - text_h - baseline - 6

        cv2.rectangle(
            image,
            (x, tag_y1),
            (x + text_w + 10, tag_y2),
            color,
            -1,
        )
        cv2.putText(
            image,
            label,
            (x + 5, tag_y2 - baseline - 3),
            font,
            font_scale,
            (255, 255, 255),
            thickness,
        )

    # -------------------------
    # Before / After annotated pair
    # -------------------------
    def draw_annotated_pair(
        self,
        img1: np.ndarray,
        img2: np.ndarray,
        boxes: List[Dict[str, int]],
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Produces two annotated images -- Before and After -- with the
        same numbered, color-coded boxes so a specific change can be
        cross-referenced directly between the two drawings.

        Which side(s) a box is drawn on depends on its change_type:
          - "Removed"  -> Before only (content existed, then vanished)
          - "Added"    -> After only  (content didn't exist, then appeared)
          - "Modified" -> both sides, same number (content changed but
                          exists in both)
        Boxes without a change_type (e.g. legacy callers) are drawn on
        both sides, matching the old draw_boxes behavior.
        """

        try:
            self.logger.info("Drawing Before/After annotated pair")

            before = self._to_uint8(img1.copy())
            after = self._to_uint8(img2.copy())

            if len(before.shape) == 2:
                before = cv2.cvtColor(before, cv2.COLOR_GRAY2BGR)
            if len(after.shape) == 2:
                after = cv2.cvtColor(after, cv2.COLOR_GRAY2BGR)

            for idx, b in enumerate(boxes, start=1):
                change_type = b.get("change_type")
                color = ProjectConfig.CHANGE_TYPE_COLORS.get(
                    change_type, ProjectConfig.BOUNDING_BOX_COLOR
                )

                draw_before = change_type in ("Removed", "Modified", None)
                draw_after = change_type in ("Added", "Modified", None)

                if draw_before:
                    self._draw_single_box(before, b, idx, color)

                if draw_after:
                    self._draw_single_box(after, b, idx, color)

            return before, after

        except Exception as e:
            self.logger.error(f"Before/After annotation failed: {e}")
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

            # 1 & 2. Before / After annotated pair -- the main output.
            # Same numbered, color-coded boxes on each side so a given
            # change can be cross-referenced between the two drawings.
            before_annotated, after_annotated = self.draw_annotated_pair(
                img1, img2, boxes
            )
            outputs.append(self.save_image(before_annotated, "before_annotated.png"))
            outputs.append(self.save_image(after_annotated, "after_annotated.png"))

            # 3. Heatmap
            heatmap = self.create_heatmap(diff_mask)
            outputs.append(self.save_image(heatmap, "heatmap.png"))

            # 4. Overlay
            overlay = self.overlay_diff(img1, diff_mask)
            outputs.append(self.save_image(overlay, "overlay.png"))

            # 5. Side-by-side (unannotated, quick visual reference)
            side = self.side_by_side(img1, img2)
            outputs.append(self.save_image(side, "side_by_side.png"))

            self.logger.info("Visualization pipeline completed successfully")

            return outputs

        except Exception as e:
            self.logger.error(f"Visualization pipeline failed: {e}")
            raise