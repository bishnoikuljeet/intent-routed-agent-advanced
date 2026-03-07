#!/usr/bin/env python3
"""
Initialize Tool Vector Store

This script populates the tool definitions vector store
with all available tools for semantic similarity search.
"""

import asyncio
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.memory.tool_vector_store import initialize_tool_vector_store
from app.core.logging import logger


async def main():
    """
    Main function to initialize the tool vector store.
    """
    try:
        logger.info_structured(
            "Starting tool vector store initialization",
            script="initialize_tool_vector_store.py"
        )
        
        # Initialize the vector store with tool definitions
        populated_count = await initialize_tool_vector_store()
        
        if populated_count > 0:
            logger.info_structured(
                "Tool vector store initialization completed successfully",
                tools_populated=populated_count
            )
            print(f"✅ Successfully populated {populated_count} tool definitions in vector store")
        else:
            logger.warning_structured(
                "No tools were populated in vector store",
                populated_count=populated_count
            )
            print("⚠️  No tools were populated in vector store")
        
        return populated_count
        
    except Exception as e:
        logger.error_structured(
            "Tool vector store initialization failed",
            error=str(e)
        )
        print(f"❌ Failed to initialize tool vector store: {e}")
        return 0


if __name__ == "__main__":
    try:
        result = asyncio.run(main())
        sys.exit(0 if result > 0 else 1)
    except KeyboardInterrupt:
        print("\n🛑 Initialization interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)
