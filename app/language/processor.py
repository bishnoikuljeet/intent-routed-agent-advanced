from typing import Tuple, Optional, Dict, Any
from langdetect import detect, LangDetectException
from deep_translator import GoogleTranslator
from app.core.logging import logger
from app.language.llm_detector import LLMLanguageDetector
import re
import asyncio


class LanguageProcessor:
    def __init__(self, llm=None):
        self.system_language = "en"
        self.llm = llm
        self.llm_detector = LLMLanguageDetector(llm) if llm else None
        self.prompt_injection_patterns = [
            r"ignore\s+previous\s+instructions",
            r"disregard\s+all\s+prior",
            r"forget\s+everything",
            r"you\s+are\s+now",
            r"new\s+instructions",
            r"system\s+prompt",
            r"<\s*script\s*>",
            r"javascript:",
            r"eval\s*\(",
        ]
    
    def detect_language(self, text: str) -> str:
        """
        Detect language using LLM-powered analysis with probability scoring.
        """
        try:
            # Use LLM detector if available
            if self.llm_detector:
                # Check if we're in an event loop
                try:
                    loop = asyncio.get_running_loop()
                    # We're in an event loop, create a task
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(asyncio.run, self.llm_detector.detect_language_with_probability(text))
                        detection_result = future.result()
                except RuntimeError:
                    # No event loop running, safe to use asyncio.run
                    detection_result = asyncio.run(self.llm_detector.detect_language_with_probability(text))
                
                final_language = self.llm_detector.get_final_language_decision(detection_result)
                
                logger.info_structured(
                    "LLM-based language detection completed",
                    detected_language=detection_result['detected_language'],
                    confidence=detection_result['confidence'],
                    final_language=final_language,
                    method=detection_result['method'],
                    is_valid_language=detection_result['is_valid_language']
                )
                
                return final_language
            else:
                # Fallback to original rule-based detection
                return self._fallback_detect_language(text)
                
        except Exception as e:
            logger.error_structured(
                "Language detection failed, using fallback",
                error=str(e),
                text_length=len(text)
            )
            return self._fallback_detect_language(text)
    
    def _fallback_detect_language(self, text: str) -> str:
        """
        Fallback language detection using rule-based approach.
        """
        try:
            # For very short text, use character-based detection only - NO hardcoded word lists
            if len(text.strip()) < 10:
                # Check if text contains only English alphabet characters
                if re.match(r'^[a-zA-Z\s]+$', text.strip()):
                    logger.debug_structured("Short text with English characters, defaulting to English", text_length=len(text))
                    return "en"
            
            # Priority 2: Use langdetect for longer text
            lang = detect(text)
            
            # Priority 3: English confidence check - if English is detected with high confidence, use it
            if lang == 'en':
                logger.debug_structured("English detected with confidence", text_length=len(text))
                return "en"
            
            # Priority 4: For other languages, require strong evidence and English characters check
            if lang in ['pt', 'fr', 'de', 'it', 'es']:
                # Only accept non-English if text has strong indicators and non-English characters
                # Check if text contains only English characters - if so, default to English
                if re.match(r'^[a-zA-Z\s\-\.!?\'\,]+$', text.strip()):
                    logger.debug_structured("Text contains only English characters, defaulting to English", detected_lang=lang, text=text[:50])
                    return "en"
                
                # For longer text, use character-based detection only - NO hardcoded word lists
                if len(text.strip()) < 50:
                    # Check if text contains only English alphabet characters
                    if re.match(r'^[a-zA-Z\s\-\.!?\'\,]+$', text.strip()):
                        logger.debug_structured("English characters detected, defaulting to English", detected_lang=lang, text=text[:50])
                        return "en"
            
            # Priority 5: Prefer English unless there's overwhelming evidence of another language
            if lang != 'en':
                # Final check: if text is mostly English characters, default to English
                english_char_count = sum(1 for c in text if c.isalpha() and c.lower() in 'abcdefghijklmnopqrstuvwxyz')
                total_alpha_count = sum(1 for c in text if c.isalpha())
                
                if total_alpha_count > 0 and (english_char_count / total_alpha_count) > 0.8:
                    logger.debug_structured("High English character ratio, defaulting to English", detected_lang=lang, english_ratio=english_char_count/total_alpha_count)
                    return "en"
            
            logger.debug_structured("Language detected", language=lang, text_length=len(text))
            return lang
        except LangDetectException:
            logger.warning_structured("Language detection failed, defaulting to English")
            return "en"
    
    async def detect_language_async(self, text: str) -> str:
        """
        Async version of detect_language for LLM-based detection.
        """
        try:
            # Use LLM detector if available
            if self.llm_detector:
                detection_result = await self.llm_detector.detect_language_with_probability(text)
                final_language = self.llm_detector.get_final_language_decision(detection_result)
                
                logger.info_structured(
                    "LLM-based language detection completed",
                    detected_language=detection_result['detected_language'],
                    confidence=detection_result['confidence'],
                    final_language=final_language,
                    method=detection_result['method'],
                    is_valid_language=detection_result['is_valid_language']
                )
                
                return final_language
            else:
                # Fallback to synchronous detection
                return self._fallback_detect_language(text)
                
        except Exception as e:
            logger.error_structured(
                "Async language detection failed, using fallback",
                error=str(e),
                text_length=len(text)
            )
            return self._fallback_detect_language(text)
    
    def translate_to_system_language(self, text: str, source_lang: str) -> str:
        if source_lang == self.system_language:
            return text
        
        try:
            translator = GoogleTranslator(source=source_lang, target=self.system_language)
            translated = translator.translate(text)
            logger.info_structured(
                "Translated to system language",
                source_lang=source_lang,
                target_lang=self.system_language
            )
            return translated
        except Exception as e:
            logger.error_structured(
                "Translation failed",
                error=str(e),
                source_lang=source_lang
            )
            return text
    
    def translate_from_system_language(self, text: str, target_lang: str) -> str:
        if target_lang == self.system_language:
            return text
        
        try:
            translator = GoogleTranslator(source=self.system_language, target=target_lang)
            translated = translator.translate(text)
            logger.info_structured(
                "Translated from system language",
                source_lang=self.system_language,
                target_lang=target_lang
            )
            return translated
        except Exception as e:
            logger.error_structured(
                "Translation failed",
                error=str(e),
                target_lang=target_lang
            )
            return text
    
    def correct_typos(self, text: str) -> str:
        """
        Correct spelling errors in text using spell checking.
        """
        try:
            from textblob import TextBlob
            
            # Create TextBlob object for spell checking
            blob = TextBlob(text)
            
            # Correct spelling
            corrected = str(blob.correct())
            
            # Normalize whitespace
            corrected = corrected.strip()
            corrected = re.sub(r'\s+', ' ', corrected)
            
            return corrected
            
        except ImportError:
            # Fallback if textblob not available - just normalize whitespace
            logger.warning_structured("textblob not available, using basic normalization")
            corrected = text.strip()
            corrected = re.sub(r'\s+', ' ', corrected)
            return corrected
        except Exception as e:
            logger.error_structured("Typo correction failed", error=str(e))
            return text
    
    def sanitize_input(self, text: str) -> str:
        sanitized = text.strip()
        sanitized = re.sub(r'[^\w\s\-.,!?@#$%&*()\[\]{}:;"\'/\\]', '', sanitized)
        
        if len(sanitized) > 5000:
            sanitized = sanitized[:5000]
            logger.warning_structured("Input truncated", original_length=len(text))
        
        return sanitized
    
    def detect_prompt_injection(self, text: str) -> Tuple[bool, Optional[str]]:
        text_lower = text.lower()
        
        for pattern in self.prompt_injection_patterns:
            if re.search(pattern, text_lower, re.IGNORECASE):
                logger.warning_structured(
                    "Potential prompt injection detected",
                    pattern=pattern,
                    text_snippet=text[:100]
                )
                return True, f"Detected pattern: {pattern}"
        
        return False, None
    
    def process_input(self, text: str) -> Tuple[str, str, bool, Optional[str]]:
        sanitized = self.sanitize_input(text)
        
        is_injection, injection_reason = self.detect_prompt_injection(sanitized)
        if is_injection:
            return sanitized, "en", True, injection_reason
        
        detected_lang = self.detect_language(sanitized)
        
        corrected = self.correct_typos(sanitized)
        
        translated = self.translate_to_system_language(corrected, detected_lang)
        
        return translated, detected_lang, False, None
    
    def process_output(self, text: str, target_language: str) -> str:
        return self.translate_from_system_language(text, target_language)
