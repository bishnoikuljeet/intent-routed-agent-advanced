"""
SQL Validator - Multi-layer SQL validation for security and performance.
"""

import re
import json
from typing import Dict, Any, Optional
from app.core.logging import logger
from langchain_core.messages import HumanMessage


class SQLValidator:
    """Multi-layer SQL validation for database queries"""
    
    def __init__(self, llm_service=None):
        """
        Initialize SQL validator
        
        Args:
            llm_service: LLM service for semantic validation (optional)
        """
        self.llm_service = llm_service
        
        # Forbidden SQL keywords
        self.forbidden_keywords = [
            'INSERT', 'UPDATE', 'DELETE', 'DROP', 'CREATE', 
            'ALTER', 'TRUNCATE', 'GRANT', 'REVOKE', 'EXEC',
            'EXECUTE', 'CALL', 'MERGE', 'REPLACE', 'RENAME',
            'COMMENT', 'LOCK', 'UNLOCK'
        ]
        
        # SQL injection patterns
        self.injection_patterns = [
            r";\s*(DROP|DELETE|UPDATE|INSERT|CREATE|ALTER|TRUNCATE)",
            r"--\s*\w+",
            r"/\*.*\*/",
            r"UNION\s+SELECT",
            r"OR\s+1\s*=\s*1",
            r"OR\s+'1'\s*=\s*'1'",
            r"'\s*OR\s+'",
            r"xp_cmdshell",
            r"INTO\s+OUTFILE",
            r"INTO\s+DUMPFILE",
            r"LOAD_FILE",
            r"BENCHMARK\s*\(",
            r"SLEEP\s*\(",
            r"WAITFOR\s+DELAY"
        ]
    
    async def validate(
        self, 
        sql: str, 
        database: str, 
        schema: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Validate SQL query with multiple layers
        
        Args:
            sql: SQL query to validate
            database: Target database name
            schema: Database schema metadata (optional)
            
        Returns:
            Validation result dictionary with 'passed', 'reason', 'suggestion'
        """
        
        # Layer 1: Read-only check
        result = self._check_read_only(sql)
        if not result["passed"]:
            return result
        
        # Layer 2: LIMIT clause check
        result = self._check_limit_clause(sql)
        if not result["passed"]:
            return result
        
        # Layer 3: Forbidden keywords
        result = self._check_forbidden_keywords(sql)
        if not result["passed"]:
            return result
        
        # Layer 4: SQL injection patterns
        result = self._check_injection_patterns(sql)
        if not result["passed"]:
            return result
        
        # Layer 5: Schema validation (if schema provided)
        if schema:
            result = self._check_schema_validity(sql, schema)
            if not result["passed"]:
                return result
        
        # Layer 6: Join complexity
        result = self._check_join_complexity(sql)
        if not result["passed"]:
            return result
        
        # Layer 7: LLM security review (if LLM service available)
        # Skip for aggregation queries as they are inherently safe
        sql_upper = sql.upper()
        aggregation_functions = ['COUNT(', 'SUM(', 'AVG(', 'MAX(', 'MIN(']
        is_aggregation = any(func in sql_upper for func in aggregation_functions)
        
        if self.llm_service and not is_aggregation:
            try:
                result = await self._llm_security_review(sql, database)
                if not result["passed"]:
                    return result
            except Exception as e:
                logger.warning(f"LLM security review failed: {e}")
                # Continue - don't fail validation if LLM review fails
        
        return {
            "passed": True,
            "safe": True,
            "reason": "All validation checks passed"
        }
    
    def _check_read_only(self, sql: str) -> Dict[str, Any]:
        """Check if query is read-only (SELECT only)"""
        sql_upper = sql.strip().upper()
        
        if not sql_upper.startswith('SELECT'):
            return {
                "passed": False,
                "reason": "Only SELECT queries are allowed",
                "suggestion": "Use SELECT statement to retrieve data"
            }
        
        return {"passed": True}
    
    def _check_limit_clause(self, sql: str) -> Dict[str, Any]:
        """Check for LIMIT clause to prevent large result sets"""
        sql_upper = sql.upper()
        
        # Skip LIMIT check for aggregation queries (COUNT, SUM, AVG, MAX, MIN)
        aggregation_functions = ['COUNT(', 'SUM(', 'AVG(', 'MAX(', 'MIN(']
        is_aggregation = any(func in sql_upper for func in aggregation_functions)
        
        if not is_aggregation and 'LIMIT' not in sql_upper:
            return {
                "passed": False,
                "reason": "Query must include LIMIT clause to prevent large result sets",
                "suggestion": "Add LIMIT clause (e.g., LIMIT 100)"
            }
        
        # Extract limit value if present
        limit_match = re.search(r'LIMIT\s+(\d+)', sql_upper)
        if limit_match:
            limit_value = int(limit_match.group(1))
            if limit_value > 1000:
                return {
                    "passed": False,
                    "reason": f"LIMIT value {limit_value} exceeds maximum of 1000",
                    "suggestion": "Reduce LIMIT to 1000 or less"
                }
        
        return {"passed": True}
    
    def _check_forbidden_keywords(self, sql: str) -> Dict[str, Any]:
        """Check for forbidden SQL keywords"""
        sql_upper = sql.upper()
        
        for keyword in self.forbidden_keywords:
            if keyword in sql_upper:
                return {
                    "passed": False,
                    "reason": f"Forbidden SQL keyword detected: {keyword}",
                    "suggestion": "Only SELECT queries are allowed for data retrieval"
                }
        
        return {"passed": True}
    
    def _check_injection_patterns(self, sql: str) -> Dict[str, Any]:
        """Check for SQL injection patterns"""
        
        for pattern in self.injection_patterns:
            if re.search(pattern, sql, re.IGNORECASE):
                return {
                    "passed": False,
                    "reason": f"Potential SQL injection pattern detected: {pattern}",
                    "suggestion": "Query contains suspicious patterns that may indicate SQL injection"
                }
        
        return {"passed": True}
    
    def _check_schema_validity(self, sql: str, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Validate SQL against database schema"""
        
        try:
            # Extract table names from SQL
            tables = self._extract_tables(sql)
            
            # Check if tables exist in schema
            schema_tables = schema.get('tables', {})
            for table in tables:
                if table.lower() not in [t.lower() for t in schema_tables.keys()]:
                    return {
                        "passed": False,
                        "reason": f"Table '{table}' does not exist in database schema",
                        "suggestion": f"Available tables: {', '.join(schema_tables.keys())}"
                    }
            
            return {"passed": True}
            
        except Exception as e:
            logger.warning(f"Schema validation error: {e}")
            # Don't fail validation if schema check fails
            return {"passed": True}
    
    def _check_join_complexity(self, sql: str) -> Dict[str, Any]:
        """Check for excessive join complexity"""
        
        sql_upper = sql.upper()
        
        # Count JOINs
        join_count = sql_upper.count('JOIN')
        if join_count > 5:
            return {
                "passed": False,
                "reason": f"Query has {join_count} JOINs, maximum allowed is 5",
                "suggestion": "Simplify query or split into multiple queries"
            }
        
        # Count subqueries
        subquery_count = sql_upper.count('SELECT') - 1  # Subtract main SELECT
        if subquery_count > 3:
            return {
                "passed": False,
                "reason": f"Query has {subquery_count} subqueries, maximum allowed is 3",
                "suggestion": "Simplify query or use temporary results"
            }
        
        return {"passed": True}
    
    def _extract_tables(self, sql: str) -> list:
        """Extract table names from SQL query"""
        
        # Simple regex-based extraction
        # Matches: FROM table, JOIN table
        pattern = r'(?:FROM|JOIN)\s+([a-zA-Z_][a-zA-Z0-9_]*)'
        matches = re.findall(pattern, sql, re.IGNORECASE)
        
        return list(set(matches))
    
    async def _llm_security_review(self, sql: str, database: str) -> Dict[str, Any]:
        """Use LLM to review SQL for security and performance issues"""
        
        prompt = f"""Analyze this SQL query for security and safety issues:

Database: {database}
Query: {sql}

Check for:
1. SQL injection attempts or suspicious patterns
2. Security risks (unauthorized data access, data modification attempts)
3. Logic errors or unusual patterns

IMPORTANT RULES:
- COUNT, SUM, AVG, MAX, MIN queries are SAFE even without WHERE clauses
- Aggregation queries that return a single value are LOW RISK
- Only flag performance issues for queries that return multiple rows without LIMIT
- Full table scans are ACCEPTABLE for aggregation queries

Respond with JSON only:
{{
    "safe": true/false,
    "issues": ["list of issues if any"],
    "risk_level": "low/medium/high",
    "recommendation": "suggestion if issues found"
}}

If the query is safe and well-formed, respond with {{"safe": true, "issues": [], "risk_level": "low"}}.
"""
        
        try:
            response = await self.llm_service.llm.ainvoke([
                HumanMessage(content=prompt)
            ])
            
            # Extract JSON from response
            content = response.content.strip()
            
            # Try to find JSON in response
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                content = json_match.group(0)
            
            result = json.loads(content)
            
            if not result.get("safe", True):
                return {
                    "passed": False,
                    "reason": f"LLM security review failed: {', '.join(result.get('issues', []))}",
                    "suggestion": result.get("recommendation", "Review and modify query")
                }
            
            if result.get("risk_level") == "high":
                return {
                    "passed": False,
                    "reason": "High-risk query detected by LLM review",
                    "suggestion": result.get("recommendation", "Query poses security risks")
                }
            
            return {"passed": True}
            
        except json.JSONDecodeError as e:
            logger.error(f"LLM security review JSON parse error: {e}")
            # Fail safe: reject on parse error
            return {
                "passed": False,
                "reason": "LLM security review could not parse response",
                "suggestion": "Query validation failed"
            }
        except Exception as e:
            logger.error(f"LLM security review failed: {e}")
            # Don't fail validation if LLM review fails
            raise
