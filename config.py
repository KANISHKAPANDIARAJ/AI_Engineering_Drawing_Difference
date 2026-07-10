"""
config.py

Central configuration for the AI-Based Engineering Drawing Difference Detection,
Visualization, and Automated Change Summarization project.
"""

from __future__ import annotations

from pathlib import Path
from typing import Final


class ProjectConfig:
    """Central configuration for application paths and processing settings."""

    # ------------------------------------------------------------------
    # Base Directory
    # ------------------------------------------------------------------
    BASE_DIR: Final[Path] = Path(__file__).resolve().parent

    # ------------------------------------------------------------------
    # Upload Directories
    # ------------------------------------------------------------------
    UPLOADS_DIR: Final[Path] = BASE_DIR / "uploads"

    PDF_UPLOAD_DIR: Final[Path] = UPLOADS_DIR / "pdf"
    IMAGE_UPLOAD_DIR: Final[Path] = UPLOADS_DIR / "images"
    CAD_UPLOAD_DIR: Final[Path] = UPLOADS_DIR / "cad"
    TEMP_UPLOAD_DIR: Final[Path] = UPLOADS_DIR / "temp"

    # ------------------------------------------------------------------
    # Output Directories
    # ------------------------------------------------------------------
    OUTPUTS_DIR: Final[Path] = BASE_DIR / "outputs"

    ALIGNED_OUTPUT_DIR: Final[Path] = OUTPUTS_DIR / "aligned"
    MASK_OUTPUT_DIR: Final[Path] = OUTPUTS_DIR / "masks"
    HIGHLIGHTED_OUTPUT_DIR: Final[Path] = OUTPUTS_DIR / "highlighted"
    STATISTICS_OUTPUT_DIR: Final[Path] = OUTPUTS_DIR / "statistics"
    SUMMARIES_OUTPUT_DIR: Final[Path] = OUTPUTS_DIR / "summaries"
    REPORTS_OUTPUT_DIR: Final[Path] = OUTPUTS_DIR / "reports"

    # ------------------------------------------------------------------
    # Application Directories
    # ------------------------------------------------------------------
    MODULES_DIR: Final[Path] = BASE_DIR / "modules"
    MODELS_DIR: Final[Path] = BASE_DIR / "models"
    UTILS_DIR: Final[Path] = BASE_DIR / "utils"
    STATIC_DIR: Final[Path] = BASE_DIR / "static"
    TEMPLATES_DIR: Final[Path] = BASE_DIR / "templates"
    TESTS_DIR: Final[Path] = BASE_DIR / "tests"
    DOCS_DIR: Final[Path] = BASE_DIR / "docs"

    # ------------------------------------------------------------------
    # Allowed File Extensions
    # ------------------------------------------------------------------
    ALLOWED_IMAGE_EXTENSIONS: Final[set[str]] = {
        ".jpg",
        ".jpeg",
        ".png",
    }

    ALLOWED_PDF_EXTENSIONS: Final[set[str]] = {
        ".pdf",
    }

    ALLOWED_CAD_EXTENSIONS: Final[set[str]] = {
        ".dwg",
        ".dxf",
    }

    ALLOWED_FILE_EXTENSIONS: Final[set[str]] = (
        ALLOWED_IMAGE_EXTENSIONS
        | ALLOWED_PDF_EXTENSIONS
        | ALLOWED_CAD_EXTENSIONS
    )

    # ------------------------------------------------------------------
    # Upload Settings
    # ------------------------------------------------------------------
    MAX_FILE_SIZE_MB: Final[int] = 50
    MAX_UPLOAD_FILES: Final[int] = 2

    # ------------------------------------------------------------------
    # PDF Conversion Settings
    # ------------------------------------------------------------------
    PDF_RENDER_DPI: Final[int] = 300

    # ------------------------------------------------------------------
    # Image Processing Parameters
    # ------------------------------------------------------------------
    TARGET_IMAGE_WIDTH: Final[int] = 1920
    TARGET_IMAGE_HEIGHT: Final[int] = 1080

    ENABLE_GRAYSCALE: Final[bool] = True
    ENABLE_HISTOGRAM_EQUALIZATION: Final[bool] = False
    ENABLE_CLAHE: Final[bool] = False

    GAUSSIAN_KERNEL_SIZE: Final[tuple[int, int]] = (5, 5)
    MEDIAN_BLUR_KERNEL_SIZE: Final[int] = 3

    # Minimum bounding-box area (in pixels) for a contour to count as a
    # real "changed region". Raised from 100 -> 400 to filter out
    # anti-aliasing specks and sub-pixel PDF rendering noise.
    MIN_CONTOUR_AREA: Final[int] = 400

    # Merges nearby fragments of the same real change into one region
    # before noise-filtering runs. Reduced to (5,5)/2 iterations so
    # different physical sections are kept as separate bounding boxes.
    MORPH_KERNEL_SIZE: Final[tuple[int, int]] = (5, 5)
    MORPH_ITERATIONS: Final[int] = 2

    # ------------------------------------------------------------------
    # Difference Detection
    # ------------------------------------------------------------------
    SSIM_FULL: Final[bool] = True
    USE_OTSU_THRESHOLD: Final[bool] = True

    # Extra fixed floor applied on top of Otsu's threshold. Otsu alone
    # can pick a very permissive cutoff on documents that are 95%+
    # identical, letting minor rendering noise through. A pixel must be
    # both a statistical outlier (Otsu) AND below this fixed similarity
    # floor to count as "changed".
    MIN_DIFF_INTENSITY: Final[int] = 140

    # A contour whose bounding box exceeds this fraction of the total
    # page area is treated as a residual alignment artifact rather than
    # a real design change, and is dropped (with a log warning).
    MAX_CONTOUR_AREA_RATIO: Final[float] = 0.15

    # Contours thinner/longer than this aspect ratio (and below 5x
    # MIN_CONTOUR_AREA) are treated as line-thickness / rendering-shift
    # artifacts rather than real changes.
    MAX_CONTOUR_ASPECT_RATIO: Final[float] = 12.0

    # ------------------------------------------------------------------
    # Alignment Quality Gate
    # ------------------------------------------------------------------
    # ORB can produce a homography that satisfies RANSAC on paper but is
    # actually wrong -- common on engineering drawings with lots of
    # repetitive features (grid lines, hatching, similar corners). If
    # the accepted match set doesn't clear these bars, alignment is
    # skipped entirely rather than applying an unreliable warp.
    ALIGNMENT_MIN_INLIERS: Final[int] = 15
    ALIGNMENT_MIN_INLIER_RATIO: Final[float] = 0.5

    # ------------------------------------------------------------------
    # Change Classification (Added / Removed / Modified)
    # ------------------------------------------------------------------
    # A pixel darker than this (0-255 grayscale) counts as "ink" -- part
    # of a line, symbol, or text -- rather than blank paper.
    INK_PIXEL_THRESHOLD: Final[int] = 200

    # A region is treated as "empty" if less than this fraction of its
    # pixels are ink. Used to tell Added (was empty, now has content)
    # apart from Removed (had content, now empty) and Modified (content
    # in both, but different).
    EMPTY_REGION_INK_RATIO: Final[float] = 0.02

    # Colors (BGR) used to draw each change type's bounding box.
    CHANGE_TYPE_COLORS: Final[dict[str, tuple[int, int, int]]] = {
        "Added": (0, 170, 0),       # green
        "Removed": (0, 0, 255),     # red
        "Modified": (0, 165, 255),  # amber
    }

    # ------------------------------------------------------------------
    # OCR Settings (Tesseract & Grid mapping)
    # ------------------------------------------------------------------
    TESSERACT_CMD: Final[str] = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    OCR_PADDING: Final[int] = 10
    OCR_UPSCALE_FACTOR: Final[int] = 2
    OCR_PSM_MODE: Final[int] = 6
    OCR_CHAR_WHITELIST: Final[str] = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz.,+-°%/:*()[]#_ "

    GRID_ROWS: Final[list[str]] = ["A", "B", "C", "D", "E", "F", "G", "H"]
    GRID_COLUMNS: Final[list[str]] = ["1", "2", "3", "4", "5", "6", "7", "8"]

    # ------------------------------------------------------------------
    # Visualization Settings
    # ------------------------------------------------------------------
    BOUNDING_BOX_COLOR: Final[tuple[int, int, int]] = (0, 0, 255)  # Red (BGR)
    BOUNDING_BOX_THICKNESS: Final[int] = 2

    # ------------------------------------------------------------------
    # Summary Settings
    # ------------------------------------------------------------------
    MINOR_CHANGE_THRESHOLD: Final[float] = 2.0
    MODERATE_CHANGE_THRESHOLD: Final[float] = 10.0

    # ------------------------------------------------------------------
    # Flask Application Settings
    # ------------------------------------------------------------------
    SECRET_KEY: Final[str] = "change-this-in-production"
    DEBUG: Final[bool] = True
    HOST: Final[str] = "127.0.0.1"
    PORT: Final[int] = 5000

    # ------------------------------------------------------------------
    # Utility Methods
    # ------------------------------------------------------------------
    @classmethod
    def create_directories(cls) -> None:
        """Create all required project directories if they do not exist."""

        directories = [
            cls.UPLOADS_DIR,
            cls.PDF_UPLOAD_DIR,
            cls.IMAGE_UPLOAD_DIR,
            cls.CAD_UPLOAD_DIR,
            cls.TEMP_UPLOAD_DIR,
            cls.OUTPUTS_DIR,
            cls.ALIGNED_OUTPUT_DIR,
            cls.MASK_OUTPUT_DIR,
            cls.HIGHLIGHTED_OUTPUT_DIR,
            cls.STATISTICS_OUTPUT_DIR,
            cls.SUMMARIES_OUTPUT_DIR,
            cls.REPORTS_OUTPUT_DIR,
            cls.MODULES_DIR,
            cls.MODELS_DIR,
            cls.UTILS_DIR,
            cls.STATIC_DIR,
            cls.TEMPLATES_DIR,
            cls.TESTS_DIR,
            cls.DOCS_DIR,
        ]

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)