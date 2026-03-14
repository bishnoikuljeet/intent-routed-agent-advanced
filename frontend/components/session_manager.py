import streamlit as st
from typing import Optional, Dict, Any
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)


class SessionManager:
    def __init__(self, api_client, session_service):
        self.api_client = api_client
        self.session_service = session_service
    
    def render(self) -> Optional[str]:
        """Render session management sidebar and return current session ID"""
        
        st.sidebar.title("🗂️ Session Management")
        
        # Initialize session state
        if 'current_session_id' not in st.session_state:
            st.session_state.current_session_id = None
        
        # New session button
        if st.sidebar.button("🆕 New Session", use_container_width=True, type="primary"):
            self._create_new_session()
        
        st.sidebar.divider()
        
        # Session list
        st.sidebar.subheader("📋 Session History")
        
        sessions = self.session_service.list_sessions(limit=50)
        
        if not sessions:
            st.sidebar.info("No sessions yet. Create a new session to get started!")
            return st.session_state.current_session_id
        
        # Search sessions
        search_query = st.sidebar.text_input("🔍 Search sessions", placeholder="Search by content...", key="session_search")
        
        if search_query:
            sessions = self.session_service.search_sessions(search_query)
        
        # Display sessions
        for session in sessions:
            self._render_session_item(session)
        
        # Session stats
        st.sidebar.divider()
        st.sidebar.subheader("📊 Statistics")
        st.sidebar.metric("Total Sessions", len(sessions))
        
        if st.session_state.current_session_id:
            current_session = self.session_service.get_session(st.session_state.current_session_id)
            if current_session:
                message_count = len(current_session.get('messages', []))
                st.sidebar.metric("Messages in Current Session", message_count)
        
        return st.session_state.current_session_id
    
    def _create_new_session(self):
        """Create a new session"""
        try:
            # Create session via API
            response = self.api_client.create_session()
            session_id = response.get('session_id') or response.get('id')
            
            # Create local session record
            self.session_service.create_session(
                session_id=session_id,
                metadata={'created_via': 'ui'}
            )
            
            # Set as current session
            st.session_state.current_session_id = session_id
            st.session_state.messages = []
            
            st.sidebar.success(f"✅ New session created: {session_id[:8]}...")
            st.rerun()
            
        except Exception as e:
            logger.error(f"Failed to create session: {e}")
            st.sidebar.error(f"Failed to create session: {str(e)}")
    
    def _render_session_item(self, session: Dict[str, Any]):
        """Render a single session item"""
        session_id = session.get('id', 'unknown')
        created_at = session.get('created_at', '')
        updated_at = session.get('updated_at', '')
        messages = session.get('messages', [])
        
        # Format timestamps
        try:
            created_dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            if created_dt.tzinfo is None:
                created_dt = created_dt.replace(tzinfo=timezone.utc)
            created_local = created_dt.astimezone()
            created_str = created_local.strftime("%Y-%m-%d %H:%M")
        except:
            created_str = created_at[:16] if created_at else "Unknown"
        
        # Session container
        is_current = st.session_state.current_session_id == session_id
        
        with st.sidebar.container():
            col1, col2 = st.columns([3, 1])
            
            with col1:
                # Session button
                button_label = f"{'🟢' if is_current else '⚪'} {session_id[:8]}..."
                if st.button(button_label, key=f"session_{session_id}", use_container_width=True):
                    self._load_session(session_id)
            
            with col2:
                # Delete button
                if st.button("🗑️", key=f"delete_{session_id}"):
                    self._delete_session(session_id)
            
            # Session info
            st.caption(f"📅 {created_str} • 💬 {len(messages)} msgs")
            
            # Show first message preview if available
            if messages:
                first_msg = messages[0].get('content', '')
                preview = first_msg[:50] + "..." if len(first_msg) > 50 else first_msg
                st.caption(f"💭 {preview}")
        
        st.sidebar.divider()
    
    def _load_session(self, session_id: str):
        """Load a session"""
        try:
            # Get session from service
            session = self.session_service.get_session(session_id)
            
            if session:
                # Set as current session
                st.session_state.current_session_id = session_id
                
                # Load messages
                st.session_state.messages = session.get('messages', [])
                
                st.sidebar.success(f"✅ Loaded session: {session_id[:8]}...")
                st.rerun()
            else:
                st.sidebar.error("Session not found")
                
        except Exception as e:
            logger.error(f"Failed to load session: {e}")
            st.sidebar.error(f"Failed to load session: {str(e)}")
    
    def _delete_session(self, session_id: str):
        """Delete a session"""
        try:
            # Delete from service
            success = self.session_service.delete_session(session_id)
            
            if success:
                # Delete from API
                self.api_client.delete_session(session_id)
                
                # Clear current session if deleted
                if st.session_state.current_session_id == session_id:
                    st.session_state.current_session_id = None
                    st.session_state.messages = []
                
                st.sidebar.success(f"✅ Deleted session: {session_id[:8]}...")
                st.rerun()
            else:
                st.sidebar.error("Failed to delete session")
                
        except Exception as e:
            logger.error(f"Failed to delete session: {e}")
            st.sidebar.error(f"Failed to delete session: {str(e)}")
