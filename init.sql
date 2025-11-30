-- Create database if not exists
CREATE DATABASE IF NOT EXISTS flaskdb;

USE flaskdb;

CREATE TABLE IF NOT EXISTS messages (
    id INT AUTO_INCREMENT PRIMARY KEY,
    input VARCHAR(255) NOT NULL,
    output VARCHAR(255) NOT NULL,
    secret_key VARCHAR(255) NOT NULL
);