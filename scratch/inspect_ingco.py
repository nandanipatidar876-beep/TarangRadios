import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db import get_db

conn = get_db()
cursor = conn.cursor()

# Check INGCO Brand
cursor.execute("SELECT * FROM brands WHERE LOWER(name) LIKE '%ingco%'")
brands = cursor.fetchall()
print("--- INGCO BRANDS ---")
for b in brands:
    print(b)

# Check INGCO Categories
cursor.execute("SELECT * FROM categories WHERE brand_id = 'ingco' OR LOWER(title) LIKE '%ingco%'")
cats = cursor.fetchall()
print("--- INGCO CATEGORIES ---")
for c in cats:
    print(c)

# Check INGCO Products
cursor.execute("SELECT id, sku, name, brand_id, category_id, subcategory, price, image FROM products WHERE brand_id = 'ingco' OR LOWER(brand) = 'ingco'")
prods = cursor.fetchall()
print("--- INGCO PRODUCTS ---")
for p in prods:
    print(p)
