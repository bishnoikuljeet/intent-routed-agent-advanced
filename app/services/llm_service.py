"""
LLM Service - Abstraction layer for LLM interactions.
Provides consistent interface for all LLM calls with prompt management integration.
"""

import json
import os
from typing import Dict, Any, List, Optional
from langchain_openai import AzureChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from app.prompts import SystemPrompts, TaskPrompts, PromptTemplates, LLMSchemas
from app.core.config import settings
from app.core.logging import logger

# Initialize LangSmith tracing for LLM calls
if settings.langchain_tracing_v2 and settings.langchain_api_key:
    try:
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        os.environ["LANGCHAIN_API_KEY"] = settings.langchain_api_key
        os.environ["LANGCHAIN_PROJECT"] = settings.langchain_project
        os.environ["LANGCHAIN_ENDPOINT"] = settings.langchain_endpoint
        
        logger.info_structured(
            "LLM Service: LangSmith tracing enabled",
            project=settings.langchain_project
        )
    except Exception as e:
        logger.warning_structured(
            "LLM Service: Failed to enable LangSmith tracing",
            error=str(e)
        )


class LLMService:
    """
    Service for managing LLM interactions.
    Centralizes prompt construction, LLM calls, and response parsing.
    """
    
    def __init__(self):
        """
        Initialize LLM service with Azure OpenAI configuration.
        """
        self.llm = AzureChatOpenAI(
            azure_endpoint=settings.azure_openai_endpoint,
            api_key=settings.azure_openai_api_key,
            api_version=settings.azure_openai_api_version,
            deployment_name=settings.azure_openai_deployment,
            temperature=0.3,
        )
        self.system_prompts = SystemPrompts()
        self.task_prompts = TaskPrompts()
        self.templates = PromptTemplates()
        self.schemas = LLMSchemas()
    
    async def infer_context(
        self,
        query: str,
        tools: List[Dict[str, Any]],
        recent_context: str = ""
    ) -> Dict[str, Any]:
        """
        Use LLM to infer context and select appropriate tool.
        
        Args:
            query: User query
            tools: Available tools with schemas
            recent_context: Recent conversation context
            
        Returns:
            Inference result dictionary
        """
        try:
            # Create token-optimized tool summary
            tools_summary = self.templates.format_tools_compact(tools)
            
            # Build messages
            system_prompt = self.system_prompts.get_prompt('context_analyzer')
            task_prompt = self.task_prompts.context_inference(
                query=query,
                tools_summary=tools_summary,
                recent_context=recent_context
            )
            
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=task_prompt)
            ]
            
            # Call LLM
            response = await self.llm.ainvoke(messages)
            
            # Parse JSON response
            json_str = self.templates.extract_json_from_response(response.content)
            result = json.loads(json_str)
            
            logger.info_structured(
                "LLM context inference completed",
                query=query[:50],
                selected_tool=result.get('selected_tool'),
                confidence=result.get('confidence')
            )
            
            return result
            
        except Exception as e:
            logger.error_structured(
                "LLM context inference failed",
                error=str(e),
                query=query[:50]
            )
            return {
                "can_handle": False,
                "selected_tool": None,
                "parameters": {},
                "confidence": 0.0,
                "reasoning": f"Error: {str(e)}",
                "needs_clarification": True,
                "clarification_question": "I encountered an error. Could you rephrase your request?"
            }
    
    async def generate_execution_plan(
        self,
        query: str,
        tools: List[Dict[str, Any]],
        intent: str = ""
    ) -> Dict[str, Any]:
        """
        Use LLM to generate execution plan.
        
        Args:
            query: User query
            tools: Available tools
            intent: User intent if known
            
        Returns:
            Execution plan dictionary
        """
        try:
            # Create compact tool summary
            tools_summary = self.templates.format_tools_compact(tools)
            
            # Build messages
            system_prompt = self.system_prompts.get_prompt('execution_planner')
            task_prompt = self.task_prompts.execution_planning(
                query=query,
                tools_summary=tools_summary,
                intent=intent
            )
            
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=task_prompt)
            ]
            
            # Call LLM
            response = await self.llm.ainvoke(messages)
            
            # Parse JSON response with error recovery
            json_str = self.templates.extract_json_from_response(response.content)
            
            try:
                result = json.loads(json_str)
            except json.JSONDecodeError as json_err:
                # Attempt to repair common JSON errors
                logger.warning_structured(
                    "JSON parsing failed, attempting repair",
                    error=str(json_err),
                    json_preview=json_str[:200]
                )
                
                # Try common fixes
                repaired_json = json_str
                
                # Fix 1: Remove trailing commas
                repaired_json = repaired_json.replace(',]', ']').replace(',}', '}')
                
                # Fix 2: Fix unquoted property names (common LLM error)
                import re
                repaired_json = re.sub(r'(\w+):', r'"\1":', repaired_json)
                
                # Fix 3: Remove comments if any
                repaired_json = re.sub(r'//.*?\n', '\n', repaired_json)
                repaired_json = re.sub(r'/\*.*?\*/', '', repaired_json, flags=re.DOTALL)
                
                try:
                    result = json.loads(repaired_json)
                    logger.info_structured("JSON repair successful")
                except json.JSONDecodeError:
                    # If repair fails, return minimal valid plan
                    logger.error_structured(
                        "JSON repair failed, returning empty plan",
                        original_error=str(json_err)
                    )
                    raise
            
            logger.info_structured(
                "LLM execution plan generated",
                query=query[:50],
                steps_count=len(result.get('steps', []))
            )
            
            return result
            
        except Exception as e:
            logger.error_structured(
                "LLM execution planning failed",
                error=str(e),
                query=query[:50]
            )
            return {
                "reasoning": f"Planning failed: {str(e)}",
                "steps": [],
                "estimated_duration": 0.0,
                "requires_parallel": False
            }
    
    async def format_response(
        self,
        query: str,
        tool_results: List[Dict[str, Any]]
    ) -> str:
        """
        Use LLM to format tool results into natural response.
        
        Args:
            query: Original user query
            tool_results: Tool execution results
            
        Returns:
            Natural language response
        """
        try:
            # Create compact results summary
            results_compact = self.templates.format_results_compact(tool_results)
            
            # Build messages
            system_prompt = self.system_prompts.get_prompt('response_formatter')
            task_prompt = self.task_prompts.response_formatting(
                query=query,
                tool_results=results_compact
            )
            
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=task_prompt)
            ]
            
            # Call LLM
            response = await self.llm.ainvoke(messages)
            
            logger.info_structured(
                "LLM response formatting completed",
                query=query[:50]
            )
            
            return response.content.strip()
            
        except Exception as e:
            logger.error_structured(
                "LLM response formatting failed",
                error=str(e)
            )
            return f"I completed the operation but encountered an error formatting the results: {str(e)}"
    
    async def assess_accuracy(
        self,
        response: str,
        tool_results: List[Dict[str, Any]]
    ) -> float:
        """
        Use LLM to assess response accuracy.
        
        Args:
            response: Generated response
            tool_results: Original tool results
            
        Returns:
            Accuracy score (0.0-1.0)
        """
        try:
            # Create compact results
            results_compact = self.templates.format_results_compact(tool_results)
            
            # Build messages
            system_prompt = self.system_prompts.get_prompt('quality_assessor')
            task_prompt = self.task_prompts.accuracy_assessment(
                response=response,
                tool_results=results_compact
            )
            
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=task_prompt)
            ]
            
            # Call LLM
            llm_response = await self.llm.ainvoke(messages)
            
            # Parse numeric response
            score_str = llm_response.content.strip()
            score = float(score_str)
            
            return max(0.0, min(1.0, score))
            
        except Exception as e:
            logger.error_structured(
                "LLM accuracy assessment failed",
                error=str(e)
            )
            return 0.7  # Default moderate score
    
    async def assess_relevance(
        self,
        query: str,
        response: str
    ) -> float:
        """
        Use LLM to assess response relevance.
        
        Args:
            query: Original query
            response: Generated response
            
        Returns:
            Relevance score (0.0-1.0)
        """
        try:
            # Build messages
            system_prompt = self.system_prompts.get_prompt('semantic_analyzer')
            task_prompt = self.task_prompts.relevance_assessment(
                query=query,
                response=response
            )
            
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=task_prompt)
            ]
            
            # Call LLM
            llm_response = await self.llm.ainvoke(messages)
            
            # Parse numeric response
            score_str = llm_response.content.strip()
            score = float(score_str)
            
            return max(0.0, min(1.0, score))
            
        except Exception as e:
            logger.error_structured(
                "LLM relevance assessment failed",
                error=str(e)
            )
            return 0.7  # Default moderate score
    
    async def check_completeness(
        self,
        query: str,
        tools: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Use LLM to check query completeness.
        Replaces rule-based word count heuristics.
        
        Args:
            query: User query
            tools: Available tools
            
        Returns:
            Completeness assessment dictionary
        """
        try:
            # Create compact tool summary
            tools_summary = self.templates.format_tools_compact(tools)
            
            # Build messages
            system_prompt = self.system_prompts.get_prompt('completeness_checker')
            task_prompt = self.task_prompts.completeness_check(
                query=query,
                tools_summary=tools_summary
            )
            
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=task_prompt)
            ]
            
            # Call LLM
            response = await self.llm.ainvoke(messages)
            
            # Parse JSON response
            json_str = self.templates.extract_json_from_response(response.content)
            result = json.loads(json_str)
            
            logger.info_structured(
                "LLM completeness check completed",
                query=query[:50],
                is_complete=result.get('is_complete')
            )
            
            return result
            
        except Exception as e:
            logger.error_structured(
                "LLM completeness check failed",
                error=str(e)
            )
            return {
                "is_complete": True,  # Default to complete on error
                "confidence": 0.5,
                "missing_info": [],
                "reasoning": f"Error during check: {str(e)}",
                "suggested_clarification": ""
            }
    
    async def assess_semantic_similarity(
        self,
        text1: str,
        text2: str
    ) -> float:
        """
        Use LLM to assess semantic similarity.
        Replaces word overlap calculations.
        
        Args:
            text1: First text
            text2: Second text
            
        Returns:
            Similarity score (0.0-1.0)
        """
        try:
            # Build messages
            system_prompt = self.system_prompts.get_prompt('semantic_analyzer')
            task_prompt = self.task_prompts.semantic_similarity(
                text1=text1,
                text2=text2
            )
            
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=task_prompt)
            ]
            
            # Call LLM
            response = await self.llm.ainvoke(messages)
            
            # Parse numeric response
            score_str = response.content.strip()
            score = float(score_str)
            
            return max(0.0, min(1.0, score))
            
        except Exception as e:
            logger.error_structured(
                "LLM semantic similarity failed",
                error=str(e)
            )
            return 0.5  # Default moderate similarity
    
    async def determine_response_type(
        self,
        query: str,
        tool_results: List[Dict[str, Any]]
    ) -> str:
        """
        Use LLM to determine response type.
        
        Args:
            query: User query
            tool_results: Tool results
            
        Returns:
            Response type string
        """
        try:
            # Create compact results summary
            results_summary = self.templates.format_results_compact(tool_results)
            
            # Build messages
            system_prompt = self.system_prompts.get_prompt('response_formatter')
            task_prompt = self.task_prompts.response_type_detection(
                query=query,
                results_summary=results_summary
            )
            
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=task_prompt)
            ]
            
            # Call LLM
            response = await self.llm.ainvoke(messages)
            
            response_type = response.content.strip().lower()
            
            # Validate against common types (but don't restrict)
            valid_types = ["comparison", "calculation", "metrics", "search", "default", "error"]
            if response_type not in valid_types:
                response_type = "default"
            
            return response_type
            
        except Exception as e:
            logger.error_structured(
                "LLM response type determination failed",
                error=str(e)
            )
            return "default"
