"""
=============================================================================
TARANG RADIOS - ALCOP INDIA BRAND CATALOG SCRAPER & SYNC ENGINE
Scrapes products, pitch sizes, rated currents, and wire specs from ALCOP India (https://www.alcopwires.com/)
Uploads high-res images to Cloudinary under brand/alcop folder hierarchy.
Seeds database (both local SQLite tarang.db and production PostgreSQL)
strictly isolated under the brand partner: "ALCOP".
=============================================================================
"""

import os
import sys
import re
import json
import time
import ssl
import urllib.request
import urllib.parse
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
except ImportError:
    pass

import cloudinary
import cloudinary.uploader
from db import get_db, get_engine_type
from migrate import run_all_migrations

# Cloudinary Setup
CLOUDINARY_CONFIGURED = False
cloud_name = os.environ.get("CLOUDINARY_CLOUD_NAME", "").strip()
api_key = os.environ.get("CLOUDINARY_API_KEY", "").strip()
api_secret = os.environ.get("CLOUDINARY_API_SECRET", "").strip()

if cloud_name and api_key and api_secret:
    cloudinary.config(
        cloud_name=cloud_name,
        api_key=api_key,
        api_secret=api_secret,
        secure=True
    )
    CLOUDINARY_CONFIGURED = True

CACHE_FILE = os.path.join(os.path.dirname(__file__), "cloudinary_alcop_cache.json")
cache_lock = threading.RLock()
ssl_ctx = ssl._create_unverified_context()
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}

def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r'[^a-z0-9]+', '_', text)
    return text.strip('_')

def load_upload_cache() -> dict:
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_upload_cache(cache: dict):
    with cache_lock:
        try:
            with open(CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(cache, f, indent=2)
        except Exception as e:
            print(f"[CACHE ERROR] Could not save cache: {e}")

def fetch_page(url: str) -> str:
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=15, context=ssl_ctx) as resp:
        return resp.read().decode("utf-8", errors="ignore")

def extract_alcop_catalog():
    cat_pages = [
        ("flexible-wires.html", "Flexible Wires", "Multi-strand flexible copper wires & cables", "#2563EB"),
        ("electronic-wires.html", "Electronic Wires", "Single core & hookup electronic wires", "#4F46E5"),
        ("relimate-connector.html", "Relimate Connector", "RMC, JST & pitch connectors (02-16 pin)", "#7C3AED"),
        ("hookup-wires.html", "Hookup Wires", "PVC insulated tinned copper hookup wires", "#0D9488"),
        ("cable-connector.html", "Cable Connector", "Wire to wire, DC pin & harness connectors", "#D97706"),
        ("ribbon-cables.html", "Ribbon Cables", "Multi-color flat ribbon cables & wires", "#DC2626"),
        ("house-wire.html", "House Wire", "Heat resistant PVC insulated building wires", "#EA580C"),
        ("electronic-cables.html", "Electronic Cables", "Multi-core shielded & unshielded cables", "#0891B2"),
        ("electrical-wires.html", "Electrical Wires", "0.5mm to 4.0mm electrical copper wires", "#059669"),
        ("led-wires.html", "LED Wires", "Tinned copper driver wires for LED fixtures", "#84CC16")
    ]

    brand_categories = {}
    brand_subcategories = {}
    catalog_items = []
    seen_prod_keys = set()

    print("[ALCOP SCRAPER] Connecting to ALCOP India (https://www.alcopwires.com/)...", flush=True)

    for page_file, main_cat_title, tagline, color in cat_pages:
        url = f"https://www.alcopwires.com/{page_file}"
        cat_id = f"cat_alcop_{slugify(main_cat_title)}"

        try:
            page_html = fetch_page(url)
            print(f"  -> Fetched '{main_cat_title}' ({len(page_html):,} bytes)", flush=True)
        except Exception as e:
            print(f"  [ERROR] Failed to fetch {page_file}: {e}", flush=True)
            continue

        brand_categories[cat_id] = {
            "id": cat_id,
            "title": main_cat_title,
            "short_title": main_cat_title,
            "tagline": tagline,
            "icon": "cable",
            "color": color,
            "image": "",
            "display_order": len(brand_categories)
        }

        # Find each product card section
        card_sections = re.findall(
            r'<div[^>]*class=[\'"][^\'"]*prdCard\s+prdCardNew[^\'"]*[\'"]>(.*?)(?=<div[^>]*class=[\'"][^\'"]*prdCard\s+prdCardNew|\s*<footer|\s*<div[^>]*class=[\'"][^\'"]*prdRng|\Z)',
            page_html,
            re.DOTALL | re.IGNORECASE
        )

        for c in card_sections:
            # 1. Product Title
            t_m = re.search(r'<(?:h2|h3|h4|a)[^>]*>(.*?)</(?:h2|h3|h4|a)>', c, re.IGNORECASE | re.DOTALL)
            raw_title = re.sub(r'<[^>]+>', '', t_m.group(1)).strip() if t_m else ""
            if not raw_title or any(k in raw_title.lower() for k in ['send enquiry', 'price on request', 'contact us', 'alcop cables', 'manufacturer', 'about us', 'privacy', 'terms', 'explore more']):
                continue

            # 2. Image Extraction
            imgs = re.findall(r'(?:dataimg|src)=[\'"](https://[^\'"]*(?:imimg|alcop)[^\'"]*(?:\.jpg|\.png|\.jpeg|\.webp))[\'"]', c, re.IGNORECASE)
            main_img = ""
            for img in imgs:
                if 'SELLER' in img or 'data5' in img or 'data4' in img:
                    main_img = re.sub(r'-\d+x\d+\.', '-500x500.', img)
                    break
            if not main_img and imgs:
                main_img = imgs[0]

            # 3. Key-Value Specifications
            specs = {}
            spec_pairs = re.findall(
                r'<span[^>]*class=[\'"][^\'"]*clr3[^\'"]*[\'"][^>]*>(.*?)</span>\s*[:\-]?\s*<(?:span|b|a)[^>]*class=[\'"][^\'"]*(?:clr2|clr1|fwb)[^\'"]*[\'"][^>]*>(.*?)</(?:span|b|a)>',
                c, re.DOTALL | re.IGNORECASE
            )
            for k, v in spec_pairs:
                ck = re.sub(r'<[^>]+>', '', k).strip().rstrip(':')
                cv = re.sub(r'<[^>]+>', '', v).strip()
                if ck and cv:
                    specs[ck] = cv

            if not specs:
                td_pairs = re.findall(r'<td[^>]*>(.*?)</td>\s*<td[^>]*>(.*?)</td>', c, re.DOTALL | re.IGNORECASE)
                for k, v in td_pairs:
                    ck = re.sub(r'<[^>]+>', '', k).strip().rstrip(':')
                    cv = re.sub(r'<[^>]+>', '', v).strip()
                    if ck and cv:
                        specs[ck] = cv

            # 4. Extract Pitch Size, Rated Current, Voltage, Pins, Wire Size
            pitch = specs.get('Pitch') or specs.get('Pitch Size') or specs.get('pitch') or ""
            current = specs.get('Rated Current') or specs.get('Current Rating') or specs.get('Current') or specs.get('Amp Capacity') or ""
            voltage = specs.get('Rated Voltage') or specs.get('Voltage Rating') or specs.get('Voltage') or specs.get('Voltage Grade') or ""
            conductor = specs.get('Conductor Material') or specs.get('Conductor Type') or specs.get('Conductor') or ""
            wire_size = specs.get('Wire Size') or specs.get('Conductor Size') or specs.get('Size') or specs.get('Conductor Cross-sectional Area') or ""
            pins = specs.get('Number Of Pins') or specs.get('No. Of Pins') or specs.get('Pin Count') or specs.get('No of Pins') or specs.get('Number of Pins') or ""

            if not pitch:
                p_m = re.search(r'(?:Pitch(?:\s*Size)?)\s*[:\-]?\s*([0-9\.]+\s*(?:mm|mil)?)', c, re.IGNORECASE)
                if p_m: pitch = p_m.group(1).strip()
            if not current:
                c_m = re.search(r'(?:Rated\s*Current|Current\s*Rating|Amp\s*Capacity)\s*[:\-]?\s*([0-9\.]+\s*(?:Amp|Amps|A)?)', c, re.IGNORECASE)
                if c_m: current = c_m.group(1).strip()

            # Enriched Title with ALCOP branding
            prod_title = raw_title
            if not prod_title.lower().startswith("alcop"):
                prod_title = f"ALCOP {prod_title}"

            # Subcategory grouping
            subcat_title = "Standard Series"
            if "connector" in main_cat_title.lower():
                if pitch:
                    subcat_title = f"{pitch} Pitch Connectors"
                elif pins:
                    subcat_title = f"{pins} Series"
                else:
                    subcat_title = "Connectors & Terminals"
            elif "wire" in main_cat_title.lower() or "cable" in main_cat_title.lower():
                if wire_size:
                    subcat_title = f"{wire_size} Range"
                elif conductor:
                    subcat_title = f"{conductor} Series"
                else:
                    subcat_title = "Single & Multi Core"

            sub_id = f"sub_alcop_{slugify(main_cat_title)}_{slugify(subcat_title)}"
            if sub_id not in brand_subcategories:
                brand_subcategories[sub_id] = {
                    "id": sub_id,
                    "category_id": cat_id,
                    "name": subcat_title,
                    "display_order": len(brand_subcategories)
                }

            # Highlights Description
            desc_parts = []
            if pitch: desc_parts.append(f"Pitch Size: {pitch}")
            if current: desc_parts.append(f"Rated Current: {current}")
            if voltage: desc_parts.append(f"Voltage Rating: {voltage}")
            if pins: desc_parts.append(f"Pins: {pins}")
            if wire_size: desc_parts.append(f"Wire Size: {wire_size}")
            if conductor: desc_parts.append(f"Conductor: {conductor}")
            for k, v in list(specs.items())[:3]:
                if k not in ['Pitch', 'Rated Current', 'Current Rating', 'Rated Voltage', 'Brand', 'Pitch Size']:
                    desc_parts.append(f"{k}: {v}")

            final_desc = " • ".join(desc_parts) if desc_parts else f"Genuine ALCOP {main_cat_title} - High durability industrial grade."

            prod_key = f"{cat_id}_{slugify(raw_title)}"
            if prod_key in seen_prod_keys:
                continue
            seen_prod_keys.add(prod_key)

            if not brand_categories[cat_id]["image"] and main_img:
                brand_categories[cat_id]["image"] = main_img

            catalog_items.append({
                "id": prod_key,
                "prod_db_id": f"prod_{prod_key}",
                "sku": f"ALCOP-{re.sub(r'[^a-z0-9]+', '', raw_title.lower()).upper()[:12]}",
                "name": prod_title,
                "category_id": cat_id,
                "category_title": main_cat_title,
                "subcategory": subcat_title,
                "sub_id": sub_id,
                "price": 0.0,
                "in_stock": 1,
                "source_image_url": main_img,
                "description": final_desc,
                "specs": json.dumps({
                    "brand": "ALCOP India",
                    "product_name": raw_title,
                    "pitch_size": pitch or "Standard",
                    "rated_current": current or "Standard",
                    "voltage_rating": voltage or "N/A",
                    "number_of_pins": pins or "N/A",
                    "wire_size": wire_size or "N/A",
                    "conductor_material": conductor or "Copper",
                    "all_specs": specs
                })
            })

    return brand_categories, brand_subcategories, catalog_items

def upload_alcop_image(item: dict, cache: dict) -> tuple:
    source_url = item["source_image_url"]
    item_id = item["id"]
    cat_slug = slugify(item["category_title"])
    sub_slug = slugify(item["subcategory"])

    if not source_url:
        return item_id, ""

    with cache_lock:
        if source_url in cache:
            return item_id, cache[source_url]

    if not CLOUDINARY_CONFIGURED:
        return item_id, source_url

    public_id = f"tarang_radio/brands/alcop/{cat_slug}/{sub_slug}/{item_id}"
    try:
        res = cloudinary.uploader.upload(
            source_url,
            public_id=public_id,
            overwrite=False,
            resource_type="image",
            transformation=[{"quality": "auto", "fetch_format": "auto"}]
        )
        secure_url = res.get("secure_url", source_url)
        with cache_lock:
            cache[source_url] = secure_url
        return item_id, secure_url
    except Exception as e:
        print(f"  [UPLOAD WARNING] Cloudinary failed for {item['name']}: {e}", flush=True)
        return item_id, source_url

def sync_alcop_catalog(db_url: str = None, workers: int = 15, dry_run: bool = False, skip_images: bool = False):
    print("=================================================================")
    print("      ALCOP INDIA -> TARANG RADIOS BRAND CATALOG SYNC            ")
    print("=================================================================")
    print(f"Source URL       : https://www.alcopwires.com")
    print(f"Target Brand     : ALCOP [The Brands We Deal With]")
    print(f"Database Engine  : {get_engine_type().upper()}")
    print(f"Cloudinary Mode  : {'Configured' if CLOUDINARY_CONFIGURED else 'Disabled (Using source URLs)'}")
    print(f"Upload Workers   : {workers} threads")
    print(f"Dry Run Mode     : {'YES' if dry_run else 'NO (Live Execution)'}")
    print("-----------------------------------------------------------------")

    # 1. Scrape ALCOP India
    brand_categories, brand_subcategories, catalog_items = extract_alcop_catalog()

    print(f"\n[STEP 1] Structured ALCOP Catalog:")
    print(f"  -> {len(brand_categories)} Brand Categories under ALCOP")
    print(f"  -> {len(brand_subcategories)} Brand Subcategories under ALCOP")
    print(f"  -> {len(catalog_items)} ALCOP Products extracted")

    # 2. Upload Images to Cloudinary
    product_image_urls = {}
    cache = load_upload_cache()

    if dry_run:
        print(f"\n[STEP 2] [DRY RUN] Would upload {len(catalog_items)} images to Cloudinary.")
        return True
    elif skip_images:
        print("\n[STEP 2] Skipping Cloudinary upload (--skip-images flag active).")
        for item in catalog_items:
            img = cache.get(item["source_image_url"]) or item["source_image_url"]
            product_image_urls[item["id"]] = img
    else:
        print(f"\n[STEP 2] Uploading images to Cloudinary ({workers} worker threads with auto-resume)...")
        t0 = time.time()
        completed = 0
        total = len(catalog_items)

        with ThreadPoolExecutor(max_workers=workers) as executor:
            future_to_item = {
                executor.submit(upload_alcop_image, item, cache): item
                for item in catalog_items
            }

            for future in as_completed(future_to_item):
                p_id, final_url = future.result()
                product_image_urls[p_id] = final_url
                completed += 1
                if completed % 5 == 0 or completed == total:
                    pct = (completed / total) * 100
                    print(f"  -> Progress: {completed}/{total} ({pct:.1f}%) uploaded...", flush=True)

        save_upload_cache(cache)
        duration = time.time() - t0
        print(f"  [OK] Image synchronization completed in {duration:.1f}s.", flush=True)

    # 3. Database Seeder (Supports both SQLite tarang.db and PostgreSQL)
    def seed_db_target(db_conn_str, label):
        print(f"\n[STEP 3] Seeding ALCOP Catalog into Database ({label})...", flush=True)
        if db_conn_str:
            os.environ["DATABASE_URL"] = db_conn_str
        else:
            os.environ["DATABASE_URL"] = ""

        run_all_migrations()
        now_iso = datetime.now().isoformat()

        with get_db() as db:
            # 1. Resolve ALCOP Brand ID dynamically (e.g., 'b3' or 'brand_alcop')
            existing_brand = db.fetchone("SELECT id, name FROM brands WHERE LOWER(name) = 'alcop'")
            if existing_brand:
                alcop_brand_id = existing_brand["id"]
                db.execute("UPDATE brands SET is_enabled = 1, updated_at = ? WHERE id = ?", (now_iso, alcop_brand_id))
                db.commit()
            else:
                alcop_brand_id = "brand_alcop"
                db.execute("""
                    INSERT INTO brands (id, name, display_order, is_enabled, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    ON CONFLICT (id) DO UPDATE SET
                        name = EXCLUDED.name,
                        is_enabled = EXCLUDED.is_enabled,
                        updated_at = EXCLUDED.updated_at
                """, (alcop_brand_id, "Alcop", 2, 1, now_iso, now_iso))
                db.commit()
            print(f"  -> [OK] Brand 'ALCOP' (ID: '{alcop_brand_id}') verified in brands table.", flush=True)

            # 2. Upsert Brand Categories (brand_id = alcop_brand_id)
            cat_rows = []
            for cat in brand_categories.values():
                cat_img = product_image_urls.get(cat.get("sample_prod_id")) or cat["image"]
                cat_rows.append((
                    cat["id"],
                    alcop_brand_id,
                    cat["title"],
                    cat["short_title"],
                    cat["tagline"],
                    cat["icon"],
                    cat_img,
                    cat["color"],
                    cat["display_order"],
                    now_iso,
                    now_iso
                ))

            db.executemany("""
                INSERT INTO categories (id, brand_id, title, short_title, tagline, icon, image, color, display_order, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT (id) DO UPDATE SET
                    brand_id = EXCLUDED.brand_id,
                    title = EXCLUDED.title,
                    short_title = EXCLUDED.short_title,
                    tagline = EXCLUDED.tagline,
                    image = EXCLUDED.image,
                    updated_at = EXCLUDED.updated_at
            """, cat_rows)
            db.commit()
            print(f"  -> [OK] {len(cat_rows)} Brand Categories upserted under ALCOP.", flush=True)

            # 3. Upsert Brand Subcategories
            sub_rows = []
            for sub in brand_subcategories.values():
                sub_rows.append((
                    sub["id"],
                    sub["category_id"],
                    sub["name"],
                    sub["display_order"]
                ))

            db.executemany("""
                INSERT INTO subcategories (id, category_id, name, display_order)
                VALUES (?, ?, ?, ?)
                ON CONFLICT (id) DO UPDATE SET
                    name = EXCLUDED.name,
                    display_order = EXCLUDED.display_order
            """, sub_rows)
            db.commit()
            print(f"  -> [OK] {len(sub_rows)} Brand Subcategories upserted under ALCOP.", flush=True)

            # 4. Upsert Brand Products
            prod_rows = []
            for item in catalog_items:
                final_img = product_image_urls.get(item["id"]) or cache.get(item["source_image_url"]) or item["source_image_url"]
                badge = "In Stock" if item["in_stock"] else "Out of Stock"

                prod_rows.append((
                    item["prod_db_id"],
                    item["sku"],
                    item["name"],
                    alcop_brand_id,
                    "Alcop",
                    item["category_id"],
                    item["subcategory"],
                    item["price"],
                    badge,
                    item["in_stock"],
                    final_img,
                    item["description"],
                    item["specs"],
                    5.0,
                    0,
                    now_iso,
                    now_iso
                ))

            db.executemany("""
                INSERT INTO products (id, sku, name, brand_id, brand, category_id, subcategory, price, badge, in_stock, image, description, specs, rating, reviews, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT (id) DO UPDATE SET
                    name = EXCLUDED.name,
                    sku = EXCLUDED.sku,
                    brand_id = EXCLUDED.brand_id,
                    brand = EXCLUDED.brand,
                    category_id = EXCLUDED.category_id,
                    subcategory = EXCLUDED.subcategory,
                    price = EXCLUDED.price,
                    badge = EXCLUDED.badge,
                    in_stock = EXCLUDED.in_stock,
                    image = EXCLUDED.image,
                    description = EXCLUDED.description,
                    specs = EXCLUDED.specs,
                    updated_at = EXCLUDED.updated_at
            """, prod_rows)
            db.commit()
            print(f"  -> [OK] {len(prod_rows)} ALCOP Products upserted under ALCOP brand.", flush=True)

    # Seed primary DB (e.g. Postgres from .env or db_url)
    primary_db = db_url or os.environ.get("DATABASE_URL", "")
    seed_db_target(primary_db, get_engine_type().upper())

    # If primary is Postgres and local tarang.db exists, also sync local tarang.db
    if primary_db and os.path.exists(os.path.join(os.path.dirname(__file__), "tarang.db")):
        try:
            seed_db_target("", "LOCAL SQLITE tarang.db")
        except Exception as e:
            print(f"  [WARNING] Could not sync local tarang.db: {e}", flush=True)
        # Restore primary DB in env
        os.environ["DATABASE_URL"] = primary_db

    print("\n-----------------------------------------------------------------", flush=True)
    print(f"SYNC COMPLETE: Successfully synchronized {len(catalog_items)} ALCOP products", flush=True)
    print(f"across {len(brand_categories)} categories under Brand 'ALCOP'!", flush=True)
    print("=================================================================\n", flush=True)
    return True

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="ALCOP India Brand Catalog Scraper & Sync Engine")
    parser.add_argument("--workers", type=int, default=15, help="Number of concurrent image upload threads (default: 15)")
    parser.add_argument("--db-url", type=str, default=None, help="Target Database connection string")
    parser.add_argument("--dry-run", action="store_true", help="Preview scraped data without uploading or writing to DB")
    parser.add_argument("--skip-images", action="store_true", help="Skip Cloudinary upload and use cached/source URLs")

    args = parser.parse_args()
    sync_alcop_catalog(
        db_url=args.db_url,
        workers=args.workers,
        dry_run=args.dry_run,
        skip_images=args.skip_images
    )
