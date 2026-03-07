from typing import Dict, Any, List
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_openai import AzureOpenAIEmbeddings
from app.schemas.state import ConversationState
from app.core.config import settings
from app.core.logging import logger
from datetime import datetime
from app.services import LLMService, ToolDiscoveryService
import json
import time


class AnswerAgent:
    def __init__(self):
        self.name = "answer"
        self.llm_service = LLMService()
        
        # Initialize embeddings for RAG-based tools
        try:
            self.embeddings = AzureOpenAIEmbeddings(
                azure_endpoint=settings.azure_embedding_openai_endpoint,
                api_key=settings.azure_embedding_openai_api_key,
                api_version=settings.azure_embedding_openai_api_version,
                deployment=settings.azure_embedding_openai_deployment
            )
            logger.info_structured("AnswerAgent embeddings configured")
        except Exception as e:
            logger.warning_structured(
                "Failed to initialize embeddings in AnswerAgent",
                error=str(e)
            )
            self.embeddings = None
        
        self.tool_discovery = ToolDiscoveryService(embeddings=self.embeddings)
    
    async def answer(self, state: ConversationState) -> ConversationState:
        """
        Generate final answer using LLM with reasoning, aggregated data, and conversation context.
        """
        logger.info_structured(
            "Answer agent started",
            conversation_id=state.get("conversation_id")
        )
        
        query = state.get("current_query", "")
        reasoning_output = state.get("reasoning_output", "")
        aggregated_data = state.get("aggregated_data", {})
        confidence_score = state.get("confidence_score", 0.5)
        
        # Get conversation context for better responses
        conversation_context = state.get("metadata", {}).get("conversation_context", "")
        conversation_summary = state.get("conversation_summary", "")
        recent_messages = state.get("recent_messages", [])
        
        # Check if clarification is needed
        needs_clarification = state.get("needs_clarification", False)
        missing_info = state.get("missing_info", {})
        
        # Check if context was already inferred and enhanced
        context_inferred = state.get("context_inferred", False)
        
        # If context was inferred, skip clarification detection
        if context_inferred:
            logger.info_structured(
                "Skipping clarification detection - context already inferred",
                conversation_id=state.get("conversation_id"),
                enhanced_query=state.get("current_query", "")
            )
            needs_clarification = False
            missing_info = {}
        else:
            # Also check for indirect clarification needs using LLM intelligence
            tools_executed = state.get("tools_executed", 0)
            plan_steps = len(state.get("execution_plan", [])) if isinstance(state.get("execution_plan", []), list) else len(state.get("execution_plan", {}).get("steps", [])) if isinstance(state.get("execution_plan", {}), dict) else 0
            
            # Use LLM service to determine if clarification is needed
            if tools_executed == 0 and plan_steps == 0 and not needs_clarification:
                # Use service for completeness check
                tools = await self.tool_discovery.discover_all_tools()
                completeness_result = await self.llm_service.check_completeness(query, tools)
                
                indirect_clarification = {
                    "needs_clarification": not completeness_result.get("is_complete", True),
                    "clarification_type": "missing_info" if not completeness_result.get("is_complete", True) else "complete",
                    "missing_information": completeness_result.get("missing_info", []),
                    "reasoning": completeness_result.get("reasoning", ""),
                    "suggested_examples": [completeness_result.get("suggested_clarification", "")],
                    "is_out_of_scope": False
                }
                
                # Check if this is an out-of-scope request
                if indirect_clarification.get("is_out_of_scope", False):
                    logger.info_structured(
                        "Out-of-scope request detected",
                        conversation_id=state.get("conversation_id"),
                        query=query[:50],
                        max_similarity=indirect_clarification.get("reasoning", "")
                    )
                    # Return the denial response in the correct format
                    denial_response = indirect_clarification.get("denial_response", "I apologize, but I don't have the capability to help with that request.")
                    state["final_answer"] = denial_response
                    return state
                
                if indirect_clarification["needs_clarification"]:
                    logger.info_structured(
                        "LLM detected indirect clarification need",
                        conversation_id=state.get("conversation_id"),
                        tools_executed=tools_executed,
                        plan_steps=plan_steps,
                        query=query[:50],
                        llm_reasoning=indirect_clarification.get("reasoning", "N/A")[:100]
                    )
                    missing_info = indirect_clarification
                    needs_clarification = True
        
        # Initialize indirect_clarification for logging
        indirect_clarification = {}
        
        logger.info_structured(
            "Answer agent checking clarification",
            conversation_id=state.get("conversation_id"),
            needs_clarification=needs_clarification,
            missing_info_keys=list(missing_info.keys()) if missing_info else [],
            missing_info_present=bool(missing_info),
            indirect_clarification=indirect_clarification
        )
        
        # Try to infer missing information from conversation context
        if needs_clarification and missing_info and (conversation_context or recent_messages):
            logger.info_structured(
                "Context inference conditions met",
                conversation_id=state.get("conversation_id"),
                needs_clarification=needs_clarification,
                has_missing_info=bool(missing_info),
                has_conversation_context=bool(conversation_context),
                has_recent_messages=bool(recent_messages)
            )
            
            # Check if we've already tried context inference for this query
            context_retry_count = state.get("context_retry_count", 0)
            max_context_retries = 1  # Only try once per query
            
            if context_retry_count < max_context_retries:
                inferred_info = await self._infer_missing_info_from_context(query, missing_info, conversation_context, recent_messages)
                if inferred_info:
                    logger.info_structured(
                        "Successfully inferred missing information from context",
                        conversation_id=state.get("conversation_id"),
                        inferred_info=inferred_info
                    )
                    # Update the query with inferred information and retry
                    enhanced_query = await self._enhance_query_with_context(query, inferred_info, recent_messages)
                    
                    logger.info_structured(
                        "Enhanced query generated",
                        conversation_id=state.get("conversation_id"),
                        original_query=query,
                        enhanced_query=enhanced_query
                    )
                    
                    # Update state with enhanced query
                    state["current_query"] = enhanced_query
                    state["needs_clarification"] = False
                    state["missing_info"] = {}
                    state["context_retry_count"] = context_retry_count + 1
                    
                    # Bypass clarification detection for enhanced queries
                    # Set a flag to indicate we've already inferred and enhanced
                    state["context_inferred"] = True
                    
                    # Reset workflow state to trigger tool execution with enhanced query
                    state["needs_clarification"] = False
                    state["missing_info"] = {}
                    state["execution_plan"] = {}
                    state["tools_executed"] = 0
                    state["tool_results"] = []
                    
                    # Generate a direct answer for the enhanced query
                    # This will trigger tool execution through the normal flow
                    direct_answer = await self._execute_tool_for_enhanced_query(enhanced_query, state)
                    state["final_answer"] = direct_answer
                    return state
            else:
                logger.info_structured(
                    "Context inference retry limit reached, proceeding with clarification",
                    conversation_id=state.get("conversation_id"),
                    context_retry_count=context_retry_count
                )
        
        # Handle clarification requests (LLM-powered)
        if needs_clarification and missing_info:
            clarification_answer = await self._generate_llm_clarification_response(
                query, missing_info, conversation_context, conversation_summary, recent_messages
            )
            
            state["final_answer"] = clarification_answer
            
            logger.info_structured(
                "LLM-powered clarification answer generated",
                conversation_id=state.get("conversation_id"),
                clarification_type=missing_info.get("clarification_type", "unknown"),
                missing_information=missing_info.get("missing_information", [])
            )
            
            return state
        
        system_prompt = """You are an answer generation agent. Create a clear, accurate, and helpful response to the user's query.

Guidelines:
- Be concise and direct
- Use the reasoning and data provided
- Consider conversation history and context
- Maintain continuity with previous interactions
- Highlight key findings
- If confidence is low, acknowledge uncertainty
- Provide actionable information when applicable

IMPORTANT: If the user's query appears to be testing or validating a feature (contains words like "test", "fix", "validate", "check"), you MUST add ALL of these follow-up questions at the end:
1. "Did this work as expected?"
2. "Would you like to test other cases?"
3. "Should we try different scenarios?"

Do not skip any of these questions for test/fix validation queries.

Generate a natural language answer that directly addresses the user's query."""
        
        context = {
            "reasoning": reasoning_output,
            "data": aggregated_data,
            "confidence": confidence_score,
            "conversation_context": conversation_context,
            "conversation_summary": conversation_summary,
            "recent_messages_count": len(recent_messages)
        }
        
        context_text = json.dumps(context, indent=2)
        
        # Build the human message with conversation context
        human_message_parts = [f"User query: {query}"]
        
        if conversation_context:
            human_message_parts.append(f"\nConversation Context:\n{conversation_context}")
        
        if conversation_summary:
            human_message_parts.append(f"\nConversation Summary:\n{conversation_summary}")
        
        human_message_parts.append(f"\nContext and analysis:\n{context_text}")
        
        human_message_parts.append("\nGenerate a clear answer to the user's query, considering the conversation history and context.")
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content="\n".join(human_message_parts))
        ]
        
        try:
            response = await self.llm_service.llm.ainvoke(messages)
            answer = response.content
            
            if confidence_score < 0.7:
                answer += f"\n\n(Note: This answer has moderate confidence. Score: {confidence_score:.2f})"
            
            state["final_answer"] = answer
            
            if state.get("metadata"):
                state["metadata"]["completed_at"] = datetime.utcnow().isoformat()
                
                start_time = state["metadata"].get("started_at")
                if start_time:
                    start = datetime.fromisoformat(start_time)
                    end = datetime.utcnow()
                    duration_ms = (end - start).total_seconds() * 1000
                    state["metadata"]["total_duration_ms"] = duration_ms
            
            logger.info_structured(
                "Answer generated",
                conversation_id=state.get("conversation_id"),
                answer_length=len(answer),
                confidence=confidence_score
            )
            
        except Exception as e:
            logger.error_structured(
                "Answer generation failed",
                error=str(e),
                conversation_id=state.get("conversation_id")
            )
            
            state["final_answer"] = f"I apologize, but I encountered an error generating the answer: {str(e)}"
            state["errors"].append(f"Answer generation error: {str(e)}")
        
        # Add execution trace tracking (even in error case)
        state["execution_trace"]["agents_called"].append(self.name)
        state["execution_trace"]["timestamps"][self.name] = datetime.utcnow().isoformat()
        
        # Save AI response to conversation history
        if state.get("final_answer"):
            if not state.get("messages"):
                state["messages"] = []
            
            # Add AI message for the response
            state["messages"].append(AIMessage(content=state["final_answer"]))
            state["recent_messages"] = state["messages"][-5:]  # Keep last 5 messages
        
        return state
    
    async def _infer_missing_info_from_context(self, query: str, missing_info: dict, conversation_context: str, recent_messages: list) -> dict:
        """
        Infer missing information using LLM - FULLY GENERIC.
        No assumptions about field names, patterns, or data structure.
        """
        try:
            # Build context from recent messages - handle both dict and message objects
            recent_text = ""
            for msg in recent_messages[-5:]:
                if isinstance(msg, dict):
                    content = msg.get('content', '')
                    msg_type = msg.get('type', 'Unknown')
                    recent_text += f"{msg_type}: {content}\n"
                elif hasattr(msg, 'content'):
                    msg_type = msg.__class__.__name__
                    recent_text += f"{msg_type}: {msg.content}\n"
            
            # Use LLM for ALL inference - completely generic, no hardcoded patterns
            inference_prompt = f"""You are an intelligent context analyzer. Analyze the conversation and infer missing information.

Current Query: "{query}"

Missing Information Needed: {json.dumps(missing_info.get('missing_information', []))}

Recent Conversation History:
{recent_text}

Additional Context:
{conversation_context}

Task: Analyze the conversation and infer ANY missing information that would help complete the query.
Look for:
- Values, numbers, or entities mentioned in previous messages
- Actions, operations, or intents from context
- Any relevant information that connects to the current query

IMPORTANT: 
- Do NOT assume specific field names or structures
- Infer ANY relevant information in a flexible format
- Only infer if you are confident based on explicit mentions

Return a JSON object:
{{
    "inferred_values": {{
        // ANY relevant key-value pairs inferred from context
        // Structure should match what's needed for the query
    }},
    "confidence": 0.0-1.0,
    "reasoning": "Brief explanation of what you inferred and why"
}}

If you cannot confidently infer information, return {{"inferred_values": {{}}, "confidence": 0.0, "reasoning": "Insufficient information in context"}}"""

            messages = [
                SystemMessage(content="You are an intelligent context analyzer. Infer information flexibly without assuming specific structures. Always respond with valid JSON."),
                HumanMessage(content=inference_prompt)
            ]
            
            response = await self.llm_service.llm.ainvoke(messages)
            
            try:
                inferred_data = json.loads(response.content.strip())
                
                if inferred_data.get("confidence", 0) > 0.6:
                    return inferred_data
                else:
                    return {}
            except json.JSONDecodeError:
                logger.error_structured(
                    "Failed to parse inference response",
                    response_content=response.content[:200]
                )
                return {}
                
        except Exception as e:
            logger.error_structured(
                "Context inference failed",
                error=str(e)
            )
            return {}
    
    async def _enhance_query_with_context(self, query: str, inferred_info: dict, recent_messages: list) -> str:
        """
        Enhance query using LLM with inferred information - FULLY GENERIC.
        No assumptions about field names or data structure.
        """
        try:
            inferred_values = inferred_info.get("inferred_values", {})
            
            # If no inferred values, return original query
            if not inferred_values:
                return query
            
            # Build context from recent messages
            recent_context = ""
            if recent_messages:
                recent_context = "\n".join([
                    f"{msg.get('type', 'Message')}: {msg.get('content', '')}"
                    for msg in recent_messages[-3:]
                ])
            
            # Let LLM enhance query with ANY inferred information - completely generic
            enhancement_prompt = f"""Enhance this query using the inferred information from context.

Original Query: "{query}"

Inferred Information:
{json.dumps(inferred_values, indent=2)}

Recent Context:
{recent_context}

Task: Create a complete, natural query that incorporates the inferred information.
If the original query is already complete, return it unchanged.
Return ONLY the enhanced query text, nothing else."""

            try:
                messages = [
                    SystemMessage(content="You are a query enhancement assistant. Analyze the inferred information and create a natural, complete query."),
                    HumanMessage(content=enhancement_prompt)
                ]
                response = await self.llm_service.llm.ainvoke(messages)
                enhanced = response.content.strip()
                return enhanced if enhanced else query
            except Exception as e:
                logger.error_structured(
                    "LLM query enhancement failed",
                    error=str(e)
                )
                return query
            
        except Exception as e:
            logger.error_structured(
                "Query enhancement failed",
                error=str(e)
            )
            return query
    
    # Method deleted - using LLMService.infer_context() instead
    
    async def _execute_tool_for_enhanced_query(self, enhanced_query: str, state: dict) -> str:
        """
        Execute tool using ToolDiscoveryService.
        """
        try:
            # Get tool selection from LLM inference in state
            inferred_info = state.get("inferred_info", {})
            inferred_values = inferred_info.get("inferred_values", {})
            
            tool_name = inferred_values.get("tool")
            tool_params = inferred_values.get("parameters", {})
            
            if not tool_name or not tool_params:
                # No tool selected by LLM - return query as-is for general answer
                return enhanced_query
                
            logger.info_structured(
                "Executing tool via service",
                tool_name=tool_name,
                tool_params=tool_params
            )
            
            # Track tool call in execution trace
            if "execution_trace" not in state:
                state["execution_trace"] = {}
            if "tools_called" not in state["execution_trace"]:
                state["execution_trace"]["tools_called"] = []
            
            tool_start_time = time.time()
            
            # Execute tool using service
            result = await self.tool_discovery.execute_tool(tool_name, tool_params)
            
            tool_end_time = time.time()
            tool_latency_ms = round((tool_end_time - tool_start_time) * 1000, 2)
            
            # Add tool call to execution trace
            tool_info = {
                "name": tool_name,
                "agent": self.name,
                "success": result is not None,
                "params": tool_params,
                "server": "discovered",
                "latency_ms": tool_latency_ms,
                "timestamp": datetime.utcnow().isoformat()
            }
            state["execution_trace"]["tools_called"].append(tool_info)
            
            logger.info_structured(
                "Tool execution completed via service",
                tool_name=tool_name,
                result_type=type(result).__name__
            )
            
            # Return result for LLM to format naturally
            return str(result)
            
        except Exception as e:
            logger.error_structured(
                "Failed to execute tool for enhanced query",
                error=str(e),
                enhanced_query=enhanced_query
            )
            return f"Error executing tool: {str(e)}"
    
    async def _generate_direct_answer(self, enhanced_query: str, state: dict) -> str:
        """
        Generate a direct answer for an enhanced query by executing appropriate tools.
        """
        try:
            # Execute the appropriate tool for the enhanced query
            # This ensures all calculations go through tools, not direct LLM responses
            return await self._execute_tool_for_enhanced_query(enhanced_query, state)
            
        except Exception as e:
            logger.error_structured(
                "Failed to generate direct answer",
                error=str(e),
                enhanced_query=enhanced_query
            )
            return f"Error generating answer: {str(e)}"
    
    async def _generate_llm_clarification_response(self, query: str, missing_info: dict, conversation_context: str = "", conversation_summary: str = "", recent_messages: list = None) -> str:
        """
        Generate contextual clarification response using LLM based on missing information analysis and conversation history.
        """
        
        # Get relevant tools using vector-based discovery for better examples
        relevant_tools = await self._find_relevant_tools(query)
        tools_context = self._format_tools_context(relevant_tools)
        
        # Build context-aware clarification prompt
        prompt_parts = [f"You are a helpful assistant. The user asked: \"{query}\""]
        
        # Add conversation context if available
        if conversation_context:
            prompt_parts.append(f"\nConversation Context:\n{conversation_context}")
        
        if conversation_summary:
            prompt_parts.append(f"\nConversation Summary:\n{conversation_summary}")
        
        if recent_messages:
            recent_text = "\n".join([
                f"{msg.__class__.__name__}: {msg.content}"
                for msg in recent_messages[-3:]  # Last 3 messages
            ])
            prompt_parts.append(f"\nRecent Messages:\n{recent_text}")
        
        prompt_parts.append(f"""
Analysis shows this query needs clarification:
- Clarification Type: {missing_info.get('clarification_type', 'unknown')}
- Missing Information: {', '.join(missing_info.get('missing_information', []))}
- Reasoning: {missing_info.get('reasoning', 'No reasoning provided')}
- Suggested Examples: {missing_info.get('suggested_examples', [])}

Relevant Capabilities Discovered:
{tools_context}

Generate a friendly, helpful clarification response that:
1. Acknowledges the user's query
2. Explains what additional information is needed
3. Provides examples using natural language descriptions of capabilities
4. AVOIDS technical terms like tool names, parameters, or implementation details
5. Uses conversational language focused on user goals
6. Maintains continuity with the conversation context
7. References previous interactions if relevant

IMPORTANT RULES:
- NEVER mention tool names or technical implementation details
- NEVER mention technical parameters
- Describe capabilities in simple, natural terms
- Focus on WHAT can be done, not HOW it's done
- Use examples that are natural and user-friendly
- Transform technical tool names into user-friendly descriptions

6. Is conversational and helpful
7. NEVER uses generic examples - use the specific, highly relevant tools discovered

Keep the response concise but comprehensive. Do not use markdown formatting.""")

        try:
            clarification_prompt = "\n".join(prompt_parts)
            messages = [
                SystemMessage(content="You are a helpful assistant that provides clear clarification requests to users."),
                HumanMessage(content=clarification_prompt)
            ]
            
            response = await self.llm_service.llm.ainvoke(messages)
            clarification_response = response.content.strip()
            
            # No hardcoded follow-up logic - LLM handles all response generation
            
            return clarification_response
            
        except Exception as e:
            logger.error_structured(
                "LLM clarification response generation failed",
                error=str(e),
                query=query[:50]
            )
            
            # Fallback to basic clarification
            return self._fallback_clarification_response(query, missing_info)
    
    def _fallback_clarification_response(self, query: str, missing_info: dict) -> str:
        """
        Fallback clarification response when LLM fails.
        """
        missing_items = missing_info.get('missing_information', [])
        clarification_type = missing_info.get('clarification_type', 'unknown')
        
        response = f"I need more information to help you with your query: '{query}'\n\n"
        
        # Generic handling - no hardcoded clarification types
        response += "Could you please provide more specific details?\n\n"
        
        if missing_items:
            response += "I need the following information:\n"
            for item in missing_items:
                response += f"• {item}\n"
        
        if missing_info.get('suggested_examples'):
            response += "\nFor example:\n"
            for example in missing_info['suggested_examples'][:3]:
                response += f"• {example}\n"
        
        response += "\nPlease provide these details and I'll be happy to help you!"
        
        return response
    
    def _get_available_tools_context(self) -> str:
        """
        Get available tools and capabilities for context-aware examples.
        This provides the LLM with information about what the system can actually do.
        """
        try:
            # Import here to avoid circular imports
            from app.registry.tool_registry import ToolRegistry
            
            tool_registry = ToolRegistry()
            tools = tool_registry.get_tool_metadata_dict()
            
            context = "Available Tools:\n"
            for tool_name, tool_info in tools.items():
                context += f"- {tool_name}: {tool_info.get('description', 'No description')}\n"
                
                # Add parameter information
                if 'parameters' in tool_info:
                    params = tool_info['parameters']
                    if isinstance(params, dict) and 'properties' in params:
                        context += "  Parameters: "
                        param_names = list(params['properties'].keys())
                        context += ", ".join(param_names) + "\n"
                context += "\n"
            
            # System capabilities derived from actual tools
            context += "\nSystem Capabilities: Based on available tools above\n"
            
            return context
            
        except Exception as e:
            logger.error_structured(
                "Failed to get available tools context",
                error=str(e)
            )
            
            # Fallback context - generic, no hardcoded tool names
            return """System Capabilities:
The system can help with various tasks based on available tools.
Please refer to tool discovery for specific capabilities."""
    
    async def _find_relevant_tools(self, query: str, top_k: int = 5) -> list:
        """
        Find relevant tools using ToolDiscoveryService.
        """
        try:
            # Use service layer for tool discovery
            all_tools = await self.tool_discovery.discover_all_tools()
            
            # Format tools with similarity_score field for compatibility
            relevant_tools = []
            for tool in all_tools[:top_k]:
                relevant_tools.append({
                    'name': tool.get('name', 'Unknown'),
                    'description': tool.get('description', 'No description'),
                    'parameters': tool.get('input_schema', {}),
                    'similarity_score': 0.8,  # Default score since we don't have vector search yet
                    'usage_examples': [],
                    'categories': []
                })
            
            logger.info_structured(
                "Tool discovery completed",
                query=query[:50],
                tools_found=len(relevant_tools),
                top_similarity=relevant_tools[0]['similarity_score'] if relevant_tools else 0.0
            )
            
            return relevant_tools
            
        except Exception as e:
            logger.error_structured(
                "Vector-based tool discovery failed",
                error=str(e),
                query=query[:50]
            )
            
            # Fallback to static tool analysis
            return await self._fallback_tool_discovery(query)
    
    async def _fallback_tool_discovery(self, query: str) -> list:
        """
        Fallback tool discovery when vector search fails.
        Uses keyword matching and heuristics.
        """
        try:
            from app.registry.tool_registry import ToolRegistry
            
            tool_registry = ToolRegistry()
            tools = tool_registry.get_tool_metadata_dict()
            
            query_lower = query.lower()
            relevant_tools = []
            
            # Keyword-based relevance scoring
            for tool_name, tool_info in tools.items():
                score = 0.0
                
                # Check tool name relevance
                if any(keyword in tool_name.lower() for keyword in query_lower.split()):
                    score += 0.5
                
                # Check description relevance
                description = tool_info.get('description', '').lower()
                if any(keyword in description for keyword in query_lower.split()):
                    score += 0.3
                
                # Check parameter relevance
                params = tool_info.get('parameters', {})
                if isinstance(params, dict) and 'properties' in params:
                    for param_name in params['properties'].keys():
                        if param_name.lower() in query_lower:
                            score += 0.2
                
                if score > 0:
                    relevant_tools.append({
                        'name': tool_name,
                        'description': tool_info.get('description', 'No description'),
                        'parameters': params,
                        'similarity_score': score,
                        'usage_examples': [],
                        'categories': []
                    })
            
            # Sort by relevance score
            relevant_tools.sort(key=lambda x: x['similarity_score'], reverse=True)
            
            logger.info_structured(
                "Fallback tool discovery completed",
                query=query[:50],
                tools_found=len(relevant_tools),
                method="keyword_matching"
            )
            
            return relevant_tools[:5]  # Return top 5
            
        except Exception as e:
            logger.error_structured(
                "Fallback tool discovery failed",
                error=str(e),
                query=query[:50]
            )
            
            # Ultimate fallback - return empty list
            return []
    
    def _format_tools_context(self, relevant_tools: list) -> str:
        """
        Format relevant tools for LLM context with user-friendly descriptions.
        """
        if not relevant_tools:
            return "No specific capabilities found for this query. Available general capabilities include data analysis, monitoring, and comparison operations."
        
        context = f"Most Relevant Capabilities for Your Query:\n\n"
        
        for i, tool in enumerate(relevant_tools, 1):
            # Convert tool name to user-friendly description
            friendly_name = self._get_tool_friendly_name(tool['name'])
            context += f"{i}. {friendly_name} (Relevance: {tool['similarity_score']:.2f})\n"
            context += f"   What I can do: {self._get_user_friendly_description(tool['description'])}\n"
            
            # Add user-friendly examples instead of technical ones
            if tool.get('usage_examples'):
                friendly_examples = self._get_user_friendly_examples(tool['name'], tool['usage_examples'][:2])
                context += f"   Examples: {friendly_examples}\n"
            
            context += "\n"
        
        # Add general capabilities summary
        context += "General System Capabilities:\n"
        context += "- Intelligent understanding of your needs\n"
        context += "- Semantic matching to find the best approach\n"
        context += "- Context-aware example generation\n"
        context += "- Dynamic tool recommendation\n"
        
        return context
    
    def _get_tool_friendly_name(self, tool_name: str) -> str:
        """
        Convert tool name to user-friendly description.
        """
        # Common tool name mappings
        name_mappings = {
            'compare_values': 'Number Comparison',
            'percentage_difference': 'Percentage Difference Calculator',
            'service_metrics': 'Performance Metrics',
            'latency_history': 'Response Time Analysis',
            'error_rate_lookup': 'Error Rate Analysis',
            'service_status': 'System Health Check',
            'alert_management': 'Alert Management',
            'security_scan': 'Security Analysis',
            'vulnerability_check': 'Vulnerability Assessment',
            'database_query': 'Database Search',
            'cache_performance': 'Cache Analysis',
            'data_validation': 'Data Verification',
            'json_yaml_parser': 'File Parser',
            'performance_profiling': 'Performance Analysis',
            'detect_language': 'Language Detection',
            'translate_text': 'Text Translation',
            'correct_typos': 'Text Correction',
            'normalize_text': 'Text Normalization'
        }
        
        # Convert snake_case to Title Case and apply mappings
        friendly_name = name_mappings.get(tool_name, tool_name.replace('_', ' ').title())
        return friendly_name
    
    def _get_user_friendly_description(self, description: str) -> str:
        """
        Convert technical description to user-friendly language.
        """
        # Remove technical jargon and simplify
        friendly_desc = description
        
        # Common technical term replacements
        replacements = {
            'retrieve': 'get',
            'query': 'search',
            'parameters': 'details',
            'execute': 'run',
            'validate': 'check',
            'parse': 'read',
            'transform': 'convert',
            'aggregate': 'summarize',
            'monitor': 'track',
            'analyze': 'examine'
        }
        
        for tech_term, simple_term in replacements.items():
            friendly_desc = friendly_desc.replace(tech_term, simple_term)
        
        return friendly_desc
    
    def _get_user_friendly_examples(self, tool_name: str, examples: list) -> str:
        """
        Convert technical examples to user-friendly ones.
        """
        friendly_examples = []
        
        for example in examples:
            # Remove tool names and technical terms
            friendly_example = example
            
            # Remove tool name references
            friendly_example = friendly_example.replace(tool_name, '')
            
            # Common pattern replacements
            replacements = {
                'using the': '',
                'with the': '',
                'tool': '',
                'parameter': 'detail',
                'value': 'number',
                'input': 'information'
            }
            
            for tech_term, simple_term in replacements.items():
                friendly_example = friendly_example.replace(tech_term, simple_term)
            
            # Clean up extra spaces
            friendly_example = ' '.join(friendly_example.split())
            
            if friendly_example and len(friendly_example) > 5:
                friendly_examples.append(friendly_example)
        
        return '; '.join(friendly_examples[:2])
    
    async def _generate_capability_denial_response(self, query: str, relevant_tools: list) -> dict:
        """
        Generate a polite denial response when the query is outside system capabilities.
        """
        try:
            # Get system capabilities summary
            system_capabilities = self._get_system_capabilities_summary()
            
            # Identify the domain of the user's query
            query_domain = self._identify_query_domain(query)
            
            denial_prompt = f"""You are a helpful AI assistant. The user asked: "{query}"

Analysis shows this query is outside the system's capabilities:
- Query Domain: {query_domain}
- Max Tool Similarity: {relevant_tools[0]['similarity_score'] if relevant_tools else 0.0:.2f}
- Available Tools: {len(relevant_tools)} found (all low similarity)

System Capabilities:
{system_capabilities}

Generate a polite, helpful denial response that:
1. Acknowledges the user's request
2. Clearly and politely states that this capability is not available
3. Explains what the system CAN do instead
4. Suggests alternative requests that are within capabilities
5. Maintains a helpful and positive tone
6. Is honest but not discouraging

Keep the response concise and conversational. Do not use markdown formatting."""

            messages = [
                SystemMessage(content="You are a helpful assistant that politely explains system limitations while maintaining a positive user experience."),
                HumanMessage(content=denial_prompt)
            ]
            
            response = await self.llm.ainvoke(messages)
            
            logger.info_structured(
                "Capability denial response generated",
                query=query[:50],
                query_domain=query_domain,
                max_similarity=relevant_tools[0]['similarity_score'] if relevant_tools else 0.0
            )
            
            return {
                "needs_clarification": False,
                "clarification_type": "out_of_scope",
                "missing_information": [],
                "reasoning": f"Query '{query}' is outside system capabilities (max similarity: {relevant_tools[0]['similarity_score'] if relevant_tools else 0.0:.2f})",
                "suggested_examples": [],
                "confidence": 0.9,
                "is_out_of_scope": True,
                "denial_response": response.content.strip()
            }
            
        except Exception as e:
            logger.error_structured(
                "Failed to generate capability denial response",
                query=query[:50],
                error=str(e)
            )
            
            # Fallback denial response
            return {
                "needs_clarification": False,
                "clarification_type": "out_of_scope",
                "missing_information": [],
                "reasoning": "Query is outside system capabilities",
                "suggested_examples": [],
                "confidence": 0.9,
                "is_out_of_scope": True,
                "denial_response": f"I apologize, but I don't have the capability to help with '{query}'. My expertise is focused on system monitoring, data analysis, and performance metrics. Is there something else I can help you with?"
            }
    
    def _get_system_capabilities_summary(self) -> str:
        """
        Get a summary of system capabilities for denial responses.
        """
        return """• System monitoring and health checks
• Performance metrics analysis
• Error rate monitoring and analysis
• Data retrieval and processing
• Statistical calculations and comparisons
• Log analysis and pattern matching
• Service status monitoring
• Resource utilization tracking"""
    
    def _identify_query_domain(self, query: str) -> str:
        """
        Identify the domain of the user's query for better denial responses.
        """
        query_lower = query.lower()
        
        # Common out-of-scope domains
        domains = {
            'translation': ['translate', 'translation', 'french', 'spanish', 'german', 'chinese', 'japanese', 'language'],
            'creative_writing': ['write', 'story', 'poem', 'creative', 'fiction', 'novel'],
            'web_browsing': ['browse', 'search', 'internet', 'web', 'website', 'google'],
            'file_operations': ['file', 'save', 'open', 'delete', 'create file', 'write file'],
            'email': ['email', 'send', 'mail', 'message'],
            'calendar': ['calendar', 'schedule', 'appointment', 'meeting'],
            'weather': ['weather', 'forecast', 'temperature', 'rain', 'snow'],
            'news': ['news', 'headlines', 'current events'],
            'social_media': ['twitter', 'facebook', 'instagram', 'social'],
            'gaming': ['game', 'play', 'gaming'],
            'cooking': ['recipe', 'cook', 'food', 'ingredients'],
            'travel': ['travel', 'flight', 'hotel', 'booking'],
            'shopping': ['buy', 'purchase', 'shop', 'price', 'cost'],
            'entertainment': ['movie', 'music', 'show', 'entertainment']
        }
        
        for domain, keywords in domains.items():
            if any(keyword in query_lower for keyword in keywords):
                return domain
        
        return 'general'
    
    async def _llm_detect_clarification_need(self, query: str, state: dict) -> dict:
        """
        Use LLM to intelligently determine if clarification is needed based on query and execution results.
        This replaces hardcoded keyword lists with dynamic LLM analysis.
        """
        
        # Gather context for LLM analysis
        intent = state.get("detected_intent", "unknown")
        entities = state.get("extracted_entities", {})
        reasoning_output = state.get("reasoning_output", {})
        aggregated_data = state.get("aggregated_data", {})
        
        # Get relevant tools using vector-based discovery
        relevant_tools = await self._find_relevant_tools(query)
        tools_context = self._format_tools_context(relevant_tools)
        
        # Check if query is outside system capabilities
        max_similarity = relevant_tools[0]['similarity_score'] if relevant_tools else 0.0
        is_out_of_scope = max_similarity < 0.3  # Threshold for capability match
        
        if is_out_of_scope:
            # Generate polite denial response
            return await self._generate_capability_denial_response(query, relevant_tools)
        
        detection_prompt = f"""You are an intelligent query analysis expert. Analyze the user's query and execution context to determine if clarification is needed.

User Query: "{query}"
Intent: {intent}
Entities: {json.dumps(entities, indent=2)}
Execution Results: No tools executed, empty plan
Reasoning Output: {str(reasoning_output)[:200] if reasoning_output else "None"}
Aggregated Data: {str(aggregated_data)[:200] if aggregated_data else "None"}

Relevant Tools Discovered (Vector-Based Similarity Search):
{tools_context}

Max Tool Similarity: {max_similarity:.2f}

Analyze and respond with JSON:

{{
    "needs_clarification": true/false,
    "clarification_type": "vague_query|missing_parameters|insufficient_context|complete|out_of_scope",
    "missing_information": ["param1", "param2"],
    "reasoning": "Brief explanation of what clarification is needed or not",
    "suggested_examples": [
        "Example using the most relevant discovered tools",
        "Another example using highly relevant tools"
    ],
    "confidence": 0.8,
    "is_out_of_scope": false
}}

Guidelines:
- If max similarity < 0.3, the query is likely outside system capabilities
- If query resulted in no tool execution and plan is empty, it likely needs clarification
- Look for vague, incomplete, or ambiguous queries
- Consider if the query has sufficient specificity for meaningful execution
- Use the RELEVANT DISCOVERED TOOLS to generate highly specific, actionable examples
- Prioritize tools with highest similarity scores in your examples
- Be conservative - if in doubt, ask for clarification
- Handle any language or query type dynamically
- NEVER use generic examples - use the specific tools discovered by vector search"""

        try:
            messages = [
                SystemMessage(content="You are a query analysis expert. Always respond with valid JSON only."),
                HumanMessage(content=detection_prompt)
            ]
            
            response = await self.llm.ainvoke(messages)
            
            # Parse the LLM response
            try:
                analysis_result = json.loads(response.content.strip())
                
                # Validate required fields
                required_fields = ["needs_clarification", "clarification_type", "reasoning", "confidence"]
                for field in required_fields:
                    if field not in analysis_result:
                        analysis_result[field] = "unknown" if field != "needs_clarification" else False
                
                # Ensure list fields exist
                if "missing_information" not in analysis_result:
                    analysis_result["missing_information"] = []
                if "suggested_examples" not in analysis_result:
                    analysis_result["suggested_examples"] = []
                
                logger.info_structured(
                    "LLM clarification detection completed",
                    query=query[:50],
                    needs_clarification=analysis_result.get("needs_clarification"),
                    clarification_type=analysis_result.get("clarification_type"),
                    confidence=analysis_result.get("confidence")
                )
                
                return analysis_result
                
            except json.JSONDecodeError as e:
                logger.error_structured(
                    "Failed to parse LLM clarification detection response",
                    error=str(e),
                    response_content=response.content[:200]
                )
                
                # Fallback to conservative clarification
                return self._fallback_clarification_detection(query)
                
        except Exception as e:
            logger.error_structured(
                "LLM clarification detection failed",
                error=str(e),
                query=query[:50]
            )
            
            # Fallback to conservative clarification
            return self._fallback_clarification_detection(query)
    
    def _fallback_clarification_detection(self, query: str) -> dict:
        """
        Fallback clarification detection when LLM fails.
        Uses conservative approach - if unsure, ask for clarification.
        """
        
        # Conservative approach: if no tools executed, assume clarification needed
        return {
            "needs_clarification": True,
            "clarification_type": "vague_query",
            "missing_information": ["specific_details"],
            "reasoning": f"Query '{query}' resulted in no execution, indicating clarification is needed.",
            "suggested_examples": [
                f"Please provide more specific details for: {query}",
                f"Specify what you want to {query.lower()}",
                f"Add context to your query about {query.lower()}"
            ],
            "confidence": 0.6
        }
