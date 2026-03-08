# Architecture Documentation
## Intent-Routed Agent Advanced

**Version**: 1.0  
**Last Updated**: March 2026

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Core Design Principles](#core-design-principles)
3. [Architecture Layers](#architecture-layers)
4. [Multi-Agent System](#multi-agent-system)
5. [LLM-Driven Tool Selection](#llm-driven-tool-selection)
6. [MCP Tool Ecosystem](#mcp-tool-ecosystem)
7. [Memory & Context Management](#memory--context-management)
8. [Language Processing Pipeline](#language-processing-pipeline)
9. [Execution Flow](#execution-flow)
10. [Retry & Failure Handling](#retry--failure-handling)
11. [Observability & Telemetry](#observability--telemetry)
12. [Data Flow Diagrams](#data-flow-diagrams)
13. [Technology Stack](#technology-stack)
14. [Scalability & Performance](#scalability--performance)

---

## System Overview

The Intent-Routed Agent Advanced is a **production-grade multi-agent AI platform** that demonstrates modern AI engineering practices. The system processes user queries through a sophisticated pipeline of specialized agents, each responsible for a specific aspect of query understanding, planning, execution, and response generation.

### Key Characteristics

- **LLM-Driven Architecture**: Uses LLM reasoning for all decision-making, avoiding hardcoded rules
- **Tool-Agnostic Design**: Adapts to any MCP tool ecosystem without code changes
- **Data-Agnostic Processing**: No assumptions about data schemas or document structures
- **Adaptive Workflows**: Multi-agent orchestration adjusts based on query complexity
- **Production-Ready**: Comprehensive error handling, observability, and resilience patterns

---

## Core Design Principles

### 1. LLM Reasoning Over Rules

**Traditional Approach (Avoided)**:
```python
# ❌ Hardcoded pattern matching
if "latency" in query and "service" in query:
    intent = "metrics_lookup"
    tools = ["service_metrics", "latency_history"]
```

**Our Approach**:
```python
# ✅ LLM-driven reasoning
intent = await llm.classify_intent(
    query=query,
    available_intents=intent_registry
)
tools = await llm.select_tools(
    query=query,
    intent=intent,
    tool_descriptions=tool_registry
)
```

### 2. Tool-Agnostic Architecture

The system discovers and selects tools dynamically through:
- **Semantic Search**: Tools are embedded and retrieved based on semantic similarity
- **LLM Reasoning**: Tool selection is based on LLM understanding of tool descriptions
- **Dynamic Registry**: Tools can be added/removed without code changes

### 3. Data-Agnostic Processing

- No hardcoded document schemas
- Semantic retrieval over keyword matching
- Adaptive chunking strategies
- Flexible metadata handling

### 4. Separation of Concerns

Each agent has a single, well-defined responsibility:
- **Coordinator**: Workflow orchestration
- **Intent**: Classification
- **Planner**: Execution planning
- **Executor**: Tool execution
- **Aggregator**: Result combination
- **Reasoning**: Analysis
- **Evaluation**: Quality assessment
- **Answer**: Response generation

---

## Architecture Layers

```
┌─────────────────────────────────────────────────────────────┐
│                     Presentation Layer                      │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐  │
│  │  Streamlit UI   │  │   FastAPI REST  │  │  CLI Tool   │  │
│  └─────────────────┘  └─────────────────┘  └─────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                    Orchestration Layer                      │
│   ┌─────────────────────────────────────────────────────┐   │
│   │        AgentOrchestrator (Main Entry Point)         │   │
│   │         - Initializes all components                │   │
│   │         - Manages agent lifecycle                   │   │
│   │         - Coordinates workflow execution            │   │
│   └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                        Agent Layer                          │
│     ┌───────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐    │
│     │Coordinator│→│  Intent  │→│ Planner  │→│ Executor │    │
│     └───────────┘ └──────────┘ └──────────┘ └──────────┘    │
│                                                   ↓         │
│     ┌───────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐    │
│     │  Answer   │←│Evaluation│←│Reasoning │←│Aggregator│    │
│     └───────────┘ └──────────┘ └──────────┘ └──────────┘    │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                      Service Layer                          │
│    ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐    │
│    │   Memory    │  │   Language  │  │  Tool Discovery │    │
│    │   Manager   │  │  Processor  │  │     Service     │    │
│    └─────────────┘  └─────────────┘  └─────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                     Integration Layer                       │
│  ┌───────────────────────────────────────────────────────┐  │
│  │              MCP Tool Ecosystem                       │  │
│  │   ┌─────────────┐ ┌────────────┐ ┌────────────┐       │  │
│  │   │Observability│ │ Knowledge  │ │  Language  │ ...   │  │
│  │   │    Server   │ │   Server   │ │   Server   │       │  │
│  │   └─────────────┘ └────────────┘ └────────────┘       │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                      Data Layer                             │
│    ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐    │
│    │    FAISS    │  │   Session   │  │   Tool Vector   │    │
│    │Vector Store │  │   Storage   │  │      Store      │    │
│    └─────────────┘  └─────────────┘  └─────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

---

## Multi-Agent System

### Agent Workflow Pipeline

```
┌─────────────────────────────────────────────────────────────┐
│                      User Query Input                       │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                  Language Processing Layer                  │
│  • Detect language (LLM-based)                              │
│  • Normalize and sanitize input                             │
│  • Detect prompt injection attempts                         │
│  • Translate to English (if needed)                         │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                     Memory Manager                          │
│  • Retrieve relevant conversation history                   │
│  • Summarize older messages (if threshold exceeded)         │
│  • Semantic search over past interactions                   │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                   Coordinator Agent                         │
│  • Initialize workflow state                                │
│  • Attach request metadata                                  │
│  • Start execution trace                                    │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                     Intent Agent                            │
│  • LLM-based intent classification                          │
│  • Entity extraction                                        │
│  • Intent categories:                                       │
│    - metrics_lookup                                         │
│    - knowledge_lookup                                       │
│    - calculation_compare                                    │
│    - system_question                                        │
│    - general_query                                          │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                     Planner Agent                           │
│  • Query tool registry (semantic search)                    │
│  • LLM selects relevant tools                               │
│  • Generate step-by-step execution plan                     │
│  • Identify parallel execution opportunities                │
│  • Estimate execution duration                              │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                    Executor Agent                           │
│  • Execute tools via MCP protocol                           │
│  • Parallel execution (asyncio.gather)                      │
│  • Sequential execution (for dependencies)                  │
│  • Retry logic with exponential backoff                     │
│  • Timeout handling (30s default)                           │
│  • Track execution metrics                                  │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                   Aggregator Agent                          │
│  • Combine tool results                                     │
│  • Structure data for reasoning                             │
│  • Identify patterns and key findings                       │
│  • Handle partial failures                                  │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                   Reasoning Agent                           │
│  • Analyze aggregated data                                  │
│  • Apply domain knowledge                                   │
│  • Draw logical conclusions                                 │
│  • Compare against thresholds                               │
│  • Provide supporting evidence                              │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                 Self-Evaluation Agent                       │
│  • Assess answer quality                                    │
│  • Compute confidence score                                 │
│  • Validate reasoning                                       │
│  • Determine if retry needed                                │
│  • Max retries: 2                                           │
└─────────────────────────────────────────────────────────────┘
                              ↓
                    ┌──────────────────┐
                    │ Confidence < 0.7 │
                    │ AND retries < 2? │
                    └──────────────────┘
                       Yes ↓    ↓ No
                           ↓    ↓
                    ┌──────┘    └──────┐
                    ↓                  ↓
            ┌───────────────┐  ┌──────────────┐
            │ Retry from    │  │ Continue to  │
            │ Planner Agent │  │ Answer Agent │
            └───────────────┘  └──────────────┘
                                      ↓
┌─────────────────────────────────────────────────────────────┐
│                     Answer Agent                            │
│  • Generate natural language response                       │
│  • Incorporate reasoning and evidence                       │
│  • Provide actionable information                           │
│  • Acknowledge uncertainty when appropriate                 │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                  Translation Layer                          │
│  • Translate answer to user's original language             │
│  • Preserve formatting and structure                        │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                    Final Response                            │
│  • Answer text                                              │
│  • Confidence score                                         │
│  • Execution trace                                          │
│  • Metadata (language, tools used, timing)                  │
└─────────────────────────────────────────────────────────────┘
```

### Agent Details

#### 1. Coordinator Agent
**File**: `app/agents/coordinator.py`

**Responsibilities**:
- Initialize workflow state
- Manage shared state across agents
- Attach request metadata (conversation_id, timestamp)
- Initialize execution trace
- Coordinate agent transitions

**Key Methods**:
```python
async def coordinate(state: AgentState) -> AgentState:
    # Initialize state
    # Attach metadata
    # Start trace
    return state
```

#### 2. Intent Agent
**File**: `app/agents/intent.py`

**Responsibilities**:
- Classify user intent using LLM
- Extract relevant entities
- Maintain intent history
- No hardcoded patterns

**Intent Categories**:
- `metrics_lookup`: Service metrics, performance queries
- `knowledge_lookup`: Documentation, policies, architecture
- `calculation_compare`: Calculations and comparisons
- `system_question`: System and tool queries
- `general_query`: General questions

**Key Methods**:
```python
async def classify_intent(query: str, context: dict) -> dict:
    # LLM-based classification
    # Entity extraction
    # Confidence scoring
    return {
        "intent": intent,
        "entities": entities,
        "confidence": confidence
    }
```

#### 3. Planner Agent
**File**: `app/agents/planner.py`

**Responsibilities**:
- Query tool registry using semantic search
- LLM selects relevant tools based on descriptions
- Generate step-by-step execution plan
- Identify parallel execution opportunities
- Estimate execution duration

**Planning Strategy**:
1. **Tool Discovery**: Semantic search over tool embeddings
2. **Tool Selection**: LLM reasons about which tools to use
3. **Plan Generation**: Create ordered execution steps
4. **Parallelization**: Group independent tools

**Key Methods**:
```python
async def create_plan(
    query: str,
    intent: str,
    entities: dict,
    tool_registry: ToolRegistry
) -> dict:
    # Discover relevant tools
    # LLM selects tools
    # Generate execution plan
    # Identify parallel groups
    return execution_plan
```

#### 4. Executor Agent
**File**: `app/agents/executor.py`

**Responsibilities**:
- Execute tools via MCP protocol
- Parallel execution using asyncio.gather
- Sequential execution for dependencies
- Retry logic with exponential backoff
- Timeout handling
- Track execution metrics

**Execution Modes**:
- **Parallel**: Tools with same `parallel_group` run concurrently
- **Sequential**: Tools without `parallel_group` run in order

**Key Methods**:
```python
async def execute_plan(plan: dict, mcp_servers: dict) -> list:
    # Group tools by parallel_group
    # Execute parallel groups concurrently
    # Execute sequential tools in order
    # Handle retries and timeouts
    return tool_results
```

#### 5. Aggregator Agent
**File**: `app/agents/aggregator.py`

**Responsibilities**:
- Combine tool execution results
- Structure data for reasoning
- Identify patterns and key findings
- Handle partial failures

**Key Methods**:
```python
async def aggregate_results(tool_results: list) -> dict:
    # Combine results
    # Extract key findings
    # Structure for reasoning
    return aggregated_data
```

#### 6. Reasoning Agent
**File**: `app/agents/reasoning.py`

**Responsibilities**:
- Analyze aggregated data
- Apply domain knowledge
- Draw logical conclusions
- Compare against thresholds
- Provide supporting evidence

**Key Methods**:
```python
async def reason(aggregated_data: dict, context: dict) -> dict:
    # Analyze data
    # Draw conclusions
    # Provide evidence
    return reasoning_output
```

#### 7. Self-Evaluation Agent
**File**: `app/agents/evaluation.py`

**Responsibilities**:
- Assess answer quality
- Compute confidence scores
- Validate reasoning
- Determine retry necessity
- Identify issues

**Evaluation Criteria**:
- Completeness of answer
- Relevance to query
- Evidence quality
- Reasoning coherence

**Key Methods**:
```python
async def evaluate(
    reasoning: dict,
    aggregated_data: dict,
    query: str
) -> dict:
    # Assess quality
    # Compute confidence
    # Determine retry
    return {
        "confidence": confidence,
        "should_retry": should_retry,
        "issues": issues
    }
```

#### 8. Answer Agent
**File**: `app/agents/answer.py`

**Responsibilities**:
- Generate natural language responses
- Incorporate reasoning and evidence
- Provide actionable information
- Acknowledge uncertainty appropriately

**Key Methods**:
```python
async def generate_answer(
    reasoning: dict,
    aggregated_data: dict,
    query: str,
    context: dict
) -> str:
    # Generate response
    # Include evidence
    # Format appropriately
    return answer
```

---

## LLM-Driven Tool Selection

### Tool Discovery Process

```
┌─────────────────────────────────────────────────────────────┐
│                    User Query                               │
│  "What is the latency of the auth service?"                 │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│              Step 1: Semantic Tool Search                   │
│  • Embed query using Azure OpenAI embeddings                │
│  • Search tool vector store (FAISS)                         │
│  • Retrieve top-k relevant tools (k=10)                     │
│                                                             │
│  Results:                                                   │
│  1. service_metrics (similarity: 0.92)                      │
│  2. latency_history (similarity: 0.88)                      │
│  3. service_status (similarity: 0.75)                       │
│  4. error_rate_lookup (similarity: 0.68)                    │
│  ...                                                        │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│           Step 2: LLM-Based Tool Selection                  │
│  Prompt to LLM:                                             │
│  "Given the query and these tool descriptions,              │
│   select the most relevant tools and explain why."          │
│                                                             │
│  LLM Response:                                              │
│  {                                                          │
│    "selected_tools": [                                      │
│      {                                                      │
│        "name": "service_metrics",                           │
│        "reason": "Directly retrieves current latency",      │
│        "params": {"service_name": "auth",                   │
│                   "metric_type": "latency"}                 │
│      }                                                      │
│    ],                                                       │
│    "execution_strategy": "single_tool_sufficient"           │
│  }                                                          │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│              Step 3: Execution Plan Generation              │
│  {                                                          │
│    "steps": [                                               │
│      {                                                      │
│        "step": 1,                                           │
│        "tool": "service_metrics",                           │
│        "params": {                                          │
│          "service_name": "auth",                            │
│          "metric_type": "latency"                           │
│        },                                                   │
│        "parallel_group": null                               │
│      }                                                      │
│    ],                                                       │
│    "reasoning": "Single tool call sufficient",              │
│    "estimated_duration_ms": 500                             │
│  }                                                          │
└─────────────────────────────────────────────────────────────┘
```

### Tool Registry Structure

**File**: `app/registry/tool_registry.py`

The tool registry maintains:
1. **Tool Metadata**: Name, description, parameters, server
2. **Tool Embeddings**: Semantic vectors for similarity search
3. **Tool Capabilities**: What each tool can do
4. **Tool Dependencies**: Inter-tool relationships

**Example Tool Entry**:
```python
{
    "name": "service_metrics",
    "description": "Retrieve current metrics for a service including latency, error rate, and throughput",
    "server": "ObservabilityMCPServer",
    "category": "monitoring",
    "input_schema": {
        "service_name": "string",
        "metric_type": "enum[latency, error_rate, throughput]"
    },
    "output_schema": {
        "value": "number",
        "threshold": "number",
        "unit": "string"
    },
    "capabilities": ["real-time", "threshold_checking"],
    "embedding": [0.123, 0.456, ...],  # 1536-dim vector
    "use_cases": ["monitoring", "alerting", "diagnostics"]
}
```

---

## MCP Tool Ecosystem

### Model Context Protocol (MCP)

MCP is a standardized protocol for exposing tools, resources, and prompts to AI systems. Our implementation uses MCP servers to provide a discoverable, tool-agnostic ecosystem.

### MCP Server Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    MCP Server Base                          │
│  • Tool registration                                        │
│  • Resource management                                      │
│  • Prompt templates                                         │
│  • Error handling                                           │
└─────────────────────────────────────────────────────────────┘
                              ↑
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
┌───────────────┐  ┌──────────────────┐  ┌─────────────────┐  ┌───────────────┐  ┌──────────────────┐
│ Observability │  │    Knowledge     │  │    Language     │  │    Utility    │  │     System       │
│    Server     │  │      Server      │  │     Server      │  │    Server     │  │     Server       │
│               │  │                  │  │                 │  │               │  │                  │
│ • Metrics     │  │ • Semantic       │  │ • Translation   │  │ • Compare     │  │ • Registry       │
│ • Latency     │  │   Search         │  │ • Detection     │  │ • Calculate   │  │ • Health         │
│ • Errors      │  │ • Documents      │  │ • Normalization │  │ • Statistics  │  │ • Workflow       │
│ • Status      │  │ • Policies       │  │                 │  │               │  │                  │
└───────────────┘  └──────────────────┘  └─────────────────┘  └───────────────┘  └──────────────────┘
```

### Available MCP Servers

#### 1. Observability Server
**File**: `app/mcp/observability_server.py`

**Tools**:
- `service_metrics`: Retrieve current service metrics
- `latency_history`: Get historical latency data
- `error_rate_lookup`: Query error rates
- `service_status`: Check service health

**Resources**:
- Service thresholds (latency, error rate, throughput)
- System metrics data

**Use Cases**:
- Real-time monitoring
- Anomaly detection
- Service diagnostics

#### 2. Knowledge Server
**File**: `app/mcp/knowledge_server.py`

**Tools**:
- `semantic_search`: Universal knowledge retrieval using natural language queries

**Resources**:
- Architecture documentation
- Operational runbooks
- Policy documents

**Use Cases**:
- Documentation lookup
- Policy queries
- Architecture questions

#### 3. Language Server
**File**: `app/mcp/language_server.py`

**Tools**:
- `detect_language`: Identify input language
- `translate_text`: Translate between languages
- `correct_typos`: Normalize and correct text
- `normalize_text`: Sanitize input

**Use Cases**:
- Multilingual support
- Input normalization
- Translation

#### 4. Utility Server
**File**: `app/mcp/utility_server.py`

**Tools**:
- `compare_values`: Compare numeric values
- `percentage_difference`: Calculate percentage changes
- `time_range_calculator`: Compute time durations
- `statistics_summary`: Generate statistical summaries

**Use Cases**:
- Calculations
- Comparisons
- Statistical analysis

#### 5. System Server
**File**: `app/mcp/system_server.py`

**Tools**:
- `tool_registry_lookup`: Query available tools
- `agent_health`: Check agent status
- `workflow_status`: Monitor workflow execution

**Use Cases**:
- System introspection
- Health checks
- Workflow monitoring

---

## Memory & Context Management

### Memory Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Memory Manager                            │
│  File: app/memory/manager.py                                │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ↓                     ↓                     ↓
┌───────────────┐  ┌──────────────────┐  ┌─────────────────┐
│    Recent     │  │   Conversation   │  │    Semantic     │
│   Messages    │  │     Summary      │  │    Retrieval    │
│               │  │                  │  │                 │
│ • Last N msgs │  │ • LLM-generated  │  │ • Vector search │
│ • Full text   │  │ • Older messages │  │ • Top-k similar │
│ • Metadata    │  │ • Compressed     │  │ • Context inject│
└───────────────┘  └──────────────────┘  └─────────────────┘
```

### Memory Workflow

**1. Message Storage**:
```python
# New message arrives
conversation_history.append({
    "role": "user",
    "content": query,
    "timestamp": datetime.now(),
    "metadata": {...}
})
```

**2. Summarization Trigger**:
```python
if len(conversation_history) > MEMORY_SUMMARY_THRESHOLD:
    # Summarize older messages
    summary = await llm.summarize(
        messages=conversation_history[:-N]
    )
    # Store summary
    conversation_summary = summary
    # Keep only recent messages
    conversation_history = conversation_history[-N:]
```

**3. Semantic Retrieval**:
```python
# Embed current query
query_embedding = await embeddings.embed(query)

# Search conversation history
similar_messages = vector_store.similarity_search(
    query_embedding,
    k=5
)

# Inject into context
context = {
    "recent_messages": conversation_history,
    "summary": conversation_summary,
    "relevant_past": similar_messages
}
```

### Memory Manager Implementation

**File**: `app/memory/manager.py`

**Key Features**:
- Automatic summarization when threshold exceeded
- Semantic search over historical messages
- Efficient embedding storage with FAISS
- Conversation context injection

**Methods**:
```python
class MemoryManager:
    async def add_message(self, message: dict):
        # Add to history
        # Check if summarization needed
        # Embed and store
        
    async def get_context(self, query: str) -> dict:
        # Retrieve recent messages
        # Get summary
        # Semantic search
        # Combine context
        
    async def summarize_history(self):
        # LLM summarization
        # Update summary
        # Prune old messages
```

---

## Language Processing Pipeline

### Multilingual Support

```
┌─────────────────────────────────────────────────────────────┐
│                    Input Processing                          │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│              Step 1: Language Detection                      │
│  • LLM-based detection (more accurate than libraries)       │
│  • Confidence scoring                                       │
│  • Fallback to langdetect library                           │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│           Step 2: Input Sanitization                         │
│  • Remove control characters                                │
│  • Normalize whitespace                                     │
│  • Validate length (max 5000 chars)                         │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│         Step 3: Prompt Injection Detection                   │
│  • Pattern matching for common attacks                      │
│  • LLM-based safety check                                   │
│  • Reject suspicious inputs                                 │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│            Step 4: Translation to English                    │
│  • If detected language != English                          │
│  • Use deep-translator library                              │
│  • Preserve intent and meaning                              │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│               Process in English                             │
│  • All agents work in English                               │
│  • Consistent processing                                    │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│         Step 5: Translation to Original Language             │
│  • Translate final answer back                              │
│  • Preserve formatting                                      │
│  • Maintain technical terms                                 │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                    Output Response                           │
└─────────────────────────────────────────────────────────────┘
```

### Language Processor

**File**: `app/language/processor.py`

**Supported Languages**:
- English, Spanish, French, German, Italian
- Portuguese, Russian, Chinese, Japanese, Korean
- Arabic, Hindi, and more

**Key Methods**:
```python
class LanguageProcessor:
    async def detect_language(self, text: str) -> str:
        # LLM-based detection
        # Fallback to langdetect
        
    async def sanitize_input(self, text: str) -> str:
        # Remove control chars
        # Normalize whitespace
        # Validate length
        
    async def detect_prompt_injection(self, text: str) -> bool:
        # Pattern matching
        # LLM safety check
        
    async def translate(
        self,
        text: str,
        source_lang: str,
        target_lang: str
    ) -> str:
        # Translation using deep-translator
```

---

## Execution Flow

### Complete Request Flow

```
1. Request Received (FastAPI/CLI/UI)
   ↓
2. AgentOrchestrator.process_query()
   ↓
3. Language Processing
   • Detect language
   • Sanitize input
   • Check for prompt injection
   • Translate to English
   ↓
4. Memory Manager
   • Retrieve conversation history
   • Summarize if needed
   • Semantic search for context
   ↓
5. Coordinator Agent
   • Initialize state
   • Attach metadata
   • Start execution trace
   ↓
6. Intent Agent
   • LLM classifies intent
   • Extract entities
   ↓
7. Planner Agent
   • Semantic search for tools
   • LLM selects tools
   • Generate execution plan
   ↓
8. Executor Agent
   • Execute tools (parallel/sequential)
   • Handle retries and timeouts
   • Collect results
   ↓
9. Aggregator Agent
   • Combine tool results
   • Structure data
   ↓
10. Reasoning Agent
    • Analyze data
    • Draw conclusions
    ↓
11. Self-Evaluation Agent
    • Assess quality
    • Compute confidence
    • Decide if retry needed
    ↓
12. Retry Logic (if needed)
    • If confidence < 0.7 AND retries < 2
    • Go back to Planner Agent
    ↓
13. Answer Agent
    • Generate natural language response
    ↓
14. Translation Layer
    • Translate to original language
    ↓
15. Response Returned
    • Answer text
    • Confidence score
    • Execution trace
    • Metadata
```

### State Management

**File**: `app/schemas/state.py`

The agent state is passed through the entire pipeline:

```python
class AgentState(TypedDict):
    # Input
    messages: List[BaseMessage]
    current_query: str
    conversation_id: str
    
    # Language Processing
    detected_language: str
    original_query: str
    
    # Intent Classification
    detected_intent: str
    extracted_entities: dict
    
    # Planning
    execution_plan: dict
    
    # Execution
    tool_results: list
    
    # Aggregation & Reasoning
    aggregated_data: dict
    reasoning_output: dict
    
    # Evaluation
    confidence_score: float
    should_retry: bool
    retry_count: int
    
    # Answer
    final_answer: str
    
    # Metadata
    metadata: dict
    execution_trace: dict
```

---

## Retry & Failure Handling

### Retry Strategy

**Controlled Retry Cycles**:
```python
MAX_RETRIES = 2
CONFIDENCE_THRESHOLD = 0.7

if confidence < CONFIDENCE_THRESHOLD and retry_count < MAX_RETRIES:
    # Retry from Planner Agent
    retry_count += 1
    return "retry"
else:
    # Continue to Answer Agent
    return "continue"
```

### Failure Handling Layers

**1. Tool Execution Level**:
```python
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type(ToolExecutionError)
)
async def execute_tool(tool_name, params):
    # Execute with timeout
    async with timeout(30):
        result = await mcp_server.call_tool(tool_name, params)
    return result
```

**2. Agent Level**:
```python
try:
    result = await agent.process(state)
except AgentError as e:
    logger.error_structured("Agent failed", error=str(e))
    # Graceful degradation
    result = fallback_response(state)
```

**3. Orchestrator Level**:
```python
try:
    response = await orchestrator.process_query(request)
except Exception as e:
    logger.error_structured("Orchestration failed", error=str(e))
    # Return error response with trace
    return ErrorResponse(
        error=str(e),
        trace=execution_trace
    )
```

### Circuit Breaker Pattern

**File**: `app/core/circuit_breaker.py`

Prevents cascading failures:
```python
class CircuitBreaker:
    def __init__(self, failure_threshold=5, timeout=60):
        self.failure_count = 0
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.last_failure_time = None
        self.state = "closed"  # closed, open, half-open
    
    async def call(self, func, *args, **kwargs):
        if self.state == "open":
            if time.time() - self.last_failure_time > self.timeout:
                self.state = "half-open"
            else:
                raise CircuitBreakerOpen()
        
        try:
            result = await func(*args, **kwargs)
            self.on_success()
            return result
        except Exception as e:
            self.on_failure()
            raise
```

---

## Observability & Telemetry

### LangSmith Integration

**Configuration**:
```python
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your_key
LANGCHAIN_PROJECT=intent-routed-agent-advanced
```

**Traced Information**:
- Agent workflow execution
- Tool calls and results
- LLM prompts and responses
- Reasoning steps
- Execution times
- Token usage

### Structured Logging

**File**: `app/core/logging.py`

All logs are JSON-formatted:
```json
{
  "timestamp": "2024-03-05T10:30:00Z",
  "level": "INFO",
  "message": "Intent classified",
  "conversation_id": "abc-123",
  "intent": "metrics_lookup",
  "confidence": 0.95,
  "execution_time_ms": 245
}
```

### Telemetry Metrics

**File**: `app/core/telemetry.py`

**Tracked Metrics**:
- Workflow duration
- Tool latency
- LLM latency
- Token usage
- Confidence scores
- Retry counts
- Error rates
- Cache hit rates

**Metrics Collection**:
```python
class Telemetry:
    def track_workflow_duration(self, duration_ms):
        self.metrics["workflow_duration"].append(duration_ms)
    
    def track_tool_latency(self, tool_name, latency_ms):
        self.metrics["tool_latency"][tool_name].append(latency_ms)
    
    def track_llm_latency(self, agent_name, latency_ms):
        self.metrics["llm_latency"][agent_name].append(latency_ms)
    
    def get_metrics_summary(self) -> dict:
        return {
            "avg_workflow_duration": mean(self.metrics["workflow_duration"]),
            "p95_workflow_duration": percentile(self.metrics["workflow_duration"], 95),
            "tool_latency": {
                tool: mean(latencies)
                for tool, latencies in self.metrics["tool_latency"].items()
            },
            "error_rate": self.calculate_error_rate()
        }
```

---

## Data Flow Diagrams

### Query Processing Data Flow

```
┌─────────────┐
│ User Query  │
└──────┬──────┘
       │
       ↓
┌─────────────────────────────────────────┐
│  Language Processor                     │
│  Input: "¿Cuál es la latencia?"        │
│  Output: {                              │
│    "detected_language": "es",           │
│    "translated_query": "What is the     │
│                         latency?",      │
│    "sanitized": true                    │
│  }                                      │
└──────┬──────────────────────────────────┘
       │
       ↓
┌─────────────────────────────────────────┐
│  Memory Manager                         │
│  Output: {                              │
│    "recent_messages": [...],            │
│    "summary": "Previous discussion...", │
│    "relevant_context": [...]            │
│  }                                      │
└──────┬──────────────────────────────────┘
       │
       ↓
┌─────────────────────────────────────────┐
│  Intent Agent                           │
│  Output: {                              │
│    "intent": "metrics_lookup",          │
│    "entities": {                        │
│      "metric_type": "latency"           │
│    },                                   │
│    "confidence": 0.95                   │
│  }                                      │
└──────┬──────────────────────────────────┘
       │
       ↓
┌─────────────────────────────────────────┐
│  Planner Agent                          │
│  Output: {                              │
│    "steps": [                           │
│      {                                  │
│        "tool": "service_metrics",       │
│        "params": {...}                  │
│      }                                  │
│    ]                                    │
│  }                                      │
└──────┬──────────────────────────────────┘
       │
       ↓
┌─────────────────────────────────────────┐
│  Executor Agent                         │
│  Output: [                              │
│    {                                    │
│      "tool": "service_metrics",         │
│      "result": {"value": 120, ...},     │
│      "success": true                    │
│    }                                    │
│  ]                                      │
└──────┬──────────────────────────────────┘
       │
       ↓
┌─────────────────────────────────────────┐
│  Aggregator Agent                       │
│  Output: {                              │
│    "key_findings": [...],               │
│    "structured_data": {...}             │
│  }                                      │
└──────┬──────────────────────────────────┘
       │
       ↓
┌─────────────────────────────────────────┐
│  Reasoning Agent                        │
│  Output: {                              │
│    "conclusion": "Latency is normal",   │
│    "evidence": [...],                   │
│    "confidence": 0.9                    │
│  }                                      │
└──────┬──────────────────────────────────┘
       │
       ↓
┌─────────────────────────────────────────┐
│  Self-Evaluation Agent                  │
│  Output: {                              │
│    "confidence": 0.9,                   │
│    "should_retry": false                │
│  }                                      │
└──────┬──────────────────────────────────┘
       │
       ↓
┌─────────────────────────────────────────┐
│  Answer Agent                           │
│  Output: "The latency is 120ms..."      │
└──────┬──────────────────────────────────┘
       │
       ↓
┌─────────────────────────────────────────┐
│  Translation Layer                      │
│  Output: "La latencia es 120ms..."      │
└──────┬──────────────────────────────────┘
       │
       ↓
┌─────────────┐
│  Response   │
└─────────────┘
```

---

## Vector Store Architecture

### Overview

The system uses **3 specialized vector stores** with organized subfolder structure for efficient semantic search and retrieval. Each vector store serves a distinct purpose and is automatically created on backend startup.

### Vector Store Structure

```
data/vector_store/
├── rag/                          # RAG Knowledge Base
│   ├── rag_index.faiss          # FAISS vector index
│   └── rag_documents.pkl        # Document metadata & chunks
│
├── conversations/                # Conversation Memory
│   ├── {conv-id-1}.index        # Per-conversation FAISS index
│   ├── {conv-id-1}.pkl          # Conversation metadata
│   └── ...                      # Multiple conversations
│
└── tools/                        # Tool Definitions
    ├── tool_definitions.index   # Tool search FAISS index
    └── tool_definitions.pkl     # Tool metadata (31 tools)
```

### 1. RAG Knowledge Base (`rag/`)

**Purpose**: Store and retrieve domain knowledge documents for answering user queries

**Location**: `data/vector_store/rag/`

**Contents**:
- **rag_index.faiss**: FAISS vector index of document chunks (1536-dimensional embeddings)
- **rag_documents.pkl**: Serialized document metadata, chunks, and categories

**Populated From**: `data/docs/` directory (`.txt` and `.md` files)

**Current Documents**:
- `architecture.md` - System architecture and microservices design
- `runbook_high_latency.md` - Troubleshooting procedures
- `slo_policy.md` - Service Level Objectives and policies
- `azure_openai.txt` - Azure OpenAI models and capabilities
- `faiss.txt` - FAISS vector search information
- `langgraph.txt` - LangGraph framework features

**Initialization**: 
- Automatic on backend startup via `AgentOrchestrator.initialize()`
- Documents chunked (1000 chars, 200 overlap) and embedded
- Supports incremental updates by adding files to `data/docs/`

**Usage**:
```python
# Semantic search over knowledge base
results = await rag_retriever.search(
    query="What is our SLO policy?",
    k=5
)
```

**Benefits**:
- ✅ **Centralized Knowledge**: Single source of truth for documentation
- ✅ **Semantic Search**: Natural language queries instead of keyword matching
- ✅ **Auto-Loading**: New documents automatically indexed on restart
- ✅ **Isolated Storage**: Clean separation from other vector stores

---

### 2. Conversation Memory (`conversations/`)

**Purpose**: Store conversation history with semantic search for context retrieval

**Location**: `data/vector_store/conversations/`

**Contents**:
- **{conversation_id}.index**: FAISS index per conversation
- **{conversation_id}.pkl**: Message history and metadata per conversation

**Populated From**: User and assistant messages during conversations

**Initialization**: 
- Created on first message in a new conversation
- Each conversation gets isolated vector store

**Usage**:
```python
# Retrieve relevant context from conversation history
context = await memory_manager.get_context(
    conversation_id="abc-123",
    query="What did we discuss about latency?"
)
```

**Benefits**:
- ✅ **Context Awareness**: Retrieve relevant past messages semantically
- ✅ **Conversation Isolation**: Each conversation has independent memory
- ✅ **Efficient Retrieval**: Vector search faster than full history scan
- ✅ **Scalability**: Handles long conversations with summarization

**Memory Management**:
- Recent messages kept in full
- Older messages summarized via LLM
- Semantic search retrieves relevant historical context
- Threshold-based summarization (configurable)

---

### 3. Tool Definitions (`tools/`)

**Purpose**: Enable semantic search for intelligent tool selection by LLM

**Location**: `data/vector_store/tools/`

**Contents**:
- **tool_definitions.index**: FAISS index of tool descriptions
- **tool_definitions.pkl**: Tool metadata (names, params, examples, keywords)

**Populated From**: Tool Registry (31 tools from 5 MCP servers)

**Initialization**: 
- Automatic on backend startup via `AgentOrchestrator._initialize_tool_vector_store()`
- All registered tools embedded with comprehensive descriptions

**Tool Coverage**:
- **Observability** (9 tools): Metrics, logs, alerts, SLO tracking
- **Knowledge** (5 tools): Semantic search, versioning, recommendations
- **Utility** (8 tools): Calculations, validation, parsing
- **System** (5 tools): Registry, health, workflow, profiling
- **Language** (4 tools): Detect, translate, correct, normalize

**Usage**:
```python
# Semantic tool discovery
relevant_tools = await planner.discover_tools(
    query="Check latency for auth service",
    top_k=10
)
# Returns: [service_metrics, latency_history, ...]
```

**Benefits**:
- ✅ **Dynamic Discovery**: LLM finds tools based on semantic similarity
- ✅ **Tool-Agnostic**: New tools automatically indexed without code changes
- ✅ **Better Selection**: Semantic matching vs keyword rules
- ✅ **Comprehensive Metadata**: Includes usage examples and keywords

---

### Vector Store Technology

**FAISS (Facebook AI Similarity Search)**:
- In-memory vector index for fast similarity search
- IndexFlatL2 for exact nearest neighbor search
- 1536-dimensional embeddings (Azure OpenAI text-embedding-3-small)
- Sub-millisecond search latency

**Serialization**:
- Python pickle for metadata storage
- Efficient load/save operations
- Preserves complex data structures

**Embeddings**:
- Azure OpenAI `text-embedding-3-small` model
- 1536 dimensions
- Batch processing for efficiency
- Cached to avoid redundant API calls

---

### Benefits of Organized Structure

**1. Clarity & Maintainability**
- Easy to identify which vector store is which
- Clear purpose for each subfolder
- Simplified debugging and inspection

**2. Independent Management**
- Backup/restore specific stores independently
- Clear/rebuild individual stores without affecting others
- Monitor storage usage per purpose

**3. Scalability**
- Add new specialized vector stores easily
- Each store can be optimized independently
- Future: Migrate to distributed storage per store

**4. Performance**
- Smaller, focused indices = faster search
- Isolated updates don't affect other stores
- Parallel initialization possible

**5. Data Governance**
- Clear data ownership and lifecycle
- Easier to implement retention policies
- Audit trail per vector store type

---

### Adding New Knowledge Documents

To add new documents to the RAG knowledge base:

1. **Add File**: Place `.txt` or `.md` file in `data/docs/`
2. **Restart Backend**: Documents automatically loaded and indexed
3. **Query**: Use `semantic_search` tool to retrieve information

**Example**:
```bash
# Add new document
echo "New policy content..." > data/docs/security_policy.md

# Restart backend
python main.py

# Query (via API or UI)
"What is our security policy?"
```

The system automatically:
- Detects new files in `data/docs/`
- Chunks documents (1000 chars, 200 overlap)
- Generates embeddings via Azure OpenAI
- Updates `rag_index.faiss` and `rag_documents.pkl`
- Makes content searchable via `semantic_search`

---

## Technology Stack

### Core Technologies

**Backend**:
- **Python 3.11+**: Modern Python with type hints
- **FastAPI**: High-performance async web framework
- **LangChain**: LLM orchestration framework
- **LangGraph**: Multi-agent workflow orchestration
- **Azure OpenAI**: LLM and embeddings

**Frontend**:
- **Streamlit**: Interactive web UI
- **Plotly**: Visualization
- **Rich**: CLI formatting

**Data & Storage**:
- **FAISS**: Vector similarity search
- **SQLite**: Session storage
- **JSON**: Configuration and data

**Tools & Utilities**:
- **Pydantic**: Data validation
- **Tenacity**: Retry logic
- **httpx**: Async HTTP client
- **python-dotenv**: Environment management

### Dependencies

See `pyproject.toml` and `requirements.txt` for complete dependency list.

---

## Scalability & Performance

### Performance Optimizations

**1. Parallel Tool Execution**:
```python
# Execute up to 5 tools concurrently
parallel_results = await asyncio.gather(
    *[execute_tool(tool) for tool in parallel_group],
    return_exceptions=True
)
```

**2. Caching**:
```python
# TTL-based caching (300s default)
@cache(ttl=300)
async def get_service_metrics(service_name):
    # Expensive operation
    return metrics
```

**3. Connection Pooling**:
```python
# Reuse HTTP connections
client = httpx.AsyncClient(
    limits=httpx.Limits(
        max_keepalive_connections=20,
        max_connections=100
    )
)
```

**4. Efficient Embeddings**:
```python
# Batch embedding generation
embeddings = await embed_batch(texts, batch_size=32)
```

**5. Async Operations**:
- All I/O operations are async
- Non-blocking throughout the pipeline
- Efficient resource utilization

### Scalability Considerations

**Horizontal Scaling**:
- Stateless API design
- Session data in external storage
- Can run multiple instances behind load balancer

**Vertical Scaling**:
- Async operations maximize CPU utilization
- Configurable parallel execution limits
- Memory-efficient vector storage

**Bottlenecks**:
- LLM API rate limits (Azure OpenAI)
- Vector store size (FAISS in-memory)
- Session storage (SQLite for small scale)

**Future Enhancements**:
- Redis for distributed caching
- PostgreSQL for session storage
- Kubernetes deployment
- Auto-scaling based on load

---

## Conclusion

The Intent-Routed Agent Advanced demonstrates a production-grade multi-agent AI architecture with:

✅ **LLM-driven decision making** throughout the pipeline  
✅ **Tool-agnostic design** that adapts to any MCP ecosystem  
✅ **Data-agnostic processing** with semantic retrieval  
✅ **Comprehensive observability** with LangSmith and structured logging  
✅ **Robust failure handling** with retries and circuit breakers  
✅ **Multilingual support** with translation pipeline  
✅ **Production-ready patterns** for scalability and resilience  

This architecture serves as a reference implementation for building adaptive, intelligent agent systems that can evolve with changing requirements and tool ecosystems.

---

**For implementation details, see the codebase at**: `c:\KB\intent_routed_agent_advanced\`

**For usage instructions, see**: [README.md](README.md)
