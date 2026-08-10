"""Central logging configuration for SmartReco.

Application modules should use ``get_logger(__name__)`` instead of configuring
logging individually. Logging is configured once per process.
"""

import logging
import os
import sys
from pathlib import Path


LOG_FORMAT = (
    "%(asctime)s | "
    "%(levelname)s | "
    "%(name)s | "
    "%(filename)s:%(lineno)d | "
    "%(message)s"
)

_CONFIGURED_ATTRIBUTE = "_smartreco_configured"


def configure_logging() -> None:
    """Configure console and file logging once."""

    root_logger = logging.getLogger()

    if getattr(root_logger, _CONFIGURED_ATTRIBUTE, False):
        return

    log_level = os.getenv("LOG_LEVEL", "INFO").upper()

    log_directory = Path(__file__).resolve().parents[2] / "logs"
    log_directory.mkdir(parents=True, exist_ok=True)

    formatter = logging.Formatter(LOG_FORMAT)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)

    file_handler = logging.FileHandler(
        log_directory / "smartreco.log",
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)

    root_logger.setLevel(log_level)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

    setattr(root_logger, _CONFIGURED_ATTRIBUTE, True)

    # Reduce noisy third-party logs.
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Return a configured logger for an application module."""

    configure_logging()
    return logging.getLogger(name)