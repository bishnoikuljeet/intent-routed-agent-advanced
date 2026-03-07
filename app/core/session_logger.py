import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Dict, Any
import json
from datetime import datetime


class SessionLogger:
    def __init__(self, session_id: str, log_dir: str = "logs"):
        self.session_id = session_id
        self.log_dir = Path(log_dir) / "sessions" / session_id
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Create separate loggers
        self.query_logger = self._setup_logger("query", "query.log")
        self.execution_logger = self._setup_logger("execution", "execution.log")
        self.error_logger = self._setup_logger("error", "error.log")
    
    def _setup_logger(self, name: str, filename: str) -> logging.Logger:
        """Setup logger with rotation"""
        logger_name = f"{self.session_id}.{name}"
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.INFO)
        
        # Remove existing handlers
        logger.handlers = []
        
        # Create rotating file handler (10MB max, 5 backups)
        handler = RotatingFileHandler(
            self.log_dir / filename,
            maxBytes=10*1024*1024,
            backupCount=5
        )
        
        # JSON formatter
        formatter = logging.Formatter(
            '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "message": %(message)s}'
        )
        handler.setFormatter(formatter)
        
        logger.addHandler(handler)
        return logger
    
    def log_query(self, query: str, metadata: Dict[str, Any] = None):
        """Log user query"""
        log_data = {
            "query": query,
            "session_id": self.session_id,
            "metadata": metadata or {}
        }
        self.query_logger.info(json.dumps(log_data))
    
    def log_execution_step(self, step: str, data: Dict[str, Any]):
        """Log execution trace step"""
        log_data = {
            "step": step,
            "session_id": self.session_id,
            "data": data,
            "timestamp": datetime.utcnow().isoformat()
        }
        self.execution_logger.info(json.dumps(log_data))
    
    def log_error(self, error: str, context: Dict[str, Any] = None):
        """Log error"""
        log_data = {
            "error": error,
            "session_id": self.session_id,
            "context": context or {},
            "timestamp": datetime.utcnow().isoformat()
        }
        self.error_logger.error(json.dumps(log_data))
    
    def log_response(self, response: Dict[str, Any]):
        """Log agent response"""
        log_data = {
            "response": response,
            "session_id": self.session_id,
            "timestamp": datetime.utcnow().isoformat()
        }
        self.execution_logger.info(json.dumps(log_data))
