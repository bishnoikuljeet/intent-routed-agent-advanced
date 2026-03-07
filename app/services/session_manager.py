import sqlite3
import uuid
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import json
import logging

logger = logging.getLogger(__name__)


class SessionManager:
    def __init__(self, db_path: str = "data/sessions/sessions.db", log_dir: str = "logs"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.log_dir = Path(log_dir)
        self._init_database()
    
    def _init_database(self):
        """Initialize SQLite database"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        # Create sessions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                metadata TEXT,
                log_dir TEXT
            )
        """)
        
        # Create messages table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                metadata TEXT,
                FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
            )
        """)
        
        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_session_id ON messages(session_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_created_at ON sessions(created_at)")
        
        conn.commit()
        conn.close()
        
        logger.info(f"Session database initialized at {self.db_path}")
    
    def create_session(self, metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """Create a new session"""
        # Generate timestamp-based session ID
        session_id = datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f")[:-3]
        created_at = datetime.utcnow().isoformat()
        
        # Create session log directory
        session_log_dir = self.log_dir / "sessions" / session_id
        session_log_dir.mkdir(parents=True, exist_ok=True)
        
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO sessions (id, created_at, updated_at, metadata, log_dir)
            VALUES (?, ?, ?, ?, ?)
        """, (
            session_id,
            created_at,
            created_at,
            json.dumps(metadata or {}),
            str(session_log_dir)
        ))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Created session: {session_id}")
        
        return {
            "id": session_id,
            "session_id": session_id,
            "created_at": created_at,
            "updated_at": created_at,
            "metadata": metadata or {},
            "log_dir": str(session_log_dir)
        }
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session by ID"""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM sessions WHERE id = ?", (session_id,))
        row = cursor.fetchone()
        
        if not row:
            conn.close()
            return None
        
        # Get messages
        cursor.execute("""
            SELECT role, content, timestamp, metadata
            FROM messages
            WHERE session_id = ?
            ORDER BY timestamp ASC
        """, (session_id,))
        
        messages = []
        for msg_row in cursor.fetchall():
            messages.append({
                "role": msg_row["role"],
                "content": msg_row["content"],
                "timestamp": msg_row["timestamp"],
                "metadata": json.loads(msg_row["metadata"]) if msg_row["metadata"] else {}
            })
        
        conn.close()
        
        return {
            "id": row["id"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
            "metadata": json.loads(row["metadata"]) if row["metadata"] else {},
            "log_dir": row["log_dir"],
            "messages": messages
        }
    
    def list_sessions(self, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """List all sessions"""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT s.*, COUNT(m.id) as message_count
            FROM sessions s
            LEFT JOIN messages m ON s.id = m.session_id
            GROUP BY s.id
            ORDER BY s.updated_at DESC
            LIMIT ? OFFSET ?
        """, (limit, offset))
        
        sessions = []
        for row in cursor.fetchall():
            sessions.append({
                "id": row["id"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
                "metadata": json.loads(row["metadata"]) if row["metadata"] else {},
                "message_count": row["message_count"]
            })
        
        conn.close()
        return sessions
    
    def update_session(self, session_id: str, metadata: Dict[str, Any]):
        """Update session metadata"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE sessions
            SET metadata = ?, updated_at = ?
            WHERE id = ?
        """, (json.dumps(metadata), datetime.utcnow().isoformat(), session_id))
        
        conn.commit()
        conn.close()
    
    def add_message(self, session_id: str, role: str, content: str, metadata: Optional[Dict] = None):
        """Add message to session"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        timestamp = datetime.utcnow().isoformat()
        
        cursor.execute("""
            INSERT INTO messages (session_id, role, content, timestamp, metadata)
            VALUES (?, ?, ?, ?, ?)
        """, (session_id, role, content, timestamp, json.dumps(metadata or {})))
        
        # Update session updated_at
        cursor.execute("""
            UPDATE sessions SET updated_at = ? WHERE id = ?
        """, (timestamp, session_id))
        
        conn.commit()
        conn.close()
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a session and its messages"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            # Delete messages first (cascade should handle this, but being explicit)
            cursor.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
            
            # Delete session
            cursor.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
            
            conn.commit()
            conn.close()
            
            # Delete log directory
            session_log_dir = self.log_dir / "sessions" / session_id
            if session_log_dir.exists():
                import shutil
                shutil.rmtree(session_log_dir)
            
            logger.info(f"Deleted session: {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete session {session_id}: {e}")
            return False
    
    def cleanup_old_sessions(self, days: int = 10):
        """Delete sessions older than specified days"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        cutoff_str = cutoff_date.isoformat()
        
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        # Get old session IDs
        cursor.execute("SELECT id FROM sessions WHERE updated_at < ?", (cutoff_str,))
        old_sessions = [row[0] for row in cursor.fetchall()]
        
        conn.close()
        
        # Delete each old session
        deleted_count = 0
        for session_id in old_sessions:
            if self.delete_session(session_id):
                deleted_count += 1
        
        logger.info(f"Cleaned up {deleted_count} old sessions (older than {days} days)")
        return deleted_count
