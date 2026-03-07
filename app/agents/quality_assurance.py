"""
Quality Assurance Agent
Responsible for validating response quality, coherence, and accuracy.
Production-grade implementation with comprehensive quality checks.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import re

from .base_agent import BaseAgent

logger = logging.getLogger(__name__)


class QualityAssuranceAgent(BaseAgent):
    """
    Quality Assurance Agent that validates response quality, coherence,
    and accuracy before final delivery to user.
    """
    
    def __init__(self, llm, memory_manager, tool_registry):
        super().__init__(llm, memory_manager, tool_registry)
        self.quality_thresholds = {
            "coherence": 0.7,
            "accuracy": 0.8,
            "completeness": 0.6,
            "relevance": 0.8
        }
        self.max_quality_retries = 1
    
    async def validate_response_quality(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate the quality of the formatted response.
        
        Args:
            state: Current workflow state
            
        Returns:
            State with quality validation results
        """
        try:
            formatted_response = state.get("formatted_response", "")
            query = state.get("current_query", "")
            tool_results = state.get("tool_results", [])
            context_enhanced = state.get("context_enhanced", False)
            
            # Perform quality checks
            quality_scores = await self._perform_quality_checks(
                query, formatted_response, tool_results, state
            )
            
            # Determine if response meets quality standards
            overall_quality = self._calculate_overall_quality(quality_scores)
            meets_quality = overall_quality >= 0.7  # 70% quality threshold
            
            if not meets_quality:
                logger.info_structured(
                    "Response quality below threshold",
                    conversation_id=state.get("conversation_id"),
                    overall_quality=overall_quality,
                    quality_scores=quality_scores
                )
                
                # Attempt quality improvement
                improved_state = await self._improve_response_quality(
                    state, quality_scores
                )
                
                if improved_state:
                    return improved_state
            
            # Add quality metadata to state
            validated_state = state.copy()
            validated_state.update({
                "quality_validation": {
                    "validated_at": datetime.utcnow().isoformat(),
                    "overall_quality": overall_quality,
                    "meets_quality": meets_quality,
                    "quality_scores": quality_scores,
                    "validation_passed": True
                }
            })
            
            logger.info_structured(
                "Response quality validation completed",
                conversation_id=state.get("conversation_id"),
                overall_quality=overall_quality,
                meets_quality=meets_quality
            )
            
            return validated_state
            
        except Exception as e:
            logger.error_structured(
                "Quality assurance validation failed",
                error=str(e),
                conversation_id=state.get("conversation_id")
            )
            # Fail gracefully - allow response to proceed
            state["quality_validation"] = {
                "validation_passed": False,
                "error": str(e),
                "validated_at": datetime.utcnow().isoformat()
            }
            return state
    
    async def _perform_quality_checks(self, query: str, response: str, 
                                    tool_results: List[Dict], state: Dict[str, Any]) -> Dict[str, float]:
        """
        Perform comprehensive quality checks on the response.
        
        Args:
            query: Original query
            response: Formatted response
            tool_results: Tool execution results
            state: Current workflow state
            
        Returns:
            Dictionary of quality scores
        """
        try:
            quality_scores = {}
            
            # 1. Coherence Check
            quality_scores["coherence"] = await self._check_coherence(query, response, state)
            
            # 2. Accuracy Check (if tools were used)
            if tool_results:
                quality_scores["accuracy"] = await self._check_accuracy(response, tool_results)
            else:
                quality_scores["accuracy"] = 0.8  # Default for conversational responses
            
            # 3. Completeness Check
            quality_scores["completeness"] = await self._check_completeness(query, response, tool_results)
            
            # 4. Relevance Check
            quality_scores["relevance"] = await self._check_relevance(query, response)
            
            # 5. Formatting Check
            quality_scores["formatting"] = await self._check_formatting(response)
            
            # 6. Safety Check
            quality_scores["safety"] = await self._check_safety(response)
            
            return quality_scores
            
        except Exception as e:
            logger.error_structured(
                "Quality checks failed",
                error=str(e)
            )
            # Return default scores
            return {
                "coherence": 0.5,
                "accuracy": 0.5,
                "completeness": 0.5,
                "relevance": 0.5,
                "formatting": 0.5,
                "safety": 0.5
            }
    
    async def _check_coherence(self, query: str, response: str, state: Dict[str, Any]) -> float:
        """Check response coherence and logical flow."""
        try:
            # Basic coherence checks
            if not response or len(response.strip()) < 10:
                return 0.3
            
            # Check for contradictory statements
            contradictions = self._detect_contradictions(response)
            if contradictions:
                return 0.4
            
            # Check for logical flow
            logical_flow_score = self._assess_logical_flow(response)
            
            # Check context consistency
            context_consistency = self._check_context_consistency(response, state)
            
            # Combine scores
            coherence_score = (logical_flow_score + context_consistency) / 2
            
            return min(coherence_score, 1.0)
            
        except Exception as e:
            logger.error_structured(
                "Coherence check failed",
                error=str(e)
            )
            return 0.5
    
    async def _check_accuracy(self, response: str, tool_results: List[Dict], query: str = "") -> float:
        """Check response accuracy using LLMService."""
        try:
            return await self.llm_service.assess_accuracy(response, tool_results)
        except Exception as e:
            logger.error_structured(
                "Accuracy check failed",
                error=str(e)
            )
            return 0.7 if tool_results and not any(r.get("error") for r in tool_results) else 0.5
    
    async def _check_completeness(self, query: str, response: str, tool_results: List[Dict]) -> float:
        """Check response completeness."""
        try:
            completeness_score = 0.8  # Base score
            
            # Check if response addresses all parts of the query
            query_parts = self._extract_query_parts(query)
            addressed_parts = 0
            
            for part in query_parts:
                if self._is_query_part_addressed(part, response):
                    addressed_parts += 1
            
            if query_parts:
                completeness_score = (addressed_parts / len(query_parts)) * 0.8
            
            # Check if tool results are fully represented
            if tool_results:
                results_represented = sum(1 for result in tool_results 
                                        if self._is_tool_result_represented(result, response))
                tool_completeness = (results_represented / len(tool_results)) * 0.2
                completeness_score += tool_completeness
            
            return min(completeness_score, 1.0)
            
        except Exception as e:
            logger.error_structured(
                "Completeness check failed",
                error=str(e)
            )
            return 0.5
    
    async def _check_relevance(self, query: str, response: str) -> float:
        """Check response relevance using LLMService."""
        try:
            return await self.llm_service.assess_relevance(query, response)
        except Exception as e:
            logger.error_structured(
                "Relevance check failed",
                error=str(e)
            )
            return 0.5
    
    async def _check_formatting(self, response: str) -> float:
        """Check response formatting quality."""
        try:
            formatting_score = 0.8  # Base score
            
            # Check for proper markdown formatting
            if "**" in response and "**" in response.split("**")[1]:
                formatting_score += 0.1  # Has bold formatting
            
            if "📊" in response or "🔍" in response or "📈" in response:
                formatting_score += 0.1  # Has emojis
            
            # Check for proper structure
            lines = response.split('\n')
            if len(lines) > 1:
                formatting_score += 0.1  # Multi-line structure
            
            # Check for proper spacing
            if not re.search(r'\s{3,}', response):  # No excessive spaces
                formatting_score += 0.1
            
            # Check for proper length
            if 50 <= len(response) <= 1000:
                formatting_score += 0.1
            elif len(response) > 1000:
                formatting_score -= 0.2  # Too long
            
            return min(formatting_score, 1.0)
            
        except Exception as e:
            logger.error_structured(
                "Formatting check failed",
                error=str(e)
            )
            return 0.5
    
    async def _check_safety(self, response: str) -> float:
        """Check response safety and appropriateness."""
        try:
            # Basic safety checks
            unsafe_patterns = [
                r'\b(hate|kill|harm|violence|terror)\b',
                r'\b(illegal|criminal|fraud|scam)\b',
                r'\b(personal|private|confidential)\s+(information|data)'
            ]
            
            safety_score = 1.0
            
            for pattern in unsafe_patterns:
                if re.search(pattern, response, re.IGNORECASE):
                    safety_score -= 0.3
            
            # Check for appropriate language
            if response.isupper() and len(response) > 50:
                safety_score -= 0.2  # Excessive shouting
            
            return max(safety_score, 0.0)
            
        except Exception as e:
            logger.error_structured(
                "Safety check failed",
                error=str(e)
            )
            return 0.5
    
    def _detect_contradictions(self, response: str) -> List[str]:
        """Detect contradictory statements in response."""
        contradictions = []
        
        # Simple contradiction patterns
        contradiction_patterns = [
            (r'\b(both|all)\b', r'\b(neither|none)\b'),
            (r'\balways\b', r'\bnever\b'),
            (r'\bgreater than\b', r'\blesser than\b'),
            (r'\bincrease\b', r'\bdecrease\b')
        ]
        
        for pattern1, pattern2 in contradiction_patterns:
            if re.search(pattern1, response, re.IGNORECASE) and re.search(pattern2, response, re.IGNORECASE):
                contradictions.append(f"Contradiction: {pattern1} vs {pattern2}")
        
        return contradictions
    
    def _assess_logical_flow(self, response: str) -> float:
        """Assess logical flow of response."""
        try:
            # Check for logical connectors
            logical_connectors = ['because', 'therefore', 'however', 'moreover', 'furthermore', 'consequently']
            connector_count = sum(1 for connector in logical_connectors if connector in response.lower())
            
            # Check for proper sentence structure
            sentences = re.split(r'[.!?]+', response)
            proper_sentences = sum(1 for sentence in sentences if len(sentence.strip()) > 5)
            
            # Calculate flow score
            flow_score = 0.6  # Base score
            
            if connector_count > 0:
                flow_score += min(connector_count * 0.1, 0.2)
            
            if proper_sentences > 1:
                flow_score += 0.2
            
            return min(flow_score, 1.0)
            
        except Exception:
            return 0.5
    
    def _check_context_consistency(self, response: str, state: Dict[str, Any]) -> float:
        """Check consistency with conversation context."""
        try:
            context_enhanced = state.get("context_enhanced", False)
            original_query = state.get("original_query", "")
            current_query = state.get("current_query", "")
            
            consistency_score = 0.8  # Base score
            
            if context_enhanced and original_query != current_query:
                # Check if response acknowledges the enhancement
                if "enhanced" in response.lower() or "context" in response.lower():
                    consistency_score += 0.2
            
            return min(consistency_score, 1.0)
            
        except Exception:
            return 0.5
    
    def _extract_query_parts(self, query: str) -> List[str]:
        """Extract meaningful parts from query."""
        # Simple implementation - split by common separators
        parts = re.split(r'\b(and|or|but|with|for|to)\b', query, flags=re.IGNORECASE)
        return [part.strip() for part in parts if part.strip() and len(part.strip()) > 2]
    
    def _is_query_part_addressed(self, query_part: str, response: str) -> bool:
        """Check if a query part is addressed in response."""
        query_words = set(re.findall(r'\b\w+\b', query_part.lower()))
        response_words = set(re.findall(r'\b\w+\b', response.lower()))
        
        # Check for significant word overlap
        overlap = len(query_words.intersection(response_words))
        return overlap >= len(query_words) * 0.5
    
    def _is_tool_result_represented(self, tool_result: Dict, response: str) -> bool:
        """Check if tool result is represented in response."""
        data = tool_result.get("result", {})
        
        # Check for key data points in response
        for key, value in data.items():
            if isinstance(value, (int, float, str)) and str(value) in response:
                return True
        
        return False
    
    def _calculate_overall_quality(self, quality_scores: Dict[str, float]) -> float:
        """Calculate overall quality score from individual scores."""
        weights = {
            "coherence": 0.25,
            "accuracy": 0.25,
            "completeness": 0.20,
            "relevance": 0.20,
            "formatting": 0.05,
            "safety": 0.05
        }
        
        overall_score = 0.0
        for metric, score in quality_scores.items():
            weight = weights.get(metric, 0.1)
            overall_score += score * weight
        
        return overall_score
    
    async def _improve_response_quality(self, state: Dict[str, Any], 
                                     quality_scores: Dict[str, float]) -> Optional[Dict[str, Any]]:
        """
        Attempt to improve response quality.
        
        Args:
            state: Current workflow state
            quality_scores: Current quality scores
            
        Returns:
            Improved state or None if improvement failed
        """
        try:
            retry_count = state.get("quality_improvement_retry_count", 0)
            
            if retry_count >= self.max_quality_retries:
                logger.info_structured(
                    "Quality improvement retry limit reached",
                    conversation_id=state.get("conversation_id"),
                    retry_count=retry_count
                )
                return None
            
            # Identify areas for improvement
            improvement_areas = [
                metric for metric, score in quality_scores.items()
                if score < self.quality_thresholds.get(metric, 0.7)
            ]
            
            if not improvement_areas:
                return None
            
            # Generate improvement prompt
            improvement_prompt = self._generate_improvement_prompt(
                state, quality_scores, improvement_areas
            )
            
            # Use LLM to improve response
            improved_response = await self._improve_with_llm(improvement_prompt, state)
            
            if improved_response and improved_response != state.get("formatted_response"):
                improved_state = state.copy()
                improved_state.update({
                    "formatted_response": improved_response,
                    "quality_improvement_retry_count": retry_count + 1,
                    "quality_improvement_applied": True
                })
                
                logger.info_structured(
                    "Response quality improved",
                    conversation_id=state.get("conversation_id"),
                    improvement_areas=improvement_areas
                )
                
                return improved_state
            
            return None
            
        except Exception as e:
            logger.error_structured(
                "Quality improvement failed",
                error=str(e)
            )
            return None
    
    def _generate_improvement_prompt(self, state: Dict[str, Any], 
                                    quality_scores: Dict[str, float], 
                                    improvement_areas: List[str]) -> str:
        """Generate improvement prompt for LLM."""
        query = state.get("current_query", "")
        response = state.get("formatted_response", "")
        
        prompt = f"""Improve the following response based on quality issues:

Original Query: {query}

Current Response: {response}

Quality Issues Found:
{chr(10).join([f"- {area}: {quality_scores[area]:.2f}" for area in improvement_areas])}

Improvement Guidelines:
"""
        
        if "coherence" in improvement_areas:
            prompt += "- Make the response more coherent and logically flowing\n"
        
        if "accuracy" in improvement_areas:
            prompt += "- Ensure all numerical values and facts are accurate\n"
        
        if "completeness" in improvement_areas:
            prompt += "- Address all parts of the original query completely\n"
        
        if "relevance" in improvement_areas:
            prompt += "- Make the response more relevant to the query\n"
        
        if "formatting" in improvement_areas:
            prompt += "- Improve formatting with proper markdown and structure\n"
        
        prompt += """
Return only the improved response (no explanation):"""
    async def _improve_with_llm(self, prompt: str, state: Dict[str, Any]) -> Optional[str]:
        """Use LLM to improve response."""
        try:
            messages = [
                SystemMessage(content="You are a response quality improvement expert. Always return only the improved response."),
                HumanMessage(content=prompt)
            ]
            
            response = await self.llm_service.llm.ainvoke(messages)
            improved_response = response.content.strip()
            
            return improved_response if improved_response else None
            
        except Exception as e:
            logger.error_structured(
                "LLM improvement failed",
                error=str(e)
            )
            return None
