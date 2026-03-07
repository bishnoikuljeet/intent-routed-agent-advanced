import requests
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)


class APIClient:
    def __init__(self, backend_url: str):
        self.backend_url = backend_url.rstrip('/')
        self.api_base = f"{self.backend_url}/api/v1"
        self.timeout = 60
    
    def health_check(self) -> Dict[str, Any]:
        """Check backend health"""
        try:
            response = requests.get(f"{self.api_base}/health", timeout=5)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {"status": "unhealthy", "error": str(e)}
    
    def create_session(self) -> Dict[str, Any]:
        """Create a new session"""
        try:
            response = requests.post(f"{self.api_base}/sessions", timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to create session: {e}")
            raise
    
    def list_sessions(self) -> List[Dict[str, Any]]:
        """List all sessions"""
        try:
            response = requests.get(f"{self.api_base}/sessions", timeout=self.timeout)
            response.raise_for_status()
            return response.json().get('sessions', [])
        except Exception as e:
            logger.error(f"Failed to list sessions: {e}")
            return []
    
    def get_session(self, session_id: str) -> Dict[str, Any]:
        """Get session details"""
        try:
            response = requests.get(f"{self.api_base}/sessions/{session_id}", timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get session {session_id}: {e}")
            raise
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a session"""
        try:
            response = requests.delete(f"{self.api_base}/sessions/{session_id}", timeout=self.timeout)
            response.raise_for_status()
            return True
        except Exception as e:
            logger.error(f"Failed to delete session {session_id}: {e}")
            return False
    
    def process_query(self, query: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Process a query"""
        try:
            payload = {"query": query}
            if session_id:
                payload["conversation_id"] = session_id
            
            response = requests.post(
                f"{self.api_base}/query",
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to process query: {e}")
            raise
    
    def get_tools(self) -> List[Dict[str, Any]]:
        """Get available tools"""
        try:
            response = requests.get(f"{self.api_base}/tools", timeout=self.timeout)
            response.raise_for_status()
            return response.json().get('tools', [])
        except Exception as e:
            logger.error(f"Failed to get tools: {e}")
            return []
    
    def get_servers(self) -> Dict[str, Any]:
        """Get MCP servers info"""
        try:
            response = requests.get(f"{self.api_base}/servers", timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get servers: {e}")
            return {}
