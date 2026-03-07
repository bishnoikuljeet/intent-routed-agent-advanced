import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Backend API
    BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8001")
    API_VERSION = "v1"
    
    # UI Settings
    PAGE_TITLE = "Intent-Routed Agent Platform"
    PAGE_ICON = "🤖"
    LAYOUT = "wide"
    
    # Autocomplete
    AUTOCOMPLETE_MAX_SUGGESTIONS = 5
    AUTOCOMPLETE_MIN_SCORE = 0.3
    
    # Session
    SESSION_TIMEOUT_MINUTES = 60
    MAX_SESSIONS_DISPLAY = 50
    
    # Appearance
    DEFAULT_THEME = "light"
    
    # Paths
    SAMPLE_PROMPTS_PATH = "sample_prompts.md"
    
    # Performance
    AUTO_REFRESH_INTERVAL = 5000  # milliseconds
    
    @property
    def api_base_url(self):
        return f"{self.BACKEND_URL}/api/{self.API_VERSION}"

config = Config()
