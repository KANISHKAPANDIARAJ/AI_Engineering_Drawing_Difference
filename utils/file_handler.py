"""
utils/file_handler.py

File handling utilities for the AI-Based Engineering Drawing Difference
Detection, Visualization, and Automated Change Summarization project.

Responsibilities:
- Validate uploaded files
- Save uploaded files
- Create required folders
- Delete temporary files
- Generate unique filenames
"""

from __future__ import annotations

import shutil
import uuid
from pathlib import Path

from werkzeug.datastructures import FileStorage

from config import ProjectConfig
from utils.constants import ALLOWED_FILE_EXTENSIONS


def validate_file(file_name: str) -> bool:
    """
    Validate whether a file has a supported extension.

    Parameters
    ----------
    file_name : str
        Name of the uploaded file.

    Returns
    -------
    bool
        True if the file extension is supported, otherwise False.
    """
    extension = Path(file_name).suffix.lower()
    return extension in ALLOWED_FILE_EXTENSIONS


def generate_unique_filename(file_name: str) -> str:
    """
    Generate a unique filename while preserving the original extension.

    Parameters
    ----------
    file_name : str
        Original filename.

    Returns
    -------
    str
        Unique filename.
    """
    extension = Path(file_name).suffix.lower()
    unique_id = uuid.uuid4().hex

    return f"{unique_id}{extension}"


def save_upload(
    file_object: FileStorage,
    destination_directory: Path,
) -> Path:
    """
    Save an uploaded file to the specified directory.

    Parameters
    ----------
    file_object : FileStorage
        Uploaded Flask file object.
    destination_directory : Path
        Destination directory.

    Returns
    -------
    Path
        Path to the saved file.
    """
    destination_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    unique_filename = generate_unique_filename(file_object.filename)

    destination_path = destination_directory / unique_filename

    file_object.save(destination_path)

    return destination_path


def create_folders() -> None:
    """
    Create all required project directories.

    Returns
    -------
    None
    """
    ProjectConfig.create_directories()


def delete_temporary_files() -> None:
    """
    Delete all files and folders inside the temporary upload directory.

    Returns
    -------
    None
    """
    temp_directory = ProjectConfig.TEMP_UPLOAD_DIR

    if not temp_directory.exists():
        return

    for item in temp_directory.iterdir():
        try:
            if item.is_file():
                item.unlink()

            elif item.is_dir():
                shutil.rmtree(item)

        except OSError:
            # Ignore files that cannot be deleted
            continue