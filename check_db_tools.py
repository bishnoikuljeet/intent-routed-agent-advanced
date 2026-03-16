#!/usr/bin/env python3
import asyncio
import sys
sys.path.insert(0, 'c:/KB/demo/5/intent-routed-agent-advanced')
from app.services.tool_discovery_service import ToolDiscoveryService

async def check_tools():
    discovery = ToolDiscoveryService()
    tools = await discovery.discover_all_tools()
    
    # Filter for database tools
    db_tools = [t for t in tools if t.get('server') == 'database']
    
    print('Database tools available:')
    for tool in db_tools:
        print(f'  - {tool.get("name")}: {tool.get("description", "No desc")[:80]}...')
    
    print(f'\nTotal database tools: {len(db_tools)}')

if __name__ == "__main__":
    asyncio.run(check_tools())
