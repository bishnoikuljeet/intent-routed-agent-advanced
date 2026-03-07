"""
LangGraph workflow definition for Intent-Routed Agent Advanced
Provides visual workflow representation for LangGraph Studio
"""

from typing import TypedDict, Annotated, Sequence
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage
import operator


class AgentState(TypedDict):
    """State definition for the agent workflow"""
    messages: Annotated[Sequence[BaseMessage], add_messages]
    current_query: str
    detected_language: str
    detected_intent: str
    extracted_entities: dict
    execution_plan: dict
    tool_results: list
    aggregated_data: dict
    reasoning_output: dict
    confidence_score: float
    final_answer: str
    conversation_id: str
    retry_count: int
    metadata: dict


def language_processing_node(state: AgentState) -> AgentState:
    """Language processing node - detects language and normalizes text"""
    # Simulate language processing for visualization
    state["detected_language"] = "en"
    state["current_query"] = state.get("current_query", "")
    print(f"✓ Language Processing: Detected {state['detected_language']}")
    return state


def intent_classification_node(state: AgentState) -> AgentState:
    """Intent classification node - identifies user intent"""
    # Simulate intent classification for visualization
    query = state.get("current_query", "").lower()
    
    if "capacity" in query or "forecast" in query:
        state["detected_intent"] = "calculation_compare"
        state["extracted_entities"] = {
            "service": "auth service",
            "metrics": ["CPU", "memory"],
            "time_frame": "30 days"
        }
    elif "version" in query or "documentation" in query:
        state["detected_intent"] = "knowledge_lookup"
        state["extracted_entities"] = {
            "documentation_type": "API documentation"
        }
    else:
        state["detected_intent"] = "general_query"
        state["extracted_entities"] = {}
    
    print(f"✓ Intent Classification: {state['detected_intent']}")
    return state


def planning_node(state: AgentState) -> AgentState:
    """Planning node - creates execution plan"""
    # Simulate planning for visualization
    intent = state.get("detected_intent", "general_query")
    
    if intent == "calculation_compare":
        state["execution_plan"] = {
            "steps": [
                {"step": 1, "tool": "capacity_planning", "resource": "cpu"},
                {"step": 2, "tool": "capacity_planning", "resource": "memory"}
            ],
            "reasoning": "Analyze CPU and memory capacity with forecasting",
            "requires_parallel": True
        }
    elif intent == "knowledge_lookup":
        state["execution_plan"] = {
            "steps": [
                {"step": 1, "tool": "document_versioning", "action": "list_versions"},
                {"step": 2, "tool": "document_versioning", "action": "compare_versions"}
            ],
            "reasoning": "List versions and compare changes",
            "requires_parallel": False
        }
    else:
        state["execution_plan"] = {
            "steps": [],
            "reasoning": "General query processing",
            "requires_parallel": False
        }
    
    print(f"✓ Planning: Created {len(state['execution_plan']['steps'])} step plan")
    return state


def execution_node(state: AgentState) -> AgentState:
    """Execution node - executes tools based on plan"""
    # Simulate tool execution for visualization
    plan = state.get("execution_plan", {})
    steps = plan.get("steps", [])
    
    state["tool_results"] = [
        {
            "tool": step.get("tool", "unknown"),
            "success": True,
            "result": {"status": "completed", "data": "simulated_data"}
        }
        for step in steps
    ]
    
    print(f"✓ Execution: Executed {len(state['tool_results'])} tools")
    return state


def aggregation_node(state: AgentState) -> AgentState:
    """Aggregation node - aggregates tool results"""
    # Simulate aggregation for visualization
    tool_results = state.get("tool_results", [])
    
    state["aggregated_data"] = {
        "key_findings": [
            f"Finding from {result['tool']}" 
            for result in tool_results
        ],
        "summary": f"Aggregated {len(tool_results)} tool results",
        "has_issues": False
    }
    
    print(f"✓ Aggregation: Processed {len(tool_results)} results")
    return state


def reasoning_node(state: AgentState) -> AgentState:
    """Reasoning node - performs logical reasoning"""
    # Simulate reasoning for visualization
    aggregated = state.get("aggregated_data", {})
    
    state["reasoning_output"] = {
        "conclusion": "Analysis complete based on tool results",
        "confidence": 0.9,
        "evidence_count": len(aggregated.get("key_findings", []))
    }
    state["confidence_score"] = 0.9
    
    print(f"✓ Reasoning: Confidence {state['confidence_score']:.2%}")
    return state


def evaluation_node(state: AgentState) -> AgentState:
    """Evaluation node - self-evaluates results"""
    # Simulate evaluation for visualization
    confidence = state.get("confidence_score", 0.9)
    retry_count = state.get("retry_count", 0)
    
    # Determine if retry is needed
    should_retry = confidence < 0.7 and retry_count < 2
    
    if should_retry:
        state["retry_count"] = retry_count + 1
        print(f"⚠ Evaluation: Low confidence, triggering retry {state['retry_count']}")
    else:
        print(f"✓ Evaluation: Confidence acceptable ({confidence:.2%})")
    
    return state


def answer_generation_node(state: AgentState) -> AgentState:
    """Answer generation node - creates final response"""
    # Simulate answer generation for visualization
    query = state.get("current_query", "")
    intent = state.get("detected_intent", "")
    confidence = state.get("confidence_score", 0.0)
    
    state["final_answer"] = (
        f"Based on the analysis of '{query}' with intent '{intent}', "
        f"the system has processed the request with {confidence:.0%} confidence. "
        f"Results have been aggregated and reasoning applied."
    )
    
    print(f"✓ Answer Generation: Response created ({len(state['final_answer'])} chars)")
    return state


def should_retry(state: AgentState) -> str:
    """Conditional edge - determines if retry is needed"""
    retry_count = state.get("retry_count", 0)
    confidence = state.get("confidence_score", 1.0)
    
    if confidence < 0.7 and retry_count < 2:
        return "retry"
    return "continue"


def create_workflow() -> StateGraph:
    """
    Create the LangGraph workflow for the Intent-Routed Agent system
    
    Returns:
        StateGraph: Compiled workflow graph
    """
    
    # Create the graph
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("language_processing", language_processing_node)
    workflow.add_node("intent_classification", intent_classification_node)
    workflow.add_node("planning", planning_node)
    workflow.add_node("execution", execution_node)
    workflow.add_node("aggregation", aggregation_node)
    workflow.add_node("reasoning", reasoning_node)
    workflow.add_node("evaluation", evaluation_node)
    workflow.add_node("answer_generation", answer_generation_node)
    
    # Define the workflow edges
    workflow.set_entry_point("language_processing")
    
    workflow.add_edge("language_processing", "intent_classification")
    workflow.add_edge("intent_classification", "planning")
    workflow.add_edge("planning", "execution")
    workflow.add_edge("execution", "aggregation")
    workflow.add_edge("aggregation", "reasoning")
    workflow.add_edge("reasoning", "evaluation")
    
    # Conditional edge for retry logic
    workflow.add_conditional_edges(
        "evaluation",
        should_retry,
        {
            "retry": "planning",  # Retry from planning
            "continue": "answer_generation"  # Continue to answer
        }
    )
    
    workflow.add_edge("answer_generation", END)
    
    # Compile the graph
    app = workflow.compile()
    
    return app


# For LangGraph Studio
graph = create_workflow()
