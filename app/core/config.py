from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Main LLM credentials
    azure_openai_api_key: str
    azure_openai_endpoint: str
    azure_openai_deployment: str = "gpt-4o-mini"
    azure_openai_api_version: str = "2024-02-15-preview"
    
    # Embedding credentials (can be separate or same as main)
    azure_embedding_openai_api_key: str = ""
    azure_embedding_openai_endpoint: str = ""
    azure_embedding_openai_deployment: str = "text-embedding-3-small"
    azure_embedding_openai_api_version: str = "2024-02-01"
    
    langchain_tracing_v2: bool = True
    langchain_endpoint: str = "https://api.smith.langchain.com"
    langchain_api_key: str = ""
    langchain_project: str = "intent-routed-agent-advanced"
    
    log_level: str = "INFO"
    max_retries: int = 2
    cache_ttl_seconds: int = 300
    memory_summary_threshold: int = 10
    max_conversation_history: int = 50
    
    embedding_dimension: int = 1536
    vector_store_path: str = "data/vector_store"
    cache_path: str = "data/cache"
    docs_path: str = "data/docs"
    
    api_host: str = "0.0.0.0"
    api_port: int = 8001
    
    max_parallel_tools: int = 5
    tool_timeout_seconds: int = 30
    
    confidence_threshold: float = 0.7
    low_confidence_retry_enabled: bool = True
    
    # Database configuration - Sales DB
    sales_db_host: str = "localhost"
    sales_db_port: int = 3306
    sales_db_name: str = "sales"
    sales_db_user: str = "readonly_user"
    sales_db_password: str = ""
    
    # Database configuration - Inventory DB
    inventory_db_host: str = "localhost"
    inventory_db_port: int = 3306
    inventory_db_name: str = "inventory"
    inventory_db_user: str = "readonly_user"
    inventory_db_password: str = ""


settings = Settings()

# Use main credentials for embedding if separate ones not provided
if not settings.azure_embedding_openai_api_key:
    settings.azure_embedding_openai_api_key = settings.azure_openai_api_key
if not settings.azure_embedding_openai_endpoint:
    settings.azure_embedding_openai_endpoint = settings.azure_openai_endpoint
