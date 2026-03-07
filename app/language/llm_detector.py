"""
LLM-Powered Language Detection with Probability Scoring
"""

from typing import Dict, Tuple, Optional
from langchain_core.messages import HumanMessage, SystemMessage
from app.core.logging import logger
import re


class LLMLanguageDetector:
    def __init__(self, llm):
        self.llm = llm
        self.system_language = "en"
        
        # NO hardcoded word lists - use LLM for language detection
    
    def _quick_english_check(self, text: str) -> Tuple[float, bool]:
        """
        Minimal character-based check - NO hardcoded word lists.
        Returns (confidence_score, is_likely_english)
        """
        # Only use character composition - no keyword matching
        confidence = 0.0
        
        alpha_chars = sum(1 for c in text if c.isalpha())
        if alpha_chars > 0:
            # Check if characters are in English alphabet range
            english_chars = sum(1 for c in text if c.isalpha() and ord(c.lower()) >= 97 and ord(c.lower()) <= 122)
            char_ratio = english_chars / alpha_chars
            confidence = char_ratio * 0.6  # Max 0.6 from character check alone
        
        # Low confidence - always defer to LLM for accurate detection
        is_likely_english = confidence >= 0.5
        
        return min(confidence, 1.0), is_likely_english
    
    async def detect_language_with_probability(self, text: str) -> Dict[str, any]:
        """
        Detect language using LLM with probability scoring.
        """
        try:
            # Quick English check first
            quick_confidence, is_likely_english = self._quick_english_check(text)
            
            logger.info_structured(
                "Quick English check completed",
                text_length=len(text),
                quick_confidence=quick_confidence,
                is_likely_english=is_likely_english
            )
            
            # If high confidence in English, return early
            if is_likely_english and quick_confidence >= 0.8:
                logger.info_structured(
                    "High confidence English detected, skipping LLM",
                    confidence=quick_confidence
                )
                return {
                    'detected_language': 'en',
                    'confidence': quick_confidence,
                    'method': 'quick_check',
                    'is_valid_language': True,
                    'reasoning': f'High confidence English detection ({quick_confidence:.2f})'
                }
            
            # Use LLM for detailed analysis
            detection_prompt = f"""Analyze the following text and determine the language with probability scoring:

Text: "{text}"

Respond with a JSON object containing:
1. "detected_language": The most likely language code (e.g., "en", "es", "fr", "de", "it", "pt", "zh", "ja", "ko", "ru", "ar", "hi", "unknown")
2. "confidence": Your confidence level (0.0 to 1.0)
3. "is_valid_language": Whether this appears to be a real human language (true/false)
4. "reasoning": Brief explanation of your decision
5. "alternative_languages": Up to 3 other possible languages with their confidence scores

Consider:
- Character sets and alphabets used
- Common words and patterns
- Grammatical structures
- Technical terms vs natural language
- Gibberish or made-up text detection

If the text appears to be random characters, code, or made-up language, set "is_valid_language" to false and "detected_language" to "unknown".

Response format:
{{"detected_language": "en", "confidence": 0.95, "is_valid_language": true, "reasoning": "Text contains common English words and patterns", "alternative_languages": [{{"language": "fr", "confidence": 0.1}}, {{"language": "de", "confidence": 0.05}}]}}"""
            
            messages = [
                SystemMessage(content="You are an expert language detector. Analyze text and provide accurate language identification with confidence scores."),
                HumanMessage(content=detection_prompt)
            ]
            
            response = await self.llm.ainvoke(messages)
            response_content = response.content.strip()
            
            # Parse JSON response
            import json
            try:
                # Clean up response to extract JSON
                json_match = re.search(r'\{.*\}', response_content, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                    result = json.loads(json_str)
                else:
                    raise ValueError("No JSON found in response")
            except (json.JSONDecodeError, ValueError) as e:
                logger.error_structured(
                    "Failed to parse LLM language detection response",
                    error=str(e),
                    response_content=response_content[:200]
                )
                # Fallback to quick check result
                return {
                    'detected_language': 'en' if quick_confidence > 0.5 else 'unknown',
                    'confidence': quick_confidence,
                    'method': 'fallback',
                    'is_valid_language': quick_confidence > 0.3,
                    'reasoning': f'LLM parsing failed, using quick check result ({quick_confidence:.2f})'
                }
            
            # Validate and enhance result
            detected_language = result.get('detected_language', 'unknown')
            confidence = result.get('confidence', 0.0)
            is_valid_language = result.get('is_valid_language', True)
            reasoning = result.get('reasoning', 'No reasoning provided')
            alternative_languages = result.get('alternative_languages', [])
            
            # If English detected with low confidence, apply quick check boost
            if detected_language == 'en' and confidence < 0.7:
                combined_confidence = (confidence + quick_confidence) / 2
                if combined_confidence > confidence:
                    confidence = combined_confidence
                    reasoning += f" (boosted by English indicators: {quick_confidence:.2f})"
            
            # Ensure confidence is within bounds
            confidence = max(0.0, min(1.0, confidence))
            
            logger.info_structured(
                "LLM language detection completed",
                detected_language=detected_language,
                confidence=confidence,
                is_valid_language=is_valid_language,
                method='llm_analysis'
            )
            
            return {
                'detected_language': detected_language,
                'confidence': confidence,
                'method': 'llm_analysis',
                'is_valid_language': is_valid_language,
                'reasoning': reasoning,
                'alternative_languages': alternative_languages
            }
            
        except Exception as e:
            logger.error_structured(
                "LLM language detection failed",
                error=str(e),
                text_length=len(text)
            )
            
            # Ultimate fallback
            quick_confidence, _ = self._quick_english_check(text)
            return {
                'detected_language': 'en' if quick_confidence > 0.5 else 'unknown',
                'confidence': quick_confidence,
                'method': 'error_fallback',
                'is_valid_language': quick_confidence > 0.3,
                'reasoning': f'LLM detection failed, using quick check ({quick_confidence:.2f})'
            }
    
    def get_final_language_decision(self, detection_result: Dict[str, any]) -> str:
        """
        Make final language decision based on detection results.
        """
        detected_language = detection_result['detected_language']
        confidence = detection_result['confidence']
        is_valid_language = detection_result['is_valid_language']
        
        # If not a valid language, default to English for system compatibility
        if not is_valid_language or detected_language == 'unknown':
            logger.info_structured(
                "Invalid or unknown language detected, defaulting to English",
                detected_language=detected_language,
                confidence=confidence,
                is_valid_language=is_valid_language
            )
            return self.system_language
        
        # If high confidence in detected language, use it
        if confidence >= 0.7:
            return detected_language
        
        # If low confidence but English detected, default to English
        if detected_language == 'en' and confidence >= 0.5:
            return detected_language
        
        # If low confidence in non-English, default to English for safety
        logger.info_structured(
            "Low confidence language detection, defaulting to English",
            detected_language=detected_language,
            confidence=confidence
        )
        return self.system_language
