"""
Comprehensive Tools Loader

This module loads the comprehensive tool registry from ALL_TOOLS_REGISTRY.py
and converts it to ToolMetadata objects for the vector store.
"""

from typing import List, Dict, Any
from app.schemas.models import ToolMetadata
from app.core.logging import logger


def load_comprehensive_tools() -> List[ToolMetadata]:
    """
    Load comprehensive tools from ALL_TOOLS_REGISTRY.py and convert to ToolMetadata objects.
    
    Returns:
        List of ToolMetadata objects.
    """
    try:
        # Import the comprehensive tool registry
        import sys
        import os
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        from ALL_TOOLS_REGISTRY import TOOL_REGISTRY
        
        tools = []
        
        # Iterate through all servers and their tools
        for server_name, server_info in TOOL_REGISTRY.items():
            server_description = server_info.get('description', '')
            
            for tool_name, tool_info in server_info.get('tools', {}).items():
                try:
                    # Convert to ToolMetadata
                    tool_metadata = ToolMetadata(
                        name=tool_name,
                        description=tool_info.get('description', ''),
                        input_schema=tool_info.get('input_schema', {}),
                        output_schema=tool_info.get('output_schema', {}),
                        capabilities=tool_info.get('use_cases', []),
                        server=server_name,
                        timeout=30
                    )
                    
                    tools.append(tool_metadata)
                    
                    logger.info_structured(
                        "Loaded comprehensive tool",
                        tool_name=tool_name,
                        server=server_name,
                        capabilities=len(tool_metadata.capabilities)
                    )
                    
                except Exception as e:
                    logger.error_structured(
                        "Failed to load tool",
                        tool_name=tool_name,
                        error=str(e)
                    )
                    continue
        
        logger.info_structured(
            "Comprehensive tools loading completed",
            total_tools=len(tools),
            servers=len(TOOL_REGISTRY)
        )
        
        return tools
        
    except Exception as e:
        logger.error_structured(
            "Failed to load comprehensive tools",
            error=str(e)
        )
        return []


def get_comprehensive_tool_registry() -> Dict[str, ToolMetadata]:
    """
    Get a dictionary of comprehensive tools by name.
    
    Returns:
        Dictionary mapping tool names to ToolMetadata objects.
    """
    tools = load_comprehensive_tools()
    return {tool.name: tool for tool in tools}


# Shared registry instance
_comprehensive_tool_registry = None

def get_shared_comprehensive_registry() -> Dict[str, ToolMetadata]:
    """
    Get the shared comprehensive tool registry instance.
    """
    global _comprehensive_tool_registry
    if _comprehensive_tool_registry is None:
        _comprehensive_tool_registry = get_comprehensive_tool_registry()
    return _comprehensive_tool_registry


def populate_comprehensive_tools():
    """
    Populate the tool registry with comprehensive tools.
    
    Returns:
        Number of tools added.
    """
    try:
        from app.registry.tool_registry import ToolRegistry
        
        tool_registry = ToolRegistry()
        tools = load_comprehensive_tools()
        
        # Add all comprehensive tools to registry
        for tool_metadata in tools:
            tool_registry.register_tool(tool_metadata)
        
        print(f"✅ Populated {len(tools)} comprehensive tools in registry")
        return len(tools)
        
    except Exception as e:
        print(f"❌ Failed to populate comprehensive tools: {e}")
        return 0


if __name__ == "__main__":
    populate_comprehensive_tools()
