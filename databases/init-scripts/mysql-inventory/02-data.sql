-- Sample data for database
-- This file is loaded after schema creation

INSERT INTO suppliers (supplier_name, contact_person, email, phone, city, country, payment_terms, rating) VALUES
('Global Parts Co', 'Tom Anderson', 'tom@globalparts.com', '+1-555-9001', 'Chicago', 'USA', 'Net 30', 4.5),
('Premium Supplies Inc', 'Sarah Lee', 'sarah@premiumsupplies.com', '+1-555-9002', 'Los Angeles', 'USA', 'Net 45', 4.8),
('Industrial Components Ltd', 'Mike Chen', 'mike@indcomp.com', '+1-555-9003', 'Houston', 'USA', 'Net 60', 4.2),
('Tech Materials Group', 'Lisa Wang', 'lisa@techmaterials.com', '+1-555-9004', 'Seattle', 'USA', 'Net 30', 4.7),
('Quality Parts Direct', 'John Smith', 'john@qualityparts.com', '+1-555-9005', 'Boston', 'USA', 'Net 45', 4.6);
INSERT INTO product_categories (category_name, description) VALUES
('Electronics', 'Electronic components and devices'),
('Hardware', 'Physical hardware components'),
('Tools', 'Hand and power tools'),
('Safety Equipment', 'Personal protective equipment'),
('Office Supplies', 'General office supplies');
INSERT INTO inventory_items (sku, item_name, category_id, supplier_id, description, unit_price, quantity_on_hand, reorder_point, reorder_quantity, unit_of_measure, location) VALUES
('SKU-001', 'Resistor Pack 100pc', 1, 1, '100-piece resistor assortment', 15.99, 250, 50, 200, 'pack', 'A-01-05'),
('SKU-002', 'LED Light Strip 5m', 1, 2, '5-meter RGB LED strip', 29.99, 180, 30, 100, 'piece', 'A-02-10'),
('SKU-003', 'Power Supply 12V 5A', 1, 1, '12V 5A switching power supply', 24.99, 120, 25, 75, 'piece', 'A-03-08'),
('SKU-004', 'Screwdriver Set 20pc', 3, 3, 'Professional screwdriver set', 45.99, 95, 20, 50, 'set', 'B-01-03'),
('SKU-005', 'Safety Goggles', 4, 4, 'Impact-resistant safety goggles', 12.99, 300, 50, 200, 'piece', 'C-01-12'),
('SKU-006', 'Cable Ties 100pc', 2, 1, 'Assorted cable ties pack', 8.99, 450, 100, 300, 'pack', 'A-04-06'),
('SKU-007', 'Multimeter Digital', 3, 2, 'Digital multimeter with LCD', 39.99, 75, 15, 50, 'piece', 'B-02-09'),
('SKU-008', 'Heat Shrink Tubing', 2, 3, 'Assorted heat shrink tubing', 18.99, 200, 40, 150, 'pack', 'A-05-11'),
('SKU-009', 'Work Gloves Pair', 4, 4, 'Heavy-duty work gloves', 9.99, 280, 60, 200, 'pair', 'C-02-07'),
('SKU-010', 'Soldering Iron Kit', 3, 5, 'Complete soldering iron kit', 55.99, 60, 12, 40, 'kit', 'B-03-04'),
('SKU-011', 'Arduino Starter Kit', 1, 2, 'Arduino UNO R3 starter kit with components', 89.99, 8, 25, 50, 'kit', 'A-06-15');
INSERT INTO purchase_orders (po_number, supplier_id, order_date, expected_delivery, total_amount, status) VALUES
('PO-2024-001', 1, '2024-03-01', '2024-03-15', 5000.00, 'delivered'),
('PO-2024-002', 2, '2024-03-05', '2024-03-20', 3500.00, 'in_transit'),
('PO-2024-003', 3, '2024-03-08', '2024-03-25', 4200.00, 'pending'),
('PO-2024-004', 4, '2024-03-10', '2024-03-28', 2800.00, 'pending'),
('PO-2024-005', 5, '2024-03-12', '2024-03-30', 3900.00, 'confirmed');
INSERT INTO purchase_order_items (po_id, item_id, quantity, unit_price, total_price) VALUES
(1, 1, 200, 15.99, 3198.00),
(1, 6, 200, 8.99, 1798.00),
(2, 2, 100, 29.99, 2999.00),
(2, 7, 15, 39.99, 599.85),
(3, 4, 50, 45.99, 2299.50),
(3, 10, 30, 55.99, 1679.70);
INSERT INTO stock_movements (item_id, movement_type, quantity, reference_number, notes, performed_by) VALUES
(1, 'receipt', 200, 'PO-2024-001', 'Received from supplier', 'warehouse_staff_1'),
(2, 'issue', 50, 'WO-2024-100', 'Issued for production', 'warehouse_staff_2'),
(3, 'adjustment', -5, 'ADJ-2024-010', 'Damaged items removed', 'warehouse_manager'),
(5, 'receipt', 200, 'PO-2024-001', 'Received from supplier', 'warehouse_staff_1'),
(6, 'issue', 100, 'WO-2024-101', 'Issued for assembly', 'warehouse_staff_3');
INSERT INTO inventory_audits (item_id, audit_date, expected_quantity, actual_quantity, variance, audited_by, notes) VALUES
(1, '2024-03-01', 250, 248, -2, 'audit_team_1', 'Minor discrepancy, acceptable'),
(2, '2024-03-01', 180, 180, 0, 'audit_team_1', 'Count matches records'),
(3, '2024-03-01', 125, 120, -5, 'audit_team_2', 'Damaged units found and removed'),
(5, '2024-03-01', 300, 300, 0, 'audit_team_1', 'Count matches records');
