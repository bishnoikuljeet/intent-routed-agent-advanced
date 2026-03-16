-- SUPPLIERS TABLE: Stores supplier/vendor information for procurement
-- Use this table for queries about: supplier names, contact persons, supplier emails, supplier phones, supplier locations, payment terms, supplier ratings, active suppliers
CREATE TABLE suppliers (
    supplier_id INT AUTO_INCREMENT PRIMARY KEY,      -- Unique identifier for each supplier
    supplier_name VARCHAR(255) NOT NULL,             -- Supplier company name
    contact_person VARCHAR(255),                     -- Primary contact person at supplier
    email VARCHAR(255),                              -- Supplier email address
    phone VARCHAR(20),                               -- Supplier phone number
    address TEXT,                                    -- Supplier street address
    city VARCHAR(100),                               -- Supplier city
    country VARCHAR(100),                            -- Supplier country
    payment_terms VARCHAR(100),                      -- Payment terms (Net 30, Net 45, Net 60, etc.)
    rating DECIMAL(3, 2),                            -- Supplier performance rating (0-5)
    is_active BOOLEAN DEFAULT TRUE                   -- Whether supplier is currently active
);

-- PRODUCT_CATEGORIES TABLE: Stores hierarchical product category structure
-- Use this table for queries about: category names, category descriptions, parent categories, category hierarchy
CREATE TABLE product_categories (
    category_id INT AUTO_INCREMENT PRIMARY KEY,      -- Unique identifier for each category
    category_name VARCHAR(100) NOT NULL,             -- Category name
    description TEXT,                                -- Category description
    parent_category_id INT,                          -- Parent category for hierarchical structure
    FOREIGN KEY (parent_category_id) REFERENCES product_categories(category_id)
);

-- INVENTORY_ITEMS TABLE: Stores inventory items with stock levels and reorder information
-- Use this table for queries about: SKUs, item names, stock quantities, reorder points, unit prices, item locations, categories, suppliers, quantities on hand, reserved quantities
CREATE TABLE inventory_items (
    item_id INT AUTO_INCREMENT PRIMARY KEY,          -- Unique identifier for each inventory item
    sku VARCHAR(100) UNIQUE NOT NULL,                -- Stock Keeping Unit (unique product code)
    item_name VARCHAR(255) NOT NULL,                 -- Item name/description
    category_id INT,                                 -- Product category
    supplier_id INT,                                 -- Primary supplier for this item
    description TEXT,                                -- Detailed item description
    unit_price DECIMAL(10, 2),                       -- Price per unit
    quantity_on_hand INT DEFAULT 0,                  -- Current stock quantity available
    quantity_reserved INT DEFAULT 0,                 -- Quantity reserved for orders
    reorder_point INT,                               -- Minimum quantity before reordering
    reorder_quantity INT,                            -- Quantity to order when restocking
    unit_of_measure VARCHAR(20),                     -- Unit (piece, pack, set, pair, kit, etc.)
    location VARCHAR(100),                           -- Warehouse location code
    last_restocked DATE,                             -- Date of last restock
    FOREIGN KEY (category_id) REFERENCES product_categories(category_id),
    FOREIGN KEY (supplier_id) REFERENCES suppliers(supplier_id)
);

-- PURCHASE_ORDERS TABLE: Stores purchase orders placed with suppliers
-- Use this table for queries about: PO numbers, order dates, delivery dates, order totals, order status, supplier orders
CREATE TABLE purchase_orders (
    po_id INT AUTO_INCREMENT PRIMARY KEY,            -- Unique identifier for each purchase order
    po_number VARCHAR(50) UNIQUE NOT NULL,           -- Purchase order number (unique)
    supplier_id INT,                                 -- Supplier for this PO
    order_date DATE NOT NULL,                        -- Date order was placed
    expected_delivery DATE,                          -- Expected delivery date
    actual_delivery DATE,                            -- Actual delivery date (NULL if not delivered)
    total_amount DECIMAL(12, 2),                     -- Total order amount
    status VARCHAR(20) DEFAULT 'pending',            -- Order status (pending, confirmed, in_transit, delivered, cancelled)
    notes TEXT,                                      -- Additional notes
    FOREIGN KEY (supplier_id) REFERENCES suppliers(supplier_id)
);

-- PURCHASE_ORDER_ITEMS TABLE: Stores line items for each purchase order
-- Use this table for queries about: items in purchase orders, order quantities, item prices, order details
CREATE TABLE purchase_order_items (
    po_item_id INT AUTO_INCREMENT PRIMARY KEY,       -- Unique identifier for each PO line item
    po_id INT,                                       -- Purchase order this item belongs to
    item_id INT,                                     -- Inventory item being ordered
    quantity INT NOT NULL,                           -- Quantity ordered
    unit_price DECIMAL(10, 2),                       -- Price per unit
    total_price DECIMAL(12, 2),                      -- Total price for this line item
    FOREIGN KEY (po_id) REFERENCES purchase_orders(po_id),
    FOREIGN KEY (item_id) REFERENCES inventory_items(item_id)
);

-- STOCK_MOVEMENTS TABLE: Tracks all inventory movements (receipts, issues, adjustments)
-- Use this table for queries about: stock receipts, stock issues, inventory adjustments, movement dates, movement types, stock transactions
CREATE TABLE stock_movements (
    movement_id INT AUTO_INCREMENT PRIMARY KEY,      -- Unique identifier for each movement
    item_id INT,                                     -- Item being moved
    movement_type VARCHAR(50) NOT NULL,              -- Type of movement (receipt, issue, adjustment, transfer)
    quantity INT NOT NULL,                           -- Quantity moved (positive for receipt, negative for issue)
    reference_number VARCHAR(100),                   -- Reference number (PO number, work order, etc.)
    movement_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- When movement occurred
    notes TEXT,                                      -- Movement notes/reason
    performed_by VARCHAR(100),                       -- User who performed the movement
    FOREIGN KEY (item_id) REFERENCES inventory_items(item_id)
);

-- INVENTORY_AUDITS TABLE: Stores physical inventory audit results
-- Use this table for queries about: audit dates, expected quantities, actual quantities, inventory variances, discrepancies, audit results
CREATE TABLE inventory_audits (
    audit_id INT AUTO_INCREMENT PRIMARY KEY,         -- Unique identifier for each audit record
    item_id INT,                                     -- Item being audited
    audit_date DATE NOT NULL,                        -- Date of audit
    expected_quantity INT,                           -- Expected quantity per system
    actual_quantity INT,                             -- Actual counted quantity
    variance INT,                                    -- Difference (actual - expected)
    audited_by VARCHAR(100),                         -- Person who performed audit
    notes TEXT,                                      -- Audit notes/findings
    FOREIGN KEY (item_id) REFERENCES inventory_items(item_id)
);








CREATE INDEX idx_inventory_sku ON inventory_items(sku);
CREATE INDEX idx_inventory_category ON inventory_items(category_id);
CREATE INDEX idx_inventory_supplier ON inventory_items(supplier_id);
CREATE INDEX idx_po_supplier ON purchase_orders(supplier_id);
CREATE INDEX idx_stock_movements_item ON stock_movements(item_id);
