"""Logging setup: writes detailed logs to file, concise summaries to console."""

from __future__ import annotations

import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path

LOG_DIR = Path(__file__).resolve().parent.parent / "logs"
LOG_FILE = LOG_DIR / "trading_bot.log"

_FILE_FORMAT = "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s"
_CONSOLE_FORMAT = "%(levelname)-7s | %(message)s"


def setup_logging(level: str | None = None) -> logging.Logger:
    """Configure root logger. Idempotent — safe to call more than once."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    level_name = (level or os.getenv("LOG_LEVEL", "INFO")).upper()
    log_level = getattr(logging, level_name, logging.INFO)

    root = logging.getLogger()
    root.setLevel(log_level)

    if getattr(root, "_trading_bot_configured", False):
        return logging.getLogger("trading_bot")

    file_handler = RotatingFileHandler(
        LOG_FILE, maxBytes=2_000_000, backupCount=5, encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(_FILE_FORMAT))

    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(logging.Formatter(_CONSOLE_FORMAT))

    root.addHandler(file_handler)
    root.addHandler(console_handler)

    # Quiet noisy third-party libraries on console; full detail still in file.
    logging.getLogger("urllib3").setLevel(logging.WARNING)

    root._trading_bot_configured = True  # type: ignore[attr-defined]
    return logging.getLogger("trading_bot")
