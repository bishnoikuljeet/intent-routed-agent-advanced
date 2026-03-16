from typing import Dict, Any
from langchain_openai import AzureChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from app.schemas.state import ConversationState
from app.schemas.models import SelfEvaluation
from app.core.config import settings
from app.core.logging import logger
from datetime import datetime
import json


class SelfEvaluationAgent:
    def __init__(self):
        self.name = "evaluation"
        self.llm = AzureChatOpenAI(
            azure_endpoint=settings.azure_openai_endpoint,
            api_key=settings.azure_openai_api_key,
            api_version=settings.azure_openai_api_version,
            deployment_name=settings.azure_openai_deployment,
            temperature=0.1,
        )
        self.confidence_threshold = settings.confidence_threshold
    
    async def evaluate(self, state: ConversationState) -> ConversationState:
        logger.info_structured(
            "Self-evaluation agent started",
            conversation_id=state.get("conversation_id")
        )
        
        query = state.get("current_query", "")
        reasoning_output = state.get("reasoning_output", {})
        aggregated_data = state.get("aggregated_data", {})
        tool_results = state.get("tool_results", [])
        
        system_prompt = """You are a self-evaluation agent. Assess the quality and reliability of the reasoning and results.

Evaluate:
1. Quality: Is the reasoning sound and well-supported?
2. Confidence: How confident are we in the conclusions?
3. Completeness: Is all necessary information present?
4. Reasoning validity: Are the logical steps correct?
5. Tool execution: Were tools executed successfully without errors?

IMPORTANT: Do NOT retry for the following issues:
- Tool parameter formatting errors (these need code fixes, not retries)
- Tool execution failures due to invalid parameters
- Data inconsistency issues that stem from tool design

ONLY retry for:
- Transient failures (network, timeouts)
- Ambiguous queries that need clarification
- Incomplete data that could be resolved with different approach

Respond in JSON format:
{
    "quality_score": 0.9,
    "confidence_score": 0.85,
    "completeness_score": 0.95,
    "reasoning_valid": true,
    "issues_found": ["issue1"],
    "should_retry": false,
    "retry_reason": null
}"""
        
        # Check for non-retryable error types
        non_retryable_errors = []
        for result in tool_results:
            if not result.get("success"):
                error_type = result.get("error_type")
                if error_type in ["not_found", "validation_failed", "configuration_error"]:
                    non_retryable_errors.append({
                        "tool": result.get("tool_name"),
                        "error_type": error_type,
                        "error": result.get("error")
                    })
        
        # If we have non-retryable errors, don't retry
        if non_retryable_errors:
            logger.info_structured(
                "Non-retryable errors detected",
                conversation_id=state.get("conversation_id"),
                errors=non_retryable_errors
            )
            
            # Set high confidence for "not_found" - we're confident the data doesn't exist
            if any(e["error_type"] == "not_found" for e in non_retryable_errors):
                state["confidence_score"] = 0.9
            else:
                state["confidence_score"] = 0.5
            
            if "metadata" not in state:
                state["metadata"] = {}
            state["metadata"]["evaluation"] = {
                "quality_score": 0.8,
                "confidence_score": state["confidence_score"],
                "completeness_score": 0.8,
                "reasoning_valid": True,
                "issues_found": [f"{e['error_type']}: {e['error']}" for e in non_retryable_errors],
                "should_retry": False,
                "retry_reason": None
            }
            
            state["execution_trace"]["agents_called"].append(self.name)
            state["execution_trace"]["timestamps"][self.name] = datetime.utcnow().isoformat()
            
            return state
        
        context = {
            "query": query,
            "reasoning": reasoning_output,
            "aggregated_data": aggregated_data,
            "tool_success_rate": sum(1 for r in tool_results if r.get("success")) / len(tool_results) if tool_results else 0,
            "tool_errors": [r.get("error") for r in tool_results if not r.get("success")],
            "execution_failures": [r for r in tool_results if not r.get("success")]
        }
        
        context_text = json.dumps(context, indent=2)
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"""Evaluate the following results:

{context_text}

Provide evaluation scores and determine if retry is needed.""")
        ]
        
        try:
            response = await self.llm.ainvoke(messages)
            
            # Handle empty or invalid JSON response
            if not response.content or response.content.strip() == "":
                logger.warning_structured("Empty evaluation response", conversation_id=state.get("conversation_id"))
                eval_data = {}
            else:
                try:
                    # Handle JSON wrapped in markdown code blocks
                    content = response.content.strip()
                    if content.startswith("```json"):
                        # Extract JSON from markdown block
                        lines = content.split('\n')
                        if len(lines) > 1 and lines[-1].strip() == "```":
                            json_content = '\n'.join(lines[1:-1])
                        else:
                            json_content = '\n'.join(lines[1:])
                        eval_data = json.loads(json_content)
                    else:
                        eval_data = json.loads(content)
                except json.JSONDecodeError as e:
                    logger.error_structured("Failed to parse evaluation JSON", error=str(e), response_content=response.content[:200])
                    eval_data = {}
            
            evaluation = SelfEvaluation(
                quality_score=eval_data.get("quality_score", 0.5),
                confidence_score=eval_data.get("confidence_score", 0.5),
                completeness_score=eval_data.get("completeness_score", 0.5),
                reasoning_valid=eval_data.get("reasoning_valid", True),
                issues_found=eval_data.get("issues_found", []),
                should_retry=eval_data.get("should_retry", False),
                retry_reason=eval_data.get("retry_reason")
            )
            
            overall_confidence = (
                evaluation.quality_score * 0.4 +
                evaluation.confidence_score * 0.4 +
                evaluation.completeness_score * 0.2
            )
            
            state["confidence_score"] = overall_confidence
            
            # Check for planning failures
            planning_failed = state.get("planning_failed", False)
            no_tools_executed = len(state.get("tool_results", [])) == 0
            vague_query = len(state.get("current_query", "").split()) < 3 and not state.get("extracted_entities", {})
            
            # Trigger retry for planning failures or no data scenarios
            if planning_failed and state.get("retry_count", 0) < state.get("max_retries", 2):
                evaluation.should_retry = True
                evaluation.retry_reason = "Planning failed, retrying with better prompt"
                evaluation.issues_found.append("Planning JSON parsing error")
                # Increment retry count here to ensure it persists
                state["retry_count"] = state.get("retry_count", 0) + 1
            elif no_tools_executed and overall_confidence > 0.8:
                # High confidence with no data is suspicious
                evaluation.should_retry = True
                evaluation.retry_reason = "High confidence with no tool results - needs investigation"
                evaluation.issues_found.append("Confidence not supported by evidence")
                # Increment retry count here to ensure it persists
                state["retry_count"] = state.get("retry_count", 0) + 1
            elif vague_query and no_tools_executed and state.get("retry_count", 0) < state.get("max_retries", 2):
                evaluation.should_retry = True
                evaluation.retry_reason = "Vague query needs clarification or better planning"
                evaluation.issues_found.append("Query too vague for confident answer")
                # Increment retry count here to ensure it persists
                state["retry_count"] = state.get("retry_count", 0) + 1
            elif (overall_confidence < self.confidence_threshold and 
                  state.get("retry_count", 0) < state.get("max_retries", 2) and
                  settings.low_confidence_retry_enabled):
                evaluation.should_retry = True
                evaluation.retry_reason = f"Confidence {overall_confidence:.2f} below threshold {self.confidence_threshold}"
                # Increment retry count here to ensure it persists
                state["retry_count"] = state.get("retry_count", 0) + 1
            
            if "metadata" not in state:
                state["metadata"] = {}
            state["metadata"]["evaluation"] = evaluation.model_dump()
            
            logger.info_structured(
                "Self-evaluation completed",
                conversation_id=state.get("conversation_id"),
                confidence_score=overall_confidence,
                should_retry=evaluation.should_retry,
                issues_count=len(evaluation.issues_found)
            )
            
        except Exception as e:
            logger.error_structured(
                "Self-evaluation failed",
                error=str(e),
                conversation_id=state.get("conversation_id")
            )
            
            state["confidence_score"] = 0.5
            if "metadata" not in state:
                state["metadata"] = {}
            state["metadata"]["evaluation"] = {
                "quality_score": 0.5,
                "confidence_score": 0.5,
                "completeness_score": 0.5,
                "reasoning_valid": False,
                "issues_found": [f"Evaluation error: {str(e)}"],
                "should_retry": False
            }
            state["errors"].append(f"Evaluation error: {str(e)}")
        
        # Add execution trace tracking (even in error case)
        state["execution_trace"]["agents_called"].append(self.name)
        state["execution_trace"]["timestamps"][self.name] = datetime.utcnow().isoformat()
        
        return state
