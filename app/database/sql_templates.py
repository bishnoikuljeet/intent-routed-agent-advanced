"""
SQL Template Registry - Pre-validated SQL templates for common database queries.
"""

from typing import Dict, Optional


class SQLTemplateRegistry:
    """Registry of pre-validated SQL templates for database operations"""
    
    def __init__(self):
        self.templates = self._initialize_templates()
    
    def _initialize_templates(self) -> Dict[str, str]:
        """Initialize all SQL templates"""
        return {
            # SALES DATABASE TEMPLATES
            
            "get_order_details": """
                SELECT 
                    so.order_id,
                    so.order_number,
                    so.order_date,
                    so.status,
                    so.subtotal,
                    so.tax_amount,
                    so.shipping_cost,
                    so.total_amount,
                    so.payment_method,
                    so.customer_id,
                    c.customer_name,
                    c.email,
                    CONCAT(sr.first_name, ' ', sr.last_name) as sales_rep,
                    sr.rep_id
                FROM sales_orders so
                JOIN customers c ON so.customer_id = c.customer_id
                JOIN sales_reps sr ON so.rep_id = sr.rep_id
                WHERE so.order_number = %s
                LIMIT 1
            """,
            
            "get_order_line_items": """
                SELECT 
                    oli.line_item_id,
                    p.product_id,
                    p.product_name,
                    p.product_code,
                    oli.quantity,
                    oli.unit_price,
                    oli.discount_percent,
                    oli.line_total
                FROM order_line_items oli
                JOIN products p ON oli.product_id = p.product_id
                WHERE oli.order_id = %s
                ORDER BY oli.line_item_id
                LIMIT 100
            """,
            
            "search_customers": """
                SELECT 
                    c.customer_id,
                    c.customer_name,
                    c.customer_type,
                    c.email,
                    c.phone,
                    c.city,
                    c.state,
                    c.credit_limit,
                    c.assigned_rep_id,
                    CONCAT(sr.first_name, ' ', sr.last_name) as sales_rep,
                    sr.territory
                FROM customers c
                LEFT JOIN sales_reps sr ON c.assigned_rep_id = sr.rep_id
                WHERE 
                    (COALESCE(%s, '') = '' OR c.customer_name LIKE CONCAT('%%', %s, '%%'))
                    AND (COALESCE(%s, '') = '' OR sr.territory = %s)
                    AND (COALESCE(%s, '') = '' OR c.customer_type = %s)
                ORDER BY c.customer_name
                LIMIT %s
            """,
            
            "get_sales_summary": """
                SELECT 
                    COALESCE(SUM(total_amount), 0) as total_sales,
                    COUNT(*) as order_count,
                    COALESCE(AVG(total_amount), 0) as average_order_value
                FROM sales_orders
                WHERE 
                    order_date BETWEEN %s AND %s
                    AND (COALESCE(%s, 0) = 0 OR rep_id = %s)
                    AND (COALESCE(%s, 0) = 0 OR customer_id = %s)
            """,
            
            "get_customer_orders": """
                SELECT 
                    so.order_id,
                    so.order_number,
                    so.order_date,
                    so.status,
                    so.total_amount
                FROM sales_orders so
                WHERE so.customer_id = %s
                ORDER BY so.order_date DESC
                LIMIT %s
            """,
            
            # INVENTORY DATABASE TEMPLATES
            
            "get_low_stock_items": """
                SELECT 
                    ii.item_id,
                    ii.sku,
                    ii.item_name,
                    ii.quantity_on_hand,
                    ii.quantity_reserved,
                    ii.reorder_point,
                    ii.reorder_quantity,
                    ii.unit_price,
                    ii.supplier_id,
                    s.supplier_name
                FROM inventory_items ii
                LEFT JOIN suppliers s ON ii.supplier_id = s.supplier_id
                WHERE 
                    (
                        (COALESCE(%s, 0) = 0 AND ii.quantity_on_hand <= ii.reorder_point)
                        OR (COALESCE(%s, 0) > 0 AND ii.quantity_on_hand <= %s)
                    )
                    AND (COALESCE(%s, 0) = 0 OR ii.category_id = %s)
                ORDER BY ii.quantity_on_hand ASC
                LIMIT %s
            """,
            
            "search_inventory": """
                SELECT 
                    ii.item_id,
                    ii.sku,
                    ii.item_name,
                    ii.quantity_on_hand,
                    ii.quantity_reserved,
                    ii.unit_price,
                    ii.category_id,
                    ii.supplier_id,
                    s.supplier_name
                FROM inventory_items ii
                LEFT JOIN suppliers s ON ii.supplier_id = s.supplier_id
                WHERE 
                    (COALESCE(%s, '') = '' OR ii.sku LIKE CONCAT('%%', %s, '%%'))
                    AND (COALESCE(%s, '') = '' OR ii.item_name LIKE CONCAT('%%', %s, '%%'))
                    AND (COALESCE(%s, 0) = 0 OR ii.category_id = %s)
                ORDER BY ii.item_name
                LIMIT %s
            """,
            
            "get_inventory_by_sku": """
                SELECT 
                    ii.item_id,
                    ii.sku,
                    ii.item_name,
                    ii.quantity_on_hand,
                    ii.quantity_reserved,
                    ii.unit_price,
                    ii.reorder_point,
                    ii.reorder_quantity,
                    s.supplier_name
                FROM inventory_items ii
                LEFT JOIN suppliers s ON ii.supplier_id = s.supplier_id
                WHERE ii.sku = %s
                LIMIT 1
            """
        }
    
    def get_sql(self, template_id: str) -> str:
        """
        Get SQL template by ID
        
        Args:
            template_id: Template identifier
            
        Returns:
            SQL template string
        """
        return self.templates.get(template_id, "")
    
    def has_template(self, template_id: str) -> bool:
        """Check if template exists"""
        return template_id in self.templates
    
    def list_templates(self) -> list:
        """List all available template IDs"""
        return list(self.templates.keys())
