from pathlib import Path
from typing import Tuple
import cv2
import numpy as np

from config import ProjectConfig
from utils.file_handler import validate_file
from utils.pdf_utils import pdf_to_image
from utils.logger import get_logger


class ImagePreprocessor:
    def __init__(self):
        self.logger = get_logger(__name__)

    # -------------------------
    # Load single file
    # -------------------------
    def _load_file(self, path: str) -> np.ndarray:
        path = Path(path)

        if not validate_file(path):
            raise ValueError(f"Invalid file: {path}")

        self.logger.info(f"Loading file: {path}")

        if path.suffix.lower() == ".pdf":
            image = pdf_to_image(path)
            image = np.array(image)
        else:
            image = cv2.imread(str(path))
            if image is None:
                raise ValueError(f"Failed to load image: {path}")

        return image

    # -------------------------
    # Load both inputs
    # -------------------------
    def _load_input(self, file1: str, file2: str):
        img1 = self._load_file(file1)
        img2 = self._load_file(file2)

        return img1, img2

    # -------------------------
    # Resize
    # -------------------------
    def resize_images(
        self,
        img1: np.ndarray,
        img2: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray]:

        try:
            self.logger.info("Resizing images")

            size = (
                ProjectConfig.TARGET_IMAGE_WIDTH,
                ProjectConfig.TARGET_IMAGE_HEIGHT
            )

            img1 = cv2.resize(img1, size, interpolation=cv2.INTER_AREA)
            img2 = cv2.resize(img2, size, interpolation=cv2.INTER_AREA)

            return img1, img2

        except Exception as e:
            self.logger.error(f"Resize failed: {e}")
            raise

    # -------------------------
    # Grayscale conversion (config driven)
    # -------------------------
    def _to_grayscale(self, img: np.ndarray) -> np.ndarray:
        if ProjectConfig.ENABLE_GRAYSCALE and len(img.shape) == 3:
            return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        return img

    # -------------------------
    # Noise removal
    # -------------------------
    def remove_noise(
        self,
        img1: np.ndarray,
        img2: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray]:

        try:
            self.logger.info("Applying Gaussian noise reduction")

            ksize = ProjectConfig.GAUSSIAN_KERNEL_SIZE

            img1 = cv2.GaussianBlur(img1, ksize, 0)
            img2 = cv2.GaussianBlur(img2, ksize, 0)

            return img1, img2

        except Exception as e:
            self.logger.error(f"Noise removal failed: {e}")
            raise

    # -------------------------
    # Contrast enhancement
    # -------------------------
    def enhance_contrast(
        self,
        img1: np.ndarray,
        img2: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray]:

        try:
            self.logger.info("Enhancing contrast")

            if ProjectConfig.ENABLE_HISTOGRAM_EQUALIZATION:

                def eq(img):
                    if len(img.shape) == 2:
                        return cv2.equalizeHist(img)

                    ycrcb = cv2.cvtColor(img, cv2.COLOR_BGR2YCrCb)
                    ycrcb[:, :, 0] = cv2.equalizeHist(ycrcb[:, :, 0])
                    return cv2.cvtColor(ycrcb, cv2.COLOR_YCrCb2BGR)

                img1 = eq(img1)
                img2 = eq(img2)

            return img1, img2

        except Exception as e:
            self.logger.error(f"Contrast enhancement failed: {e}")
            raise

    # -------------------------
    # ORB alignment
    # -------------------------
    def _align_images(
        self,
        img1: np.ndarray,
        img2: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray]:

        try:
            self.logger.info("Starting ORB feature alignment")

            img1_gray = self._to_grayscale(img1)
            img2_gray = self._to_grayscale(img2)

            # More features helps on line-drawing content where ORB has
            # fewer strong corners to work with than photos.
            orb = cv2.ORB_create(nfeatures=3000)

            kp1, des1 = orb.detectAndCompute(img1_gray, None)
            kp2, des2 = orb.detectAndCompute(img2_gray, None)

            if des1 is None or des2 is None:
                self.logger.warning("ORB descriptors missing, skipping alignment")
                return img1, img2

            if len(kp1) == 0 or len(kp2) == 0:
                self.logger.warning("No keypoints found, skipping alignment")
                return img1, img2

            bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
            matches = bf.match(des1, des2)

            if len(matches) < 10:
                self.logger.warning("Not enough matches for homography, skipping alignment")
                return img1, img2

            matches = sorted(matches, key=lambda x: x.distance)
            good = matches[: min(80, len(matches))]

            pts1 = np.float32([kp1[m.queryIdx].pt for m in good]).reshape(-1, 1, 2)
            pts2 = np.float32([kp2[m.trainIdx].pt for m in good]).reshape(-1, 1, 2)

            H, inlier_mask = cv2.findHomography(pts2, pts1, cv2.RANSAC, 5.0)

            if H is None or inlier_mask is None:
                self.logger.warning("Homography estimation failed, skipping alignment")
                return img1, img2

            # -----------------------------------------------------------
            # Quality check: on engineering drawings, ORB frequently
            # matches repetitive features (grid lines, hatching, similar
            # corners) which can produce a homography that satisfies
            # RANSAC's threshold on paper but is actually wrong. A low
            # inlier count/ratio is a strong signal of exactly that --
            # in that case it's safer to skip alignment entirely than to
            # apply a bad warp that manufactures fake "differences".
            # -----------------------------------------------------------
            num_inliers = int(inlier_mask.sum())
            inlier_ratio = num_inliers / len(good)

            if (
                num_inliers < ProjectConfig.ALIGNMENT_MIN_INLIERS
                or inlier_ratio < ProjectConfig.ALIGNMENT_MIN_INLIER_RATIO
            ):
                self.logger.warning(
                    f"Homography unreliable (inliers={num_inliers}/{len(good)}, "
                    f"ratio={inlier_ratio:.2f}) - skipping alignment"
                )
                return img1, img2

            h, w = img1.shape[:2]

            # -----------------------------------------------------------
            # Fill any area exposed by the warp with white (matching the
            # drawing's background) instead of the OpenCV default of
            # black. Black fill was the main cause of huge false
            # "difference" regions along the page edges whenever the
            # homography introduced even a slight rotation or shift --
            # white-on-white edges stay similar, black-on-white edges do
            # not.
            # -----------------------------------------------------------
            img2_aligned = cv2.warpPerspective(
                img2,
                H,
                (w, h),
                borderMode=cv2.BORDER_CONSTANT,
                borderValue=(255, 255, 255),
            )

            self.logger.info(
                f"Alignment accepted (inliers={num_inliers}/{len(good)}, "
                f"ratio={inlier_ratio:.2f})"
            )

            return img1, img2_aligned

        except Exception as e:
            self.logger.warning(f"Alignment failed: {e}")
            return img1, img2

    # -------------------------
    # Normalization
    # -------------------------
    def normalize_images(
        self,
        img1: np.ndarray,
        img2: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray]:

        try:
            self.logger.info("Normalizing images")

            img1 = img1.astype(np.float32) / 255.0
            img2 = img2.astype(np.float32) / 255.0

            return img1, img2

        except Exception as e:
            self.logger.error(f"Normalization failed: {e}")
            raise

    # -------------------------
    # Full pipeline
    # -------------------------
    def prepare_images(
        self,
        file1: str,
        file2: str
    ) -> Tuple[np.ndarray, np.ndarray]:

        try:
            self.logger.info(f"Pipeline started: {file1}, {file2}")

            img1, img2 = self._load_input(file1, file2)

            img1, img2 = self.resize_images(img1, img2)
            img1, img2 = self.remove_noise(img1, img2)
            img1, img2 = self.enhance_contrast(img1, img2)

            img1, img2 = self._align_images(img1, img2)

            img1, img2 = self.normalize_images(img1, img2)

            self.logger.info("Pipeline completed successfully")

            return img1, img2

        except Exception as e:
            self.logger.error(f"Pipeline failed: {e}")
            raise