from typing import List, Optional, Dict, Any
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_openai import AzureChatOpenAI, AzureOpenAIEmbeddings
from app.core.config import settings
from app.core.logging import logger
from app.memory.vector_store import VectorMemoryStore
import json


class MemoryManager:
    def __init__(self):
        self.llm = AzureChatOpenAI(
            azure_endpoint=settings.azure_openai_endpoint,
            api_key=settings.azure_openai_api_key,
            api_version=settings.azure_openai_api_version,
            deployment_name=settings.azure_openai_deployment,
            temperature=0.3,
        )
        
        self.embeddings = AzureOpenAIEmbeddings(
            azure_endpoint=settings.azure_embedding_openai_endpoint,
            api_key=settings.azure_embedding_openai_api_key,
            api_version=settings.azure_embedding_openai_api_version,
            deployment=settings.azure_embedding_openai_deployment,
        )
        
        self.vector_store = VectorMemoryStore(self.embeddings)
        self.summary_threshold = settings.memory_summary_threshold
        self.max_history = settings.max_conversation_history
    
    def should_summarize(self, messages: List[BaseMessage]) -> bool:
        return len(messages) > self.summary_threshold
    
    async def summarize_conversation(
        self,
        messages: List[BaseMessage],
        existing_summary: Optional[str] = None
    ) -> str:
        messages_text = "\n".join([
            f"{msg.__class__.__name__}: {msg.content}"
            for msg in messages
        ])
        
        prompt = f"""Summarize the following conversation concisely, preserving key information, decisions, and context.

{f'Previous summary: {existing_summary}' if existing_summary else ''}

Recent conversation:
{messages_text}

Provide a concise summary that captures the essential information:"""
        
        try:
            response = await self.llm.ainvoke([HumanMessage(content=prompt)])
            summary = response.content
            
            logger.info_structured(
                "Conversation summarized",
                message_count=len(messages),
                summary_length=len(summary)
            )
            
            return summary
        except Exception as e:
            logger.error_structured("Summarization failed", error=str(e))
            return existing_summary or "Conversation summary unavailable"
    
    def split_messages(
        self,
        messages: List[BaseMessage],
        threshold: int
    ) -> tuple[List[BaseMessage], List[BaseMessage]]:
        if len(messages) <= threshold:
            return [], messages
        
        split_point = len(messages) - threshold
        return messages[:split_point], messages[split_point:]
    
    async def process_memory(
        self,
        conversation_id: str,
        messages: List[BaseMessage],
        current_summary: Optional[str] = None
    ) -> tuple[List[BaseMessage], Optional[str]]:
        # Always save new messages to vector store for immediate retrieval
        if messages:
            for msg in messages:
                await self.vector_store.add_message(
                    conversation_id=conversation_id,
                    message=msg,
                    metadata={"message_type": msg.__class__.__name__}
                )
        
        if not self.should_summarize(messages):
            return messages, current_summary
        
        old_messages, recent_messages = self.split_messages(
            messages,
            self.summary_threshold // 2
        )
        
        if old_messages:
            new_summary = await self.summarize_conversation(old_messages, current_summary)
            
            # Update old messages with summarized flag
            for msg in old_messages:
                await self.vector_store.add_message(
                    conversation_id=conversation_id,
                    message=msg,
                    metadata={"summarized": True, "message_type": msg.__class__.__name__}
                )
            
            return recent_messages, new_summary
        
        return messages, current_summary
    
    async def retrieve_relevant_context(
        self,
        conversation_id: str,
        query: str,
        k: int = 5
    ) -> List[Dict[str, Any]]:
        try:
            results = await self.vector_store.search(
                conversation_id=conversation_id,
                query=query,
                k=k
            )
            
            logger.info_structured(
                "Retrieved relevant context",
                conversation_id=conversation_id,
                result_count=len(results)
            )
            
            return results
        except Exception as e:
            logger.error_structured(
                "Context retrieval failed",
                error=str(e),
                conversation_id=conversation_id
            )
            return []
    
    def format_context_for_prompt(self, context: List[Dict[str, Any]]) -> str:
        if not context:
            return ""
        
        formatted = "Relevant conversation history:\n"
        for i, ctx in enumerate(context, 1):
            formatted += f"{i}. {ctx['content']}\n"
        
        return formatted
    
    async def get_conversation_context(
        self,
        conversation_id: str,
        current_query: str,
        recent_messages: List[BaseMessage],
        summary: Optional[str] = None
    ) -> str:
        context_parts = []
        
        if summary:
            context_parts.append(f"Conversation Summary:\n{summary}\n")
        
        relevant_history = await self.retrieve_relevant_context(
            conversation_id=conversation_id,
            query=current_query,
            k=3
        )
        
        if relevant_history:
            context_parts.append(self.format_context_for_prompt(relevant_history))
        
        if recent_messages:
            recent_text = "\n".join([
                f"{msg.__class__.__name__}: {msg.content}"
                for msg in recent_messages[-5:]
            ])
            context_parts.append(f"Recent messages:\n{recent_text}")
        
        return "\n\n".join(context_parts)
