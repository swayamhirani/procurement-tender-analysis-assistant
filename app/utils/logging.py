"""Structured application logging configuration."""

import logging
import sys


def setup_logging(level: int = logging.INFO) -> logging.Logger:
    """Configure structured logging for the application."""
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.StreamHandler(sys.stdout),
        ],
    )
    return logging.getLogger("procurement_assistant")


def get_logger(name: str) -> logging.Logger:
    """Get a named logger instance."""
    return logging.getLogger(name)
