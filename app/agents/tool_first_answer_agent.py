"""
Tool-First Answer Agent - Generic Solution
Always requires tool execution or polite decline with capabilities
"""

import json
from typing import Dict, Any, List
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_openai import AzureOpenAIEmbeddings
from app.schemas.state import ConversationState
from app.core.config import settings
from app.core.logging import logger
from datetime import datetime
from app.services import LLMService, ToolDiscoveryService
from app.services.context_service import ContextService


class ToolFirstAnswerAgent:
    """
    Tool-First Answer Agent that requires tool execution for every response.
    Either executes tools with available data or politely declines with capabilities.
    Generic design that adapts to any tools without hardcoded logic.
    """
    
    def __init__(self):
        self.name = "tool_first_answer"
        self.llm_service = LLMService()
        
        # Initialize embeddings for RAG-based tools
        try:
            self.embeddings = AzureOpenAIEmbeddings(
                azure_endpoint=settings.azure_embedding_openai_endpoint,
                api_key=settings.azure_embedding_openai_api_key,
                api_version=settings.azure_embedding_openai_api_version,
                deployment=settings.azure_embedding_openai_deployment
            )
            logger.info_structured("ToolFirstAnswerAgent embeddings configured")
        except Exception as e:
            logger.warning_structured(
                "Failed to initialize embeddings in ToolFirstAnswerAgent",
                error=str(e)
            )
            self.embeddings = None
        
        self.tool_discovery = ToolDiscoveryService(embeddings=self.embeddings)
        self.context_service = ContextService()
        self.capability_cache = {}  # Cache generated capabilities
        
    async def answer(self, state: ConversationState) -> ConversationState:
        """
        Process query with tool-first approach.
        Uses existing tool results or generates polite decline.
        """
        logger.info_structured(
            "Tool-first answer agent started",
            conversation_id=state.get("conversation_id")
        )
        
        query = state.get("current_query", "")
        
        # Skip tool execution for empty queries
        if not query.strip():
            state["final_answer"] = self._generate_empty_query_response()
            return state
        
        try:
            # Check if tools were already executed in the workflow
            tool_results = state.get("tool_results", [])
            tools_executed = state.get("tools_executed", 0)
            
            logger.info_structured(
                "ToolFirstAnswerAgent checking existing results",
                conversation_id=state.get("conversation_id"),
                tools_executed=tools_executed,
                tool_results_count=len(tool_results),
                tool_results_sample=str(tool_results[:1]) if tool_results else "None",
                state_keys=list(state.keys()),
                has_tool_history="tool_history" in state,
                tool_history_count=len(state.get("tool_history", []))
            )
            
            # Check multiple indicators that tools were executed
            tool_history = state.get("tool_history", [])
            has_tool_results = tools_executed > 0 or len(tool_results) > 0 or len(tool_history) > 0
            
            if has_tool_results:
                # Tools already executed - use existing results
                logger.info_structured(
                    "Using existing tool results from workflow",
                    conversation_id=state.get("conversation_id"),
                    tool_results_count=len(tool_results)
                )
                
                # Use tool_results if available, otherwise extract from tool_history
                results_to_use = tool_results if tool_results else tool_history
                answer = await self._generate_answer_with_existing_tool_data(query, results_to_use, state)
                state["final_answer"] = answer
                state["has_tool_data"] = True
                
            else:
                # No tools executed - try context-aware tool execution or polite decline
                messages = state.get("messages", [])
                enhanced_query = await self.context_service.enhance_query_with_context(query, messages)
                tool_result = await self._attempt_tool_execution(enhanced_query, state)
                
                if tool_result["success"]:
                    # Tool executed successfully - generate answer with tool data
                    answer = await self._generate_answer_with_tool_data(query, tool_result, state)
                    state["final_answer"] = answer
                    state["tools_executed"] = state.get("tools_executed", 0) + 1
                    state["tool_results"] = state.get("tool_results", [])
                    state["tool_results"].append(tool_result)
                    state["has_tool_data"] = True
                    
                else:
                    # Tool execution failed - try enhanced context or generate polite decline
                    if enhanced_query != query:
                        # Try one more time with original query if context enhancement didn't work
                        tool_result_retry = await self._attempt_tool_execution(query, state)
                        if tool_result_retry["success"]:
                            answer = await self._generate_answer_with_tool_data(query, tool_result_retry, state)
                            state["final_answer"] = answer
                            state["tools_executed"] = state.get("tools_executed", 0) + 1
                            state["tool_results"] = state.get("tool_results", [])
                            state["tool_results"].append(tool_result_retry)
                            state["has_tool_data"] = True
                        else:
                            # Generate polite decline with capabilities
                            capabilities = await self._generate_capabilities_from_vector_db()
                            decline_response = await self._generate_polite_decline(query, capabilities, tool_result.get("missing_data"))
                            state["final_answer"] = decline_response
                            state["tools_executed"] = 0
                            state["has_tool_data"] = False
                    else:
                        # Generate polite decline with capabilities
                        capabilities = await self._generate_capabilities_from_vector_db()
                        decline_response = await self._generate_polite_decline(query, capabilities, tool_result.get("missing_data"))
                        state["final_answer"] = decline_response
                        state["tools_executed"] = 0
                        state["has_tool_data"] = False
            
            # Update metadata
            if state.get("metadata"):
                state["metadata"]["completed_at"] = datetime.utcnow().isoformat()
            
            logger.info_structured(
                "Tool-first answer completed",
                conversation_id=state.get("conversation_id"),
                tools_executed=state.get("tools_executed", 0),
                has_tool_data=state.get("has_tool_data", False)
            )
            
        except Exception as e:
            logger.error_structured(
                "Tool-first answer failed",
                error=str(e),
                conversation_id=state.get("conversation_id")
            )
            
            # Fallback to capabilities-based decline
            capabilities = await self._generate_capabilities_from_vector_db()
            state["final_answer"] = await self._generate_polite_decline(query, capabilities, "system_error")
            state["has_tool_data"] = False
        
        return state
    
    # Context enhancement methods moved to centralized ContextService
    
    async def _attempt_tool_execution(self, query: str, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Attempt to find and execute relevant tools for the query.
        Enhanced generic approach with better error handling and parameter validation.
        """
        try:
            # Discover available tools
            all_tools = await self.tool_discovery.discover_all_tools()
            
            if not all_tools:
                return {
                    "success": False,
                    "reason": "no_tools_available",
                    "missing_data": "No tools are currently available"
                }
            
            # Use LLM to identify relevant tools and extract parameters
            tool_selection = await self._select_tools_with_llm(query, all_tools)
            
            if not tool_selection["relevant_tools"]:
                return {
                    "success": False,
                    "reason": "no_relevant_tools",
                    "missing_data": tool_selection.get("missing_data", "No relevant tools found")
                }
            
            # Try to execute the most relevant tool with enhanced parameter handling
            selected_tool = tool_selection["relevant_tools"][0]
            
            # Extract parameters with better validation
            params = await self._extract_tool_parameters(selected_tool, query)
            
            # Validate required parameters before execution
            input_schema = selected_tool.get('input_schema', {})
            required_params = input_schema.get('required', [])
            missing_required = []
            
            for param in required_params:
                if param not in params or params[param] is None:
                    missing_required.append(param)
            
            if missing_required:
                # Try to infer missing parameters from context or use smart defaults
                enhanced_params = await self._enhance_parameters_with_context(selected_tool, params, query, state)
                
                # Re-check after enhancement
                still_missing = [p for p in required_params if p not in enhanced_params or enhanced_params[p] is None]
                
                if still_missing:
                    # Set clarification flags so answer agent generates follow-up questions
                    missing_info = {
                        "needs_clarification": True,
                        "clarification_type": "missing_parameters",
                        "missing_information": still_missing,
                        "reasoning": f"The {selected_tool['name']} tool requires these parameters: {', '.join(still_missing)}",
                        "suggested_examples": [f"Please provide values for: {', '.join(still_missing)}"],
                        "suggested_tool": selected_tool,
                        "extracted_params": enhanced_params
                    }
                    
                    return {
                        "success": False,
                        "reason": "missing_parameters",
                        "missing_data": f"Missing required parameters: {', '.join(still_missing)}",
                        "missing_info": missing_info
                    }
                
                params = enhanced_params
            
            # Execute the tool with validated parameters
            tool_result = await self._execute_selected_tool(selected_tool, query, state, params)
            
            return tool_result
            
        except Exception as e:
            logger.error_structured(
                "Tool execution attempt failed",
                error=str(e),
                query=query[:50]
            )
            return {
                "success": False,
                "reason": "execution_error",
                "missing_data": f"Tool execution error: {str(e)}"
            }
    
    async def _select_tools_with_llm(self, query: str, tools: List[Dict]) -> Dict[str, Any]:
        """
        Use LLM to select relevant tools for the query.
        Generic approach that works with any tool descriptions.
        """
        try:
            # Create tool descriptions for LLM
            tool_descriptions = []
            for i, tool in enumerate(tools):
                desc = f"{i+1}. {tool['name']}: {tool['description']}"
                if 'input_schema' in tool and 'properties' in tool['input_schema']:
                    params = list(tool['input_schema']['properties'].keys())
                    if params:
                        desc += f" (requires: {', '.join(params)})"
                tool_descriptions.append(desc)
            
            tools_text = "\n".join(tool_descriptions)
            
            # Use LLM to select relevant tools
            messages = [
                SystemMessage(content="You are a tool selection assistant. Analyze the user query and identify which tools can help. Return your response as JSON with 'relevant_tools' (list of tool indices) and 'missing_data' (what information is needed)."),
                HumanMessage(content=f"""
User Query: "{query}"

Available Tools:
{tools_text}

Analyze which tools can help with this query. For "compare" queries, use the compare_values tool. For "percentage" queries, use percentage_difference tool.

Respond with ONLY JSON format:
{{"relevant_tools": [tool_indices], "missing_data": "description if no tools found"}}

Example for comparison: {{"relevant_tools": [0], "missing_data": ""}}
Example for percentage: {{"relevant_tools": [1], "missing_data": ""}}
""")
            ]
            
            response = await self.llm_service.llm.ainvoke(messages)
            
            try:
                result = json.loads(response.content)
                relevant_indices = result.get("relevant_tools", [])
                
                # Convert indices back to tool objects
                relevant_tools = []
                for idx in relevant_indices:
                    if 0 <= idx < len(tools):
                        relevant_tools.append(tools[idx])
                
                return {
                    "relevant_tools": relevant_tools,
                    "missing_data": result.get("missing_data", "")
                }
                
            except json.JSONDecodeError:
                # Fallback: try to extract tool names from response
                response_text = response.content.lower()
                relevant_tools = []
                
                for tool in tools:
                    if tool['name'].lower() in response_text:
                        relevant_tools.append(tool)
                
                # Second fallback: direct keyword matching from query
                if not relevant_tools:
                    query_lower = query.lower()
                    if "compare" in query_lower:
                        relevant_tools = [tool for tool in tools if "compare" in tool['name'].lower()]
                    elif "percentage" in query_lower or "percent" in query_lower:
                        relevant_tools = [tool for tool in tools if "percentage" in tool['name'].lower()]
                    elif "validate" in query_lower or "json" in query_lower:
                        relevant_tools = [tool for tool in tools if "validation" in tool['name'].lower() or "parser" in tool['name'].lower()]
                
                return {
                    "relevant_tools": relevant_tools,
                    "missing_data": "Could not parse LLM response" if not relevant_tools else ""
                }
                
        except Exception as e:
            logger.error_structured(
                "LLM tool selection failed",
                error=str(e)
            )
            return {"relevant_tools": [], "missing_data": f"Tool selection error: {str(e)}"}
    
    async def _check_missing_parameters(self, tool: Dict[str, Any], query: str) -> List[str]:
        """
        Check if tool has all required parameters from the query.
        Generic parameter extraction using LLM.
        """
        try:
            input_schema = tool.get('input_schema', {})
            required_params = input_schema.get('required', [])
            
            if not required_params:
                return []  # No required parameters
            
            # Use LLM to extract parameters from query
            param_descriptions = []
            for param in required_params:
                param_info = input_schema.get('properties', {}).get(param, {})
                param_type = param_info.get('type', 'string')
                param_desc = param_info.get('description', '')
                param_descriptions.append(f"- {param} ({param_type}): {param_desc}")
            
            params_text = "\n".join(param_descriptions)
            
            messages = [
                SystemMessage(content="You are a parameter extraction assistant. Extract parameter values from user queries. Return JSON with parameter names and values."),
                HumanMessage(content=f"""
User Query: "{query}"

Tool: {tool['name']}
Required Parameters:
{params_text}

Extract values for these parameters from the query. If any parameter is missing, indicate it. Respond with JSON format:
{{"extracted_params": {{"param_name": "value", ...}}, "missing_params": ["param1", "param2"]}}
""")
            ]
            
            response = await self.llm_service.llm.ainvoke(messages)
            
            try:
                result = json.loads(response.content)
                return result.get("missing_params", [])
                
            except json.JSONDecodeError:
                # Fallback: check if required words are in query
                missing = []
                for param in required_params:
                    if param.lower() not in query.lower():
                        missing.append(param)
                return missing
                
        except Exception as e:
            logger.error_structured(
                "Parameter check failed",
                error=str(e)
            )
            return required_params  # Assume all are missing on error
    
    async def _execute_selected_tool(self, tool: Dict[str, Any], query: str, state: Dict[str, Any], params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Execute the selected tool with extracted parameters.
        Enhanced generic tool execution with comprehensive error handling.
        """
        try:
            # Use provided params or extract them
            if params is None:
                params = await self._extract_tool_parameters(tool, query)
            
            # Log execution attempt with parameter details
            logger.info_structured(
                "Attempting tool execution",
                tool_name=tool.get('name', 'unknown'),
                parameters=params,
                query=query[:50]
            )
            
            # Execute the tool
            result = await self.tool_discovery.execute_tool(tool['name'], params)
            
            logger.info_structured(
                "Tool execution successful",
                tool_name=tool.get('name', 'unknown'),
                result_type=type(result).__name__
            )
            
            return {
                "success": True,
                "tool_name": tool['name'],
                "tool_description": tool['description'],
                "parameters": params,
                "result": result,
                "query": query
            }
            
        except Exception as e:
            error_msg = str(e)
            logger.error_structured(
                "Tool execution failed",
                tool_name=tool.get('name', 'unknown'),
                error=error_msg,
                parameters=params if params else "none"
            )
            
            # Analyze error type for better handling
            if "missing" in error_msg.lower() or "required" in error_msg.lower():
                return {
                    "success": False,
                    "reason": "parameter_error",
                    "missing_data": f"Parameter error: {error_msg}",
                    "extracted_params": params if params else {}
                }
            elif "not found" in error_msg.lower() or "exists" in error_msg.lower():
                return {
                    "success": False,
                    "reason": "tool_not_available",
                    "missing_data": f"Tool unavailable: {error_msg}"
                }
            else:
                return {
                    "success": False,
                    "reason": "execution_failed",
                    "missing_data": f"Execution failed: {error_msg}"
                }
    
    async def _extract_tool_parameters(self, tool: Dict[str, Any], query: str) -> Dict[str, Any]:
        """
        Extract parameters for tool execution from query.
        Enhanced generic parameter extraction with better error handling.
        """
        try:
            input_schema = tool.get('input_schema', {})
            properties = input_schema.get('properties', {})
            
            if not properties:
                return {}
            
            # Build parameter descriptions for LLM
            param_descriptions = []
            required_params = input_schema.get('required', [])
            
            for param_name, param_info in properties.items():
                param_type = param_info.get('type', 'string')
                param_desc = param_info.get('description', '')
                required = param_name in required_params
                param_descriptions.append(f"- {param_name} ({param_type}, required={required}): {param_desc}")
            
            params_text = "\n".join(param_descriptions)
            tool_name = tool.get('name', 'unknown')
            
            messages = [
                SystemMessage(content="You are a parameter extraction assistant. Extract parameter values from user queries for tool execution. Return JSON with parameter names and values. For missing required parameters, use null values and include them in the response."),
                HumanMessage(content=f"""
User Query: "{query}"

Tool: {tool_name}
Parameters:
{params_text}

Extract appropriate values for these parameters from the query. For required parameters that are missing, use null. For optional parameters, infer reasonable defaults if possible. Respond with JSON format:
{{"param_name": "value_or_null", ...}}

IMPORTANT: Always include all required parameters in your response, even if their value is null.
""")
            ]
            
            response = await self.llm_service.llm.ainvoke(messages)
            
            try:
                params = json.loads(response.content)
                
                # Validate that all required parameters are present
                missing_required = []
                for param in required_params:
                    if param not in params:
                        missing_required.append(param)
                        params[param] = None
                
                if missing_required:
                    logger.warning_structured(
                        "Missing required parameters in extraction",
                        tool_name=tool_name,
                        missing_params=missing_required,
                        extracted_params=list(params.keys())
                    )
                
                return params
                
            except json.JSONDecodeError:
                # Fallback: simple regex extraction for common patterns
                logger.warning_structured(
                    "Failed to parse parameter extraction, using regex fallback",
                    tool_name=tool_name,
                    response_content=response.content[:100]
                )
                return self._extract_parameters_with_regex(tool, query)
                
        except Exception as e:
            logger.error_structured(
                "Parameter extraction failed",
                tool_name=tool.get('name', 'unknown'),
                error=str(e)
            )
            # Return empty dict but include required params as null to prevent execution errors
            input_schema = tool.get('input_schema', {})
            required_params = input_schema.get('required', [])
            return {param: None for param in required_params}
    
    async def _enhance_parameters_with_context(self, tool: Dict[str, Any], params: Dict[str, Any], query: str, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enhance extracted parameters with context and smart defaults.
        Generic parameter enhancement that works with any tool.
        """
        try:
            enhanced_params = params.copy()
            input_schema = tool.get('input_schema', {})
            properties = input_schema.get('properties', {})
            
            # Use context service to get relevant information
            messages = state.get('messages', [])
            context_enhanced_query = await self.context_service.enhance_query_with_context(query, messages)
            
            # Try to extract missing parameters from enhanced context
            for param_name, param_info in properties.items():
                if param_name not in enhanced_params or enhanced_params[param_name] is None:
                    param_type = param_info.get('type', 'string')
                    param_desc = param_info.get('description', '')
                    
                    # Smart defaults based on parameter type and description
                    # Only set defaults for specific, meaningful cases - avoid meaningless defaults
                    if param_type == 'string':
                        if 'service' in param_desc.lower() and 'payment' in query.lower():
                            enhanced_params[param_name] = 'payment-service'
                        elif 'time' in param_desc.lower() or 'date' in param_desc.lower():
                            enhanced_params[param_name] = 'current'
                        # Otherwise leave as None - don't use meaningless defaults
                    elif param_type == 'number':
                        # DO NOT set default numeric values - they are meaningless
                        # Comparisons with 0, calculations with 0, etc. provide no value
                        # Leave as None to trigger proper clarification
                        pass
                    elif param_type == 'boolean':
                        # Only set boolean default if it makes sense in context
                        if 'enable' in param_desc.lower() or 'active' in param_desc.lower():
                            enhanced_params[param_name] = True
                    # For other types, leave as None to trigger clarification
            
            logger.info_structured(
                "Parameters enhanced with context",
                tool_name=tool.get('name', 'unknown'),
                original_params=list(params.keys()),
                enhanced_params=list(enhanced_params.keys())
            )
            
            return enhanced_params
            
        except Exception as e:
            logger.error_structured(
                "Parameter enhancement failed",
                tool_name=tool.get('name', 'unknown'),
                error=str(e)
            )
            return params  # Return original params on failure
    
    def _extract_parameters_with_regex(self, tool: Dict[str, Any], query: str) -> Dict[str, Any]:
        """
        Extract parameters using regex patterns for common tools.
        Fallback method when LLM extraction fails.
        """
        import re
        
        params = {}
        tool_name = tool.get('name', '').lower()
        
        # Extract numbers from query
        numbers = re.findall(r'\b\d+\.?\d*\b', query)
        
        if 'compare' in tool_name and len(numbers) >= 2:
            params = {
                'value1': float(numbers[0]),
                'value2': float(numbers[1]),
                'comparison_type': 'greater_than'
            }
        elif 'percentage' in tool_name and len(numbers) >= 2:
            params = {
                'value1': float(numbers[0]),
                'value2': float(numbers[1])
            }
        elif 'validation' in tool_name or 'parser' in tool_name:
            # Extract JSON from query
            json_match = re.search(r'\{.*\}', query, re.DOTALL)
            if json_match:
                try:
                    import json
                    params['data'] = json.loads(json_match.group())
                except:
                    params['data'] = json_match.group()
            else:
                params['data'] = query
        else:
            # Generic: try to map numbers to parameters
            input_schema = tool.get('input_schema', {})
            properties = input_schema.get('properties', {})
            required = input_schema.get('required', [])
            
            param_names = list(properties.keys())
            for i, num in enumerate(numbers[:len(param_names)]):
                if i < len(param_names):
                    param_name = param_names[i]
                    param_type = properties[param_name].get('type', 'string')
                    if param_type == 'number':
                        params[param_name] = float(num)
                    else:
                        params[param_name] = num
        
        return params
    
    async def _generate_answer_with_existing_tool_data(self, query: str, tool_results: List[Dict], state: Dict[str, Any]) -> str:
        """
        Generate answer using existing tool results from workflow.
        """
        try:
            # Extract tool data from results
            tool_data = []
            for result in tool_results:
                if isinstance(result, dict) and 'result' in result:
                    tool_data.append({
                        'tool_name': result.get('tool_name', 'unknown'),
                        'result': result['result'],
                        'parameters': result.get('parameters', {})
                    })
            
            if not tool_data:
                # Fallback to generic response if no valid tool data
                return "I processed your query, but couldn't extract specific tool results. Please try rephrasing your request."
            
            # Generate answer using LLM with existing tool data
            tool_data_text = json.dumps(tool_data, indent=2)
            
            messages = [
                SystemMessage(content="You are a helpful assistant. Generate a clear, accurate answer based on the tool execution results provided. Explain what the tools did and what the results mean."),
                HumanMessage(content=f"""
User Query: "{query}"

Tool Execution Results:
{tool_data_text}

Generate a natural, helpful answer that:
1. Directly addresses the user's query
2. Explains what was calculated/analyzed
3. Presents the results clearly
4. Provides context for what the results mean

Keep it conversational and easy to understand.
""")
            ]
            
            response = await self.llm_service.llm.ainvoke(messages)
            return response.content.strip()
            
        except Exception as e:
            logger.error_structured(
                "Answer generation with existing tool data failed",
                error=str(e)
            )
            # Fallback response with raw tool data
            if tool_results:
                first_result = tool_results[0]
                return f"I used the {first_result.get('tool_name', 'tool')} to help with your query. The result was: {json.dumps(first_result.get('result', {}), indent=2)}"
            else:
                return "I processed your query but encountered an issue generating the response."
    
    async def _generate_capabilities_from_vector_db(self) -> str:
        """
        Generate system capabilities from vector DB (tools and files).
        Generic capability generation that adapts to any tools.
        """
        try:
            # Check cache first
            cache_key = "system_capabilities"
            if cache_key in self.capability_cache:
                return self.capability_cache[cache_key]
            
            # Get all available tools
            tools = await self.tool_discovery.discover_all_tools()
            
            # Generate capabilities description using LLM
            tool_descriptions = []
            for tool in tools:
                desc = f"• {tool['name']}: {tool['description']}"
                if 'input_schema' in tool and 'properties' in tool['input_schema']:
                    params = list(tool['input_schema']['properties'].keys())
                    if params:
                        desc += f" (uses: {', '.join(params[:3])}{'...' if len(params) > 3 else ''})"
                tool_descriptions.append(desc)
            
            tools_text = "\n".join(tool_descriptions)
            
            # Use LLM to generate natural capabilities description
            messages = [
                SystemMessage(content="You are a system capabilities generator. Create a natural, friendly description of what the system can do based on available tools."),
                HumanMessage(content=f"""
Available Tools:
{tools_text}

Generate a concise, friendly description of what this system can help users with. Focus on the main capabilities and use natural language. Keep it under 150 words.
""")
            ]
            
            response = await self.llm_service.llm.ainvoke(messages)
            capabilities = response.content.strip()
            
            # Cache the result
            self.capability_cache[cache_key] = capabilities
            
            return capabilities
            
        except Exception as e:
            logger.error_structured(
                "Capabilities generation failed",
                error=str(e)
            )
            return "I can help with various computational and data analysis tasks using specialized tools."
    
    async def _generate_polite_decline(self, query: str, capabilities: str, missing_data: str) -> str:
        """
        Generate polite decline response with capabilities and specific data requests.
        Includes follow-up questions to guide the user.
        """
        try:
            messages = [
                SystemMessage(content="You are a helpful assistant. When you can't help with a specific request, politely decline by explaining what you CAN do and what specific information you would need to help."),
                HumanMessage(content=f"""
User Query: "{query}"

System Capabilities:
{capabilities}

Missing Information: {missing_data}

Generate a polite response that:
1. Acknowledges the user's request
2. Explains what you can help with (based on capabilities)
3. Specifically asks for what information is needed
4. Is friendly and helpful

IMPORTANT - FOLLOW-UP QUESTIONS:
After your response, ALWAYS add 2-3 specific follow-up questions that:
- Guide the user to provide the missing information
- Give concrete examples of what they can ask
- Help them understand how to use the available capabilities

Format follow-up questions as:
**Follow-up questions:**
- [Specific question about missing info 1]
- [Example of what they can ask 2]
- [Alternative way to phrase their request 3]

Keep the response concise and natural.
""")
            ]
            
            response = await self.llm_service.llm.ainvoke(messages)
            return response.content.strip()
            
        except Exception as e:
            logger.error_structured(
                "Polite decline generation failed",
                error=str(e)
            )
            return f"I understand you're asking about: {query}. Based on my capabilities, I can help with: {capabilities}. To assist you better, could you provide more specific details?\n\n**Follow-up questions:**\n- What specific values would you like to work with?\n- Could you provide more details about what you're trying to accomplish?\n- Would you like to see examples of what I can help with?"
    
    async def _generate_answer_with_tool_data(self, query: str, tool_result: Dict[str, Any], state: Dict[str, Any]) -> str:
        """
        Generate answer using tool execution results.
        Generic answer generation that works with any tool data.
        """
        try:
            tool_name = tool_result["tool_name"]
            tool_description = tool_result["tool_description"]
            parameters = tool_result["parameters"]
            result = tool_result["result"]
            
            messages = [
                SystemMessage(content="You are a helpful assistant. Generate a clear, accurate answer based on tool execution results. Explain what the tool did and what the results mean."),
                HumanMessage(content=f"""
User Query: "{query}"

Tool Used: {tool_name}
Tool Description: {tool_description}
Parameters Used: {json.dumps(parameters, indent=2)}

Tool Results:
{json.dumps(result, indent=2)}

Generate a natural, helpful answer that:
1. Directly addresses the user's query
2. Explains what was calculated/analyzed
3. Presents the results clearly
4. Provides context for what the results mean

Keep it conversational and easy to understand.
""")
            ]
            
            response = await self.llm_service.llm.ainvoke(messages)
            return response.content.strip()
            
        except Exception as e:
            logger.error_structured(
                "Answer generation with tool data failed",
                error=str(e)
            )
            return f"I used the {tool_result.get('tool_name', 'tool')} to help with your query. The result was: {json.dumps(tool_result.get('result', {}), indent=2)}"
    
    def _generate_empty_query_response(self) -> str:
        """Generate response for empty queries."""
        return "I'd be happy to help you! Please let me know what you'd like to do, and I'll use the appropriate tools to assist you."
