-- Sample data for database
-- This file is loaded after schema creation

INSERT INTO sales_reps (first_name, last_name, email, phone, territory, hire_date, quota, commission_rate) VALUES
('Tom', 'Richards', 'tom.r@sales.com', '+1-555-1101', 'Northeast', '2022-01-15', 500000.00, 5.00),
('Amy', 'Foster', 'amy.f@sales.com', '+1-555-1102', 'Southeast', '2021-06-20', 450000.00, 5.00),
('Kevin', 'Murphy', 'kevin.m@sales.com', '+1-555-1103', 'Midwest', '2023-03-10', 400000.00, 5.50),
('Rachel', 'Cooper', 'rachel.c@sales.com', '+1-555-1104', 'West', '2022-09-05', 550000.00, 4.50),
('Steve', 'Bennett', 'steve.b@sales.com', '+1-555-1105', 'Southwest', '2023-01-12', 425000.00, 5.25);
INSERT INTO customers (customer_name, customer_type, email, phone, city, state, country, credit_limit, payment_terms, assigned_rep_id) VALUES
('Acme Corporation', 'enterprise', 'purchasing@acme.com', '+1-555-2101', 'New York', 'NY', 'USA', 100000.00, 'Net 30', 1),
('Beta Industries', 'mid-market', 'orders@betaind.com', '+1-555-2102', 'Atlanta', 'GA', 'USA', 50000.00, 'Net 45', 2),
('Gamma Solutions', 'small-business', 'info@gammasol.com', '+1-555-2103', 'Chicago', 'IL', 'USA', 25000.00, 'Net 30', 3),
('Delta Enterprises', 'enterprise', 'procurement@delta.com', '+1-555-2104', 'San Francisco', 'CA', 'USA', 150000.00, 'Net 60', 4),
('Epsilon Tech', 'mid-market', 'buying@epsilontech.com', '+1-555-2105', 'Austin', 'TX', 'USA', 75000.00, 'Net 30', 5),
('Zeta Manufacturing', 'enterprise', 'orders@zetamfg.com', '+1-555-2106', 'Boston', 'MA', 'USA', 120000.00, 'Net 45', 1),
('Theta Systems', 'small-business', 'contact@thetasys.com', '+1-555-2107', 'Miami', 'FL', 'USA', 30000.00, 'Net 30', 2);
INSERT INTO products (product_code, product_name, category, description, unit_price, cost, stock_quantity) VALUES
('PROD-A100', 'Professional Workstation', 'Hardware', 'High-performance workstation computer', 2499.99, 1799.99, 50),
('PROD-A101', 'Business Laptop', 'Hardware', 'Enterprise-grade laptop', 1299.99, 899.99, 120),
('PROD-A102', 'Server Rack Unit', 'Hardware', '2U rack-mounted server', 3999.99, 2899.99, 30),
('PROD-B200', 'Software License Pro', 'Software', 'Professional software license', 499.99, 199.99, 1000),
('PROD-B201', 'Cloud Storage 1TB', 'Services', 'Annual cloud storage subscription', 299.99, 149.99, 5000),
('PROD-C300', 'Network Switch 24-port', 'Networking', 'Managed network switch', 899.99, 599.99, 75),
('PROD-C301', 'Wireless Access Point', 'Networking', 'Enterprise wireless AP', 349.99, 229.99, 100),
('PROD-D400', 'Security Camera System', 'Security', '8-camera security system', 1599.99, 1099.99, 40);
INSERT INTO sales_orders (order_number, customer_id, rep_id, order_date, required_date, status, subtotal, tax_amount, shipping_cost, total_amount, payment_method) VALUES
('SO-2024-001', 1, 1, '2024-03-01', '2024-03-15', 'shipped', 25000.00, 2000.00, 150.00, 27150.00, 'wire_transfer'),
('SO-2024-002', 2, 2, '2024-03-05', '2024-03-20', 'processing', 15000.00, 1200.00, 100.00, 16300.00, 'credit_card'),
('SO-2024-003', 3, 3, '2024-03-08', '2024-03-22', 'pending', 8500.00, 680.00, 75.00, 9255.00, 'purchase_order'),
('SO-2024-004', 4, 4, '2024-03-10', '2024-03-25', 'shipped', 45000.00, 3600.00, 200.00, 48800.00, 'wire_transfer'),
('SO-2024-005', 5, 5, '2024-03-12', '2024-03-28', 'processing', 12000.00, 960.00, 80.00, 13040.00, 'credit_card');
INSERT INTO order_line_items (order_id, product_id, quantity, unit_price, discount_percent, line_total) VALUES
(1, 1, 10, 2499.99, 0, 24999.90),
(2, 2, 10, 1299.99, 5, 12349.90),
(2, 4, 5, 499.99, 0, 2499.95),
(3, 6, 8, 899.99, 10, 6479.93),
(3, 7, 5, 349.99, 5, 1662.45),
(4, 3, 10, 3999.99, 5, 37999.90),
(4, 2, 5, 1299.99, 0, 6499.95),
(5, 8, 5, 1599.99, 10, 7199.96),
(5, 4, 10, 499.99, 5, 4749.90);
INSERT INTO quotations (quote_number, customer_id, rep_id, quote_date, valid_until, total_amount, status) VALUES
('QT-2024-001', 6, 1, '2024-03-14', '2024-04-14', 35000.00, 'pending'),
('QT-2024-002', 7, 2, '2024-03-15', '2024-04-15', 18000.00, 'accepted');
INSERT INTO commissions (rep_id, order_id, commission_amount, commission_date, payment_status) VALUES
(1, 1, 1250.00, '2024-03-15', 'paid'),
(4, 4, 2025.00, '2024-03-20', 'pending');
