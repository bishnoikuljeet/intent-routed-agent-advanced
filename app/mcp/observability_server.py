from app.mcp.base import BaseMCPServer, MCPTool, MCPResource, MCPPrompt
from typing import Dict, Any, List, Optional
import random
from datetime import datetime, timedelta
import uuid


class ObservabilityMCPServer(BaseMCPServer):
    def __init__(self):
        super().__init__("observability")
    
    def _initialize(self):
        self.register_tool(MCPTool(
            name="service_metrics",
            description="Retrieve current metrics for a service",
            input_schema={
                "type": "object",
                "properties": {
                    "service_name": {"type": "string"},
                    "metric_type": {"type": "string", "enum": ["latency", "error_rate", "throughput"]}
                },
                "required": ["service_name", "metric_type"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "value": {"type": "number"},
                    "threshold": {"type": "number"},
                    "unit": {"type": "string"},
                    "timestamp": {"type": "string"}
                }
            },
            handler=self._get_service_metrics
        ))
        
        self.register_tool(MCPTool(
            name="latency_history",
            description="Get latency history for a service over time",
            input_schema={
                "type": "object",
                "properties": {
                    "service_name": {"type": "string"},
                    "time_range_minutes": {"type": "integer", "default": 60}
                },
                "required": ["service_name"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "data_points": {"type": "array"},
                    "average": {"type": "number"},
                    "p95": {"type": "number"},
                    "p99": {"type": "number"}
                }
            },
            handler=self._get_latency_history
        ))
        
        self.register_tool(MCPTool(
            name="error_rate_lookup",
            description="Get error rate for a service",
            input_schema={
                "type": "object",
                "properties": {
                    "service_name": {"type": "string"},
                    "time_range_minutes": {"type": "integer", "default": 60}
                },
                "required": ["service_name"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "error_rate": {"type": "number"},
                    "total_requests": {"type": "integer"},
                    "failed_requests": {"type": "integer"}
                }
            },
            handler=self._get_error_rate
        ))
        
        self.register_tool(MCPTool(
            name="service_status",
            description="Get overall health status of a service",
            input_schema={
                "type": "object",
                "properties": {
                    "service_name": {"type": "string"}
                },
                "required": ["service_name"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "status": {"type": "string", "enum": ["healthy", "degraded", "down"]},
                    "uptime_percentage": {"type": "number"},
                    "last_incident": {"type": "string"}
                }
            },
            handler=self._get_service_status
        ))
        
        self.register_resource(MCPResource(
            uri="observability://thresholds",
            name="Service Thresholds",
            description="Operational thresholds for all services",
            mime_type="application/json",
            content={
                "auth_service": {
                    "latency_ms": 150,
                    "error_rate": 0.01,
                    "throughput_rps": 1000
                },
                "payment_service": {
                    "latency_ms": 200,
                    "error_rate": 0.005,
                    "throughput_rps": 500
                },
                "user_service": {
                    "latency_ms": 100,
                    "error_rate": 0.01,
                    "throughput_rps": 2000
                }
            }
        ))
        
        self.register_prompt(MCPPrompt(
            name="anomaly_detection",
            description="Detect anomalies in service metrics",
            template="""Analyze the following metrics and identify any anomalies:

Service: {service_name}
Current Metrics: {metrics}
Historical Baseline: {baseline}
Thresholds: {thresholds}

Identify any anomalies and their severity.""",
            arguments=["service_name", "metrics", "baseline", "thresholds"]
        ))
        
        self.register_prompt(MCPPrompt(
            name="service_diagnostics",
            description="Generate diagnostic report for a service",
            template="""Generate a diagnostic report for the service:

Service: {service_name}
Status: {status}
Recent Metrics: {metrics}
Error Logs: {errors}

Provide diagnosis and recommended actions.""",
            arguments=["service_name", "status", "metrics", "errors"]
        ))
        
        # New Advanced Tools
        self.register_tool(MCPTool(
            name="alert_management",
            description="Manage and query alerts for services",
            input_schema={
                "type": "object",
                "properties": {
                    "action": {"type": "string", "enum": ["list", "create", "acknowledge", "resolve"]},
                    "service_name": {"type": "string"},
                    "severity": {"type": "string", "enum": ["critical", "warning", "info"]},
                    "alert_id": {"type": "string"}
                },
                "required": ["action"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "alerts": {"type": "array"},
                    "total_count": {"type": "integer"},
                    "critical_count": {"type": "integer"}
                }
            },
            handler=self._alert_management
        ))
        
        self.register_tool(MCPTool(
            name="log_aggregation",
            description="Search and aggregate logs from services",
            input_schema={
                "type": "object",
                "properties": {
                    "service_name": {"type": "string"},
                    "log_level": {"type": "string", "enum": ["ERROR", "WARN", "INFO", "DEBUG"]},
                    "search_query": {"type": "string"},
                    "time_range_minutes": {"type": "integer", "default": 60},
                    "limit": {"type": "integer", "default": 100}
                },
                "required": ["service_name"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "logs": {"type": "array"},
                    "total_count": {"type": "integer"},
                    "error_count": {"type": "integer"}
                }
            },
            handler=self._log_aggregation
        ))
        
        self.register_tool(MCPTool(
            name="slo_tracking",
            description="Track Service Level Objectives (SLO) compliance",
            input_schema={
                "type": "object",
                "properties": {
                    "service_name": {"type": "string"},
                    "slo_type": {"type": "string", "enum": ["availability", "latency", "error_rate"]},
                    "time_range_days": {"type": "integer", "default": 30}
                },
                "required": ["service_name", "slo_type"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "current_compliance": {"type": "number"},
                    "target_slo": {"type": "number"},
                    "error_budget_remaining": {"type": "number"},
                    "status": {"type": "string"}
                }
            },
            handler=self._slo_tracking
        ))
        
        self.register_tool(MCPTool(
            name="capacity_planning",
            description="Analyze current usage AND forecast future capacity needs in a single call. Returns both current metrics and 30-day predictions with growth rates and days-until-full calculations.",
            input_schema={
                "type": "object",
                "properties": {
                    "service_name": {
                        "type": "string",
                        "description": "Service name to analyze"
                    },
                    "resource_type": {
                        "type": "string",
                        "enum": ["cpu", "memory", "disk", "network"],
                        "description": "Resource type (cpu, memory, disk, network)"
                    },
                    "forecast_days": {
                        "type": "integer",
                        "default": 30,
                        "description": "Forecast period in days (returns both current + forecast)"
                    }
                },
                "required": ["service_name", "resource_type"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "current_usage": {
                        "type": "number",
                        "description": "Current usage percentage"
                    },
                    "predicted_usage": {
                        "type": "number",
                        "description": "Predicted usage after forecast period"
                    },
                    "capacity_limit": {
                        "type": "number",
                        "description": "Maximum capacity (100%)"
                    },
                    "days_until_full": {
                        "type": "integer",
                        "description": "Days until capacity reaches 100%"
                    },
                    "growth_rate": {
                        "type": "number",
                        "description": "Growth rate multiplier"
                    }
                }
            },
            handler=self._capacity_planning
        ))
        
        self.register_tool(MCPTool(
            name="incident_management",
            description="Manage and track incidents",
            input_schema={
                "type": "object",
                "properties": {
                    "action": {"type": "string", "enum": ["list", "create", "update", "resolve"]},
                    "incident_id": {"type": "string"},
                    "service_name": {"type": "string"},
                    "severity": {"type": "string", "enum": ["P0", "P1", "P2", "P3"]},
                    "description": {"type": "string"}
                },
                "required": ["action"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "incidents": {"type": "array"},
                    "total_count": {"type": "integer"},
                    "open_count": {"type": "integer"}
                }
            },
            handler=self._incident_management
        ))
    
    async def _get_service_metrics(self, service_name: str, metric_type: str) -> Dict[str, Any]:
        # Define metric ranges and thresholds
        metric_config = {
            "latency": {
                "min": 50,
                "max": 300,
                "threshold": 200,  # Alert if latency > 200ms
                "unit": "ms"
            },
            "error_rate": {
                "min": 0.001,
                "max": 0.05,
                "threshold": 0.02,  # Alert if error rate > 2%
                "unit": "percentage"
            },
            "throughput": {
                "min": 100,
                "max": 2000,
                "threshold": 500,  # Alert if throughput < 500 rps
                "unit": "rps"
            }
        }
        
        config = metric_config.get(metric_type, {
            "min": 0,
            "max": 100,
            "threshold": 50,
            "unit": "unit"
        })
        
        value = random.uniform(config["min"], config["max"])
        
        return {
            "value": round(value, 2),
            "threshold": config["threshold"],
            "unit": config["unit"],
            "timestamp": datetime.utcnow().isoformat(),
            "service": service_name
        }
    
    async def _get_latency_history(
        self,
        service_name: str,
        time_range_minutes: int = 60
    ) -> Dict[str, Any]:
        data_points = []
        for i in range(time_range_minutes):
            timestamp = datetime.utcnow() - timedelta(minutes=time_range_minutes - i)
            value = random.uniform(50, 250)
            data_points.append({
                "timestamp": timestamp.isoformat(),
                "value": round(value, 2)
            })
        
        values = [dp["value"] for dp in data_points]
        values.sort()
        
        return {
            "data_points": data_points,
            "average": round(sum(values) / len(values), 2),
            "p95": round(values[int(len(values) * 0.95)], 2),
            "p99": round(values[int(len(values) * 0.99)], 2)
        }
    
    async def _get_error_rate(
        self,
        service_name: str,
        time_range_minutes: int = 60
    ) -> Dict[str, Any]:
        total_requests = random.randint(10000, 50000)
        failed_requests = random.randint(10, 500)
        error_rate = failed_requests / total_requests
        
        return {
            "error_rate": round(error_rate, 4),
            "total_requests": total_requests,
            "failed_requests": failed_requests,
            "time_range_minutes": time_range_minutes
        }
    
    async def _get_service_status(self, service_name: str) -> Dict[str, Any]:
        statuses = ["healthy", "degraded", "healthy", "healthy"]
        status = random.choice(statuses)
        
        return {
            "status": status,
            "uptime_percentage": round(random.uniform(99.0, 100.0), 2),
            "last_incident": (datetime.utcnow() - timedelta(days=random.randint(1, 30))).isoformat(),
            "service": service_name
        }
    
    async def _alert_management(
        self,
        action: str,
        service_name: Optional[str] = None,
        severity: Optional[str] = None,
        alert_id: Optional[str] = None
    ) -> Dict[str, Any]:
        if action == "list":
            alerts = []
            for i in range(random.randint(2, 8)):
                alerts.append({
                    "alert_id": str(uuid.uuid4()),
                    "service": service_name or random.choice(["auth", "payment", "api"]),
                    "severity": random.choice(["critical", "warning", "info"]),
                    "message": f"Alert {i+1}: Service metric exceeded threshold",
                    "timestamp": (datetime.utcnow() - timedelta(minutes=random.randint(1, 120))).isoformat(),
                    "status": random.choice(["active", "acknowledged"])
                })
            
            critical_count = sum(1 for a in alerts if a["severity"] == "critical")
            
            return {
                "alerts": alerts,
                "total_count": len(alerts),
                "critical_count": critical_count,
                "action": action
            }
        
        elif action == "create":
            return {
                "alert_id": str(uuid.uuid4()),
                "service": service_name,
                "severity": severity or "warning",
                "status": "active",
                "created_at": datetime.utcnow().isoformat(),
                "action": action
            }
        
        else:
            return {
                "alert_id": alert_id or str(uuid.uuid4()),
                "status": "resolved" if action == "resolve" else "acknowledged",
                "updated_at": datetime.utcnow().isoformat(),
                "action": action
            }
    
    async def _log_aggregation(
        self,
        service_name: str,
        log_level: str = "INFO",
        search_query: Optional[str] = None,
        time_range_minutes: int = 60,
        limit: int = 100
    ) -> Dict[str, Any]:
        logs = []
        num_logs = min(random.randint(10, 50), limit)
        
        log_messages = [
            "Request processed successfully",
            "Database connection established",
            "Cache miss, fetching from database",
            "Authentication successful",
            "Rate limit exceeded",
            "Invalid request parameters",
            "Service unavailable",
            "Timeout waiting for response"
        ]
        
        for i in range(num_logs):
            level = random.choice(["ERROR", "WARN", "INFO", "INFO", "INFO"])
            logs.append({
                "timestamp": (datetime.utcnow() - timedelta(minutes=random.randint(1, time_range_minutes))).isoformat(),
                "level": level,
                "service": service_name,
                "message": random.choice(log_messages),
                "request_id": str(uuid.uuid4()),
                "metadata": {
                    "user_id": f"user_{random.randint(1000, 9999)}",
                    "endpoint": random.choice(["/api/users", "/api/orders", "/api/payments"])
                }
            })
        
        error_count = sum(1 for log in logs if log["level"] == "ERROR")
        
        return {
            "logs": sorted(logs, key=lambda x: x["timestamp"], reverse=True),
            "total_count": len(logs),
            "error_count": error_count,
            "search_query": search_query,
            "time_range_minutes": time_range_minutes
        }
    
    async def _slo_tracking(
        self,
        service_name: str,
        slo_type: str,
        time_range_days: int = 30
    ) -> Dict[str, Any]:
        slo_targets = {
            "availability": 99.9,
            "latency": 95.0,  # 95% of requests under threshold
            "error_rate": 99.0  # 99% success rate
        }
        
        target = slo_targets.get(slo_type, 99.0)
        current = round(random.uniform(target - 1.0, target + 0.5), 2)
        
        error_budget = 100 - target
        consumed = max(0, target - current)
        remaining = max(0, error_budget - consumed)
        
        status = "healthy" if current >= target else "at_risk" if current >= target - 0.5 else "breached"
        
        return {
            "current_compliance": current,
            "target_slo": target,
            "error_budget_remaining": round(remaining, 2),
            "error_budget_consumed": round(consumed, 2),
            "status": status,
            "slo_type": slo_type,
            "time_range_days": time_range_days
        }
    
    async def _capacity_planning(
        self,
        service_name: str,
        resource_type: str,
        forecast_days: int = 30
    ) -> Dict[str, Any]:
        capacity_limits = {
            "cpu": 100.0,
            "memory": 100.0,
            "disk": 100.0,
            "network": 100.0
        }
        
        limit = capacity_limits.get(resource_type, 100.0)
        current = round(random.uniform(40, 85), 2)
        
        # Simulate growth rate
        growth_rate = random.uniform(0.5, 2.0)  # % per day
        predicted = min(limit, current + (growth_rate * forecast_days))
        
        days_until_full = int((limit - current) / growth_rate) if growth_rate > 0 else 999
        
        return {
            "current_usage": current,
            "predicted_usage": round(predicted, 2),
            "capacity_limit": limit,
            "days_until_full": days_until_full,
            "growth_rate_per_day": round(growth_rate, 2),
            "resource_type": resource_type,
            "forecast_days": forecast_days
        }
    
    async def _incident_management(
        self,
        action: str,
        incident_id: Optional[str] = None,
        service_name: Optional[str] = None,
        severity: Optional[str] = None,
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        if action == "list":
            incidents = []
            for i in range(random.randint(2, 6)):
                incidents.append({
                    "incident_id": str(uuid.uuid4()),
                    "service": service_name or random.choice(["auth", "payment", "api"]),
                    "severity": random.choice(["P0", "P1", "P2", "P3"]),
                    "description": f"Incident {i+1}: Service degradation detected",
                    "status": random.choice(["open", "investigating", "resolved"]),
                    "created_at": (datetime.utcnow() - timedelta(hours=random.randint(1, 72))).isoformat(),
                    "assigned_to": f"team_{random.randint(1, 5)}"
                })
            
            open_count = sum(1 for inc in incidents if inc["status"] != "resolved")
            
            return {
                "incidents": incidents,
                "total_count": len(incidents),
                "open_count": open_count,
                "action": action
            }
        
        elif action == "create":
            return {
                "incident_id": str(uuid.uuid4()),
                "service": service_name,
                "severity": severity or "P2",
                "description": description or "New incident created",
                "status": "open",
                "created_at": datetime.utcnow().isoformat(),
                "action": action
            }
        
        else:
            return {
                "incident_id": incident_id or str(uuid.uuid4()),
                "status": "resolved" if action == "resolve" else "investigating",
                "updated_at": datetime.utcnow().isoformat(),
                "action": action
            }
