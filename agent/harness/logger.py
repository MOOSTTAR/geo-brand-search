import sys
import json
import logging
from datetime import datetime, timezone
from typing import Any


def setup_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    handler = logging.StreamHandler(sys.stderr)
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
    logger.addHandler(handler)

    return logger


_initialized: set[str] = set()


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if name not in _initialized:
        _initialized.add(name)
        handler = logging.StreamHandler(sys.stderr)
        handler.setLevel(logging.DEBUG)
        handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)
    return logger


def log_event(logger: logging.Logger, event: str, **kwargs: Any):
    """Emit a structured log event to stderr (not stdout, which is reserved for JSON protocol)."""
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event": event,
        **kwargs,
    }
    logger.info(json.dumps(entry, ensure_ascii=False))
