import logging
import json
import sys
from datetime import datetime
from typing import Any, Dict, Optional
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


def setup_logging():
    logging.setLoggerClass(StructuredLogger)
    
    logger = logging.getLogger("intent_routed_agent")
    logger.setLevel(getattr(logging, settings.log_level.upper()))
    
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(getattr(logging, settings.log_level.upper()))
    
    formatter = logging.Formatter('%(message)s')
    handler.setFormatter(formatter)
    
    logger.addHandler(handler)
    
    return logger


logger = setup_logging()
