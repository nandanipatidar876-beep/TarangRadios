-- =============================================================================
-- Migration 004: Widen ID and Name Columns
-- Expands VARCHAR(64) ID and Title columns to VARCHAR(255) / VARCHAR(500)
-- to support descriptive category and subcategory slug identifiers.
-- =============================================================================

-- Categories Table
ALTER TABLE categories ALTER COLUMN id TYPE VARCHAR(255);
ALTER TABLE categories ALTER COLUMN brand_id TYPE VARCHAR(255);
ALTER TABLE categories ALTER COLUMN title TYPE VARCHAR(500);

-- Subcategories Table
ALTER TABLE subcategories ALTER COLUMN id TYPE VARCHAR(255);
ALTER TABLE subcategories ALTER COLUMN category_id TYPE VARCHAR(255);
ALTER TABLE subcategories ALTER COLUMN name TYPE VARCHAR(500);

-- Products Table
ALTER TABLE products ALTER COLUMN id TYPE VARCHAR(255);
ALTER TABLE products ALTER COLUMN category_id TYPE VARCHAR(255);
ALTER TABLE products ALTER COLUMN brand_id TYPE VARCHAR(255);
ALTER TABLE products ALTER COLUMN subcategory TYPE VARCHAR(500);
ALTER TABLE products ALTER COLUMN sku TYPE VARCHAR(255);
ALTER TABLE products ALTER COLUMN name TYPE VARCHAR(500);

-- Brands Table
ALTER TABLE brands ALTER COLUMN id TYPE VARCHAR(255);
