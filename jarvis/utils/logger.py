from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler

from jarvis.utils.config import settings


def setup_logger() -> logging.Logger:
    settings.user_data_dir.mkdir(parents=True, exist_ok=True)
    log_file = settings.user_data_dir / "jarvis.log"

    logger = logging.getLogger("jarvis")
    logger.setLevel(logging.DEBUG if settings.debug else logging.INFO)
    logger.handlers.clear()

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    stream_handler.setLevel(logging.DEBUG if settings.debug else logging.INFO)

    file_handler = RotatingFileHandler(
        log_file, maxBytes=1_000_000, backupCount=5, encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.DEBUG)

    logger.addHandler(stream_handler)
    logger.addHandler(file_handler)
    logger.propagate = False
    return logger
