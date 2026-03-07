from typing import Dict, List, Optional
from app.schemas.models import ToolMetadata
from app.core.logging import logger


class ToolRegistry:
    def __init__(self):
        self.tools: Dict[str, ToolMetadata] = {}
        self.server_tools: Dict[str, List[str]] = {}
    
    def register_tool(self, metadata: ToolMetadata):
        self.tools[metadata.name] = metadata
        
        if metadata.server not in self.server_tools:
            self.server_tools[metadata.server] = []
        
        self.server_tools[metadata.server].append(metadata.name)
        
        logger.info_structured(
            "Registered tool in registry",
            tool=metadata.name,
            server=metadata.server,
            capabilities=metadata.capabilities
        )
    
    def get_tool(self, tool_name: str) -> Optional[ToolMetadata]:
        return self.tools.get(tool_name)
    
    def get_tools_by_server(self, server: str) -> List[ToolMetadata]:
        tool_names = self.server_tools.get(server, [])
        return [self.tools[name] for name in tool_names if name in self.tools]
    
    def get_tools_by_capability(self, capability: str) -> List[ToolMetadata]:
        return [
            tool for tool in self.tools.values()
            if capability in tool.capabilities
        ]
    
    def list_all_tools(self) -> List[ToolMetadata]:
        return list(self.tools.values())
    
    def search_tools(self, query: str) -> List[ToolMetadata]:
        query_lower = query.lower()
        results = []
        
        for tool in self.tools.values():
            if (query_lower in tool.name.lower() or
                query_lower in tool.description.lower() or
                any(query_lower in cap.lower() for cap in tool.capabilities)):
                results.append(tool)
        
        return results
    
    def get_tool_metadata_dict(self) -> Dict[str, Dict]:
        return {
            name: {
                "name": tool.name,
                "description": tool.description,
                "input_schema": tool.input_schema,
                "output_schema": tool.output_schema,
                "capabilities": tool.capabilities,
                "server": tool.server,
                "timeout": tool.timeout
            }
            for name, tool in self.tools.items()
        }
