# Sample User Queries for All Tools

## OBSERVABILITY SERVER (9 Tools)

### service_metrics
- "What is the current throughput for the API gateway?"
    - Should use: service_metrics
    - Expected: Current throughput value in requests per second

### latency_history
- "What is the current latency for the payment service?"
    - Should use: latency_history
    - Expected: Current latency metric value with threshold and timestamp
- "Show me the latency trend for payment_service over the last 2 hours"
    - Should use: latency_history (service_metrics)
    - Expected: Historical latency data points with p95, p99, and average
- "What was the latency pattern for auth_service in the last hour?"
    - Should use: latency_history
    - Expected: Time-series latency data with percentile statistics
- "Display the performance history of database_service"
    - Should use: latency_history (error_rate_lookup)
    - Expected: Historical latency metrics with trend analysis

### error_rate_lookup
- "Show me the error rate for auth_service"
    - Should use: error_rate_lookup
    - Expected: Current error rate percentage for authentication service
- "What's the error rate for payment_service in the last 60 minutes?"
    - Should use: error_rate_lookup
    - Expected: Error rate percentage with total and failed request counts
- "Check the failure rate for user_service over the past day"
    - Should use: error_rate_lookup
    - Expected: Error rate statistics over 24-hour period
- "How many errors has the API service had recently?"
    - Should use: error_rate_lookup
    - Expected: Error count and rate for recent time window

### service_status
- "Is the payment service healthy?"
    - Should use: service_status (service_metrics)
    - Expected: Health status (healthy/degraded/down) with uptime percentage

### alert_management
- "Show me all active alerts for payment_service"
    - Should use: alert_management
    - Expected: List of alerts with severity and status
- "List all unacknowledged alerts"
    - Should use: alert_management
    - Expected: Filtered list of alerts pending acknowledgment

### log_aggregation
- "Show me ERROR logs from payment_service in the last hour"
    - Should use: log_aggregation
    - Expected: Filtered error logs with timestamps and messages
- "Search for 'timeout' errors in api_service"
    - Should use: log_aggregation
    - Expected: Logs matching timeout keyword with context

### slo_tracking
- "What's our availability SLO compliance for payment_service?"
    - Should use: slo_tracking
    - Expected: Current compliance percentage vs target with error budget
- "Check the latency SLO for auth_service this month"
    - Should use: slo_tracking
    - Expected: SLO compliance status with remaining error budget
- "What is our SLO for latency?"
    - Should use: slo_tracking
    - Expected: Current latency SLO targets and compliance status

### capacity_planning
- "Predict memory usage for payment_service over the next 30 days"
    - Should use: capacity_planning
    - Expected: Resource usage forecast with scaling recommendations
- "When will we need to scale the database?"
    - Should use: capacity_planning
    - Expected: Capacity prediction with timeline

### incident_management
- "List all open incidents for payment_service"
    - Should use: incident_management
    - Expected: Active incidents with severity and status
- "Update incident INC-123 with resolution details"
    - Should use: semantic_search
    - Expected intent: general_query (auto-corrected)

---

## KNOWLEDGE SERVER (5 Tools)

### semantic_search
- "What services are in our microservices architecture?"
    - Should use: semantic_search
    - Expected: List of services from architecture.md
- "How do I troubleshoot high latency issues?"
    - Should use: semantic_search
    - Expected: Steps from runbook_high_latency.md
- "What technology stack does the payment service use?"
    - Should use: semantic_search
    - Expected: Payment service technologies and frameworks
- "What are the availability requirements for production services?"
    - Should use: semantic_search
    - Expected: Availability SLOs and targets from policy docs
- "Describe the authentication service architecture"
    - Should use: semantic_search
    - Expected: Auth service details, tech stack, endpoints
- "Suggest documentation relevant to API authentication"
    - Should use: semantic_search
    - Expected: Related docs about auth, security, and APIs
- "What is LangGraph?"
    - Should use: semantic_search
    - Expected: LangGraph description and features from langgraph.txt
- "Tell me about Azure OpenAI models"
    - Should use: semantic_search
    - Expected: Azure OpenAI info from azure_openai.txt
- "How does FAISS vector search work?"
    - Should use: semantic_search
    - Expected: FAISS information from faiss.txt

### document_versioning
- "Show me all versions of the API documentation"
    - Should use: document_versioning
    - Expected: List of document versions with timestamps
- "What changed between v2.1 and v2.2 of the payment API docs?"
    - Should use: document_versioning
    - Expected: Diff showing changes between versions
- "Get version history for the SLO policy document"
    - Should use: document_versioning
    - Expected: Version list with authors and dates
- "Compare the current architecture doc with the previous version"
    - Should use: document_versioning
    - Expected: Version comparison with highlighted changes

### change_tracking
- "Who modified the security policy document last month?"
    - Should use: change_tracking (document_versioning)
    - Expected: List of changes with authors and timestamps
- "Show me all changes to the payment API documentation"
    - Should use: change_tracking (document_versioning)
    - Expected: Audit trail of document modifications
- "What updates were made to the runbook in the last 30 days?"
    - Should use: change_tracking (document_versioning)
    - Expected: Recent changes with contributor information
- "Track changes made by user_123 to architecture docs"
    - Should use: change_tracking (document_versioning)
    - Expected: Filtered changes by specific author

### recommendation_engine
- "What related documents should I read after the payment guide?"
    - Should use: recommendation_engine
    - Expected: Related docs about payment, security, and APIs

### knowledge_graph_query
- "What services depend on the payment_service?"
    - Should use: knowledge_graph_query
    - Expected: Dependency tree with relationships
- "Map the relationships between security concepts"
    - Should use: knowledge_graph_query
    - Expected: Knowledge graph of security-related entities

---

## UTILITY SERVER (8 Tools)

### compare_values
- "Is 150ms greater than our 100ms latency threshold?"
    - Should use: compare_values
    - Expected: Comparison result (true) with difference and ratio
- "Is the availability 99.5% meeting our 99.9% SLO?"
    - Should use: compare_values
    - Expected: Comparison result (false) with gap analysis

### percentage_difference
- "What's the percentage change from 1000 to 1200 requests?"
    - Should use: percentage_difference
    - Expected: 20% increase with absolute difference
- "How much did latency increase from 50ms to 75ms?"
    - Should use: percentage_difference
    - Expected: 50% increase calculation
- "What's the percentage change from 1000 to 1200 requests?"
    - Should use: percentage_difference
    - Expected: 20% increase with absolute difference

### time_range_calculator
- "How many minutes between 2026-03-06T00:00:00Z and 2026-03-06T01:30:00Z?"
    - Should use: time_range_calculator
    - Expected: 90 minutes duration

### statistics_summary
- "Calculate statistics for these latency values: [100, 150]"
    - Should use: statistics_summary
    - Expected: Mean, median, std dev, min, max values
- "What are the stats for error rates: [1.2, 1.5]?"
    - Should use: statistics_summary
    - Expected: Complete statistical analysis

### trend_analysis
- "Forecast the next 5 periods based on [100, 120, 140, 160, 180]"
    - Should use: trend_analysis
    - Expected: Trend direction, slope, and forecasted values

### anomaly_detection
- "Detect anomalies in [100, 105, 102, 500, 98, 103]"
    - Should use: anomaly_detection
    - Expected: Anomaly list showing 500 as outlier

### data_validation
- "Check if this email format is valid: user@example.com"
    - Should use: data_validation
    - Expected: Validation status and rule compliance
- "Clean and validate this text input"
    - Should use: data_validation
    - Expected: Text cleaning and validation

### json_yaml_parser
- "Convert this JSON to YAML: {\"timeout\": 30, \"retries\": 3}"
    - Should use: json_yaml_parser
    - Expected: YAML format conversion

---

## SYSTEM SERVER (7 Tools)

### tool_registry_lookup
- "What tools are available for capacity planning?"
    - Should use: tool_registry_lookup
    - Expected: Tool metadata for capacity_planning
- "What parameters does the service_metrics tool accept?"
    - Should use: tool_registry_lookup
    - Expected: Tool schema with input parameters

### agent_health
- "Is the planner agent healthy?"
    - Should use: agent_health
    - Expected: Agent health status with uptime percentage
- "Check the status of all agents"
    - Should use: agent_health
    - Expected: Health report for all system agents
- "When did the executor agent last run?"
    - Should use: agent_health
    - Expected: Last execution timestamp and status

### workflow_status
- "What's the status of workflow_123?"
    - Should use: workflow_status
    - Expected: Current workflow status and progress
- "Show me the current step in the active workflow"
    - Should use: workflow_status
    - Expected: Current step name and progress percentage
- "Is the incident response workflow still running?"
    - Should use: workflow_status
    - Expected: Workflow execution status

### list_mcp_servers
- "What MCP servers are available?"
    - Should use: list_mcp_servers
    - Expected: List of all servers with tool counts
- "Show me all connected servers and their status"
    - Should use: list_mcp_servers
    - Expected: Server inventory with health status
- "List the available tool servers"
    - Should use: list_mcp_servers
    - Expected: Complete server list with capabilities
- "Show me all tools in the observability server"
    - Should use: list_mcp_servers
    - Expected: List of observability tools with descriptions

### performance_profiling
- "Profile the performance of all agents"
    - Should use: performance_profiling
    - Expected: Performance metrics with bottleneck identification
- "What are the bottlenecks in the LLM component?"
    - Should use: performance_profiling
    - Expected: Bottleneck identification in the LLM component

---

## LANGUAGE SERVER (4 Tools)

### translate_text
- "Translate 'Hello world' to Spanish"
    - Should use: semantic_search
    - Expected intent: general_query (auto-corrected)
- "Convert this error message to French"
    - Should use: semantic_search
    - Expected intent: general_query (auto-corrected)
- "Translate 'Bonjour le monde' from French to English"
    - Should use: semantic_search
    - Expected intent: general_query (auto-corrected)