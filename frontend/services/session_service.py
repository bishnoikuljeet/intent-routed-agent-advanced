import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)


class SessionService:
    def __init__(self, storage_path: str = "data/sessions"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.sessions_file = self.storage_path / "sessions.json"
        self._ensure_storage()
    
    def _ensure_storage(self):
        """Ensure storage file exists"""
        if not self.sessions_file.exists():
            self._save_sessions({})
    
    def _load_sessions(self) -> Dict[str, Any]:
        """Load sessions from storage"""
        try:
            with open(self.sessions_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load sessions: {e}")
            return {}
    
    def _save_sessions(self, sessions: Dict[str, Any]):
        """Save sessions to storage"""
        try:
            with open(self.sessions_file, 'w') as f:
                json.dump(sessions, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save sessions: {e}")
    
    def create_session(self, session_id: str, metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """Create a new session"""
        sessions = self._load_sessions()

        now_utc = datetime.now(timezone.utc).isoformat()
        
        session = {
            "id": session_id,
            "created_at": now_utc,
            "updated_at": now_utc,
            "messages": [],
            "metadata": metadata or {}
        }
        
        sessions[session_id] = session
        self._save_sessions(sessions)
        
        return session
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get a session by ID"""
        sessions = self._load_sessions()
        return sessions.get(session_id)
    
    def list_sessions(self, limit: int = 50) -> List[Dict[str, Any]]:
        """List all sessions"""
        sessions = self._load_sessions()
        session_list = list(sessions.values())
        
        # Sort by updated_at descending
        session_list.sort(key=lambda x: x.get('updated_at', ''), reverse=True)
        
        return session_list[:limit]
    
    def update_session(self, session_id: str, updates: Dict[str, Any]):
        """Update a session"""
        sessions = self._load_sessions()
        
        if session_id in sessions:
            sessions[session_id].update(updates)
            sessions[session_id]['updated_at'] = datetime.now(timezone.utc).isoformat()
            self._save_sessions(sessions)
    
    def add_message(self, session_id: str, role: str, content: str, metadata: Optional[Dict] = None):
        """Add a message to session"""
        sessions = self._load_sessions()
        
        if session_id in sessions:
            message = {
                "role": role,
                "content": content,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "metadata": metadata or {}
            }
            
            sessions[session_id]['messages'].append(message)
            sessions[session_id]['updated_at'] = datetime.now(timezone.utc).isoformat()
            self._save_sessions(sessions)
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a session"""
        sessions = self._load_sessions()
        
        if session_id in sessions:
            del sessions[session_id]
            self._save_sessions(sessions)
            return True
        
        return False
    
    def search_sessions(self, query: str) -> List[Dict[str, Any]]:
        """Search sessions by query content"""
        sessions = self._load_sessions()
        results = []
        
        query_lower = query.lower()
        
        for session in sessions.values():
            # Search in messages
            for message in session.get('messages', []):
                if query_lower in message.get('content', '').lower():
                    results.append(session)
                    break
        
        return results
