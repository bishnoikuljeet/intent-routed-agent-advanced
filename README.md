# Intent-Routed Agent Advanced

Production-grade multi-agent AI platform with LLM-driven tool selection, multilingual support, conversation memory, and adaptive workflow orchestration.

## 📺 Demo Video

### 🎥 Watch the Demo
- **[Watch on GitHub Pages](https://bishnoikuljeet.github.io/intent-routed-agent-advanced/assets/demos/demo.mp4)** 

**📹 Demo Video Location**: `assets/demos/demo.mp4`

---

## 🎯 Overview

This system demonstrates modern AI engineering practices through a sophisticated multi-agent architecture where specialized agents collaborate to process user queries. The platform uses **LLM reasoning** for dynamic tool discovery and selection, avoiding hardcoded rules and ensuring adaptability to changing tool ecosystems.

📖 **[Read the detailed Architecture Documentation →](ARCHITECTURE.md)**

## 🏗️ Architecture

### Core Design Principles

1. **LLM-Driven Tool Selection**: Tools are discovered and selected through semantic reasoning, not pattern matching
2. **Tool-Agnostic Design**: System adapts to any MCP tool ecosystem without code changes
3. **Data-Agnostic Processing**: No assumptions about vector store schemas or document structures
4. **Adaptive Workflows**: Multi-agent orchestration adjusts based on query complexity

### Agent Workflow

```
User Query
   ↓
Language Processing (detection, normalization, safety)
   ↓
Memory Manager (context retrieval, summarization)
   ↓
Coordinator Agent (workflow orchestration)
   ↓
Intent Agent (LLM-based classification, entity extraction)
   ↓
Planner Agent (dynamic tool selection via LLM reasoning)
   ↓
Executor Agent (parallel/sequential tool execution)
   ↓
Aggregator Agent (result combination)
   ↓
Reasoning Agent (analysis, conclusions)
   ↓
Self-Evaluation Agent (quality assessment, retry logic)
   ↓
Answer Agent (response generation)
   ↓
Translation Layer (multilingual output)
```

### Agent Responsibilities

**Coordinator Agent**
- Orchestrates overall workflow
- Manages shared state
- Initializes execution trace

**Intent Agent**
- Uses LLM to classify user intent
- Extracts relevant entities
- No hardcoded patterns or rules

**Planner Agent**
- **LLM-driven tool discovery** from registry
- Generates execution plans dynamically
- Identifies parallel execution opportunities
- Adapts to available tools

**Executor Agent**
- Executes tools via MCP protocol
- Supports parallel and sequential execution
- Implements retry logic with exponential backoff
- Handles timeouts gracefully

**Aggregator Agent**
- Combines tool results
- Structures data for reasoning
- Handles partial failures

**Reasoning Agent**
- Analyzes aggregated data
- Draws logical conclusions
- Provides supporting evidence

**Self-Evaluation Agent**
- Assesses answer quality
- Computes confidence scores
- Triggers retry when needed (max 2 retries)

**Answer Agent**
- Generates natural language responses
- Incorporates reasoning and evidence
- Acknowledges uncertainty appropriately

## 🛠️ MCP Tool Ecosystem

### Model Context Protocol (MCP)

The system uses **MCP servers** to expose tools in a standardized, discoverable way. Tools are selected dynamically by LLM reasoning over tool descriptions.

### Available MCP Servers

#### **Observability Server**
- `service_metrics`: Retrieve service metrics
- `latency_history`: Historical latency data
- `error_rate_lookup`: Query error rates
- `service_status`: Check service health

#### **Knowledge Server**
- `semantic_search`: Universal knowledge retrieval using semantic similarity

#### **Language Server**
- `detect_language`: Identify input language
- `translate_text`: Translate between languages
- `correct_typos`: Normalize and correct text
- `normalize_text`: Sanitize input

#### **Utility Server**
- `compare_values`: Compare numeric values
- `percentage_difference`: Calculate percentage changes
- `time_range_calculator`: Compute time durations
- `statistics_summary`: Generate statistical summaries

#### **System Server**
- `tool_registry_lookup`: Query available tools
- `agent_health`: Check agent status
- `workflow_status`: Monitor workflow execution

## 🧠 Memory System

### Conversation Memory

The memory system maintains conversation context with:

1. **Recent Messages**: Last N messages kept in full
2. **Conversation Summary**: Older messages summarized by LLM
3. **Semantic Retrieval**: Vector search over historical messages

### Memory Summarization

When conversation exceeds threshold (default: 10 messages):
- Older messages are summarized
- Summary stored in state
- Recent messages remain unchanged
- Summarized messages embedded and stored

### Semantic Memory Retrieval

For each query:
- Relevant past conversation segments retrieved
- Top-k similar messages found using embeddings
- Context injected into agent prompts

## 🌍 Multilingual Support

### Language Processing Pipeline

**Input Processing:**
1. Detect user's language (LLM-based)
2. Sanitize and normalize input
3. Detect prompt injection attempts
4. Translate to system language (English)

**Output Processing:**
1. Generate answer in English
2. Translate back to user's original language

### Safety Features

- Prompt injection detection
- Input length limits (5000 characters)
- Character sanitization
- Security logging

## 🔄 Controlled Retry Cycles

### Retry Mechanism

The system implements bounded retry loops to improve answer quality:

```
Execute Plan → Evaluate Results
   ↓
If confidence < 0.7 AND retries < 2
   ↓
Retry from Planner
```

**Retry Triggers:**
- Low confidence score (< 0.7)
- Quality issues identified
- Incomplete information

**Retry Limits:**
- Maximum retries: 2 (configurable)
- Prevents infinite loops
- Tracks retry count in state

## �️ Vector Store Architecture

The system uses **3 specialized vector stores** with organized subfolder structure for efficient semantic search and retrieval. All stores are automatically created on backend startup.

### Vector Store Structure

```
data/vector_store/
├── rag/                          # RAG Knowledge Base
│   ├── rag_index.faiss          # FAISS vector index
│   └── rag_documents.pkl        # Document metadata
│
├── conversations/                # Conversation Memory
│   ├── {conv-id}.index          # Per-conversation indices
│   └── {conv-id}.pkl            # Conversation metadata
│
└── tools/                        # Tool Definitions
    ├── tool_definitions.index   # Tool search index
    └── tool_definitions.pkl     # 31 tools metadata
```

### 1. RAG Knowledge Base (`rag/`)

**Purpose**: Store and retrieve domain knowledge documents

**Documents Loaded From**: `data/docs/` directory
- `architecture.md` - System architecture
- `runbook_high_latency.md` - Troubleshooting procedures
- `slo_policy.md` - Service Level Objectives
- `azure_openai.txt` - Azure OpenAI capabilities
- `faiss.txt` - FAISS information
- `langgraph.txt` - LangGraph framework

**How to Add Documents**:
1. Place `.txt` or `.md` file in `data/docs/`
2. Restart backend - auto-indexed
3. Query via `semantic_search` tool

**Benefits**:
- ✅ Centralized knowledge base
- ✅ Semantic search (natural language queries)
- ✅ Auto-loading on startup
- ✅ Isolated from other stores

### 2. Conversation Memory (`conversations/`)

**Purpose**: Store conversation history with semantic search

**Features**:
- Per-conversation vector stores
- Semantic retrieval of past messages
- LLM-based summarization for long conversations
- Context-aware responses

**Benefits**:
- ✅ Retrieve relevant past context
- ✅ Conversation isolation
- ✅ Efficient memory management
- ✅ Scalable for long conversations

### 3. Tool Definitions (`tools/`)

**Purpose**: Enable semantic tool discovery by LLM

**Contents**: 31 tools from 5 MCP servers
- Observability (9 tools)
- Knowledge (5 tools)
- Utility (8 tools)
- System (5 tools)
- Language (4 tools)

**Benefits**:
- ✅ Dynamic tool discovery
- ✅ Semantic matching vs keyword rules
- ✅ Tool-agnostic architecture
- ✅ Auto-populated on startup

### Technology

- **Engine**: FAISS (Facebook AI Similarity Search)
- **Embeddings**: Azure OpenAI `text-embedding-3-small`
- **Dimension**: 1536
- **Chunking**: 1000 chars, 200 overlap
- **Search**: Sub-millisecond semantic similarity

## ⚡ Parallel Tool Execution

### Execution Modes

**Parallel Execution:**
- Tools in same `parallel_group` run concurrently
- Uses `asyncio.gather` for parallelism
- Maximum parallel limit: 5 (configurable)

**Sequential Execution:**
- Tools without `parallel_group` run in order
- Useful for dependent operations

## 🛡️ Failure Handling

### Retry Strategy

- **Library**: tenacity
- **Max attempts**: 3
- **Backoff**: Exponential (1s, 2s, 4s, 8s, 10s max)

### Timeout Handling

- Tool timeout: 30 seconds (configurable)
- Graceful timeout with error reporting
- Partial result handling

### Error Propagation

- Errors captured at each layer
- Aggregated in state
- Included in execution trace
- User-friendly error messages

## 📊 Observability

### LangSmith Integration

Enable tracing in `.env`:
```
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your_key
LANGCHAIN_PROJECT=intent-routed-agent-advanced
```

**Traced Information:**
- Agent workflow execution
- Tool calls and results
- LLM prompts and responses
- Reasoning steps
- Execution times

### Structured Logging

All logs are JSON-formatted with:
```json
{
  "timestamp": "2024-03-05T10:30:00Z",
  "level": "INFO",
  "message": "Intent classified",
  "conversation_id": "abc-123",
  "intent": "metrics_lookup",
  "confidence": 0.95
}
```

### Telemetry Metrics

Tracked metrics:
- Workflow duration
- Tool latency
- LLM latency
- Token usage
- Confidence scores
- Retry counts

## 🚀 Getting Started

### Prerequisites

- Python 3.11+
- Azure OpenAI account
- LangSmith account (optional)

### Installation

1. **Clone the repository**
```bash
cd c:\KB\intent_routed_agent_advanced
```

2. **Install dependencies**

**Option A: Automated setup (Windows)**
```bash
setup_venvs.bat
```
This script will:
- Create separate virtual environments for backend and frontend
- Install all dependencies automatically
- Set up the project structure

**Option B: Manual installation**

Create and activate separate virtual environments:

**Backend environment:**
```bash
# Create backend virtual environment
python -m venv .venv-backend

# Activate backend environment
# For Command Prompt:
.venv-backend\Scripts\activate.bat

# For PowerShell:
.venv-backend\Scripts\Activate.ps1

# Install backend dependencies
pip install -e .

# Deactivate when done
deactivate
```

**Frontend environment:**
```bash
# Create frontend virtual environment
python -m venv frontend\.venv-frontend

# Activate frontend environment
# For Command Prompt:
frontend\.venv-frontend\Scripts\activate.bat

# For PowerShell:
frontend\.venv-frontend\Scripts\Activate.ps1

# Install frontend dependencies
pip install -r frontend\requirements.txt

# Deactivate when done
deactivate
```

**Note:** The project uses two separate virtual environments:
- `.venv-backend` - For backend API and agents
- `frontend\.venv-frontend` - For Streamlit frontend UI

**Troubleshooting virtual environment creation:**

If you get errors like "Unable to copy venvlauncher.exe", you're likely inside another virtual environment. Try these solutions:

**Solution 1: Deactivate all environments first**
```bash
# Deactivate conda if active
conda deactivate

# Deactivate any other virtualenv
deactivate

# Then create the environments
python -m venv .venv-backend
```

**Solution 2: Use full path to base Python**
```bash
# Find your base Python installation
where python

# Use the base Python (not from virtualenvs folder)
C:\Python311\python.exe -m venv .venv-backend
C:\Python311\python.exe -m venv frontend\.venv-frontend
```

**Solution 3: Use the automated script (recommended)**
```bash
# This handles environment conflicts automatically
setup_venvs.bat
```

3. **Configure environment**
```bash
cp .env.example .env
# Edit .env with your API keys
```

Required environment variables:

**Azure OpenAI (Main LLM):**
- `AZURE_OPENAI_API_KEY` - Your Azure OpenAI API key
- `AZURE_OPENAI_ENDPOINT` - Azure OpenAI endpoint URL
- `AZURE_OPENAI_DEPLOYMENT` - Deployment name (e.g., gpt-4o-mini)
- `AZURE_OPENAI_API_VERSION` - API version (e.g., 2025-04-01-preview)

**Azure OpenAI (Embeddings):**
- `AZURE_EMBEDDING_OPENAI_API_KEY` - API key for embeddings
- `AZURE_EMBEDDING_OPENAI_ENDPOINT` - Endpoint for embeddings
- `AZURE_EMBEDDING_OPENAI_DEPLOYMENT` - Embedding model (e.g., text-embedding-3-small)
- `AZURE_EMBEDDING_OPENAI_API_VERSION` - API version (e.g., 2024-02-01)

**LangSmith (Optional - for tracing):**
- `LANGCHAIN_API_KEY` - LangSmith API key
- `LANGCHAIN_TRACING_V2` - Enable tracing (true/false)
- `LANGCHAIN_PROJECT` - Project name for LangSmith

**System Configuration:**
- `LOG_LEVEL` - Logging level (INFO, DEBUG, WARNING, ERROR)
- `MAX_RETRIES` - Maximum retry attempts (default: 2)
- `CACHE_TTL_SECONDS` - Cache TTL in seconds (default: 300)
- `MEMORY_SUMMARY_THRESHOLD` - Messages before summarization (default: 10)
- `MAX_CONVERSATION_HISTORY` - Max conversation history (default: 50)
- `API_HOST` - API host (default: 0.0.0.0)
- `API_PORT` - API port (default: 8001)

### Running the Backend API

**Option 1: Using Python directly**
```bash
python main.py
```

**Option 2: Using batch file (Windows)**
```bash
start_backend.bat
```

Backend API available at `http://localhost:8001`

### Running the Frontend UI

**Option 1: Using Streamlit directly**
```bash
cd frontend
streamlit run app.py
```

**Option 2: Using batch file (Windows)**
```bash
start_frontend.bat
```

Frontend UI available at `http://localhost:8501`

### Running Both Services

```bash
start_both.bat
```

### Running the CLI

```bash
python cli/cli.py
```

### Running LangGraph Studio

**Option 1: Using batch file (Windows)**
```bash
start_langgraph_studio.bat
```

**Option 2: Using langgraph CLI directly**
```bash
langgraph dev
```

LangGraph Studio will be available at `http://localhost:8123`

**Testing the workflow:**
```bash
python scripts\run_langgraph_studio.py
```

### API Endpoints

**Query endpoint:**
```bash
POST http://localhost:8001/api/v1/query
Content-Type: application/json

{
  "query": "Is auth service latency above threshold?",
  "conversation_id": "optional-id"
}
```

**Health check:**
```bash
GET http://localhost:8001/api/v1/health
```

**List tools:**
```bash
GET http://localhost:8001/api/v1/tools
```

**List servers:**
```bash
GET http://localhost:8001/api/v1/servers
```

**Metrics:**
```bash
GET http://localhost:8001/api/v1/metrics
```

**Cache stats:**
```bash
GET http://localhost:8001/api/v1/cache/stats
```

## 📁 Project Structure

```
intent_routed_agent_advanced/
├── app/                                    # Core application package
│   ├── agents/                             # Specialized AI agents
│   │   ├── coordinator.py                  # Orchestrates workflow and manages state
│   │   ├── intent.py                       # LLM-based intent classification
│   │   ├── planner.py                      # Dynamic execution planning with tool selection
│   │   ├── executor.py                     # Parallel/sequential tool execution
│   │   ├── aggregator.py                   # Combines and structures tool results
│   │   ├── reasoning.py                    # Logical analysis and conclusion generation
│   │   ├── evaluation.py                   # Self-assessment and retry logic
│   │   ├── answer.py                       # Natural language response generation
│   │   ├── tool_first_answer_agent.py      # Alternative tool-first approach agent
│   │   ├── context_enhancer.py             # Enriches context with additional information
│   │   ├── quality_assurance.py            # Quality checks and validation
│   │   └── response_formatter.py           # Formats responses for different outputs
│   ├── api/                                # FastAPI REST API
│   │   ├── app.py                          # FastAPI application setup
│   │   └── routes.py                       # API endpoints and route handlers
│   ├── core/                               # Core utilities and configuration
│   │   ├── config.py                       # Settings and environment configuration
│   │   ├── logging.py                      # Structured JSON logging setup
│   │   ├── cache.py                        # TTL-based caching implementation
│   │   ├── circuit_breaker.py              # Circuit breaker pattern for resilience
│   │   ├── errors.py                       # Custom exception classes
│   │   ├── guardrails.py                   # Input validation and safety checks
│   │   ├── metrics.py                      # Performance metrics collection
│   │   ├── telemetry.py                    # Telemetry and observability
│   │   ├── request_context.py              # Request context management
│   │   └── session_logger.py               # Session-specific logging
│   ├── graph/                              # LangGraph workflow definitions
│   │   └── workflow.py                     # Multi-agent workflow implementation
│   ├── language/                           # Language processing
│   │   ├── processor.py                    # Multilingual processing pipeline
│   │   └── llm_detector.py                 # LLM-based language detection
│   ├── mcp/                                # Model Context Protocol servers
│   │   ├── base.py                         # Base MCP server implementation
│   │   ├── observability_server.py         # Metrics and monitoring tools
│   │   ├── knowledge_server.py             # Semantic search and knowledge retrieval
│   │   ├── language_server.py              # Translation and language tools
│   │   ├── utility_server.py               # Calculation and utility tools
│   │   └── system_server.py                # System and registry tools
│   ├── memory/                             # Conversation memory management
│   │   ├── manager.py                      # Memory manager with summarization
│   │   ├── vector_store.py                 # FAISS vector store for embeddings
│   │   ├── tool_vector_store.py            # Tool description vector store
│   │   └── comprehensive_tools.py          # Tool metadata and descriptions
│   ├── prompts/                            # LLM prompt templates
│   ├── rag/                                # Retrieval-Augmented Generation
│   │   └── retriever.py                    # Document retrieval with FAISS
│   ├── registry/                           # Tool registry
│   │   └── tool_registry.py                # Dynamic tool discovery and registration
│   ├── schemas/                            # Data models
│   │   ├── models.py                       # Pydantic request/response models
│   │   └── state.py                        # Agent state definitions
│   ├── services/                           # Business logic services
│   │   ├── orchestrator.py                 # Main orchestration service (ACTIVE)
│   │   ├── session_manager.py              # Session lifecycle management
│   │   ├── llm_service.py                  # LLM interaction service
│   │   ├── context_service.py              # Context enrichment service
│   │   └── tool_discovery_service.py       # Dynamic tool discovery
│   └── workflow/                           # LangGraph Studio integration
│       └── graph.py                        # Workflow visualization for LangGraph Studio
├── cli/                                    # Command-line interface
│   └── cli.py                              # Interactive CLI with Rich formatting
├── data/                                   # Persistent data storage
│   ├── docs/                               # Knowledge base documents (auto-loaded)
│   │   ├── architecture.md                 # System architecture documentation
│   │   ├── runbook_high_latency.md         # Troubleshooting runbook
│   │   ├── slo_policy.md                   # Service Level Objectives
│   │   ├── azure_openai.txt                # Azure OpenAI information
│   │   ├── faiss.txt                       # FAISS vector search info
│   │   └── langgraph.txt                   # LangGraph framework info
│   ├── sessions/                           # Session data and conversation history
│   │   ├── sessions.db                     # SQLite session database
│   │   └── sessions.json                   # JSON session backup
│   └── vector_store/                       # FAISS vector embeddings (3 stores)
│       ├── rag/                            # RAG knowledge base (auto-created)
│       │   ├── rag_index.faiss            # Document embeddings index
│       │   └── rag_documents.pkl          # Document metadata
│       ├── conversations/                  # Conversation memory (per-conversation)
│       │   ├── {conv-id}.index            # Per-conversation FAISS index
│       │   └── {conv-id}.pkl              # Conversation metadata
│       └── tools/                          # Tool definitions (auto-created)
│           ├── tool_definitions.index     # Tool search index
│           └── tool_definitions.pkl       # 31 tools metadata
├── docker/                                 # Docker deployment
│   ├── docker-compose.yml                  # Multi-container orchestration
│   └── .env.example                        # Docker environment template
├── frontend/                               # Streamlit web interface
│   ├── app.py                              # Main Streamlit application
│   ├── components/                         # UI components
│   │   ├── chat_interface.py               # Chat UI with message history
│   │   ├── help_panel.py                   # Help and example queries panel
│   │   ├── session_manager.py              # Session management UI
│   │   └── trace_viewer.py                 # Execution trace visualization
│   ├── services/                           # Frontend services
│   │   ├── api_client.py                   # Backend API client
│   │   ├── autocomplete_service.py         # Query autocomplete
│   │   ├── example_queries_service.py      # Example query management
│   │   └── session_service.py              # Session service client
│   ├── config.py                           # Frontend configuration
│   └── requirements.txt                    # Frontend dependencies
├── scripts/                                # Utility scripts
│   ├── cleanup_sessions.py                 # Clean old session data
│   ├── initialize_tool_vector_store.py     # Initialize tool embeddings
│   ├── populate_tool_vector_store.py       # Populate tool vector store
│   ├── run_langgraph_studio.py             # LangGraph Studio test runner
│   ├── setup.py                            # Project setup script
│   └── verify_installation.py              # Verify dependencies and config
├── .windsurf/                              # Windsurf IDE configuration
│   └── rules/                              # Custom IDE rules and settings
├── main.py                                 # Backend API entry point
├── pyproject.toml                          # Project metadata and dependencies
├── requirements.txt                        # Python dependencies (generated)
├── .env.example                            # Environment variables template
├── .gitignore                              # Git ignore patterns
├── Dockerfile                              # Docker image definition
├── langgraph.json                          # LangGraph Studio configuration
├── ALL_TOOLS_REGISTRY.py                   # Complete tool registry (31 tools)
├── sample_prompts.md                       # Example queries for all available tools
├── setup_venvs.bat                         # Setup virtual environments (Windows)
├── start_backend.bat                       # Start backend server (Windows)
├── start_frontend.bat                      # Start frontend UI (Windows)
├── start_both.bat                          # Start both services (Windows)
├── start_langgraph_studio.bat              # Start LangGraph Studio (Windows)
├── ARCHITECTURE.md                         # Detailed architecture documentation
└── README.md                               # This file
```

## 🔧 Configuration

Key settings in `.env`:

```bash
# Azure OpenAI
AZURE_OPENAI_API_KEY=your_key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT=gpt-4o-mini
AZURE_OPENAI_API_VERSION=2025-04-01-preview

# Azure Embeddings
AZURE_EMBEDDING_OPENAI_API_KEY=your_key
AZURE_EMBEDDING_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_EMBEDDING_OPENAI_DEPLOYMENT=text-embedding-3-small
AZURE_EMBEDDING_OPENAI_API_VERSION=2024-02-01

# LangSmith (optional)
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your_key
LANGCHAIN_PROJECT=intent-routed-agent-advanced

# System
LOG_LEVEL=INFO
MAX_RETRIES=2
CACHE_TTL_SECONDS=300
MEMORY_SUMMARY_THRESHOLD=10
MAX_CONVERSATION_HISTORY=50

# API
API_HOST=0.0.0.0
API_PORT=8001
```

## 📈 Performance Optimization

- **Parallel tool execution**: Up to 5 concurrent tools
- **Caching**: TTL-based caching (300s default)
- **Efficient embeddings**: Batch processing
- **Connection pooling**: Reused HTTP connections
- **Async operations**: Non-blocking I/O throughout

## 🎯 Example Queries

**Metrics lookup:**
```
"What is the latency of the auth service?"
"Is the payment service error rate above threshold?"
```

**Knowledge lookup:**
```
"What is our architecture for the payment service?"
"Show me the runbook for high latency issues"
```

**Calculation:**
```
"Compare auth service latency to its threshold"
"What's the percentage difference between current and baseline?"
```

**Multilingual:**
```
"¿Cuál es la latencia del servicio de autenticación?" (Spanish)
"Quelle est la latence du service d'authentification?" (French)
```

## 🏆 Key Features

✅ **LLM-driven tool selection** - No hardcoded rules  
✅ **Multi-agent orchestration** with LangGraph  
✅ **MCP-based tool ecosystem** (5 servers, 31 tools)  
✅ **Multilingual input/output** processing  
✅ **Conversation memory** with summarization  
✅ **RAG retrieval** with FAISS  
✅ **Parallel tool execution**  
✅ **Controlled retry cycles**  
✅ **Comprehensive failure handling**  
✅ **LangSmith observability**  
✅ **Structured JSON logging**  
✅ **Production-ready FastAPI** backend  
✅ **Streamlit UI** with real-time updates  
✅ **Interactive CLI**  
✅ **Tool-agnostic & data-agnostic** design  

## 🎨 LangGraph Studio Integration

Visualize and debug the workflow:

```bash
langgraph dev
```

Then open `http://localhost:8123` and select `agent_workflow`.

Or run the test script:
```bash
python run_langgraph_studio.py
```

## 📝 License

MIT License

## 🤝 Contributing

This is a demonstration project showcasing production-grade AI engineering practices with emphasis on:
- LLM reasoning over rule-based logic
- Tool-agnostic architecture
- Adaptive workflows
- Modern observability

---

**Built with**: Python 3.11+ • LangGraph • Azure OpenAI • FastAPI • Streamlit • FAISS • MCP
