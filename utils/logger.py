"""
utils/logger.py

Reusable logging configuration for the AI-Based Engineering Drawing Difference
Detection, Visualization, and Automated Change Summarization project.

Features:
- Console logging
- Rotating file logging
- Automatic logs directory creation
- Consistent timestamped log format
"""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from config import ProjectConfig


# =============================================================================
# Log Directory Configuration
# =============================================================================

LOGS_DIR = ProjectConfig.BASE_DIR / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)

LOG_FILE = LOGS_DIR / "application.log"


# =============================================================================
# Log Formatter
# =============================================================================

LOG_FORMAT = (
    "%(asctime)s | "
    "%(levelname)-8s | "
    "%(name)s | "
    "%(filename)s:%(lineno)d | "
    "%(message)s"
)

DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


# =============================================================================
# Logger Factory
# =============================================================================

def get_logger(name: str) -> logging.Logger:
    """
    Create or retrieve a configured logger.

    Parameters
    ----------
    name : str
        Logger name (typically __name__).

    Returns
    -------
    logging.Logger
        Configured logger instance.
    """

    logger = logging.getLogger(name)

    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)
    logger.propagate = False

    formatter = logging.Formatter(
        fmt=LOG_FORMAT,
        datefmt=DATE_FORMAT,
    )

    # -------------------------------------------------------------------------
    # Console Handler
    # -------------------------------------------------------------------------
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    # -------------------------------------------------------------------------
    # Rotating File Handler
    # -------------------------------------------------------------------------
    file_handler = RotatingFileHandler(
        filename=LOG_FILE,
        maxBytes=5 * 1024 * 1024,  # 5 MB
        backupCount=5,
        encoding="utf-8",
    )

    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)

    # -------------------------------------------------------------------------
    # Register Handlers
    # -------------------------------------------------------------------------
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger