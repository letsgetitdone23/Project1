from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict


def _get_logger() -> logging.Logger:
    level_name = os.getenv("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)
    logger = logging.getLogger("restaurant_recommender")
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter("%(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    logger.setLevel(level)
    return logger


def log_event(event_type: str, payload: Dict[str, Any]) -> None:
    logger = _get_logger()
    record = {"event": event_type, **payload}
    logger.info(json.dumps(record, ensure_ascii=True))

