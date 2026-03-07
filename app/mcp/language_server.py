from app.mcp.base import BaseMCPServer, MCPTool, MCPResource, MCPPrompt
from typing import Dict, Any
from app.language.processor import LanguageProcessor


class LanguageMCPServer(BaseMCPServer):
    def __init__(self):
        self.processor = LanguageProcessor()
        super().__init__("language")
    
    def _initialize(self):
        self.register_tool(MCPTool(
            name="detect_language",
            description="Detect the language of input text",
            input_schema={
                "type": "object",
                "properties": {
                    "text": {"type": "string"}
                },
                "required": ["text"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "language": {"type": "string"},
                    "confidence": {"type": "number"}
                }
            },
            handler=self._detect_language
        ))
        
        self.register_tool(MCPTool(
            name="translate_text",
            description="Translate text from one language to another",
            input_schema={
                "type": "object",
                "properties": {
                    "text": {"type": "string"},
                    "source_lang": {"type": "string"},
                    "target_lang": {"type": "string"}
                },
                "required": ["text", "target_lang"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "translated_text": {"type": "string"},
                    "source_lang": {"type": "string"},
                    "target_lang": {"type": "string"}
                }
            },
            handler=self._translate_text
        ))
        
        self.register_tool(MCPTool(
            name="correct_typos",
            description="Correct typos and normalize text",
            input_schema={
                "type": "object",
                "properties": {
                    "text": {"type": "string"}
                },
                "required": ["text"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "corrected_text": {"type": "string"},
                    "changes_made": {"type": "boolean"}
                }
            },
            handler=self._correct_typos
        ))
        
        self.register_tool(MCPTool(
            name="normalize_text",
            description="Normalize and sanitize input text",
            input_schema={
                "type": "object",
                "properties": {
                    "text": {"type": "string"}
                },
                "required": ["text"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "normalized_text": {"type": "string"},
                    "is_safe": {"type": "boolean"}
                }
            },
            handler=self._normalize_text
        ))
        
        self.register_prompt(MCPPrompt(
            name="translation",
            description="Translate text with context preservation",
            template="""Translate the following text from {source_lang} to {target_lang}, preserving meaning and context:

Text: {text}

Provide an accurate translation.""",
            arguments=["text", "source_lang", "target_lang"]
        ))
        
        self.register_prompt(MCPPrompt(
            name="grammar_correction",
            description="Correct grammar and improve text quality",
            template="""Correct any grammar errors and improve the quality of this text:

{text}

Provide the corrected version.""",
            arguments=["text"]
        ))
    
    async def _detect_language(self, text: str) -> Dict[str, Any]:
        language = self.processor.detect_language(text)
        
        return {
            "language": language,
            "confidence": 0.95,
            "text_length": len(text)
        }
    
    async def _translate_text(
        self,
        text: str,
        target_lang: str,
        source_lang: str = None
    ) -> Dict[str, Any]:
        if not source_lang:
            source_lang = self.processor.detect_language(text)
        
        if source_lang == target_lang:
            return {
                "translated_text": text,
                "source_lang": source_lang,
                "target_lang": target_lang,
                "translation_needed": False
            }
        
        translated = self.processor.translate_from_system_language(text, target_lang) \
            if source_lang == "en" else self.processor.translate_to_system_language(text, source_lang)
        
        return {
            "translated_text": translated,
            "source_lang": source_lang,
            "target_lang": target_lang,
            "translation_needed": True
        }
    
    async def _correct_typos(self, text: str) -> Dict[str, Any]:
        corrected = self.processor.correct_typos(text)
        
        return {
            "corrected_text": corrected,
            "changes_made": corrected != text,
            "original_length": len(text),
            "corrected_length": len(corrected)
        }
    
    async def _normalize_text(self, text: str) -> Dict[str, Any]:
        sanitized = self.processor.sanitize_input(text)
        is_injection, _ = self.processor.detect_prompt_injection(sanitized)
        
        return {
            "normalized_text": sanitized,
            "is_safe": not is_injection,
            "original_length": len(text),
            "normalized_length": len(sanitized)
        }
