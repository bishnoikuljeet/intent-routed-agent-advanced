import re
from pathlib import Path
from typing import Dict, List, Tuple


class ExampleQueriesService:
    """Service to parse and provide example queries from sample_prompts.md"""
    
    def __init__(self, sample_prompts_path: str = None):
        if sample_prompts_path is None:
            # Default path relative to the backend directory
            self.sample_prompts_path = Path(__file__).parent.parent.parent / "sample_prompts.md"
        else:
            self.sample_prompts_path = Path(sample_prompts_path)
    
    def parse_sample_prompts(self) -> List[Dict]:
        """Parse sample_prompts.md and extract all queries with their tools and expected results"""
        queries = []
        
        try:
            with open(self.sample_prompts_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Split content by tool sections
            tool_sections = re.split(r'### ([a-zA-Z_]+)', content)
            
            current_tool = None
            for i, section in enumerate(tool_sections):
                if i == 0:  # Skip the header part
                    continue
                
                if i % 2 == 1:  # This is a tool name
                    current_tool = section.strip()
                else:  # This is the content for the tool
                    if current_tool and current_tool != "normalize_text":  # Skip empty sections
                        # Extract queries from this section
                        section_queries = self._extract_queries_from_section(section, current_tool)
                        queries.extend(section_queries)
        
        except FileNotFoundError:
            print(f"Warning: sample_prompts.md not found at {self.sample_prompts_path}")
            return []
        except Exception as e:
            print(f"Error parsing sample_prompts.md: {e}")
            return []
        
        return queries
    
    def _extract_queries_from_section(self, section: str, tool: str) -> List[Dict]:
        """Extract queries from a tool section"""
        queries = []
        
        # Find all query blocks
        query_pattern = r'- "([^"]+)"\s*\n\s*- Should use: ([^\n]+)\s*\n\s*- Expected: ([^\n]+)'
        matches = re.findall(query_pattern, section)
        
        for match in matches:
            query_text = match[0].strip()
            should_use = match[1].strip()
            expected = match[2].strip()
            
            # Determine the intent based on the tool and expected result
            intent = self._determine_intent(tool, should_use, expected)
            
            queries.append({
                "query": query_text,
                "tool": tool,
                "should_use": should_use,
                "expected": expected,
                "intent": intent
            })
        
        return queries
    
    def _determine_intent(self, tool: str, should_use: str, expected: str) -> str:
        """Determine intent based on tool and expected result"""
        # Map tools to intents
        tool_intent_map = {
            "service_metrics": "metrics_lookup",
            "latency_history": "metrics_lookup", 
            "error_rate_lookup": "metrics_lookup",
            "service_status": "metrics_lookup",
            "alert_management": "metrics_lookup",
            "log_aggregation": "metrics_lookup",
            "slo_tracking": "metrics_lookup",
            "capacity_planning": "general_query",
            "incident_management": "metrics_lookup",
            "semantic_search": "knowledge_lookup",
            "document_versioning": "knowledge_lookup",
            "change_tracking": "knowledge_lookup",
            "recommendation_engine": "knowledge_lookup",
            "knowledge_graph_query": "knowledge_lookup",
            "compare_values": "calculation_compare",
            "percentage_difference": "calculation_compare",
            "time_range_calculator": "calculation_compare",
            "statistics_summary": "calculation_compare",
            "trend_analysis": "calculation_compare",
            "anomaly_detection": "calculation_compare",
            "data_validation": "data_validation",
            "json_yaml_parser": "data_validation",
            "tool_registry_lookup": "system_question",
            "agent_health": "system_question",
            "workflow_status": "system_question",
            "list_mcp_servers": "system_question",
            "performance_profiling": "system_question",
            "translate_text": "general_query",
            "detect_language": "data_validation",
            "correct_typos": "general_query",
            "normalize_text": "data_validation",
            "get_order_details": "database_query",
            "search_customers": "database_query",
            "get_sales_summary": "database_query",
            "get_customer_orders": "database_query",
            "get_low_stock_items": "database_query",
            "search_inventory": "database_query",
            "query_database": "database_query"
        }
        
        # Check if should_use contains parentheses (alternative tool)
        if "(" in should_use:
            primary_tool = should_use.split("(")[0].strip()
            if primary_tool in tool_intent_map:
                return tool_intent_map[primary_tool]
        
        # Use direct tool mapping
        if tool in tool_intent_map:
            return tool_intent_map[tool]
        
        # Fallback: try to determine from expected text
        expected_lower = expected.lower()
        if "auto-corrected" in expected_lower:
            return "general_query"
        elif any(word in expected_lower for word in ["validation", "check", "verify"]):
            return "data_validation"
        elif any(word in expected_lower for word in ["lookup", "search", "find"]):
            return "knowledge_lookup"
        elif any(word in expected_lower for word in ["calculate", "compare", "percentage"]):
            return "calculation_compare"
        else:
            return "general_query"
    
    def get_queries_by_category(self) -> Dict[str, List[Dict]]:
        """Group queries by server category"""
        queries = self.parse_sample_prompts()
        
        categories = {
            "OBSERVABILITY SERVER": [],
            "KNOWLEDGE SERVER": [],
            "UTILITY SERVER": [],
            "SYSTEM SERVER": [],
            "LANGUAGE SERVER": [],
            "DATABASE SERVER": []
        }
        
        # Categorize based on tool mapping (more reliable)
        for query in queries:
            tool = query["tool"]
            categorized = False
            
            # Skip empty sections
            if tool == "normalize_text" and not query["query"]:
                continue
            
            # Map tools to categories
            if tool in ["service_metrics", "latency_history", "error_rate_lookup", "service_status", 
                      "alert_management", "log_aggregation", "slo_tracking", "capacity_planning", 
                      "incident_management"]:
                categories["OBSERVABILITY SERVER"].append(query)
                categorized = True
            elif tool in ["semantic_search", "document_versioning", "change_tracking", 
                       "recommendation_engine", "knowledge_graph_query"]:
                categories["KNOWLEDGE SERVER"].append(query)
                categorized = True
            elif tool in ["compare_values", "percentage_difference", "time_range_calculator", 
                       "statistics_summary", "trend_analysis", "anomaly_detection", "data_validation", 
                       "json_yaml_parser"]:
                categories["UTILITY SERVER"].append(query)
                categorized = True
            elif tool in ["tool_registry_lookup", "agent_health", "workflow_status", 
                       "list_mcp_servers", "performance_profiling"]:
                categories["SYSTEM SERVER"].append(query)
                categorized = True
            elif tool in ["translate_text", "detect_language", "correct_typos", "normalize_text"]:
                categories["LANGUAGE SERVER"].append(query)
                categorized = True
            elif tool in ["get_order_details", "search_customers", "get_sales_summary", 
                       "get_customer_orders", "get_low_stock_items", "search_inventory", 
                       "query_database"]:
                categories["DATABASE SERVER"].append(query)
                categorized = True
            
            # If not categorized by tool, try to categorize by intent
            if not categorized:
                intent = query["intent"]
                if intent == "metrics_lookup":
                    categories["OBSERVABILITY SERVER"].append(query)
                elif intent == "knowledge_lookup":
                    categories["KNOWLEDGE SERVER"].append(query)
                elif intent == "calculation_compare" or intent == "data_validation":
                    categories["UTILITY SERVER"].append(query)
                elif intent == "system_question":
                    categories["SYSTEM SERVER"].append(query)
                elif intent == "database_query":
                    categories["DATABASE SERVER"].append(query)
                else:
                    # Default to knowledge server for general queries
                    categories["KNOWLEDGE SERVER"].append(query)
        
        return categories
    
    def get_all_queries(self) -> List[Dict]:
        """Get all queries as a flat list"""
        return self.parse_sample_prompts()
    
    def get_query_count(self) -> int:
        """Get total number of queries"""
        return len(self.parse_sample_prompts())
