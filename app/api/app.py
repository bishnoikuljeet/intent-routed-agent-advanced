from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router
from app.core.config import settings
from app.core.logging import logger

# Initialize LangSmith tracing
import os
if settings.langchain_tracing_v2 and settings.langchain_api_key:
    try:
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        os.environ["LANGCHAIN_API_KEY"] = settings.langchain_api_key
        os.environ["LANGCHAIN_PROJECT"] = settings.langchain_project
        os.environ["LANGCHAIN_ENDPOINT"] = settings.langchain_endpoint
        
        # Import and initialize LangSmith
        from langsmith import Client as LangSmithClient
        langsmith_client = LangSmithClient(
            api_url=settings.langchain_endpoint,
            api_key=settings.langchain_api_key
        )
        
        logger.info_structured(
            "LangSmith tracing initialized",
            project=settings.langchain_project,
            endpoint=settings.langchain_endpoint
        )
    except Exception as e:
        logger.warning_structured(
            "Failed to initialize LangSmith tracing",
            error=str(e)
        )
else:
    logger.info_structured("LangSmith tracing disabled")

app = FastAPI(
    title="Intent Routed Agent Advanced",
    description="Production-grade multi-agent AI platform with MCP tool ecosystem",
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/v1")


@app.on_event("startup")
async def startup():
    logger.info_structured(
        "Application starting",
        host=settings.api_host,
        port=settings.api_port
    )


@app.on_event("shutdown")
async def shutdown():
    logger.info_structured("Application shutting down")


@app.get("/")
async def root():
    return {
        "service": "Intent Routed Agent Advanced",
        "version": "0.1.0",
        "status": "running"
    }
