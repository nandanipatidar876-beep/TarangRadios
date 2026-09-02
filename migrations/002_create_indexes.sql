-- =============================================================================
-- Migration 002: Performance Indexes
-- Description: B-Tree indexes for fast product search, category filtering, and SKU lookups.
-- =============================================================================

CREATE INDEX IF NOT EXISTS idx_products_category_id ON products(category_id);
CREATE INDEX IF NOT EXISTS idx_products_brand_id ON products(brand_id);
CREATE INDEX IF NOT EXISTS idx_products_sku ON products(sku);
CREATE INDEX IF NOT EXISTS idx_products_name ON products(name);
CREATE INDEX IF NOT EXISTS idx_products_subcategory ON products(subcategory);

CREATE INDEX IF NOT EXISTS idx_categories_brand_id ON categories(brand_id);
CREATE INDEX IF NOT EXISTS idx_categories_display_order ON categories(display_order);

CREATE INDEX IF NOT EXISTS idx_subcategories_category_id ON subcategories(category_id);
CREATE INDEX IF NOT EXISTS idx_subcategories_display_order ON subcategories(display_order);

CREATE INDEX IF NOT EXISTS idx_brands_display_order ON brands(display_order);
CREATE INDEX IF NOT EXISTS idx_sessions_admin_id ON sessions(admin_id);
