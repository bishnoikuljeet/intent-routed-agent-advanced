"""
Context Enhancement Agent
Responsible for inferring missing information from conversation context and enhancing queries.
Production-grade implementation with proper error handling and logging.
"""

import logging
import re
from typing import Dict, List, Any, Optional
from langchain_core.messages import HumanMessage, SystemMessage

logger = logging.getLogger(__name__)


class ContextEnhancerAgent:
    """
    Context Enhancement Agent that infers missing information from conversation context
    and enhances queries to make them executable.
    """
    
    def __init__(self, llm, memory_manager=None, tool_registry=None):
        self.llm = llm
        self.memory_manager = memory_manager
        self.tool_registry = tool_registry
        self.max_context_retries = 1
        self.confidence_threshold = 0.7
    
    async def enhance_query(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enhance query using conversation context if needed.
        
        Args:
            state: Current workflow state
            
        Returns:
            Enhanced state with potentially modified query
        """
        try:
            query = state.get("current_query", "")
            conversation_context = state.get("conversation_context", "")
            recent_messages = state.get("recent_messages", [])
            
            # Check if query needs enhancement
            enhancement_needed = await self._analyze_query_completeness(query)
            
            if not enhancement_needed.get("needs_enhancement", False):
                logger.info_structured(
                    "Query enhancement not needed",
                    conversation_id=state.get("conversation_id"),
                    query=query[:50]
                )
                return state
            
            # Check if we've already tried enhancement
            context_retry_count = state.get("context_enhancement_retry_count", 0)
            
            if context_retry_count >= self.max_context_retries:
                logger.info_structured(
                    "Context enhancement retry limit reached",
                    conversation_id=state.get("conversation_id"),
                    retry_count=context_retry_count
                )
                return state
            
            # Attempt context enhancement
            enhanced_query = await self._enhance_with_context(
                query, conversation_context, recent_messages
            )
            
            if enhanced_query and enhanced_query != query:
                logger.info_structured(
                    "Query successfully enhanced",
                    conversation_id=state.get("conversation_id"),
                    original_query=query[:50],
                    enhanced_query=enhanced_query[:50]
                )
                
                # Update state with enhanced query
                enhanced_state = state.copy()
                enhanced_state.update({
                    "current_query": enhanced_query,
                    "original_query": query,
                    "context_enhanced": True,
                    "context_enhancement_retry_count": context_retry_count + 1,
                    "query_enhancement_metadata": {
                        "enhancement_applied": True,
                        "confidence": enhancement_needed.get("confidence", 0.0),
                        "missing_elements": enhancement_needed.get("missing_elements", [])
                    }
                })
                
                return enhanced_state
            else:
                logger.info_structured(
                    "Context enhancement failed",
                    conversation_id=state.get("conversation_id"),
                    query=query[:50]
                )
                return state
                
        except Exception as e:
            logger.error_structured(
                "Context enhancement failed",
                error=str(e),
                conversation_id=state.get("conversation_id")
            )
            return state
    
    async def _analyze_query_completeness(self, query: str) -> Dict[str, Any]:
        """
        Analyze if query needs enhancement based on completeness.
        
        Args:
            query: Current query
            
        Returns:
            Analysis result with enhancement needs
        """
        try:
            prompt = f"""Analyze the following query for completeness:

Query: "{query}"

Determine if the query needs enhancement by checking:
1. Missing specific values/parameters
2. Vague operations or actions
3. Incomplete context for execution

Return JSON format:
{{
    "needs_enhancement": true/false,
    "confidence": 0.0-1.0,
    "missing_elements": ["list of missing elements"],
    "query_type": "comparison/calculation/search/general",
    "reasoning": "Brief explanation"
}}

Analyze the query semantically without relying on specific keywords or patterns.
Focus on whether the query has sufficient information to be actionable."""

            messages = [
                SystemMessage(content="You are a query analysis expert. Always respond with valid JSON."),
                HumanMessage(content=prompt)
            ]
            
            response = await self.llm.ainvoke(messages)
            
            try:
                import json
                analysis = json.loads(response.content.strip())
                return analysis
            except json.JSONDecodeError:
                logger.warning_structured(
                    "Failed to parse query completeness analysis",
                    response=response.content[:100]
                )
                return {"needs_enhancement": False, "confidence": 0.0}
                
        except Exception as e:
            logger.error_structured(
                "Query completeness analysis failed",
                error=str(e)
            )
            return {"needs_enhancement": False, "confidence": 0.0}
    
    async def _enhance_with_context(self, query: str, context: str, recent_messages: List) -> Optional[str]:
        """
        Enhance query using conversation context.
        
        Args:
            query: Original query
            context: Conversation context
            recent_messages: Recent message history
            
        Returns:
            Enhanced query or None if enhancement failed
        """
        try:
            # Build context from recent messages
            recent_text = "\n".join([
                f"{'User' if msg.get('type') == 'human' else 'Assistant'}: {msg.get('content', '')}"
                for msg in recent_messages[-5:]  # Last 5 messages
            ])
            
            prompt = f"""Enhance the query using conversation context.

Original Query: "{query}"

Recent Conversation:
{recent_text}

Context Information:
{context}

Your task: Enhance the query with missing information from context. Look for:
1. Numbers, values, or entities mentioned in previous messages
2. Operations or actions the user was trying to perform
3. Patterns that suggest what the user wants

Rules:
- Only enhance if you're confident about the missing information
- Preserve the original intent
- Make the enhanced query specific and executable
- If no enhancement possible, return the original query
- Use semantic understanding to combine query with context naturally

Return only the enhanced query (no explanation):"""

            messages = [
                SystemMessage(content="You are a context enhancement expert. Always return only the enhanced query."),
                HumanMessage(content=prompt)
            ]
            
            response = await self.llm.ainvoke(messages)
            enhanced_query = response.content.strip()
            
            # Validate enhancement
            if enhanced_query and enhanced_query != query:
                # Basic validation - enhanced query should be more specific
                if len(enhanced_query) > len(query) or any(char.isdigit() for char in enhanced_query):
                    return enhanced_query
            
            return None
            
        except Exception as e:
            logger.error_structured(
                "Context enhancement failed",
                error=str(e),
                original_query=query
            )
            return None
    
    async def get_enhancement_metadata(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get metadata about query enhancement for logging and debugging.
        
        Args:
            state: Current workflow state
            
        Returns:
            Enhancement metadata
        """
        return {
            "context_enhanced": state.get("context_enhanced", False),
            "original_query": state.get("original_query"),
            "enhanced_query": state.get("current_query"),
            "enhancement_retry_count": state.get("context_enhancement_retry_count", 0),
            "enhancement_metadata": state.get("query_enhancement_metadata", {})
        }
