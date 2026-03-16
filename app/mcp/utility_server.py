from app.mcp.base import BaseMCPServer, MCPTool, MCPResource, MCPPrompt
from typing import Dict, Any, List, Optional, Union
from app.core.logging import logger
import statistics
import json
import re
from datetime import datetime, timezone
import time


def handle_default_params(params: Dict[str, Any], defaults: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generic helper to handle null parameters by applying defaults.
    
    Args:
        params: Input parameters that may contain null values
        defaults: Default values for null parameters
        
    Returns:
        Parameters with null values replaced by defaults
    """
    result = params.copy()
    for key, default_value in defaults.items():
        if result.get(key) is None:
            result[key] = default_value
    return result


class UtilityMCPServer(BaseMCPServer):
    def __init__(self):
        super().__init__("utility")
    
    def _initialize(self):
        self.register_tool(MCPTool(
            name="compare_values",
            description="Compare two numeric values",
            input_schema={
                "type": "object",
                "properties": {
                    "value1": {"type": "number"},
                    "value2": {"type": "number"},
                    "comparison_type": {"type": "string", "enum": ["greater", "less", "equal", "not_equal"]}
                },
                "required": ["value1", "value2"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "result": {"type": "boolean"},
                    "difference": {"type": "number"},
                    "ratio": {"type": "number"}
                }
            },
            handler=self._compare_values
        ))
        
        self.register_tool(MCPTool(
            name="percentage_difference",
            description="Calculate percentage difference between two values",
            input_schema={
                "type": "object",
                "properties": {
                    "value1": {"type": "number"},
                    "value2": {"type": "number"}
                },
                "required": ["value1", "value2"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "percentage_diff": {"type": "number"},
                    "absolute_diff": {"type": "number"},
                    "direction": {"type": "string"}
                }
            },
            handler=self._percentage_difference
        ))
        
        self.register_tool(MCPTool(
            name="time_range_calculator",
            description="Calculate time ranges and durations",
            input_schema={
                "type": "object",
                "properties": {
                    "start_time": {"type": "string"},
                    "end_time": {"type": "string"},
                    "unit": {"type": "string", "enum": ["seconds", "minutes", "hours", "days"]}
                },
                "required": ["start_time", "end_time"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "duration": {"type": "number"},
                    "unit": {"type": "string"}
                }
            },
            handler=self._time_range_calculator
        ))
        
        self.register_tool(MCPTool(
            name="statistics_summary",
            description="Calculate statistical summary of a dataset",
            input_schema={
                "type": "object",
                "properties": {
                    "values": {"type": "array", "items": {"type": "number"}}
                },
                "required": ["values"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "mean": {"type": "number"},
                    "median": {"type": "number"},
                    "std_dev": {"type": "number"},
                    "min": {"type": "number"},
                    "max": {"type": "number"}
                }
            },
            handler=self._statistics_summary
        ))
        
        # New Advanced Tools
        self.register_tool(MCPTool(
            name="trend_analysis",
            description="Analyze trends and forecast future values",
            input_schema={
                "type": "object",
                "properties": {
                    "values": {"type": "array", "items": {"type": "number"}},
                    "forecast_periods": {"type": "integer", "default": 5},
                    "confidence_level": {"type": "number", "default": 0.95}
                },
                "required": ["values"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "trend": {"type": "string"},
                    "slope": {"type": "number"},
                    "forecast": {"type": "array"},
                    "confidence_interval": {"type": "object"}
                }
            },
            handler=self._trend_analysis
        ))
        
        self.register_tool(MCPTool(
            name="anomaly_detection",
            description="Detect anomalies in a dataset using statistical methods",
            input_schema={
                "type": "object",
                "properties": {
                    "values": {"type": "array", "items": {"type": "number"}},
                    "sensitivity": {"type": "number", "default": 2.0},
                    "method": {"type": "string", "enum": ["zscore", "iqr", "mad"], "default": "zscore"}
                },
                "required": ["values"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "anomalies": {"type": "array"},
                    "anomaly_count": {"type": "integer"},
                    "anomaly_percentage": {"type": "number"}
                }
            },
            handler=self._anomaly_detection
        ))
        
        self.register_tool(MCPTool(
            name="data_validation",
            description="Validate data against schema and business rules",
            input_schema={
                "type": "object",
                "properties": {
                    "data": {"type": "object"},
                    "rules": {"type": "array"},
                    "strict_mode": {"type": "boolean", "default": False}
                },
                "required": ["data", "rules"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "is_valid": {"type": "boolean"},
                    "errors": {"type": "array"},
                    "warnings": {"type": "array"}
                }
            },
            handler=self._data_validation
        ))
        
        self.register_tool(MCPTool(
            name="json_yaml_parser",
            description="Parse and convert between JSON and YAML formats",
            input_schema={
                "type": "object",
                "properties": {
                    "content": {"type": "string"},
                    "input_format": {"type": "string", "enum": ["json", "yaml"]},
                    "output_format": {"type": "string", "enum": ["json", "yaml"]},
                    "validate": {"type": "boolean", "default": True}
                },
                "required": ["content", "input_format", "output_format"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "parsed_data": {"type": "object"},
                    "converted_content": {"type": "string"},
                    "is_valid": {"type": "boolean"}
                }
            },
            handler=self._json_yaml_parser
        ))
        
        self.register_tool(MCPTool(
            name="get_current_datetime",
            description="Get the current date and time",
            input_schema={
                "type": "object",
                "properties": {
                    "timezone": {
                        "type": "string",
                        "description": "Timezone (e.g., 'UTC', 'America/New_York', 'Asia/Kolkata')",
                        "default": "UTC"
                    },
                    "format": {
                        "type": "string",
                        "description": "Output format: 'iso', 'readable', 'timestamp'",
                        "enum": ["iso", "readable", "timestamp"],
                        "default": "iso"
                    }
                },
                "required": []
            },
            output_schema={
                "type": "object",
                "properties": {
                    "datetime": {"type": "string"},
                    "timezone": {"type": "string"},
                    "unix_timestamp": {"type": "number"},
                    "components": {
                        "type": "object",
                        "properties": {
                            "year": {"type": "integer"},
                            "month": {"type": "integer"},
                            "day": {"type": "integer"},
                            "hour": {"type": "integer"},
                            "minute": {"type": "integer"},
                            "second": {"type": "integer"},
                            "weekday": {"type": "string"}
                        }
                    }
                }
            },
            handler=self._get_current_datetime
        ))
    
    async def _compare_values(
        self,
        value1: float,
        value2: float,
        comparison_type: str = "greater"
    ) -> Dict[str, Any]:
        comparisons = {
            "greater": value1 > value2,
            "less": value1 < value2,
            "equal": value1 == value2,
            "not_equal": value1 != value2
        }
        
        result = comparisons.get(comparison_type, False)
        difference = value1 - value2
        ratio = value1 / value2 if value2 != 0 else float('inf')
        
        return {
            "result": result,
            "difference": round(difference, 2),
            "ratio": round(ratio, 2),
            "comparison_type": comparison_type
        }
    
    async def _percentage_difference(self, value1: float, value2: float) -> Dict[str, Any]:
        absolute_diff = abs(value1 - value2)
        
        if value2 == 0:
            percentage_diff = 100.0 if value1 != 0 else 0.0
        else:
            percentage_diff = (absolute_diff / abs(value2)) * 100
        
        direction = "increase" if value1 > value2 else "decrease" if value1 < value2 else "no_change"
        
        return {
            "percentage_diff": round(percentage_diff, 2),
            "absolute_diff": round(absolute_diff, 2),
            "direction": direction,
            "value1": value1,
            "value2": value2
        }
    
    async def _time_range_calculator(
        self,
        start_time: str,
        end_time: str,
        unit: str = "minutes"
    ) -> Dict[str, Any]:
        from datetime import datetime
        
        try:
            start = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            end = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
            
            duration_seconds = (end - start).total_seconds()
            
            conversions = {
                "seconds": 1,
                "minutes": 60,
                "hours": 3600,
                "days": 86400
            }
            
            duration = duration_seconds / conversions.get(unit, 60)
            
            return {
                "duration": round(duration, 2),
                "unit": unit,
                "start_time": start_time,
                "end_time": end_time
            }
        except Exception as e:
            return {
                "duration": 0,
                "unit": unit,
                "error": str(e)
            }
    
    async def _statistics_summary(self, values: List[float]) -> Dict[str, Any]:
        if not values:
            return {
                "mean": 0,
                "median": 0,
                "std_dev": 0,
                "min": 0,
                "max": 0,
                "count": 0
            }
        
        return {
            "mean": round(statistics.mean(values), 2),
            "median": round(statistics.median(values), 2),
            "std_dev": round(statistics.stdev(values), 2) if len(values) > 1 else 0,
            "min": round(min(values), 2),
            "max": round(max(values), 2),
            "count": len(values)
        }
    
    async def _trend_analysis(
        self,
        values: List[float],
        forecast_periods: int = 5,
        confidence_level: float = 0.95
    ) -> Dict[str, Any]:
        if len(values) < 2:
            return {
                "trend": "insufficient_data",
                "slope": 0,
                "forecast": [],
                "confidence_interval": {}
            }
        
        # Simple linear regression
        n = len(values)
        x = list(range(n))
        
        mean_x = sum(x) / n
        mean_y = sum(values) / n
        
        numerator = sum((x[i] - mean_x) * (values[i] - mean_y) for i in range(n))
        denominator = sum((x[i] - mean_x) ** 2 for i in range(n))
        
        slope = numerator / denominator if denominator != 0 else 0
        intercept = mean_y - slope * mean_x
        
        # Determine trend
        if abs(slope) < 0.01:
            trend = "stable"
        elif slope > 0:
            trend = "increasing"
        else:
            trend = "decreasing"
        
        # Forecast
        forecast = []
        for i in range(forecast_periods):
            forecast_x = n + i
            forecast_y = slope * forecast_x + intercept
            forecast.append(round(forecast_y, 2))
        
        # Simple confidence interval (using std dev)
        residuals = [values[i] - (slope * i + intercept) for i in range(n)]
        std_error = statistics.stdev(residuals) if len(residuals) > 1 else 0
        margin = 1.96 * std_error  # 95% confidence
        
        return {
            "trend": trend,
            "slope": round(slope, 4),
            "intercept": round(intercept, 2),
            "forecast": forecast,
            "confidence_interval": {
                "lower": [round(f - margin, 2) for f in forecast],
                "upper": [round(f + margin, 2) for f in forecast]
            },
            "r_squared": round(1 - (sum(r**2 for r in residuals) / sum((v - mean_y)**2 for v in values)), 3) if values else 0
        }
    
    async def _anomaly_detection(
        self,
        values: List[float],
        sensitivity: float = 2.0,
        method: str = "zscore"
    ) -> Dict[str, Any]:
        # Handle null values by using defaults
        if sensitivity is None:
            sensitivity = 2.0
        if method is None:
            method = "zscore"
            
        if len(values) < 3:
            return {
                "anomalies": [],
                "anomaly_count": 0,
                "anomaly_percentage": 0,
                "method": method,
                "sensitivity": sensitivity
            }
        
        anomalies = []
        
        if method == "zscore":
            mean = statistics.mean(values)
            std_dev = statistics.stdev(values)
            
            for i, value in enumerate(values):
                z_score = abs((value - mean) / std_dev) if std_dev > 0 else 0
                if z_score > sensitivity:
                    anomalies.append({
                        "index": i,
                        "value": value,
                        "z_score": round(z_score, 2),
                        "deviation": round(value - mean, 2)
                    })
        
        elif method == "iqr":
            sorted_values = sorted(values)
            q1 = sorted_values[len(sorted_values) // 4]
            q3 = sorted_values[3 * len(sorted_values) // 4]
            iqr = q3 - q1
            
            lower_bound = q1 - sensitivity * iqr
            upper_bound = q3 + sensitivity * iqr
            
            for i, value in enumerate(values):
                if value < lower_bound or value > upper_bound:
                    anomalies.append({
                        "index": i,
                        "value": value,
                        "lower_bound": round(lower_bound, 2),
                        "upper_bound": round(upper_bound, 2)
                    })
        
        elif method == "mad":
            median = statistics.median(values)
            deviations = [abs(v - median) for v in values]
            mad = statistics.median(deviations)
            
            for i, value in enumerate(values):
                modified_z = abs((value - median) / mad) if mad > 0 else 0
                if modified_z > sensitivity:
                    anomalies.append({
                        "index": i,
                        "value": value,
                        "modified_z_score": round(modified_z, 2)
                    })
        
        anomaly_percentage = (len(anomalies) / len(values)) * 100 if values else 0
        
        return {
            "anomalies": anomalies,
            "anomaly_count": len(anomalies),
            "anomaly_percentage": round(anomaly_percentage, 2),
            "method": method,
            "sensitivity": sensitivity
        }
    
    async def _data_validation(
        self,
        data: Dict[str, Any],
        rules: List[Dict[str, Any]],
        strict_mode: bool = False
    ) -> Dict[str, Any]:
        # Handle null values by using defaults
        if rules is None:
            rules = []
        if strict_mode is None:
            strict_mode = False
            
        errors = []
        warnings = []
        
        for rule in rules:
            field = rule.get("field")
            rule_type = rule.get("type")
            required = rule.get("required", False)
            
            value = data.get(field)
            
            # Check required fields
            if required and value is None:
                errors.append({
                    "field": field,
                    "error": "required_field_missing",
                    "message": f"Field '{field}' is required"
                })
                continue
            
            if value is None:
                continue
            
            # Type validation
            if rule_type == "number":
                if not isinstance(value, (int, float)):
                    errors.append({
                        "field": field,
                        "error": "invalid_type",
                        "message": f"Field '{field}' must be a number"
                    })
                else:
                    # Range validation
                    min_val = rule.get("min")
                    max_val = rule.get("max")
                    
                    if min_val is not None and value < min_val:
                        errors.append({
                            "field": field,
                            "error": "value_too_low",
                            "message": f"Field '{field}' must be >= {min_val}"
                        })
                    
                    if max_val is not None and value > max_val:
                        errors.append({
                            "field": field,
                            "error": "value_too_high",
                            "message": f"Field '{field}' must be <= {max_val}"
                        })
            
            elif rule_type == "string":
                if not isinstance(value, str):
                    errors.append({
                        "field": field,
                        "error": "invalid_type",
                        "message": f"Field '{field}' must be a string"
                    })
                else:
                    # Pattern validation
                    pattern = rule.get("pattern")
                    if pattern and not re.match(pattern, value):
                        warnings.append({
                            "field": field,
                            "warning": "pattern_mismatch",
                            "message": f"Field '{field}' does not match expected pattern"
                        })
        
        is_valid = len(errors) == 0 if strict_mode else len(errors) == 0 and len(warnings) == 0
        
        return {
            "is_valid": is_valid,
            "errors": errors,
            "warnings": warnings,
            "error_count": len(errors),
            "warning_count": len(warnings)
        }
    
    async def _json_yaml_parser(
        self,
        content: str,
        input_format: str,
        output_format: str,
        validate: bool = True
    ) -> Dict[str, Any]:
        try:
            # Parse input
            if input_format == "json":
                parsed_data = json.loads(content)
            else:  # yaml
                # Demo: YAML parsing requires PyYAML library in production
                parsed_data = {"note": "YAML parsing requires PyYAML library"}
            
            # Convert to output format
            if output_format == "json":
                converted_content = json.dumps(parsed_data, indent=2)
            else:  # yaml
                # Demo: YAML output requires PyYAML library in production
                converted_content = "# YAML output requires PyYAML library\n"
                converted_content += json.dumps(parsed_data, indent=2)
            
            return {
                "parsed_data": parsed_data,
                "converted_content": converted_content,
                "is_valid": True,
                "input_format": input_format,
                "output_format": output_format
            }
        
        except json.JSONDecodeError as e:
            return {
                "parsed_data": {},
                "converted_content": "",
                "is_valid": False,
                "error": str(e)
            }
    
    async def _get_current_datetime(
        self,
        timezone: str = "UTC",
        format: str = "iso"
    ) -> Dict[str, Any]:
        """Get current date and time with timezone support"""
        try:
            # Get current time in UTC
            from datetime import timezone as tz
            now_utc = datetime.now(tz.utc)
            
            # For simplicity, we'll handle UTC and a few common timezones
            # In production, you'd use pytz or zoneinfo for full timezone support
            if timezone == "UTC":
                now = now_utc
            elif timezone == "America/New_York":
                # EST (UTC-5) or EDT (UTC-4) based on daylight saving
                now = now_utc.replace(hour=now_utc.hour - 5)  # Simplified
            elif timezone == "Asia/Kolkata":
                # IST (UTC+5:30)
                now = now_utc.replace(hour=now_utc.hour + 5, minute=now_utc.minute + 30)
            else:
                # Default to UTC for unknown timezones
                now = now_utc
            
            # Format the datetime based on requested format
            if format == "iso":
                datetime_str = now.isoformat()
            elif format == "readable":
                datetime_str = now.strftime("%B %d, %Y at %I:%M:%S %p")
            elif format == "timestamp":
                datetime_str = str(int(now.timestamp()))
            else:
                datetime_str = now.isoformat()
            
            # Get components
            weekdays = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            components = {
                "year": now.year,
                "month": now.month,
                "day": now.day,
                "hour": now.hour,
                "minute": now.minute,
                "second": now.second,
                "weekday": weekdays[now.weekday()]
            }
            
            return {
                "datetime": datetime_str,
                "timezone": timezone,
                "unix_timestamp": now.timestamp(),
                "components": components,
                "format": format
            }
            
        except Exception as e:
            return {
                "datetime": "Error getting datetime",
                "timezone": timezone,
                "unix_timestamp": 0,
                "components": {},
                "error": str(e)
            }
    
