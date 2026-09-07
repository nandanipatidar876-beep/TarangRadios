import sys
import os
import json
import shutil

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db import get_db
import cloudinary_service

print("--- STARTING INGCO BRAND PRODUCTS INTEGRATION ---")

# 1. Image Files Mapping
USER_UPLOADED_DIR = r"C:\Users\dell\.gemini\antigravity-ide\brain\952646ab-afb6-443e-baaf-3519dc6a63ae\.user_uploaded"
TARGET_IMG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "uploads", "brands", "ingco")
os.makedirs(TARGET_IMG_DIR, exist_ok=True)

image_mapping = {
    "media_1788756699796.jpg": "ingco_si01606_70w_soldering_iron.jpg",
    "media_1788756719060.jpg": "ingco_si0248_40w_soldering_iron.jpg",
    "media_1788756734735.jpg": "ingco_gg148_20w_glue_gun.jpg",
    "media_1788756748575.jpg": "ingco_akb1012_mounted_grinding_stones.jpg",
    "media_1788756763641.jpg": "ingco_mg13328_130w_mini_grinder.jpg",
}

final_img_urls = {}

for src_name, dst_name in image_mapping.items():
    src_path = os.path.join(USER_UPLOADED_DIR, src_name)
    dst_path = os.path.join(TARGET_IMG_DIR, dst_name)
    if os.path.exists(src_path):
        shutil.copy2(src_path, dst_path)
        print(f"Copied {src_name} -> {dst_path}")
    
    # Check Cloudinary
    cloud_url = None
    if os.path.exists(dst_path):
        cloud_res = cloudinary_service.upload_image(dst_path, folder="tarang_radio/brands/ingco")
        if cloud_res and cloud_res.get("secure_url"):
            cloud_url = cloud_res.get("secure_url")
            print(f"Uploaded to Cloudinary: {cloud_url}")
    
    local_rel_url = f"uploads/brands/ingco/{dst_name}"
    final_img_urls[dst_name] = cloud_url or local_rel_url

conn = get_db()
cursor = conn.cursor()

# 2. Ensure INGCO Brand Exists
cursor.execute("SELECT id FROM brands WHERE id = 'brand_ingco' OR LOWER(name) = 'ingco'")
brand_row = cursor.fetchone()
brand_id = "brand_ingco"
if not brand_row:
    cursor.execute("""
        INSERT INTO brands (id, name, display_order, is_enabled, created_at, updated_at)
        VALUES ('brand_ingco', 'INGCO', 6, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
    """)
    conn.commit()
    print("Created INGCO brand partner.")
else:
    brand_id = brand_row["id"]
    cursor.execute("UPDATE brands SET is_enabled = 1 WHERE id = ?", (brand_id,))
    conn.commit()

# 3. Create INGCO Brand Categories (STRICTLY tied to brand_ingco!)
categories_def = [
    {
        "id": "cat_ingco_soldering",
        "brand_id": brand_id,
        "title": "INGCO Soldering & Welding Tools",
        "short_title": "INGCO Soldering",
        "tagline": "Professional Temperature-Controlled & Electric Soldering Irons",
        "icon": "zap",
        "color": "#F2C94C",
        "display_order": 1
    },
    {
        "id": "cat_ingco_rotary",
        "brand_id": brand_id,
        "title": "INGCO Mini Grinder & Rotary Sets",
        "short_title": "INGCO Rotary Tools",
        "tagline": "Precision 130W Rotary Tools, Flex Shafts & Abrasive Stones",
        "icon": "settings",
        "color": "#D14B14",
        "display_order": 2
    },
    {
        "id": "cat_ingco_glue",
        "brand_id": brand_id,
        "title": "INGCO Hot Glue Guns & Adhesives",
        "short_title": "INGCO Glue Guns",
        "tagline": "Fast Heating Electric Glue Guns & Glue Sticks",
        "icon": "flame",
        "color": "#F2C94C",
        "display_order": 3
    }
]

for cat in categories_def:
    cursor.execute("SELECT id FROM categories WHERE id = ?", (cat["id"],))
    if not cursor.fetchone():
        cursor.execute("""
            INSERT INTO categories (id, brand_id, title, short_title, tagline, icon, color, display_order, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        """, (cat["id"], cat["brand_id"], cat["title"], cat["short_title"], cat["tagline"], cat["icon"], cat["color"], cat["display_order"]))
        print(f"Created category {cat['title']}")
    else:
        cursor.execute("""
            UPDATE categories SET brand_id = ?, title = ?, short_title = ?, tagline = ? WHERE id = ?
        """, (cat["brand_id"], cat["title"], cat["short_title"], cat["tagline"], cat["id"]))

conn.commit()

# 4. Create Subcategories for INGCO (subcategories table schema: id, category_id, name, display_order)
subcategories_def = [
    {"id": "sub_ingco_soldering_irons", "category_id": "cat_ingco_soldering", "name": "Soldering Irons", "display_order": 1},
    {"id": "sub_ingco_rotary_tools", "category_id": "cat_ingco_rotary", "name": "Rotary Tools & Accessories", "display_order": 1},
    {"id": "sub_ingco_glue_guns", "category_id": "cat_ingco_glue", "name": "Hot Melt Glue Guns", "display_order": 1},
]

for sub in subcategories_def:
    cursor.execute("SELECT id FROM subcategories WHERE id = ?", (sub["id"],))
    if not cursor.fetchone():
        cursor.execute("""
            INSERT INTO subcategories (id, category_id, name, display_order)
            VALUES (?, ?, ?, ?)
        """, (sub["id"], sub["category_id"], sub["name"], sub["display_order"]))
        print(f"Created subcategory {sub['name']}")

conn.commit()

# 5. Insert / Update the 5 INGCO Products (STRICTLY tied to brand_ingco!)
products_def = [
    {
        "id": "prod_ingco_si01606",
        "sku": "SI01606",
        "name": "INGCO 70W Temperature Control Soldering Iron (SI01606)",
        "brand_id": brand_id,
        "brand": "INGCO",
        "category_id": "cat_ingco_soldering",
        "subcategory": "Soldering Irons",
        "price": 450.00,
        "badge": "Ceramic Core",
        "in_stock": 1,
        "image": final_img_urls.get("ingco_si01606_70w_soldering_iron.jpg"),
        "description": "Professional INGCO 70W electric soldering iron with built-in ceramic heating core, quick 120-second preheating, adjustable temperature control knob, On/Off power switch, and long-life replaceable tip.",
        "specs": json.dumps({
            "Model Number": "SI01606",
            "Input Power": "70W",
            "Voltage": "220-240V ~ 50/60Hz",
            "Heating Core": "Ceramic Heating Element",
            "Temperature Control": "Adjustable Knob (200°C - 500°C)",
            "Preheat Time": "120 - 180 seconds",
            "Features": "On/Off Power Switch, Long Life Tip",
            "Warranty": "INGCO Official Brand Warranty"
        }, ensure_ascii=False),
        "rating": 4.9,
        "reviews": 38
    },
    {
        "id": "prod_ingco_si0248",
        "sku": "SI0248",
        "name": "INGCO 40W Electric Soldering Iron (SI0248)",
        "brand_id": brand_id,
        "brand": "INGCO",
        "category_id": "cat_ingco_soldering",
        "subcategory": "Soldering Irons",
        "price": 240.00,
        "badge": "Titan Heater",
        "in_stock": 1,
        "image": final_img_urls.get("ingco_si0248_40w_soldering_iron.jpg"),
        "description": "Reliable INGCO 40W electric soldering iron equipped with long-life titan heater, fast thermal recovery, straight replaceable tip, EU 2-pin plug, and ergonomic non-slip handle.",
        "specs": json.dumps({
            "Model Number": "SI0248",
            "Input Power": "40W",
            "Voltage": "220-240V ~ 50/60Hz",
            "Heater Type": "Long Life Titan Heater",
            "Preheat Time": "3 - 5 minutes",
            "Tip Type": "Straight Replaceable Long Life Tip",
            "Plug Standard": "EU 2-Pin",
            "Warranty": "INGCO Official Brand Warranty"
        }, ensure_ascii=False),
        "rating": 4.8,
        "reviews": 29
    },
    {
        "id": "prod_ingco_gg148",
        "sku": "GG148",
        "name": "INGCO 20W (Max 100W) Hot Melt Glue Gun (GG148)",
        "brand_id": brand_id,
        "brand": "INGCO",
        "category_id": "cat_ingco_glue",
        "subcategory": "Hot Melt Glue Guns",
        "price": 380.00,
        "badge": "Max 100W Peak",
        "in_stock": 1,
        "image": final_img_urls.get("ingco_gg148_20w_glue_gun.jpg"),
        "description": "Heavy-duty INGCO 20W (Max 100W peak) hot melt glue gun compatible with 11.2mm glue sticks. Features PTC heating element, ergonomic trigger, fold-down stand, and includes 2 Pcs 11mm glue sticks.",
        "specs": json.dumps({
            "Model Number": "GG148",
            "Input Power": "20W (Max 100W Peak)",
            "Voltage": "220-240V ~ 50/60Hz",
            "Glue Stick Diameter": "11.2mm (Ø11mm)",
            "Gluing Capacity": "13 - 18 g/min",
            "Preheat Time": "3 - 5 minutes",
            "Included Accessories": "2 Pcs Ø11mm Glue Sticks",
            "Warranty": "INGCO Official Brand Warranty"
        }, ensure_ascii=False),
        "rating": 4.9,
        "reviews": 42
    },
    {
        "id": "prod_ingco_akb1012",
        "sku": "AKB1012",
        "name": "INGCO 10Pcs Mounted Grinding Stone Set (AKB1012)",
        "brand_id": brand_id,
        "brand": "INGCO",
        "category_id": "cat_ingco_rotary",
        "subcategory": "Rotary Tools & Accessories",
        "price": 160.00,
        "badge": "3mm Shank",
        "in_stock": 1,
        "image": final_img_urls.get("ingco_akb1012_mounted_grinding_stones.jpg"),
        "description": "Precision 10Pcs INGCO aluminum oxide mounted grinding stone set with standard 3mm shank for rotary mini grinders (MG13328). Includes bullet, cone, T-type, and round grinding stones.",
        "specs": json.dumps({
            "Model Number": "AKB1012",
            "Set Count": "10 Pieces per Set",
            "Shank Diameter": "3mm (1/8 inch)",
            "Material": "High-Grade Aluminum Oxide Abrasive",
            "Compatible Tools": "INGCO Mini Grinders (MG13328, MG2008)",
            "Set Contents": "2 Pcs Bullet, 4 Pcs Cone, 2 Pcs T-Type, 2 Pcs Round Stones",
            "Packaging": "Blister Display Box (50 Sets / Box)"
        }, ensure_ascii=False),
        "rating": 4.7,
        "reviews": 19
    },
    {
        "id": "prod_ingco_mg13328",
        "sku": "MG13328",
        "name": "INGCO 130W Variable Speed Mini Grinder Kit (MG13328)",
        "brand_id": brand_id,
        "brand": "INGCO",
        "category_id": "cat_ingco_rotary",
        "subcategory": "Rotary Tools & Accessories",
        "price": 1850.00,
        "badge": "109Pcs Kit + Flex Shaft",
        "in_stock": 1,
        "image": final_img_urls.get("ingco_mg13328_130w_mini_grinder.jpg"),
        "description": "High-precision INGCO 130W variable speed rotary tool & mini grinder kit (10,000 - 35,000 RPM) with flexible extension shaft, 109 Pcs accessories set, replacement carbon brushes, and heavy-duty blow-molded carrying case.",
        "specs": json.dumps({
            "Model Number": "MG13328",
            "Input Power": "130W",
            "Voltage": "220-240V ~ 50/60Hz",
            "No-Load Speed": "10,000 - 35,000 RPM (6 Speed Control)",
            "Collet Capacity": "3.2mm / 2.3mm",
            "Included Accessories": "109 Pcs Accessories + Flexible Extension Shaft",
            "Case Type": "Heavy Duty BMC Carrying Case",
            "Warranty": "INGCO Official Brand Warranty"
        }, ensure_ascii=False),
        "rating": 4.9,
        "reviews": 65
    }
]

for p in products_def:
    cursor.execute("SELECT id FROM products WHERE id = ?", (p["id"],))
    if not cursor.fetchone():
        cursor.execute("""
            INSERT INTO products (
                id, sku, name, brand_id, brand, category_id, subcategory,
                price, badge, in_stock, image, description, specs, rating, reviews, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        """, (
            p["id"], p["sku"], p["name"], p["brand_id"], p["brand"], p["category_id"], p["subcategory"],
            p["price"], p["badge"], p["in_stock"], p["image"], p["description"], p["specs"], p["rating"], p["reviews"]
        ))
        print(f"Inserted product: {p['name']}")
    else:
        cursor.execute("""
            UPDATE products SET
                sku = ?, name = ?, brand_id = ?, brand = ?, category_id = ?, subcategory = ?,
                price = ?, badge = ?, in_stock = ?, image = ?, description = ?, specs = ?
            WHERE id = ?
        """, (
            p["sku"], p["name"], p["brand_id"], p["brand"], p["category_id"], p["subcategory"],
            p["price"], p["badge"], p["in_stock"], p["image"], p["description"], p["specs"], p["id"]
        ))
        print(f"Updated product: {p['name']}")

conn.commit()
conn.close()

print("--- INGCO INTEGRATION COMPLETED SUCCESSFULLY ---")
