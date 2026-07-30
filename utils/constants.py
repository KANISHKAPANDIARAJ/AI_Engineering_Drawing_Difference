"""
utils/constants.py

Reusable constants for the AI-Based Engineering Drawing Difference Detection,
Visualization, and Automated Change Summarization project.

This module contains immutable constants shared across the application.
"""

from __future__ import annotations

# ==========================================================================
# FILE EXTENSIONS
# ==========================================================================

IMAGE_FILE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
}

PDF_FILE_EXTENSIONS = {
    ".pdf",
}

CAD_FILE_EXTENSIONS = {
    ".dwg",
    ".dxf",
}

ALLOWED_FILE_EXTENSIONS = (
    IMAGE_FILE_EXTENSIONS
    | PDF_FILE_EXTENSIONS
    | CAD_FILE_EXTENSIONS
)

# ==========================================================================
# IMAGE RESIZE SETTINGS
# ==========================================================================

TARGET_IMAGE_WIDTH = 1920
TARGET_IMAGE_HEIGHT = 1080

TARGET_IMAGE_SIZE = (
    TARGET_IMAGE_WIDTH,
    TARGET_IMAGE_HEIGHT,
)

# ==========================================================================
# PDF SETTINGS
# ==========================================================================

PDF_RENDER_DPI = 300

# ==========================================================================
# IMAGE PROCESSING SETTINGS
# ==========================================================================

ENABLE_GRAYSCALE = True
ENABLE_HISTOGRAM_EQUALIZATION = False
ENABLE_CLAHE = False

GAUSSIAN_KERNEL_SIZE = (5, 5)
MEDIAN_BLUR_KERNEL_SIZE = 3

# ==========================================================================
# IMAGE ALIGNMENT
# ==========================================================================

MINIMUM_MATCH_COUNT = 10
RANSAC_REPROJECTION_THRESHOLD = 5.0

# ==========================================================================
# SSIM SETTINGS
# ==========================================================================

SSIM_THRESHOLD = 0.95
SSIM_FULL = True

# ==========================================================================
# THRESHOLDING
# ==========================================================================

USE_OTSU_THRESHOLD = True

# ==========================================================================
# MORPHOLOGICAL PROCESSING
# ==========================================================================

MORPH_KERNEL_SIZE = (5, 5)
MORPH_ITERATIONS = 2
MIN_CONTOUR_AREA = 100

# ==========================================================================
# BOUNDING BOX SETTINGS (OpenCV BGR Format)
# ==========================================================================

BOUNDING_BOX_COLOR = (0, 0, 255)
BOUNDING_BOX_THICKNESS = 2

# ==========================================================================
# MASK VISUALIZATION
# ==========================================================================

MASK_COLOR = (255, 255, 255)
MASK_BACKGROUND_COLOR = (0, 0, 0)

# ==========================================================================
# TEXT / FONT SETTINGS (OpenCV)
# ==========================================================================

FONT_FACE = 0  # cv2.FONT_HERSHEY_SIMPLEX
FONT_SCALE = 0.6
FONT_THICKNESS = 2

FONT_COLOR = (0, 255, 0)
TEXT_BACKGROUND_COLOR = (0, 0, 0)

# ==========================================================================
# CHANGE SEVERITY LEVELS
# ==========================================================================

SEVERITY_MINOR = "Minor"
SEVERITY_MODERATE = "Moderate"
SEVERITY_MAJOR = "Major"

MINOR_CHANGE_THRESHOLD = 2.0
MODERATE_CHANGE_THRESHOLD = 10.0

# ==========================================================================
# CHANGE CLASSIFICATION LABELS
# ==========================================================================

CHANGE_TYPE_ADDED_ANNOTATION = "Added Annotation"
CHANGE_TYPE_REMOVED_ANNOTATION = "Removed Annotation"
CHANGE_TYPE_MODIFIED_DIMENSION = "Modified Dimension"
CHANGE_TYPE_ADDED_HOLE = "Added Hole"
CHANGE_TYPE_REMOVED_SYMBOL = "Removed Symbol"
CHANGE_TYPE_STRUCTURAL_MODIFICATION = "Structural Modification"
CHANGE_TYPE_UNKNOWN = "Unknown"

# ==========================================================================
# LOCATION LABELS
# ==========================================================================

LOCATION_TOP_LEFT = "Top Left"
LOCATION_TOP_CENTER = "Top Center"
LOCATION_TOP_RIGHT = "Top Right"

LOCATION_CENTER_LEFT = "Center Left"
LOCATION_CENTER = "Center"
LOCATION_CENTER_RIGHT = "Center Right"

LOCATION_BOTTOM_LEFT = "Bottom Left"
LOCATION_BOTTOM_CENTER = "Bottom Center"
LOCATION_BOTTOM_RIGHT = "Bottom Right"

# ==========================================================================
# REPORT SETTINGS
# ==========================================================================

PERCENTAGE_PRECISION = 2
AREA_PRECISION = 2

# ==========================================================================
# APPLICATION SETTINGS
# ==========================================================================

MAX_UPLOAD_FILES = 2
MAX_FILE_SIZE_MB = 50

