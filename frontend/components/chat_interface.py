import streamlit as st
from typing import Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ChatInterface:
    def __init__(self, api_client, autocomplete_service, session_service):
        self.api_client = api_client
        self.autocomplete_service = autocomplete_service
        self.session_service = session_service
    
    def render(self, session_id: Optional[str] = None):
        """Render the main chat interface"""
        
        # Initialize session state
        if 'messages' not in st.session_state:
            st.session_state.messages = []
        if 'current_query' not in st.session_state:
            st.session_state.current_query = ""
        if 'show_suggestions' not in st.session_state:
            st.session_state.show_suggestions = False
        
        # Load session messages if session_id provided
        if session_id and session_id != st.session_state.get('loaded_session_id'):
            session = self.session_service.get_session(session_id)
            if session:
                st.session_state.messages = session.get('messages', [])
                st.session_state.loaded_session_id = session_id
        
        # Display chat history
        self._render_chat_history()
        
        # Input area with autocomplete
        self._render_input_area(session_id)
    
    def _render_chat_history(self):
        """Render chat message history"""
        st.markdown("### 💬 Conversation")
        
        if not st.session_state.messages:
            st.info("👋 Welcome! Start by typing a query below or select from suggestions.")
            return
        
        # Display messages
        for message in st.session_state.messages:
            role = message.get('role', 'user')
            content = message.get('content', '')
            timestamp = message.get('timestamp', '')
            
            if role == 'user':
                with st.chat_message("user", avatar="�"):
                    st.markdown(content)
                    if timestamp:
                        st.caption(f"🕐 {timestamp}")
            else:
                with st.chat_message("assistant", avatar="🤖"):
                    st.markdown(content)
                    if timestamp:
                        st.caption(f"🕐 {timestamp}")
                    
                    # Show execution trace if available
                    if 'trace' in message:
                        self._render_inline_trace(message['trace'])
    
    def _handle_query_change(self):
        """Handle query input change for real-time autocomplete"""
        # This will be called when the text input changes
        # The main logic in _render_input_area will handle the rest
        pass
    
    def _render_inline_trace(self, trace: Dict[str, Any]):
        """Render execution trace inline with message"""
        with st.expander("📊 View Execution Trace", expanded=False):
            from .trace_viewer import TraceViewer
            trace_viewer = TraceViewer()
            trace_viewer.render(trace)
    
    def _render_input_area(self, session_id: Optional[str]):
        """Render input area with autocomplete"""
        
        # Initialize session state for autocomplete
        if 'current_query' not in st.session_state:
            st.session_state.current_query = ''
        if 'show_suggestions' not in st.session_state:
            st.session_state.show_suggestions = False
        if 'last_query_length' not in st.session_state:
            st.session_state.last_query_length = 0
        
        st.markdown("### 🔍 Ask a Question")
        
        col1, col2 = st.columns([5, 1])
        
        with col1:
            # Add clear instructions for user
            st.markdown("""
            <style>
            .autocomplete-hint {
                font-size: 0.8rem;
                color: #666;
                margin-bottom: 0.5rem;
            }
            </style>
            <div class="autocomplete-hint">💡 Type 2+ characters to see suggestions automatically</div>
            """, unsafe_allow_html=True)
            
            # Use text_input without key to avoid session state conflicts
            query = st.text_input(
                "Your Query",
                value=st.session_state.current_query,
                placeholder="Type your question here and press Enter...",
                label_visibility="collapsed"
            )
            
            # Detect changes and update state
            if query != st.session_state.current_query:
                st.session_state.current_query = query
                st.session_state.show_suggestions = len(query) >= 2
                st.rerun()
            
            # Show typing indicator
            if len(query) > 0 and len(query) < 2:
                st.caption("🔍 Type 2+ characters and press Enter for suggestions...")
        
        with col2:
            send_button = st.button("🚀 Send", use_container_width=True, type="primary")
        
        # Show autocomplete suggestions (Google-style dropdown)
        if st.session_state.get('show_suggestions', False) and len(st.session_state.get('current_query', '')) >= 2:
            self._render_autocomplete_suggestions()
        
        # Action buttons
        col_clear, col_help = st.columns(2)
        with col_clear:
            if st.button("🗑️ Clear Chat", use_container_width=True):
                st.session_state.messages = []
                st.session_state.current_query = ""
                st.rerun()
        
        # Process query on send button
        if send_button and query.strip():
            # Hide suggestions when processing
            st.session_state.show_suggestions = False
            self._process_query(query, session_id)
    
    def _render_autocomplete_suggestions(self):
        """Render Google-style autocomplete suggestions"""
        suggestions = self.autocomplete_service.get_suggestions(
            st.session_state.current_query,
            max_results=5
        )
        
        if suggestions:
            # Google-style suggestion box
            st.markdown("""
            <style>
            .suggestion-box {
                background: white;
                border: 1px solid #dfe1e5;
                border-radius: 8px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                margin-top: -10px;
                padding: 8px 0;
            }
            .suggestion-item {
                padding: 8px 16px;
                cursor: pointer;
                transition: background 0.1s;
            }
            .suggestion-item:hover {
                background: #f8f9fa;
            }
            .suggestion-text {
                font-size: 14px;
                color: #202124;
            }
            .suggestion-meta {
                font-size: 12px;
                color: #5f6368;
                margin-top: 2px;
            }
            </style>
            """, unsafe_allow_html=True)
            
            st.markdown("**💡 Suggestions:**")
            
            for i, suggestion in enumerate(suggestions, 1):
                # Create clickable suggestion
                col1, col2 = st.columns([5, 1])
                
                with col1:
                    st.markdown(f"**{i}.** {suggestion['text']}")
                    st.caption(f"📁 {suggestion['category']} • 🛠️ {suggestion['tool']}")
                
                with col2:
                    if st.button("Use", key=f"use_suggestion_{i}", use_container_width=True):
                        # Update the tracked query
                        st.session_state.current_query = suggestion['text']
                        st.session_state.show_suggestions = False
                        st.rerun()
            
            st.markdown("---")
            st.caption("💡 **Tip:** Select a suggestion or type your own query and press Enter")
    
    def _process_query(self, query: str, session_id: Optional[str]):
        """Process user query"""
        
        # Add user message
        user_message = {
            'role': 'user',
            'content': query,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        st.session_state.messages.append(user_message)
        
        # Show processing indicator
        with st.spinner("🔍 Processing your query..."):
            try:
                # Call API
                response = self.api_client.process_query(query, session_id)
                
                # Extract response data
                answer = response.get('answer', 'No answer received')
                trace = response.get('trace', {})
                confidence = response.get('confidence', 0.0)
                intent = response.get('intent', 'unknown')
                
                # Format answer with metadata
                answer_text = f"{answer}\n\n"
                answer_text += f"**Intent:** {intent} | **Confidence:** {confidence:.2%}"
                
                # Add assistant message
                assistant_message = {
                    'role': 'assistant',
                    'content': answer_text,
                    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'trace': trace,
                    'metadata': {
                        'intent': intent,
                        'confidence': confidence
                    }
                }
                st.session_state.messages.append(assistant_message)
                
                # Save messages to backend session
                if session_id:
                    try:
                        self.session_service.add_message(
                            session_id, 
                            user_message['role'], 
                            user_message['content'],
                            {'timestamp': user_message['timestamp']}
                        )
                        self.session_service.add_message(
                            session_id, 
                            assistant_message['role'], 
                            assistant_message['content'],
                            {
                                'timestamp': assistant_message['timestamp'],
                                'trace': assistant_message.get('trace'),
                                'metadata': assistant_message.get('metadata', {})
                            }
                        )
                    except Exception as e:
                        logger.error(f"Failed to save messages to session: {e}")
                
                # Clear input
                st.session_state.current_query = ""
                st.session_state.show_suggestions = False
                
                # Success notification
                st.success("✅ Query processed successfully!")
                
            except Exception as e:
                logger.error(f"Failed to process query: {e}")
                
                # Add error message
                error_message = {
                    'role': 'assistant',
                    'content': f"❌ **Error:** {str(e)}\n\nPlease try again or rephrase your query.",
                    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                st.session_state.messages.append(error_message)
                
                st.error(f"Failed to process query: {str(e)}")
        
        # Rerun to update UI
        st.rerun()
