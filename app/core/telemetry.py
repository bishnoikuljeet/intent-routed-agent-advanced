from typing import Dict, Any, Optional
from datetime import datetime
from collections import defaultdict
from app.core.logging import logger
import threading


class TelemetryCollector:
    """Collect and track runtime metrics"""
    
    def __init__(self):
        self._lock = threading.Lock()
        self._metrics = defaultdict(list)
        self._counters = defaultdict(int)
        self._token_usage = {
            "total_prompt_tokens": 0,
            "total_completion_tokens": 0,
            "total_tokens": 0,
            "total_cost_usd": 0.0
        }
    
    def record_workflow_duration(self, duration_ms: float, conversation_id: str):
        """Record workflow execution duration"""
        with self._lock:
            self._metrics["workflow_duration_ms"].append({
                "value": duration_ms,
                "timestamp": datetime.utcnow().isoformat(),
                "conversation_id": conversation_id
            })
    
    def record_tool_latency(self, tool_name: str, latency_ms: float):
        """Record tool execution latency"""
        with self._lock:
            self._metrics[f"tool_latency_{tool_name}"].append({
                "value": latency_ms,
                "timestamp": datetime.utcnow().isoformat()
            })
    
    def record_llm_latency(self, agent_name: str, latency_ms: float):
        """Record LLM call latency"""
        with self._lock:
            self._metrics[f"llm_latency_{agent_name}"].append({
                "value": latency_ms,
                "timestamp": datetime.utcnow().isoformat()
            })
    
    def record_token_usage(
        self,
        prompt_tokens: int,
        completion_tokens: int,
        model: str = "gpt-4o-mini"
    ):
        """Record token usage and estimate cost"""
        total_tokens = prompt_tokens + completion_tokens
        
        # Cost per 1M tokens (approximate)
        cost_per_1m_prompt = 0.15  # $0.15 per 1M prompt tokens for gpt-4o-mini
        cost_per_1m_completion = 0.60  # $0.60 per 1M completion tokens
        
        prompt_cost = (prompt_tokens / 1_000_000) * cost_per_1m_prompt
        completion_cost = (completion_tokens / 1_000_000) * cost_per_1m_completion
        total_cost = prompt_cost + completion_cost
        
        with self._lock:
            self._token_usage["total_prompt_tokens"] += prompt_tokens
            self._token_usage["total_completion_tokens"] += completion_tokens
            self._token_usage["total_tokens"] += total_tokens
            self._token_usage["total_cost_usd"] += total_cost
            
            self._metrics["token_usage"].append({
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": total_tokens,
                "estimated_cost_usd": total_cost,
                "model": model,
                "timestamp": datetime.utcnow().isoformat()
            })
        
        logger.info_structured(
            "Token usage recorded",
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            estimated_cost_usd=round(total_cost, 6),
            model=model
        )
    
    def increment_counter(self, counter_name: str, value: int = 1):
        """Increment a counter"""
        with self._lock:
            self._counters[counter_name] += value
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get summary of collected metrics"""
        with self._lock:
            summary = {
                "token_usage": self._token_usage.copy(),
                "counters": dict(self._counters),
                "metrics": {}
            }
            
            # Calculate averages for numeric metrics
            for metric_name, values in self._metrics.items():
                if values and isinstance(values[0].get("value"), (int, float)):
                    numeric_values = [v["value"] for v in values]
                    summary["metrics"][metric_name] = {
                        "count": len(numeric_values),
                        "average": sum(numeric_values) / len(numeric_values),
                        "min": min(numeric_values),
                        "max": max(numeric_values),
                        "total": sum(numeric_values)
                    }
            
            return summary
    
    def reset_metrics(self):
        """Reset all metrics"""
        with self._lock:
            self._metrics.clear()
            self._counters.clear()
            self._token_usage = {
                "total_prompt_tokens": 0,
                "total_completion_tokens": 0,
                "total_tokens": 0,
                "total_cost_usd": 0.0
            }


# Global telemetry collector instance
telemetry = TelemetryCollector()
