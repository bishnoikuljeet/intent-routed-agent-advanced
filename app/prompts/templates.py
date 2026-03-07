"""
Reusable prompt templates for common patterns.
Supports dynamic composition and token optimization.
"""

from typing import Dict, List, Any


class PromptTemplates:
    """Reusable prompt templates and utilities."""
    
    @staticmethod
    def format_tools_compact(tools: List[Dict[str, Any]]) -> str:
        """
        Format tools with descriptions, capabilities, and parameter names for semantic matching.
        Includes input schema parameter names so planner uses exact names instead of inferring.
        
        Args:
            tools: List of tool dictionaries with full schemas
            
        Returns:
            Enhanced tool summary string with capabilities and parameter names
        """
        lines = []
        for tool in tools:
            name = tool.get('name', 'unknown')
            desc = tool.get('description', 'No description')
            
            # Include use cases/capabilities if available
            use_cases = tool.get('use_cases', []) or tool.get('capabilities', [])
            
            # Build tool line with description
            tool_line = f"- {name}: {desc}"
            
            # Add use cases for better semantic matching
            if use_cases:
                use_cases_str = ', '.join(use_cases[:3])  # Limit to 3 for token efficiency
                tool_line += f" | Use for: {use_cases_str}"
            
            # CRITICAL: Add input parameter names from schema so planner uses exact names
            input_schema = tool.get('input_schema', {})
            if input_schema and 'properties' in input_schema:
                properties = input_schema['properties']
                required = input_schema.get('required', [])
                
                param_names = []
                for param_name in properties.keys():
                    if param_name in required:
                        param_names.append(f"{param_name}*")
                    else:
                        param_names.append(param_name)
                
                if param_names:
                    params_str = ', '.join(param_names)
                    tool_line += f" | Params: {params_str}"
            
            lines.append(tool_line)
        
        return '\n'.join(lines)
    
    @staticmethod
    def format_tool_params_compact(tool_schema: Dict[str, Any]) -> str:
        """
        Format tool parameters in compact format.
        
        Args:
            tool_schema: Tool input schema
            
        Returns:
            Compact parameter description
        """
        if not tool_schema or 'properties' not in tool_schema:
            return "No parameters"
        
        params = []
        properties = tool_schema.get('properties', {})
        required = tool_schema.get('required', [])
        
        for param_name, param_info in properties.items():
            param_type = param_info.get('type', 'any')
            is_required = param_name in required
            req_marker = '*' if is_required else ''
            desc = param_info.get('description', '')[:50]
            params.append(f"{param_name}{req_marker} ({param_type}): {desc}")
        
        return '\n'.join(params)
    
    @staticmethod
    def format_results_compact(results: List[Dict[str, Any]]) -> str:
        """
        Format tool results in compact format.
        
        Args:
            results: List of tool execution results
            
        Returns:
            Compact results summary
        """
        lines = []
        for i, result in enumerate(results, 1):
            tool_name = result.get('tool_name', 'unknown')
            if result.get('error'):
                lines.append(f"{i}. {tool_name}: ERROR - {result['error']}")
            else:
                data = result.get('result', {})
                # Summarize result data
                if isinstance(data, dict):
                    key_count = len(data)
                    lines.append(f"{i}. {tool_name}: {key_count} fields")
                else:
                    lines.append(f"{i}. {tool_name}: {str(data)[:50]}")
        
        return '\n'.join(lines)
    
    @staticmethod
    def create_json_schema_instruction(schema_example: str) -> str:
        """
        Create strict JSON output instruction.
        
        Args:
            schema_example: Example JSON structure
            
        Returns:
            Instruction string
        """
        return f"""Output MUST be valid JSON matching this structure:
{schema_example}

Rules:
- Return ONLY valid JSON
- No markdown, no code blocks
- No explanatory text before or after
- All fields required unless marked optional"""
    
    @staticmethod
    def create_reasoning_instruction() -> str:
        """Create instruction for explicit reasoning."""
        return """Before providing your answer:
1. Analyze the information
2. Consider alternatives
3. Evaluate options
4. State your reasoning
5. Provide conclusion"""
    
    @staticmethod
    def create_numeric_output_instruction(min_val: float = 0.0, max_val: float = 1.0) -> str:
        """
        Create instruction for numeric-only output.
        
        Args:
            min_val: Minimum value
            max_val: Maximum value
            
        Returns:
            Instruction string
        """
        return f"""Output MUST be a single number between {min_val} and {max_val}.

Rules:
- Return ONLY the number
- No text, no explanation
- No units or symbols
- Example: 0.85"""
    
    @staticmethod
    def create_single_word_instruction(valid_options: List[str]) -> str:
        """
        Create instruction for single-word output.
        
        Args:
            valid_options: List of valid options
            
        Returns:
            Instruction string
        """
        options_str = ', '.join(valid_options)
        return f"""Output MUST be exactly ONE word from: {options_str}

Rules:
- Return ONLY the word
- No explanation
- No punctuation
- Lowercase only"""
    
    @staticmethod
    def optimize_context(text: str, max_chars: int = 500) -> str:
        """
        Optimize context text for token efficiency.
        
        Args:
            text: Original context text
            max_chars: Maximum characters to keep
            
        Returns:
            Optimized context
        """
        if len(text) <= max_chars:
            return text
        
        # Keep first and last portions
        half = max_chars // 2
        return f"{text[:half]}...[truncated]...{text[-half:]}"
    
    @staticmethod
    def create_llm_message_pair(system_prompt: str, task_prompt: str) -> List[Dict[str, str]]:
        """
        Create properly formatted message pair for LLM.
        
        Args:
            system_prompt: System role prompt
            task_prompt: Task-specific prompt
            
        Returns:
            List of message dictionaries
        """
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": task_prompt}
        ]
    
    @staticmethod
    def extract_json_from_response(response: str) -> str:
        """
        Extract JSON from LLM response that might have extra text.
        
        Args:
            response: Raw LLM response
            
        Returns:
            Extracted JSON string
        """
        # Remove markdown code blocks if present
        response = response.strip()
        
        if response.startswith('```'):
            # Find the JSON content between code blocks
            lines = response.split('\n')
            json_lines = []
            in_code_block = False
            
            for line in lines:
                if line.startswith('```'):
                    in_code_block = not in_code_block
                    continue
                if in_code_block:
                    json_lines.append(line)
            
            response = '\n'.join(json_lines)
        
        # Find JSON object or array
        start_idx = response.find('{')
        if start_idx == -1:
            start_idx = response.find('[')
        
        if start_idx != -1:
            # Find matching closing bracket
            bracket_count = 0
            is_object = response[start_idx] == '{'
            close_char = '}' if is_object else ']'
            
            for i in range(start_idx, len(response)):
                if response[i] in '{[':
                    bracket_count += 1
                elif response[i] in '}]':
                    bracket_count -= 1
                    if bracket_count == 0:
                        return response[start_idx:i+1]
        
        return response.strip()
    
    @staticmethod
    def create_error_handling_instruction() -> str:
        """Create instruction for error handling in LLM responses."""
        return """If you cannot complete the task:
1. Explain why clearly
2. Suggest alternatives
3. Ask for clarification if needed
4. Never make up information"""
    
    @staticmethod
    def create_confidence_instruction() -> str:
        """Create instruction for confidence scoring."""
        return """Include confidence score (0.0-1.0):
- 1.0: Completely certain
- 0.8: Very confident
- 0.6: Moderately confident
- 0.4: Somewhat uncertain
- 0.2: Very uncertain
- 0.0: Cannot determine"""
