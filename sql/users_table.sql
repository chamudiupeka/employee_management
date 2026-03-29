-- Create users table for authentication
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
-- Insert admin user with hashed password for "admin123"
INSERT INTO users (username, password_hash)
VALUES (
        'admin',
        'scrypt:32768:8:1$wv1ktAZEupQzOQKz$0376623688e513a8619c53f298505e9de708d41420fc7c22c20059043fc94c6132861faa3554f289c0b71918bb162563acb1f73cf81cff788c36da985866b28c'
    );