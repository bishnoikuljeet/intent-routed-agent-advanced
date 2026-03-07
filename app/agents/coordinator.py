from typing import Dict, Any
from langchain_core.messages import HumanMessage, SystemMessage
from app.schemas.state import ConversationState
from app.core.logging import logger
from datetime import datetime
import uuid


class CoordinatorAgent:
    def __init__(self):
        self.name = "coordinator"
    
    async def coordinate(self, state: ConversationState) -> ConversationState:
        logger.info_structured(
            "Coordinator agent started",
            conversation_id=state.get("conversation_id"),
            query=state.get("current_query")
        )
        
        if not state.get("conversation_id"):
            state["conversation_id"] = str(uuid.uuid4())
        
        if not state.get("metadata"):
            state["metadata"] = {}
        
        state["metadata"]["started_at"] = datetime.utcnow().isoformat()
        state["metadata"]["coordinator_timestamp"] = datetime.utcnow().isoformat()
        
        if not state.get("execution_trace"):
            state["execution_trace"] = {
                "processing_components": [],
                "agents_called": [],
                "tools_called": [],
                "timestamps": {}
            }
        
        state["execution_trace"]["agents_called"].append(self.name)
        state["execution_trace"]["timestamps"][self.name] = datetime.utcnow().isoformat()
        
        if not state.get("retry_count"):
            state["retry_count"] = 0
        
        if not state.get("max_retries"):
            state["max_retries"] = 2
        
        if not state.get("errors"):
            state["errors"] = []
        
        if not state.get("intent_history"):
            state["intent_history"] = []
        
        if not state.get("tool_history"):
            state["tool_history"] = []
        
        # Add current query to conversation history
        current_query = state.get("current_query", "")
        if current_query:
            if not state.get("messages"):
                state["messages"] = []
            
            # Add human message for current query
            state["messages"].append(HumanMessage(content=current_query))
            state["recent_messages"] = state["messages"][-5:]  # Keep last 5 messages
        
        logger.info_structured(
            "Coordinator agent completed",
            conversation_id=state["conversation_id"],
            metadata_keys=list(state["metadata"].keys()),
            messages_count=len(state.get("messages", []))
        )
        
        return state
