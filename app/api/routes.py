from fastapi import APIRouter, HTTPException
from app.schemas.models import QueryRequest, QueryResponse
from app.services.orchestrator import AgentOrchestrator
from app.services.session_manager import SessionManager
from app.core.logging import logger
from app.core.telemetry import telemetry
from app.core.cache import query_cache, embedding_cache, metrics_cache
from app.core.session_logger import SessionLogger
from typing import List, Dict, Any

router = APIRouter()
orchestrator = AgentOrchestrator()
session_manager = SessionManager()


@router.on_event("startup")
async def startup_event():
    await orchestrator.initialize()
    logger.info_structured("API routes initialized")


@router.post("/query", response_model=QueryResponse)
async def process_query(request: QueryRequest) -> QueryResponse:
    try:
        logger.info_structured(
            "API query received",
            query_length=len(request.query),
            has_conversation_id=request.conversation_id is not None
        )
        
        response = await orchestrator.process_query(request)
        
        return response
        
    except Exception as e:
        logger.error_structured(
            "API query failed",
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "intent-routed-agent-advanced",
        "initialized": orchestrator._initialized
    }


@router.get("/tools")
async def list_tools():
    if not orchestrator._initialized:
        await orchestrator.initialize()
    
    tools = orchestrator.tool_registry.list_all_tools()
    
    return {
        "tools": [
            {
                "name": tool.name,
                "description": tool.description,
                "server": tool.server,
                "capabilities": tool.capabilities
            }
            for tool in tools
        ],
        "total": len(tools)
    }


@router.get("/servers")
async def list_servers():
    if not orchestrator._initialized:
        await orchestrator.initialize()
    
    servers_info = {}
    for server_name, server in orchestrator.mcp_servers.items():
        servers_info[server_name] = {
            "tools": len(server.tools),
            "resources": len(server.resources),
            "prompts": len(server.prompts)
        }
    
    return {
        "servers": servers_info,
        "total": len(orchestrator.mcp_servers)
    }


@router.get("/metrics")
async def get_metrics():
    """Get telemetry metrics summary"""
    try:
        summary = telemetry.get_metrics_summary()
        
        return {
            "status": "success",
            "metrics": summary
        }
    except Exception as e:
        logger.error_structured("Failed to get metrics", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/metrics/reset")
async def reset_metrics():
    """Reset all telemetry metrics"""
    try:
        telemetry.reset_metrics()
        
        return {
            "status": "success",
            "message": "Metrics reset successfully"
        }
    except Exception as e:
        logger.error_structured("Failed to reset metrics", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cache/stats")
async def get_cache_stats():
    """Get cache statistics"""
    try:
        return {
            "status": "success",
            "caches": {
                "query_cache": query_cache.get_stats(),
                "embedding_cache": embedding_cache.get_stats(),
                "metrics_cache": metrics_cache.get_stats()
            }
        }
    except Exception as e:
        logger.error_structured("Failed to get cache stats", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cache/clear")
async def clear_cache():
    """Clear all caches"""
    try:
        query_cache.clear()
        embedding_cache.clear()
        metrics_cache.clear()
        
        return {
            "status": "success",
            "message": "All caches cleared successfully"
        }
    except Exception as e:
        logger.error_structured("Failed to clear cache", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# Session Management Endpoints

@router.post("/sessions")
async def create_session(metadata: Dict[str, Any] = None):
    """Create a new session"""
    try:
        session = session_manager.create_session(metadata=metadata)
        
        logger.info_structured(
            "Session created",
            session_id=session["id"]
        )
        
        return session
        
    except Exception as e:
        logger.error_structured("Failed to create session", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions")
async def list_sessions(limit: int = 50, offset: int = 0):
    """List all sessions"""
    try:
        sessions = session_manager.list_sessions(limit=limit, offset=offset)
        
        return {
            "sessions": sessions,
            "total": len(sessions)
        }
        
    except Exception as e:
        logger.error_structured("Failed to list sessions", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{session_id}")
async def get_session(session_id: str):
    """Get session details"""
    try:
        session = session_manager.get_session(session_id)
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return session
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error_structured("Failed to get session", error=str(e), session_id=session_id)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    """Delete a session"""
    try:
        success = session_manager.delete_session(session_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Session not found or deletion failed")
        
        return {
            "status": "success",
            "message": f"Session {session_id} deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error_structured("Failed to delete session", error=str(e), session_id=session_id)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sessions/cleanup")
async def cleanup_old_sessions(days: int = 10):
    """Cleanup sessions older than specified days"""
    try:
        deleted_count = session_manager.cleanup_old_sessions(days=days)
        
        return {
            "status": "success",
            "message": f"Deleted {deleted_count} old sessions",
            "deleted_count": deleted_count
        }
        
    except Exception as e:
        logger.error_structured("Failed to cleanup sessions", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
