import asyncio
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.table import Table
from app.services.orchestrator import AgentOrchestrator
from app.schemas.models import QueryRequest
from app.core.logging import logger
import sys

console = Console()


class CLI:
    def __init__(self):
        self.orchestrator = AgentOrchestrator()
        self.conversation_id = None
    
    async def initialize(self):
        console.print("[yellow]Initializing agent system...[/yellow]")
        await self.orchestrator.initialize()
        console.print("[green]✓ System initialized[/green]\n")
    
    def display_welcome(self):
        welcome_text = """
# Intent Routed Agent Advanced

Production-grade multi-agent AI platform with:
- Multi-agent orchestration
- MCP-based tool ecosystem
- Multilingual support
- Conversation memory
- RAG retrieval
- Parallel tool execution

Type your questions or commands:
- `exit` or `quit` to exit
- `help` for available commands
- `clear` to start new conversation
"""
        console.print(Panel(Markdown(welcome_text), title="Welcome", border_style="blue"))
    
    def display_help(self):
        table = Table(title="Available Commands")
        table.add_column("Command", style="cyan")
        table.add_column("Description", style="white")
        
        table.add_row("exit, quit", "Exit the CLI")
        table.add_row("help", "Show this help message")
        table.add_row("clear", "Start a new conversation")
        table.add_row("tools", "List available tools")
        table.add_row("servers", "List MCP servers")
        
        console.print(table)
    
    def display_tools(self):
        tools = self.orchestrator.tool_registry.list_all_tools()
        
        table = Table(title=f"Available Tools ({len(tools)})")
        table.add_column("Tool", style="cyan")
        table.add_column("Server", style="yellow")
        table.add_column("Description", style="white")
        
        for tool in tools:
            table.add_row(
                tool.name,
                tool.server,
                tool.description[:60] + "..." if len(tool.description) > 60 else tool.description
            )
        
        console.print(table)
    
    def display_servers(self):
        table = Table(title="MCP Servers")
        table.add_column("Server", style="cyan")
        table.add_column("Tools", style="yellow")
        table.add_column("Resources", style="green")
        table.add_column("Prompts", style="magenta")
        
        for server_name, server in self.orchestrator.mcp_servers.items():
            table.add_row(
                server_name,
                str(len(server.tools)),
                str(len(server.resources)),
                str(len(server.prompts))
            )
        
        console.print(table)
    
    def display_response(self, response):
        console.print("\n[bold green]Answer:[/bold green]")
        console.print(Panel(response.answer, border_style="green"))
        
        trace_table = Table(title="Execution Trace", show_header=True)
        trace_table.add_column("Metric", style="cyan")
        trace_table.add_column("Value", style="white")
        
        trace_table.add_row("Confidence", f"{response.confidence:.2%}")
        trace_table.add_row("Execution Time", f"{response.execution_time_ms:.0f}ms")
        trace_table.add_row("Language", response.language)
        
        if response.trace.get("processing_components"):
            components = ", ".join(response.trace["processing_components"])
            trace_table.add_row("Processing Components", components)
        
        if response.trace.get("agents_called"):
            agents = ", ".join(response.trace["agents_called"])
            trace_table.add_row("Agents Called", agents)
        
        if response.trace.get("tools_called"):
            tools_info = []
            for tool in response.trace["tools_called"]:
                if isinstance(tool, dict):
                    # New format with parameters
                    params_str = ", ".join([f"{k}={v}" for k, v in tool.get("params", {}).items()])
                    tool_desc = f"{tool['name']}({params_str})" if params_str else tool['name']
                    if tool.get("success") is False:
                        tool_desc += " ❌"
                    elif tool.get("latency_ms"):
                        tool_desc += f" [{tool['latency_ms']:.0f}ms]"
                    tools_info.append(tool_desc)
                else:
                    # Backward compatibility for old format
                    tools_info.append(str(tool))
            
            tools_str = "\n".join(tools_info) if len(tools_info) > 1 else ", ".join(tools_info)
            trace_table.add_row("Tools Called", tools_str)
        
        console.print(trace_table)
        console.print()
    
    async def process_command(self, command: str) -> bool:
        command = command.strip().lower()
        
        if command in ["exit", "quit"]:
            console.print("[yellow]Goodbye![/yellow]")
            return False
        
        elif command == "help":
            self.display_help()
        
        elif command == "clear":
            self.conversation_id = None
            console.print("[green]✓ Started new conversation[/green]")
        
        elif command == "tools":
            self.display_tools()
        
        elif command == "servers":
            self.display_servers()
        
        else:
            return True
        
        return True
    
    async def run(self):
        await self.initialize()
        self.display_welcome()
        
        while True:
            try:
                query = console.input("\n[bold cyan]> [/bold cyan]")
                
                if not query.strip():
                    continue
                
                if not await self.process_command(query):
                    break
                
                if query.strip().lower() in ["exit", "quit", "help", "clear", "tools", "servers"]:
                    continue
                
                console.print("[yellow]Processing...[/yellow]")
                
                request = QueryRequest(
                    query=query,
                    conversation_id=self.conversation_id
                )
                
                response = await self.orchestrator.process_query(request)
                
                if not self.conversation_id:
                    self.conversation_id = response.conversation_id
                
                self.display_response(response)
                
            except KeyboardInterrupt:
                console.print("\n[yellow]Interrupted. Type 'exit' to quit.[/yellow]")
            except Exception as e:
                console.print(f"[red]Error: {str(e)}[/red]")
                logger.error_structured("CLI error", error=str(e))


async def main():
    cli = CLI()
    await cli.run()


if __name__ == "__main__":
    asyncio.run(main())
