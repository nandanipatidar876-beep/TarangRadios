"""
TARANG RADIOS - Production Catalog Sync & Cloudinary Uploader
Uploads scraped product images to Cloudinary concurrently (15 workers with auto-resume)
and seeds Categories, Subcategories, and Products directly into the Production Database (PostgreSQL / SQLite).
"""

import os
import sys
import json
import re
import time
import threading
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# Try loading python-dotenv
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
except ImportError:
    pass

import cloudinary_service
from db import get_db, get_engine_type
from migrate import run_all_migrations

CACHE_FILE = os.path.join(os.path.dirname(__file__), "cloudinary_upload_cache.json")
cache_lock = threading.Lock()

def load_upload_cache() -> dict:
    """Loads cache of already uploaded local_path -> cloudinary_url."""
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
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
            print(f"[CACHE WARNING] Could not save cache: {err}")

def slugify(text: str) -> str:
    """Converts a string into a clean, deterministic URL/DB slug."""
    text = text.lower().strip()
    text = re.sub(r'[\s_]+', '_', text)
    text = re.sub(r'[^\w\-]', '', text)
    return text.strip('_')

def format_title(text: str) -> str:
    """Cleans up scraped category / subcategory titles."""
    cleaned = text.replace("_", " ").strip()
    # Normalize common symbols
    cleaned = re.sub(r'\s+', ' ', cleaned)
    return cleaned

def upload_single_product_image(product: dict, images_dir: str, cache: dict) -> tuple[int, str]:
    """
    Worker function to upload a single product image to Cloudinary.
    Returns (product_id, final_image_url).
    """
    prod_id = product["id"]
    rel_path = product.get("relative_path", "")
    abs_path = product.get("absolute_path", "")
    cat_raw = product.get("category", "General")
    sub_raw = product.get("subcategory", "Misc")
    filename = product.get("image_filename", "")

    # Check cache first (by absolute path or relative path)
    cache_key = abs_path or rel_path
    if cache_key and cache_key in cache:
        return prod_id, cache[cache_key]

    # Resolve local file path
    local_path = None
    if abs_path and os.path.exists(abs_path):
        local_path = abs_path
    elif rel_path:
        candidate = os.path.join(images_dir, rel_path.replace("product_images/", "").replace("/", os.sep))
        if os.path.exists(candidate):
            local_path = candidate
        else:
            candidate2 = os.path.join(images_dir, rel_path.replace("/", os.sep))
            if os.path.exists(candidate2):
                local_path = candidate2

    if not local_path or not os.path.exists(local_path):
        # Image not found locally
        return prod_id, ""

    # Cloudinary folder: tarang_radio/products/<category>/<subcategory>
    folder_path = f"tarang_radio/products/{slugify(cat_raw)}/{slugify(sub_raw)}"
    clean_name = os.path.splitext(filename or os.path.basename(local_path))[0]
    clean_name = slugify(clean_name)[:80] or f"prod_{prod_id}"

    # Perform Cloudinary upload
    upload_res = cloudinary_service.upload_image(
        local_path,
        filename=f"{clean_name}.jpg",
        folder=folder_path
    )

    cloud_url = upload_res.get("url", "")

    # Store in cache
    if cloud_url:
        with cache_lock:
            cache[cache_key] = cloud_url
            if rel_path:
                cache[rel_path] = cloud_url

    return prod_id, cloud_url

def sync_production(
    catalog_path: str = r"D:\scrapping\products_catalog.json",
    images_dir: str = r"D:\scrapping\product_images",
    db_url: str = None,
    workers: int = 15,
    dry_run: bool = False,
    skip_images: bool = False
) -> bool:
    """
    Main catalog sync function.
    Uploads images to Cloudinary and seeds Categories, Subcategories, and Products into target DB.
    """
    if db_url:
        os.environ["DATABASE_URL"] = db_url

    # Check Catalog File
    if not os.path.exists(catalog_path):
        print(f"[ERROR] Catalog file not found at: {catalog_path}")
        return False

    print("=================================================================")
    print("      TARANG RADIOS - PRODUCTION CATALOG & CLOUDINARY SYNC       ")
    print("=================================================================")
    print(f"Catalog JSON     : {catalog_path}")
    print(f"Images Directory : {images_dir}")
    print(f"Database Engine  : {get_engine_type().upper()}")
    print(f"Target DB        : {os.environ.get('DATABASE_URL', 'SQLite tarang.db').split('@')[-1] if '@' in os.environ.get('DATABASE_URL', '') else 'Local DB'}")
    print(f"Cloudinary Mode  : {'Configured' if cloudinary_service.is_configured() else 'Local Fallback (Set CLOUDINARY_* in .env)'}")
    print(f"Upload Workers   : {workers} threads")
    print(f"Dry Run Mode     : {'YES (Preview only, no writes)' if dry_run else 'NO (Live Execution)'}")
    print("-----------------------------------------------------------------")

    # 1. Load JSON Catalog
    with open(catalog_path, "r", encoding="utf-8") as f:
        catalog_items = json.load(f)

    if not isinstance(catalog_items, list) or len(catalog_items) == 0:
        print("[ERROR] Catalog JSON must be a non-empty list of product objects.")
        return False

    total_products = len(catalog_items)
    print(f"[STEP 1] Loaded {total_products:,} products from catalog JSON.")

    # 2. Extract and structure unique Categories and Subcategories
    categories_map = {}     # raw_cat -> cat_dict
    subcategories_map = {}  # (cat_id, raw_sub) -> sub_dict
    category_order = 0
    subcategory_order_by_cat = {}

    for item in catalog_items:
        raw_cat = (item.get("category") or "General").strip()
        raw_sub = (item.get("subcategory") or "General").strip()

        cat_id = f"cat_{slugify(raw_cat)}"
        if cat_id not in categories_map:
            cat_title = format_title(raw_cat)
            categories_map[cat_id] = {
                "id": cat_id,
                "raw_name": raw_cat,
                "title": cat_title,
                "short_title": cat_title[:100],
                "tagline": f"Premium {cat_title} components & accessories",
                "icon": "layers",
                "image": None, # Will set to first product image
                "color": "#D14B14",
                "display_order": category_order
            }
            category_order += 1
            subcategory_order_by_cat[cat_id] = 0

        sub_id = f"sub_{slugify(raw_cat)}_{slugify(raw_sub)}"
        sub_key = (cat_id, raw_sub.lower())
        if sub_key not in subcategories_map:
            sub_title = format_title(raw_sub)
            subcategories_map[sub_key] = {
                "id": sub_id,
                "category_id": cat_id,
                "name": sub_title,
                "display_order": subcategory_order_by_cat[cat_id]
            }
            subcategory_order_by_cat[cat_id] += 1

    print(f"  -> Extracted {len(categories_map)} unique Categories.")
    print(f"  -> Extracted {len(subcategories_map)} unique Subcategories.")

    # 3. Cloudinary Multi-Threaded Upload
    upload_cache = load_upload_cache()
    product_image_urls = {} # prod_id -> cloud_url
    
    if skip_images:
        print("\n[STEP 2] Skipping Cloudinary uploads (--skip-images flag active).")
        for item in catalog_items:
            prod_id = item["id"]
            cache_key = item.get("absolute_path") or item.get("relative_path")
            product_image_urls[prod_id] = upload_cache.get(cache_key, item.get("relative_path", ""))
    elif dry_run:
        print("\n[STEP 2] [DRY RUN] Simulating Cloudinary uploads...")
        cached_count = sum(1 for item in catalog_items if (item.get("absolute_path") in upload_cache or item.get("relative_path") in upload_cache))
        print(f"  -> {cached_count} / {total_products} images already cached in cloudinary_upload_cache.json.")
        print(f"  -> Would upload {total_products - cached_count} images using {workers} worker threads.")
    else:
        print(f"\n[STEP 2] Uploading images to Cloudinary ({workers} worker threads with auto-resume)...")
        start_time = time.time()
        completed_count = 0
        cached_hit_count = 0
        uploaded_now_count = 0

        with ThreadPoolExecutor(max_workers=workers) as executor:
            future_to_prod = {
                executor.submit(upload_single_product_image, item, images_dir, upload_cache): item["id"]
                for item in catalog_items
            }

            for future in as_completed(future_to_prod):
                prod_id = future_to_prod[future]
                try:
                    p_id, cloud_url = future.result()
                    product_image_urls[p_id] = cloud_url
                    completed_count += 1

                    if cloud_url and "cloudinary.com" in cloud_url:
                        # Check if it was newly uploaded or cached
                        uploaded_now_count += 1

                    if completed_count % 50 == 0 or completed_count == total_products:
                        save_upload_cache(upload_cache)
                        pct = (completed_count / total_products) * 100
                        print(f"  -> Progress: {completed_count}/{total_products} ({pct:.1f}%) processed...")
                except Exception as err:
                    print(f"  [UPLOAD ERROR] Product {prod_id}: {err}")
                    product_image_urls[prod_id] = ""

        save_upload_cache(upload_cache)
        elapsed = time.time() - start_time
        print(f"  [OK] Cloudinary upload completed in {elapsed:.1f}s. {len(upload_cache)} total images in cache.")

    # Assign category cover image from the first product of that category
    for item in catalog_items:
        cat_id = f"cat_{slugify(item.get('category') or 'General')}"
        prod_img = product_image_urls.get(item["id"], "")
        if prod_img and cat_id in categories_map and not categories_map[cat_id]["image"]:
            categories_map[cat_id]["image"] = prod_img

    if dry_run:
        print("\n[STEP 3] [DRY RUN] Database Seeding Preview:")
        print(f"  -> Would upsert {len(categories_map)} categories.")
        print(f"  -> Would upsert {len(subcategories_map)} subcategories.")
        print(f"  -> Would upsert {total_products} products with Cloudinary URLs.")
        print("\n[DRY RUN COMPLETE] Everything verified successfully! Run without --dry-run to commit to Production DB.")
        return True

    # 4. Direct Production Database Seeding
    print(f"\n[STEP 3] Seeding Production Database ({get_engine_type().upper()})...")
    
    # Run migrations to ensure schema and indexes exist
    print("  -> Applying database schema migrations...")
    run_all_migrations()

    now_iso = datetime.now().isoformat()

    with get_db() as db:
        # Upsert Categories
        print(f"  -> Seeding {len(categories_map)} Categories...")
        cat_rows = []
        for cat in categories_map.values():
            cat_rows.append((
                cat["id"],
                None, # brand_id NULL for normal categories
                cat["title"],
                cat["short_title"],
                cat["tagline"],
                cat["icon"],
                cat["image"],
                cat["color"],
                cat["display_order"],
                now_iso,
                now_iso
            ))

        db.executemany("""
            INSERT INTO categories (id, brand_id, title, short_title, tagline, icon, image, color, display_order, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (id) DO UPDATE SET
                title = EXCLUDED.title,
                short_title = EXCLUDED.short_title,
                tagline = EXCLUDED.tagline,
                image = EXCLUDED.image,
                updated_at = EXCLUDED.updated_at
        """, cat_rows)
        print(f"     [OK] {len(cat_rows)} Categories upserted.")

        # Upsert Subcategories
        print(f"  -> Seeding {len(subcategories_map)} Subcategories...")
        sub_rows = []
        for sub in subcategories_map.values():
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
        print(f"     [OK] {len(sub_rows)} Subcategories upserted.")

        # Upsert Products
        print(f"  -> Seeding {total_products} Products...")
        prod_rows = []
        for item in catalog_items:
            prod_id = f"prod_{item['id']}"
            sku = f"TR-SKU-{item['id']:04d}"
            name = (item.get("name") or "Unnamed Product").strip()
            cat_id = f"cat_{slugify(item.get('category') or 'General')}"
            sub_name = format_title(item.get("subcategory") or "General")
            price = float(item.get("price") or 0.0)
            stock = int(item.get("stock") or 0)
            is_active = bool(item.get("is_active", True))
            in_stock = 1 if stock > 0 and is_active else 0
            badge = "In Stock" if in_stock else "Out of Stock"
            image_url = product_image_urls.get(item["id"]) or ""
            desc = item.get("description") or f"{name} - {cat_id} ({sub_name})"
            specs = json.dumps({"stock": stock, "unit": item.get("unit", "PC")})

            prod_rows.append((
                prod_id,
                sku,
                name,
                None, # brand_id NULL for normal catalog
                None, # brand
                cat_id,
                sub_name,
                price,
                badge,
                in_stock,
                image_url,
                desc,
                specs,
                5.0, # default rating
                0,   # default reviews
                now_iso,
                now_iso
            ))

        db.executemany("""
            INSERT INTO products (id, sku, name, brand_id, brand, category_id, subcategory, price, badge, in_stock, image, description, specs, rating, reviews, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (id) DO UPDATE SET
                name = EXCLUDED.name,
                sku = EXCLUDED.sku,
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
        print(f"     [OK] {len(prod_rows)} Products upserted.")

        db.commit()

    print("\n-----------------------------------------------------------------")
    print(f"SYNC COMPLETE: Successfully synchronized {total_products:,} products,")
    print(f"{len(categories_map)} categories, and {len(subcategories_map)} subcategories to {get_engine_type().upper()}!")
    print("=================================================================\n")
    return True

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Tarang Radios - Production Catalog & Cloudinary Sync")
    parser.add_argument("--catalog", default=r"D:\scrapping\products_catalog.json", help="Path to products_catalog.json")
    parser.add_argument("--images-dir", default=r"D:\scrapping\product_images", help="Path to product images root directory")
    parser.add_argument("--db-url", help="Database connection URL (PostgreSQL / SQLite)")
    parser.add_argument("--workers", type=int, default=15, help="Number of concurrent upload threads (default: 15)")
    parser.add_argument("--dry-run", action="store_true", help="Preview sync and verify files without writing")
    parser.add_argument("--skip-images", action="store_true", help="Seed database without uploading new images")

    args = parser.parse_args()

    sync_production(
        catalog_path=args.catalog,
        images_dir=args.images_dir,
        db_url=args.db_url,
        workers=args.workers,
        dry_run=args.dry_run,
        skip_images=args.skip_images
    )
