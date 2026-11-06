"""Structured logging setup using Loguru."""

import sys
from pathlib import Path
from loguru import logger


def setup_logging(log_level: str = "INFO", log_file: Path | None = None) -> None:
    """Configure Loguru logger with custom formats and sinks."""
    logger.remove()

    # Console sink with color and contextual info
    log_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
        "<level>{message}</level>"
    )

    logger.add(
        sys.stderr,
        level=log_level,
        format=log_format,
        colorize=True,
    )

    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        logger.add(
            str(log_file),
            level=log_level,
            format=log_format,
            rotation="10 MB",
            retention="7 days",
            compression="zip",
        )


def get_logger(name: str):
    """Return a contextualized logger."""
    return logger.bind(name=name)
