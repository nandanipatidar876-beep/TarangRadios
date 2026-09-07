import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import db

with open("scratch/uploaded_ingco_images.json", "r", encoding="utf-8") as f:
    images = json.load(f)

print(f"Loaded {len(images)} uploaded Cloudinary images.")

conn = db.get_db()
cursor = conn.cursor()

# 1. Ensure INGCO Brand exists
brand_id = "brand_ingco"
cursor.execute("SELECT id FROM brands WHERE id = %s OR LOWER(name) = 'ingco'", (brand_id,))
b_row = cursor.fetchone()
if not b_row:
    cursor.execute("""
        INSERT INTO brands (id, name, display_order, is_enabled, created_at, updated_at)
        VALUES (%s, 'INGCO', 6, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
    """, (brand_id,))
else:
    brand_id = b_row["id"]
    cursor.execute("UPDATE brands SET is_enabled = 1 WHERE id = %s", (brand_id,))

# 2. Setup INGCO Brand-Specific Categories
brand_categories = [
    {
        "id": "cat_ingco_soldering",
        "brand_id": brand_id,
        "title": "INGCO Soldering & Welding",
        "short_title": "Soldering & Welding",
        "tagline": "Professional Temperature-Controlled & Electric Soldering Tools",
        "icon": "zap",
        "color": "#F2C94C",
        "display_order": 1
    },
    {
        "id": "cat_ingco_rotary",
        "brand_id": brand_id,
        "title": "INGCO Mini Grinders & Rotary",
        "short_title": "Rotary & Grinders",
        "tagline": "Variable Speed Rotary Tools, Flex Shafts & Mounted Stones",
        "icon": "settings",
        "color": "#D14B14",
        "display_order": 2
    },
    {
        "id": "cat_ingco_glue",
        "brand_id": brand_id,
        "title": "INGCO Glue Guns & Adhesives",
        "short_title": "Glue Guns",
        "tagline": "Fast Heating Electric Glue Guns & Supplies",
        "icon": "flame",
        "color": "#F2C94C",
        "display_order": 3
    },
    {
        "id": "cat_ingco_cordless",
        "brand_id": brand_id,
        "title": "INGCO Cordless Power Tools",
        "short_title": "Cordless Tools",
        "tagline": "High Performance 20V P20S, 12V & 4V Lithium-Ion Drills",
        "icon": "battery-charging",
        "color": "#E67E22",
        "display_order": 4
    },
    {
        "id": "cat_ingco_electric",
        "brand_id": brand_id,
        "title": "INGCO Electric Power Tools",
        "short_title": "Electric Tools",
        "tagline": "Heavy Duty Impact Drills, Drills & Heat Guns",
        "icon": "cpu",
        "color": "#C0392B",
        "display_order": 5
    },
    {
        "id": "cat_ingco_handtools",
        "brand_id": brand_id,
        "title": "INGCO Hand Tools & Cutters",
        "short_title": "Hand Tools",
        "tagline": "Precision Wire Strippers, Pliers, Crimpers & Utility Knives",
        "icon": "tool",
        "color": "#27AE60",
        "display_order": 6
    }
]

for cat in brand_categories:
    cursor.execute("SELECT id FROM categories WHERE id = %s", (cat["id"],))
    if not cursor.fetchone():
        cursor.execute("""
            INSERT INTO categories (id, brand_id, title, short_title, tagline, icon, color, display_order, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        """, (cat["id"], cat["brand_id"], cat["title"], cat["short_title"], cat["tagline"], cat["icon"], cat["color"], cat["display_order"]))
        print(f"Created category {cat['title']}")
    else:
        cursor.execute("""
            UPDATE categories SET brand_id = %s, title = %s, short_title = %s, tagline = %s, color = %s WHERE id = %s
        """, (cat["brand_id"], cat["title"], cat["short_title"], cat["tagline"], cat["color"], cat["id"]))

# 3. Setup Subcategories
subcategories = [
    {"id": "sub_ingco_soldering_irons", "category_id": "cat_ingco_soldering", "name": "Soldering Irons", "display_order": 1},
    {"id": "sub_ingco_rotary_tools", "category_id": "cat_ingco_rotary", "name": "Rotary Tools & Accessories", "display_order": 1},
    {"id": "sub_ingco_glue_guns", "category_id": "cat_ingco_glue", "name": "Hot Melt Glue Guns", "display_order": 1},
    {"id": "sub_ingco_cordless_drills", "category_id": "cat_ingco_cordless", "name": "Cordless Drills & Screwdrivers", "display_order": 1},
    {"id": "sub_ingco_batteries", "category_id": "cat_ingco_cordless", "name": "Batteries & Chargers", "display_order": 2},
    {"id": "sub_ingco_impact_drills", "category_id": "cat_ingco_electric", "name": "Electric Drills & Impact Drills", "display_order": 1},
    {"id": "sub_ingco_heat_guns", "category_id": "cat_ingco_electric", "name": "Electric Heat Guns", "display_order": 2},
    {"id": "sub_ingco_wire_strippers", "category_id": "cat_ingco_handtools", "name": "Wire Strippers & Crimpers", "display_order": 1},
    {"id": "sub_ingco_pliers", "category_id": "cat_ingco_handtools", "name": "Pliers", "display_order": 2},
    {"id": "sub_ingco_utility_knives", "category_id": "cat_ingco_handtools", "name": "Utility Knives & Cutters", "display_order": 3},
    {"id": "sub_ingco_testers", "category_id": "cat_ingco_handtools", "name": "Test Pencils & Detectors", "display_order": 4}
]

for sub in subcategories:
    cursor.execute("SELECT id FROM subcategories WHERE id = %s", (sub["id"],))
    if not cursor.fetchone():
        cursor.execute("""
            INSERT INTO subcategories (id, category_id, name, display_order)
            VALUES (%s, %s, %s, %s)
        """, (sub["id"], sub["category_id"], sub["name"], sub["display_order"]))
        print(f"Created subcategory {sub['name']}")

# 4. Verified Products Data List
products = [
    # --- SOLDERING & ROTARY & GLUE ---
    {
        "sku": "SI01606",
        "name": "INGCO 70W Temperature Control Soldering Iron (SI01606)",
        "category_id": "cat_ingco_soldering",
        "subcategory": "Soldering Irons",
        "price": 450.00,
        "badge": "Ceramic Core",
        "description": "Professional 70W electric soldering iron with built-in ceramic heating core, quick 120-second preheating, adjustable temperature control knob (200°C-500°C), On/Off power switch, and long-life replaceable tip.",
        "specs": {
            "Model Number": "SI01606",
            "Input Power": "70W",
            "Voltage": "220-240V ~ 50/60Hz",
            "Heating Core": "Ceramic Heating Element",
            "Temperature Control": "Adjustable Knob (200°C - 500°C)",
            "Preheat Time": "120 - 180 seconds",
            "Features": "On/Off Power Switch, Replaceable Long Life Tip"
        }
    },
    {
        "sku": "SF0248",
        "name": "INGCO 40W Electric Soldering Iron (SF0248 / SI0248)",
        "category_id": "cat_ingco_soldering",
        "subcategory": "Soldering Irons",
        "price": 240.00,
        "badge": "Titan Heater",
        "description": "Reliable 40W electric soldering iron equipped with long-life titan heater, fast thermal recovery, straight replaceable tip, EU 2-pin plug, and ergonomic non-slip handle.",
        "specs": {
            "Model Number": "SF0248 / SI0248",
            "Input Power": "40W",
            "Voltage": "220-240V ~ 50/60Hz",
            "Heater Type": "Long Life Titan Heater",
            "Preheat Time": "3 - 5 minutes",
            "Tip Type": "Straight Replaceable Long Life Tip",
            "Plug Standard": "EU 2-Pin"
        }
    },
    {
        "sku": "GG148",
        "name": "INGCO 20W (Max 100W) Hot Melt Glue Gun (GG148)",
        "category_id": "cat_ingco_glue",
        "subcategory": "Hot Melt Glue Guns",
        "price": 380.00,
        "badge": "Max 100W Peak",
        "description": "Heavy-duty 20W (Max 100W peak) hot melt glue gun compatible with 11.2mm glue sticks. Features PTC heating element, ergonomic trigger, fold-down stand, and includes 2 Pcs 11mm glue sticks.",
        "specs": {
            "Model Number": "GG148",
            "Input Power": "20W (Max 100W Peak)",
            "Voltage": "220-240V ~ 50/60Hz",
            "Glue Stick Diameter": "11.2mm (Ø11mm)",
            "Gluing Capacity": "13 - 18 g/min",
            "Preheat Time": "3 - 5 minutes",
            "Included Accessories": "2 Pcs Ø11mm Glue Sticks"
        }
    },
    {
        "sku": "AKB1012",
        "name": "INGCO 10Pcs Mounted Grinding Stone Set (AKB1012)",
        "category_id": "cat_ingco_rotary",
        "subcategory": "Rotary Tools & Accessories",
        "price": 160.00,
        "badge": "3mm Shank",
        "description": "Precision 10Pcs aluminum oxide mounted grinding stone set with standard 3mm shank for rotary mini grinders (MG13328). Includes bullet, cone, T-type, and round grinding stones.",
        "specs": {
            "Model Number": "AKB1012",
            "Set Count": "10 Pieces per Set",
            "Shank Diameter": "3mm (1/8 inch)",
            "Material": "High-Grade Aluminum Oxide Abrasive",
            "Compatible Tools": "INGCO Mini Grinders (MG13328, MG2008)",
            "Set Contents": "2 Pcs Bullet, 4 Pcs Cone, 2 Pcs T-Type, 2 Pcs Round Stones"
        }
    },
    {
        "sku": "MG13328",
        "name": "INGCO 130W Variable Speed Mini Grinder Kit (MG13328)",
        "category_id": "cat_ingco_rotary",
        "subcategory": "Rotary Tools & Accessories",
        "price": 1850.00,
        "badge": "109Pcs Kit + Flex Shaft",
        "description": "High-precision 130W variable speed rotary tool & mini grinder kit (10,000 - 35,000 RPM) with flexible extension shaft, 109 Pcs accessories set, replacement carbon brushes, and heavy-duty blow-molded carrying case.",
        "specs": {
            "Model Number": "MG13328",
            "Input Power": "130W",
            "Voltage": "220-240V ~ 50/60Hz",
            "No-Load Speed": "10,000 - 35,000 RPM (6 Speed Control)",
            "Collet Capacity": "3.2mm / 2.3mm",
            "Included Accessories": "109 Pcs Accessories + Flexible Extension Shaft",
            "Case Type": "Heavy Duty BMC Carrying Case"
        }
    },

    # --- WIRE STRIPPERS & HAND TOOLS ---
    {
        "sku": "HWSP102418",
        "name": "INGCO 3-in-1 Automatic Wire Stripper (HWSP102418)",
        "category_id": "cat_ingco_handtools",
        "subcategory": "Wire Strippers & Crimpers",
        "price": 750.00,
        "badge": "3-in-1 Automatic",
        "description": "Heavy-duty 3-in-1 multi-function automatic wire stripper, wire cutter, and terminal crimper (210mm / 8.5 inch). Self-adjusting mechanism strips 10-24 AWG (0.2-6mm²) wires cleanly without damaging conductor strands.",
        "specs": {
            "Model Number": "HWSP102418",
            "Functions": "Stripping, Cutting, Crimping",
            "Stripping Range": "10 - 24 AWG (0.2 - 6.0 mm²)",
            "Crimping Capacity": "Insulated & Non-Insulated 0.5 - 6.0 mm²",
            "Overall Length": "210 mm (8.5 inch)",
            "Handle": "Ergonomic Two-Tone Non-Slip Grip"
        }
    },
    {
        "sku": "HWSP851",
        "name": "INGCO 8.5 Inch Wire Stripper & Cutter (HWSP851)",
        "category_id": "cat_ingco_handtools",
        "subcategory": "Wire Strippers & Crimpers",
        "price": 280.00,
        "badge": "Multi-Gauge",
        "description": "Professional 8.5 inch (215mm) manual wire stripper and cutter forged from high-carbon steel. Features precision-ground stripping notches for 7 wire gauges, screw shearing holes, and looping holes.",
        "specs": {
            "Model Number": "HWSP851",
            "Size": "8.5 Inch (215 mm)",
            "Material": "High-Carbon Steel",
            "Wire Sizes": "Strips 7 different wire sizes",
            "Screw Shearing": "Cuts 5 copper screw sizes",
            "Handle": "Double-Dipped Cushion Grip"
        }
    },
    {
        "sku": "HWSP101",
        "name": "INGCO 10 Inch Heavy Duty Wire Stripper (HWSP101)",
        "category_id": "cat_ingco_handtools",
        "subcategory": "Wire Strippers & Crimpers",
        "price": 340.00,
        "badge": "CR-V Steel",
        "description": "Rugged 10 inch (254mm) heavy-duty industrial wire stripper and crimping pliers constructed from heat-treated Chrome Vanadium (CR-V) steel for extended jobsite durability.",
        "specs": {
            "Model Number": "HWSP101",
            "Size": "10 Inch (254 mm)",
            "Material": "Chrome Vanadium (CR-V) Steel",
            "Functions": "Wire Stripping, Wire Cutting, Terminal Crimping",
            "Cutting Edges": "Induction-Hardened Precision Edges"
        }
    },
    {
        "sku": "HRCPG05210",
        "name": "INGCO 6 Inch Ratchet Crimping Plier (HRCPG05210)",
        "category_id": "cat_ingco_handtools",
        "subcategory": "Wire Strippers & Crimpers",
        "price": 890.00,
        "badge": "Self-Adjusting Ratchet",
        "description": "Professional self-adjusting ratchet crimping pliers (0.25 - 10 mm² / AWG 23-7) for tubular bare terminals and pre-insulated wire ferrules. Built-in ratchet release ensures uniform, gas-tight crimps every cycle.",
        "specs": {
            "Model Number": "HRCPG05210",
            "Crimping Capacity": "0.25 - 10 mm² (AWG 23 - 7)",
            "Mechanism": "Adjustable Ratchet with Quick Release",
            "Applicable Terminals": "Tubular Bare & Pre-insulated Ferrules",
            "Material": "Special Carbon Steel with Black Oxide Finish"
        }
    },
    {
        "sku": "HCP08202",
        "name": "INGCO 8 Inch High Leverage Combination Pliers (HCP08202)",
        "category_id": "cat_ingco_handtools",
        "subcategory": "Pliers",
        "price": 320.00,
        "badge": "Cr-V High Leverage",
        "description": "Industrial grade 8 inch (200mm) combination pliers made of forged Chrome Vanadium (Cr-V) steel. High leverage design delivers 30% more cutting power with less hand force.",
        "specs": {
            "Model Number": "HCP08202",
            "Size": "8 Inch (200 mm)",
            "Material": "Chrome Vanadium (Cr-V) Steel",
            "Features": "30% High Leverage Energy Saving Pivot",
            "Handle": "Ergonomic Two-Color TPR Grip"
        }
    },
    {
        "sku": "HLNP08168",
        "name": "INGCO 6 Inch High Leverage Long Nose Pliers (HLNP08168)",
        "category_id": "cat_ingco_handtools",
        "subcategory": "Pliers",
        "price": 280.00,
        "badge": "Cr-V Long Nose",
        "description": "Precision 6 inch (160mm) high leverage long nose needle pliers with integrated wire cutting blade. Ideal for electronics, gripping small components, and intricate mechanical assembly.",
        "specs": {
            "Model Number": "HLNP08168",
            "Size": "6 Inch (160 mm)",
            "Material": "Forged Chrome Vanadium (Cr-V)",
            "Features": "Precision Serrated Jaws, Induction-Hardened Cutters",
            "Finish": "Anti-Rust Polished Teflon Coating"
        }
    },
    {
        "sku": "HKNS110925",
        "name": "INGCO 9mm Snap-off Blade Utility Knife (HKNS110925)",
        "category_id": "cat_ingco_handtools",
        "subcategory": "Utility Knives & Cutters",
        "price": 60.00,
        "badge": "Auto-Lock SK5",
        "description": "Slim, high-durability snap-off utility cutter with 9mm x 80mm high-carbon SK5 steel blades, positive auto-lock slider button, and integrated blade snapper tail cap.",
        "specs": {
            "Model Number": "HKNS110925",
            "Blade Size": "9 mm x 80 mm",
            "Blade Material": "SK5 High Carbon Steel",
            "Locking Mechanism": "Automatic Safety Slider Lock",
            "Body": "Durable Lightweight ABS with Tail Blade Snapper"
        }
    },
    {
        "sku": "HUK615",
        "name": "INGCO Heavy Duty Zinc Alloy Utility Knife (HUK615)",
        "category_id": "cat_ingco_handtools",
        "subcategory": "Utility Knives & Cutters",
        "price": 140.00,
        "badge": "Zinc Alloy Body",
        "description": "Heavy-duty 19x61mm industrial utility knife featuring a solid zinc alloy die-cast body, multi-position locking slide, non-slip rubber grip, and quick-change blade mechanism.",
        "specs": {
            "Model Number": "HUK615",
            "Blade Size": "19 mm x 61 mm Trapezoid Blade",
            "Body Material": "Die-Cast Zinc Alloy",
            "Handle": "Ergonomic Rubber Soft Grip",
            "Features": "Multi-Stop Retractable Blade Slider"
        }
    },
    {
        "sku": "HSDT1908",
        "name": "INGCO 100-500V Electrical Test Pencil (HSDT1908)",
        "category_id": "cat_ingco_handtools",
        "subcategory": "Test Pencils & Detectors",
        "price": 85.00,
        "badge": "100-500V AC",
        "description": "Essential electrician's 100-500V AC voltage tester screwdriver (4mm x 190mm) with high-visibility neon indicator bulb, insulated transparent handle, and pocket clip.",
        "specs": {
            "Model Number": "HSDT1908",
            "Test Voltage Range": "100V - 500V AC",
            "Tip Dimensions": "Slotted 4.0 mm x 190 mm",
            "Indicator": "High-Luminance Neon Lamp",
            "Safety standard": "CE Certified Insulation"
        }
    },

    # --- CORDLESS POWER TOOLS ---
    {
        "sku": "CDLI 205062",
        "name": "INGCO 20V Compact Brushless Cordless Drill (CDLI 205062)",
        "category_id": "cat_ingco_cordless",
        "subcategory": "Cordless Drills & Screwdrivers",
        "price": 3850.00,
        "badge": "Brushless Motor",
        "description": "High-efficiency 20V brushless cordless drill driver delivering 50Nm max torque, 2-speed all-metal gearbox (0-500 / 0-2000 RPM), 20+1 clutch settings, 13mm keyless metal chuck, and LED worklight.",
        "specs": {
            "Model Number": "CDLI 205062",
            "Voltage": "20V (INGCO P20S Platform)",
            "Motor Type": "High Efficiency Brushless Motor",
            "Max Torque": "50 Nm",
            "No-Load Speed": "0-500 / 0-2000 RPM (2-Speed)",
            "Chuck Capacity": "13 mm (1/2\") Metal Keyless",
            "Clutch Settings": "20 + 1 Settings"
        }
    },
    {
        "sku": "CIDLI 20558",
        "name": "INGCO 20V Brushless Cordless Impact Drill (CIDLI 20558)",
        "category_id": "cat_ingco_cordless",
        "subcategory": "Cordless Drills & Screwdrivers",
        "price": 4650.00,
        "badge": "20V Brushless Impact",
        "description": "Industrial grade 20V brushless cordless impact hammer drill (55Nm torque) with hammer drilling mode for masonry and brick, 13mm heavy-duty ratcheting chuck, and dual speed transmission.",
        "specs": {
            "Model Number": "CIDLI 20558",
            "Voltage": "20V (P20S Compatible)",
            "Motor Type": "Industrial Brushless Motor",
            "Max Torque": "55 Nm",
            "Impact Rate": "0-7500 / 0-30000 BPM",
            "No-Load Speed": "0-550 / 0-2000 RPM",
            "Chuck Size": "13 mm Metal Keyless"
        }
    },
    {
        "sku": "FBLI 20011",
        "name": "INGCO 20V 2.0Ah Lithium-Ion Battery Pack (FBLI 20011)",
        "category_id": "cat_ingco_cordless",
        "subcategory": "Batteries & Chargers",
        "price": 1450.00,
        "badge": "2.0Ah P20S Pack",
        "description": "Official INGCO P20S 20V 2.0Ah lithium-ion high-capacity battery pack with integrated 3-stage LED battery power status indicator and internal cell protection against overheating and overload.",
        "specs": {
            "Model Number": "FBLI 20011",
            "Voltage": "20V",
            "Battery Chemistry": "Lithium-Ion",
            "Capacity": "2.0 Ah (40 Wh)",
            "Compatibility": "All INGCO 20V P20S Power Tools",
            "Features": "LED Battery Fuel Gauge"
        }
    },
    {
        "sku": "CDLI 12456",
        "name": "INGCO 12V Cordless Drill Driver (CDLI 12456)",
        "category_id": "cat_ingco_cordless",
        "subcategory": "Cordless Drills & Screwdrivers",
        "price": 1750.00,
        "badge": "12V Li-Ion",
        "description": "Compact and lightweight 12V lithium-ion cordless drill driver with 20Nm torque, 15+1 torque stage clutch, 0.8-10mm keyless chuck, integrated LED light, and ergonomic rubber handle.",
        "specs": {
            "Model Number": "CDLI 12456",
            "Voltage": "12V",
            "Max Torque": "20 Nm",
            "No-Load Speed": "0 - 750 RPM",
            "Chuck Capacity": "0.8 - 10 mm Keyless",
            "Torque Settings": "15 + 1 Stages"
        }
    },
    {
        "sku": "CDLI 12206",
        "name": "INGCO 12V Cordless Drill with 2-Speed Gearbox (CDLI 12206)",
        "category_id": "cat_ingco_cordless",
        "subcategory": "Cordless Drills & Screwdrivers",
        "price": 1950.00,
        "badge": "2-Speed Transmission",
        "description": "Versatile 12V cordless drill featuring a mechanical 2-speed gearbox (0-400 / 0-1500 RPM), 20Nm maximum torque, 10mm chuck, and rapid battery charging system.",
        "specs": {
            "Model Number": "CDLI 12206",
            "Voltage": "12V",
            "Max Torque": "20 Nm",
            "No-Load Speed": "0-400 / 0-1500 RPM (2-Speed)",
            "Chuck Capacity": "0.8 - 10 mm Keyless Chuck",
            "Torque Settings": "15 + 1 Position"
        }
    },
    {
        "sku": "CIDLI 12206",
        "name": "INGCO 12V Cordless Impact Drill (CIDLI 12206)",
        "category_id": "cat_ingco_cordless",
        "subcategory": "Cordless Drills & Screwdrivers",
        "price": 2350.00,
        "badge": "12V Impact Action",
        "description": "Multi-mode 12V cordless impact drill with hammer drilling capability for light concrete and brick, 20Nm torque, 2-speed control, and built-in LED workspace illumination.",
        "specs": {
            "Model Number": "CIDLI 12206",
            "Voltage": "12V",
            "Function": "Drilling, Screwdriving, Impact Drilling",
            "Max Torque": "20 Nm",
            "No-Load Speed": "0-400 / 0-1500 RPM",
            "Impact Rate": "0 - 22,500 BPM"
        }
    },
    {
        "sku": "CDLI 1218",
        "name": "INGCO 12V Compact Cordless Drill (CDLI 1218)",
        "category_id": "cat_ingco_cordless",
        "subcategory": "Cordless Drills & Screwdrivers",
        "price": 1650.00,
        "badge": "Ultra Compact",
        "description": "Ergonomic 12V cordless drill driver engineered for home improvement, cabinet installation, and light electrical maintenance. Includes high-performance 12V battery and charger.",
        "specs": {
            "Model Number": "CDLI 1218",
            "Voltage": "12V",
            "Max Torque": "18 Nm",
            "No-Load Speed": "0 - 700 RPM",
            "Chuck Capacity": "10 mm Keyless",
            "Torque Settings": "15 + 1"
        }
    },
    {
        "sku": "CSDLI 0442",
        "name": "INGCO 4V Cordless Screwdriver USB-C (CSDLI 0442)",
        "category_id": "cat_ingco_cordless",
        "subcategory": "Cordless Drills & Screwdrivers",
        "price": 850.00,
        "badge": "USB Rechargeable",
        "description": "Compact 4V lithium-ion cordless screwdriver with modern USB-C charging port, 4Nm torque, 240 RPM speed, forward/reverse rocker switch, built-in LED front flashlight, and accessory screwdriver bits.",
        "specs": {
            "Model Number": "CSDLI 0442",
            "Voltage": "4V",
            "Max Torque": "4 Nm",
            "No-Load Speed": "240 RPM",
            "Charging Port": "Type-C USB Port (Fast Charging)",
            "Features": "Worklight, Battery Indicator, Cr-V Bits Included"
        }
    },

    # --- ELECTRIC POWER TOOLS ---
    {
        "sku": "ID7118",
        "name": "INGCO 710W Impact Drill 13mm (ID7118)",
        "category_id": "cat_ingco_electric",
        "subcategory": "Electric Drills & Impact Drills",
        "price": 1650.00,
        "badge": "710W Motor",
        "description": "Powerful 710W corded electric impact hammer drill with 13mm keyed chuck, variable speed control dial (0-3000 RPM), forward/reverse selector, depth gauge rod, and auxiliary 360° side handle.",
        "specs": {
            "Model Number": "ID7118",
            "Input Power": "710W",
            "Voltage": "220-240V ~ 50/60Hz",
            "No-Load Speed": "0 - 3000 RPM (Variable Speed)",
            "Chuck Capacity": "1.5 - 13 mm Keyed Chuck",
            "Max Drilling Capacity": "Steel: 13mm, Concrete: 13mm, Wood: 30mm"
        }
    },
    {
        "sku": "ED50028",
        "name": "INGCO 500W Electric Drill 10mm (ED50028)",
        "category_id": "cat_ingco_electric",
        "subcategory": "Electric Drills & Impact Drills",
        "price": 1250.00,
        "badge": "500W Motor",
        "description": "Durable 500W corded electric drill machine with 10mm keyless chuck, smooth variable speed trigger (0-3300 RPM), lock-on button for continuous drilling, and belt clip.",
        "specs": {
            "Model Number": "ED50028",
            "Input Power": "500W",
            "Voltage": "220-240V ~ 50/60Hz",
            "No-Load Speed": "0 - 3300 RPM",
            "Chuck Capacity": "1.0 - 10 mm Keyless",
            "Drilling Capacity": "Steel: 10mm, Wood: 25mm"
        }
    },
    {
        "sku": "HG200078",
        "name": "INGCO 2000W Electric Heat Gun (HG200078)",
        "category_id": "cat_ingco_electric",
        "subcategory": "Electric Heat Guns",
        "price": 1150.00,
        "badge": "2000W Dual Temp",
        "description": "Heavy duty 2000W industrial electric heat gun with dual temperature settings (350°C / 550°C) and airflow stages (300 / 500 L/min). Ideal for heat-shrink tubing, plastic welding, and paint removal.",
        "specs": {
            "Model Number": "HG200078",
            "Input Power": "2000W",
            "Voltage": "220-240V ~ 50/60Hz",
            "Temperature Stages": "Stage 1: 350°C, Stage 2: 550°C",
            "Airflow": "Stage 1: 300 L/min, Stage 2: 500 L/min",
            "Included Accessories": "Reducer Nozzle, Scraper"
        }
    }
]

print(f"Prepared {len(products)} products for insertion.")

# 5. Insert / Update verified products into Database
for p in products:
    sku = p["sku"]
    # Look up image in uploaded images dictionary
    img_url = images.get(sku) or images.get(sku.replace(" ", "")) or images.get(sku.split(" / ")[0])
    if not img_url:
        print(f"Warning: No Cloudinary image found for {sku}!")
        continue
    
    prod_id = "prod_ingco_" + sku.replace(" ", "_").replace("/", "_").lower()
    specs_json = json.dumps(p["specs"], ensure_ascii=False)
    
    cursor.execute("SELECT id FROM products WHERE id = %s OR sku = %s", (prod_id, sku))
    row = cursor.fetchone()
    if not row:
        cursor.execute("""
            INSERT INTO products (
                id, sku, name, brand_id, brand, category_id, subcategory,
                price, badge, in_stock, image, description, specs, rating, reviews, created_at, updated_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 1, %s, %s, %s, 4.8, 25, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
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

# 6. Verify count of INGCO products in DB
cursor.execute("SELECT COUNT(*) as cnt FROM products WHERE brand_id = %s", (brand_id,))
total_db_ingco = cursor.fetchone()["cnt"]
print(f"\n--- SUCCESS: Total INGCO products in PostgreSQL: {total_db_ingco} ---")

# 7. Sync to local SQLite tarang.db
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
print("Total INGCO products in SQLite tarang.db:", sq_cur.execute("SELECT COUNT(*) FROM products WHERE brand_id = 'brand_ingco'").fetchone()[0])
sq_conn.close()
conn.close()
