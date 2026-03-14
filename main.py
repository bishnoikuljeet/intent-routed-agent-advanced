import uvicorn
from app.core.config import settings

if __name__ == "__main__":
    uvicorn.run(
        "app.api.app:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=False,
        log_level=settings.log_level.lower()
    )
