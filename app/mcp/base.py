from typing import Any, Dict, List, Optional, Callable
from abc import ABC, abstractmethod
from pydantic import BaseModel, ConfigDict
from app.core.logging import logger
import asyncio


class MCPTool(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    name: str
    description: str
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]
    handler: Optional[Callable] = None


class MCPResource(BaseModel):
    uri: str
    name: str
    description: str
    mime_type: str
    content: Any


class MCPPrompt(BaseModel):
    name: str
    description: str
    template: str
    arguments: List[str] = []


class BaseMCPServer(ABC):
    def __init__(self, name: str):
        self.name = name
        self.tools: Dict[str, MCPTool] = {}
        self.resources: Dict[str, MCPResource] = {}
        self.prompts: Dict[str, MCPPrompt] = {}
        self._initialize()
    
    @abstractmethod
    def _initialize(self):
        pass
    
    def register_tool(self, tool: MCPTool):
        self.tools[tool.name] = tool
        logger.info_structured(
            "Registered MCP tool",
            server=self.name,
            tool=tool.name
        )
    
    def register_resource(self, resource: MCPResource):
        self.resources[resource.uri] = resource
        logger.info_structured(
            "Registered MCP resource",
            server=self.name,
            resource=resource.name
        )
    
    def register_prompt(self, prompt: MCPPrompt):
        self.prompts[prompt.name] = prompt
        logger.info_structured(
            "Registered MCP prompt",
            server=self.name,
            prompt=prompt.name
        )
    
    async def call_tool(self, tool_name: str, params: Dict[str, Any]) -> Any:
        if tool_name not in self.tools:
            raise ValueError(f"Tool {tool_name} not found in server {self.name}")
        
        tool = self.tools[tool_name]
        
        if not tool.handler:
            raise ValueError(f"Tool {tool_name} has no handler")
        
        try:
            logger.info_structured(
                "Calling MCP tool",
                server=self.name,
                tool=tool_name,
                params=params
            )
            
            if asyncio.iscoroutinefunction(tool.handler):
                result = await tool.handler(**params)
            else:
                result = tool.handler(**params)
            
            logger.info_structured(
                "MCP tool completed",
                server=self.name,
                tool=tool_name
            )
            
            return result
        except Exception as e:
            logger.error_structured(
                "MCP tool failed",
                server=self.name,
                tool=tool_name,
                error=str(e)
            )
            raise
    
    def get_resource(self, uri: str) -> Optional[MCPResource]:
        return self.resources.get(uri)
    
    def get_prompt(self, name: str) -> Optional[MCPPrompt]:
        return self.prompts.get(name)
    
    def list_tools(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "input_schema": tool.input_schema,
                "output_schema": tool.output_schema
            }
            for tool in self.tools.values()
        ]
    
    def list_resources(self) -> List[Dict[str, Any]]:
        return [
            {
                "uri": resource.uri,
                "name": resource.name,
                "description": resource.description,
                "mime_type": resource.mime_type
            }
            for resource in self.resources.values()
        ]
    
    def list_prompts(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": prompt.name,
                "description": prompt.description,
                "arguments": prompt.arguments
            }
            for prompt in self.prompts.values()
        ]
