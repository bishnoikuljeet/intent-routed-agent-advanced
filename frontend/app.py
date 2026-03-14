import streamlit as st
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from config import config
from services import APIClient, SessionService, AutoCompleteService
from components import ChatInterface, SessionManager, HelpPanel

# Page configuration
st.set_page_config(
    page_title=config.PAGE_TITLE,
    page_icon=config.PAGE_ICON,
    layout=config.LAYOUT,
    initial_sidebar_state="expanded"
)

# Custom CSS - Google-style autocomplete
st.markdown("""
<style>
    .stButton>button {
        width: 100%;
    }
    .stTextInput>div>div>input {
        font-size: 16px;
        border-radius: 24px;
        padding: 12px 20px;
        border: 1px solid #dfe1e5;
    }
    .stTextInput>div>div>input:focus {
        border-color: #4285f4;
        box-shadow: 0 1px 6px rgba(32,33,36,.28);
    }
    .chat-message {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    .user-message {
        background-color: #e3f2fd;
    }
    .assistant-message {
        background-color: #f5f5f5;
    }
    div[data-testid="stExpander"] {
        border: 1px solid #e0e0e0;
        border-radius: 0.5rem;
    }
    /* Google-style suggestion container */
    .suggestion-container {
        background: white;
        border: 1px solid #dfe1e5;
        border-radius: 8px;
        box-shadow: 0 4px 6px rgba(32,33,36,.28);
        margin-top: 8px;
        overflow: hidden;
    }
    .suggestion-item {
        padding: 12px 16px;
        border-bottom: 1px solid #f1f3f4;
        cursor: pointer;
        transition: background-color 0.1s;
    }
    .suggestion-item:hover {
        background-color: #f8f9fa;
    }
    .suggestion-item:last-child {
        border-bottom: none;
    }
    .suggestion-number {
        color: #5f6368;
        font-weight: 500;
        margin-right: 8px;
    }
    .suggestion-query {
        color: #202124;
        font-size: 14px;
    }
    .suggestion-meta {
        color: #5f6368;
        font-size: 12px;
        margin-top: 4px;
    }
</style>
""", unsafe_allow_html=True)

# Initialize services
@st.cache_resource
def init_services():
    """Initialize services (cached)"""
    api_client = APIClient(backend_url=config.BACKEND_URL)
    session_service = SessionService(storage_path="../data/sessions")
    
    # Get absolute path to sample prompts (one level up from frontend folder)
    prompts_path = Path(__file__).parent.parent / config.SAMPLE_PROMPTS_PATH
    autocomplete_service = AutoCompleteService(prompts_file=str(prompts_path))
    
    return api_client, session_service, autocomplete_service

# Main app
def main():
    # Initialize services
    api_client, session_service, autocomplete_service = init_services()
    
    # Header
    col1, col2, col3 = st.columns([6, 1, 1])
    
    with col1:
        st.title("🤖 Intent-Routed Agent Platform")
        st.caption("Production-grade multi-agent AI platform with MCP tool ecosystem")
    
    with col2:
        if st.button("❓ Help"):
            st.session_state.show_help = not st.session_state.get('show_help', False)
    
    with col3:
        # Backend health check
        health = api_client.health_check()
        if health.get('status') == 'healthy':
            st.success("🟢 Online")
        else:
            st.error("🔴 Offline")
    
    # Show help panel if requested
    if st.session_state.get('show_help', False):
        help_panel = HelpPanel()
        help_panel.render()
        return
    
    # Sidebar: Session management
    with st.sidebar:
        session_manager = SessionManager(api_client, session_service)
        current_session_id = session_manager.render()
    
    # Main area: Chat interface
    chat_interface = ChatInterface(api_client, autocomplete_service, session_service)
    chat_interface.render(session_id=current_session_id)
    
    # Footer
    st.divider()
    col1, col2, col3 = st.columns(3)
    with col1:
        st.caption("💡 Click Suggestions to see query options")
    with col2:
        st.caption("📊 View execution traces for insights")
    with col3:
        st.caption("🔄 Switch sessions to organize conversations")

if __name__ == "__main__":
    main()
