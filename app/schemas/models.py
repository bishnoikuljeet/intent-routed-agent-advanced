from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from enum import Enum


class IntentType(str, Enum):
    METRICS_LOOKUP = "metrics_lookup"
    KNOWLEDGE_LOOKUP = "knowledge_lookup"
    CALCULATION_COMPARE = "calculation_compare"
    SYSTEM_QUESTION = "system_question"
    DATA_VALIDATION = "data_validation"
    DATABASE_QUERY = "database_query"
    GENERAL_QUERY = "general_query"


class ToolMetadata(BaseModel):
    name: str
    description: str
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]
    capabilities: List[str]
    server: str
    timeout: int = 30


class ExecutionStep(BaseModel):
    step_number: int
    description: str
    tool_name: str
    tool_params: Dict[str, Any]
    parallel_group: Optional[int] = None


class ExecutionPlan(BaseModel):
    steps: List[ExecutionStep]
    estimated_duration: float
    requires_parallel: bool = False


class ToolResult(BaseModel):
    tool_name: str
    success: bool
    result: Any
    error: Optional[str] = None
    error_type: Optional[str] = None  # "not_found", "validation_failed", "execution_failed", "configuration_error"
    latency_ms: float
    metadata: Dict[str, Any] = Field(default_factory=dict)


class IntentClassification(BaseModel):
    intent: IntentType
    confidence: float
    entities: Dict[str, Any] = Field(default_factory=dict)
    reasoning: str


class ReasoningOutput(BaseModel):
    analysis: str
    conclusion: str
    supporting_evidence: List[str]
    confidence: float


class SelfEvaluation(BaseModel):
    quality_score: float
    confidence_score: float
    completeness_score: float
    reasoning_valid: bool
    issues_found: List[str] = Field(default_factory=list)
    should_retry: bool = False
    retry_reason: Optional[str] = None


class QueryRequest(BaseModel):
    query: str
    conversation_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class QueryResponse(BaseModel):
    answer: str
    confidence: float
    intent: str = "unknown"
    trace: Dict[str, Any]
    conversation_id: str
    language: str
    execution_time_ms: float
    metadata: Dict[str, Any] = Field(default_factory=dict)
