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

    MIN_CONTOUR_AREA: Final[int] = 100

    MORPH_KERNEL_SIZE: Final[tuple[int, int]] = (5, 5)
    MORPH_ITERATIONS: Final[int] = 2

    # ------------------------------------------------------------------
    # Difference Detection
    # ------------------------------------------------------------------
    SSIM_FULL: Final[bool] = True
    USE_OTSU_THRESHOLD: Final[bool] = True

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