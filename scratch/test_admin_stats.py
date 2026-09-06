import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db import get_db

conn = get_db()
cursor = conn.cursor()

cursor.execute("SELECT COUNT(*) as cnt FROM brands")
total_brands = cursor.fetchone()["cnt"]

cursor.execute("SELECT COUNT(*) as cnt FROM categories WHERE brand_id IS NULL OR brand_id = ''")
total_normal_cats = cursor.fetchone()["cnt"]

cursor.execute("SELECT COUNT(*) as cnt FROM categories WHERE brand_id IS NOT NULL AND brand_id != ''")
total_brand_cats = cursor.fetchone()["cnt"]

cursor.execute("SELECT COUNT(*) as cnt FROM subcategories")
total_subs = cursor.fetchone()["cnt"]

cursor.execute("SELECT COUNT(*) as total, SUM(CASE WHEN in_stock = 1 THEN 1 ELSE 0 END) as in_stock, AVG(price) as avg_p FROM products")
row = cursor.fetchone()
total_prods = row["total"] or 0
in_stock_prods = row["in_stock"] or 0
avg_price = round(float(row["avg_p"] or 0), 2)

print("total_brands:", total_brands)
print("total_normal_cats:", total_normal_cats)
print("total_brand_cats:", total_brand_cats)
print("total_subs:", total_subs)
print("total_prods:", total_prods)
print("in_stock_prods:", in_stock_prods)
print("avg_price:", avg_price)
