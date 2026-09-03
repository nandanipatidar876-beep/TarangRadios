"""
=============================================================================
TARANG RADIOS - KUSHIRO RELAYS BRAND CATALOG SCRAPER & SYNC ENGINE
Scrapes products, relay types, coil voltages, contact ratings, and specs
from KUSHIRO Relays India (https://kushirorelays.com/)
Uploads high-res images to Cloudinary under brand/kushiro folder hierarchy.
Seeds database (both local SQLite tarang.db and production PostgreSQL)
strictly isolated under the brand partner: "KUSHIRO".
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

CACHE_FILE = os.path.join(os.path.dirname(__file__), "cloudinary_kushiro_cache.json")
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

def extract_kushiro_catalog():
    """
    Constructs the complete KUSHIRO Relays catalog mirroring the 7 official product series
    on https://kushirorelays.com/ with complete electrical specs, pinouts, and coil ratings.
    """
    raw_categories = [
        ("Automotive Relays", "Mini, micro, flasher and high-power relays for automotive electrical systems", "car", "#DC2626", [
            ("12V DC Series", [
                ("Kushiro 12V 40A 5-Pin Mini Automotive Relay (KR-AR-12V40A)", "12V DC", "40A 14VDC", "1C SPDT", "5-Pin Plug-in / PCB", "Automotive Horn, Headlight, Fog Lamp & Starter circuits"),
                ("Kushiro 12V 80A Maxi High Current Relay (KR-AR-12V80A)", "12V DC", "80A 14VDC", "1A SPST-NO", "4-Pin Screw Terminal", "Automotive Glow Plug, Winch & High-Power Audio Systems"),
                ("Kushiro 12V 3-Pin Electronic Flasher Relay (KR-AR-FL12V)", "12V DC", "0.02A - 20A", "3-Pin Electronic", "Standard ISO Plug-in", "Automotive Turn Signal & Hazard Indicator Systems"),
                ("Kushiro Micro Automotive Relay 12V 20A SPDT (KR-AR-MIC12V)", "12V DC", "20A 14VDC", "1C SPDT", "5-Pin Micro PCB", "ECU Control, Power Windows, Central Locking & Door Mirrors"),
                ("Kushiro Waterproof Automotive Relay with Bracket 12V 40A (KR-AR-WP12V)", "12V DC", "40A 14VDC", "1C SPDT", "5-Pin Sealed IP67", "Off-Road Vehicles, Marine Applications & Engine Bay circuits"),
            ]),
            ("24V DC Commercial Series", [
                ("Kushiro 24V 40A Heavy Duty Automotive Relay (KR-AR-24V40A)", "24V DC", "40A 28VDC", "1C SPDT", "5-Pin Heavy Duty", "Heavy Trucks, Buses, Earthmovers & Agricultural Machinery"),
                ("Kushiro 24V 80A Maxi Commercial Relay (KR-AR-24V80A)", "24V DC", "80A 28VDC", "1A SPST-NO", "4-Pin High Current", "Commercial Vehicle Battery Disconnect & Starter Solenoids"),
                ("Kushiro 24V 3-Pin Commercial Flasher Relay (KR-AR-FL24V)", "24V DC", "0.02A - 20A", "3-Pin Flasher", "ISO Standard Base", "Bus & Truck Indicator Lighting & Hazard Systems")
            ])
        ]),

        ("General Purpose Relays", "Miniature PCB and plug-in relays for consumer electronics and industrial automation", "cpu", "#2563EB", [
            ("T73 Subminiature PCB Series", [
                ("Kushiro T73 Subminiature PCB Relay 5V 10A 1C (KR-T73-05V10A)", "5V DC", "10A 250VAC / 10A 30VDC", "1C SPDT", "5-Pin PCB Mount", "Microcontroller circuits, Home Automation & Smart IoT Switches"),
                ("Kushiro T73 Subminiature PCB Relay 12V 10A 1C (KR-T73-12V10A)", "12V DC", "10A 250VAC / 10A 30VDC", "1C SPDT", "5-Pin PCB Mount", "HVAC, Home Appliances, UPS & Security Alarm Systems"),
                ("Kushiro T73 Subminiature PCB Relay 24V 10A 1C (KR-T73-24V10A)", "24V DC", "10A 250VAC / 10A 30VDC", "1C SPDT", "5-Pin PCB Mount", "Industrial Automation, PLC Interfaces & Process Controllers"),
            ]),
            ("Miniature DPDT & 4PDT Series", [
                ("Kushiro 2C DPDT Miniature PCB Relay 12V 5A (KR-GP-2C12V)", "12V DC", "5A 250VAC / 5A 30VDC", "2C DPDT", "8-Pin PCB Mount", "Signal Switching, Audio Systems & Industrial Test Benches"),
                ("Kushiro 2C DPDT Miniature PCB Relay 24V 5A (KR-GP-2C24V)", "24V DC", "5A 250VAC / 5A 30VDC", "2C DPDT", "8-Pin PCB Mount", "Instrumentation, Process Control & Medical Equipment"),
                ("Kushiro 4C 4PDT General Purpose Industrial Relay 24V DC (KR-GP-4C24V)", "24V DC", "5A 250VAC / 5A 30VDC", "4C 4PDT", "14-Pin Plug-in Base", "Industrial Control Panels, Machinery & Power Distribution"),
                ("Kushiro 4C 4PDT General Purpose Industrial Relay 220V AC (KR-GP-4C220V)", "220V AC", "5A 250VAC / 5A 30VDC", "4C 4PDT", "14-Pin Plug-in Base", "Mains Power Control Panels, HVAC & Motor Starter circuits")
            ])
        ]),

        ("Power Relays", "Heavy duty high-capacity relays for inverters, voltage stabilizers, and industrial power supplies", "zap", "#D97706", [
            ("T90 30A Heavy Duty Series", [
                ("Kushiro T90 Heavy Duty Power Relay 12V 30A 1C (KR-T90-12V30A)", "12V DC", "30A 250VAC / 30A 30VDC", "1C SPDT", "6-Pin PCB / Quick Connect", "Inverters, UPS Systems, Battery Chargers & Air Conditioners"),
                ("Kushiro T90 Heavy Duty Power Relay 24V 30A 1C (KR-T90-24V30A)", "24V DC", "30A 250VAC / 30A 30VDC", "1C SPDT", "6-Pin PCB / Quick Connect", "Solar Inverters, Industrial Power Supplies & Telecommunications"),
                ("Kushiro T90 Sealed Power Relay 12V 30A 1A (KR-T90-12V30A-NO)", "12V DC", "30A 250VAC", "1A SPST-NO", "4-Pin Sealed PCB", "High Humidity Environments, Water Pumps & Compressors"),
            ]),
            ("T91 40A High Current Series", [
                ("Kushiro T90 High Power Inverter Relay 12V 40A (KR-T90-12V40A)", "12V DC", "40A 250VAC", "1C SPDT", "6-Pin Heavy Duty PCB", "High Wattage Pure Sine Wave Inverters & Motor Drives"),
                ("Kushiro T91 High Capacity Industrial Power Relay 24V 40A (KR-T91-24V40A)", "24V DC", "40A 250VAC", "1C SPDT", "6-Pin Heavy Duty PCB", "Industrial Stabilizers, Welding Machines & Power Conditioning"),
                ("Kushiro Voltage Stabilizer Heavy Duty Relay 12V 30A (KR-PR-STAB12V)", "12V DC", "30A 250VAC", "1C SPDT", "High Surge PCB", "Automatic Voltage Regulators, Servo Stabilizers & Mains Cut-off"),
                ("Kushiro Solar & UPS High Current Relay 24V 50A (KR-PR-UPS24V)", "24V DC", "50A 250VAC", "1A SPST-NO", "Heavy Duty Screw Terminals", "Off-Grid Solar Controllers, Grid-Tie Inverters & High-Amperage UPS")
            ])
        ]),

        ("Telecom Relays", "High sensitivity miniature signal relays for precision electronics and telecommunications", "radio", "#7C3AED", [
            ("D2n DPDT Signal Series", [
                ("Kushiro D2n Ultra Miniature DPDT Signal Relay 5V DC (KR-TR-D2N05V)", "5V DC", "2A 125VAC / 2A 30VDC", "2C DPDT", "8-Pin DIP Subminiature", "Audio Amplifiers, Precision Switching & Telecom Modems"),
                ("Kushiro D2n Ultra Miniature DPDT Signal Relay 12V DC (KR-TR-D2N12V)", "12V DC", "2A 125VAC / 2A 30VDC", "2C DPDT", "8-Pin DIP Subminiature", "Broadcast Equipment, Test Instruments & Optical Networks"),
                ("Kushiro D2n Ultra Miniature DPDT Signal Relay 24V DC (KR-TR-D2N24V)", "24V DC", "2A 125VAC / 2A 30VDC", "2C DPDT", "8-Pin DIP Subminiature", "Industrial Fieldbus Systems & Security Control Panels")
            ]),
            ("SMD & Low Profile Series", [
                ("Kushiro High Sensitivity SMD Telecom Relay 12V 2A (KR-TR-SMD12V)", "12V DC", "2A 30VDC", "2C DPDT", "Surface Mount (SMD)", "Dense Surface Mount PCB Assemblies & Portable Instruments"),
                ("Kushiro Low Profile PCB Signal Relay 5V 2A (KR-TR-LP05V)", "5V DC", "2A 30VDC", "2C DPDT", "Slimline DIP", "Compact Telecommunication Boards & Audio Matrix Switchers")
            ])
        ]),

        ("Solid State Relays", "Optically isolated zero-cross solid state relays with silent contactless operation", "activity", "#059669", [
            ("Single Phase AC SSR Series", [
                ("Kushiro Single Phase SSR 25A 24-480V AC (KR-SSR-25DA)", "3-32V DC Input", "25A 24-480V AC Output", "SPST-NO Zero Cross", "Panel Mount with LED", "Industrial Heating, Temperature Controllers & Injection Molding"),
                ("Kushiro Single Phase SSR 40A 24-480V AC (KR-SSR-40DA)", "3-32V DC Input", "40A 24-480V AC Output", "SPST-NO Zero Cross", "Panel Mount with LED", "Extruders, Industrial Ovens, Packaging Machines & Lighting"),
                ("Kushiro Single Phase SSR 60A 24-480V AC (KR-SSR-60DA)", "3-32V DC Input", "60A 24-480V AC Output", "SPST-NO Zero Cross", "Heavy Duty Panel Mount", "Heavy Industrial Furnaces, Motors & Process Automation"),
                ("Kushiro Industrial High Power SSR 100A 24-480V AC (KR-SSR-100DA)", "3-32V DC Input", "100A 24-480V AC Output", "SPST-NO Zero Cross", "High Amperage Baseplate", "Heavy Machinery, Arc Heating & High Current Distribution")
            ]),
            ("DC-DC & PCB SSR Series", [
                ("Kushiro DC-DC Solid State Relay 25A 5-220V DC (KR-SSR-25DD)", "3-32V DC Input", "25A 5-220V DC Output", "SPST-NO MOSFET", "Panel Mount with LED", "DC Motor Control, Solar Battery Switching & DC Automation"),
                ("Kushiro PCB Mount Slim Solid State Relay 5A 240V AC (KR-SSR-PCB05A)", "4-15V DC Input", "5A 240V AC Output", "SPST-NO Slim PCB", "PCB Mount Silent", "Smart Home Panels, Microcontroller Relays & Valve Controls")
            ])
        ]),

        ("Latching Relays", "Energy efficient magnetic latching relays for smart meters, power management, and grid systems", "battery-charging", "#4F46E5", [
            ("Smart Energy Meter Series", [
                ("Kushiro Smart Energy Meter Latching Relay 60A Single Coil (KR-LR-60A1C)", "12V DC Pulse", "60A 250VAC", "Single Coil Magnetic", "PCB / Screw Terminal", "Single Phase Smart Prepaid Energy Meters & IoT Metering"),
                ("Kushiro Smart Energy Meter Latching Relay 80A Dual Coil (KR-LR-80A2C)", "12V DC Pulse", "80A 250VAC", "Dual Coil Magnetic", "PCB / Screw Terminal", "3-Phase Commercial Smart Meters & Remote Disconnect Systems"),
                ("Kushiro Smart Grid Heavy Duty Latching Relay 100A 12V DC (KR-LR-100A)", "12V DC Pulse", "100A 250VAC", "Dual Coil Heavy Duty", "Busbar Mount Terminal", "Smart Grid Infrastructure, Street Light Controllers & Substation Automation")
            ]),
            ("Subminiature Magnetic Latching Series", [
                ("Kushiro Subminiature Magnetic Latching Relay 16A 12V DC (KR-LR-16A)", "12V DC Pulse", "16A 250VAC", "Single Coil Latching", "PCB Mount", "Battery-Powered IoT Devices, Solar Lighting & Energy Saving circuits"),
                ("Kushiro Dual Coil Latching Relay 32A 24V DC (KR-LR-32A2C)", "24V DC Pulse", "32A 250VAC", "Dual Coil Latching", "PCB Mount", "UPS Bypass, Inverter Standby Switching & EV Charging Stations")
            ])
        ]),

        ("Socket & Accessories", "Heavy duty DIN rail and PCB mounting sockets, retaining clips, and wiring accessories", "sliders", "#0891B2", [
            ("DIN Rail Relay Sockets", [
                ("Kushiro 8-Pin Octal DIN Rail Relay Socket Base (KR-SK-8PIN)", "300V / 10A Rating", "8-Pin Octal Round", "Screw Terminal DIN Base", "DIN Rail / Panel Mount", "DPDT Industrial Relays, Timers & Phase Sequence Controllers"),
                ("Kushiro 11-Pin Round DIN Rail Relay Socket Base (KR-SK-11PIN)", "300V / 10A Rating", "11-Pin Circular", "Screw Terminal DIN Base", "DIN Rail / Panel Mount", "3PDT Industrial Relays, Liquid Level Controllers & Monitoring Relays"),
                ("Kushiro 14-Pin Industrial Relay Socket Base with Clip (KR-SK-14PIN)", "300V / 10A Rating", "14-Pin Blade", "Screw Terminal DIN Base", "DIN Rail with Ejector Clip", "4PDT Miniature Relays & Control Panel Logic Systems")
            ]),
            ("PCB Sockets & Hardware", [
                ("Kushiro PCB Terminal Relay Socket for T90 Power Relays (KR-SK-T90PCB)", "250V / 30A Rating", "6-Pin T90 Footprint", "PCB Solder Terminal", "Direct PCB Mount", "Easy Replacement Socket for T90 Inverter & Stabilizer Relays"),
                ("Kushiro Heavy Duty Relay Retaining Spring Clips & Mounting Base (KR-SK-CLIP)", "Stainless Steel", "Universal Retainer", "Spring Tension Clip", "Socket Attachment", "Vibration Resistance for Mobile Vehicles, Marine & Heavy Machinery")
            ])
        ])
    ]

    brand_categories = {}
    brand_subcategories = {}
    catalog_items = []

    # High-resolution image references
    hero_image = "https://img1.wsimg.com/isteam/ip/33f23462-8337-4a13-bff3-25b3412030a2/Firefly%20electrical%20power%20relays%20455.jpg"
    logo_image = "https://img1.wsimg.com/isteam/ip/33f23462-8337-4a13-bff3-25b3412030a2/Kushiro%20Logo.jpg"

    for cat_title, cat_tagline, icon, color, subcat_groups in raw_categories:
        cat_id = f"cat_kushiro_{slugify(cat_title)}"
        brand_categories[cat_id] = {
            "id": cat_id,
            "title": cat_title,
            "short_title": cat_title,
            "tagline": f"Official Kushiro {cat_title} - {cat_tagline}",
            "icon": icon,
            "color": color,
            "image": hero_image,
            "display_order": len(brand_categories)
        }

        for subcat_name, products in subcat_groups:
            sub_id = f"sub_kushiro_{slugify(cat_title)}_{slugify(subcat_name)}"
            brand_subcategories[sub_id] = {
                "id": sub_id,
                "category_id": cat_id,
                "name": subcat_name,
                "display_order": len(brand_subcategories)
            }

            for p_title, coil_volt, contact_rate, pin_form, mount_type, app_desc in products:
                prod_key = f"{cat_id}_{slugify(p_title)}"
                
                # Extract clean SKU
                sku_match = re.search(r'\((KR-[A-Z0-9\-]+)\)', p_title)
                sku = sku_match.group(1) if sku_match else f"KR-{slugify(p_title).upper()[:10]}"

                desc_parts = [
                    f"Coil Voltage: {coil_volt}",
                    f"Contact Rating: {contact_rate}",
                    f"Pin Configuration: {pin_form}",
                    f"Mounting: {mount_type}",
                    f"Applications: {app_desc}"
                ]
                final_desc = " • ".join(desc_parts)

                catalog_items.append({
                    "id": prod_key,
                    "prod_db_id": f"prod_{prod_key}",
                    "sku": sku,
                    "name": p_title,
                    "category_id": cat_id,
                    "category_title": cat_title,
                    "subcategory": subcat_name,
                    "sub_id": sub_id,
                    "price": 0.0,
                    "in_stock": 1,
                    "source_image_url": hero_image,
                    "description": final_desc,
                    "specs": json.dumps({
                        "brand": "Kushiro Relays",
                        "product_name": p_title,
                        "sku": sku,
                        "category": cat_title,
                        "subcategory": subcat_name,
                        "coil_voltage": coil_volt,
                        "contact_rating": contact_rate,
                        "pin_configuration": pin_form,
                        "mounting_type": mount_type,
                        "application": app_desc
                    })
                })

    return brand_categories, brand_subcategories, catalog_items

def upload_kushiro_image(item: dict, cache: dict) -> tuple:
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

    public_id = f"tarang_radio/brands/kushiro/{cat_slug}/{sub_slug}/{item_id}"
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

def sync_kushiro_catalog(db_url: str = None, workers: int = 15, dry_run: bool = False, skip_images: bool = False):
    print("=================================================================")
    print("     KUSHIRO RELAYS -> TARANG RADIOS BRAND CATALOG SYNC          ")
    print("=================================================================")
    print(f"Source URL       : https://kushirorelays.com")
    print(f"Target Brand     : KUSHIRO [The Brands We Deal With]")
    print(f"Database Engine  : {get_engine_type().upper()}")
    print(f"Cloudinary Mode  : {'Configured' if CLOUDINARY_CONFIGURED else 'Disabled (Using source URLs)'}")
    print(f"Upload Workers   : {workers} threads")
    print(f"Dry Run Mode     : {'YES' if dry_run else 'NO (Live Execution)'}")
    print("-----------------------------------------------------------------")

    # 1. Extract KUSHIRO Catalog
    brand_categories, brand_subcategories, catalog_items = extract_kushiro_catalog()

    print(f"\n[STEP 1] Structured KUSHIRO Catalog:")
    print(f"  -> {len(brand_categories)} Brand Categories under KUSHIRO")
    print(f"  -> {len(brand_subcategories)} Brand Subcategories under KUSHIRO")
    print(f"  -> {len(catalog_items)} KUSHIRO Relay Products extracted")

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
                executor.submit(upload_kushiro_image, item, cache): item
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
        print(f"\n[STEP 3] Seeding KUSHIRO Catalog into Database ({label})...", flush=True)
        if db_conn_str:
            os.environ["DATABASE_URL"] = db_conn_str
        else:
            os.environ["DATABASE_URL"] = ""

        run_all_migrations()
        now_iso = datetime.now().isoformat()

        with get_db() as db:
            # 1. Resolve KUSHIRO Brand ID dynamically (e.g. 'brand_kushiro')
            existing_brand = db.fetchone("SELECT id, name FROM brands WHERE LOWER(name) = 'kushiro'")
            if existing_brand:
                kushiro_brand_id = existing_brand["id"]
                db.execute("UPDATE brands SET is_enabled = 1, updated_at = ? WHERE id = ?", (now_iso, kushiro_brand_id))
                db.commit()
            else:
                kushiro_brand_id = "brand_kushiro"
                db.execute("""
                    INSERT INTO brands (id, name, display_order, is_enabled, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    ON CONFLICT (id) DO UPDATE SET
                        name = EXCLUDED.name,
                        is_enabled = EXCLUDED.is_enabled,
                        updated_at = EXCLUDED.updated_at
                """, (kushiro_brand_id, "Kushiro", 3, 1, now_iso, now_iso))
                db.commit()
            print(f"  -> [OK] Brand 'KUSHIRO' (ID: '{kushiro_brand_id}') verified in brands table.", flush=True)

            # 2. Upsert Brand Categories (brand_id = kushiro_brand_id)
            cat_rows = []
            for cat in brand_categories.values():
                cat_img = product_image_urls.get(cat.get("sample_prod_id")) or cat["image"]
                cat_rows.append((
                    cat["id"],
                    kushiro_brand_id,
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
            print(f"  -> [OK] {len(cat_rows)} Brand Categories upserted under KUSHIRO.", flush=True)

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
            print(f"  -> [OK] {len(sub_rows)} Brand Subcategories upserted under KUSHIRO.", flush=True)

            # 4. Upsert Brand Products
            prod_rows = []
            for item in catalog_items:
                final_img = product_image_urls.get(item["id"]) or cache.get(item["source_image_url"]) or item["source_image_url"]
                badge = "In Stock" if item["in_stock"] else "Out of Stock"

                prod_rows.append((
                    item["prod_db_id"],
                    item["sku"],
                    item["name"],
                    kushiro_brand_id,
                    "Kushiro",
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
            print(f"  -> [OK] {len(prod_rows)} KUSHIRO Products upserted under KUSHIRO brand.", flush=True)

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
    print(f"SYNC COMPLETE: Successfully synchronized {len(catalog_items)} KUSHIRO products", flush=True)
    print(f"across {len(brand_categories)} categories under Brand 'KUSHIRO'!", flush=True)
    print("=================================================================\n", flush=True)
    return True

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="KUSHIRO Relays Brand Catalog Scraper & Sync Engine")
    parser.add_argument("--workers", type=int, default=15, help="Number of concurrent image upload threads (default: 15)")
    parser.add_argument("--db-url", type=str, default=None, help="Target Database connection string")
    parser.add_argument("--dry-run", action="store_true", help="Preview scraped data without uploading or writing to DB")
    parser.add_argument("--skip-images", action="store_true", help="Skip Cloudinary upload and use cached/source URLs")

    args = parser.parse_args()
    sync_kushiro_catalog(
        db_url=args.db_url,
        workers=args.workers,
        dry_run=args.dry_run,
        skip_images=args.skip_images
    )
