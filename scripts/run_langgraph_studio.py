"""
Script to run and test LangGraph Studio integration
"""

import asyncio
from app.workflow.graph import create_workflow


async def test_workflow():
    """Test the workflow with sample input"""
    
    # Create the workflow
    graph = create_workflow()
    
    # Test input
    test_input = {
        "messages": [],
        "current_query": "Analyze CPU and memory capacity for the auth service and forecast needs for the next 30 days.",
        "detected_language": "",
        "detected_intent": "",
        "extracted_entities": {},
        "execution_plan": {},
        "tool_results": [],
        "aggregated_data": {},
        "reasoning_output": {},
        "confidence_score": 0.0,
        "final_answer": "",
        "conversation_id": "test-workflow-001",
        "retry_count": 0,
        "metadata": {}
    }
    
    print("=" * 80)
    print("🚀 Testing LangGraph Workflow")
    print("=" * 80)
    print(f"\n📝 Query: {test_input['current_query']}\n")
    
    # Run the workflow
    print("⚙️  Executing workflow...\n")
    result = await graph.ainvoke(test_input)
    
    # Display results
    print("=" * 80)
    print("✅ Workflow Execution Complete")
    print("=" * 80)
    print(f"\n🌍 Detected Language: {result.get('detected_language', 'N/A')}")
    print(f"🎯 Detected Intent: {result.get('detected_intent', 'N/A')}")
    print(f"📊 Confidence Score: {result.get('confidence_score', 0.0):.2%}")
    print(f"💬 Final Answer: {result.get('final_answer', 'N/A')}")
    print(f"🔄 Retry Count: {result.get('retry_count', 0)}")
    
    print("\n" + "=" * 80)
    print("📋 Full State:")
    print("=" * 80)
    for key, value in result.items():
        if key not in ['messages']:  # Skip messages for brevity
            print(f"  {key}: {value}")
    
    return result


def main():
    """Main entry point"""
    print("\n" + "=" * 80)
    print("🎨 LangGraph Studio Integration - Intent-Routed Agent Advanced")
    print("=" * 80)
    print("\n📚 To start LangGraph Studio:")
    print("   1. Run: langgraph dev")
    print("   2. Open: http://localhost:8123")
    print("   3. Select: agent_workflow")
    print("\n" + "=" * 80 + "\n")
    
    # Run test
    asyncio.run(test_workflow())
    
    print("\n" + "=" * 80)
    print("✨ Test Complete!")
    print("=" * 80)
    print("\n💡 Next Steps:")
    print("   - Start LangGraph Studio: langgraph dev")
    print("   - Visualize workflow execution")
    print("   - Set breakpoints and debug")
    print("   - Monitor performance metrics")
    print("\n" + "=" * 80 + "\n")


if __name__ == "__main__":
    main()
