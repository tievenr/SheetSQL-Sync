CREATE DATABASE IF NOT EXISTS syncdb;
USE syncdb;

CREATE TABLE IF NOT EXISTS synced_data (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL,
    status ENUM('active', 'inactive') DEFAULT 'active',
    last_modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_last_modified (last_modified)
);

-- Insert initial test data 
INSERT INTO synced_data (id, name, email, status, last_modified) VALUES
(1, 'January', 'testjy@gmail.com', 'active', '2025-01-13 10:00:00'),
(2, 'February', 'testfb@gmail.com', 'active', '2025-01-14 10:00:00'),
(3, 'March', 'testmc@gmail.com', 'active', '2025-01-15 10:00:00'),
(4, 'April', 'testar@gmail.com', 'active', '2025-01-16 10:00:00'),
(5, 'May', 'testmy@gmail.com', 'active', '2025-01-17 10:00:00');