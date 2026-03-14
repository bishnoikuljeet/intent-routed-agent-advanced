"""
Strict output schemas for LLM responses.
Ensures consistent, parseable outputs.
"""

from typing import Dict, Any


class LLMSchemas:
    """Strict JSON schemas for LLM outputs."""
    
    CONTEXT_INFERENCE_SCHEMA = {
        "type": "object",
        "required": ["can_handle", "selected_tool", "parameters", "confidence", "reasoning", "needs_clarification"],
        "properties": {
            "can_handle": {
                "type": "boolean",
                "description": "Whether the query can be handled with available tools"
            },
            "selected_tool": {
                "type": ["string", "null"],
                "description": "Name of the selected tool, or null if cannot handle"
            },
            "parameters": {
                "type": "object",
                "description": "Extracted parameters for the tool"
            },
            "confidence": {
                "type": "number",
                "minimum": 0.0,
                "maximum": 1.0,
                "description": "Confidence in the selection (0.0-1.0)"
            },
            "reasoning": {
                "type": "string",
                "description": "Brief explanation of the decision"
            },
            "needs_clarification": {
                "type": "boolean",
                "description": "Whether clarification is needed"
            },
            "clarification_question": {
                "type": "string",
                "description": "Question to ask if clarification needed"
            }
        }
    }
    
    EXECUTION_PLAN_SCHEMA = {
        "type": "object",
        "required": ["reasoning", "steps", "estimated_duration", "requires_parallel"],
        "properties": {
            "reasoning": {
                "type": "string",
                "description": "Brief explanation of the plan"
            },
            "steps": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["step_number", "description", "tool_name", "tool_params", "parallel_group", "depends_on"],
                    "properties": {
                        "step_number": {"type": "integer"},
                        "description": {"type": "string"},
                        "tool_name": {"type": "string"},
                        "tool_params": {"type": "object"},
                        "parallel_group": {"type": "integer"},
                        "depends_on": {"type": "array", "items": {"type": "integer"}}
                    }
                }
            },
            "estimated_duration": {
                "type": "number",
                "description": "Estimated execution time in seconds"
            },
            "requires_parallel": {
                "type": "boolean",
                "description": "Whether parallel execution is needed"
            }
        }
    }
    
    COMPLETENESS_CHECK_SCHEMA = {
        "type": "object",
        "required": ["is_complete", "confidence", "missing_info", "reasoning"],
        "properties": {
            "is_complete": {
                "type": "boolean",
                "description": "Whether the query is complete"
            },
            "confidence": {
                "type": "number",
                "minimum": 0.0,
                "maximum": 1.0,
                "description": "Confidence in the assessment"
            },
            "missing_info": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of missing information items"
            },
            "reasoning": {
                "type": "string",
                "description": "Explanation of the assessment"
            },
            "suggested_clarification": {
                "type": "string",
                "description": "Question to ask if incomplete"
            }
        }
    }
    
    TOOL_CAPABILITY_SCHEMA = {
        "type": "object",
        "required": ["can_handle", "confidence", "reasoning"],
        "properties": {
            "can_handle": {
                "type": "boolean",
                "description": "Whether the tool can handle the query"
            },
            "confidence": {
                "type": "number",
                "minimum": 0.0,
                "maximum": 1.0,
                "description": "Confidence in the assessment"
            },
            "reasoning": {
                "type": "string",
                "description": "Explanation of the decision"
            }
        }
    }
    
    PARAMETER_EXTRACTION_SCHEMA = {
        "type": "object",
        "required": ["extracted_params", "confidence", "missing_required", "reasoning"],
        "properties": {
            "extracted_params": {
                "type": "object",
                "description": "Extracted parameter values"
            },
            "confidence": {
                "type": "number",
                "minimum": 0.0,
                "maximum": 1.0,
                "description": "Confidence in extraction"
            },
            "missing_required": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of missing required parameters"
            },
            "reasoning": {
                "type": "string",
                "description": "Explanation of extraction"
            }
        }
    }
    
    @staticmethod
    def get_schema(schema_name: str) -> Dict[str, Any]:
        """
        Get a schema by name.
        
        Args:
            schema_name: Name of the schema
            
        Returns:
            Schema dictionary
        """
        schemas = {
            'context_inference': LLMSchemas.CONTEXT_INFERENCE_SCHEMA,
            'execution_plan': LLMSchemas.EXECUTION_PLAN_SCHEMA,
            'completeness_check': LLMSchemas.COMPLETENESS_CHECK_SCHEMA,
            'tool_capability': LLMSchemas.TOOL_CAPABILITY_SCHEMA,
            'parameter_extraction': LLMSchemas.PARAMETER_EXTRACTION_SCHEMA
        }
        
        return schemas.get(schema_name, {})
    
    @staticmethod
    def get_example_output(schema_name: str) -> str:
        """
        Get example output for a schema.
        
        Args:
            schema_name: Name of the schema
            
        Returns:
            Example JSON string
        """
        examples = {
            'context_inference': '''{
    "can_handle": true,
    "selected_tool": "compare_values",
    "parameters": {"value1": null, "value2": null},
    "confidence": 0.9,
    "reasoning": "Query asks to compare two numbers but values not provided",
    "needs_clarification": true,
    "clarification_question": "What are the two values you'd like to compare?"
}''',
            'execution_plan': '''{
    "reasoning": "Need to get metric then calculate difference",
    "steps": [
        {
            "step_number": 1,
            "description": "Get current metric",
            "tool_name": "get_metric",
            "tool_params": {"metric": "latency"},
            "parallel_group": 1,
            "depends_on": []
        }
    ],
    "estimated_duration": 1.5,
    "requires_parallel": false
}''',
            'completeness_check': '''{
    "is_complete": false,
    "confidence": 0.85,
    "missing_info": ["service_name"],
    "reasoning": "Query lacks specific service identifier",
    "suggested_clarification": "Which service would you like to check?"
}''',
            'tool_capability': '''{
    "can_handle": true,
    "confidence": 0.9,
    "reasoning": "Tool description matches query intent"
}''',
            'parameter_extraction': '''{
    "extracted_params": {"service_name": "payment-service", "metric": "latency"},
    "confidence": 0.95,
    "missing_required": [],
    "reasoning": "Service name and metric clearly stated in query"
}'''
        }
        
        return examples.get(schema_name, '{}')
