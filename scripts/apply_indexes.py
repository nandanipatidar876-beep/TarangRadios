"""
Database Performance Migration - Create B-Tree Indexes for Products, Categories, Subcategories, Brands
Applies to both SQLite and PostgreSQL.
"""
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from db import get_db, get_engine_type

INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_products_category_id ON products(category_id);",
    "CREATE INDEX IF NOT EXISTS idx_products_brand_id ON products(brand_id);",
    "CREATE INDEX IF NOT EXISTS idx_products_subcategory ON products(subcategory);",
    "CREATE INDEX IF NOT EXISTS idx_products_sku ON products(sku);",
    "CREATE INDEX IF NOT EXISTS idx_products_name ON products(name);",
    "CREATE INDEX IF NOT EXISTS idx_products_price ON products(price);",
    "CREATE INDEX IF NOT EXISTS idx_products_created_at ON products(created_at);",
    "CREATE INDEX IF NOT EXISTS idx_subcategories_category_id ON subcategories(category_id);",
    "CREATE INDEX IF NOT EXISTS idx_categories_brand_id ON categories(brand_id);",
    "CREATE INDEX IF NOT EXISTS idx_brands_is_enabled ON brands(is_enabled);"
]

def apply_indexes():
    engine = get_engine_type()
    print(f"[INDEX MIGRATION] Applying B-Tree indexes on active database engine: {engine.upper()}...")
    applied = 0
    with get_db() as db:
        for sql in INDEXES:
            try:
                db.execute(sql)
                applied += 1
            except Exception as e:
                print(f"[INDEX WARNING] Error executing '{sql}': {e}")
    print(f"[INDEX MIGRATION] Successfully verified and applied {applied}/{len(INDEXES)} indexes.")

if __name__ == "__main__":
    apply_indexes()
