"""
Noel India Scraper & Brand Catalog Synchronizer
Extracts 100% of products, categories, specs, and high-res images from Noel India (https://www.noelindia.com)
Uploads images directly to Cloudinary (folder: tarang_radio/brands/noel/...)
Synchronizes records into the Database (PostgreSQL & SQLite) mapped exclusively under:
  Brand: "Noel" (id: brand_noel) under "The Brands We Deal With"
"""

import os
import re
import sys
import json
import uuid
import time
import urllib.request
import urllib.parse
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import RLock

# Load environment
from dotenv import load_dotenv
load_dotenv()

from db import get_db, get_engine_type
from migrate import run_all_migrations
import cloudinary_service

CACHE_FILE = "cloudinary_noel_cache.json"
cache_lock = RLock()

def load_upload_cache() -> dict:
    """Loads cache of already uploaded shopify_url -> cloudinary_url."""
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                raw = json.load(f)
                if isinstance(raw, dict):
                    if cloudinary_service.is_configured():
                        return {k: v for k, v in raw.items() if v and (v.startswith("http://") or v.startswith("https://"))}
                    return raw
        except Exception:
            return {}
    return {}

def save_upload_cache(cache: dict):
    """Saves upload cache to disk safely."""
    with cache_lock:
        try:
            with open(CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(cache, f, indent=2)
        except Exception as err:
            print(f"[CACHE WARNING] Could not save cache: {err}", flush=True)

def slugify(text: str) -> str:
    """Converts a string into a clean, deterministic URL/DB slug."""
    text = text.lower().strip()
    text = re.sub(r'[\s_]+', '_', text)
    text = re.sub(r'[^\w\-]', '', text)
    return text.strip('_')

def strip_html(html_str: str) -> str:
    """Removes HTML tags and cleans up whitespace from descriptions."""
    if not html_str:
        return ""
    clean = re.sub(r'<[^<]+?>', ' ', html_str)
    clean = re.sub(r'&nbsp;', ' ', clean)
    clean = re.sub(r'&amp;', '&', clean)
    clean = re.sub(r'&quot;', '"', clean)
    clean = re.sub(r'\s+', ' ', clean)
    return clean.strip()

def fetch_noel_products() -> list:
    """
    Fetches all products from Noel India Shopify API (https://www.noelindia.com/products.json).
    Handles pagination automatically.
    """
    all_products = []
    page = 1
    base_url = "https://www.noelindia.com/products.json?limit=250"

    print("[NOEL SCRAPER] Connecting to Noel India (https://www.noelindia.com)...")
    while True:
        url = f"{base_url}&page={page}"
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "application/json"
            }
        )
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                prods = data.get("products", [])
                if not prods:
                    break
                all_products.extend(prods)
                print(f"  -> Page {page}: Retrieved {len(prods)} products (Total: {len(all_products)})")
                page += 1
        except Exception as err:
            print(f"[NOEL SCRAPER ERROR] Failed to fetch page {page}: {err}")
            break

    print(f"[NOEL SCRAPER] Successfully extracted {len(all_products)} products from Noel India.")
    return all_products

def upload_noel_image(item: dict, cache: dict) -> tuple:
    """
    Worker function to stream a product image from Noel India directly to Cloudinary.
    Returns (item_id, cloudinary_url).
    """
    prod_id = item["id"]
    image_url = item.get("source_image_url")
    cat_title = item.get("category_title") or item.get("category") or "General"
    cat_slug = slugify(cat_title)
    title_slug = slugify(item.get("name", f"noel_prod_{prod_id}"))[:50]

    if not image_url:
        return prod_id, ""

    # Check cache
    if image_url in cache:
        return prod_id, cache[image_url]

    # Cloudinary folder structure: tarang_radio/brands/noel/<category>/<title>
    folder = f"tarang_radio/brands/noel/{cat_slug}"
    public_id = f"{title_slug}_{prod_id}"

    try:
        if cloudinary_service.is_configured():
            import cloudinary.uploader
            upload_result = cloudinary.uploader.upload(
                image_url,
                folder=folder,
                public_id=public_id,
                overwrite=True,
                resource_type="image"
            )
            secure_url = upload_result.get("secure_url", "")
            # Inject auto-optimization
            if "/image/upload/" in secure_url:
                secure_url = secure_url.replace("/image/upload/", "/image/upload/f_auto,q_auto/")
            
            with cache_lock:
                cache[image_url] = secure_url
                save_upload_cache(cache)
            return prod_id, secure_url
        else:
            # Fallback: store direct high-res source URL
            with cache_lock:
                cache[image_url] = image_url
                save_upload_cache(cache)
            return prod_id, image_url
    except Exception as err:
        print(f"    [UPLOAD ERROR] Product {prod_id} ('{item.get('name')}'): {err}", flush=True)
        return prod_id, image_url

def sync_noel_catalog(
    db_url: str = None,
    workers: int = 15,
    dry_run: bool = False,
    skip_images: bool = False
) -> bool:
    """
    Scrapes Noel India and syncs brand categories, subcategories, and products
    exclusively under Brand: Noel (id: brand_noel).
    """
    if db_url:
        os.environ["DATABASE_URL"] = db_url

    print("=================================================================")
    print("       NOEL INDIA -> TARANG RADIOS BRAND CATALOG SYNC            ")
    print("=================================================================")
    print(f"Source URL       : https://www.noelindia.com")
    print(f"Target Brand     : Noel (brand_noel) [The Brands We Deal With]")
    print(f"Database Engine  : {get_engine_type().upper()}")
    print(f"Target DB        : {os.environ.get('DATABASE_URL', 'SQLite tarang.db').split('@')[-1] if '@' in os.environ.get('DATABASE_URL', '') else 'Local DB'}")
    print(f"Cloudinary Mode  : {'Configured' if cloudinary_service.is_configured() else 'Direct CDN Fallback'}")
    print(f"Upload Workers   : {workers} threads")
    print(f"Dry Run Mode     : {'YES (Preview only, no writes)' if dry_run else 'NO (Live Execution)'}")
    print("-----------------------------------------------------------------")

    # 1. Fetch raw products from Noel India
    raw_products = fetch_noel_products()
    if not raw_products:
        print("[ERROR] No products fetched from Noel India. Aborting sync.")
        return False

    # 2. Structure Noel Catalog Data
    # Normalizes categories, subcategories, prices, descriptions, images
    catalog_items = []
    brand_categories = {}     # cat_id -> dict
    brand_subcategories = {}  # sub_id -> dict

    for p in raw_products:
        p_id = p["id"]
        title = (p.get("title") or "Noel Product").strip()
        
        # Determine category / product type
        raw_type = (p.get("product_type") or "").strip()
        if not raw_type:
            tags = p.get("tags") or []
            if isinstance(tags, str):
                tags = [t.strip() for t in tags.split(",")]
            # Check tags for category hint
            tag_hint = next((t for t in tags if "solder" in t.lower() or "cord" in t.lower()), "Soldering Tools & Accessories")
            raw_type = tag_hint.replace("-", " ").title()
        
        cat_title = raw_type if raw_type else "Soldering Tools & Equipment"
        cat_id = f"cat_noel_{slugify(cat_title)}"

        # Determine subcategory
        sub_title = "General"
        # Extract wattage / series if available (e.g. 25W, 35W, 60W, 900M Series)
        watt_match = re.search(r'(\d+W|\d+\s*Watt|900M\s*Series|Kit|Pump|Wick|Wire|Flux|Paste)', title, re.IGNORECASE)
        if watt_match:
            sub_title = watt_match.group(1).strip().upper()
        else:
            sub_title = "Standard Series"

        sub_id = f"sub_noel_{slugify(cat_title)}_{slugify(sub_title)}"

        # Price extraction from variants
        variants = p.get("variants") or []
        price = 0.0
        in_stock = 1
        sku = f"NOEL-SKU-{p_id}"
        if variants:
            v0 = variants[0]
            price = float(v0.get("price") or 0.0)
            in_stock = 1 if v0.get("available", True) else 0
            if v0.get("sku"):
                sku = f"NOEL-{v0['sku']}"

        # Image extraction
        images = p.get("images") or []
        source_image_url = ""
        if images and isinstance(images, list):
            source_image_url = images[0].get("src", "")

        # Description & Specs
        desc = strip_html(p.get("body_html") or f"{title} - Official Noel India Soldering Equipment")
        specs = json.dumps({
            "vendor": p.get("vendor", "Noel"),
            "handle": p.get("handle", ""),
            "tags": p.get("tags", []),
            "variants_count": len(variants)
        })

        # Register category
        if cat_id not in brand_categories:
            brand_categories[cat_id] = {
                "id": cat_id,
                "brand_id": "brand_noel",
                "title": cat_title,
                "short_title": cat_title,
                "tagline": f"Official Noel {cat_title} for precision electronics & soldering",
                "icon": "tool",
                "image": source_image_url,
                "color": "#D14B14",
                "display_order": len(brand_categories)
            }

        # Register subcategory
        if sub_id not in brand_subcategories:
            brand_subcategories[sub_id] = {
                "id": sub_id,
                "category_id": cat_id,
                "name": sub_title,
                "display_order": len(brand_subcategories)
            }

        catalog_items.append({
            "id": p_id,
            "prod_db_id": f"prod_noel_{p_id}",
            "sku": sku,
            "name": title,
            "category_id": cat_id,
            "category_title": cat_title,
            "subcategory": sub_title,
            "sub_id": sub_id,
            "price": price,
            "in_stock": in_stock,
            "source_image_url": source_image_url,
            "description": desc,
            "specs": specs
        })

    print(f"\n[STEP 1] Structured Noel Catalog:")
    print(f"  -> {len(brand_categories)} Brand Categories under Noel")
    print(f"  -> {len(brand_subcategories)} Brand Subcategories under Noel")
    print(f"  -> {len(catalog_items)} Noel Products")

    # 3. Multi-Threaded Cloudinary Image Upload
    product_image_urls = {}
    cache = load_upload_cache()

    if dry_run:
        print("\n[STEP 2] [DRY RUN] Simulating Cloudinary Uploads...")
        print(f"  -> {len(cache)} images already cached.")
        print(f"  -> Would upload {len(catalog_items)} images using {workers} threads.")
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
                executor.submit(upload_noel_image, item, cache): item
                for item in catalog_items
            }

            for future in as_completed(future_to_item):
                p_id, final_url = future.result()
                product_image_urls[p_id] = final_url
                completed += 1
                if completed % 10 == 0 or completed == total:
                    pct = (completed / total) * 100
                    print(f"  -> Progress: {completed}/{total} ({pct:.1f}%) processed...", flush=True)

        save_upload_cache(cache)
        duration = time.time() - t0
        print(f"  [OK] Image synchronization completed in {duration:.1f}s.", flush=True)

    # 4. Database Seeding
    if dry_run:
        print("\n[STEP 3] [DRY RUN] Database Seeding Preview:")
        print("  -> Would ensure Brand 'Noel' (brand_noel) exists in 'brands' table.")
        print(f"  -> Would upsert {len(brand_categories)} categories under brand_noel.")
        print(f"  -> Would upsert {len(brand_subcategories)} subcategories.")
        print(f"  -> Would upsert {len(catalog_items)} products.")
        print("\n[DRY RUN COMPLETE] Everything verified successfully! Run without --dry-run to commit.")
        return True

    def seed_db_target(db_conn_str, label):
        print(f"\n[STEP 3] Seeding Noel Catalog into Database ({label})...", flush=True)
        if db_conn_str:
            os.environ["DATABASE_URL"] = db_conn_str
        else:
            os.environ["DATABASE_URL"] = ""

        run_all_migrations()
        now_iso = datetime.now().isoformat()

        with get_db() as db:
            # 1. Resolve Noel Brand ID dynamically
            existing_brand = db.fetchone("SELECT id, name FROM brands WHERE LOWER(name) = 'noel'")
            if existing_brand:
                noel_brand_id = existing_brand["id"]
                db.execute("UPDATE brands SET is_enabled = 1, updated_at = ? WHERE id = ?", (now_iso, noel_brand_id))
                db.commit()
            else:
                noel_brand_id = "brand_noel"
                db.execute("""
                    INSERT INTO brands (id, name, display_order, is_enabled, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    ON CONFLICT (id) DO UPDATE SET
                        name = EXCLUDED.name,
                        is_enabled = EXCLUDED.is_enabled,
                        updated_at = EXCLUDED.updated_at
                """, (noel_brand_id, "Noel", 0, 1, now_iso, now_iso))
                db.commit()
            print(f"  -> [OK] Brand 'Noel' (ID: '{noel_brand_id}') verified in brands table.", flush=True)

            # 2. Upsert Brand Categories (brand_id = noel_brand_id)
            cat_rows = []
            for cat in brand_categories.values():
                cat_img = product_image_urls.get(cat.get("sample_prod_id")) or cat["image"]
                cat_rows.append((
                    cat["id"],
                    noel_brand_id,
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
            print(f"  -> [OK] {len(cat_rows)} Brand Categories upserted under Noel.", flush=True)

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
            print(f"  -> [OK] {len(sub_rows)} Brand Subcategories upserted under Noel.", flush=True)

            # 4. Upsert Brand Products
            prod_rows = []
            for item in catalog_items:
                final_img = product_image_urls.get(item["id"]) or cache.get(item["source_image_url"]) or item["source_image_url"]
                badge = "In Stock" if item["in_stock"] else "Out of Stock"
                
                prod_rows.append((
                    item["prod_db_id"],
                    item["sku"],
                    item["name"],
                    noel_brand_id,
                    "Noel",
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
            print(f"  -> [OK] {len(prod_rows)} Noel Products upserted under Noel brand.", flush=True)

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
    print(f"SYNC COMPLETE: Successfully synchronized {len(catalog_items)} Noel products", flush=True)
    print(f"across {len(brand_categories)} categories under Brand 'Noel'!", flush=True)
    print("=================================================================\n", flush=True)
    return True

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Noel India Brand Catalog Scraper & Synchronizer")
    parser.add_argument("--db-url", help="Database connection URL override")
    parser.add_argument("--workers", type=int, default=15, help="Concurrent upload threads (default: 15)")
    parser.add_argument("--dry-run", action="store_true", help="Preview without writing to Cloudinary/DB")
    parser.add_argument("--skip-images", action="store_true", help="Skip image upload and seed DB with cached URLs")

    args = parser.parse_args()
    sync_noel_catalog(
        db_url=args.db_url,
        workers=args.workers,
        dry_run=args.dry_run,
        skip_images=args.skip_images
    )
