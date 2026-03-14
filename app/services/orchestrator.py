from typing import Dict, Any, Optional
import os
from langchain_openai import AzureOpenAIEmbeddings
from app.agents.coordinator import CoordinatorAgent
from app.agents.intent import IntentAgent
from app.agents.planner import PlannerAgent
from app.agents.executor import ExecutorAgent
from app.agents.aggregator import AggregatorAgent
from app.agents.reasoning import ReasoningAgent
from app.agents.evaluation import SelfEvaluationAgent
from app.agents.tool_first_answer_agent import ToolFirstAnswerAgent
from app.memory.manager import MemoryManager
from app.language.processor import LanguageProcessor
from app.graph.workflow import MultiAgentWorkflow
from app.mcp.observability_server import ObservabilityMCPServer
from app.mcp.knowledge_server import KnowledgeMCPServer
from app.mcp.language_server import LanguageMCPServer
from app.mcp.utility_server import UtilityMCPServer
from app.mcp.system_server import SystemMCPServer
from app.registry.tool_registry import ToolRegistry
from app.rag.retriever import RAGRetriever
from app.services.tool_discovery_service import ToolDiscoveryService
from app.schemas.models import ToolMetadata, QueryRequest, QueryResponse
from app.core.config import settings
from app.core.logging import logger
from app.core.telemetry import telemetry
from app.core.request_context import set_request_id, generate_request_id
from datetime import datetime


class AgentOrchestrator:
    def __init__(self):
        self.embeddings = None
        self.rag_retriever = None
        self.memory_manager = None
        self.language_processor = None
        self.tool_registry = None
        self.tool_discovery_service = None
        self.mcp_servers = {}
        self.workflow = None
        
        self._initialized = False
    
    async def initialize(self):
        if self._initialized:
            return
        
        logger.info_structured("Initializing agent orchestrator")
        
        # Initialize LangSmith tracing for workflow
        if settings.langchain_tracing_v2 and settings.langchain_api_key:
            try:
                os.environ["LANGCHAIN_TRACING_V2"] = "true"
                os.environ["LANGCHAIN_API_KEY"] = settings.langchain_api_key
                os.environ["LANGCHAIN_PROJECT"] = settings.langchain_project
                os.environ["LANGCHAIN_ENDPOINT"] = settings.langchain_endpoint
                
                logger.info_structured(
                    "Orchestrator: LangSmith tracing enabled",
                    project=settings.langchain_project
                )
            except Exception as e:
                logger.warning_structured(
                    "Orchestrator: Failed to enable LangSmith tracing",
                    error=str(e)
                )
        
        self.embeddings = AzureOpenAIEmbeddings(
            azure_endpoint=settings.azure_embedding_openai_endpoint,
            api_key=settings.azure_embedding_openai_api_key,
            api_version=settings.azure_embedding_openai_api_version,
            deployment=settings.azure_embedding_openai_deployment,
        )
        
        self.rag_retriever = RAGRetriever(self.embeddings)
        logger.info_structured("RAG retriever instance created")
        
        # Initialize RAG with documents from data/docs directory
        logger.info_structured("Starting RAG document loading from data/docs")
        try:
            await self.rag_retriever.load_documents_from_directory("data/docs", force_reload=True)
            logger.info_structured("RAG document loading completed successfully")
        except Exception as rag_error:
            logger.error_structured(
                "RAG initialization failed, continuing without documents",
                error=str(rag_error),
                error_type=type(rag_error).__name__
            )
        
        self.memory_manager = MemoryManager()
        
        # Initialize language processor with LLM for intelligent detection
        intent_agent = IntentAgent()
        self.language_processor = LanguageProcessor(llm=intent_agent.llm)
        
        self.tool_registry = ToolRegistry()
        
        self._initialize_mcp_servers()
        
        self._register_tools()
        
        # Initialize tool discovery service with embeddings and pre-load all tools
        logger.info_structured("Initializing tool discovery service")
        self.tool_discovery_service = ToolDiscoveryService(embeddings=self.embeddings)
        await self.tool_discovery_service.initialize_tools()
        logger.info_structured("Tool discovery service initialized and tools cached")
        
        # Initialize tool vector store for semantic tool search
        await self._initialize_tool_vector_store()
        
        self._initialize_workflow()
        
        self._initialized = True
        
        logger.info_structured(
            "Agent orchestrator initialized",
            mcp_servers=len(self.mcp_servers),
            registered_tools=len(self.tool_registry.list_all_tools())
        )
    
    def _initialize_mcp_servers(self):
        self.mcp_servers["observability"] = ObservabilityMCPServer()
        self.mcp_servers["knowledge"] = KnowledgeMCPServer(self.rag_retriever)
        self.mcp_servers["language"] = LanguageMCPServer()
        self.mcp_servers["utility"] = UtilityMCPServer()
        self.mcp_servers["system"] = SystemMCPServer(self.tool_registry)
        
        logger.info_structured(
            "MCP servers initialized",
            servers=list(self.mcp_servers.keys())
        )
    
    def _register_tools(self):
        for server_name, server in self.mcp_servers.items():
            for tool_name, tool in server.tools.items():
                metadata = ToolMetadata(
                    name=tool.name,
                    description=tool.description,
                    input_schema=tool.input_schema,
                    output_schema=tool.output_schema,
                    capabilities=self._extract_capabilities(tool.description),
                    server=server_name,
                    timeout=30
                )
                self.tool_registry.register_tool(metadata)
        
        logger.info_structured(
            "Tools registered",
            total_tools=len(self.tool_registry.list_all_tools())
        )
    
    def _extract_capabilities(self, description: str) -> list[str]:
        capabilities = []
        
        # Return general category - semantic capability detection delegated to LLM layer
        return ["general"]
    
    async def _initialize_tool_vector_store(self):
        """Initialize tool vector store with all registered tools."""
        try:
            from app.memory.tool_vector_store import ToolVectorStore
            
            logger.info_structured("Initializing tool vector store")
            
            tool_vector_store = ToolVectorStore()
            populated_count = await tool_vector_store.populate_tool_definitions()
            
            logger.info_structured(
                "Tool vector store initialized",
                tools_populated=populated_count
            )
        except Exception as e:
            logger.warning_structured(
                "Tool vector store initialization failed, continuing without it",
                error=str(e),
                error_type=type(e).__name__
            )
    
    def _initialize_workflow(self):
        coordinator = CoordinatorAgent()
        # Use the same intent agent that was used for language processor
        intent = IntentAgent()  
        planner = PlannerAgent(self.tool_registry, self.tool_discovery_service)
        executor = ExecutorAgent(self.mcp_servers)
        aggregator = AggregatorAgent()
        reasoning = ReasoningAgent()
        evaluation = SelfEvaluationAgent()
        answer = ToolFirstAnswerAgent()
        
        self.workflow = MultiAgentWorkflow(
            coordinator=coordinator,
            intent=intent,
            planner=planner,
            executor=executor,
            aggregator=aggregator,
            reasoning=reasoning,
            evaluation=evaluation,
            answer=answer,
            memory_manager=self.memory_manager,
            language_processor=self.language_processor
        )
        
        logger.info_structured("Workflow initialized")
    
    async def process_query(self, request: QueryRequest) -> QueryResponse:
        if not self._initialized:
            await self.initialize()
        
        request_id = generate_request_id()
        set_request_id(request_id)
        
        start_time = datetime.utcnow()
        
        logger.info_structured(
            "Processing query",
            query=request.query,
            conversation_id=request.conversation_id,
            request_id=request_id
        )
        
        try:
            final_state = await self.workflow.run(
                query=request.query,
                conversation_id=request.conversation_id
            )
            
            end_time = datetime.utcnow()
            execution_time_ms = (end_time - start_time).total_seconds() * 1000
            
            telemetry.record_workflow_duration(
                execution_time_ms,
                final_state.get("conversation_id", "")
            )
            
            response = QueryResponse(
                answer=final_state.get("final_answer", "No answer generated"),
                confidence=final_state.get("confidence_score", 0.0),
                intent=final_state.get("detected_intent", "unknown"),
                trace=final_state.get("execution_trace", {}),
                conversation_id=final_state.get("conversation_id", ""),
                language=final_state.get("user_language", "en"),
                execution_time_ms=execution_time_ms,
                metadata=final_state.get("metadata", {})
            )
            
            logger.info_structured(
                "Query processed successfully",
                conversation_id=response.conversation_id,
                confidence=response.confidence,
                execution_time_ms=execution_time_ms,
                retry_count=final_state.get("retry_count", 0),
                request_id=request_id
            )
            
            return response
            
        except Exception as e:
            logger.error_structured(
                "Query processing failed",
                error=str(e),
                query=request.query
            )
            
            end_time = datetime.utcnow()
            execution_time_ms = (end_time - start_time).total_seconds() * 1000
            
            return QueryResponse(
                answer=f"An error occurred while processing your query: {str(e)}",
                confidence=0.0,
                trace={"error": str(e)},
                conversation_id=request.conversation_id or "",
                language="en",
                execution_time_ms=execution_time_ms,
                metadata={"error": str(e)}
            )
