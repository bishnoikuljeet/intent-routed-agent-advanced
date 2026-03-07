#!/usr/bin/env python3
"""
Populate Tool Vector Store

This script populates the tool definitions vector store with all tools.
"""

import asyncio
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.memory.tool_vector_store import ToolVectorStore
from app.memory.comprehensive_tools import get_shared_comprehensive_registry
from app.core.logging import logger


async def populate_all_tools():
    """
    Populate the vector store with all comprehensive tools.
    """
    try:
        print("🚀 Starting tool vector store population...")
        
        # Initialize the tool vector store
        store = ToolVectorStore()
        
        # Get all comprehensive tools
        registry = get_shared_comprehensive_registry()
        tools = list(registry.values())
        
        print(f"📋 Found {len(tools)} tools to populate")
        
        populated_count = 0
        
        for tool_metadata in tools:
            try:
                # Create document
                doc = store._create_tool_document(tool_metadata.name, tool_metadata)
                
                # Add to vector store
                from langchain_core.messages import HumanMessage
                tool_message = HumanMessage(content=doc['text'])
                
                await store.vector_store.add_message(
                    conversation_id="tool_definitions",
                    message=tool_message,
                    metadata={
                        "type": "tool_definition",
                        "name": tool_metadata.name,
                        "description": tool_metadata.description,
                        "parameters": tool_metadata.input_schema,
                        "usage_examples": doc["usage_examples"],
                        "categories": doc["categories"],
                        "keywords": doc["keywords"]
                    }
                )
                
                populated_count += 1
                
                if populated_count % 5 == 0:
                    print(f"  ✅ Populated {populated_count}/{len(tools)} tools...")
                
            except Exception as e:
                print(f"  ❌ Failed to populate {tool_metadata.name}: {e}")
                continue
        
        print(f"🎉 Successfully populated {populated_count}/{len(tools)} tools!")
        
        # Test the populated store
        print("\n🔍 Testing vector store search...")
        test_queries = ["compare", "metrics", "security", "data", "monitor"]
        
        for query in test_queries:
            results = await store.vector_store.search("tool_definitions", query, k=3)
            print(f"  Query '{query}': {len(results)} results")
            for result in results:
                name = result['metadata']['name']
                score = result.get('score', 0)
                print(f"    - {name}: {score:.2f}")
        
        return populated_count
        
    except Exception as e:
        print(f"❌ Failed to populate vector store: {e}")
        import traceback
        traceback.print_exc()
        return 0


if __name__ == "__main__":
    try:
        result = asyncio.run(populate_all_tools())
        if result > 0:
            print(f"\n✅ Success! Populated {result} tools in vector store")
            sys.exit(0)
        else:
            print("\n❌ Failed to populate any tools")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n🛑 Population interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)
