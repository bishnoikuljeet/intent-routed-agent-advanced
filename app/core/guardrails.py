from typing import Tuple, Optional, Any, Dict
from pydantic import BaseModel, ValidationError
from app.core.logging import logger
import re


class GuardrailValidator:
    """Enhanced validation and safety checks"""
    
    def __init__(self):
        self.max_input_length = 5000
        self.max_output_length = 10000
        self.min_confidence_threshold = 0.0
        self.max_confidence_threshold = 1.0
    
    def validate_input_length(self, text: str) -> Tuple[bool, Optional[str]]:
        """Validate input length"""
        if len(text) > self.max_input_length:
            return False, f"Input exceeds maximum length of {self.max_input_length} characters"
        
        if len(text) == 0:
            return False, "Input cannot be empty"
        
        return True, None
    
    def validate_output_length(self, text: str) -> Tuple[bool, Optional[str]]:
        """Validate output length"""
        if len(text) > self.max_output_length:
            return False, f"Output exceeds maximum length of {self.max_output_length} characters"
        
        return True, None
    
    def validate_confidence_score(self, score: float) -> Tuple[bool, Optional[str]]:
        """Validate confidence score is in valid range"""
        if not isinstance(score, (int, float)):
            return False, "Confidence score must be a number"
        
        if score < self.min_confidence_threshold or score > self.max_confidence_threshold:
            return False, f"Confidence score must be between {self.min_confidence_threshold} and {self.max_confidence_threshold}"
        
        return True, None
    
    def validate_json_structure(self, data: Any, expected_keys: list) -> Tuple[bool, Optional[str]]:
        """Validate JSON structure has expected keys"""
        if not isinstance(data, dict):
            return False, "Data must be a dictionary"
        
        missing_keys = [key for key in expected_keys if key not in data]
        
        if missing_keys:
            return False, f"Missing required keys: {', '.join(missing_keys)}"
        
        return True, None
    
    def validate_pydantic_model(self, model_class: type[BaseModel], data: Dict) -> Tuple[bool, Optional[str], Optional[BaseModel]]:
        """Validate data against Pydantic model"""
        try:
            instance = model_class(**data)
            return True, None, instance
        except ValidationError as e:
            error_msg = f"Validation failed: {str(e)}"
            logger.warning_structured("Pydantic validation failed", error=error_msg)
            return False, error_msg, None
    
    def sanitize_sql_input(self, text: str) -> str:
        """Basic SQL injection prevention"""
        # Remove common SQL injection patterns
        dangerous_patterns = [
            r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|EXECUTE)\b)",
            r"(--|\#|\/\*|\*\/)",
            r"(\bOR\b.*=.*)",
            r"(\bAND\b.*=.*)",
            r"(;|\||&)"
        ]
        
        sanitized = text
        for pattern in dangerous_patterns:
            sanitized = re.sub(pattern, "", sanitized, flags=re.IGNORECASE)
        
        return sanitized.strip()
    
    def validate_tool_parameters(self, params: Dict, schema: Dict) -> Tuple[bool, Optional[str]]:
        """Validate tool parameters against schema"""
        if not isinstance(params, dict):
            return False, "Parameters must be a dictionary"
        
        required_fields = schema.get("required", [])
        properties = schema.get("properties", {})
        
        # Check required fields
        missing = [field for field in required_fields if field not in params]
        if missing:
            return False, f"Missing required parameters: {', '.join(missing)}"
        
        # Check parameter types
        for param_name, param_value in params.items():
            if param_name in properties:
                expected_type = properties[param_name].get("type")
                
                type_mapping = {
                    "string": str,
                    "integer": int,
                    "number": (int, float),
                    "boolean": bool,
                    "array": list,
                    "object": dict
                }
                
                expected_python_type = type_mapping.get(expected_type)
                
                if expected_python_type and not isinstance(param_value, expected_python_type):
                    return False, f"Parameter '{param_name}' must be of type {expected_type}"
        
        return True, None
    
    def validate_conversation_id(self, conversation_id: str) -> Tuple[bool, Optional[str]]:
        """Validate conversation ID format"""
        if not conversation_id:
            return True, None  # Optional field
        
        # Check format (UUID-like or alphanumeric with hyphens)
        if not re.match(r'^[a-zA-Z0-9\-_]+$', conversation_id):
            return False, "Invalid conversation ID format"
        
        if len(conversation_id) > 100:
            return False, "Conversation ID too long"
        
        return True, None
    
    def check_rate_limit_headers(self, headers: Dict) -> Tuple[bool, Optional[str]]:
        """Check if rate limit headers indicate throttling needed"""
        # TODO: Integrate with actual rate limiting system
        return True, None
    
    def validate_language_code(self, lang_code: str) -> Tuple[bool, Optional[str]]:
        """Validate language code format"""
        # ISO 639-1 two-letter codes
        if not re.match(r'^[a-z]{2}$', lang_code):
            return False, "Invalid language code format (expected ISO 639-1)"
        
        return True, None
    
    def validate_execution_trace(self, trace: Dict) -> Tuple[bool, Optional[str]]:
        """Validate execution trace structure"""
        required_keys = ["agents_called", "tools_called", "timestamps"]
        
        for key in required_keys:
            if key not in trace:
                return False, f"Execution trace missing required key: {key}"
        
        if not isinstance(trace["agents_called"], list):
            return False, "agents_called must be a list"
        
        if not isinstance(trace["tools_called"], list):
            return False, "tools_called must be a list"
        
        if not isinstance(trace["timestamps"], dict):
            return False, "timestamps must be a dictionary"
        
        return True, None


# Global guardrail validator instance
guardrails = GuardrailValidator()
