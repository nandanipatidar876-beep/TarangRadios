"""
TARANG RADIOS - Local Images to Cloudinary CDN Migration Tool
Scans all products/categories in the database that reference local images,
uploads them to Cloudinary, and updates the database records with the new CDN URLs.
Usage:
    python scripts/migrate_images_to_cloudinary.py [--dry-run]
"""

import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from db import get_db, get_engine_type
import cloudinary_service

STATIC_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

def migrate_images(dry_run: bool = False):
    if not cloudinary_service.is_configured():
        print("[ERROR] Cloudinary is not configured.")
        print("Please set CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY, and CLOUDINARY_API_SECRET in your .env file.")
        return False

    print("=================================================================")
    print("      TARANG RADIOS - LOCAL IMAGES TO CLOUDINARY MIGRATION       ")
    print("=================================================================")
    print(f"Cloud Name   : {cloudinary_service.CLOUD_NAME}")
    print(f"Database     : {get_engine_type().upper()}")
    print(f"Dry Run Mode : {'YES (no uploads or DB updates)' if dry_run else 'NO (live migration)'}")
    print("-----------------------------------------------------------------")

    with get_db() as db:
        # 1. Migrate Products images
        products = db.fetchall("SELECT id, name, image FROM products WHERE image IS NOT NULL AND image != ''")
        print(f"\nFound {len(products)} products with image references.")

        uploaded_count = 0
        skipped_count = 0
        failed_count = 0

        for prod in products:
            img_val = prod["image"].strip()
            if img_val.startswith("http://") or img_val.startswith("https://"):
                # Already a remote URL (Cloudinary or CDN)
                skipped_count += 1
                continue

            # Resolve local file path
            local_path = os.path.join(STATIC_ROOT, img_val.replace("/", os.sep))
            if not os.path.exists(local_path):
                # Try in uploads folder
                local_path = os.path.join(STATIC_ROOT, "uploads", os.path.basename(img_val))

            if not os.path.exists(local_path):
                print(f"  [MISSING FILE] Product '{prod['name']}' references non-existent file: {img_val}")
                failed_count += 1
                continue

            if dry_run:
                print(f"  [DRY RUN] Would upload {img_val} for product '{prod['name']}'")
                uploaded_count += 1
                continue

            print(f"  -> Uploading '{os.path.basename(local_path)}' for '{prod['name']}'...")
            res = cloudinary_service.upload_image(local_path, filename=os.path.basename(local_path), folder="tarang_radios/products")
            
            if res.get("success") and res.get("is_cloud"):
                cloud_url = res["url"]
                db.execute("UPDATE products SET image = ? WHERE id = ?", (cloud_url, prod["id"]))
                print(f"     [OK] Updated product '{prod['name']}' -> {cloud_url}")
                uploaded_count += 1
            else:
                print(f"     [FAILED] Could not upload {local_path} to Cloudinary.")
                failed_count += 1

        db.commit()

        print("\n-----------------------------------------------------------------")
        print(f"Migration Summary:")
        print(f"  - Uploaded & Updated : {uploaded_count}")
        print(f"  - Already on Cloud   : {skipped_count}")
        print(f"  - Missing / Failed   : {failed_count}")
        print("=================================================================\n")
    return True

if __name__ == "__main__":
    is_dry = "--dry-run" in sys.argv
    migrate_images(dry_run=is_dry)
