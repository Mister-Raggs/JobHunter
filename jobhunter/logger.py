"""Logging setup for JobHunter."""

import logging
import os
import sys
from pathlib import Path

LOG_FILE = Path(__file__).parent.parent / "data" / "jobhunter.log"
LOG_FORMAT = "%(asctime)s [%(levelname)s] %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def get_logger() -> logging.Logger:
    """Return the JobHunter logger, configuring it on first call."""
    logger = logging.getLogger("jobhunter")
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)

    # stdout handler
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
    logger.addHandler(stdout_handler)

    # file handler — only if data/ dir is writable
    try:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(LOG_FILE)
        file_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
        logger.addHandler(file_handler)
    except OSError:
        pass

    return logger