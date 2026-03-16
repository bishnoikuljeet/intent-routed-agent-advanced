"""
Task prompts - Specific instructions for different tasks.
Token-optimized and structured with strict output schemas.
"""

class TaskPrompts:
    """Centralized task prompts for specific operations."""
    
    @staticmethod
    def context_inference(query: str, tools_summary: str, recent_context: str = "") -> str:
        """
        Prompt for LLM-powered context inference.
        Token-optimized: sends tool summaries, not full schemas.
        """
        context_section = f"\nRecent Context:\n{recent_context}\n" if recent_context else ""
        
        return f"""Analyze this query and determine the best tool to use.

Query: "{query}"{context_section}
Available Tools (name: description):
{tools_summary}

Task:
1. Determine if you can handle this query with available tools
2. If yes, select the most appropriate tool
3. Extract required parameters from the query
4. Assess confidence in your selection

Output JSON only:
{{
    "can_handle": true/false,
    "selected_tool": "tool_name" or null,
    "parameters": {{"param": "value"}},
    "confidence": 0.0-1.0,
    "reasoning": "brief explanation",
    "needs_clarification": true/false,
    "clarification_question": "question if needed"
}}"""

    @staticmethod
    def execution_planning(query: str, tools_summary: str, intent: str = "") -> str:
        """
        Prompt for execution plan generation.
        Token-optimized with compact tool representation.
        """
        intent_section = f"\nUser Intent: {intent}\n" if intent else ""
        
        return f"""Create an execution plan for this request.

Query: "{query}"{intent_section}
Available Tools:
{tools_summary}

Requirements:
1. Use only available tools
2. Extract ALL required parameters for each tool from the query
3. Check each tool's 'required' field and ensure all required params are in tool_params
4. Infer parameter values semantically from the query context
5. Identify dependencies between steps
6. Mark steps that can run in parallel
7. CRITICAL: For multi-step queries, use result references like "${{step_1.field_name}}"
   - Step 2 depends on Step 1 → Step 2 parallel_group > Step 1 parallel_group
   - Use "${{step_X.field_name}}" to pass data from previous steps
   - Examples: "${{step_1.customer_id}}", "${{step_1.order_id}}", "${{step_1.product_id}}"

TOOL SELECTION STRATEGY:
1. Read the user's intent and query carefully
2. For each available tool, analyze its description to understand what it does
3. Match the tool's capability to what the query is asking for
4. Select tools whose descriptions semantically align with the query goal
5. CRITICAL: Match based on semantic meaning, not keyword matching
   - If query asks about "documentation" or "architecture" → select tools that search/retrieve information
   - If query asks about "performance" or "metrics" → select tools that retrieve monitoring data
   - If query asks about "status" or "health" → select tools that check service state
   - If query asks to "compare" or "analyze" → select tools that perform calculations/analysis

PARAMETER EXTRACTION STRATEGY:
1. Read the selected tool's input schema to identify ALL required parameters
2. For each required parameter:
   - Use the EXACT parameter name from the tool's input schema (e.g., if schema says "values", use "values" NOT "data")
   - Extract or infer the parameter value from the query
   - Search the query for relevant information matching the parameter's purpose
   - CRITICAL: Extract values in the EXACT FORMAT specified in the parameter description
3. CRITICAL: Always use exact parameter names from the tool schema in tool_params
   - CORRECT: "values": [100, 120, 140] (if schema defines "values")
   - WRONG: "data": [100, 120, 140] (if schema defines "values")
   - CORRECT: "query": "search text" (if schema defines "query")
   - WRONG: "search_text": "search text" (if schema defines "query")
4. CRITICAL: Extract parameter VALUES in the correct format as specified in descriptions:
   - If description says "lowercase name like 'french'" → use "french" NOT "French"
   - If description says "code like 'fr'" → use "fr" NOT "FR"
   - If description has enum values → use exact enum value, case-sensitive
   - If description specifies format → follow that exact format
   - When extracting text from quotes in query → extract ONLY the content, NOT the quotes
     * Query: "Correct this text: 'Ths is a tst'" → extract "Ths is a tst" NOT "'Ths is a tst'"
     * Query: "Translate 'Hello world'" → extract "Hello world" NOT "'Hello world'"
5. Common parameter value patterns (use schema's exact names AND formats):
   - Array/list data → Extract arrays like [1,2,3] from query, use schema's exact parameter name
   - Query/search text → Use the user's question, map to schema's text parameter name
   - Entity identifiers → Extract names/IDs, map to schema's entity parameter name
   - Metric types → Infer from keywords, map to schema's metric parameter name
   - Time ranges → Infer from temporal expressions, map to schema's time parameter name
   - Numeric values → Extract numbers, map to schema's numeric parameter names
   - Language names → Convert to lowercase (e.g., "French" → "french", "English" → "english")
6. CRITICAL: For comparison/calculation tools (compare_values, percentage_difference, statistics_summary, trend_analysis):
   - If parameter values are NOT explicitly stated in the query, set them to null
   - DO NOT infer or guess numeric values for comparisons - this leads to meaningless results
   - Example: Query "compare" without values → set value1: null, value2: null
7. For other tools, you may infer reasonable parameter values from context when appropriate
8. NEVER use generic parameter names - always use the exact names from the tool's input schema

Examples (Pattern-Based):

Example 1 - Information Retrieval:
Query: "What is the process for X?"
Analysis: User wants to retrieve documented information
Tool Selection: Use semantic_search for all natural language questions about documentation
Parameter Strategy: Pass the user's question as the query parameter
Correct: Use semantic_search with query parameter
Wrong: Using monitoring/metrics tools for documentation questions

Example 2 - Data Retrieval with Multiple Parameters:
Query: "Show me the performance of component A"
Analysis: User wants performance data for a specific component
Tool Selection: Choose tool that retrieves performance/monitoring data
Parameter Strategy: 
  - Extract entity: "component A" → entity_name/resource_id parameter
  - Infer metric type: "performance" → could be latency, throughput, etc.
  - Check tool schema for ALL required parameters
Correct: Include all required parameters, infer missing ones from context
Wrong: Omitting required parameters even if not explicit in query

Example 3 - Array Data Extraction:
Query: "Forecast the next 5 periods based on [100, 120, 140, 160, 180]"
Analysis: User wants trend analysis and forecasting
Tool Selection: Choose trend_analysis tool
Tool Schema Check: 
  - Required params: "values" (array), "forecast_periods" (number)
  - NOT "data" or "numbers" - use EXACT schema names
Parameter Strategy:
  - Extract array: [100, 120, 140, 160, 180]
  - Extract forecast count: 5
  - Map to EXACT schema parameter names
Correct: {{"values": [100, 120, 140, 160, 180], "forecast_periods": 5}}
Wrong: {{"data": [100, 120, 140, 160, 180], "periods": 5}}
Why wrong: Used "data" instead of schema's "values", used "periods" instead of "forecast_periods"

Example 4 - Text Correction with Quote Stripping:
Query: "Correct this text: 'Ths is a tst'"
Analysis: User wants typo correction
Tool Selection: Choose correct_typos tool
Tool Schema Check:
  - Required params: "text" (string)
Parameter Strategy:
  - Extract text from query: 'Ths is a tst' (quoted in query)
  - CRITICAL: Remove surrounding quotes, extract ONLY the content
  - Text to extract: "Ths is a tst" (without the quotes)
Correct: {{"text": "Ths is a tst"}}
Wrong: {{"text": "'Ths is a tst'"}}
Why wrong: Included the quotes from the query instead of extracting just the text content

Example 5 - Language Translation with Format Requirements:
Query: "Translate 'Bonjour le monde' from French to English"
Analysis: User wants text translation between languages
Tool Selection: Choose translate_text tool
Tool Schema Check:
  - Required params: "text" (string), "target_lang" (string)
  - Optional params: "source_lang" (string)
  - Parameter descriptions specify: "lowercase name like 'french' or code like 'fr'"
Parameter Strategy:
  - Extract text: 'Bonjour le monde' → strip quotes → "Bonjour le monde"
  - Extract source language: "French" → convert to lowercase → "french"
  - Extract target language: "English" → convert to lowercase → "english"
  - Follow format specified in parameter description
Correct: {{"text": "Bonjour le monde", "source_lang": "french", "target_lang": "english"}}
Wrong: {{"text": "'Bonjour le monde'", "source_lang": "French", "target_lang": "English"}}
Why wrong: Included quotes AND used capitalized language names

Example 6 - Multi-Step Database Queries:
Query: "Show me orders for customer Acme Corporation"
Analysis: User wants customer orders, but needs customer_id first
Tool Selection: 2-step process - find customer, then get orders
Step 1: search_customers to find customer_id for "Acme Corporation"
Step 2: get_customer_orders using the customer_id from step 1
Parameter Strategy:
  - Step 1: Extract customer_name "Acme Corporation" → search_customers.customer_name
  - Step 2: Use result from step 1 → get_customer_orders.customer_id = "${{step_1.customer_id}}"
Correct: [
  {{"step_number": 1, "tool_name": "search_customers", "tool_params": {{"customer_name": "Acme Corporation"}}, "parallel_group": 1}},
  {{"step_number": 2, "tool_name": "get_customer_orders", "tool_params": {{"customer_id": "${{step_1.customer_id}}"}}, "parallel_group": 2}}
]
Wrong: [
  {{"step_number": 1, "tool_name": "search_customers", "tool_params": {{"customer_name": "Acme Corporation"}}, "parallel_group": 1}},
  {{"step_number": 2, "tool_name": "get_customer_orders", "tool_params": {{"customer_id": "customer_id"}}, "parallel_group": 2}}
]
Why wrong: Used literal string "customer_id" instead of reference to step 1 result

Example 7 - Semantic Tool Matching:
Query: "Compare X and Y"
Analysis: User wants comparison/analysis
Tool Selection: Match query intent to tool capability
  - Read each tool's description
  - Select tool that performs comparisons, calculations, or analysis
  - Avoid tools designed for retrieval or monitoring
Parameter Strategy: Extract entities X and Y, map to tool's EXACT parameter names from schema
Correct: Match tool capability to query goal semantically AND use exact schema parameter names
Wrong: Selecting tools based on keyword matching alone OR using generic parameter names

Output JSON only:
{{
    "reasoning": "brief plan explanation",
    "steps": [
        {{
            "step_number": 1,
            "description": "what this does",
            "tool_name": "exact_tool_name",
            "tool_params": {{"all_required_params": "with_values"}},
            "parallel_group": 1,
            "depends_on": []
        }}
    ],
    "estimated_duration": 1.0,
    "requires_parallel": false
}}"""

    @staticmethod
    def response_formatting(query: str, tool_results: str) -> str:
        """
        Prompt for natural response generation.
        Token-optimized: compact result representation.
        """
        return f"""Format a natural response for the user.

Query: "{query}"

Tool Results:
{tool_results}

Requirements:
1. Answer the user's question directly
2. Present key information clearly
3. Use natural, conversational language
4. Avoid technical jargon and tool names
5. Be concise but complete

Output: Natural language response only (no JSON)."""

    @staticmethod
    def response_type_detection(query: str, results_summary: str) -> str:
        """
        Prompt for response type determination.
        Token-optimized with result summary.
        """
        return f"""Determine the best response format type.

Query: "{query}"
Results Summary: {results_summary}

Choose ONE type:
- comparison: comparing values/items
- calculation: numerical computations
- metrics: measurements/statistics
- search: lookup/retrieval results
- default: general information

Output: Type name only (one word)."""

    @staticmethod
    def accuracy_assessment(response: str, tool_results: str) -> str:
        """
        Prompt for accuracy scoring.
        Strict numeric output.
        """
        return f"""Assess response accuracy against tool results.

Tool Results:
{tool_results}

Response:
"{response}"

Evaluate:
1. Does response accurately reflect results?
2. Are key values correct?
3. Is information factually accurate?

Output: Single number 0.0-1.0 only (e.g., 0.85)."""

    @staticmethod
    def relevance_assessment(query: str, response: str) -> str:
        """
        Prompt for relevance scoring.
        Strict numeric output.
        """
        return f"""Assess response relevance to query.

Query: "{query}"
Response: "{response}"

Evaluate:
1. Does it answer the question?
2. Is information relevant?
3. Does it address user's need?

Output: Single number 0.0-1.0 only (e.g., 0.90)."""

    @staticmethod
    def completeness_check(query: str, tools_summary: str) -> str:
        """
        Prompt for query completeness assessment.
        LLM reasoning instead of word count rules.
        """
        return f"""Assess if this query has sufficient information.

Query: "{query}"

Available Tools:
{tools_summary}

Evaluate:
1. Is the query specific enough?
2. Are required parameters present or inferable?
3. Can this be executed with available tools?
4. IMPORTANT: If query_database tool is available, natural language questions about data are COMPLETE - the tool converts natural language to SQL automatically.

DYNAMIC COMPLETENESS ASSESSMENT:

1. ENTITY RECOGNITION:
   - Identify if query contains extractable entities (names, IDs, dates, locations)
   - Any mention of specific items makes query more complete than generic requests

2. TOOL REQUIREMENT ANALYSIS:
   - Check if query provides enough information to determine tool category
   - Look for intent indicators: "find", "show", "list", "details", "summary"
   - Verify at least one searchable parameter is present

3. PARAMETER INFERENCE RULES:
   - Descriptive names (customer names, product names) are SUFFICIENT
   - Natural language dates are SUFFICIENT - system can parse and convert
   - Order identifiers in any format are SUFFICIENT - system can normalize
   - Locations and territories are SUFFICIENT - can be used directly
   - CRITICAL: Tools with DEFAULT values are COMPLETE if only required params are provided
     * anomaly_detection: Only "values" required (sensitivity/method have defaults)
     * data_validation: Only "data" required (rules/strict_mode have defaults)
     * translate_text: Only "text" and "target_lang" required (source_lang has default)

4. MULTI-STEP COMPLETENESS:
   - Query is COMPLETE if it provides enough information for the FIRST step
   - Missing secondary parameters (like specific IDs) are acceptable
   - System can chain tools to resolve missing information

5. CONTEXT COMPLETENESS:
   - Domain-specific queries (sales, orders, customers) are inherently complete
   - User intent is clear even if exact parameters need extraction
   - Database queries benefit from permissive completeness

6. GENERAL PRINCIPLE:
   - When in doubt, mark as COMPLETE for database queries
   - Prefer action over clarification when intent is clear
   - Let the execution layer handle parameter extraction and validation
   - For database_query intent, assume completeness unless query is completely vague
   - ANY mention of customer, product, order, or sales should be marked COMPLETE

7. SPECIFIC EXAMPLES:
   - "Detect anomalies in [100, 105, 102, 500, 98, 103]" → COMPLETE
     * Has required "values" parameter (the array)
     * sensitivity/method have defaults (2.0, "zscore")
     * Should NOT ask for clarification
   - "Calculate statistics for [1, 2, 3]" → COMPLETE  
     * Has required "values" parameter
     * Other parameters are optional
   - "Translate 'Hello' to Spanish" → COMPLETE
     * Has required "text" and "target_lang" 
     * source_lang has default

Output JSON only:
{{
    "is_complete": true/false,
    "confidence": 0.0-1.0,
    "missing_info": ["item1", "item2"],
    "reasoning": "brief explanation",
    "suggested_clarification": "question if incomplete"
}}"""

    @staticmethod
    def semantic_similarity(text1: str, text2: str) -> str:
        """
        Prompt for semantic similarity assessment.
        Replaces word overlap calculations.
        """
        return f"""Assess semantic similarity between these texts.

Text 1: "{text1}"
Text 2: "{text2}"

Evaluate:
1. Do they discuss the same topic?
2. Is the meaning similar?
3. Are they semantically related?

Output: Single number 0.0-1.0 only (e.g., 0.75)."""

    @staticmethod
    def minimal_plan_generation(query: str, tools_summary: str) -> str:
        """
        Prompt for minimal fallback plan.
        Used when normal planning fails.
        """
        return f"""Generate a minimal execution plan.

Query: "{query}"

Available Tools:
{tools_summary}

Create the simplest possible plan that could help.
Use only available tools.

Output JSON only:
{{
    "reasoning": "why this minimal plan",
    "steps": [
        {{
            "step_number": 1,
            "description": "step description",
            "tool_name": "actual_tool_name",
            "tool_params": {{}},
            "parallel_group": 1,
            "depends_on": []
        }}
    ],
    "estimated_duration": 1.0,
    "requires_parallel": false
}}"""

    @staticmethod
    def tool_capability_matching(query: str, tool_name: str, tool_description: str) -> str:
        """
        Prompt for assessing if a tool can handle a query.
        Semantic matching instead of keyword matching.
        """
        return f"""Can this tool handle the query?

Query: "{query}"
Tool: {tool_name}
Description: {tool_description}

Evaluate:
1. Does the tool's capability match the need?
2. Can it accomplish what's requested?
3. Is it semantically relevant?

Output JSON only:
{{
    "can_handle": true/false,
    "confidence": 0.0-1.0,
    "reasoning": "brief explanation"
}}"""

    @staticmethod
    def parameter_extraction(query: str, tool_schema: str) -> str:
        """
        Prompt for extracting parameters from query.
        Schema-aware extraction.
        """
        return f"""Extract parameters for this tool from the query.

Query: "{query}"

Tool Parameter Schema:
{tool_schema}

Task:
1. Identify parameter values in the query
2. Infer implicit parameters from context
3. Mark missing required parameters

Output JSON only:
{{
    "extracted_params": {{"param": "value"}},
    "confidence": 0.0-1.0,
    "missing_required": ["param1"],
    "reasoning": "brief explanation"
}}"""
