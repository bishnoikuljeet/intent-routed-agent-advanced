"""
Tool Definitions Vector Store

This module handles the storage and retrieval of tool definitions
in a vector store for semantic similarity search.
"""

import json
import asyncio
from typing import Dict, List, Any
from pathlib import Path
from app.core.logging import logger
from app.memory.vector_store import VectorMemoryStore
from app.registry.tool_registry import ToolRegistry


class ToolVectorStore:
    """
    Vector store for tool definitions with semantic similarity search capabilities.
    """
    
    def __init__(self, collection_name: str = "tool_definitions"):
        self.collection_name = collection_name
        from langchain_openai import AzureOpenAIEmbeddings
        from app.core.config import settings
        
        # Initialize embeddings with proper configuration
        self.embeddings = AzureOpenAIEmbeddings(
            azure_deployment=settings.azure_embedding_openai_deployment,
            openai_api_version=settings.azure_embedding_openai_api_version,
            azure_endpoint=settings.azure_embedding_openai_endpoint,
            api_key=settings.azure_embedding_openai_api_key
        )
        
        # Initialize vector store for tool definitions in tools/ subfolder
        self.vector_store = VectorMemoryStore(embeddings=self.embeddings)
        self.vector_store.store_path = Path(settings.vector_store_path) / "tools"
        self.vector_store.store_path.mkdir(parents=True, exist_ok=True)
    
    async def populate_tool_definitions(self) -> int:
        """
        Populate the vector store with tool definitions from the tool registry.
        
        Returns:
            Number of tools successfully added to the vector store.
        """
        try:
            logger.info_structured(
                "Starting tool definitions population",
                collection_name=self.collection_name
            )
            
            # Get all tools from registry - use the comprehensive tool registry
            from app.memory.comprehensive_tools import get_shared_comprehensive_registry
            tool_registry = get_shared_comprehensive_registry()
            tools = list(tool_registry.values())
            
            populated_count = 0
            
            for tool_metadata in tools:
                try:
                    # Create comprehensive tool document for vector embedding
                    tool_document = self._create_tool_document(tool_metadata.name, tool_metadata)
                    
                    # Store in vector store using conversation-based approach
                    from langchain_core.messages import HumanMessage
                    
                    # Create a message with tool information
                    tool_message = HumanMessage(content=tool_document["text"])
                    
                    await self.vector_store.add_message(
                        conversation_id="tool_definitions",
                        message=tool_message,
                        metadata={
                            "type": "tool_definition",
                            "name": tool_metadata.name,
                            "description": tool_metadata.description,
                            "parameters": tool_metadata.input_schema,
                            "usage_examples": tool_document["usage_examples"],
                            "categories": tool_document["categories"],
                            "keywords": tool_document["keywords"]
                        }
                    )
                    
                    populated_count += 1
                    
                    logger.info_structured(
                        "Tool definition added to vector store",
                        tool_name=tool_metadata.name,
                        categories=tool_document["categories"]
                    )
                    
                except Exception as e:
                    logger.error_structured(
                        "Failed to add tool definition to vector store",
                        tool_name=tool_metadata.name,
                        error=str(e)
                    )
                    continue
            
            logger.info_structured(
                "Tool definitions population completed",
                total_tools=len(tools),
                populated_count=populated_count,
                collection_name=self.collection_name
            )
            
            return populated_count
            
        except Exception as e:
            logger.error_structured(
                "Tool definitions population failed",
                error=str(e)
            )
            return 0
    
    def _create_tool_document(self, tool_name: str, tool_metadata) -> Dict[str, Any]:
        """
        Create a comprehensive text document for a tool definition.
        """
        # Base description
        description = tool_metadata.description
        
        # Extract parameter information
        parameters = tool_metadata.input_schema
        param_text = ""
        
        if isinstance(parameters, dict) and 'properties' in parameters:
            param_names = []
            param_descriptions = []
            
            for param_name, param_details in parameters['properties'].items():
                param_names.append(param_name)
                if isinstance(param_details, dict) and 'description' in param_details:
                    param_descriptions.append(param_details['description'])
                else:
                    param_descriptions.append(f"Parameter: {param_name}")
            
            param_text = f"Parameters: {', '.join(param_names)}. {'. '.join(param_descriptions)}"
        
        # Generate usage examples based on tool name and parameters
        usage_examples = self._generate_usage_examples(tool_name, parameters)
        
        # Extract keywords from tool name and description
        keywords = self._extract_keywords(tool_name, description)
        
        # Determine categories based on tool name and description
        categories = self._determine_categories(tool_name, description, parameters)
        
        # Create comprehensive text for embedding
        text_parts = [
            f"Tool: {tool_name}",
            f"Description: {description}",
            param_text,
            f"Usage examples: {'; '.join(usage_examples)}",
            f"Keywords: {', '.join(keywords)}",
            f"Categories: {', '.join(categories)}"
        ]
        
        text = ". ".join(filter(None, text_parts))
        
        return {
            "text": text,
            "usage_examples": usage_examples,
            "categories": categories,
            "keywords": keywords
        }
    
    def _generate_usage_examples(self, tool_name: str, parameters: Dict[str, Any]) -> List[str]:
        """
        Generate realistic usage examples for a tool based on its name and parameters.
        """
        examples = []
        
        # Extract parameter names for examples
        param_names = []
        if isinstance(parameters, dict) and 'properties' in parameters:
            param_names = list(parameters['properties'].keys())
        
        # Generate parameter-based examples
        if param_names:
            if len(param_names) == 1:
                examples.append(f"Get {tool_name} for {param_names[0]}")
            elif len(param_names) >= 2:
                examples.append(f"Use {tool_name} with {param_names[0]} and {param_names[1]}")
        
        # Generic fallback
        if not examples:
            examples.append(f"Execute {tool_name}")
        
        return examples[:3]  # Return top 3 examples
    
    def _extract_keywords(self, tool_name: str, description: str) -> List[str]:
        """
        Extract relevant keywords from tool name and description.
        """
        keywords = []
        
        # Add tool name parts
        name_parts = tool_name.lower().replace('_', ' ').split()
        keywords.extend([part for part in name_parts if len(part) > 2])
        
        # Add description keywords
        desc_words = description.lower().split()
        keywords.extend([word for word in desc_words if len(word) > 3])
        
        # Extract keywords from description only - NO hardcoded keyword lists
        # Remove duplicates and return
        return list(set(keywords))[:10]  # Limit to top 10 keywords
    
    def _determine_categories(self, tool_name: str, description: str, parameters: Dict[str, Any]) -> List[str]:
        """
        Determine categories for a tool based on its characteristics.
        NO hardcoded keyword matching - use parameter count only.
        """
        categories = []
        
        # Derive categories from tool description - NO hardcoded keyword matching
        # Parameter-based categories only
        if isinstance(parameters, dict) and 'properties' in parameters:
            param_count = len(parameters['properties'])
            if param_count > 3:
                categories.append('complex')
            elif param_count == 1:
                categories.append('simple')
            else:
                categories.append('moderate')
        
        # Default category
        if not categories:
            categories.append('general')
        
        return categories
    
    async def search_tools(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Search for tools using vector similarity.
        
        Args:
            query: The search query
            top_k: Number of results to return
            
        Returns:
            List of tool documents with similarity scores.
        """
        try:
            # Search for similar tools using conversation-based API
            results = await self.vector_store.search(
                conversation_id="tool_definitions",
                query=query,
                k=top_k
            )
            
            # Filter for tool definitions only
            tool_results = []
            for result in results:
                if result.get('metadata', {}).get('type') == 'tool_definition':
                    tool_results.append(result)
            
            return tool_results
            
        except Exception as e:
            logger.error_structured(
                "Tool search failed",
                query=query[:50],
                error=str(e)
            )
            return []
    
    async def get_tool_by_name(self, tool_name: str) -> Dict[str, Any]:
        """
        Get a specific tool by name.
        
        Args:
            tool_name: The name of the tool to retrieve
            
        Returns:
            Tool document or empty dict if not found.
        """
        try:
            # Search for the tool by name
            results = await self.vector_store.search(
                conversation_id="tool_definitions",
                query=tool_name,
                k=10  # Search more to find the specific tool
            )
            
            # Find the exact match
            for result in results:
                metadata = result.get('metadata', {})
                if metadata.get('type') == 'tool_definition' and metadata.get('name') == tool_name:
                    return result
            
            return {}
            
        except Exception as e:
            logger.error_structured(
                "Failed to get tool by name",
                tool_name=tool_name,
                error=str(e)
            )
            return {}


# Singleton instance
_tool_vector_store = None

def get_tool_vector_store() -> ToolVectorStore:
    """
    Get the singleton tool vector store instance.
    """
    global _tool_vector_store
    if _tool_vector_store is None:
        _tool_vector_store = ToolVectorStore()
    return _tool_vector_store


async def initialize_tool_vector_store() -> int:
    """
    Initialize the tool vector store with current tool definitions.
    
    Returns:
        Number of tools successfully populated.
    """
    tool_store = get_tool_vector_store()
    return await tool_store.populate_tool_definitions()
