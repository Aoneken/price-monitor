"""Central logging configuration for the web application.

Sets up a console handler and a rotating file handler with a structured
log format including timestamp, level, module, and message.

Call init_logging() early (e.g. in webapp/main.py) before using CRUD or
background tasks.
"""

from __future__ import annotations

import logging
import os
from logging.handlers import RotatingFileHandler

LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
LOG_PATH = os.path.join(LOG_DIR, "app.log")

DEFAULT_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"


def init_logging(level: int = logging.INFO) -> None:
    os.makedirs(LOG_DIR, exist_ok=True)

    root = logging.getLogger()
    if any(isinstance(h, RotatingFileHandler) for h in root.handlers):
        # Already initialized
        return

    root.setLevel(level)

    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(level)
    ch.setFormatter(logging.Formatter(DEFAULT_FORMAT))
    root.addHandler(ch)

    # Rotating file handler
    fh = RotatingFileHandler(
        LOG_PATH, maxBytes=2_000_000, backupCount=3, encoding="utf-8"
    )
    fh.setLevel(level)
    fh.setFormatter(logging.Formatter(DEFAULT_FORMAT))
    root.addHandler(fh)

    logging.getLogger(__name__).info("Logging initialized -> %s", LOG_PATH)
