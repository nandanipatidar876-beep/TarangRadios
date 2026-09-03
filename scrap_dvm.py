"""
=============================================================================
TARANG RADIOS - DVM INDIA BRAND CATALOG SCRAPER & SYNC ENGINE
Scrapes products, categories, and subcategories from DVM India (https://dvmindia.in/)
Uploads high-res images to Cloudinary under brand/dvm folder hierarchy.
Seeds database (both local SQLite tarang.db and production PostgreSQL)
strictly isolated under the brand partner: "DVM".
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

CACHE_FILE = os.path.join(os.path.dirname(__file__), "cloudinary_dvm_cache.json")
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

def extract_dvm_catalog():
    cat_pages = [
        ("AC-Power-Adapters.html", "AC Power Adapters", "Plugin & TableTop AC Power Adapters with BIS certification", "#0284C7"),
        ("Laptop-Adapters.html", "Laptop Adapters", "High efficiency replacement adapters for all laptop models", "#2563EB"),
        ("Mobile-Accessories.html", "Mobile Accessories", "SuperFast charging cables, adaptors & mobile essentials", "#7C3AED"),
        ("CCTV-Accessories.html", "CCTV Accessories", "Centralized multi-channel SMPS power supplies & camera cables", "#DC2626"),
        ("EV-Chargers.html", "EV Chargers", "Smart EV chargers for E-Cycles, E-Bikes and E-Rickshaws", "#16A34A"),
        ("Powerstrips.html", "Powerstrips & Spike Guards", "Multi-socket spike guards with surge protection & brass sockets", "#D97706"),
        ("Wall-Mounts.html", "Wall Mounts", "Heavy duty fixed & moving wall brackets for LCD & LED TVs", "#4B5563"),
        ("Cords-&-Cables.html", "Cords & Cables", "Full copper power cords, CAT6 patch cords & AV cables", "#0D9488")
    ]

    brand_categories = {}
    brand_subcategories = {}
    catalog_items = []
    seen_img_urls = set()

    print("[DVM SCRAPER] Connecting to DVM India (https://dvmindia.in/)...", flush=True)

    for page_file, main_cat_title, tagline, color in cat_pages:
        url = f"https://dvmindia.in/{urllib.parse.quote(page_file)}"
        cat_id = f"cat_dvm_{slugify(main_cat_title)}"
        
        try:
            page_html = fetch_page(url)
            print(f"  -> Fetched '{main_cat_title}' ({len(page_html):,} bytes)", flush=True)
        except Exception as e:
            print(f"  [ERROR] Failed to fetch {page_file}: {e}", flush=True)
            continue

        body_content = re.sub(r'<script.*?</script>', '', page_html, flags=re.DOTALL | re.IGNORECASE)
        body_content = re.sub(r'<style.*?</style>', '', body_content, flags=re.DOTALL | re.IGNORECASE)

        brand_categories[cat_id] = {
            "id": cat_id,
            "title": main_cat_title,
            "short_title": main_cat_title,
            "tagline": tagline,
            "icon": "zap",
            "color": color,
            "image": "",
            "display_order": len(brand_categories)
        }

        # Split into subcategory sections
        sections = re.split(r'(<h[2-4][^>]*>.*?</h[2-4]>)', body_content, flags=re.IGNORECASE | re.DOTALL)
        current_subcat_title = "Standard Series"

        for sec in sections:
            h_match = re.match(r'<h[2-4][^>]*>(.*?)</h[2-4]>', sec, re.IGNORECASE | re.DOTALL)
            if h_match:
                raw_h = re.sub(r'<[^>]+>', '', h_match.group(1)).strip()
                if raw_h and not any(k in raw_h.lower() for k in [
                    'useful links', 'social', 'address', 'product category', 'reach out', 
                    'dvm india', 'navigation', 'filter', 'subscribe', 'terms', 'privacy', 'no record'
                ]):
                    current_subcat_title = raw_h
                continue

            img_tags = re.findall(r'<img[^>]+src=[\'"]([^\'"]+)[\'"][^>]*>', sec, re.IGNORECASE)
            valid_imgs = [
                i for i in img_tags 
                if 'images/' in i and not any(k in i.lower() for k in ['banner', 'logo', 'icon', 'arrow', 'preloader', 'placeholder', 'user', 'slider', 'web_banner'])
            ]

            if valid_imgs:
                lis = re.findall(r'<li[^>]*>(.*?)</li>', sec, flags=re.DOTALL | re.IGNORECASE)
                clean_lis = [re.sub(r'<[^>]+>', '', li).strip() for li in lis if li.strip()]

                # Clean up subcategory name
                subcat_clean = current_subcat_title.replace("Model :", "").replace("MODEL :", "").strip()
                if not subcat_clean or len(subcat_clean) < 2:
                    subcat_clean = "Standard Series"

                sub_id = f"sub_dvm_{slugify(main_cat_title)}_{slugify(subcat_clean)}"
                if sub_id not in brand_subcategories:
                    brand_subcategories[sub_id] = {
                        "id": sub_id,
                        "category_id": cat_id,
                        "name": subcat_clean,
                        "display_order": len(brand_subcategories)
                    }

                for img in valid_imgs:
                    full_img_url = f"https://dvmindia.in/{urllib.parse.quote(img)}" if not img.startswith('http') else img
                    if full_img_url in seen_img_urls:
                        continue
                    seen_img_urls.add(full_img_url)

                    # Generate clean product name
                    raw_name = img.split('/')[-1].replace('.webp', '').replace('.jpg', '').replace('.png', '').strip()
                    # Clean up model naming
                    clean_model = raw_name.replace('ADP', 'DVM Adapter').replace('SPIKE', 'DVM Spike Guard').replace('Wallmount', 'DVM Mount').replace('Cable', 'DVM Cable').replace('CABLE', 'DVM Cable')
                    
                    prod_title = f"{clean_model} - {subcat_clean}"
                    if not prod_title.startswith("DVM"):
                        prod_title = f"DVM {prod_title}"

                    item_id = f"dvm_{slugify(raw_name)}"
                    desc = " • ".join(clean_lis[:5]) if clean_lis else f"Official DVM India {subcat_clean} - High quality, BIS certified."

                    if not brand_categories[cat_id]["image"]:
                        brand_categories[cat_id]["image"] = full_img_url

                    catalog_items.append({
                        "id": item_id,
                        "prod_db_id": f"prod_{item_id}",
                        "sku": f"DVM-{slugify(raw_name).upper()[:14]}",
                        "name": prod_title,
                        "category_id": cat_id,
                        "category_title": main_cat_title,
                        "subcategory": subcat_clean,
                        "sub_id": sub_id,
                        "price": 0.0,
                        "in_stock": 1,
                        "source_image_url": full_img_url,
                        "description": desc,
                        "specs": json.dumps({
                            "brand": "DVM India",
                            "model": raw_name,
                            "category": main_cat_title,
                            "subcategory": subcat_clean,
                            "highlights": clean_lis[:5]
                        })
                    })

    return brand_categories, brand_subcategories, catalog_items

def upload_dvm_image(item: dict, cache: dict) -> tuple:
    source_url = item["source_image_url"]
    item_id = item["id"]
    cat_slug = slugify(item["category_title"])
    sub_slug = slugify(item["subcategory"])

    with cache_lock:
        if source_url in cache:
            return item_id, cache[source_url]

    if not CLOUDINARY_CONFIGURED:
        return item_id, source_url

    public_id = f"tarang_radio/brands/dvm/{cat_slug}/{sub_slug}/{item_id}"
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

def sync_dvm_catalog(db_url: str = None, workers: int = 15, dry_run: bool = False, skip_images: bool = False):
    print("=================================================================")
    print("       DVM INDIA -> TARANG RADIOS BRAND CATALOG SYNC             ")
    print("=================================================================")
    print(f"Source URL       : https://dvmindia.in")
    print(f"Target Brand     : DVM [The Brands We Deal With]")
    print(f"Database Engine  : {get_engine_type().upper()}")
    print(f"Cloudinary Mode  : {'Configured' if CLOUDINARY_CONFIGURED else 'Disabled (Using source URLs)'}")
    print(f"Upload Workers   : {workers} threads")
    print(f"Dry Run Mode     : {'YES' if dry_run else 'NO (Live Execution)'}")
    print("-----------------------------------------------------------------")

    # 1. Scrape DVM India
    brand_categories, brand_subcategories, catalog_items = extract_dvm_catalog()

    print(f"\n[STEP 1] Structured DVM Catalog:")
    print(f"  -> {len(brand_categories)} Brand Categories under DVM")
    print(f"  -> {len(brand_subcategories)} Brand Subcategories under DVM")
    print(f"  -> {len(catalog_items)} DVM Products extracted")

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
                executor.submit(upload_dvm_image, item, cache): item
                for item in catalog_items
            }

            for future in as_completed(future_to_item):
                p_id, final_url = future.result()
                product_image_urls[p_id] = final_url
                completed += 1
                if completed % 10 == 0 or completed == total:
                    pct = (completed / total) * 100
                    print(f"  -> Progress: {completed}/{total} ({pct:.1f}%) uploaded...", flush=True)

        save_upload_cache(cache)
        duration = time.time() - t0
        print(f"  [OK] Image synchronization completed in {duration:.1f}s.", flush=True)

    # 3. Database Seeder (Supports both SQLite tarang.db and PostgreSQL)
    def seed_db_target(db_conn_str, label):
        print(f"\n[STEP 3] Seeding DVM Catalog into Database ({label})...", flush=True)
        if db_conn_str:
            os.environ["DATABASE_URL"] = db_conn_str
        else:
            os.environ["DATABASE_URL"] = ""

        run_all_migrations()
        now_iso = datetime.now().isoformat()

        with get_db() as db:
            # 1. Resolve DVM Brand ID dynamically
            existing_brand = db.fetchone("SELECT id, name FROM brands WHERE LOWER(name) = 'dvm'")
            if existing_brand:
                dvm_brand_id = existing_brand["id"]
                db.execute("UPDATE brands SET is_enabled = 1, updated_at = ? WHERE id = ?", (now_iso, dvm_brand_id))
                db.commit()
            else:
                dvm_brand_id = "brand_dvm"
                db.execute("""
                    INSERT INTO brands (id, name, display_order, is_enabled, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    ON CONFLICT (id) DO UPDATE SET
                        name = EXCLUDED.name,
                        is_enabled = EXCLUDED.is_enabled,
                        updated_at = EXCLUDED.updated_at
                """, (dvm_brand_id, "DVM", 1, 1, now_iso, now_iso))
                db.commit()
            print(f"  -> [OK] Brand 'DVM' (ID: '{dvm_brand_id}') verified in brands table.", flush=True)

            # 2. Upsert Brand Categories (brand_id = dvm_brand_id)
            cat_rows = []
            for cat in brand_categories.values():
                cat_img = product_image_urls.get(cat.get("sample_prod_id")) or cat["image"]
                cat_rows.append((
                    cat["id"],
                    dvm_brand_id,
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
            print(f"  -> [OK] {len(cat_rows)} Brand Categories upserted under DVM.", flush=True)

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
            print(f"  -> [OK] {len(sub_rows)} Brand Subcategories upserted under DVM.", flush=True)

            # 4. Upsert Brand Products
            prod_rows = []
            for item in catalog_items:
                final_img = product_image_urls.get(item["id"]) or cache.get(item["source_image_url"]) or item["source_image_url"]
                badge = "In Stock" if item["in_stock"] else "Out of Stock"

                prod_rows.append((
                    item["prod_db_id"],
                    item["sku"],
                    item["name"],
                    dvm_brand_id,
                    "DVM",
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
            print(f"  -> [OK] {len(prod_rows)} DVM Products upserted under DVM brand.", flush=True)

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
    print(f"SYNC COMPLETE: Successfully synchronized {len(catalog_items)} DVM products", flush=True)
    print(f"across {len(brand_categories)} categories under Brand 'DVM'!", flush=True)
    print("=================================================================\n", flush=True)
    return True

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="DVM India Brand Catalog Scraper & Sync Engine")
    parser.add_argument("--workers", type=int, default=15, help="Number of concurrent image upload threads (default: 15)")
    parser.add_argument("--db-url", type=str, default=None, help="Target Database connection string")
    parser.add_argument("--dry-run", action="store_true", help="Preview scraped data without uploading or writing to DB")
    parser.add_argument("--skip-images", action="store_true", help="Skip Cloudinary upload and use cached/source URLs")

    args = parser.parse_args()
    sync_dvm_catalog(
        db_url=args.db_url,
        workers=args.workers,
        dry_run=args.dry_run,
        skip_images=args.skip_images
    )
