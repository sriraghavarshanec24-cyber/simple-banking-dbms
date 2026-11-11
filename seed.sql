-- =======================================================
-- Simple Banking System (NexBank)
-- Initial Seed Data (DML)
-- Matching Appendix A (Pages 28-30) of Project Report
-- =======================================================

-- 1. Default Admin User (admin / admin123)
INSERT INTO users (username, password, role) VALUES 
('admin', 'admin123', 'admin');

-- 2. Branches
INSERT INTO branches (branch_id, name, address, city, phone) VALUES
(1, 'Downtown Main Branch', '100 Main Street', 'New York', '212-555-0100'),
(2, 'Westside Branch', '250 West Boulevard', 'Los Angeles', '310-555-0200'),
(3, 'Central Business Branch', '500 Commerce Avenue', 'Chicago', '312-555-0300'),
(4, 'Tech Park Branch', '75 Innovation Drive', 'San Francisco', '415-555-0400'),
(5, 'Suburban Branch', '1200 Oak Lane', 'Houston', '713-555-0500');

-- 3. Customers
INSERT INTO customers (customer_id, first_name, last_name, email, phone, address, city, dob, branch_id) VALUES
(1, 'John', 'Smith', 'john.smith@email.com', '555-0101', '45 Elm Street', 'New York', '1990-05-15', 1),
(2, 'Sarah', 'Johnson', 'sarah.j@email.com', '555-0102', '78 Pine Avenue', 'Los Angeles', '1988-11-22', 2),
(3, 'Michael', 'Williams', 'mike.w@email.com', '555-0103', '320 River Road', 'Chicago', '1995-03-08', 3),
(4, 'Emily', 'Brown', 'emily.b@email.com', '555-0104', '15 Sunset Boulevard', 'San Francisco', '1992-07-30', 4),
(5, 'David', 'Davis', 'david.d@email.com', '555-0105', '890 Garden Street', 'Houston', '1985-01-17', 5),
(6, 'Jessica', 'Miller', 'jessica.m@email.com', '555-0106', '456 Broadway', 'New York', '1993-09-25', 1),
(7, 'Robert', 'Wilson', 'robert.w@email.com', '555-0107', '222 Harbor Lane', 'Los Angeles', '1991-12-03', 2),
(8, 'Amanda', 'Taylor', 'amanda.t@email.com', '555-0108', '67 Lake Drive', 'Chicago', '1987-06-14', 3);

-- Customer login accounts (username: first name in lowercase, password: password123)
INSERT INTO users (username, password, role, customer_id) VALUES
('john', 'password123', 'customer', 1),
('sarah', 'password123', 'customer', 2),
('mike', 'password123', 'customer', 3),
('emily', 'password123', 'customer', 4),
('david', 'password123', 'customer', 5),
('jessica', 'password123', 'customer', 6),
('robert', 'password123', 'customer', 7),
('amanda', 'password123', 'customer', 8);

-- 4. Accounts
INSERT INTO accounts (account_id, customer_id, account_type, balance, status, created_at) VALUES
(1, 1, 'savings', 15000.00, 'active', '2026-03-25 10:00:00'),
(2, 1, 'current', 8500.00, 'active', '2026-03-25 10:15:00'),
(3, 2, 'savings', 22000.00, 'active', '2026-03-25 11:00:00'),
(4, 3, 'savings', 5000.00, 'active', '2026-03-25 11:30:00'),
(5, 3, 'current', 12000.00, 'active', '2026-03-25 12:00:00'),
(6, 4, 'savings', 35000.00, 'active', '2026-03-25 12:30:00'),
(7, 5, 'current', 18000.00, 'active', '2026-03-25 13:00:00'),
(8, 6, 'savings', 9500.00, 'active', '2026-03-25 13:30:00'),
(9, 7, 'savings', 27000.00, 'active', '2026-03-25 14:00:00'),
(10, 8, 'current', 11000.00, 'active', '2026-03-25 14:30:00');

-- 5. Transactions
INSERT INTO transactions (txn_id, account_id, txn_type, amount, to_account_id, description, created_at) VALUES
(1, 1, 'deposit', 1500.00, NULL, 'Cash deposit #1', '2026-04-01 14:02:00'),
(2, 1, 'deposit', 15000.00, NULL, 'Initial Deposit', '2026-03-25 09:27:00'),
(3, 3, 'withdrawal', 2492.62, NULL, 'ATM withdrawal #3', '2026-03-24 09:05:00'),
(4, 7, 'deposit', 3405.71, NULL, 'Cash deposit #4', '2026-03-23 11:15:00'),
(5, 2, 'withdrawal', 500.00, NULL, 'ATM withdrawal #5', '2026-03-22 16:40:00'),
(6, 4, 'deposit', 2000.00, NULL, 'Payroll direct deposit', '2026-03-20 08:30:00'),
(7, 5, 'withdrawal', 1200.00, NULL, 'Utility bill payment', '2026-03-18 10:12:00'),
(8, 6, 'deposit', 5000.00, NULL, 'Cash deposit #8', '2026-03-15 13:45:00'),
(9, 8, 'withdrawal', 750.00, NULL, 'ATM withdrawal #9', '2026-03-12 18:22:00'),
(10, 9, 'deposit', 3200.00, NULL, 'Cash deposit #10', '2026-03-10 11:05:00'),
(11, 10, 'withdrawal', 620.00, NULL, 'ATM withdrawal #11', '2026-03-08 14:19:00'),
(12, 1, 'transfer_out', 1000.00, 3, 'Transfer to Sarah Johnson', '2026-03-05 15:30:00'),
(13, 3, 'transfer_in', 1000.00, 1, 'Transfer from John Smith', '2026-03-05 15:30:00'),
(14, 2, 'deposit', 450.00, NULL, 'Cash deposit #14', '2026-03-03 12:00:00'),
(15, 6, 'withdrawal', 850.00, NULL, 'ATM withdrawal #15', '2026-02-28 09:50:00'),
(16, 4, 'deposit', 1100.00, NULL, 'Cash deposit #16', '2026-02-25 17:10:00'),
(17, 7, 'withdrawal', 1400.00, NULL, 'ATM withdrawal #17', '2026-02-20 16:20:00'),
(18, 9, 'deposit', 2500.00, NULL, 'Cash deposit #18', '2026-02-18 10:45:00'),
(19, 5, 'deposit', 3000.00, NULL, 'Cash deposit #19', '2026-02-14 13:15:00'),
(20, 8, 'withdrawal', 300.00, NULL, 'ATM withdrawal #20', '2026-02-10 11:35:00');

-- 6. Loans
INSERT INTO loans (loan_id, customer_id, loan_type, amount, interest_rate, tenure_months, status, start_date, created_at) VALUES
(1, 1, 'home', 250000.00, 7.50, 240, 'approved', '2025-01-15', '2025-01-10 10:00:00'),
(2, 2, 'personal', 15000.00, 10.50, 36, 'approved', '2025-06-01', '2025-05-28 11:30:00'),
(3, 3, 'auto', 35000.00, 8.00, 60, 'pending', NULL, '2026-03-26 14:00:00'),
(4, 4, 'education', 50000.00, 6.50, 48, 'closed', '2025-03-20', '2025-03-15 09:45:00'),
(5, 5, 'business', 100000.00, 9.00, 120, 'rejected', NULL, '2026-03-24 16:15:00'),
(6, 6, 'personal', 8000.00, 11.00, 24, 'rejected', NULL, '2026-03-22 13:20:00');
