"""
Complete MCP Tools Registry
All 35 tools with descriptions, schemas, and metadata
Generated from enhanced Intent-Routed Agent Advanced system
(Simplified: removed redundant knowledge tools - policy_lookup, document_lookup, configuration_lookup)
"""

TOOL_REGISTRY = {
    "observability": {
        "server_name": "ObservabilityMCPServer",
        "description": "Comprehensive observability and monitoring tools",
        "tools": {
            "service_metrics": {
                "name": "service_metrics",
                "description": "Retrieve current metrics for a service",
                "category": "monitoring",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "service_name": {
                            "type": "string",
                            "description": "Name of the service to query"
                        },
                        "metric_type": {
                            "type": "string",
                            "enum": ["latency", "error_rate", "throughput"],
                            "description": "Type of metric to retrieve"
                        }
                    },
                    "required": ["service_name", "metric_type"]
                },
                "output_schema": {
                    "type": "object",
                    "properties": {
                        "value": {"type": "number", "description": "Current metric value"},
                        "threshold": {"type": "number", "description": "Alert threshold"},
                        "unit": {"type": "string", "description": "Measurement unit"},
                        "timestamp": {"type": "string", "description": "Measurement timestamp"}
                    }
                },
                "use_cases": ["Real-time monitoring", "Threshold checking", "Service health"],
                "examples": [
                    {"service_name": "payment_service", "metric_type": "latency"},
                    {"service_name": "auth_service", "metric_type": "error_rate"}
                ]
            },
            
            "latency_history": {
                "name": "latency_history",
                "description": "Get latency history for a service over time",
                "category": "monitoring",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "service_name": {
                            "type": "string",
                            "description": "Name of the service"
                        },
                        "time_range_minutes": {
                            "type": "integer",
                            "default": 60,
                            "description": "Time range in minutes"
                        }
                    },
                    "required": ["service_name"]
                },
                "output_schema": {
                    "type": "object",
                    "properties": {
                        "data_points": {
                            "type": "array",
                            "description": "Historical latency data points"
                        },
                        "average": {"type": "number", "description": "Average latency"},
                        "p95": {"type": "number", "description": "95th percentile latency"},
                        "p99": {"type": "number", "description": "99th percentile latency"}
                    }
                },
                "use_cases": ["Performance analysis", "Trend identification", "SLA monitoring"],
                "examples": [
                    {"service_name": "api_service", "time_range_minutes": 120},
                    {"service_name": "database_service", "time_range_minutes": 60}
                ]
            },
            
            "error_rate_lookup": {
                "name": "error_rate_lookup",
                "description": "Get error rate for a service",
                "category": "monitoring",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "service_name": {
                            "type": "string",
                            "description": "Name of the service"
                        },
                        "time_range_minutes": {
                            "type": "integer",
                            "default": 60,
                            "description": "Time range in minutes"
                        }
                    },
                    "required": ["service_name"]
                },
                "output_schema": {
                    "type": "object",
                    "properties": {
                        "error_rate": {
                            "type": "number",
                            "description": "Error rate as percentage"
                        },
                        "total_requests": {
                            "type": "integer",
                            "description": "Total request count"
                        },
                        "failed_requests": {
                            "type": "integer",
                            "description": "Failed request count"
                        }
                    }
                },
                "use_cases": ["Service health monitoring", "SLA compliance", "Error analysis"],
                "examples": [
                    {"service_name": "payment_service", "time_range_minutes": 60},
                    {"service_name": "user_service", "time_range_minutes": 1440}
                ]
            },
            
            "service_status": {
                "name": "service_status",
                "description": "Get overall health status of a service",
                "category": "monitoring",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "service_name": {
                            "type": "string",
                            "description": "Name of the service"
                        }
                    },
                    "required": ["service_name"]
                },
                "output_schema": {
                    "type": "object",
                    "properties": {
                        "status": {
                            "type": "string",
                            "enum": ["healthy", "degraded", "down"],
                            "description": "Service health status"
                        },
                        "uptime_percentage": {
                            "type": "number",
                            "description": "Uptime percentage"
                        },
                        "last_incident": {
                            "type": "string",
                            "description": "Last incident timestamp"
                        }
                    }
                },
                "use_cases": ["Health checks", "Dashboard displays", "Service monitoring"],
                "examples": [
                    {"service_name": "auth_service"},
                    {"service_name": "payment_service"}
                ]
            },
            
            "alert_management": {
                "name": "alert_management",
                "description": "Manage and query alerts for services",
                "category": "incident_management",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "action": {
                            "type": "string",
                            "enum": ["list", "create", "acknowledge", "resolve"],
                            "description": "Action to perform"
                        },
                        "service_name": {
                            "type": "string",
                            "description": "Service name for filtering"
                        },
                        "severity": {
                            "type": "string",
                            "enum": ["critical", "warning", "info"],
                            "description": "Alert severity level"
                        },
                        "alert_id": {
                            "type": "string",
                            "description": "Alert ID for specific operations"
                        }
                    },
                    "required": ["action"]
                },
                "output_schema": {
                    "type": "object",
                    "properties": {
                        "alerts": {
                            "type": "array",
                            "description": "List of alerts"
                        },
                        "total_count": {
                            "type": "integer",
                            "description": "Total alert count"
                        },
                        "critical_count": {
                            "type": "integer",
                            "description": "Critical alerts count"
                        }
                    }
                },
                "use_cases": ["Alert lifecycle management", "Incident response", "On-call workflows"],
                "examples": [
                    {"action": "list", "service_name": "payment_service"},
                    {"action": "create", "service_name": "auth_service", "severity": "critical"}
                ]
            },
            
            "log_aggregation": {
                "name": "log_aggregation",
                "description": "Search and aggregate logs from services",
                "category": "logging",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "service_name": {
                            "type": "string",
                            "description": "Service name"
                        },
                        "log_level": {
                            "type": "string",
                            "enum": ["ERROR", "WARN", "INFO", "DEBUG"],
                            "description": "Log level filter"
                        },
                        "search_query": {
                            "type": "string",
                            "description": "Search query string"
                        },
                        "time_range_minutes": {
                            "type": "integer",
                            "default": 60,
                            "description": "Time range"
                        },
                        "limit": {
                            "type": "integer",
                            "default": 100,
                            "description": "Maximum results"
                        }
                    },
                    "required": ["service_name"]
                },
                "output_schema": {
                    "type": "object",
                    "properties": {
                        "logs": {
                            "type": "array",
                            "description": "Filtered log entries"
                        },
                        "total_count": {
                            "type": "integer",
                            "description": "Total log count"
                        },
                        "error_count": {
                            "type": "integer",
                            "description": "Error log count"
                        }
                    }
                },
                "use_cases": ["Error investigation", "Audit trails", "Debugging"],
                "examples": [
                    {"service_name": "api_service", "log_level": "ERROR", "time_range_minutes": 60},
                    {"service_name": "payment_service", "search_query": "timeout", "limit": 50}
                ]
            },
            
            "slo_tracking": {
                "name": "slo_tracking",
                "description": "Track Service Level Objectives (SLO) compliance",
                "category": "slo_monitoring",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "service_name": {
                            "type": "string",
                            "description": "Service name"
                        },
                        "slo_type": {
                            "type": "string",
                            "enum": ["availability", "latency", "error_rate"],
                            "description": "SLO type"
                        },
                        "time_range_days": {
                            "type": "integer",
                            "default": 30,
                            "description": "Time range in days"
                        }
                    },
                    "required": ["service_name", "slo_type"]
                },
                "output_schema": {
                    "type": "object",
                    "properties": {
                        "current_compliance": {
                            "type": "number",
                            "description": "Current compliance percentage"
                        },
                        "target_slo": {
                            "type": "number",
                            "description": "Target SLO percentage"
                        },
                        "error_budget_remaining": {
                            "type": "number",
                            "description": "Remaining error budget"
                        },
                        "status": {
                            "type": "string",
                            "enum": ["healthy", "at_risk", "breached"],
                            "description": "Compliance status"
                        }
                    }
                },
                "use_cases": ["SLO monitoring", "Error budget management", "Reliability engineering"],
                "examples": [
                    {"service_name": "payment_service", "slo_type": "availability", "time_range_days": 30},
                    {"service_name": "auth_service", "slo_type": "latency", "time_range_days": 7}
                ]
            },
            
            "capacity_planning": {
                "name": "capacity_planning",
                "description": "Analyze capacity and predict resource needs",
                "category": "capacity_management",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "service_name": {
                            "type": "string",
                            "description": "Service name"
                        },
                        "resource_type": {
                            "type": "string",
                            "enum": ["cpu", "memory", "disk", "network"],
                            "description": "Resource type"
                        },
                        "forecast_days": {
                            "type": "integer",
                            "default": 30,
                            "description": "Forecast period"
                        }
                    },
                    "required": ["service_name", "resource_type"]
                },
                "output_schema": {
                    "type": "object",
                    "properties": {
                        "current_usage": {
                            "type": "number",
                            "description": "Current usage percentage"
                        },
                        "predicted_usage": {
                            "type": "number",
                            "description": "Predicted usage"
                        },
                        "capacity_limit": {
                            "type": "number",
                            "description": "Maximum capacity"
                        },
                        "days_until_full": {
                            "type": "integer",
                            "description": "Days until capacity is full"
                        }
                    }
                },
                "use_cases": ["Infrastructure planning", "Cost optimization", "Scaling decisions"],
                "examples": [
                    {"service_name": "auth_service", "resource_type": "cpu", "forecast_days": 30},
                    {"service_name": "payment_service", "resource_type": "memory", "forecast_days": 60}
                ]
            },
            
            "incident_management": {
                "name": "incident_management",
                "description": "Manage and track incidents",
                "category": "incident_management",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "action": {
                            "type": "string",
                            "enum": ["list", "create", "update", "resolve"],
                            "description": "Action to perform"
                        },
                        "incident_id": {
                            "type": "string",
                            "description": "Incident ID"
                        },
                        "service_name": {
                            "type": "string",
                            "description": "Service name"
                        },
                        "severity": {
                            "type": "string",
                            "enum": ["P0", "P1", "P2", "P3"],
                            "description": "Incident severity"
                        },
                        "description": {
                            "type": "string",
                            "description": "Incident description"
                        }
                    },
                    "required": ["action"]
                },
                "output_schema": {
                    "type": "object",
                    "properties": {
                        "incidents": {
                            "type": "array",
                            "description": "List of incidents"
                        },
                        "total_count": {
                            "type": "integer",
                            "description": "Total incident count"
                        },
                        "open_count": {
                            "type": "integer",
                            "description": "Open incidents count"
                        }
                    }
                },
                "use_cases": ["Incident lifecycle management", "Post-mortem analysis", "On-call workflows"],
                "examples": [
                    {"action": "list", "service_name": "payment_service"},
                    {"action": "create", "service_name": "auth_service", "severity": "P1", "description": "High latency detected"}
                ]
            }
        },
        "total_tools": 10
    },
    
    "knowledge": {
        "server_name": "KnowledgeMCPServer",
        "description": "Knowledge management and documentation tools",
        "tools": {
            "semantic_search": {
                "name": "semantic_search",
                "description": "Search all documentation using natural language queries and semantic similarity",
                "category": "search",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Natural language search query"
                        },
                        "top_k": {
                            "type": "integer",
                            "default": 5,
                            "description": "Number of results"
                        },
                        "filter": {
                            "type": "object",
                            "default": {},
                            "description": "Metadata filters"
                        }
                    },
                    "required": ["query"]
                },
                "output_schema": {
                    "type": "object",
                    "properties": {
                        "results": {
                            "type": "array",
                            "description": "Search results"
                        },
                        "total_found": {
                            "type": "integer",
                            "description": "Total results count"
                        }
                    }
                },
                "use_cases": ["Answer natural language questions", "Find policies and procedures", "Search architecture documentation", "Knowledge discovery"],
                "examples": [
                    {"query": "payment processing", "top_k": 10},
                    {"query": "API authentication", "filter": {"category": "security"}}
                ]
            },
            
                        
            "document_versioning": {
                "name": "document_versioning",
                "description": "Manage document versions and track changes",
                "category": "version_control",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "action": {
                            "type": "string",
                            "enum": ["list_versions", "get_version", "compare_versions"],
                            "description": "Action to perform"
                        },
                        "document_id": {
                            "type": "string",
                            "description": "Document ID"
                        },
                        "version_id": {
                            "type": "string",
                            "description": "Specific version ID"
                        },
                        "compare_with": {
                            "type": "string",
                            "description": "Version to compare with"
                        }
                    },
                    "required": ["action", "document_id"]
                },
                "output_schema": {
                    "type": "object",
                    "properties": {
                        "versions": {
                            "type": "array",
                            "description": "List of versions"
                        },
                        "current_version": {
                            "type": "string",
                            "description": "Current version ID"
                        },
                        "changes": {
                            "type": "array",
                            "description": "Change details"
                        }
                    }
                },
                "use_cases": ["Version control", "Change tracking", "Rollback operations"],
                "examples": [
                    {"action": "list_versions", "document_id": "doc_api_v2"},
                    {"action": "compare_versions", "document_id": "doc_api_v2", "version_id": "v2.1", "compare_with": "v2.2"}
                ]
            },
            
            "change_tracking": {
                "name": "change_tracking",
                "description": "Track and audit document changes",
                "category": "audit",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "document_id": {
                            "type": "string",
                            "description": "Document ID"
                        },
                        "time_range_days": {
                            "type": "integer",
                            "default": 30,
                            "description": "Time range in days"
                        },
                        "author": {
                            "type": "string",
                            "description": "Filter by author"
                        }
                    },
                    "required": ["document_id"]
                },
                "output_schema": {
                    "type": "object",
                    "properties": {
                        "changes": {
                            "type": "array",
                            "description": "List of changes"
                        },
                        "total_changes": {
                            "type": "integer",
                            "description": "Total change count"
                        },
                        "contributors": {
                            "type": "array",
                            "description": "List of contributors"
                        }
                    }
                },
                "use_cases": ["Audit trails", "Compliance", "Collaboration tracking"],
                "examples": [
                    {"document_id": "doc_payment_api", "time_range_days": 30},
                    {"document_id": "doc_security_policy", "author": "user_123"}
                ]
            },
            
            "recommendation_engine": {
                "name": "recommendation_engine",
                "description": "Get document recommendations based on context",
                "category": "recommendations",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "current_document": {
                            "type": "string",
                            "description": "Current document ID"
                        },
                        "user_context": {
                            "type": "object",
                            "description": "User context data"
                        },
                        "max_recommendations": {
                            "type": "integer",
                            "default": 5,
                            "description": "Maximum recommendations"
                        }
                    },
                    "required": ["current_document"]
                },
                "output_schema": {
                    "type": "object",
                    "properties": {
                        "recommendations": {
                            "type": "array",
                            "description": "Recommended documents"
                        },
                        "relevance_scores": {
                            "type": "array",
                            "description": "Relevance scores"
                        }
                    }
                },
                "use_cases": ["Content discovery", "User engagement", "Knowledge navigation"],
                "examples": [
                    {"current_document": "doc_payment_guide", "max_recommendations": 5},
                    {"current_document": "doc_api_reference", "user_context": {"role": "developer"}}
                ]
            },
            
            "knowledge_graph_query": {
                "name": "knowledge_graph_query",
                "description": "Query relationships between documents and concepts",
                "category": "knowledge_graph",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "entity": {
                            "type": "string",
                            "description": "Entity to query"
                        },
                        "relationship_type": {
                            "type": "string",
                            "enum": ["related_to", "depends_on", "references", "all"],
                            "default": "all",
                            "description": "Relationship filter"
                        },
                        "depth": {
                            "type": "integer",
                            "default": 1,
                            "description": "Graph traversal depth"
                        }
                    },
                    "required": ["entity"]
                },
                "output_schema": {
                    "type": "object",
                    "properties": {
                        "nodes": {
                            "type": "array",
                            "description": "Graph nodes"
                        },
                        "edges": {
                            "type": "array",
                            "description": "Graph edges"
                        },
                        "graph_summary": {
                            "type": "string",
                            "description": "Summary description"
                        }
                    }
                },
                "use_cases": ["Knowledge mapping", "Dependency analysis", "Concept exploration"],
                "examples": [
                    {"entity": "payment_service", "relationship_type": "depends_on", "depth": 2},
                    {"entity": "authentication", "depth": 1}
                ]
            }
        },
        "total_tools": 5
    },
    
    "utility": {
        "server_name": "UtilityMCPServer",
        "description": "Data processing and analysis utilities",
        "tools": {
            "compare_values": {
                "name": "compare_values",
                "description": "Compare two numeric values",
                "category": "comparison",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "value1": {
                            "type": "number",
                            "description": "First value"
                        },
                        "value2": {
                            "type": "number",
                            "description": "Second value"
                        },
                        "comparison_type": {
                            "type": "string",
                            "enum": ["greater", "less", "equal", "not_equal"],
                            "default": "greater",
                            "description": "Comparison type"
                        }
                    },
                    "required": ["value1", "value2"]
                },
                "output_schema": {
                    "type": "object",
                    "properties": {
                        "result": {
                            "type": "boolean",
                            "description": "Comparison result"
                        },
                        "difference": {
                            "type": "number",
                            "description": "Absolute difference"
                        },
                        "ratio": {
                            "type": "number",
                            "description": "Value ratio"
                        }
                    }
                },
                "use_cases": ["Threshold checks", "Metric comparisons", "Value analysis"],
                "examples": [
                    {"value1": 100, "value2": 85, "comparison_type": "greater"},
                    {"value1": 0.95, "value2": 0.99, "comparison_type": "less"}
                ]
            },
            
            "percentage_difference": {
                "name": "percentage_difference",
                "description": "Calculate percentage difference between two values",
                "category": "calculation",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "value1": {
                            "type": "number",
                            "description": "First value"
                        },
                        "value2": {
                            "type": "number",
                            "description": "Second value"
                        }
                    },
                    "required": ["value1", "value2"]
                },
                "output_schema": {
                    "type": "object",
                    "properties": {
                        "percentage_diff": {
                            "type": "number",
                            "description": "Percentage difference"
                        },
                        "absolute_diff": {
                            "type": "number",
                            "description": "Absolute difference"
                        },
                        "direction": {
                            "type": "string",
                            "description": "Change direction"
                        }
                    }
                },
                "use_cases": ["Trend analysis", "Change detection", "Growth calculation"],
                "examples": [
                    {"value1": 1000, "value2": 1200},
                    {"value1": 95.5, "value2": 89.2}
                ]
            },
            
            "time_range_calculator": {
                "name": "time_range_calculator",
                "description": "Calculate time ranges and durations",
                "category": "time_calculation",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "start_time": {
                            "type": "string",
                            "description": "Start timestamp"
                        },
                        "end_time": {
                            "type": "string",
                            "description": "End timestamp"
                        },
                        "unit": {
                            "type": "string",
                            "enum": ["seconds", "minutes", "hours", "days"],
                            "default": "minutes",
                            "description": "Time unit"
                        }
                    },
                    "required": ["start_time", "end_time"]
                },
                "output_schema": {
                    "type": "object",
                    "properties": {
                        "duration": {
                            "type": "number",
                            "description": "Calculated duration"
                        },
                        "unit": {
                            "type": "string",
                            "description": "Time unit"
                        }
                    }
                },
                "use_cases": ["SLA calculations", "Time tracking", "Duration analysis"],
                "examples": [
                    {"start_time": "2026-03-06T00:00:00Z", "end_time": "2026-03-06T01:30:00Z", "unit": "minutes"},
                    {"start_time": "2026-03-01T00:00:00Z", "end_time": "2026-03-06T23:59:59Z", "unit": "days"}
                ]
            },
            
            "statistics_summary": {
                "name": "statistics_summary",
                "description": "Calculate statistical summary of a dataset",
                "category": "statistics",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "values": {
                            "type": "array",
                            "items": {"type": "number"},
                            "description": "Array of numbers"
                        }
                    },
                    "required": ["values"]
                },
                "output_schema": {
                    "type": "object",
                    "properties": {
                        "mean": {
                            "type": "number",
                            "description": "Average value"
                        },
                        "median": {
                            "type": "number",
                            "description": "Median value"
                        },
                        "std_dev": {
                            "type": "number",
                            "description": "Standard deviation"
                        },
                        "min": {
                            "type": "number",
                            "description": "Minimum value"
                        },
                        "max": {
                            "type": "number",
                            "description": "Maximum value"
                        }
                    }
                },
                "use_cases": ["Data analysis", "Performance metrics", "Statistical insights"],
                "examples": [
                    {"values": [100, 150, 120, 180, 140]},
                    {"values": [1.2, 1.5, 1.1, 1.8, 1.3, 1.6]}
                ]
            },
            
            "trend_analysis": {
                "name": "trend_analysis",
                "description": "Analyze trends and forecast future values",
                "category": "forecasting",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "values": {
                            "type": "array",
                            "items": {"type": "number"},
                            "description": "Historical data points"
                        },
                        "forecast_periods": {
                            "type": "integer",
                            "default": 5,
                            "description": "Forecast periods"
                        },
                        "confidence_level": {
                            "type": "number",
                            "default": 0.95,
                            "description": "Confidence level"
                        }
                    },
                    "required": ["values"]
                },
                "output_schema": {
                    "type": "object",
                    "properties": {
                        "trend": {
                            "type": "string",
                            "description": "Trend direction"
                        },
                        "slope": {
                            "type": "number",
                            "description": "Trend slope"
                        },
                        "forecast": {
                            "type": "array",
                            "description": "Forecasted values"
                        },
                        "confidence_interval": {
                            "type": "object",
                            "description": "Confidence intervals"
                        }
                    }
                },
                "use_cases": ["Capacity planning", "Predictive analytics", "Resource forecasting"],
                "examples": [
                    {"values": [100, 120, 140, 160, 180], "forecast_periods": 5},
                    {"values": [1000, 1050, 1100, 1150], "forecast_periods": 3, "confidence_level": 0.90}
                ]
            },
            
            "anomaly_detection": {
                "name": "anomaly_detection",
                "description": "Detect anomalies in a dataset using statistical methods",
                "category": "anomaly_detection",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "values": {
                            "type": "array",
                            "items": {"type": "number"},
                            "description": "Data points"
                        },
                        "sensitivity": {
                            "type": "number",
                            "default": 2.0,
                            "description": "Detection sensitivity"
                        },
                        "method": {
                            "type": "string",
                            "enum": ["zscore", "iqr", "mad"],
                            "default": "zscore",
                            "description": "Detection method"
                        }
                    },
                    "required": ["values"]
                },
                "output_schema": {
                    "type": "object",
                    "properties": {
                        "anomalies": {
                            "type": "array",
                            "description": "Detected anomalies"
                        },
                        "anomaly_count": {
                            "type": "integer",
                            "description": "Total anomaly count"
                        },
                        "anomaly_percentage": {
                            "type": "number",
                            "description": "Percentage of anomalies"
                        }
                    }
                },
                "use_cases": ["Outlier detection", "Fraud detection", "Quality assurance"],
                "examples": [
                    {"values": [100, 105, 102, 500, 98, 103], "method": "zscore"},
                    {"values": [1.2, 1.3, 1.1, 5.0, 1.4], "sensitivity": 2.5, "method": "iqr"}
                ]
            },
            
            "data_validation": {
                "name": "data_validation",
                "description": "Validate data against schema and business rules",
                "category": "validation",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "data": {
                            "type": "object",
                            "description": "Data to validate"
                        },
                        "rules": {
                            "type": "array",
                            "description": "Validation rules"
                        },
                        "strict_mode": {
                            "type": "boolean",
                            "default": False,
                            "description": "Strict validation mode"
                        }
                    },
                    "required": ["data", "rules"]
                },
                "output_schema": {
                    "type": "object",
                    "properties": {
                        "is_valid": {
                            "type": "boolean",
                            "description": "Validation result"
                        },
                        "errors": {
                            "type": "array",
                            "description": "Validation errors"
                        },
                        "warnings": {
                            "type": "array",
                            "description": "Validation warnings"
                        }
                    }
                },
                "use_cases": ["Input validation", "Data quality checks", "Compliance verification"],
                "examples": [
                    {"data": {"timeout": 30, "retries": 3}, "rules": [{"field": "timeout", "type": "number", "min": 1, "max": 300}]},
                    {"data": {"email": "user@example.com"}, "rules": [{"field": "email", "type": "string", "pattern": r"^[^@]+@[^@]+\.[^@]+$"}]}
                ]
            },
            
            "json_yaml_parser": {
                "name": "json_yaml_parser",
                "description": "Parse and convert between JSON and YAML formats",
                "category": "data_transformation",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "content": {
                            "type": "string",
                            "description": "Content to parse"
                        },
                        "input_format": {
                            "type": "string",
                            "enum": ["json", "yaml"],
                            "description": "Input format"
                        },
                        "output_format": {
                            "type": "string",
                            "enum": ["json", "yaml"],
                            "description": "Output format"
                        },
                        "validate": {
                            "type": "boolean",
                            "default": True,
                            "description": "Validate syntax"
                        }
                    },
                    "required": ["content", "input_format", "output_format"]
                },
                "output_schema": {
                    "type": "object",
                    "properties": {
                        "parsed_data": {
                            "type": "object",
                            "description": "Parsed data structure"
                        },
                        "converted_content": {
                            "type": "string",
                            "description": "Converted content"
                        },
                        "is_valid": {
                            "type": "boolean",
                            "description": "Validation status"
                        }
                    }
                },
                "use_cases": ["Configuration management", "Data transformation", "API integration"],
                "examples": [
                    {"content": '{"timeout": 30, "retries": 3}', "input_format": "json", "output_format": "yaml"},
                    {"content": "timeout: 30\nretries: 3", "input_format": "yaml", "output_format": "json"}
                ]
            }
        },
        "total_tools": 8
    },
    
    "system": {
        "server_name": "SystemMCPServer",
        "description": "System monitoring and infrastructure tools",
        "tools": {
            "tool_registry_lookup": {
                "name": "tool_registry_lookup",
                "description": "Look up tool metadata from the registry",
                "category": "registry",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "tool_name": {
                            "type": "string",
                            "description": "Specific tool name"
                        },
                        "server": {
                            "type": "string",
                            "description": "Filter by server"
                        }
                    },
                    "required": []
                },
                "output_schema": {
                    "type": "object",
                    "properties": {
                        "tools": {
                            "type": "array",
                            "description": "Tool metadata"
                        }
                    }
                },
                "use_cases": ["Tool discovery", "Capability queries", "Registry inspection"],
                "examples": [
                    {"tool_name": "capacity_planning"},
                    {"server": "observability"}
                ]
            },
            
            "agent_health": {
                "name": "agent_health",
                "description": "Check health status of agents",
                "category": "health_monitoring",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "agent_name": {
                            "type": "string",
                            "description": "Specific agent name"
                        }
                    },
                    "required": []
                },
                "output_schema": {
                    "type": "object",
                    "properties": {
                        "status": {
                            "type": "string",
                            "description": "Health status"
                        },
                        "uptime": {
                            "type": "number",
                            "description": "Uptime percentage"
                        },
                        "last_execution": {
                            "type": "string",
                            "description": "Last execution timestamp"
                        }
                    }
                },
                "use_cases": ["System monitoring", "Health checks", "Agent status"],
                "examples": [
                    {"agent_name": "planner"},
                    {}
                ]
            },
            
            "workflow_status": {
                "name": "workflow_status",
                "description": "Get current workflow execution status",
                "category": "workflow_monitoring",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "workflow_id": {
                            "type": "string",
                            "description": "Workflow identifier"
                        }
                    },
                    "required": []
                },
                "output_schema": {
                    "type": "object",
                    "properties": {
                        "status": {
                            "type": "string",
                            "description": "Execution status"
                        },
                        "current_step": {
                            "type": "string",
                            "description": "Current step"
                        },
                        "progress": {
                            "type": "number",
                            "description": "Progress percentage"
                        }
                    }
                },
                "use_cases": ["Workflow monitoring", "Execution tracking", "Progress monitoring"],
                "examples": [
                    {"workflow_id": "workflow_123"},
                    {}
                ]
            },
            
            "list_mcp_servers": {
                "name": "list_mcp_servers",
                "description": "List all available MCP servers and their information",
                "category": "server_inventory",
                "input_schema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                },
                "output_schema": {
                    "type": "object",
                    "properties": {
                        "servers": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "name": {"type": "string"},
                                    "tool_count": {"type": "number"},
                                    "status": {"type": "string"}
                                }
                            },
                            "description": "List of servers"
                        }
                    }
                },
                "use_cases": ["System inventory", "Capability discovery", "Server monitoring"],
                "examples": [{}]
            },
            
            "performance_profiling": {
                "name": "performance_profiling",
                "description": "Profile system performance and identify bottlenecks",
                "category": "performance_analysis",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "component": {
                            "type": "string",
                            "enum": ["agents", "tools", "llm", "database", "all"],
                            "description": "Component to profile"
                        },
                        "time_range_minutes": {
                            "type": "integer",
                            "default": 60,
                            "description": "Time range"
                        },
                        "include_traces": {
                            "type": "boolean",
                            "default": False,
                            "description": "Include trace data"
                        }
                    },
                    "required": ["component"]
                },
                "output_schema": {
                    "type": "object",
                    "properties": {
                        "metrics": {
                            "type": "object",
                            "description": "Performance metrics"
                        },
                        "bottlenecks": {
                            "type": "array",
                            "description": "Identified bottlenecks"
                        },
                        "recommendations": {
                            "type": "array",
                            "description": "Optimization recommendations"
                        }
                    }
                },
                "use_cases": ["Performance optimization", "Bottleneck identification", "Capacity planning"],
                "examples": [
                    {"component": "all", "time_range_minutes": 60},
                    {"component": "agents", "include_traces": True}
                ]
            }
        },
        "total_tools": 5
    },
    
    "language": {
        "server_name": "LanguageMCPServer",
        "description": "Multilingual processing and translation tools",
        "tools": {
            "detect_language": {
                "name": "detect_language",
                "description": "Identify input language",
                "category": "language_detection",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "text": {
                            "type": "string",
                            "description": "Text to analyze"
                        }
                    },
                    "required": ["text"]
                },
                "output_schema": {
                    "type": "object",
                    "properties": {
                        "language": {
                            "type": "string",
                            "description": "Detected language code"
                        },
                        "confidence": {
                            "type": "number",
                            "description": "Detection confidence"
                        }
                    }
                },
                "use_cases": ["Multilingual support", "Content routing", "Language identification"],
                "examples": [
                    {"text": "Bonjour comment allez-vous"},
                    {"text": "Hola cómo estás"}
                ]
            },
            
            "translate_text": {
                "name": "translate_text",
                "description": "Translate between languages",
                "category": "translation",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "text": {
                            "type": "string",
                            "description": "Text to translate"
                        },
                        "source_lang": {
                            "type": "string",
                            "description": "Source language (lowercase name like 'french' or code like 'fr')"
                        },
                        "target_lang": {
                            "type": "string",
                            "description": "Target language (lowercase name like 'english' or code like 'en')"
                        }
                    },
                    "required": ["text", "target_lang"]
                },
                "output_schema": {
                    "type": "object",
                    "properties": {
                        "translated_text": {
                            "type": "string",
                            "description": "Translated text"
                        },
                        "source_language": {
                            "type": "string",
                            "description": "Detected source language"
                        }
                    }
                },
                "use_cases": ["Multilingual support", "Internationalization", "Content translation"],
                "examples": [
                    {"text": "Hello world", "target_lang": "es"},
                    {"text": "Bonjour le monde", "source_lang": "fr", "target_lang": "en"}
                ]
            },
            
            "correct_typos": {
                "name": "correct_typos",
                "description": "Normalize and correct text",
                "category": "text_correction",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "text": {
                            "type": "string",
                            "description": "Text to correct"
                        }
                    },
                    "required": ["text"]
                },
                "output_schema": {
                    "type": "object",
                    "properties": {
                        "corrected_text": {
                            "type": "string",
                            "description": "Corrected text"
                        },
                        "corrections": {
                            "type": "array",
                            "description": "List of corrections"
                        }
                    }
                },
                "use_cases": ["Input normalization", "Quality improvement", "Text correction"],
                "examples": [
                    {"text": "Helo wrld"},
                    {"text": "Ths is a tst"}
                ]
            },
            
            "normalize_text": {
                "name": "normalize_text",
                "description": "Sanitize input",
                "category": "text_sanitization",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "text": {
                            "type": "string",
                            "description": "Text to sanitize"
                        }
                    },
                    "required": ["text"]
                },
                "output_schema": {
                    "type": "object",
                    "properties": {
                        "normalized_text": {
                            "type": "string",
                            "description": "Sanitized text"
                        },
                        "removed_chars": {
                            "type": "array",
                            "description": "Removed characters"
                        }
                    }
                },
                "use_cases": ["Security", "Input validation", "Text sanitization"],
                "examples": [
                    {"text": "Hello<script>alert('xss')</script>World"},
                    {"text": "Normal text with special chars: !@#$%^&*()"}
                ]
            }
        },
        "total_tools": 4
    }
}

# Summary statistics
TOTAL_TOOLS = sum(server["total_tools"] for server in TOOL_REGISTRY.values())
TOTAL_SERVERS = len(TOOL_REGISTRY)

# Tool categories
CATEGORIES = {
    "monitoring": ["service_metrics", "latency_history", "error_rate_lookup", "service_status"],
    "incident_management": ["alert_management", "incident_management"],
    "performance_analysis": ["performance_profiling"],
    "logging": ["log_aggregation"],
    "slo_monitoring": ["slo_tracking"],
    "capacity_management": ["capacity_planning"],
    "search": ["semantic_search"],
    "version_control": ["document_versioning"],
    "audit": ["change_tracking"],
    "recommendations": ["recommendation_engine"],
    "knowledge_graph": ["knowledge_graph_query"],
    "comparison": ["compare_values"],
    "calculation": ["percentage_difference", "time_range_calculator"],
    "statistics": ["statistics_summary"],
    "forecasting": ["trend_analysis"],
    "anomaly_detection": ["anomaly_detection"],
    "validation": ["data_validation"],
    "data_transformation": ["json_yaml_parser"],
    "registry": ["tool_registry_lookup"],
    "health_monitoring": ["agent_health"],
    "workflow_monitoring": ["workflow_status"],
    "server_inventory": ["list_mcp_servers"],
    "language_detection": ["detect_language"],
    "translation": ["translate_text"],
    "text_correction": ["correct_typos"],
    "text_sanitization": ["normalize_text"]
}

# Helper functions
def get_tool_by_name(tool_name):
    """Get tool metadata by name across all servers"""
    for server_name, server_data in TOOL_REGISTRY.items():
        if tool_name in server_data["tools"]:
            return server_data["tools"][tool_name]
    return None

def get_tools_by_category(category):
    """Get all tools in a specific category"""
    tools = []
    for server_data in TOOL_REGISTRY.values():
        for tool_name, tool_data in server_data["tools"].items():
            if tool_data.get("category") == category:
                tools.append(tool_data)
    return tools

def get_tools_by_server(server_name):
    """Get all tools for a specific server"""
    return TOOL_REGISTRY.get(server_name, {}).get("tools", {})

def search_tools(query):
    """Search tools by name, description, or category"""
    results = []
    query_lower = query.lower()
    
    for server_data in TOOL_REGISTRY.values():
        for tool_name, tool_data in server_data["tools"].items():
            if (query_lower in tool_name.lower() or 
                query_lower in tool_data["description"].lower() or
                query_lower in tool_data.get("category", "").lower()):
                results.append(tool_data)
    
    return results

if __name__ == "__main__":
    print(f"MCP Tools Registry")
    print(f"Total Servers: {TOTAL_SERVERS}")
    print(f"Total Tools: {TOTAL_TOOLS}")
    print(f"Total Categories: {len(CATEGORIES)}")
    
    print("\nServer Summary:")
    for server_name, server_data in TOOL_REGISTRY.items():
        print(f"  {server_name}: {server_data['total_tools']} tools")
    
    print("\nCategory Summary:")
    for category, tools in CATEGORIES.items():
        print(f"  {category}: {len(tools)} tools")
