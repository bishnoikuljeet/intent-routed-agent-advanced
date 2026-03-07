from typing import Dict, Any
from langchain_openai import AzureChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from app.schemas.state import ConversationState
from app.schemas.models import ReasoningOutput
from app.core.config import settings
from app.core.logging import logger
from datetime import datetime
import json


class ReasoningAgent:
    def __init__(self):
        self.name = "reasoning"
        self.llm = AzureChatOpenAI(
            azure_endpoint=settings.azure_openai_endpoint,
            api_key=settings.azure_openai_api_key,
            api_version=settings.azure_openai_api_version,
            deployment_name=settings.azure_openai_deployment,
            temperature=0.2,
        )
    
    async def reason(self, state: ConversationState) -> ConversationState:
        logger.info_structured(
            "Reasoning agent started",
            conversation_id=state.get("conversation_id")
        )
        
        query = state.get("current_query", "")
        aggregated_data = state.get("aggregated_data", {})
        intent = state.get("detected_intent", "")
        
        system_prompt = """You are a reasoning agent. Analyze the aggregated data and draw logical conclusions.

Apply domain knowledge, identify patterns, and make inferences based on the data.

For metrics analysis:
- Compare values against thresholds
- Identify anomalies
- Determine severity

For knowledge queries:
- Synthesize information
- Identify relevant details
- Connect related concepts

Respond in JSON format:
{
    "analysis": "Detailed analysis of the data",
    "conclusion": "Main conclusion",
    "supporting_evidence": ["evidence1", "evidence2"],
    "confidence": 0.9
}"""
        
        aggregated_text = json.dumps(aggregated_data, indent=2)
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"""User query: {query}
Intent: {intent}

Aggregated data:
{aggregated_text}

Provide reasoning and conclusions.""")
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
                reasoning_data = json.loads(json_content)
            else:
                reasoning_data = json.loads(content)
            
            reasoning = ReasoningOutput(
                analysis=reasoning_data.get("analysis", ""),
                conclusion=reasoning_data.get("conclusion", ""),
                supporting_evidence=reasoning_data.get("supporting_evidence", []),
                confidence=reasoning_data.get("confidence", 0.5)
            )
            
            state["reasoning_output"] = reasoning.dict()
            
            logger.info_structured(
                "Reasoning completed",
                conversation_id=state.get("conversation_id"),
                confidence=reasoning.confidence,
                evidence_count=len(reasoning.supporting_evidence)
            )
            
        except Exception as e:
            logger.error_structured(
                "Reasoning failed",
                error=str(e),
                conversation_id=state.get("conversation_id")
            )
            
            state["reasoning_output"] = {
                "analysis": "Reasoning failed",
                "conclusion": "Unable to draw conclusions",
                "supporting_evidence": [],
                "confidence": 0.0,
                "error": str(e)
            }
            state["errors"].append(f"Reasoning error: {str(e)}")
        
        # Add execution trace tracking (even in error case)
        state["execution_trace"]["agents_called"].append(self.name)
        state["execution_trace"]["timestamps"][self.name] = datetime.utcnow().isoformat()
        
        return state
