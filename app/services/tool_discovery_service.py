"""
Tool Discovery Service - Centralized tool discovery from all MCP servers.
Provides dynamic tool discovery without hardcoded server lists.
"""

from typing import List, Dict, Any
from app.mcp.utility_server import UtilityMCPServer
from app.mcp.system_server import SystemMCPServer
from app.mcp.knowledge_server import KnowledgeMCPServer
from app.mcp.observability_server import ObservabilityMCPServer
from app.mcp.language_server import LanguageMCPServer
from app.mcp.database_server import DatabaseMCPServer
from app.registry.tool_registry import ToolRegistry
from app.core.logging import logger


class ToolDiscoveryService:
    """
    Service for discovering tools from all available MCP servers.
    Centralizes tool discovery logic.
    """
    
    def __init__(self, embeddings=None):
        """Initialize tool discovery service.
        
        Args:
            embeddings: Optional embeddings model for RAG-based tools
        """
        self.tool_registry = ToolRegistry()
        self._registered_servers = []
        self._comprehensive_registry_cache = None
        self._server_instances = {}
        self._tools_cache = None  # Cache discovered tools
        self._cache_initialized = False
        self.embeddings = embeddings
    
    def _get_comprehensive_registry(self):
        """
        Get comprehensive tool registry with enhanced metadata.
        
        Returns:
            Dictionary mapping tool names to enhanced metadata
        """
        if self._comprehensive_registry_cache is None:
            try:
                from ALL_TOOLS_REGISTRY import TOOL_REGISTRY
                
                enhanced_registry = {}
                
                for server_name, server_info in TOOL_REGISTRY.items():
                    for tool_name, tool_info in server_info.get('tools', {}).items():
                        enhanced_registry[tool_name] = {
                            'name': tool_name,
                            'description': tool_info.get('description', ''),
                            'input_schema': tool_info.get('input_schema', {}),
                            'output_schema': tool_info.get('output_schema', {}),
                            'capabilities': tool_info.get('use_cases', []),
                            'use_cases': tool_info.get('use_cases', []),
                            'examples': tool_info.get('examples', []),
                            'category': tool_info.get('category', ''),
                            'server': server_name
                        }
                
                self._comprehensive_registry_cache = enhanced_registry
                
                logger.info_structured(
                    "Loaded comprehensive tool registry",
                    total_tools=len(enhanced_registry)
                )
                
            except Exception as e:
                logger.error_structured(
                    "Failed to load comprehensive registry",
                    error=str(e)
                )
                self._comprehensive_registry_cache = {}
        
        return self._comprehensive_registry_cache
    
    def _enhance_tool_metadata(self, tool_name: str, tool: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enhance tool metadata with information from comprehensive registry.
        
        Args:
            tool_name: Name of the tool
            tool: Basic tool metadata from MCP server
            
        Returns:
            Enhanced tool metadata
        """
        comprehensive = self._get_comprehensive_registry()
        
        if tool_name in comprehensive:
            enhanced = comprehensive[tool_name].copy()
            # Keep MCP server-specific fields
            enhanced.update({
                'name': tool['name'],
                'description': tool['description'],
                'input_schema': tool['input_schema'],
                'output_schema': tool['output_schema'],
                'server': tool['server']
            })
            return enhanced
        
        # Return basic tool if not in comprehensive registry
        return tool
    
    def _create_server_instance(self, server_class):
        """
        Create server instance with proper dependency injection.
        
        Args:
            server_class: MCP server class to instantiate
            
        Returns:
            Server instance with required dependencies
        """
        try:
            # Handle servers with required dependencies
            if server_class == SystemMCPServer:
                return server_class(self.tool_registry)
            elif server_class == DatabaseMCPServer:
                # DatabaseMCPServer needs LLM service and RAG retriever for query_database tool
                from app.services.llm_service import LLMService
                from app.rag.retriever import RAGRetriever
                llm_service = LLMService()
                # Create RAG retriever with embeddings if available
                rag_retriever = RAGRetriever(embeddings=self.embeddings) if self.embeddings else None
                return server_class(llm_service=llm_service, rag_retriever=rag_retriever)
            elif server_class == KnowledgeMCPServer:
                # Create RAG retriever with embeddings if available
                from app.rag.retriever import RAGRetriever
                rag_retriever = RAGRetriever(embeddings=self.embeddings)
                
                if self.embeddings:
                    logger.info_structured(
                        "Created KnowledgeMCPServer with RAGRetriever",
                        embeddings_configured=True
                    )
                else:
                    logger.info_structured(
                        "Created KnowledgeMCPServer with RAGRetriever",
                        embeddings_configured=False,
                        note="Embeddings can be configured later via set_embeddings()"
                    )
                return server_class(rag_retriever)
            elif server_class == LanguageMCPServer:
                # LanguageMCPServer creates its own LanguageProcessor, but handle potential errors
                try:
                    return server_class()
                except Exception as e:
                    logger.warning_structured(
                        "Could not create LanguageProcessor, LanguageMCPServer may have limited functionality",
                        error=str(e)
                    )
                    # Try creating without processor
                    server = server_class.__new__(server_class)
                    server.name = "language"
                    server.tools = {}
                    return server
            else:
                # Servers without required dependencies (ObservabilityMCPServer, UtilityMCPServer)
                return server_class()
        except Exception as e:
            logger.error_structured(
                "Failed to create server instance",
                server=server_class.__name__,
                error=str(e)
            )
            raise
    
    def register_server(self, server_class):
        """
        Register an MCP server for tool discovery.
        
        Args:
            server_class: MCP server class to register
        """
        if server_class not in self._registered_servers:
            self._registered_servers.append(server_class)
            logger.info_structured(
                "MCP server registered",
                server=server_class.__name__
            )
    
    async def initialize_tools(self):
        """
        Pre-initialize all tools at startup.
        This should be called once during application startup to populate the cache.
        """
        logger.info_structured("Pre-initializing tools at startup")
        await self.discover_all_tools(force_refresh=True)
        logger.info_structured(
            "Tools pre-initialized",
            total_tools=len(self._tools_cache) if self._tools_cache else 0
        )
    
    async def discover_all_tools(self, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """
        Discover all tools from all registered MCP servers.
        Uses caching to avoid re-creating server instances on every call.
        
        Args:
            force_refresh: If True, bypass cache and re-discover tools
        
        Returns:
            List of tool dictionaries with schemas
        """
        # Return cached tools if available and not forcing refresh
        if self._cache_initialized and self._tools_cache is not None and not force_refresh:
            logger.debug(
                f"Returning cached tools (count: {len(self._tools_cache)})"
            )
            return self._tools_cache
        
        tools = []
        
        # Default servers if none registered
        if not self._registered_servers:
            self._registered_servers = [
                UtilityMCPServer,
                ObservabilityMCPServer,
                SystemMCPServer,
                KnowledgeMCPServer,
                LanguageMCPServer
            ]
        
        # Discover from each server
        for server_class in self._registered_servers:
            try:
                # Reuse cached server instance if available
                server_class_name = server_class.__name__
                if server_class_name in self._server_instances and not force_refresh:
                    server = self._server_instances[server_class_name]
                else:
                    server = self._create_server_instance(server_class)
                    self._server_instances[server_class_name] = server
                
                for tool_name, tool in server.tools.items():
                    enhanced_tool = self._enhance_tool_metadata(tool_name, {
                        "name": tool.name,
                        "description": tool.description,
                        "input_schema": tool.input_schema,
                        "output_schema": tool.output_schema,
                        "capabilities": getattr(tool, 'capabilities', []),
                        "server": server.name
                    })
                    tools.append(enhanced_tool)
                
                logger.info_structured(
                    "Tools discovered from server",
                    server=server.name,
                    tool_count=len(server.tools)
                )
                
            except Exception as e:
                logger.error_structured(
                    "Failed to discover tools from server",
                    server=server_class.__name__,
                    error=str(e)
                )
        
        # Cache the discovered tools
        self._tools_cache = tools
        self._cache_initialized = True
        
        logger.info_structured(
            "Total tools discovered",
            total_count=len(tools),
            cached=not force_refresh
        )
        
        return tools
    
    async def discover_tools_by_capability(self, capability: str) -> List[Dict[str, Any]]:
        """
        Discover tools that have a specific capability.
        
        Args:
            capability: Capability to search for
            
        Returns:
            List of matching tools
        """
        all_tools = await self.discover_all_tools()
        
        matching_tools = [
            tool for tool in all_tools
            if capability in tool.get('capabilities', [])
        ]
        
        logger.info_structured(
            "Tools discovered by capability",
            capability=capability,
            count=len(matching_tools)
        )
        
        return matching_tools
    
    async def get_tool_schema(self, tool_name: str) -> Dict[str, Any]:
        """
        Get schema for a specific tool.
        
        Args:
            tool_name: Name of the tool
            
        Returns:
            Tool schema dictionary
        """
        all_tools = await self.discover_all_tools()
        
        for tool in all_tools:
            if tool['name'] == tool_name:
                return tool
        
        logger.warning_structured(
            "Tool schema not found",
            tool_name=tool_name
        )
        
        return {}
    
    async def get_tools_for_query(self, query: str, llm_service) -> List[Dict[str, Any]]:
        """
        Get relevant tools for a query using LLM semantic matching.
        
        Args:
            query: User query
            llm_service: LLM service for semantic matching
            
        Returns:
            List of relevant tools
        """
        all_tools = await self.discover_all_tools()
        
        # Return all tools - LLM will select appropriate tools during context inference
        relevant_tools = []
        
        for tool in all_tools:
            try:
                # Add all tools - semantic matching happens in LLM context inference layer
                relevant_tools.append(tool)
                
            except Exception as e:
                logger.error_structured(
                    "Tool capability assessment failed",
                    tool=tool['name'],
                    error=str(e)
                )
        
        return relevant_tools
    
    def get_compact_tool_summary(self, tools: List[Dict[str, Any]]) -> str:
        """
        Get compact, token-efficient summary of tools.
        
        Args:
            tools: List of tool dictionaries
            
        Returns:
            Compact tool summary string
        """
        from app.prompts import PromptTemplates
        
        templates = PromptTemplates()
        return templates.format_tools_compact(tools)
    
    async def execute_tool(
        self,
        tool_name: str,
        parameters: Dict[str, Any]
    ) -> Any:
        """
        Execute a tool by name with parameters.
        
        Args:
            tool_name: Name of the tool to execute
            parameters: Tool parameters
            
        Returns:
            Tool execution result
        """
        # Ensure servers are initialized
        if not self._server_instances:
            await self.discover_all_tools()
        
        # Find which server has this tool
        for server_class_name, server in self._server_instances.items():
            try:
                if tool_name in server.tools:
                    # Execute tool via MCP protocol
                    result = await server.call_tool(tool_name, parameters)
                    
                    logger.info_structured(
                        "Tool executed successfully",
                        tool=tool_name,
                        server=server.name
                    )
                    
                    return result
                    
            except Exception as e:
                logger.error_structured(
                    "Tool execution failed",
                    tool=tool_name,
                    server=server_class_name,
                    error=str(e)
                )
        
        # Tool not found
        logger.error_structured(
            "Tool not found in any server",
            tool=tool_name
        )
        
        return {"error": f"Tool '{tool_name}' not found"}
