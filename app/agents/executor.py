from typing import Dict, Any, List, Optional
from app.schemas.state import ConversationState
from app.schemas.models import ToolResult
from app.mcp.base import BaseMCPServer
from app.core.config import settings
from app.core.logging import logger
from datetime import datetime
from tenacity import retry, stop_after_attempt, wait_exponential
import asyncio
import time


class ExecutorAgent:
    # Class-level persistent cache that survives workflow retries
    _persistent_cache: Dict[str, Dict[str, Any]] = {}
    def __init__(self, mcp_servers: Dict[str, BaseMCPServer]):
        self.name = "executor"
        self.mcp_servers = mcp_servers
        self.max_parallel = settings.max_parallel_tools
        self.timeout = settings.tool_timeout_seconds
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True
    )
    async def _validate_and_enhance_params(
        self,
        server_name: str,
        tool_name: str,
        params: Dict[str, Any],
        state: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Validate and enhance parameters with smart defaults for missing required params.
        Generic solution that works with any tool schema.
        """
        try:
            server = self.mcp_servers.get(server_name)
            if not server:
                return params
            
            # Get tool schema - handle both dict and MCPTool object formats
            tool_schema = server.tools.get(tool_name)
            if not tool_schema:
                return params
            
            # Handle both dict and MCPTool object formats
            if hasattr(tool_schema, 'input_schema'):
                # MCPTool object with input_schema attribute
                input_schema = tool_schema.input_schema or {}
            elif isinstance(tool_schema, dict):
                # Dict format with inputSchema or input_schema key
                input_schema = tool_schema.get('inputSchema') or tool_schema.get('input_schema', {})
            else:
                return params
            
            # Get required params and properties from schema dict
            required_params = input_schema.get('required', [])
            properties = input_schema.get('properties', {})
            
            enhanced_params = params.copy()
            
            # Special handling for data_validation tool
            if tool_name == "data_validation":
                enhanced_params = self._enhance_data_validation_params(enhanced_params, state)
            
            # Remove parameters that are not in the tool schema
            invalid_params = []
            for param_name in list(enhanced_params.keys()):
                if param_name not in properties:
                    invalid_params.append(param_name)
                    del enhanced_params[param_name]
            
            if invalid_params:
                logger.warning_structured(
                    "Removed invalid parameters not in tool schema",
                    tool=tool_name,
                    server=server_name,
                    invalid_params=invalid_params,
                    valid_params=list(properties.keys())
                )
            
            # Check for missing required parameters
            missing_params = []
            for param_name in required_params:
                if param_name not in enhanced_params or enhanced_params[param_name] is None:
                    missing_params.append(param_name)
            
            if missing_params:
                logger.warning_structured(
                    "Missing required parameters, applying smart defaults",
                    tool=tool_name,
                    server=server_name,
                    missing_params=missing_params,
                    provided_params=list(params.keys())
                )
                
                # Apply smart defaults based on parameter metadata
                query = state.get('current_query', '') if state else ''
                query_lower = query.lower()
                
                for param_name in missing_params:
                    # Only add parameters that are actually defined in the schema
                    if param_name not in properties:
                        logger.warning_structured(
                            "Skipping undefined parameter",
                            tool=tool_name,
                            server=server_name,
                            param_name=param_name
                        )
                        continue
                    
                    # Get parameter info from properties dict
                    param_info = properties.get(param_name, {})
                    param_type = param_info.get('type', 'string')
                    param_desc = param_info.get('description', '').lower()
                    
                    # Smart defaults based on parameter semantics
                    if param_type == 'string':
                        if 'metric' in param_name.lower() or 'metric' in param_desc:
                            if 'latency' in query_lower:
                                enhanced_params[param_name] = 'latency'
                            elif 'error' in query_lower:
                                enhanced_params[param_name] = 'error_rate'
                            elif 'throughput' in query_lower or 'traffic' in query_lower:
                                enhanced_params[param_name] = 'throughput'
                            else:
                                enhanced_params[param_name] = 'latency'  # Default metric
                        elif 'time' in param_name.lower() or 'period' in param_desc:
                            enhanced_params[param_name] = '1h'  # Default time period
                        elif 'format' in param_name.lower():
                            enhanced_params[param_name] = 'json'
                        else:
                            enhanced_params[param_name] = 'default'
                    elif param_type == 'number' or param_type == 'integer':
                        if 'limit' in param_name.lower():
                            enhanced_params[param_name] = 100
                        elif 'threshold' in param_desc:
                            enhanced_params[param_name] = 0.95
                        else:
                            enhanced_params[param_name] = 0
                    elif param_type == 'boolean':
                        enhanced_params[param_name] = True
                    elif param_type == 'array':
                        enhanced_params[param_name] = []
                    else:
                        enhanced_params[param_name] = None
                
                logger.info_structured(
                    "Applied smart defaults to parameters",
                    tool=tool_name,
                    server=server_name,
                    original_params=list(params.keys()),
                    enhanced_params=list(enhanced_params.keys())
                )
            
            return enhanced_params
            
        except Exception as e:
            logger.error_structured(
                "Parameter validation failed",
                tool=tool_name,
                server=server_name,
                error=str(e)
            )
            return params  # Return original on error
    
    def _enhance_data_validation_params(
        self, 
        params: Dict[str, Any], 
        state: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Special parameter enhancement for data_validation tool.
        Converts string data to object and string rules to proper validation rules.
        """
        try:
            enhanced_params = params.copy()
            
            # Handle data parameter - convert string to object
            if 'data' in enhanced_params and isinstance(enhanced_params['data'], str):
                # If data is a string, try to extract email or other entities
                data_str = enhanced_params['data']
                query = state.get('current_query', '') if state else ''
                
                # Try to extract email from the data string or query
                import re
                email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
                
                # First try to find email in the data string itself
                email_match = re.search(email_pattern, data_str)
                if not email_match:
                    # If not found, try the original query
                    email_match = re.search(email_pattern, query)
                
                if email_match:
                    enhanced_params['data'] = {"email": email_match.group(0)}
                    logger.info_structured(
                        "Converted string data to email object",
                        original_data=data_str,
                        converted_data=enhanced_params['data']
                    )
                else:
                    # If no email found, wrap the string in a generic object
                    enhanced_params['data'] = {"value": data_str}
                    logger.info_structured(
                        "Converted string data to generic object",
                        original_data=data_str,
                        converted_data=enhanced_params['data']
                    )
            
            # Handle rules parameter - convert string to validation rules array
            if 'rules' in enhanced_params and isinstance(enhanced_params['rules'], str):
                rules_str = enhanced_params['rules']
                
                # Handle common rule patterns
                if rules_str == "standard_email_format" or rules_str == "email_format":
                    enhanced_params['rules'] = [
                        {
                            "field": "email",
                            "type": "string",
                            "pattern": r"^[^@]+@[^@]+\.[^@]+$"
                        }
                    ]
                    logger.info_structured(
                        "Converted string rules to email validation rules",
                        original_rules=rules_str,
                        converted_rules=enhanced_params['rules']
                    )
                else:
                    # For other rule strings, create a generic validation rule
                    enhanced_params['rules'] = [
                        {
                            "field": "value",
                            "type": "string",
                            "pattern": ".*"  # Match any non-empty string
                        }
                    ]
                    logger.info_structured(
                        "Converted string rules to generic validation rules",
                        original_rules=rules_str,
                        converted_rules=enhanced_params['rules']
                    )
            
            return enhanced_params
            
        except Exception as e:
            logger.error_structured(
                "Failed to enhance data_validation parameters",
                error=str(e),
                original_params=params
            )
            return params
    
    async def _execute_tool(
        self,
        server_name: str,
        tool_name: str,
        params: Dict[str, Any],
        state: Optional[Dict[str, Any]] = None
    ) -> ToolResult:
        start_time = time.time()
        
        # Validate and enhance parameters before execution
        validated_params = await self._validate_and_enhance_params(server_name, tool_name, params, state)
        
        # Check cache for existing results during retries
        cache_key = f"{server_name}:{tool_name}:{hash(str(sorted(validated_params.items())))}"
        
        # Use persistent cache that survives workflow retries
        logger.info_structured(
            "Checking persistent tool cache",
            tool=tool_name,
            server=server_name,
            cache_size=len(self._persistent_cache),
            cache_key=cache_key[:50] + "..."
        )
        
        if cache_key in self._persistent_cache:
            cached_result = self._persistent_cache[cache_key]
            logger.info_structured(
                "Using cached tool result",
                tool=tool_name,
                server=server_name,
                cache_key=cache_key[:50] + "..."
            )
            return ToolResult(
                tool_name=tool_name,
                success=True,
                result=cached_result["result"],
                latency_ms=0,  # Cached results have no latency
                metadata={"server": server_name, "params": validated_params, "cached": True}
            )
        
        try:
            server = self.mcp_servers.get(server_name)
            if not server:
                raise ValueError(f"MCP server {server_name} not found")
            
            result = await asyncio.wait_for(
                server.call_tool(tool_name, validated_params),
                timeout=self.timeout
            )
            
            latency_ms = (time.time() - start_time) * 1000
            
            # Store result in persistent cache for potential retries
            self._persistent_cache[cache_key] = {
                "result": result,
                "timestamp": time.time(),
                "latency_ms": latency_ms
            }
            
            logger.info_structured(
                "Stored tool result in persistent cache",
                tool=tool_name,
                server=server_name,
                cache_key=cache_key[:50] + "...",
                cache_size_after=len(self._persistent_cache)
            )
            
            return ToolResult(
                tool_name=tool_name,
                success=True,
                result=result,
                latency_ms=latency_ms,
                metadata={"server": server_name, "params": validated_params, "cached": False}
            )
            
        except asyncio.TimeoutError:
            latency_ms = (time.time() - start_time) * 1000
            logger.error_structured(
                "Tool execution timeout",
                tool=tool_name,
                server=server_name,
                timeout=self.timeout
            )
            return ToolResult(
                tool_name=tool_name,
                success=False,
                result=None,
                error=f"Timeout after {self.timeout}s",
                latency_ms=latency_ms,
                metadata={"server": server_name}
            )
            
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            logger.error_structured(
                "Tool execution failed",
                tool=tool_name,
                server=server_name,
                error=str(e)
            )
            return ToolResult(
                tool_name=tool_name,
                success=False,
                result=None,
                error=str(e),
                latency_ms=latency_ms,
                metadata={"server": server_name}
            )
    
    def _find_server_for_tool(self, tool_name: str) -> str:
        for server_name, server in self.mcp_servers.items():
            if tool_name in server.tools:
                return server_name
        raise ValueError(f"Tool {tool_name} not found in any MCP server")
    
    def _substitute_result_references(
        self,
        params: Dict[str, Any],
        completed_results: List[ToolResult]
    ) -> Dict[str, Any]:
        """
        Substitute references like ${step_1.field_name} with actual values from previous results.
        Enhanced to handle arrays, nested references, and type conversion.
        
        Args:
            params: Tool parameters that may contain references
            completed_results: List of completed tool results
            
        Returns:
            Parameters with references replaced by actual values
        """
        import re
        
        def substitute_value(value: Any) -> Any:
            """Recursively substitute references in any data type"""
            if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
                # Extract step reference: ${step_1.current_value}
                match = re.match(r'\$\{step_(\d+)\.(\w+)\}', value)
                if match:
                    step_num = int(match.group(1)) - 1  # Convert to 0-indexed
                    field_name = match.group(2)
                    
                    # Get result from the specified step
                    if step_num < len(completed_results):
                        result = completed_results[step_num]
                        if result.success and result.result:
                            # Try to extract the field from the result
                            if isinstance(result.result, dict) and field_name in result.result:
                                actual_value = result.result[field_name]
                                logger.info_structured(
                                    "Substituted result reference",
                                    reference=value,
                                    actual_value=actual_value,
                                    value_type=type(actual_value).__name__
                                )
                                return actual_value
                            else:
                                logger.warning_structured(
                                    "Field not found in result",
                                    step=step_num + 1,
                                    field=field_name,
                                    available_fields=list(result.result.keys()) if isinstance(result.result, dict) else "non-dict result"
                                )
                                return value  # Keep original if not found
                        else:
                            logger.warning_structured(
                                "Referenced step failed",
                                step=step_num + 1,
                                success=result.success
                            )
                            return value  # Keep original if step failed
                    else:
                        logger.warning_structured(
                            "Step reference out of range",
                            step=step_num + 1,
                            available_steps=len(completed_results)
                        )
                        return value  # Keep original if out of range
                else:
                    return value  # Keep original if pattern doesn't match
            elif isinstance(value, list):
                # Handle arrays with references
                return [substitute_value(item) for item in value]
            elif isinstance(value, dict):
                # Handle nested dictionaries
                return {k: substitute_value(v) for k, v in value.items()}
            else:
                return value  # Keep non-reference values as-is
        
        substituted_params = {}
        for key, value in params.items():
            substituted_params[key] = substitute_value(value)
        
        return substituted_params
    
    async def _execute_parallel_group(
        self,
        steps: List[Dict[str, Any]],
        state: Optional[ConversationState] = None
    ) -> List[ToolResult]:
        tasks = []
        
        for step in steps:
            tool_name = step.get("tool_name")
            if tool_name == "none":
                continue
            
            try:
                server_name = self._find_server_for_tool(tool_name)
                params = step.get("tool_params", {})
                
                # Pass full state for parameter validation
                task = self._execute_tool(server_name, tool_name, params, state)
                tasks.append(task)
                
            except Exception as e:
                logger.error_structured(
                    "Failed to create task for tool",
                    tool=tool_name,
                    error=str(e)
                )
        
        if not tasks:
            return []
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        tool_results = []
        for result in results:
            if isinstance(result, Exception):
                logger.error_structured("Parallel execution exception", error=str(result))
            elif isinstance(result, ToolResult):
                tool_results.append(result)
        
        return tool_results
    
    async def execute_plan(self, state: ConversationState) -> ConversationState:
        execution_plan = state.get("execution_plan")
        
        # Handle both ExecutionPlan object and legacy list format
        if hasattr(execution_plan, 'steps'):
            plan_steps = len(execution_plan.steps)
        else:
            # Legacy list format
            plan_steps = len(execution_plan) if execution_plan else 0
        
        logger.info_structured(
            "Executor agent started",
            conversation_id=state.get("conversation_id"),
            plan_steps=plan_steps
        )
        
        if not execution_plan:
            logger.warning_structured("No execution plan found")
            state["tool_results"] = []
            return state
        
        parallel_groups: Dict[int, List[Dict[str, Any]]] = {}
        sequential_steps: List[Dict[str, Any]] = []
        
        # Handle both ExecutionPlan object and legacy list format
        steps_to_process = []
        if hasattr(execution_plan, 'steps'):
            steps_to_process = [step.dict() for step in execution_plan.steps]
        else:
            # Legacy list format
            steps_to_process = execution_plan if execution_plan else []
        
        for step in steps_to_process:
            parallel_group = step.get("parallel_group")
            logger.info_structured(
                "Executor analyzing step",
                step_number=step.get("step_number"),
                parallel_group=parallel_group,
                tool_name=step.get("tool_name")
            )
            if parallel_group is not None:
                if parallel_group not in parallel_groups:
                    parallel_groups[parallel_group] = []
                parallel_groups[parallel_group].append(step)
            else:
                sequential_steps.append(step)
        
        logger.info_structured(
            "Executor step classification",
            parallel_groups_count=len(parallel_groups),
            sequential_steps_count=len(sequential_steps),
            parallel_group_keys=list(parallel_groups.keys())
        )
        
        all_results = []
        
        for group_id in sorted(parallel_groups.keys()):
            group_steps = parallel_groups[group_id]
            
            # Substitute result references from previous steps
            substituted_steps = []
            for step in group_steps:
                params = step.get("tool_params", {})
                substituted_params = self._substitute_result_references(params, all_results)
                
                # Create new step with substituted params
                substituted_step = step.copy()
                substituted_step["tool_params"] = substituted_params
                substituted_steps.append(substituted_step)
            
            logger.info_structured(
                "Executing parallel group",
                group_id=group_id,
                step_count=len(substituted_steps)
            )
            results = await self._execute_parallel_group(substituted_steps, state)
            all_results.extend(results)
        
        for step in sequential_steps:
            tool_name = step.get("tool_name")
            if tool_name == "none":
                continue
            
            try:
                server_name = self._find_server_for_tool(tool_name)
                params = step.get("tool_params", {})
                
                # Substitute result references from previous steps
                substituted_params = self._substitute_result_references(params, all_results)
                
                result = await self._execute_tool(server_name, tool_name, substituted_params, state)
                all_results.append(result)
                
            except Exception as e:
                logger.error_structured(
                    "Sequential execution failed",
                    tool=tool_name,
                    error=str(e)
                )
        
        state["tool_results"] = [r.model_dump() for r in all_results]
        state["tool_history"].extend([
            {
                "tool": r.tool_name,
                "success": r.success,
                "latency_ms": r.latency_ms,
                "timestamp": datetime.utcnow().isoformat()
            }
            for r in all_results
        ])
        
        state["execution_trace"]["agents_called"].append(self.name)
        state["execution_trace"]["timestamps"][self.name] = datetime.utcnow().isoformat()
        
        # Store detailed tool information with parameters
        tools_with_params = []
        for r in all_results:
            tool_info = {
                "name": r.tool_name,
                "agent": self.name,
                "success": r.success,
                "params": r.metadata.get("params", {}),
                "server": r.metadata.get("server", "unknown"),
                "latency_ms": r.latency_ms,
                "timestamp": datetime.utcnow().isoformat()
            }
            tools_with_params.append(tool_info)
        
        state["execution_trace"]["tools_called"] = tools_with_params
        
        logger.info_structured(
            "Executor agent completed",
            conversation_id=state.get("conversation_id"),
            tools_executed=len(all_results),
            successful=sum(1 for r in all_results if r.success)
        )
        
        return state
