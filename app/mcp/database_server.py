"""
Database MCP Server - Exposes database operations as MCP tools.
"""

from app.mcp.base import BaseMCPServer, MCPTool
from app.database.sql_templates import SQLTemplateRegistry
from app.database.sql_validator import SQLValidator
from app.database.sql_generator import SQLGenerator
from app.database.connection_manager import DatabaseConnectionManager
from typing import Dict, Any, Optional
from app.core.logging import logger
from decimal import Decimal
from datetime import date, datetime


class DatabaseMCPServer(BaseMCPServer):
    """Database MCP Server - Provides database query tools"""
    
    def __init__(self, llm_service=None, rag_retriever=None):
        """
        Initialize Database MCP Server
        
        Args:
            llm_service: LLM service for SQL generation and validation
            rag_retriever: RAG retriever for schema documentation lookup
        """
        self.connection_manager = DatabaseConnectionManager()
        self.template_registry = SQLTemplateRegistry()
        self.sql_validator = SQLValidator(llm_service=llm_service)
        self.sql_generator = SQLGenerator(llm_service=llm_service) if llm_service else None
        self.llm_service = llm_service
        self.rag_retriever = rag_retriever
        
        super().__init__("database")
    
    def configure_databases(self, sales_config: Dict[str, Any], inventory_config: Dict[str, Any]):
        """
        Configure database connections
        
        Args:
            sales_config: Sales database configuration
            inventory_config: Inventory database configuration
        """
        self.connection_manager.configure_database(
            database="sales",
            **sales_config
        )
        
        self.connection_manager.configure_database(
            database="inventory",
            **inventory_config
        )
    
    def _initialize(self):
        """Register all database tools"""
        
        # SALES DATABASE TOOLS
        
        self.register_tool(MCPTool(
            name="get_order_details",
            description="Retrieve complete order information including customer, line items, and sales rep. Use for queries about specific order numbers like 'SO-2024-001'. Returns order header, customer details, line items with products, pricing, and sales representative information.",
            input_schema={
                "type": "object",
                "properties": {
                    "order_number": {
                        "type": "string",
                        "description": "Order number in format SO-YYYY-NNN (e.g., SO-2024-001)"
                    }
                },
                "required": ["order_number"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "success": {"type": "boolean"},
                    "order_id": {"type": "integer"},
                    "customer_id": {"type": "integer"},
                    "order_number": {"type": "string"},
                    "order_date": {"type": "string"},
                    "customer_name": {"type": "string"},
                    "total_amount": {"type": "number"},
                    "status": {"type": "string"},
                    "line_items": {"type": "array"},
                    "error": {"type": "string"},
                    "error_type": {"type": "string"}
                }
            },
            handler=self._get_order_details
        ))
        
        self.register_tool(MCPTool(
            name="search_customers",
            description="Search and filter customers by name, territory, or type. Supports partial name matching. Use for queries like 'customers in Northeast', 'enterprise customers', or 'find customer Acme'. Returns customer list with contact information and assigned sales representatives.",
            input_schema={
                "type": "object",
                "properties": {
                    "customer_name": {
                        "type": "string",
                        "description": "Customer name (partial match supported)"
                    },
                    "territory": {
                        "type": "string",
                        "description": "Sales territory (Northeast, Southeast, Midwest, West, Southwest)"
                    },
                    "customer_type": {
                        "type": "string",
                        "description": "Customer type (enterprise, mid-market, small-business)"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum results to return (default 50, max 100)",
                        "default": 50
                    }
                },
                "required": []
            },
            output_schema={
                "type": "object",
                "properties": {
                    "success": {"type": "boolean"},
                    "customers": {"type": "array"},
                    "total_count": {"type": "integer"}
                }
            },
            handler=self._search_customers
        ))
        
        self.register_tool(MCPTool(
            name="get_sales_summary",
            description="Get sales summary and statistics for a date range. Can be filtered by sales rep or customer. Use for queries like 'sales in March 2024', 'total sales by rep', or 'sales for customer X'. Returns total sales, order count, and average order value.",
            input_schema={
                "type": "object",
                "properties": {
                    "start_date": {
                        "type": "string",
                        "description": "Start date in YYYY-MM-DD format",
                        "format": "date"
                    },
                    "end_date": {
                        "type": "string",
                        "description": "End date in YYYY-MM-DD format",
                        "format": "date"
                    },
                    "rep_id": {
                        "type": "integer",
                        "description": "Filter by sales representative ID"
                    },
                    "customer_id": {
                        "type": "integer",
                        "description": "Filter by customer ID"
                    }
                },
                "required": ["start_date", "end_date"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "success": {"type": "boolean"},
                    "total_sales": {"type": "number"},
                    "order_count": {"type": "integer"},
                    "average_order_value": {"type": "number"}
                }
            },
            handler=self._get_sales_summary
        ))
        
        self.register_tool(MCPTool(
            name="get_customer_orders",
            description="Get all orders for a specific customer. Use when you have customer_id from a previous query. Returns list of orders with basic information.",
            input_schema={
                "type": "object",
                "properties": {
                    "customer_id": {
                        "type": "integer",
                        "description": "Customer ID"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum orders to return (default 50)",
                        "default": 50
                    }
                },
                "required": ["customer_id"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "success": {"type": "boolean"},
                    "orders": {"type": "array"},
                    "total_count": {"type": "integer"}
                }
            },
            handler=self._get_customer_orders
        ))
        
        # INVENTORY DATABASE TOOLS
        
        self.register_tool(MCPTool(
            name="get_low_stock_items",
            description="Find inventory items with stock below reorder point or custom threshold. Use for queries like 'low stock products', 'items to reorder', or 'inventory below 50 units'. Returns items that need restocking with current quantities and reorder information.",
            input_schema={
                "type": "object",
                "properties": {
                    "threshold": {
                        "type": "integer",
                        "description": "Stock threshold (if not provided, uses reorder_point)"
                    },
                    "category_id": {
                        "type": "integer",
                        "description": "Filter by product category ID"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum results (default 50, max 100)",
                        "default": 50
                    }
                },
                "required": []
            },
            output_schema={
                "type": "object",
                "properties": {
                    "success": {"type": "boolean"},
                    "items": {"type": "array"},
                    "total_count": {"type": "integer"}
                }
            },
            handler=self._get_low_stock_items
        ))
        
        self.register_tool(MCPTool(
            name="search_inventory",
            description="Search inventory items by SKU, name, or category. Supports partial matching. Use for queries like 'find product PROD-A100', 'items in Hardware category', or 'search for laptop'. Returns matching inventory items with stock levels and supplier information.",
            input_schema={
                "type": "object",
                "properties": {
                    "sku": {
                        "type": "string",
                        "description": "Product SKU (partial match supported)"
                    },
                    "item_name": {
                        "type": "string",
                        "description": "Item name (partial match supported)"
                    },
                    "category_id": {
                        "type": "integer",
                        "description": "Filter by category ID"
                    },
                    "limit": {
                        "type": "integer",
                        "default": 50
                    }
                },
                "required": []
            },
            output_schema={
                "type": "object",
                "properties": {
                    "success": {"type": "boolean"},
                    "items": {"type": "array"},
                    "total_count": {"type": "integer"}
                }
            },
            handler=self._search_inventory
        ))
        
        # DYNAMIC SQL TOOL
        
        if self.sql_generator:
            self.register_tool(MCPTool(
                name="query_database",
                description="Execute custom database query for complex data retrieval not covered by specific tools. LLM generates and validates SQL based on natural language description. Use ONLY when specific tools don't match the requirement. Supports both sales and inventory databases.",
                input_schema={
                    "type": "object",
                    "properties": {
                        "database": {
                            "type": "string",
                            "description": "Target database name",
                            "enum": ["sales", "inventory"]
                        },
                        "query_description": {
                            "type": "string",
                            "description": "Natural language description of what data to retrieve"
                        },
                        "filters": {
                            "type": "object",
                            "description": "Optional key-value filters to apply",
                            "additionalProperties": True
                        }
                    },
                    "required": ["database", "query_description"]
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "success": {"type": "boolean"},
                        "results": {"type": "array"},
                        "row_count": {"type": "integer"},
                        "sql_executed": {"type": "string"}
                    }
                },
                handler=self._query_database
            ))
    
    def _serialize_value(self, value):
        """Convert database values to JSON-serializable format"""
        if isinstance(value, Decimal):
            return float(value)
        elif isinstance(value, (date, datetime)):
            return value.isoformat()
        return value
    
    def _serialize_row(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """Serialize a database row"""
        return {k: self._serialize_value(v) for k, v in row.items()}
    
    # Tool Handlers
    
    async def _get_order_details(self, order_number: str) -> Dict[str, Any]:
        """Get order details using fixed SQL template"""
        
        try:
            sql = self.template_registry.get_sql("get_order_details")
            
            results = await self.connection_manager.execute_query(
                database="sales",
                sql=sql,
                params=[order_number]
            )
            
            if not results:
                return {
                    "success": False,
                    "error": f"Order {order_number} not found",
                    "error_type": "not_found"
                }
            
            order = self._serialize_row(results[0])
            
            # Get line items
            line_items_sql = self.template_registry.get_sql("get_order_line_items")
            line_items = await self.connection_manager.execute_query(
                database="sales",
                sql=line_items_sql,
                params=[order["order_id"]]
            )
            
            return {
                "success": True,
                "order_id": order["order_id"],
                "customer_id": order["customer_id"],
                "order_number": order["order_number"],
                "order_date": order["order_date"],
                "customer_name": order["customer_name"],
                "customer_email": order["email"],
                "sales_rep": order["sales_rep"],
                "rep_id": order["rep_id"],
                "status": order["status"],
                "subtotal": order["subtotal"],
                "tax_amount": order["tax_amount"],
                "shipping_cost": order["shipping_cost"],
                "total_amount": order["total_amount"],
                "payment_method": order["payment_method"],
                "line_items": [self._serialize_row(item) for item in line_items]
            }
            
        except Exception as e:
            logger.error_structured(
                "Failed to get order details",
                order_number=order_number,
                error=str(e)
            )
            return {
                "success": False,
                "error": str(e),
                "error_type": "execution_failed"
            }
    
    async def _search_customers(
        self,
        customer_name: str = None,
        territory: str = None,
        customer_type: str = None,
        limit: int = None
    ) -> Dict[str, Any]:
        """Search customers using fixed SQL template"""
        
        try:
            sql = self.template_registry.get_sql("search_customers")
            
            # Ensure limit has a default value
            if limit is None:
                limit = 50
            
            # SQL template uses COALESCE pattern which requires each param twice
            results = await self.connection_manager.execute_query(
                database="sales",
                sql=sql,
                params=[
                    customer_name, customer_name,  # For LIKE check
                    territory, territory,          # For territory check
                    customer_type, customer_type,  # For type check
                    min(limit, 100)
                ]
            )
            
            return {
                "success": True,
                "customers": [self._serialize_row(row) for row in results],
                "total_count": len(results)
            }
            
        except Exception as e:
            logger.error_structured(
                "Failed to search customers",
                error=str(e)
            )
            return {
                "success": False,
                "error": str(e),
                "error_type": "execution_failed"
            }
    
    async def _get_sales_summary(
        self,
        start_date: str,
        end_date: str,
        rep_id: int = None,
        customer_id: int = None
    ) -> Dict[str, Any]:
        """Get sales summary using fixed SQL template"""
        
        try:
            sql = self.template_registry.get_sql("get_sales_summary")
            
            # SQL template uses COALESCE pattern which requires each param twice
            results = await self.connection_manager.execute_query(
                database="sales",
                sql=sql,
                params=[
                    start_date, end_date,
                    rep_id, rep_id,              # For rep_id check
                    customer_id, customer_id     # For customer_id check
                ]
            )
            
            if results:
                row = self._serialize_row(results[0])
                return {
                    "success": True,
                    "total_sales": row["total_sales"],
                    "order_count": row["order_count"],
                    "average_order_value": row["average_order_value"],
                    "start_date": start_date,
                    "end_date": end_date
                }
            else:
                return {
                    "success": True,
                    "total_sales": 0.0,
                    "order_count": 0,
                    "average_order_value": 0.0,
                    "start_date": start_date,
                    "end_date": end_date
                }
                
        except Exception as e:
            logger.error_structured(
                "Failed to get sales summary",
                error=str(e)
            )
            return {
                "success": False,
                "error": str(e),
                "error_type": "execution_failed"
            }
    
    async def _get_customer_orders(
        self,
        customer_id: int,
        limit: int = None
    ) -> Dict[str, Any]:
        """Get customer orders using fixed SQL template"""
        
        try:
            sql = self.template_registry.get_sql("get_customer_orders")
            
            # Ensure limit has a default value
            if limit is None:
                limit = 50
            
            results = await self.connection_manager.execute_query(
                database="sales",
                sql=sql,
                params=[customer_id, min(limit, 100)]
            )
            
            return {
                "success": True,
                "orders": [self._serialize_row(row) for row in results],
                "total_count": len(results)
            }
            
        except Exception as e:
            logger.error_structured(
                "Failed to get customer orders",
                customer_id=customer_id,
                error=str(e)
            )
            return {
                "success": False,
                "error": str(e),
                "error_type": "execution_failed"
            }
    
    async def _get_low_stock_items(
        self,
        threshold: int = None,
        category_id: int = None,
        limit: int = None
    ) -> Dict[str, Any]:
        """Get low stock items using fixed SQL template"""
        
        try:
            sql = self.template_registry.get_sql("get_low_stock_items")
            
            # Ensure limit has a default value
            if limit is None:
                limit = 50
            
            # SQL template uses COALESCE pattern: threshold appears 3 times, category_id twice
            results = await self.connection_manager.execute_query(
                database="inventory",
                sql=sql,
                params=[
                    threshold, threshold, threshold,  # For threshold checks
                    category_id, category_id,         # For category_id check
                    min(limit, 100)
                ]
            )
            
            return {
                "success": True,
                "items": [self._serialize_row(row) for row in results],
                "total_count": len(results)
            }
            
        except Exception as e:
            logger.error_structured(
                "Failed to get low stock items",
                error=str(e)
            )
            return {
                "success": False,
                "error": str(e),
                "error_type": "execution_failed"
            }
    
    async def _search_inventory(
        self,
        sku: str = None,
        item_name: str = None,
        category_id: int = None,
        limit: int = None
    ) -> Dict[str, Any]:
        """Search inventory using fixed SQL template"""
        
        try:
            sql = self.template_registry.get_sql("search_inventory")
            
            # Ensure limit has a default value
            if limit is None:
                limit = 50
            
            # SQL template uses COALESCE pattern which requires each param twice
            results = await self.connection_manager.execute_query(
                database="inventory",
                sql=sql,
                params=[
                    sku, sku,                    # For SKU LIKE check
                    item_name, item_name,        # For item_name LIKE check
                    category_id, category_id,    # For category_id check
                    min(limit, 100)
                ]
            )
            
            return {
                "success": True,
                "items": [self._serialize_row(row) for row in results],
                "total_count": len(results)
            }
            
        except Exception as e:
            logger.error_structured(
                "Failed to search inventory",
                error=str(e)
            )
            return {
                "success": False,
                "error": str(e),
                "error_type": "execution_failed"
            }
    
    async def _query_database(
        self,
        database: str,
        query_description: str,
        filters: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Execute dynamic SQL query with LLM generation and validation"""
        
        if not self.sql_generator:
            return {
                "success": False,
                "error": "Dynamic SQL generation not available (LLM service not configured)",
                "error_type": "configuration_error"
            }
        
        try:
            # Get schema from database
            schema = await self.connection_manager.get_schema(database)
            
            # Enhance schema with RAG documentation if available
            schema_context = ""
            if self.rag_retriever:
                try:
                    # Search for relevant schema documentation
                    rag_results = await self.rag_retriever.search(
                        query=f"{database} database schema tables columns {query_description}",
                        k=3
                    )
                    
                    # Filter for database schema documents
                    schema_docs = [
                        doc for doc in rag_results 
                        if doc.get("metadata", {}).get("type") == "database_schema"
                        and database in doc.get("metadata", {}).get("category", "")
                    ]
                    
                    if schema_docs:
                        schema_context = "\n\n".join([doc["content"] for doc in schema_docs])
                        logger.info_structured(
                            "Retrieved schema documentation from RAG",
                            database=database,
                            docs_found=len(schema_docs)
                        )
                except Exception as rag_error:
                    logger.warning_structured(
                        "Failed to retrieve schema from RAG, continuing with basic schema",
                        error=str(rag_error)
                    )
            
            # Add schema context to schema dict
            if schema_context:
                schema["documentation"] = schema_context
            
            # Generate SQL using LLM
            sql_result = await self.sql_generator.generate(
                database=database,
                description=query_description,
                filters=filters or {},
                schema=schema
            )
            
            if not sql_result["valid"]:
                return {
                    "success": False,
                    "error": f"SQL generation failed: {sql_result['reason']}",
                    "error_type": "validation_failed"
                }
            
            sql = sql_result["sql"]
            
            # Validate SQL
            validation = await self.sql_validator.validate(
                sql=sql,
                database=database,
                schema=schema
            )
            
            if not validation["passed"]:
                return {
                    "success": False,
                    "error": f"SQL validation failed: {validation['reason']}",
                    "suggestion": validation.get("suggestion", ""),
                    "error_type": "validation_failed"
                }
            
            # Execute
            results = await self.connection_manager.execute_query(
                database=database,
                sql=sql,
                params=None  # Parameters already embedded in generated SQL
            )
            
            return {
                "success": True,
                "results": [self._serialize_row(row) for row in results],
                "row_count": len(results),
                "sql_executed": sql,
                "query_description": query_description
            }
            
        except Exception as e:
            logger.error_structured(
                "Dynamic query failed",
                database=database,
                description=query_description,
                error=str(e)
            )
            return {
                "success": False,
                "error": str(e),
                "error_type": "execution_failed"
            }
