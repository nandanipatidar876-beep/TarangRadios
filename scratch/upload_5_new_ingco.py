import os
import sys
import json
import shutil

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import db
import cloudinary_service

USER_UPLOADED_DIR = r"C:\Users\dell\.gemini\antigravity-ide\brain\952646ab-afb6-443e-baaf-3519dc6a63ae\.user_uploaded"
TARGET_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "uploads", "brands", "ingco")
os.makedirs(TARGET_DIR, exist_ok=True)

# 1. Image mapping
image_mapping = {
    "CGCI 2003": ("media_1788763185069.jpg", "ingco_cgci_2003.jpg"),
    "CABLI 20018": ("media_1788763284051.jpg", "ingco_cabli_20018.jpg"),
    "CDLI 1228": ("media_1788763383482.jpg", "ingco_cdli_1228.jpg"),
    "CSDLI 08025": ("media_1788763542896.jpg", "ingco_csdli_08025.jpg"),
    "HLDD0355": ("media_1788763620594.jpg", "ingco_hldd0355.jpg"),
}

cloud_urls = {}

for sku, (src_name, dst_name) in image_mapping.items():
    src_path = os.path.join(USER_UPLOADED_DIR, src_name)
    dst_path = os.path.join(TARGET_DIR, dst_name)
    
    if os.path.exists(src_path):
        shutil.copy2(src_path, dst_path)
        print(f"Copied {src_name} -> {dst_path}")
    
    # Upload to Cloudinary
    res = cloudinary_service.upload_image(dst_path, folder="tarang_radio/brands/ingco")
    if res and res.get("url"):
        cloud_url = res["url"]
        cloud_urls[sku] = cloud_url
        print(f"Uploaded {sku} to Cloudinary: {cloud_url}")
    else:
        print(f"Failed Cloudinary upload for {sku}: {res}")

# Update uploaded cache file
cache_file = "scratch/uploaded_ingco_images.json"
uploaded = {}
if os.path.exists(cache_file):
    with open(cache_file, "r") as f:
        uploaded = json.load(f)

uploaded.update(cloud_urls)
with open(cache_file, "w") as f:
    json.dump(uploaded, f, indent=2)

# 2. Database Integration
conn = db.get_db()
cursor = conn.cursor()
brand_id = "brand_ingco"

# Ensure Category for Measuring & Testing Tools exists
measuring_cat = {
    "id": "cat_ingco_measuring",
    "brand_id": brand_id,
    "title": "INGCO Measuring & Testing Tools",
    "short_title": "Measuring & Testing",
    "tagline": "High Precision Laser Distance Meters, Detectors & Meters",
    "icon": "activity",
    "color": "#9B59B6",
    "display_order": 7
}

cursor.execute("SELECT id FROM categories WHERE id = %s", (measuring_cat["id"],))
if not cursor.fetchone():
    cursor.execute("""
        INSERT INTO categories (id, brand_id, title, short_title, tagline, icon, color, display_order, created_at, updated_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
    """, (measuring_cat["id"], measuring_cat["brand_id"], measuring_cat["title"], measuring_cat["short_title"], measuring_cat["tagline"], measuring_cat["icon"], measuring_cat["color"], measuring_cat["display_order"]))
    print(f"Created category {measuring_cat['title']}")

# Ensure Subcategories
new_subs = [
    {"id": "sub_ingco_laser_meters", "category_id": "cat_ingco_measuring", "name": "Laser Distance Meters", "display_order": 1},
    {"id": "sub_ingco_cordless_blowers", "category_id": "cat_ingco_cordless", "name": "Cordless Blowers", "display_order": 3},
    {"id": "sub_ingco_cordless_glue", "category_id": "cat_ingco_glue", "name": "Cordless Glue Guns", "display_order": 2},
]

for sub in new_subs:
    cursor.execute("SELECT id FROM subcategories WHERE id = %s", (sub["id"],))
    if not cursor.fetchone():
        cursor.execute("""
            INSERT INTO subcategories (id, category_id, name, display_order)
            VALUES (%s, %s, %s, %s)
        """, (sub["id"], sub["category_id"], sub["name"], sub["display_order"]))
        print(f"Created subcategory {sub['name']}")

# 3. Product Definitions
new_products = [
    {
        "sku": "CGCI 2003",
        "name": "INGCO 20V Lithium-Ion Cordless Hot Melt Glue Gun (CGCI 2003)",
        "category_id": "cat_ingco_glue",
        "subcategory": "Cordless Glue Guns",
        "price": 1250.00,
        "badge": "20V P20S Cordless",
        "description": "Industrial 20V cordless hot melt glue gun (P20S share system) with rapid 60-second heating time, 17-20 g/min gluing output, compatible with standard 11.2mm glue sticks, and includes 3 Pcs glue sticks.",
        "specs": {
            "Model Number": "CGCI 2003",
            "Voltage": "20V (P20S Multi-Tool Platform)",
            "Gluing Capacity": "17 - 20 g/min",
            "Glue Stick Diameter": "11.2 mm (Ø11.2mm)",
            "Preheat Time": "60 - 90 seconds",
            "Features": "LED Heat Indicator, Anti-Drip Nozzle, Stand Base",
            "Included Accessories": "3 Pcs Ø11.2mm Glue Sticks"
        }
    },
    {
        "sku": "CABLI 20018",
        "name": "INGCO 20V Lithium-Ion Cordless Air Blower (CABLI 20018)",
        "category_id": "cat_ingco_cordless",
        "subcategory": "Cordless Blowers",
        "price": 2450.00,
        "badge": "2.7m³/min 2-Speed",
        "description": "High-velocity 20V cordless leaf & jobsite air blower with 2-speed volume control (0-9000 / 0-18000 RPM), max airflow rate of 2.7 m³/min, detachable blower nozzle, and ergonomic handle.",
        "specs": {
            "Model Number": "CABLI 20018",
            "Voltage": "20V (INGCO P20S Platform)",
            "No-Load Speed": "0-9000 / 0-18000 RPM (2-Speed)",
            "Max Air Volume": "2.7 m³/min (95 CFM)",
            "Speed Settings": "2-Speed Slide Switch",
            "Features": "Lightweight Compact Body, Ergonomic Soft Grip"
        }
    },
    {
        "sku": "CDLI 1228",
        "name": "INGCO 12V Cordless Drill Driver 25Nm (CDLI 1228)",
        "category_id": "cat_ingco_cordless",
        "subcategory": "Cordless Drills & Screwdrivers",
        "price": 2150.00,
        "badge": "25Nm Torque + 2 Batteries",
        "description": "Powerful 12V cordless drill driver delivering 25Nm maximum torque, 15+1 torque clutch settings, 0.8-10mm keyless chuck, integrated LED work light, 2x 1.5Ah lithium batteries, charger, and carrying case.",
        "specs": {
            "Model Number": "CDLI 1228",
            "Voltage": "12V",
            "Max Torque": "25 Nm",
            "Chuck Capacity": "0.8 - 10 mm Keyless",
            "Torque Settings": "15 + 1",
            "Included Accessories": "2x 1.5Ah Batteries, 1x Charger, 1x Cr-V Bit, Plastic BMC Case"
        }
    },
    {
        "sku": "CSDLI 08025",
        "name": "INGCO 8V Cordless Screwdriver 17Pcs Set (CSDLI 08025)",
        "category_id": "cat_ingco_cordless",
        "subcategory": "Cordless Drills & Screwdrivers",
        "price": 1350.00,
        "badge": "8V 6Nm + Type-C USB",
        "description": "Versatile 8V lithium-ion cordless screwdriver with 6Nm torque, convenient Type-C USB charging, 2-position dual-angle pivoting handle, built-in LED front worklight, and 17 Pcs screwdriver bits & accessories set in a storage case.",
        "specs": {
            "Model Number": "CSDLI 08025",
            "Voltage": "8V",
            "Max Torque": "6 Nm",
            "No-Load Speed": "220 RPM",
            "Handle Type": "Dual-Position Rotating Pivot Handle (Straight & Pistol)",
            "Charging Port": "Type-C USB Charging",
            "Included Accessories": "17 Pcs Bits & Accessories, USB Cable, Storage Case"
        }
    },
    {
        "sku": "HLDD0355",
        "name": "INGCO 35M Digital Laser Distance Detector (HLDD0355)",
        "category_id": "cat_ingco_measuring",
        "subcategory": "Laser Distance Meters",
        "price": 1650.00,
        "badge": "35m Range ±2.0mm",
        "description": "High-precision 35-meter digital laser distance meter with ±2.0mm accuracy, multi-function measurement modes (distance, area, volume, indirect Pythagoras), backlit LCD display, and includes LR03 AAA batteries.",
        "specs": {
            "Model Number": "HLDD0355",
            "Measuring Range": "0.05 m - 35 m (115 ft)",
            "Measuring Accuracy": "± 2.0 mm",
            "Laser Type": "635 nm, < 1 mW, Class 2",
            "Functions": "Single/Continuous Distance, Area, Volume, Pythagoras Calculation",
            "Battery Type": "2x 1.5V LR03 AAA (Included)"
        }
    }
]

for p in new_products:
    sku = p["sku"]
    img_url = cloud_urls.get(sku)
    if not img_url:
        print(f"Error: Missing image for {sku}")
        continue
    
    prod_id = "prod_ingco_" + sku.replace(" ", "_").lower()
    specs_json = json.dumps(p["specs"], ensure_ascii=False)
    
    cursor.execute("SELECT id FROM products WHERE id = %s OR sku = %s", (prod_id, sku))
    row = cursor.fetchone()
    if not row:
        cursor.execute("""
            INSERT INTO products (
                id, sku, name, brand_id, brand, category_id, subcategory,
                price, badge, in_stock, image, description, specs, rating, reviews, created_at, updated_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 1, %s, %s, %s, 4.9, 28, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        """, (
            prod_id, sku, p["name"], brand_id, "INGCO", p["category_id"], p["subcategory"],
            p["price"], p["badge"], img_url, p["description"], specs_json
        ))
        print(f"[INSERTED] {p['name']} -> {img_url}")
    else:
        cursor.execute("""
            UPDATE products SET
                sku = %s, name = %s, brand_id = %s, brand = 'INGCO', category_id = %s, subcategory = %s,
                price = %s, badge = %s, in_stock = 1, image = %s, description = %s, specs = %s, updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """, (
            sku, p["name"], brand_id, p["category_id"], p["subcategory"],
            p["price"], p["badge"], img_url, p["description"], specs_json, row["id"]
        ))
        print(f"[UPDATED] {p['name']} -> {img_url}")

conn.commit()

# Sync to SQLite tarang.db
import sqlite3
sq_conn = sqlite3.connect("tarang.db")
sq_cur = sq_conn.cursor()

# Sync categories
cursor.execute("SELECT * FROM categories WHERE brand_id = %s", (brand_id,))
for c in cursor.fetchall():
    c = dict(c)
    sq_cur.execute("INSERT OR REPLACE INTO categories (id, brand_id, title, short_title, tagline, icon, color, display_order) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                   (c['id'], c['brand_id'], c['title'], c['short_title'], c['tagline'], c['icon'], c['color'], c['display_order']))

# Sync subcategories
cursor.execute("SELECT s.* FROM subcategories s JOIN categories c ON s.category_id = c.id WHERE c.brand_id = %s", (brand_id,))
for s in cursor.fetchall():
    s = dict(s)
    sq_cur.execute("INSERT OR REPLACE INTO subcategories (id, category_id, name, display_order) VALUES (?, ?, ?, ?)",
                   (s['id'], s['category_id'], s['name'], s['display_order']))

# Sync products
cursor.execute("SELECT * FROM products WHERE brand_id = %s", (brand_id,))
for pr in cursor.fetchall():
    pr = dict(pr)
    sq_cur.execute("""
        INSERT OR REPLACE INTO products (id, sku, name, brand_id, brand, category_id, subcategory, price, badge, in_stock, image, description, specs, rating, reviews)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (pr['id'], pr['sku'], pr['name'], pr['brand_id'], pr['brand'], pr['category_id'], pr['subcategory'], pr['price'], pr['badge'], pr['in_stock'], pr['image'], pr['description'], pr['specs'], pr['rating'], pr['reviews']))

sq_conn.commit()

cursor.execute("SELECT COUNT(*) as cnt FROM products WHERE brand_id = %s", (brand_id,))
total_pg = cursor.fetchone()["cnt"]
print(f"\n--- SUCCESS ---")
print(f"Total INGCO products in PostgreSQL: {total_pg}")
print(f"Total INGCO products in SQLite: {sq_cur.execute('SELECT COUNT(*) FROM products WHERE brand_id = \'brand_ingco\'').fetchone()[0]}")

sq_conn.close()
conn.close()
