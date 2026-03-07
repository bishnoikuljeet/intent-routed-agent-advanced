from typing import Dict, Any, List
from langchain_openai import AzureChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from app.schemas.state import ConversationState
from app.core.config import settings
from app.core.logging import logger
from datetime import datetime
import json


class AggregatorAgent:
    def __init__(self):
        self.name = "aggregator"
        self.llm = AzureChatOpenAI(
            azure_endpoint=settings.azure_openai_endpoint,
            api_key=settings.azure_openai_api_key,
            api_version=settings.azure_openai_api_version,
            deployment_name=settings.azure_openai_deployment,
            temperature=0.1,
        )
    
    async def aggregate_results(self, state: ConversationState) -> ConversationState:
        logger.info_structured(
            "Aggregator agent started",
            conversation_id=state.get("conversation_id"),
            tool_results_count=len(state.get("tool_results", []))
        )
        
        tool_results = state.get("tool_results", [])
        query = state.get("current_query", "")
        
        if not tool_results:
            state["aggregated_data"] = {
                "summary": "No tool results to aggregate",
                "data": {}
            }
            return state
        
        successful_results = [r for r in tool_results if r.get("success")]
        failed_results = [r for r in tool_results if not r.get("success")]
        
        system_prompt = """You are an aggregator agent. Combine and structure the tool execution results.

Extract key information, identify patterns, and organize the data for further reasoning.

Respond in JSON format:
{
    "summary": "Brief summary of aggregated data",
    "key_findings": ["finding1", "finding2"],
    "data": {
        "key1": "value1",
        "key2": "value2"
    },
    "metrics": {},
    "issues": []
}"""
        
        results_text = json.dumps(successful_results, indent=2)
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"""User query: {query}

Tool results:
{results_text}

Aggregate and structure this data.""")
        ]
        
        try:
            response = await self.llm.ainvoke(messages)
            
            # Handle JSON wrapped in markdown code blocks
            content = response.content.strip()
            if content.startswith("```json"):
                # Extract JSON from markdown block
                lines = content.split('\n')
                if len(lines) > 1 and lines[-1].strip() == "```":
                    json_content = '\n'.join(lines[1:-1])
                else:
                    json_content = '\n'.join(lines[1:])
                aggregated = json.loads(json_content)
            else:
                aggregated = json.loads(content)
            
            if failed_results:
                aggregated["failed_tools"] = [
                    {
                        "tool": r.get("tool_name"),
                        "error": r.get("error")
                    }
                    for r in failed_results
                ]
            
            state["aggregated_data"] = aggregated
            
            logger.info_structured(
                "Aggregation completed",
                conversation_id=state.get("conversation_id"),
                key_findings_count=len(aggregated.get("key_findings", [])),
                has_issues=len(aggregated.get("issues", [])) > 0
            )
            
        except Exception as e:
            logger.error_structured(
                "Aggregation failed",
                error=str(e),
                conversation_id=state.get("conversation_id")
            )
            
            state["aggregated_data"] = {
                "summary": "Aggregation failed",
                "data": {
                    "raw_results": successful_results
                },
                "error": str(e)
            }
            state["errors"].append(f"Aggregation error: {str(e)}")
        
        # Add execution trace tracking (even in error case)
        state["execution_trace"]["agents_called"].append(self.name)
        state["execution_trace"]["timestamps"][self.name] = datetime.utcnow().isoformat()
        
        return state
