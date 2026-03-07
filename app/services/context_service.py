"""
Context Enhancement Service - Centralized context management for all agents
"""

import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from langchain_core.messages import SystemMessage, HumanMessage
from app.services.llm_service import LLMService
from app.core.logging import logger


class ContextService:
    """
    Centralized context enhancement service for all agents.
    Handles conversation context, summarization, and query enhancement.
    """
    
    def __init__(self):
        self.llm_service = LLMService()
        self.logger = logger
        # Validation threshold for context enhancement
        self.validation_similarity_threshold = 0.5
        
    async def enhance_query_with_context(self, query: str, messages: List[Dict[str, Any]]) -> str:
        """
        Enhance query with conversation context using LLM.
        Uses last 10 messages, summarizes older messages if needed.
        
        Args:
            query: Current user query
            messages: Conversation history (list of message dicts)
            
        Returns:
            Enhanced query with context or original query if no enhancement needed
        """
        try:
            if not messages or len(messages) <= 1:
                return query  # No conversation history
            
            # Prepare conversation context
            conversation_context = await self._prepare_conversation_context(messages, query)
            
            if not conversation_context:
                return query  # No context prepared
            
            # Use LLM to enhance query with context
            enhanced_query = await self._enhance_query_with_llm(query, conversation_context)
            
            self.logger.info_structured(
                "Query enhanced with context",
                original_query=query,
                enhanced_query=enhanced_query,
                context_messages=len(messages)
            )
            
            return enhanced_query if enhanced_query != query else query
            
        except Exception as e:
            self.logger.error_structured(
                "Context enhancement failed",
                error=str(e)
            )
            return query  # Return original on error
    
    async def _prepare_conversation_context(self, messages: List[Dict[str, Any]], current_query: str) -> str:
        """
        Prepare conversation context with last 10 user-AI messages and summary of older messages.
        Only includes actual conversation between user and AI (what user sees), not internal LLM calls.
        """
        try:
            # Filter ONLY user and assistant messages (actual conversation)
            conversation_messages = []
            
            for msg in messages:
                if isinstance(msg, dict):
                    role = msg.get("role", "").lower()
                    content = msg.get("content", str(msg))
                    
                    # ONLY include user and assistant messages (actual conversation)
                    # Skip system, tool, or other internal messages
                    if role in ["user", "assistant"] and content.strip():
                        conversation_messages.append(f"{role}: {content}")
                else:
                    # Simple string messages - assume user
                    content = str(msg)
                    if content.strip():
                        conversation_messages.append(f"user: {content}")
            
            # If we have more than 10 conversation messages, summarize the oldest ones
            if len(conversation_messages) > 10:
                # Keep last 10 conversation messages
                recent_messages = conversation_messages[-10:]
                older_messages = conversation_messages[:-10]
                
                # Summarize older conversation messages
                summary = await self._summarize_conversation(older_messages)
                
                # Combine summary with recent conversation messages
                context = f"Previous conversation summary:\n{summary}\n\nRecent conversation:\n" + "\n".join(recent_messages)
            else:
                # Use all conversation messages
                context = "Conversation:\n" + "\n".join(conversation_messages)
            
            return context
            
        except Exception as e:
            self.logger.error_structured(
                "Context preparation failed",
                error=str(e)
            )
            return ""
    
    async def _summarize_conversation(self, messages: List[str]) -> str:
        """
        Summarize older conversation messages using LLM.
        """
        try:
            if not messages:
                return "No previous conversation."
            
            conversation_text = "\n".join(messages)
            
            messages = [
                SystemMessage(content="Summarize the conversation in 2-3 sentences, focusing on key information, numbers, and context that might be relevant for future queries."),
                HumanMessage(content=f"Summarize this conversation:\n\n{conversation_text}")
            ]
            
            response = await self.llm_service.llm.ainvoke(messages)
            return response.content.strip()
            
        except Exception as e:
            self.logger.error_structured(
                "Conversation summarization failed",
                error=str(e)
            )
            return "Previous conversation contained various queries and responses."
    
    async def _enhance_query_with_llm(self, query: str, context: str) -> str:
        """
        Use LLM to enhance query with conversation context.
        Generic approach for any tool and context type.
        """
        try:
            messages = [
                SystemMessage(content="""You are a context enhancement assistant. Your job is to enhance queries ONLY when they contain clear references to previous context in the conversation.

RULES:
1. ONLY enhance if the query has context indicators referring to previous conversation
2. DO NOT enhance if the query is self-contained and doesn't reference previous context
3. DO NOT force context into unrelated queries
4. Preserve the original intent and structure of the query
5. If unsure, return the original query unchanged
6. Only respond with the enhanced query, no explanations
"""),
                HumanMessage(content=f"""
Current Query: "{query}"

Conversation Context:
{context}

Analyze if the query contains clear context indicators that refer to previous conversation context. If yes, enhance it by replacing context references with actual values from the conversation. If no, return it unchanged.

Enhanced Query:
""")
            ]
            
            response = await self.llm_service.llm.ainvoke(messages)
            enhanced_query = response.content.strip()
            
            # Remove quotes if present
            if enhanced_query.startswith('"') and enhanced_query.endswith('"'):
                enhanced_query = enhanced_query[1:-1]
            
            # Validate the enhancement
            if enhanced_query != query and self._is_valid_enhancement(query, enhanced_query, context):
                self.logger.info_structured(
                    "Query enhanced with context",
                    original_query=query,
                    enhanced_query=enhanced_query
                )
                return enhanced_query
            else:
                return query
                
        except Exception as e:
            self.logger.error_structured(
                "LLM query enhancement failed",
                error=str(e)
            )
            return query
    
    def _is_valid_enhancement(self, original_query: str, enhanced_query: str, context: str) -> bool:
        """
        Generic validation that enhancement is appropriate and doesn't force context into unrelated queries.
        """
        # If no enhancement was made
        if enhanced_query == original_query:
            return True
        
        # Check if enhancement is reasonable
        try:
            # Enhancement should be longer but not excessively longer
            if len(enhanced_query) > len(original_query) * 3.0:
                return False
            
            # Generic context indicators (not just numeric)
            context_indicators = [
                "these", "those", "both", "the previous", "the first", "the last", 
                "above", "below", "earlier", "mentioned", "same", "different",
                "these 2", "these two", "both values", "those numbers"
            ]
            
            # Check if original query has any context indicators
            has_indicator = any(indicator in original_query.lower() for indicator in context_indicators)
            
            if not has_indicator:
                # No clear indicator - enhancement is suspicious
                return False
            
            # Check if enhancement adds specific content from context
            # This is generic - could be numbers, text, file names, etc.
            original_words = set(original_query.lower().split())
            enhanced_words = set(enhanced_query.lower().split())
            
            # Enhancement should add meaningful content
            new_content = enhanced_words - original_words
            if len(new_content) == 0:
                return False
            
            # But shouldn't add too much unrelated content
            if len(new_content) > 10:  # Arbitrary limit for reasonable enhancement
                return False
            
            # Check if enhancement maintains original query structure
            original_structure = original_query.lower().replace(" ", "").replace(",", "").replace(".", "")
            enhanced_structure = enhanced_query.lower().replace(" ", "").replace(",", "").replace(".", "")
            
            # Enhanced query should contain most of original structure
            common_chars = set(original_structure) & set(enhanced_structure)
            similarity = len(common_chars) / max(len(set(original_structure)), len(set(enhanced_structure)))
            
            if similarity < self.validation_similarity_threshold:  # Similarity below threshold is suspicious
                return False
            
            return True
            
        except Exception:
            # If validation fails, be conservative and don't enhance
            return False
    
    async def extract_context_info(self, messages: List[Dict[str, Any]], info_type: str = "all") -> Dict[str, Any]:
        """
        Extract specific context information from conversation history.
        Only uses user-AI conversation messages (not internal LLM calls).
        
        Args:
            messages: Conversation history
            info_type: Type of info to extract ("numbers", "tools", "topics", "all")
            
        Returns:
            Dictionary with extracted context information
        """
        try:
            if not messages:
                return {}
            
            # Filter ONLY user and assistant messages (actual conversation)
            conversation_messages = []
            for msg in messages:
                if isinstance(msg, dict):
                    role = msg.get("role", "").lower()
                    content = msg.get("content", str(msg))
                    
                    # ONLY include user and assistant messages
                    if role in ["user", "assistant"] and content.strip():
                        conversation_messages.append(f"{role}: {content}")
            
            # Get recent conversation context (last 10 messages)
            recent_conversation = conversation_messages[-10:]
            
            if info_type == "all":
                context_text = "\n".join(recent_conversation)
                
                messages_llm = [
                    SystemMessage(content="Extract key information from the conversation including numbers, tools used, topics discussed, and any other relevant context. Return as JSON."),
                    HumanMessage(content=f"Extract context information:\n\n{context_text}")
                ]
                
                response = await self.llm_service.llm.ainvoke(messages_llm)
                
                try:
                    context_info = json.loads(response.content.strip())
                    return context_info
                except json.JSONDecodeError:
                    return {"raw_context": response.content.strip()}
            
            else:
                # Extract specific type of information from conversation
                context_text = "\n".join(recent_conversation)
                
                messages_llm = [
                    SystemMessage(content=f"Extract {info_type} from the conversation. Return as JSON."),
                    HumanMessage(content=f"Extract {info_type}:\n\n{context_text}")
                ]
                
                response = await self.llm_service.llm.ainvoke(messages_llm)
                
                try:
                    info = json.loads(response.content.strip())
                    return {info_type: info}
                except json.JSONDecodeError:
                    return {info_type: response.content.strip()}
            
        except Exception as e:
            self.logger.error_structured(
                "Context extraction failed",
                error=str(e)
            )
            return {}
    
    async def get_conversation_summary(self, messages: List[Dict[str, Any]], max_length: int = 200) -> str:
        """
        Get a concise summary of the conversation.
        Only uses user-AI conversation messages (not internal LLM calls).
        
        Args:
            messages: Conversation history
            max_length: Maximum length of summary
            
        Returns:
            Concise conversation summary
        """
        try:
            if not messages:
                return "No conversation history."
            
            # Filter ONLY user and assistant messages (actual conversation)
            conversation_messages = []
            for msg in messages:
                if isinstance(msg, dict):
                    role = msg.get("role", "").lower()
                    content = msg.get("content", str(msg))
                    
                    # ONLY include user and assistant messages
                    if role in ["user", "assistant"] and content.strip():
                        conversation_messages.append(f"{role}: {content}")
            
            # Get all conversation messages
            conversation_text = "\n".join(conversation_messages)
            
            messages_llm = [
                SystemMessage(content=f"Summarize the conversation in a single sentence (max {max_length} characters), focusing on the main topics and key information."),
                HumanMessage(content=f"Summarize this conversation:\n\n{conversation_text}")
            ]
            
            response = await self.llm_service.llm.ainvoke(messages_llm)
            summary = response.content.strip()
            
            # Ensure it doesn't exceed max length
            if len(summary) > max_length:
                summary = summary[:max_length-3] + "..."
            
            return summary
            
        except Exception as e:
            self.logger.error_structured(
                "Conversation summary failed",
                error=str(e)
            )
            return "Conversation summary unavailable."
    
    def has_context_indicators(self, query: str) -> bool:
        """
        Check if query contains context indicators.
        
        Args:
            query: User query
            
        Returns:
            True if query contains context indicators
        """
        context_indicators = [
            "these 2", "these two", "the previous", "the values", 
            "those numbers", "both values", "the first", "the last",
            "earlier", "before", "mentioned", "discussed", "above",
            "the same", "that number", "this number", "the result"
        ]
        
        query_lower = query.lower()
        return any(indicator in query_lower for indicator in context_indicators)
