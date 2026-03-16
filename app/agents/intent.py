from typing import Dict, Any
from langchain_openai import AzureChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from app.schemas.state import ConversationState
from app.schemas.models import IntentClassification, IntentType
from app.core.config import settings
from app.core.logging import logger
from app.core.telemetry import telemetry
from datetime import datetime
import json
import time


class IntentAgent:
    def __init__(self):
        self.name = "intent"
        self.llm = AzureChatOpenAI(
            azure_endpoint=settings.azure_openai_endpoint,
            api_key=settings.azure_openai_api_key,
            api_version=settings.azure_openai_api_version,
            deployment_name=settings.azure_openai_deployment,
            temperature=0.1,
        )
    
    async def classify_intent(self, state: ConversationState) -> ConversationState:
        logger.info_structured(
            "Intent agent started",
            conversation_id=state.get("conversation_id"),
            query=state.get("current_query")
        )
        
        query = state.get("current_query", "")
        
        # Early detection of malicious database operations
        malicious_keywords = [
            "delete", "drop", "truncate", "alter", "update", "insert",
            "grant", "revoke", "exec", "execute", "modify", "remove"
        ]
        
        query_lower = query.lower()
        if any(keyword in query_lower for keyword in malicious_keywords):
            logger.warning_structured(
                "Malicious intent detected",
                conversation_id=state.get("conversation_id"),
                query=query
            )
            
            state["detected_intent"] = "general_query"
            state["extracted_entities"] = {}
            state["needs_clarification"] = True
            state["missing_info"] = {
                "reasoning": "Query contains forbidden database operations",
                "clarification_question": "I can only retrieve information from the database. I cannot modify, delete, or update data. How can I help you find information instead?"
            }
            state["execution_trace"]["agents_called"].append(self.name)
            state["execution_trace"]["timestamps"][self.name] = datetime.utcnow().isoformat()
            
            return state
        
        system_prompt = """You are an intent classification agent. Classify the user's query into one of these intents:

1. knowledge_lookup: Questions about documented information, policies, architecture, procedures, definitions, OR document operations
   - "What is our SLO?" → knowledge_lookup (asking about documented target)
   - "What services are in our architecture?" → knowledge_lookup (asking about documented design)
   - "How do I troubleshoot X?" → knowledge_lookup (asking about documented procedures)
   - "What is the definition of X?" → knowledge_lookup (asking about documented concepts)
   - "Compare the current architecture doc with the previous version" → knowledge_lookup (document versioning)
   - "Show me all versions of the API documentation" → knowledge_lookup (document versioning)
   - "What changed between v2.1 and v2.2?" → knowledge_lookup (document comparison)
   - "Who modified the security policy document?" → knowledge_lookup (document tracking)

2. metrics_lookup: Questions about current/live SYSTEM/SERVICE performance, monitoring data, or runtime metrics (NOT sales/business data)
   - "What is our current SLO compliance?" → metrics_lookup (asking about service performance)
   - "Are we meeting our SLO?" → metrics_lookup (asking about service targets)
   - "What is the latency right now?" → metrics_lookup (asking about service metrics)
   - "Show me recent error rates" → metrics_lookup (asking about service errors)
   - "Show me all active alerts for payment_service" → metrics_lookup (asking about service alerts)
   - "List alerts for auth_service" → metrics_lookup (asking about service monitoring)
   - NOTE: Questions about AGENT/TOOL health are system_question, NOT metrics_lookup
   - NOTE: Questions about sales, orders, customers, inventory are database_query, NOT metrics_lookup

3. calculation_compare: Query requiring NUMERIC calculations or NUMERIC comparisons
   - "Is 150ms greater than 100ms?" → calculation_compare (numeric comparison)
   - "Calculate percentage difference between 95% and 89%" → calculation_compare (numeric calculation)
   - "What's the trend in [100, 120, 140]?" → calculation_compare (statistical analysis)
   - NOTE: Document comparisons are NOT calculation_compare, they are knowledge_lookup

4. data_validation: Requests to validate, check, verify, or test data formats, structures, or content
   - "Check if this email format is valid" → data_validation (email format validation)
   - "Validate this phone number" → data_validation (phone number validation)
   - "Is this JSON structure correct?" → data_validation (JSON structure validation)
   - "Verify the data format" → data_validation (general format validation)
   - "Test if this input is valid" → data_validation (input validation)
   - "Check the format of X" → data_validation (format checking)

5. system_question: Query about THIS SYSTEM's internal components (agents, tools, workflows, registry)
   - "Is the planner agent healthy?" → system_question (asking about agent health)
   - "Check the status of all agents" → system_question (asking about agent status)
   - "What tools are available?" → system_question (asking about tool registry)
   - "Show me workflow status" → system_question (asking about workflow state)
   - "What parameters does tool X accept?" → system_question (asking about tool metadata)
   - NOTE: This is for the AI system itself, NOT business services/applications

6. database_query: Queries requiring database retrieval from sales or inventory systems
   - "Details of order SO-2024-001" → database_query (specific order lookup)
   - "Show me order number SO-2024-003" → database_query (order retrieval)
   - "List all customers in Northeast territory" → database_query (customer search)
   - "Show enterprise customers" → database_query (customer filtering)
   - "Find customer Acme Corporation" → database_query (customer search)
   - "Which products are low on stock?" → database_query (inventory query)
   - "Show me items that need reordering" → database_query (inventory status)
   - "Find product PROD-A100" → database_query (product search)
   - "What were total sales in March 2024?" → database_query (sales aggregation)
   - "Sales summary from 2024-03-01 to 2024-03-31" → database_query (sales reporting)
   - "How many orders do we have in total?" → database_query (order count aggregation)
   - "What is our average order value?" → database_query (sales metric calculation from DB)
   - "Show me the top 5 customers by order volume" → database_query (customer ranking from DB)
   - "Show me orders for customer Acme Corporation" → database_query (customer orders)
   - "Get order SO-2024-001 and show me the customer's other orders" → database_query (multi-step DB query)
   - "Show orders with products that are currently low in stock" → database_query (cross-database query)
   - NOTE: Database queries are about retrieving data from sales/inventory/customer databases, NOT about system/service metrics

7. general_query: General questions not fitting other categories

CRITICAL DISTINCTIONS:
- "What IS" (definition/policy) → knowledge_lookup
- "What IS our current/Are we" (live service state) → metrics_lookup
- "Compare documents/versions" → knowledge_lookup (NOT calculation_compare)
- "Compare numbers/metrics" → calculation_compare
- "Agent/tool/workflow health or status" → system_question (NOT metrics_lookup)
- "Business service health or status" → metrics_lookup (NOT system_question)
- "Alerts for business services (payment_service, auth_service, etc.)" → metrics_lookup (NOT system_question)
- "Alerts for agents/tools (planner agent, executor agent, etc.)" → system_question (NOT metrics_lookup)
- "Check/Validate/Verify/Test format/structure" → data_validation (NOT general_query)
- "Sales/orders/customers/inventory/products data" → database_query (NOT metrics_lookup)
- "Average order value/total sales/order count" → database_query (NOT metrics_lookup)

Extract relevant entities from the query.

Respond in JSON format:
{
    "intent": "intent_type",
    "confidence": 0.95,
    "entities": {"key": "value"},
    "reasoning": "explanation"
}"""
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Classify this query: {query}")
        ]
        
        try:
            start_time = time.time()
            response = await self.llm.ainvoke(messages)
            latency_ms = (time.time() - start_time) * 1000
            
            telemetry.record_llm_latency(self.name, latency_ms)
            
            if hasattr(response, 'response_metadata'):
                usage = response.response_metadata.get('token_usage', {})
                if usage:
                    telemetry.record_token_usage(
                        prompt_tokens=usage.get('prompt_tokens', 0),
                        completion_tokens=usage.get('completion_tokens', 0),
                        model=settings.azure_openai_deployment
                    )
            
            result = json.loads(response.content)
            
            classification = IntentClassification(
                intent=IntentType(result.get("intent", "general_query")),
                confidence=result.get("confidence", 0.5),
                entities=result.get("entities", {}),
                reasoning=result.get("reasoning", "")
            )
            
            state["detected_intent"] = classification.intent.value
            state["extracted_entities"] = classification.entities
            state["intent_history"].append({
                "intent": classification.intent.value,
                "confidence": classification.confidence,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            logger.info_structured(
                "Intent classified",
                conversation_id=state.get("conversation_id"),
                intent=classification.intent.value,
                confidence=classification.confidence,
                entities=classification.entities
            )
            
        except Exception as e:
            logger.error_structured(
                "Intent classification failed",
                error=str(e),
                conversation_id=state.get("conversation_id")
            )
            state["detected_intent"] = "general_query"
            state["extracted_entities"] = {}
            state["errors"].append(f"Intent classification error: {str(e)}")
        
        # Add execution trace tracking (only once at the end)
        state["execution_trace"]["agents_called"].append(self.name)
        state["execution_trace"]["timestamps"][self.name] = datetime.utcnow().isoformat()
        
        return state
