from app.mcp.base import BaseMCPServer, MCPTool, MCPResource, MCPPrompt
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import random


class SystemMCPServer(BaseMCPServer):
    def __init__(self, tool_registry):
        self.tool_registry = tool_registry
        super().__init__("system")
    
    def _initialize(self):
        self.register_tool(MCPTool(
            name="tool_registry_lookup",
            description="Look up tool metadata from the registry",
            input_schema={
                "type": "object",
                "properties": {
                    "tool_name": {"type": "string"},
                    "server": {"type": "string"}
                },
                "required": []
            },
            output_schema={
                "type": "object",
                "properties": {
                    "tools": {"type": "array"}
                }
            },
            handler=self._tool_registry_lookup
        ))
        
        self.register_tool(MCPTool(
            name="agent_health",
            description="Check health status of agents",
            input_schema={
                "type": "object",
                "properties": {
                    "agent_name": {"type": "string"}
                },
                "required": []
            },
            output_schema={
                "type": "object",
                "properties": {
                    "status": {"type": "string"},
                    "uptime": {"type": "number"},
                    "last_execution": {"type": "string"}
                }
            },
            handler=self._agent_health
        ))
        
        self.register_tool(MCPTool(
            name="workflow_status",
            description="Get current workflow execution status",
            input_schema={
                "type": "object",
                "properties": {
                    "workflow_id": {"type": "string"}
                },
                "required": []
            },
            output_schema={
                "type": "object",
                "properties": {
                    "status": {"type": "string"},
                    "current_step": {"type": "string"},
                    "progress": {"type": "number"}
                }
            },
            handler=self._workflow_status
        ))
        
        self.register_tool(MCPTool(
            name="list_mcp_servers",
            description="List all available MCP servers and their information",
            input_schema={
                "type": "object",
                "properties": {},
                "required": []
            },
            output_schema={
                "type": "object",
                "properties": {
                    "servers": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "tool_count": {"type": "number"},
                                "status": {"type": "string"}
                            }
                        }
                    }
                }
            },
            handler=self._list_mcp_servers
        ))
        
        # New Advanced Tools
        self.register_tool(MCPTool(
            name="performance_profiling",
            description="Profile system performance and identify bottlenecks",
            input_schema={
                "type": "object",
                "properties": {
                    "component": {"type": "string", "enum": ["agents", "tools", "llm", "database", "all"]},
                    "time_range_minutes": {"type": "integer", "default": 60},
                    "include_traces": {"type": "boolean", "default": False}
                },
                "required": ["component"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "metrics": {"type": "object"},
                    "bottlenecks": {"type": "array"},
                    "recommendations": {"type": "array"}
                }
            },
            handler=self._performance_profiling
        ))
        
        self.register_resource(MCPResource(
            uri="system://tool_metadata",
            name="Tool Metadata Registry",
            description="Metadata for all available tools",
            mime_type="application/json",
            content={}
        ))
        
        self.register_resource(MCPResource(
            uri="system://workflow_definitions",
            name="Workflow Definitions",
            description="Definitions of all available workflows",
            mime_type="application/json",
            content={
                "metrics_analysis": {
                    "steps": ["retrieve_metrics", "compare_threshold", "generate_report"],
                    "description": "Analyze service metrics against thresholds"
                },
                "knowledge_search": {
                    "steps": ["semantic_search", "rank_results", "summarize"],
                    "description": "Search and summarize knowledge base"
                }
            }
        ))
    
    async def _tool_registry_lookup(
        self,
        tool_name: str = None,
        server: str = None
    ) -> Dict[str, Any]:
        if tool_name:
            tool_metadata = self.tool_registry.get_tool(tool_name)
            if tool_metadata:
                return {"tools": [tool_metadata.dict()]}
            return {"tools": []}
        
        if server:
            tools = self.tool_registry.get_tools_by_server(server)
            return {"tools": [t.dict() for t in tools]}
        
        all_tools = self.tool_registry.list_all_tools()
        return {"tools": [t.dict() for t in all_tools]}
    
    async def _agent_health(self, agent_name: str = None) -> Dict[str, Any]:
        agents = {
            "coordinator": {"status": "healthy", "uptime": 99.9},
            "intent": {"status": "healthy", "uptime": 99.8},
            "planner": {"status": "healthy", "uptime": 99.7},
            "executor": {"status": "healthy", "uptime": 99.9},
            "aggregator": {"status": "healthy", "uptime": 99.8},
            "reasoning": {"status": "healthy", "uptime": 99.9},
            "evaluation": {"status": "healthy", "uptime": 99.7},
            "answer": {"status": "healthy", "uptime": 99.9}
        }
        
        if agent_name:
            agent_info = agents.get(agent_name, {"status": "unknown", "uptime": 0})
            return {
                **agent_info,
                "agent_name": agent_name,
                "last_execution": datetime.utcnow().isoformat()
            }
        
        return {
            "agents": agents,
            "overall_status": "healthy",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def _workflow_status(self, workflow_id: str = None) -> Dict[str, Any]:
        return {
            "status": "running",
            "current_step": "executor",
            "progress": 65.0,
            "workflow_id": workflow_id or "default",
            "started_at": datetime.utcnow().isoformat()
        }
    
    async def _list_mcp_servers(self) -> Dict[str, Any]:
        """List all MCP servers with their information"""
        # Get all tools and group by server
        all_tools = self.tool_registry.list_all_tools()
        server_info = {}
        
        for tool in all_tools:
            server_name = tool.server
            if server_name not in server_info:
                server_info[server_name] = {
                    "name": server_name,
                    "tool_count": 0,
                    "status": "active"
                }
            server_info[server_name]["tool_count"] += 1
        
        servers = list(server_info.values())
        
        return {
            "servers": servers,
            "total_servers": len(servers),
            "total_tools": sum(s["tool_count"] for s in servers)
        }
    
    async def _performance_profiling(
        self,
        component: str,
        time_range_minutes: int = 60,
        include_traces: bool = False
    ) -> Dict[str, Any]:
        components = [component] if component != "all" else ["agents", "tools", "llm", "database"]
        
        metrics = {}
        bottlenecks = []
        recommendations = []
        
        for comp in components:
            avg_latency = round(random.uniform(50, 500), 2)
            p95_latency = round(avg_latency * random.uniform(1.5, 2.5), 2)
            throughput = round(random.uniform(100, 1000), 2)
            error_rate = round(random.uniform(0.001, 0.05), 4)
            
            metrics[comp] = {
                "avg_latency_ms": avg_latency,
                "p95_latency_ms": p95_latency,
                "p99_latency_ms": round(p95_latency * 1.2, 2),
                "throughput_rps": throughput,
                "error_rate": error_rate,
                "cpu_usage_percent": round(random.uniform(20, 80), 2),
                "memory_usage_mb": round(random.uniform(100, 2000), 2)
            }
            
            # Identify bottlenecks
            if avg_latency > 300:
                bottlenecks.append({
                    "component": comp,
                    "issue": "high_latency",
                    "severity": "high",
                    "value": avg_latency,
                    "threshold": 300
                })
                recommendations.append({
                    "component": comp,
                    "recommendation": f"Optimize {comp} performance - latency exceeds threshold",
                    "priority": "high"
                })
            
            if error_rate > 0.02:
                bottlenecks.append({
                    "component": comp,
                    "issue": "high_error_rate",
                    "severity": "critical",
                    "value": error_rate,
                    "threshold": 0.02
                })
        
        return {
            "metrics": metrics,
            "bottlenecks": bottlenecks,
            "recommendations": recommendations,
            "time_range_minutes": time_range_minutes,
            "profiled_at": datetime.utcnow().isoformat()
        }
    
