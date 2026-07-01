"""
utils/pdf_utils.py

PDF utility functions for the AI-Based Engineering Drawing Difference
Detection, Visualization, and Automated Change Summarization project.

Features:
- High-resolution PDF rendering
- First-page PDF processing
- Warning for multi-page PDFs
- Save rendered images
- Return rendered page as a NumPy array
"""

from __future__ import annotations

from pathlib import Path

import cv2
import fitz
import numpy as np

from config import ProjectConfig
from utils.logger import get_logger

logger = get_logger(__name__)


def _render_page(page: fitz.Page) -> np.ndarray:
    """
    Render a PDF page as a high-resolution OpenCV BGR image.

    Parameters
    ----------
    page : fitz.Page
        PDF page to render.

    Returns
    -------
    np.ndarray
        Rendered page as a BGR image.
    """
    zoom = ProjectConfig.PDF_RENDER_DPI / 72.0
    matrix = fitz.Matrix(zoom, zoom)

    pixmap = page.get_pixmap(
        matrix=matrix,
        alpha=False,
    )

    image = np.frombuffer(
        pixmap.samples,
        dtype=np.uint8,
    ).reshape(
        pixmap.height,
        pixmap.width,
        pixmap.n,
    )

    if pixmap.n == 3:
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

    elif pixmap.n == 4:
        image = cv2.cvtColor(image, cv2.COLOR_RGBA2BGR)

    return image


def pdf_to_image(pdf_path: Path) -> np.ndarray:
    """
    Convert a PDF into a high-resolution OpenCV image.

    Project Contract
    ----------------
    - Single-page PDF: return the rendered page.
    - Multi-page PDF: render only the first page and log a warning.

    Parameters
    ----------
    pdf_path : Path
        Path to the PDF file.

    Returns
    -------
    np.ndarray
        First rendered page as a BGR image.

    Raises
    ------
    FileNotFoundError
        If the PDF file does not exist.
    ValueError
        If the PDF is empty.
    RuntimeError
        If the PDF cannot be opened or rendered.
    """
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    try:
        with fitz.open(pdf_path) as document:

            if document.page_count == 0:
                raise ValueError("The PDF contains no pages.")

            if document.page_count > 1:
                logger.warning(
                    "PDF '%s' contains %d pages. "
                    "Only the first page will be processed.",
                    pdf_path.name,
                    document.page_count,
                )

            first_page = document.load_page(0)

            return _render_page(first_page)

    except Exception as error:
        raise RuntimeError(
            f"Unable to read PDF '{pdf_path}'."
        ) from error


def save_images(
    images: list[np.ndarray],
    output_directory: Path,
    base_filename: str,
) -> list[Path]:
    """
    Save one or more rendered images as PNG files.

    Parameters
    ----------
    images : list[np.ndarray]
        Images to save.
    output_directory : Path
        Destination directory.
    base_filename : str
        Base filename for generated images.

    Returns
    -------
    list[Path]
        Paths of the saved images.

    Raises
    ------
    RuntimeError
        If an image cannot be written to disk.
    """
    output_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    saved_paths: list[Path] = []

    for index, image in enumerate(images, start=1):
        image_path = output_directory / f"{base_filename}_page_{index}.png"

        success = cv2.imwrite(str(image_path), image)

        if not success:
            raise RuntimeError(
                f"Failed to save image: {image_path}"
            )

        saved_paths.append(image_path)

    return saved_paths