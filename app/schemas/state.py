from typing import Annotated, List, Dict, Any, Optional
from typing_extensions import TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class ConversationState(TypedDict):
    conversation_id: str
    messages: Annotated[List[BaseMessage], add_messages]
    recent_messages: List[BaseMessage]
    conversation_summary: Optional[str]
    intent_history: List[str]
    tool_history: List[Dict[str, Any]]
    user_language: str
    
    current_query: str
    original_query: str
    detected_intent: Optional[str]
    extracted_entities: Dict[str, Any]
    
    execution_plan: List[Dict[str, Any]]
    tool_results: List[Dict[str, Any]]
    aggregated_data: Dict[str, Any]
    reasoning_output: Optional[str]
    
    confidence_score: float
    retry_count: int
    max_retries: int
    
    final_answer: Optional[str]
    execution_trace: Dict[str, Any]
    
    errors: List[str]
    metadata: Dict[str, Any]
