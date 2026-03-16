-- SALES_REPS TABLE: Stores sales representative information and quotas
-- Use this table for queries about: sales rep names, territories, quotas, commission rates, sales performance
CREATE TABLE sales_reps (
    rep_id INT AUTO_INCREMENT PRIMARY KEY,              -- Unique identifier for each sales rep
    first_name VARCHAR(100) NOT NULL,                   -- Sales rep's first name
    last_name VARCHAR(100) NOT NULL,                    -- Sales rep's last name
    email VARCHAR(255) UNIQUE NOT NULL,                 -- Sales rep email address (unique)
    phone VARCHAR(20),                                  -- Sales rep phone number
    territory VARCHAR(100),                             -- Sales territory (Northeast, West, etc.)
    hire_date DATE,                                     -- Date sales rep was hired
    quota DECIMAL(12, 2),                               -- Sales quota target
    commission_rate DECIMAL(5, 2),                      -- Commission rate percentage
    is_active BOOLEAN DEFAULT TRUE                      -- Whether sales rep is currently active
);

-- CUSTOMERS TABLE: Stores customer account information and contact details
-- Use this table for queries about: customer names, emails, addresses, registration dates, loyalty points, active customers
CREATE TABLE customers (
    customer_id INT AUTO_INCREMENT PRIMARY KEY,         -- Unique identifier for each customer
    customer_name VARCHAR(255) NOT NULL,                -- Customer/company name
    customer_type VARCHAR(50),                          -- Type (enterprise, mid-market, small-business)
    email VARCHAR(255),                                 -- Customer email address
    phone VARCHAR(20),                                  -- Customer phone number
    billing_address TEXT,                               -- Billing address
    shipping_address TEXT,                              -- Shipping address
    city VARCHAR(100),                                  -- City
    state VARCHAR(50),                                  -- State/province
    country VARCHAR(100),                               -- Country
    postal_code VARCHAR(20),                            -- Postal/ZIP code
    credit_limit DECIMAL(12, 2),                        -- Credit limit
    payment_terms VARCHAR(50),                          -- Payment terms (Net 30, Net 45, etc.)
    assigned_rep_id INT,                                -- Assigned sales representative
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,     -- When customer was created
    FOREIGN KEY (assigned_rep_id) REFERENCES sales_reps(rep_id)
);

-- PRODUCTS TABLE: Stores product catalog with pricing and inventory information
-- Use this table for queries about: product names, prices, stock quantities, categories, brands, SKUs, product descriptions
CREATE TABLE products (
    product_id INT AUTO_INCREMENT PRIMARY KEY,          -- Unique identifier for each product
    product_code VARCHAR(50) UNIQUE NOT NULL,           -- Product code/SKU (unique)
    product_name VARCHAR(255) NOT NULL,                 -- Product name
    category VARCHAR(100),                              -- Product category
    description TEXT,                                   -- Product description
    unit_price DECIMAL(10, 2),                          -- Selling price per unit
    cost DECIMAL(10, 2),                                -- Cost per unit
    stock_quantity INT DEFAULT 0,                       -- Current stock quantity
    is_active BOOLEAN DEFAULT TRUE                      -- Whether product is active
);

-- SALES_ORDERS TABLE: Stores sales orders and transaction details
-- Use this table for queries about: order numbers, order dates, order totals, order status, customer orders
CREATE TABLE sales_orders (
    order_id INT AUTO_INCREMENT PRIMARY KEY,            -- Unique identifier for each order
    order_number VARCHAR(50) UNIQUE NOT NULL,           -- Order number (unique)
    customer_id INT,                                    -- Customer who placed the order
    rep_id INT,                                         -- Sales rep who handled the order
    order_date DATE NOT NULL,                           -- Date order was placed
    required_date DATE,                                 -- Date customer needs order by
    shipped_date DATE,                                  -- Date order was shipped
    status VARCHAR(20) DEFAULT 'pending',               -- Order status (pending, processing, shipped)
    subtotal DECIMAL(12, 2),                            -- Subtotal before tax and shipping
    tax_amount DECIMAL(10, 2),                          -- Tax amount
    shipping_cost DECIMAL(10, 2),                       -- Shipping cost
    total_amount DECIMAL(12, 2),                        -- Total order amount
    payment_method VARCHAR(50),                         -- Payment method used
    notes TEXT,                                         -- Order notes
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
    FOREIGN KEY (rep_id) REFERENCES sales_reps(rep_id)
);

-- ORDER_LINE_ITEMS TABLE: Stores individual line items for each sales order
-- Use this table for queries about: products in orders, order quantities, item prices, discounts, line totals, order details
CREATE TABLE order_line_items (
    line_item_id INT AUTO_INCREMENT PRIMARY KEY,       -- Unique identifier for each line item
    order_id INT,                                       -- Sales order this item belongs to
    product_id INT,                                     -- Product being ordered
    quantity INT NOT NULL,                              -- Quantity ordered
    unit_price DECIMAL(10, 2),                          -- Price per unit
    discount_percent DECIMAL(5, 2) DEFAULT 0,           -- Discount percentage applied
    line_total DECIMAL(12, 2),                          -- Total for this line item
    FOREIGN KEY (order_id) REFERENCES sales_orders(order_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);

-- QUOTATIONS TABLE: Stores sales quotations and price quotes
-- Use this table for queries about: quote numbers, quote dates, quote amounts, quote validity, quote status, customer quotes
CREATE TABLE quotations (
    quote_id INT AUTO_INCREMENT PRIMARY KEY,           -- Unique identifier for each quotation
    quote_number VARCHAR(50) UNIQUE NOT NULL,           -- Quotation number (unique)
    customer_id INT,                                    -- Customer receiving the quote
    rep_id INT,                                         -- Sales rep who created the quote
    quote_date DATE NOT NULL,                           -- Date quote was created
    valid_until DATE,                                   -- Quote expiration date
    total_amount DECIMAL(12, 2),                        -- Total quoted amount
    status VARCHAR(20) DEFAULT 'pending',               -- Quote status (pending, accepted, rejected, expired)
    notes TEXT,                                         -- Additional notes
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
    FOREIGN KEY (rep_id) REFERENCES sales_reps(rep_id)
);

-- COMMISSIONS TABLE: Stores sales commission payments for representatives
-- Use this table for queries about: commission amounts, commission dates, payment status, rep commissions, earned commissions
CREATE TABLE commissions (
    commission_id INT AUTO_INCREMENT PRIMARY KEY,      -- Unique identifier for each commission record
    rep_id INT,                                         -- Sales rep earning the commission
    order_id INT,                                       -- Order that generated the commission
    commission_amount DECIMAL(10, 2),                   -- Commission amount earned
    commission_date DATE,                               -- Date commission was calculated
    payment_status VARCHAR(20) DEFAULT 'pending',       -- Payment status (pending, paid, cancelled)
    FOREIGN KEY (rep_id) REFERENCES sales_reps(rep_id),
    FOREIGN KEY (order_id) REFERENCES sales_orders(order_id)
);








CREATE INDEX idx_customers_rep ON customers(assigned_rep_id);
CREATE INDEX idx_sales_orders_customer ON sales_orders(customer_id);
CREATE INDEX idx_sales_orders_rep ON sales_orders(rep_id);
CREATE INDEX idx_sales_orders_date ON sales_orders(order_date);
CREATE INDEX idx_order_items_order ON order_line_items(order_id);
CREATE INDEX idx_commissions_rep ON commissions(rep_id);
