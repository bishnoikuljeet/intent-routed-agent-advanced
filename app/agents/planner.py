from typing import Dict, Any, List, Optional
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_openai import AzureOpenAIEmbeddings
from app.schemas.state import ConversationState
from app.schemas.models import ExecutionPlan, ExecutionStep
from app.core.config import settings
from app.core.logging import logger
from app.services import LLMService, ToolDiscoveryService
from app.services.context_service import ContextService
from datetime import datetime
import json


class PlannerAgent:
    def __init__(self, tool_registry=None, tool_discovery_service=None):
        self.name = "planner"
        self.tool_registry = tool_registry
        self.llm_service = LLMService()
        
        # Use shared ToolDiscoveryService if provided, otherwise create new one
        if tool_discovery_service is not None:
            self.tool_discovery = tool_discovery_service
            logger.info_structured("PlannerAgent using shared ToolDiscoveryService")
        else:
            # Fallback: create own instance (for backward compatibility)
            try:
                self.embeddings = AzureOpenAIEmbeddings(
                    azure_endpoint=settings.azure_embedding_openai_endpoint,
                    api_key=settings.azure_embedding_openai_api_key,
                    api_version=settings.azure_embedding_openai_api_version,
                    deployment=settings.azure_embedding_openai_deployment
                )
                logger.info_structured("PlannerAgent embeddings configured")
            except Exception as e:
                logger.warning_structured(
                    "Failed to initialize embeddings in PlannerAgent",
                    error=str(e)
                )
                self.embeddings = None
            
            self.tool_discovery = ToolDiscoveryService(embeddings=self.embeddings)
            logger.warning_structured("PlannerAgent created own ToolDiscoveryService (not using shared instance)")
        
        self.context_service = ContextService()

    async def create_plan(self, state: ConversationState) -> ConversationState:
        logger.info_structured(
            "Enhanced planner agent started",
            conversation_id=state.get("conversation_id"),
            intent=state.get("detected_intent"),
            context_enhanced=state.get("context_enhanced", False)
        )

        query = state.get("current_query", "")
        intent = state.get("detected_intent", "general_query")
        entities = state.get("extracted_entities", {})
        context_enhanced = state.get("context_enhanced", False)

        # Special handling for vague database queries
        if intent == "database_query":
            vague_patterns = [
                r"^show\s+(me\s+)?orders?$",
                r"^(list|get)\s+customers?$",
                r"^sales\s+report$",
                r"^inventory$",
                r"^show\s+(me\s+)?products?$",
                r"^(list|get)\s+items?$"
            ]
            
            import re
            is_vague = any(re.match(pattern, query.lower().strip()) for pattern in vague_patterns)
            
            if is_vague:
                logger.info_structured(
                    "Vague database query detected",
                    conversation_id=state.get("conversation_id"),
                    query=query
                )
                
                # Generate helpful clarification
                clarification = self._generate_db_clarification(query)
                
                empty_plan = ExecutionPlan(
                    reasoning="Database query is too vague, needs clarification",
                    steps=[],
                    estimated_duration=0.1,
                    requires_parallel=False
                )
                
                state["execution_plan"] = empty_plan
                state["needs_clarification"] = True
                state["missing_info"] = {
                    "reasoning": "Database query is too vague",
                    "clarification_question": clarification
                }
                state["planning_failed"] = False
                
                return state
        
        # Apply context enhancement if not already done
        if not context_enhanced:
            messages = state.get("messages", [])
            enhanced_query = await self.context_service.enhance_query_with_context(query, messages)
            
            if enhanced_query != query:
                logger.info_structured(
                    "Planner enhanced query with context",
                    original_query=query,
                    enhanced_query=enhanced_query
                )
                query = enhanced_query
                state["context_enhanced"] = True

        # Get available tools for analysis using tool discovery service
        available_tools = await self.tool_discovery.discover_all_tools()
        
        # Filter tools based on intent to improve tool selection accuracy
        filtered_tools = self._filter_tools_by_intent(available_tools, intent)
        
        # Convert to dict format for compatibility
        available_tools_dict = {tool['name']: tool for tool in filtered_tools}

        # Skip completeness check if context was already enhanced
        if not context_enhanced:
            # Use LLMService for query analysis
            analysis_data = await self._analyze_query_completeness(query, intent, entities, available_tools_dict)

            logger.info_structured(
                "LLM query analysis completed",
                needs_clarification=analysis_data.get("needs_clarification"),
                confidence=analysis_data.get("confidence")
            )

            # Only require clarification if confidence is reasonable AND truly missing critical info
            # Lowered threshold from 0.8 to 0.4 to catch more vague queries early
            if analysis_data.get("needs_clarification") and analysis_data.get("confidence", 0) > 0.4:
                logger.info_structured(
                    "LLM detected missing information with high confidence",
                    conversation_id=state.get("conversation_id"),
                    missing_info=analysis_data
                )

                # Create an empty plan but set clarification needed flag
                empty_plan = ExecutionPlan(
                    reasoning=analysis_data.get("reasoning"),
                    steps=[],
                    estimated_duration=0.1,
                    requires_parallel=False
                )

                state["execution_plan"] = empty_plan
                state["needs_clarification"] = True
                state["missing_info"] = analysis_data
                state["planning_failed"] = False  # This is not a failure, just needs clarification

                logger.info_structured(
                    "Clarification needed flag set (LLM-powered)",
                    conversation_id=state.get("conversation_id"),
                    clarification_type=analysis_data.get("clarification_type", "general")
                )

                return state

        # Continue with normal planning if no clarification needed or if context was enhanced
        logger.info_structured(
            "Creating execution plan",
            conversation_id=state.get("conversation_id"),
            query=query,
            context_enhanced=context_enhanced
        )

        system_prompt = f"""You are an intelligent planning agent. Analyze the user's query and create an OPTIMIZED execution plan that maximizes parallelism while respecting dependencies.

⚠️ CRITICAL RULE FOR DATABASE QUERIES:
- If user asks "how many orders" or "total" WITHOUT specifying dates → Use query_database tool
- NEVER add arbitrary date ranges (like 2023-01-01 to 2023-12-31) when user doesn't specify dates
- "How many orders do we have in total?" → query_database, NOT get_sales_summary
- Only use get_sales_summary when user explicitly mentions a date range

Available tools:
{json.dumps(available_tools_dict, indent=2)}

User query: {query}
Detected intent: {intent}
Extracted entities: {json.dumps(entities)}

=== EXECUTION STRATEGY ===

1. PARALLEL: Independent operations → same parallel_group
2. SEQUENTIAL: Dependent operations → higher parallel_group number  
3. REFERENCE: Use ${{step_X.field_name}} for dependencies

=== EXAMPLES ===

Parallel: "Get multiple independent metrics" → All in parallel_group 1
Sequential: "Get data then process it" → Group 1 (retrieve), Group 2 (process using ${{step_1.value}})
Hybrid: "Get multiple items then aggregate" → Group 1 (multiple parallel), Group 2 (aggregate using ${{step_1.value}}, ${{step_2.value}}, etc.)

DYNAMIC TOOL SELECTION FRAMEWORK:

1. ANALYZE USER INTENT:
   - Identify key entities: order IDs, customer names, product SKUs, dates, territories
   - Determine primary goal: retrieve details, search lists, get summaries, check status

2. MATCH TOOLS BY CAPABILITY:
   - Read each tool's description and input schema
   - Match query intent to tool capabilities
   - Extract required parameters from natural language

3. PARAMETER EXTRACTION STRATEGY:
   - Order IDs: Extract any alphanumeric patterns (SO-####, ####, order numbers)
   - Names: Extract proper nouns and quoted strings
   - Dates: Parse natural language dates and convert to required format
   - Quantities: Extract numbers and units
   - Locations: Extract place names and territories

4. MULTI-STEP PLANNING:
   - If tool requires specific ID but query provides descriptive name:
     Step 1: Use search tool to find ID
     Step 2: Use ID with target tool
   - Use ${{step_X.field_name}} references for dependencies

5. FALLBACK STRATEGY:
   - If no exact tool match, use query_database for natural language queries
   - If multiple tools possible, choose most specific one
   - If uncertain, prefer tools with fewer required parameters

6. ADAPTIVE MAPPING:
   - Map query keywords to tool capabilities dynamically
   - "details", "information", "show" → lookup tools
   - "find", "search", "list" → search tools  
   - "summary", "total", "count", "average" → aggregation tools
   - "status", "check", "verify" → status tools

7. CONCRETE MAPPING EXAMPLES:
   - "total sales" + date range → get_sales_summary with dates
   - "how many orders" + date range → get_sales_summary with dates
   - "average order value" + date range → get_sales_summary with dates
   - "total sales/average value" WITHOUT dates → query_database (natural language)
   - "how many orders" WITHOUT dates → query_database (natural language)
   - "details of order", "order information" → get_order_details
   - "find customer", "list customers" → search_customers
   - "orders for customer" → search_customers → get_customer_orders (multi-step)
   - "low stock", "reorder" → get_low_stock_items
   - "find product" → search_inventory

8. DATE HANDLING STRATEGY - CRITICAL:
   - Queries with specific dates → Use get_sales_summary with extracted dates
   - Queries with "total" but NO dates → Use query_database (NOT get_sales_summary)
   - NEVER invent or assume date ranges when user doesn't specify them
   - "How many orders total" = query_database, NOT get_sales_summary with random dates
   - "Average order value" without dates = query_database, NOT get_sales_summary
   - If you must use get_sales_summary without dates, DO NOT add arbitrary year defaults


=== FIELD REFERENCE GUIDE ===
Common result fields to reference:
- service_metrics: value (current metric value), threshold (alert threshold), unit, timestamp, service
- capacity_planning: current_usage, predicted_usage, capacity_limit, days_until_full, growth_rate
- semantic_search: results, total_found
- compare_values: result, difference
- statistics_summary: mean, median, std_dev
- trend_analysis: trend, slope, forecast, confidence_interval
- anomaly_detection: anomalies, anomaly_count, anomaly_percentage

IMPORTANT TOOL CAPABILITIES:
- capacity_planning: Returns BOTH current usage AND forecast predictions in single call
- slo_tracking: Returns BOTH current compliance AND historical trends

IMPORTANT: When comparing metrics with thresholds, use BOTH value and threshold from the same step:
- Correct: {{"value1": "${{step_1.value}}", "value2": "${{step_1.threshold}}", "comparison_type": "greater"}}
- Wrong: {{"value1": "${{step_1.value}}", "value2": "threshold_auth", "comparison_type": "greater"}}

IMPORTANT: For arrays of values, use proper reference format:
- Correct: {{"values": ["${{step_1.predicted_usage}}", "${{step_2.predicted_usage}}"]}}
- Wrong: {{"values": "${{step_1.predicted_usage}}, ${{step_2.predicted_usage}}"}}

=== RESPONSE FORMAT ===
{{
    "reasoning": "Brief explanation of your execution strategy and why you chose parallel vs sequential",
    "steps": [
        {{
            "step_number": 1,
            "description": "Clear description of what this step does",
            "tool_name": "exact_tool_name",
            "tool_params": {{"param1": "value1", "param2": "${{step_X.field}}"}},
            "parallel_group": 1,
            "depends_on": []
        }}
    ],
    "estimated_duration": 2.5,
    "requires_parallel": true
}}

CRITICAL: Complete your entire JSON response. Do not truncate. Ensure all brackets, braces, and quotes are properly closed. The response must be valid JSON.

IMPORTANT JSON FORMATTING RULES:
- Use ONLY double quotes for strings (never single quotes)
- Escape any quotes inside strings with backslash: \\"
- Do not use smart quotes (', ')
- Do not truncate your response
- Ensure all braces and brackets are properly paired
- No trailing commas in JSON objects/arrays

STEPS:
1. Identify operations needed
2. Check dependencies between them
3. Group independent operations (same parallel_group)
4. Order dependent operations (higher parallel_group)
5. Add result references for dependencies"""

        # Enhance prompt for retries
        retry_count = state.get("retry_count", 0)
        if retry_count > 0:
            # Add retry-specific instructions
            retry_prompt = f"""

=== RETRY INSTRUCTIONS ===
This is retry attempt #{retry_count + 1}. Previous attempt failed.
Please ensure:
1. Generate VALID JSON only - no markdown formatting, no extra text
2. Use simple, clear descriptions
3. For vague queries like "what's the status", use service_status tool
4. Double-check all quotes and commas in JSON
5. Keep it simple - one tool is usually enough

CRITICAL: Respond with ONLY valid JSON, nothing else."""
            system_prompt += retry_prompt

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Create an execution plan for: {query}")
        ]

        try:
            # Use LLM service properly - convert tools dict to list
            tools = list(available_tools_dict.values()) if available_tools_dict else []
            plan_data = await self.llm_service.generate_execution_plan(
                query=query,
                tools=tools,
                intent=intent
            )
            
            # Parse plan_data to create ExecutionPlan
            steps = [ExecutionStep(**step) for step in plan_data.get("steps", [])]
            plan = ExecutionPlan(
                steps=steps,
                estimated_duration=plan_data.get("estimated_duration", 0),
                requires_parallel=plan_data.get("requires_parallel", False)
            )
            
            state["execution_plan"] = plan
            state["estimated_duration"] = plan.estimated_duration
            
            logger.info_structured(
                "Planner completed via service",
                conversation_id=state.get("conversation_id"),
                steps_count=len(steps)
            )

            # Execution plan already set above - no duplicate code needed

        except json.JSONDecodeError as e:
            logger.error_structured(
                "Planning JSON parsing failed",
                conversation_id=state.get("conversation_id"),
                error=str(e),
                plan_data_preview=str(plan_data)[:200] + "..." if len(str(plan_data)) > 200 else str(plan_data)
            )

            # Check if we should retry instead of using fallback
            retry_count = state.get("retry_count", 0)
            max_retries = state.get("max_retries", 2)

            if retry_count < max_retries:
                # Don't create fallback plan - let retry mechanism handle it
                logger.info_structured(
                    "JSON parsing failed, will trigger retry",
                    conversation_id=state.get("conversation_id"),
                    retry_count=retry_count,
                    max_retries=max_retries
                )
                state["execution_plan"] = []  # Empty plan signals retry needed
                state["errors"].append(f"JSON parsing error: {str(e)}")
                state["planning_failed"] = True  # Flag for retry logic
            else:
                # After max retries - use LLM-generated minimal plan
                logger.warning_structured(
                    "Max retries reached, generating minimal generic plan",
                    conversation_id=state.get("conversation_id")
                )

                # Use LLM to generate a minimal plan based on available tools
                minimal_plan = await self._generate_minimal_plan(query, available_tools_dict)
                state["execution_plan"] = minimal_plan
                state["errors"].append(f"JSON parsing error after retries: {str(e)}")
                return state

        except Exception as e:
            logger.error_structured(
                "Planning failed",
                error=str(e),
                conversation_id=state.get("conversation_id")
            )

            # Check if we should retry instead of using fallback
            retry_count = state.get("retry_count", 0)
            max_retries = state.get("max_retries", 2)

            if retry_count < max_retries:
                # Don't create a fallback plan - let the retry mechanism handle it
                state["execution_plan"] = []  # Empty plan signals retry needed
                state["errors"].append(f"Planning error: {str(e)}")
                state["planning_failed"] = True  # Flag for retry logic
            else:
                # After max retries - generate minimal plan using LLM
                logger.warning_structured(
                    "Max retries reached after planning error, generating minimal plan",
                    conversation_id=state.get("conversation_id")
                )
                minimal_plan = await self._generate_minimal_plan(query, available_tools_dict)
                state["execution_plan"] = minimal_plan
                state["errors"].append(f"Planning error: {str(e)} (max retries reached)")

        # Add execution trace tracking (even in error case)
        state["execution_trace"]["agents_called"].append(self.name)
        state["execution_trace"]["timestamps"][self.name] = datetime.utcnow().isoformat()

        logger.info_structured(
            "Planner agent completed",
            conversation_id=state.get("conversation_id"),
            plan_steps=len(state["execution_plan"]) if isinstance(state["execution_plan"], list) else len(state["execution_plan"].steps) if hasattr(state["execution_plan"], 'steps') else 0
        )

        return state
    
    def _filter_tools_by_intent(self, tools: List[Dict[str, Any]], intent: str) -> List[Dict[str, Any]]:
        """
        Filter tools based on detected intent to improve tool selection accuracy.
        
        Args:
            tools: List of all available tools
            intent: Detected user intent
            
        Returns:
            Filtered list of tools relevant to the intent
        """
        # Define intent-to-server mapping
        intent_tool_mapping = {
            "knowledge_lookup": ["knowledge", "language"],  # Documentation, search, translation
            "metrics_lookup": ["observability", "utility"],  # Metrics, monitoring, calculations
            "calculation_compare": ["utility"],  # Calculations, comparisons
            "data_validation": ["utility"],  # Data validation, format checking
            "system_question": ["system"],  # System tools
            "database_query": ["database"],  # Database retrieval tools
            "general_query": None  # No filtering for general queries
        }
        
        # Get relevant servers for this intent
        relevant_servers = intent_tool_mapping.get(intent)
        
        # If no specific mapping or general query, return all tools
        if relevant_servers is None:
            return tools
        
        # Filter tools by server
        filtered = []
        for tool in tools:
            # Extract server from tool metadata or name
            server = tool.get('server', '')
            
            # If server info not in tool dict, try to infer from description
            if not server:
                desc = tool.get('description', '').lower()
                if any(keyword in desc for keyword in ['documentation', 'search', 'knowledge', 'policy']):
                    server = 'knowledge'
                elif any(keyword in desc for keyword in ['metric', 'monitoring', 'latency', 'error', 'slo']):
                    server = 'observability'
                elif any(keyword in desc for keyword in ['compare', 'calculate', 'percentage', 'statistics']):
                    server = 'utility'
                elif any(keyword in desc for keyword in ['system', 'agent', 'workflow']):
                    server = 'system'
            
            # Include tool if its server matches the intent
            if server in relevant_servers:
                filtered.append(tool)
        
        # Log filtering results
        logger.info_structured(
            "Filtered tools by intent",
            intent=intent,
            total_tools=len(tools),
            filtered_tools=len(filtered),
            relevant_servers=relevant_servers
        )
        
        return filtered if filtered else tools  # Return all if filtering resulted in empty list
    
    async def _analyze_query_completeness(self, query: str, intent: str, entities: dict, available_tools: dict) -> dict:
        """
        Use LLMService to analyze query completeness.
        No rule-based heuristics.
        """
        try:
            # Convert available tools dict to list for service
            tools = list(available_tools.values()) if available_tools else []
            
            # Use LLM service for completeness check
            result = await self.llm_service.check_completeness(
                query=query,
                tools=tools
            )
            
            # Convert to expected format
            return {
                "needs_clarification": not result.get("is_complete", True),
                "clarification_type": "missing_info" if not result.get("is_complete", True) else "complete",
                "missing_information": result.get("missing_info", []),
                "reasoning": result.get("reasoning", "Query analysis completed"),
                "suggested_examples": [result.get("suggested_clarification", "")] if not result.get("is_complete", True) else [],
                "confidence": result.get("confidence", 0.7)
            }
            
        except Exception as e:
            logger.error_structured(
                "LLM completeness check failed",
                error=str(e)
            )
            return {
                "needs_clarification": False,
                "clarification_type": "complete",
                "missing_information": [],
                "reasoning": "Default due to error",
                "suggested_examples": [],
                "confidence": 0.5
            }
    
    def _generate_db_clarification(self, query: str) -> str:
        """Generate helpful clarification question for vague database queries"""
        
        query_lower = query.lower()
        
        if "order" in query_lower:
            return """Which orders would you like to see? Please specify:
- A specific order number (e.g., SO-2024-001)
- A date range (e.g., orders from March 2024)
- A customer name"""
        
        elif "customer" in query_lower:
            return """Which customers are you looking for? Please specify:
- Customer name (e.g., Acme Corporation)
- Territory (Northeast, Southeast, Midwest, West, Southwest)
- Customer type (enterprise, mid-market, small-business)"""
        
        elif "sales" in query_lower:
            return """What sales information do you need? Please specify:
- Date range (e.g., March 2024 or 2024-03-01 to 2024-03-31)
- Specific customer or sales rep
- Type of summary (total sales, order count, average order value)"""
        
        elif any(word in query_lower for word in ["inventory", "product", "item", "stock"]):
            return """What inventory information do you need? Please specify:
- Specific product SKU or name
- Category
- Stock status (e.g., low stock items)
- Search criteria"""
        
        return "Could you provide more details about what you're looking for? Please specify filters, date ranges, or specific identifiers."
    
    async def _generate_minimal_plan(self, query: str, available_tools: dict) -> ExecutionPlan:
        """
        Generate a minimal execution plan with actual tool execution.
        Enhanced to create working plans instead of empty ones.
        """
        try:
            # Select the most relevant tool based on query keywords
            query_lower = query.lower()
            selected_tool = None
            
            # Simple keyword-based tool selection
            for tool_name, tool_info in available_tools.items():
                tool_desc = tool_info.get('description', '').lower()
                tool_name_lower = tool_name.lower()
                
                if ('latency' in query_lower and 'latency' in tool_name_lower) or \
                   ('payment' in query_lower and 'service' in tool_desc) or \
                   ('metrics' in query_lower and 'metric' in tool_desc) or \
                   ('status' in query_lower and 'status' in tool_name_lower):
                    selected_tool = tool_info
                    break
            
            # If no specific tool found, pick the first available tool
            if not selected_tool and available_tools:
                selected_tool = list(available_tools.values())[0]
            
            if not selected_tool:
                # Create empty plan if no tools available
                return ExecutionPlan(
                    reasoning="No tools available for execution",
                    steps=[],
                    estimated_duration=0.1,
                    requires_parallel=False
                )
            
            # Generate a simple plan with one tool execution step
            tool_name = selected_tool['name']
            input_schema = selected_tool.get('input_schema', {})
            required_params = input_schema.get('required', [])
            
            # Create basic parameters
            # DO NOT use meaningless defaults - only add params with actual values
            # Leave params out of dict if no value can be inferred - this triggers clarification
            tool_params = {}
            for param in required_params:
                param_info = input_schema.get('properties', {}).get(param, {})
                param_type = param_info.get('type', 'string')
                
                # Only add parameter to dict if we have a meaningful value
                if param_type == 'string':
                    if 'service' in param.lower() and 'payment' in query_lower:
                        tool_params[param] = 'payment-service'
                    # Otherwise don't add to dict - missing params trigger clarification
                # For numbers and other types, don't add to dict unless we have actual values
                # Missing required params will be detected downstream and trigger clarification
            
            step = ExecutionStep(
                step_number=1,
                description=f"Execute {tool_name} to address the query",
                tool_name=tool_name,
                tool_params=tool_params,
                parallel_group=1,
                depends_on=[]
            )
            
            return ExecutionPlan(
                reasoning=f"Minimal plan generated to execute {tool_name} for query: {query[:50]}",
                steps=[step],
                estimated_duration=2.0,
                requires_parallel=False
            )
            
        except Exception as e:
            logger.error_structured(
                "Minimal plan generation failed",
                error=str(e)
            )
            # Return absolute minimal plan
            return ExecutionPlan(
                reasoning="Fallback plan due to error",
                steps=[],
                estimated_duration=0.1,
                requires_parallel=False
            )
