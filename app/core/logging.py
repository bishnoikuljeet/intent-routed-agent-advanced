import logging
import json
import sys
from datetime import datetime
from typing import Any, Dict, Optional
from logging.handlers import RotatingFileHandler
from pathlib import Path

from app.core.config import settings


class StructuredLogger(logging.Logger):
    def _log_structured(self, level: int, msg: str, extra: Dict[str, Any] = None):
        from app.core.request_context import get_request_id
        
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": logging.getLevelName(level),
            "message": msg,
        }
        
        request_id = get_request_id()
        if request_id:
            log_data["request_id"] = request_id
        
        if extra:
            log_data.update(extra)
        
        super()._log(level, json.dumps(log_data), ())
    
    def info_structured(self, msg: str, **kwargs):
        self._log_structured(logging.INFO, msg, kwargs)
    
    def error_structured(self, msg: str, **kwargs):
        self._log_structured(logging.ERROR, msg, kwargs)
    
    def warning_structured(self, msg: str, **kwargs):
        self._log_structured(logging.WARNING, msg, kwargs)
    
    def debug_structured(self, msg: str, **kwargs):
        self._log_structured(logging.DEBUG, msg, kwargs)


LOG_DIR = Path("logs")
LOG_FILE = LOG_DIR / "app.log"


def setup_logging():
    logging.setLoggerClass(StructuredLogger)
    
    logger = logging.getLogger("intent_routed_agent")
    logger.setLevel(getattr(logging, settings.log_level.upper()))
    logger.handlers.clear()

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    formatter = logging.Formatter('%(message)s')

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setLevel(getattr(logging, settings.log_level.upper()))
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    file_handler = RotatingFileHandler(LOG_FILE, maxBytes=5 * 1024 * 1024, backupCount=5)
    file_handler.setLevel(getattr(logging, settings.log_level.upper()))
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    return logger


logger = setup_logging()
