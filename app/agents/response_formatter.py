"""
Response Formatting Agent
Responsible for formatting tool results and responses into user-friendly output.
Production-grade implementation with multiple formatting strategies.
"""

import logging
from typing import Dict, Any, List
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from app.schemas.state import ConversationState
from app.core.config import settings
from app.core.logging import logger
from app.services import LLMService
from datetime import datetime
import json


class ResponseFormatterAgent:
    def __init__(self):
        self.name = "response_formatter"
        self.llm_service = LLMService()
    
    async def format_response(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format the response based on tool results and context.
        
        Args:
            state: Current workflow state
            
        Returns:
            State with formatted response
        """
        try:
            tool_results = state.get("tool_results", [])
            query = state.get("current_query", "")
            context_enhanced = state.get("context_enhanced", False)
            
            if not tool_results:
                # No tool results - generate conversational response
                formatted_response = await self._generate_conversational_response(state)
            else:
                # Format tool results
                formatted_response = await self._format_tool_results(tool_results, query, state)
            
            # Add contextual information if enhancement was used
            if context_enhanced:
                formatted_response = self._add_context_note(formatted_response, state)
            
            # Update state with formatted response
            formatted_state = state.copy()
            formatted_state.update({
                "formatted_response": formatted_response,
                "response_metadata": {
                    "formatted_at": datetime.utcnow().isoformat(),
                    "tool_results_count": len(tool_results),
                    "context_enhanced": context_enhanced,
                    "response_type": self._determine_response_type(tool_results)
                }
            })
            
            logger.info_structured(
                "Response formatted successfully",
                conversation_id=state.get("conversation_id"),
                response_type=formatted_state["response_metadata"]["response_type"],
                context_enhanced=context_enhanced
            )
            
            return formatted_state
            
        except Exception as e:
            logger.error_structured(
                "Response formatting failed",
                error=str(e),
                conversation_id=state.get("conversation_id")
            )
            # Fallback response
            state["formatted_response"] = "I apologize, but I encountered an issue formatting the response."
            return state
    
    async def _format_tool_results(self, tool_results: List[Dict], query: str, state: Dict[str, Any]) -> str:
        """
        Format tool results into user-friendly response.
        
        Args:
            tool_results: List of tool execution results
            query: Original query
            state: Current workflow state
            
        Returns:
            Formatted response string
        """
        try:
            if not tool_results:
                return "I don't have any results to display."
            
            # Determine response type based on tool results
            response_type = self._determine_response_type(tool_results)
            
            # Get appropriate formatting strategy
            formatter = self.formatting_strategies.get(response_type, self.formatting_strategies["default"])
            
            # Format the results
            formatted_response = await formatter(tool_results, query, state)
            
            return formatted_response
            
        except Exception as e:
            logger.error_structured(
                "Tool result formatting failed",
                error=str(e)
            )
            return f"I executed some tools, but encountered an error formatting the results: {str(e)}"
    
    async def _determine_response_type(self, tool_results: List[Dict], query: str) -> str:
        """
        Use LLMService to determine response type.
        """
        try:
            return await self.llm_service.determine_response_type(query, tool_results)
        except Exception as e:
            logger.error_structured(
                "LLM response type determination failed",
                error=str(e)
            )
            return "default"
    
    # All specific formatting methods removed - use single LLM formatting
    
    async def _format_error_result(self, tool_results: List[Dict], query: str, state: Dict[str, Any]) -> str:
        """Format error results."""
        try:
            response = f"**Error Encountered:**\n\n"
            
            for result in tool_results:
                error = result.get("error")
                tool_name = result.get("tool_name", "Unknown tool")
                
                if error:
                    response += f"❌ **{tool_name}**: {error}\n"
            
            response += f"\nI apologize for the inconvenience. Please try rephrasing your query or check if the required parameters are correct."
            
            return response
            
        except Exception as e:
            logger.error_structured(
                "Error result formatting failed",
                error=str(e)
            )
            return "I encountered an error while formatting the error results."
    
    async def _format_with_llm(self, tool_results: List[Dict], query: str, state: Dict[str, Any]) -> str:
        """
        Use LLMService for all response formatting.
        """
        try:
            return await self.llm_service.format_response(query, tool_results)
        except Exception as e:
            logger.error_structured(
                "LLM response formatting failed",
                error=str(e)
            )
            # Simple fallback
            return f"I completed the operation but encountered an issue formatting the results: {str(e)}"
    
    async def _generate_conversational_response(self, state: Dict[str, Any]) -> str:
        """
        Generate conversational response when no tools were executed.
        
        Args:
            state: Current workflow state
            
        Returns:
            Conversational response string
        """
        try:
            query = state.get("current_query", "")
            context_enhanced = state.get("context_enhanced", False)
            
            if context_enhanced:
                # Query was enhanced but still no tools - provide contextual response
                return f"I understand you're asking about: {query}\n\nHowever, I don't have the appropriate tools available to handle this specific request. Could you provide more details or try a different approach?"
            else:
                # No enhancement and no tools - general conversational response
                return f"I understand you're asking about: {query}\n\nI don't have the right tools available to process this request. Could you provide more specific details or rephrase your question?"
                
        except Exception as e:
            logger.error_structured(
                "Conversational response generation failed",
                error=str(e)
            )
            return "I'm not sure how to help with that request. Could you provide more details?"
    
    def _add_context_note(self, response: str, state: Dict[str, Any]) -> str:
        """
        Add context enhancement note to response.
        
        Args:
            response: Original response
            state: Current workflow state
            
        Returns:
            Response with context note
        """
        try:
            original_query = state.get("original_query")
            enhanced_query = state.get("current_query")
            
            if original_query and enhanced_query and original_query != enhanced_query:
                note = f"\n\n*Note: I enhanced your request from \"{original_query}\" to \"{enhanced_query}\" based on our conversation context.*"
                return response + note
            
            return response
            
        except Exception as e:
            logger.error_structured(
                "Failed to add context note",
                error=str(e)
            )
            return response
