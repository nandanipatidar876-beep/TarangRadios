-- =============================================================================
-- Migration 001: Initial Core Schema
-- Description: Creates core tables for Tarang Radios catalog & admin management.
-- Compatible with PostgreSQL & SQLite.
-- =============================================================================

-- Admins Table
CREATE TABLE IF NOT EXISTS admins (
    id VARCHAR(255) PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(256) NOT NULL,
    salt VARCHAR(64) NOT NULL,
    name VARCHAR(150),
    created_at VARCHAR(64) NOT NULL
);

-- Sessions Table
CREATE TABLE IF NOT EXISTS sessions (
    token VARCHAR(128) PRIMARY KEY,
    admin_id VARCHAR(255) NOT NULL,
    expires_at VARCHAR(64) NOT NULL,
    FOREIGN KEY (admin_id) REFERENCES admins(id) ON DELETE CASCADE
);

-- Brands Table ("The Brands We Deal With" - Strictly independent)
CREATE TABLE IF NOT EXISTS brands (
    id VARCHAR(255) PRIMARY KEY,
    name VARCHAR(150) UNIQUE NOT NULL,
    display_order INTEGER DEFAULT 0,
    is_enabled INTEGER DEFAULT 1,
    created_at VARCHAR(64),
    updated_at VARCHAR(64)
);

-- Categories Table (brand_id is NULL for Normal Categories, or points to a Brand in "The Brands We Deal With")
CREATE TABLE IF NOT EXISTS categories (
    id VARCHAR(255) PRIMARY KEY,
    brand_id VARCHAR(255),
    title VARCHAR(500) NOT NULL,
    short_title VARCHAR(200),
    tagline VARCHAR(500),
    icon VARCHAR(50) DEFAULT 'layers',
    image TEXT,
    color VARCHAR(20) DEFAULT '#D14B14',
    display_order INTEGER DEFAULT 0,
    created_at VARCHAR(64),
    updated_at VARCHAR(64),
    FOREIGN KEY (brand_id) REFERENCES brands(id) ON DELETE CASCADE
);

-- Subcategories Table
CREATE TABLE IF NOT EXISTS subcategories (
    id VARCHAR(255) PRIMARY KEY,
    category_id VARCHAR(255) NOT NULL,
    name VARCHAR(500) NOT NULL,
    display_order INTEGER DEFAULT 0,
    FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE CASCADE
);

-- Products Table
CREATE TABLE IF NOT EXISTS products (
    id VARCHAR(255) PRIMARY KEY,
    sku VARCHAR(255),
    name VARCHAR(500) NOT NULL,
    brand_id VARCHAR(255),
    brand VARCHAR(150),
    category_id VARCHAR(255) NOT NULL,
    subcategory VARCHAR(500),
    price DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    badge VARCHAR(50),
    in_stock INTEGER DEFAULT 1,
    image TEXT,
    description TEXT,
    specs TEXT,
    rating DOUBLE PRECISION DEFAULT 5.0,
    reviews INTEGER DEFAULT 0,
    created_at VARCHAR(64),
    updated_at VARCHAR(64),
    FOREIGN KEY (brand_id) REFERENCES brands(id) ON DELETE CASCADE,
    FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE CASCADE
);
