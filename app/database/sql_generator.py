"""
SQL Generator - LLM-powered SQL generation for complex database queries.
"""

import json
import re
from typing import Dict, Any, Optional
from app.core.logging import logger
from langchain_core.messages import SystemMessage, HumanMessage


class SQLGenerator:
    """LLM-powered SQL generation with schema awareness"""
    
    def __init__(self, llm_service):
        """
        Initialize SQL generator
        
        Args:
            llm_service: LLM service for SQL generation
        """
        self.llm_service = llm_service
    
    async def generate(
        self,
        database: str,
        description: str,
        filters: Dict[str, Any],
        schema: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate SQL query using LLM with schema awareness
        
        Args:
            database: Target database name
            description: Natural language description of query
            filters: Optional filters to apply
            schema: Database schema metadata
            
        Returns:
            Dictionary with 'valid', 'sql', 'parameters', 'explanation'
        """
        
        try:
            # Build schema description
            schema_desc = self._format_schema(schema)
            
            # Build prompt
            prompt = self._build_generation_prompt(
                database=database,
                description=description,
                filters=filters,
                schema_desc=schema_desc
            )
            
            # Call LLM
            response = await self.llm_service.llm.ainvoke([
                SystemMessage(content="You are an expert SQL query generator. Generate safe, efficient, read-only SQL queries."),
                HumanMessage(content=prompt)
            ])
            
            # Parse response
            result = self._parse_llm_response(response.content)
            
            if not result["valid"]:
                return result
            
            # Basic validation
            sql = result["sql"]
            
            if not sql.strip().upper().startswith("SELECT"):
                return {
                    "valid": False,
                    "reason": "Generated query must be SELECT statement"
                }
            
            if "LIMIT" not in sql.upper():
                # Auto-add LIMIT if missing
                sql = sql.rstrip(';').strip() + " LIMIT 100"
                result["sql"] = sql
                logger.info("Auto-added LIMIT clause to generated SQL")
            
            logger.info_structured(
                "SQL generated successfully",
                database=database,
                description=description[:50]
            )
            
            return result
            
        except Exception as e:
            logger.error_structured(
                "SQL generation failed",
                error=str(e),
                database=database,
                description=description[:50]
            )
            return {
                "valid": False,
                "reason": f"SQL generation error: {str(e)}"
            }
    
    def _format_schema(self, schema: Dict[str, Any]) -> str:
        """Format schema for LLM prompt"""
        
        # Check if we have RAG documentation (preferred)
        if schema.get('documentation'):
            logger.info("Using RAG schema documentation for SQL generation")
            return schema['documentation']
        
        # Fallback to basic schema if no documentation
        if not schema or not schema.get('tables'):
            return "Schema information not available"
        
        schema_lines = []
        tables = schema.get('tables', {})
        
        for table_name, table_info in tables.items():
            schema_lines.append(f"\nTable: {table_name}")
            
            columns = table_info.get('columns', [])
            if columns:
                schema_lines.append("  Columns:")
                for col in columns:
                    col_name = col.get('name', '')
                    col_type = col.get('type', '')
                    nullable = " (nullable)" if col.get('nullable') else ""
                    schema_lines.append(f"    - {col_name}: {col_type}{nullable}")
            
            # Foreign keys
            fkeys = table_info.get('foreign_keys', [])
            if fkeys:
                schema_lines.append("  Foreign Keys:")
                for fk in fkeys:
                    schema_lines.append(f"    - {fk.get('column')} -> {fk.get('references')}")
        
        return "\n".join(schema_lines)
    
    def _build_generation_prompt(
        self,
        database: str,
        description: str,
        filters: Dict[str, Any],
        schema_desc: str
    ) -> str:
        """Build prompt for SQL generation"""
        
        filters_str = json.dumps(filters, indent=2) if filters else "None"
        
        prompt = f"""Generate a READ-ONLY SQL query for the following request:

Database: {database}
Request: {description}
Filters: {filters_str}

Database Schema:
{schema_desc}

Requirements:
1. Generate ONLY a SELECT query (no INSERT/UPDATE/DELETE/DROP/etc)
2. Include LIMIT clause (maximum 100 rows)
3. Use MySQL syntax with %s for parameter placeholders
4. Include proper JOINs based on foreign key relationships
5. Use meaningful column aliases for clarity
6. Optimize for performance (use WHERE clauses, avoid SELECT *)
7. Handle NULL values appropriately
8. Use CONCAT for string concatenation, not ||
9. Use LIKE with CONCAT('%%', value, '%%') for partial matching

Respond with JSON only:
{{
    "sql": "SELECT ... FROM ... WHERE ... LIMIT 100",
    "parameters": {{"param1": "value1", "param2": "value2"}},
    "explanation": "Brief explanation of the query logic",
    "tables_used": ["table1", "table2"]
}}

Important: 
- Use %s for parameter placeholders (MySQL style)
- Ensure all JOINs are based on actual foreign key relationships from schema
- Include only necessary columns, not SELECT *
- Always include LIMIT clause
- Use MySQL-specific functions (CONCAT, COALESCE, etc.)
"""
        
        return prompt
    
    def _parse_llm_response(self, content: str) -> Dict[str, Any]:
        """Parse LLM response and extract SQL"""
        
        try:
            # Try to extract JSON from response
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if not json_match:
                return {
                    "valid": False,
                    "reason": "Could not find JSON in LLM response"
                }
            
            json_str = json_match.group(0)
            result = json.loads(json_str)
            
            # Validate required fields
            if "sql" not in result:
                return {
                    "valid": False,
                    "reason": "LLM response missing 'sql' field"
                }
            
            return {
                "valid": True,
                "sql": result["sql"],
                "parameters": result.get("parameters", {}),
                "explanation": result.get("explanation", ""),
                "tables_used": result.get("tables_used", [])
            }
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            return {
                "valid": False,
                "reason": f"Invalid JSON in LLM response: {str(e)}"
            }
        except Exception as e:
            logger.error(f"Error parsing LLM response: {e}")
            return {
                "valid": False,
                "reason": f"Error parsing response: {str(e)}"
            }
