"""
TARANG RADIOS - Backend REST API Server & Static Asset Server
Powered by Python 3 native standard libraries (http.server, sqlite3, hashlib, json, urllib).
Features strict separation between Normal Catalog and 'The Brands We Deal With'.
"""

import http.server
import socketserver
import json
import os
import sys
import uuid
import hashlib
import secrets
import urllib.parse
from datetime import datetime, timedelta

from db import get_db, get_status as get_db_status
from migrate import run_all_migrations
import cloudinary_service

PORT = int(os.environ.get("PORT", 8000))
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploads")
STATIC_DIR = os.path.dirname(__file__)

os.makedirs(UPLOAD_DIR, exist_ok=True)

# ---------------------------------------------------------------------------
# Password & Hash Helpers
# ---------------------------------------------------------------------------
def hash_password(password: str, salt: str = None) -> tuple[str, str]:
    if not salt:
        salt = secrets.token_hex(16)
    pwd_hash = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt.encode('utf-8'),
        100000
    ).hex()
    return pwd_hash, salt

def verify_password(password: str, pwd_hash: str, salt: str) -> bool:
    new_hash, _ = hash_password(password, salt)
    return secrets.compare_digest(new_hash, pwd_hash)


# ---------------------------------------------------------------------------
# Authentication Session Validation
# ---------------------------------------------------------------------------
def authenticate_request(headers):
    auth_header = headers.get("Authorization", "")
    token = None
    if auth_header.startswith("Bearer "):
        token = auth_header.split(" ", 1)[1].strip()
    elif "cookie" in headers:
        cookies = dict(item.strip().split("=", 1) for item in headers["cookie"].split(";") if "=" in item)
        token = cookies.get("tarang_admin_token")

    if not token:
        return None

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT s.token, s.expires_at, a.id, a.username, a.name
        FROM sessions s
        JOIN admins a ON s.admin_id = a.id
        WHERE s.token = ?
    """, (token,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return None

    if datetime.fromisoformat(row["expires_at"]) < datetime.now():
        return None

    return {
        "token": row["token"],
        "id": row["id"],
        "username": row["username"],
        "name": row["name"]
    }

# ---------------------------------------------------------------------------
# Request Handler
# ---------------------------------------------------------------------------
class TarangRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=STATIC_DIR, **kwargs)

    def send_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Requested-With")

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_cors_headers()
        self.end_headers()

    def send_json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_cors_headers()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def read_json_body(self):
        content_length = int(self.headers.get("Content-Length", 0))
        if content_length <= 0:
            return {}
        raw = self.rfile.read(content_length).decode("utf-8")
        try:
            return json.loads(raw)
        except Exception:
            return {}

    # -----------------------------------------------------------------------
    # GET Requests Routing
    # -----------------------------------------------------------------------
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        # Public Data
        if path == "/api/public-data":
            return self.handle_get_public_data()

        # System Status & Health Check
        if path == "/api/status":
            return self.send_json({
                "status": "online",
                "database": get_db_status(),
                "cloudinary": cloudinary_service.get_status(),
                "timestamp": datetime.now().isoformat()
            })

        # Auth
        if path == "/api/auth/me":
            user = authenticate_request(self.headers)
            if not user:
                return self.send_json({"error": "Unauthorized"}, 401)
            return self.send_json({"authenticated": True, "user": user})

        # Admin stats
        if path == "/api/admin/stats":
            if not authenticate_request(self.headers):
                return self.send_json({"error": "Unauthorized"}, 401)
            return self.handle_get_admin_stats()

        # Brands endpoints
        if path == "/api/brands":
            all_brands = query.get("all", ["0"])[0] == "1"
            return self.handle_get_brands(all_brands)

        # Dedicated Brands Hierarchy Tree
        if path == "/api/brands/hierarchy":
            brand_id = query.get("brand_id", [None])[0]
            return self.handle_get_brands_hierarchy(brand_id)

        # Categories list (can filter normal vs brand-specific)
        if path == "/api/categories":
            brand_id = query.get("brand_id", [None])[0]
            cat_type = query.get("type", [None])[0]
            return self.handle_get_categories(brand_id, cat_type)

        # Subcategories list
        if path == "/api/subcategories":
            cat_id = query.get("category_id", [None])[0]
            cat_type = query.get("type", [None])[0]
            return self.handle_get_subcategories(cat_id, cat_type)

        # Products list
        if path == "/api/products":
            return self.handle_get_products(query)

        # CSV Template
        if path == "/api/export/csv-template":
            return self.handle_csv_template_download()

        # Fallback to static files
        return super().do_GET()

    # -----------------------------------------------------------------------
    # POST Requests Routing
    # -----------------------------------------------------------------------
    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        # Login / Logout
        if path == "/api/auth/login":
            return self.handle_auth_login()
        if path == "/api/auth/logout":
            return self.handle_auth_logout()

        user = authenticate_request(self.headers)
        if not user:
            return self.send_json({"error": "Unauthorized."}, 401)

        # Password change
        if path == "/api/auth/change-password":
            return self.handle_change_password(user)

        # Brands Management
        if path == "/api/brands":
            return self.handle_create_brand()
        if path == "/api/brands/reorder":
            return self.handle_reorder_brands()
        if path.startswith("/api/brands/") and path.endswith("/toggle"):
            brand_id = path.split("/")[3]
            return self.handle_toggle_brand(brand_id)

        # Categories Management
        if path == "/api/categories":
            return self.handle_create_category()
        if path == "/api/categories/reorder":
            return self.handle_reorder_categories()

        # Subcategories Management
        if path == "/api/subcategories":
            return self.handle_create_subcategory()
        if path == "/api/subcategories/reorder":
            return self.handle_reorder_subcategories()

        # Products Management
        if path == "/api/products":
            return self.handle_create_product()
        if path.startswith("/api/products/") and path.endswith("/duplicate"):
            prod_id = path.split("/")[3]
            return self.handle_duplicate_product(prod_id)

        # Quick Price Management
        if path == "/api/products/quick-price":
            return self.handle_quick_price_update()

        # Bulk Upload & Import
        if path == "/api/upload/images":
            return self.handle_bulk_image_upload()
        if path == "/api/import/bulk-products":
            return self.handle_bulk_product_import()

        self.send_json({"error": "Not Found"}, 404)

    # -----------------------------------------------------------------------
    # PUT Requests Routing
    # -----------------------------------------------------------------------
    def do_PUT(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if not authenticate_request(self.headers):
            return self.send_json({"error": "Unauthorized"}, 401)

        if path.startswith("/api/brands/"):
            brand_id = path.split("/")[3]
            return self.handle_update_brand(brand_id)

        if path.startswith("/api/categories/"):
            cat_id = path.split("/")[3]
            return self.handle_update_category(cat_id)

        if path.startswith("/api/subcategories/"):
            sub_id = path.split("/")[3]
            return self.handle_update_subcategory(sub_id)

        if path.startswith("/api/products/"):
            prod_id = path.split("/")[3]
            return self.handle_update_product(prod_id)

        self.send_json({"error": "Not Found"}, 404)

    # -----------------------------------------------------------------------
    # DELETE Requests Routing
    # -----------------------------------------------------------------------
    def do_DELETE(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if not authenticate_request(self.headers):
            return self.send_json({"error": "Unauthorized"}, 401)

        if path.startswith("/api/brands/"):
            brand_id = path.split("/")[3]
            return self.handle_delete_brand(brand_id)

        if path.startswith("/api/categories/"):
            cat_id = path.split("/")[3]
            return self.handle_delete_category(cat_id)

        if path.startswith("/api/subcategories/"):
            sub_id = path.split("/")[3]
            return self.handle_delete_subcategory(sub_id)

        if path.startswith("/api/products/"):
            prod_id = path.split("/")[3]
            return self.handle_delete_product(prod_id)

        self.send_json({"error": "Not Found"}, 404)

    # -----------------------------------------------------------------------
    # PUBLIC CENTRALIZED CATALOG DATA
    # -----------------------------------------------------------------------
    def handle_get_public_data(self):
        conn = get_db()
        cursor = conn.cursor()

        # Enabled Brands (Only name, ordered by display_order)
        cursor.execute("SELECT id, name FROM brands WHERE is_enabled = 1 ORDER BY display_order ASC, name ASC")
        brands = [{"id": b["id"], "name": b["name"]} for b in cursor.fetchall()]

        # Normal Categories (for main category grid & filter chips)
        cursor.execute("""
            SELECT c.* FROM categories c
            WHERE c.brand_id IS NULL OR c.brand_id = ''
            ORDER BY c.display_order ASC, c.title ASC
        """)
        cat_rows = cursor.fetchall()

        # Brand-specific Categories
        cursor.execute("""
            SELECT c.*, b.name as brand_name FROM categories c
            JOIN brands b ON c.brand_id = b.id
            WHERE b.is_enabled = 1
            ORDER BY b.display_order ASC, c.display_order ASC, c.title ASC
        """)
        brand_cat_rows = cursor.fetchall()

        # Subcategories
        cursor.execute("SELECT * FROM subcategories ORDER BY display_order ASC, name ASC")
        sub_rows = cursor.fetchall()

        sub_map = {}
        for s in sub_rows:
            cid = s["category_id"]
            if cid not in sub_map:
                sub_map[cid] = []
            sub_map[cid].append(s["name"])

        categories = []
        for c in cat_rows:
            categories.append({
                "id": c["id"],
                "title": c["title"],
                "shortTitle": c["short_title"] or c["title"],
                "tagline": c["tagline"] or "",
                "icon": c["icon"] or "layers",
                "image": c["image"] or "",
                "color": c["color"] or "#D14B14",
                "subcategories": sub_map.get(c["id"], [])
            })

        brand_categories = []
        for c in brand_cat_rows:
            brand_categories.append({
                "id": c["id"],
                "brandId": c["brand_id"],
                "brandName": c["brand_name"],
                "title": c["title"],
                "shortTitle": c["short_title"] or c["title"],
                "tagline": c["tagline"] or "",
                "icon": c["icon"] or "layers",
                "image": c["image"] or "",
                "color": c["color"] or "#D14B14",
                "subcategories": sub_map.get(c["id"], [])
            })

        # All Active Products (Normal + Brand Products)
        cursor.execute("""
            SELECT p.*, b.name as brand_name_resolved, c.title as category_title
            FROM products p
            LEFT JOIN brands b ON p.brand_id = b.id
            LEFT JOIN categories c ON p.category_id = c.id
            WHERE (p.brand_id IS NULL OR b.is_enabled = 1)
            ORDER BY p.created_at DESC
        """)
        prod_rows = cursor.fetchall()
        products = []
        for p in prod_rows:
            specs = {}
            if p["specs"]:
                try: specs = json.loads(p["specs"])
                except Exception: specs = {}

            brand_name = p["brand_name_resolved"] or p["brand"] or ""
            products.append({
                "id": p["id"],
                "sku": p["sku"] or "",
                "name": p["name"],
                "brandId": p["brand_id"] or "",
                "brand": brand_name,
                "categoryId": p["category_id"],
                "categoryTitle": p["category_title"] or "",
                "subcategory": p["subcategory"] or "",
                "price": float(p["price"]),
                "badge": p["badge"] or "",
                "inStock": bool(p["in_stock"]),
                "image": p["image"] or "",
                "description": p["description"] or "",
                "specs": specs,
                "rating": float(p["rating"] or 5.0),
                "reviews": int(p["reviews"] or 0)
            })

        conn.close()
        return self.send_json({
            "brands": brands,
            "categories": categories,
            "brandCategories": brand_categories,
            "products": products
        })

    # -----------------------------------------------------------------------
    # ADMIN DASHBOARD STATS
    # -----------------------------------------------------------------------
    def handle_get_admin_stats(self):
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM brands")
        total_brands = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM categories WHERE brand_id IS NULL OR brand_id = ''")
        total_normal_cats = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM categories WHERE brand_id IS NOT NULL AND brand_id != ''")
        total_brand_cats = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM subcategories")
        total_subs = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*), SUM(CASE WHEN in_stock = 1 THEN 1 ELSE 0 END), AVG(price) FROM products")
        row = cursor.fetchone()
        total_prods = row[0] or 0
        in_stock_prods = row[1] or 0
        avg_price = round(row[2] or 0, 2)

        cursor.execute("""
            SELECT p.id, p.sku, p.name, p.price, p.subcategory, p.in_stock, p.image, COALESCE(b.name, p.brand, '') as brand_name
            FROM products p
            LEFT JOIN brands b ON p.brand_id = b.id
            ORDER BY p.created_at DESC LIMIT 6
        """)
        recent = [dict(r) for r in cursor.fetchall()]

        conn.close()
        return self.send_json({
            "totalBrands": total_brands,
            "totalNormalCategories": total_normal_cats,
            "totalBrandCategories": total_brand_cats,
            "totalCategories": total_normal_cats + total_brand_cats,
            "totalSubcategories": total_subs,
            "totalProducts": total_prods,
            "inStockProducts": in_stock_prods,
            "outOfStockProducts": total_prods - in_stock_prods,
            "avgPrice": avg_price,
            "recentProducts": recent
        })

    # -----------------------------------------------------------------------
    # 'THE BRANDS WE DEAL WITH' CRUD & HIERARCHY
    # -----------------------------------------------------------------------
    def handle_get_brands(self, all_brands=False):
        conn = get_db()
        cursor = conn.cursor()
        sql = """
            SELECT b.*,
            (SELECT COUNT(*) FROM categories c WHERE c.brand_id = b.id) as category_count,
            (SELECT COUNT(*) FROM products p WHERE p.brand_id = b.id) as product_count
            FROM brands b
        """
        if not all_brands:
            sql += " WHERE b.is_enabled = 1"
        sql += " ORDER BY b.display_order ASC, b.name ASC"

        cursor.execute(sql)
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return self.send_json(rows)

    def handle_create_brand(self):
        data = self.read_json_body()
        name = (data.get("name") or "").strip()
        if not name:
            return self.send_json({"error": "Brand name is required"}, 400)

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM brands WHERE LOWER(name) = LOWER(?)", (name,))
        if cursor.fetchone():
            conn.close()
            return self.send_json({"error": f"Brand '{name}' already exists"}, 400)

        brand_id = data.get("id") or f"brand_{uuid.uuid4().hex[:8]}"
        display_order = int(data.get("displayOrder") or 0)
        is_enabled = 1 if data.get("isEnabled", True) else 0
        now = datetime.now().isoformat()

        cursor.execute("""
            INSERT INTO brands (id, name, display_order, is_enabled, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (brand_id, name, display_order, is_enabled, now, now))
        conn.commit()
        conn.close()

        return self.send_json({"success": True, "id": brand_id, "name": name, "message": f"Brand '{name}' added successfully"}, 201)

    def handle_update_brand(self, brand_id):
        data = self.read_json_body()
        name = (data.get("name") or "").strip()
        if not name:
            return self.send_json({"error": "Brand name is required"}, 400)

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM brands WHERE id = ?", (brand_id,))
        old_brand = cursor.fetchone()
        if not old_brand:
            conn.close()
            return self.send_json({"error": "Brand not found"}, 404)

        old_name = old_brand["name"]
        display_order = int(data.get("displayOrder") or 0)
        is_enabled = 1 if data.get("isEnabled", True) else 0
        now = datetime.now().isoformat()

        cursor.execute("""
            UPDATE brands
            SET name = ?, display_order = ?, is_enabled = ?, updated_at = ?
            WHERE id = ?
        """, (name, display_order, is_enabled, now, brand_id))

        if old_name != name:
            cursor.execute("UPDATE products SET brand = ? WHERE brand_id = ?", (name, brand_id))

        conn.commit()
        conn.close()
        return self.send_json({"success": True, "message": f"Brand '{name}' updated successfully"})

    def handle_delete_brand(self, brand_id):
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM brands WHERE id = ?", (brand_id,))
        brand = cursor.fetchone()
        if not brand:
            conn.close()
            return self.send_json({"error": "Brand not found"}, 404)

        # Cascade delete brand categories, subcategories, products
        cursor.execute("SELECT id FROM categories WHERE brand_id = ?", (brand_id,))
        cat_ids = [r["id"] for r in cursor.fetchall()]
        for cid in cat_ids:
            cursor.execute("DELETE FROM subcategories WHERE category_id = ?", (cid,))
        
        cursor.execute("DELETE FROM products WHERE brand_id = ?", (brand_id,))
        cursor.execute("DELETE FROM categories WHERE brand_id = ?", (brand_id,))
        cursor.execute("DELETE FROM brands WHERE id = ?", (brand_id,))
        conn.commit()
        conn.close()
        return self.send_json({"success": True, "message": f"Brand '{brand['name']}' and its catalog deleted."})

    def handle_toggle_brand(self, brand_id):
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT is_enabled, name FROM brands WHERE id = ?", (brand_id,))
        brand = cursor.fetchone()
        if not brand:
            conn.close()
            return self.send_json({"error": "Brand not found"}, 404)

        new_status = 0 if brand["is_enabled"] == 1 else 1
        now = datetime.now().isoformat()
        cursor.execute("UPDATE brands SET is_enabled = ?, updated_at = ? WHERE id = ?", (new_status, now, brand_id))
        conn.commit()
        conn.close()
        status_text = "Enabled" if new_status == 1 else "Disabled"
        return self.send_json({"success": True, "isEnabled": new_status, "message": f"Brand '{brand['name']}' {status_text}."})

    def handle_reorder_brands(self):
        data = self.read_json_body()
        order_list = data.get("order", [])
        conn = get_db()
        cursor = conn.cursor()
        for idx, bid in enumerate(order_list):
            cursor.execute("UPDATE brands SET display_order = ? WHERE id = ?", (idx, bid))
        conn.commit()
        conn.close()
        return self.send_json({"success": True, "message": "Brands reordered successfully."})

    def handle_get_brands_hierarchy(self, target_brand_id=None):
        conn = get_db()
        cursor = conn.cursor()

        if target_brand_id:
            cursor.execute("SELECT * FROM brands WHERE id = ?", (target_brand_id,))
        else:
            cursor.execute("SELECT * FROM brands ORDER BY display_order ASC, name ASC")
        brands = [dict(b) for b in cursor.fetchall()]

        cursor.execute("SELECT * FROM categories WHERE brand_id IS NOT NULL ORDER BY display_order ASC, title ASC")
        categories = [dict(c) for c in cursor.fetchall()]

        cursor.execute("SELECT * FROM subcategories ORDER BY display_order ASC, name ASC")
        subcategories = [dict(s) for s in cursor.fetchall()]

        cursor.execute("SELECT id, name, sku, price, brand_id, category_id, subcategory, in_stock, image, description FROM products WHERE brand_id IS NOT NULL ORDER BY name ASC")
        products = [dict(p) for p in cursor.fetchall()]

        conn.close()

        tree = []
        for b in brands:
            b_node = {
                "id": b["id"],
                "name": b["name"],
                "displayOrder": b["display_order"],
                "isEnabled": bool(b["is_enabled"]),
                "categories": []
            }

            b_cats = [c for c in categories if c.get("brand_id") == b["id"]]
            for c in b_cats:
                c_node = {
                    "id": c["id"],
                    "title": c["title"],
                    "shortTitle": c["short_title"],
                    "tagline": c["tagline"],
                    "color": c["color"],
                    "image": c["image"],
                    "subcategories": []
                }

                c_subs = [s for s in subcategories if s["category_id"] == c["id"]]
                for s in c_subs:
                    s_prods = [p for p in products if p["category_id"] == c["id"] and p["subcategory"] == s["name"]]
                    s_node = {
                        "id": s["id"],
                        "name": s["name"],
                        "productsCount": len(s_prods),
                        "products": s_prods
                    }
                    c_node["subcategories"].append(s_node)

                direct_prods = [p for p in products if p["category_id"] == c["id"] and not p.get("subcategory")]
                if direct_prods:
                    c_node["subcategories"].append({
                        "id": f"sub_{c['id']}_general",
                        "name": "General",
                        "productsCount": len(direct_prods),
                        "products": direct_prods
                    })

                b_node["categories"].append(c_node)

            tree.append(b_node)

        return self.send_json(tree)

    # -----------------------------------------------------------------------
    # CATEGORIES CRUD (Normal vs Brand)
    # -----------------------------------------------------------------------
    def handle_get_categories(self, brand_id=None, cat_type=None):
        conn = get_db()
        cursor = conn.cursor()

        if cat_type == "normal" or brand_id == "normal" or brand_id == "none":
            # Normal categories only
            cursor.execute("""
                SELECT c.*,
                (SELECT COUNT(*) FROM subcategories s WHERE s.category_id = c.id) as subcategory_count,
                (SELECT COUNT(*) FROM products p WHERE p.category_id = c.id) as product_count
                FROM categories c
                WHERE c.brand_id IS NULL OR c.brand_id = ''
                ORDER BY c.display_order ASC, c.title ASC
            """)
        elif brand_id and brand_id != "all":
            # Specific brand categories
            cursor.execute("""
                SELECT c.*, b.name as brand_name,
                (SELECT COUNT(*) FROM subcategories s WHERE s.category_id = c.id) as subcategory_count,
                (SELECT COUNT(*) FROM products p WHERE p.category_id = c.id) as product_count
                FROM categories c
                LEFT JOIN brands b ON c.brand_id = b.id
                WHERE c.brand_id = ?
                ORDER BY c.display_order ASC, c.title ASC
            """, (brand_id,))
        else:
            cursor.execute("""
                SELECT c.*, b.name as brand_name,
                (SELECT COUNT(*) FROM subcategories s WHERE s.category_id = c.id) as subcategory_count,
                (SELECT COUNT(*) FROM products p WHERE p.category_id = c.id) as product_count
                FROM categories c
                LEFT JOIN brands b ON c.brand_id = b.id
                ORDER BY c.display_order ASC, c.title ASC
            """)

        cats = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return self.send_json(cats)

    def handle_create_category(self):
        data = self.read_json_body()
        title = (data.get("title") or "").strip()
        if not title:
            return self.send_json({"error": "Category title is required"}, 400)

        cat_id = data.get("id") or title.lower().replace(" ", "-").replace("&", "and")
        cat_id = "".join(c for c in cat_id if c.isalnum() or c in "-_")

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM categories WHERE id = ?", (cat_id,))
        if cursor.fetchone():
            cat_id = f"{cat_id}-{uuid.uuid4().hex[:6]}"

        brand_id = data.get("brandId") or data.get("brand_id") or None
        if brand_id in ["", "none", "null", "normal"]:
            brand_id = None

        short_title = data.get("shortTitle") or title
        tagline = data.get("tagline") or ""
        icon = data.get("icon") or "layers"
        image = data.get("image") or ""
        color = data.get("color") or "#D14B14"
        display_order = int(data.get("displayOrder") or 0)
        now = datetime.now().isoformat()

        cursor.execute("""
            INSERT INTO categories (id, brand_id, title, short_title, tagline, icon, image, color, display_order, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (cat_id, brand_id, title, short_title, tagline, icon, image, color, display_order, now, now))

        if "subcategories" in data and isinstance(data["subcategories"], list):
            for i, sub_name in enumerate(data["subcategories"]):
                if sub_name.strip():
                    sub_id = f"sub_{cat_id}_{uuid.uuid4().hex[:6]}"
                    cursor.execute("""
                        INSERT INTO subcategories (id, category_id, name, display_order)
                        VALUES (?, ?, ?, ?)
                    """, (sub_id, cat_id, sub_name.strip(), i))

        conn.commit()
        conn.close()
        return self.send_json({"success": True, "id": cat_id, "message": f"Category '{title}' created successfully"}, 201)

    def handle_update_category(self, cat_id):
        data = self.read_json_body()
        title = (data.get("title") or "").strip()
        if not title:
            return self.send_json({"error": "Category title is required"}, 400)

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id, brand_id FROM categories WHERE id = ?", (cat_id,))
        cat_row = cursor.fetchone()
        if not cat_row:
            conn.close()
            return self.send_json({"error": "Category not found"}, 404)

        # Retain existing brand_id unless explicitly updated
        brand_id = data.get("brandId", data.get("brand_id", cat_row["brand_id"]))
        if brand_id in ["", "none", "null", "normal"]:
            brand_id = None

        short_title = data.get("shortTitle") or title
        tagline = data.get("tagline") or ""
        icon = data.get("icon") or "layers"
        image = data.get("image") or ""
        color = data.get("color") or "#D14B14"
        display_order = int(data.get("displayOrder") or 0)
        now = datetime.now().isoformat()

        cursor.execute("""
            UPDATE categories 
            SET brand_id = ?, title = ?, short_title = ?, tagline = ?, icon = ?, image = ?, color = ?, display_order = ?, updated_at = ?
            WHERE id = ?
        """, (brand_id, title, short_title, tagline, icon, image, color, display_order, now, cat_id))

        if brand_id:
            cursor.execute("SELECT name FROM brands WHERE id = ?", (brand_id,))
            b_row = cursor.fetchone()
            if b_row:
                cursor.execute("UPDATE products SET brand_id = ?, brand = ? WHERE category_id = ?", (brand_id, b_row["name"], cat_id))
        else:
            cursor.execute("UPDATE products SET brand_id = NULL, brand = NULL WHERE category_id = ?", (cat_id,))

        conn.commit()
        conn.close()
        return self.send_json({"success": True, "message": f"Category '{title}' updated successfully"})

    def handle_delete_category(self, cat_id):
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM categories WHERE id = ?", (cat_id,))
        cursor.execute("DELETE FROM subcategories WHERE category_id = ?", (cat_id,))
        cursor.execute("DELETE FROM products WHERE category_id = ?", (cat_id,))
        conn.commit()
        conn.close()
        return self.send_json({"success": True, "message": "Category and all associated items deleted"})

    def handle_reorder_categories(self):
        data = self.read_json_body()
        order_list = data.get("order", [])
        conn = get_db()
        cursor = conn.cursor()
        for idx, cid in enumerate(order_list):
            cursor.execute("UPDATE categories SET display_order = ? WHERE id = ?", (idx, cid))
        conn.commit()
        conn.close()
        return self.send_json({"success": True, "message": "Categories reordered"})

    # -----------------------------------------------------------------------
    # SUBCATEGORIES CRUD
    # -----------------------------------------------------------------------
    def handle_get_subcategories(self, category_id=None, cat_type=None):
        conn = get_db()
        cursor = conn.cursor()

        if category_id and category_id != "all":
            cursor.execute("""
                SELECT s.*, c.title as category_title, c.brand_id, b.name as brand_name,
                (SELECT COUNT(*) FROM products p WHERE p.subcategory = s.name AND p.category_id = s.category_id) as product_count
                FROM subcategories s
                JOIN categories c ON s.category_id = c.id
                LEFT JOIN brands b ON c.brand_id = b.id
                WHERE s.category_id = ?
                ORDER BY s.display_order ASC, s.name ASC
            """, (category_id,))
        elif cat_type == "normal":
            cursor.execute("""
                SELECT s.*, c.title as category_title, c.brand_id, NULL as brand_name,
                (SELECT COUNT(*) FROM products p WHERE p.subcategory = s.name AND p.category_id = s.category_id) as product_count
                FROM subcategories s
                JOIN categories c ON s.category_id = c.id
                WHERE c.brand_id IS NULL OR c.brand_id = ''
                ORDER BY c.display_order ASC, s.display_order ASC, s.name ASC
            """)
        else:
            cursor.execute("""
                SELECT s.*, c.title as category_title, c.brand_id, b.name as brand_name,
                (SELECT COUNT(*) FROM products p WHERE p.subcategory = s.name AND p.category_id = s.category_id) as product_count
                FROM subcategories s
                JOIN categories c ON s.category_id = c.id
                LEFT JOIN brands b ON c.brand_id = b.id
                ORDER BY c.title ASC, s.display_order ASC, s.name ASC
            """)

        subs = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return self.send_json(subs)

    def handle_create_subcategory(self):
        data = self.read_json_body()
        name = (data.get("name") or "").strip()
        category_id = (data.get("categoryId") or "").strip()

        if not name or not category_id:
            return self.send_json({"error": "Subcategory name and parent Category are required"}, 400)

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM categories WHERE id = ?", (category_id,))
        if not cursor.fetchone():
            conn.close()
            return self.send_json({"error": "Parent category does not exist"}, 400)

        sub_id = data.get("id") or f"sub_{uuid.uuid4().hex[:8]}"
        display_order = int(data.get("displayOrder") or 0)

        cursor.execute("""
            INSERT INTO subcategories (id, category_id, name, display_order)
            VALUES (?, ?, ?, ?)
        """, (sub_id, category_id, name, display_order))
        conn.commit()
        conn.close()
        return self.send_json({"success": True, "id": sub_id, "message": f"Subcategory '{name}' created successfully"}, 201)

    def handle_update_subcategory(self, sub_id):
        data = self.read_json_body()
        name = (data.get("name") or "").strip()
        category_id = (data.get("categoryId") or "").strip()

        if not name or not category_id:
            return self.send_json({"error": "Subcategory name and parent Category are required"}, 400)

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT name, category_id FROM subcategories WHERE id = ?", (sub_id,))
        old_sub = cursor.fetchone()
        if not old_sub:
            conn.close()
            return self.send_json({"error": "Subcategory not found"}, 404)

        old_name = old_sub["name"]
        old_cid = old_sub["category_id"]
        display_order = int(data.get("displayOrder") or 0)

        cursor.execute("""
            UPDATE subcategories 
            SET name = ?, category_id = ?, display_order = ?
            WHERE id = ?
        """, (name, category_id, display_order, sub_id))

        if old_name != name or old_cid != category_id:
            cursor.execute("""
                UPDATE products
                SET subcategory = ?, category_id = ?
                WHERE subcategory = ? AND category_id = ?
            """, (name, category_id, old_name, old_cid))

        conn.commit()
        conn.close()
        return self.send_json({"success": True, "message": f"Subcategory '{name}' updated successfully"})

    def handle_delete_subcategory(self, sub_id):
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM subcategories WHERE id = ?", (sub_id,))
        conn.commit()
        conn.close()
        return self.send_json({"success": True, "message": "Subcategory deleted successfully"})

    def handle_reorder_subcategories(self):
        data = self.read_json_body()
        order_list = data.get("order", [])
        conn = get_db()
        cursor = conn.cursor()
        for idx, sid in enumerate(order_list):
            cursor.execute("UPDATE subcategories SET display_order = ? WHERE id = ?", (idx, sid))
        conn.commit()
        conn.close()
        return self.send_json({"success": True, "message": "Subcategories reordered"})

    # -----------------------------------------------------------------------
    # PRODUCTS CRUD
    # -----------------------------------------------------------------------
    def handle_get_products(self, query):
        brand_id = query.get("brand_id", [None])[0]
        cat_id = query.get("category_id", [None])[0]
        subcat = query.get("subcategory", [None])[0]
        search = query.get("q", [None])[0]
        sort = query.get("sort", ["date_desc"])[0]
        catalog_type = query.get("type", [None])[0]

        sql = """
            SELECT p.*, c.title as category_title, b.name as brand_name
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.id
            LEFT JOIN brands b ON p.brand_id = b.id
            WHERE 1=1
        """
        params = []

        if catalog_type == "normal" or brand_id == "normal" or brand_id == "none":
            sql += " AND (p.brand_id IS NULL OR p.brand_id = '')"
        elif brand_id and brand_id != "all":
            sql += " AND p.brand_id = ?"
            params.append(brand_id)

        if cat_id and cat_id != "all":
            sql += " AND p.category_id = ?"
            params.append(cat_id)

        if subcat and subcat != "all":
            sql += " AND p.subcategory = ?"
            params.append(subcat)

        if search:
            search_param = f"%{search}%"
            sql += " AND (p.name LIKE ? OR p.sku LIKE ? OR p.brand LIKE ? OR p.description LIKE ?)"
            params.extend([search_param, search_param, search_param, search_param])

        if sort == "price_asc":
            sql += " ORDER BY p.price ASC"
        elif sort == "price_desc":
            sql += " ORDER BY p.price DESC"
        elif sort == "name_asc":
            sql += " ORDER BY p.name ASC"
        elif sort == "name_desc":
            sql += " ORDER BY p.name DESC"
        else:
            sql += " ORDER BY p.created_at DESC"

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(sql, params)
        rows = cursor.fetchall()
        conn.close()

        products = []
        for r in rows:
            d = dict(r)
            if d.get("specs"):
                try: d["specs"] = json.loads(d["specs"])
                except Exception: d["specs"] = {}
            products.append(d)

        return self.send_json(products)

    def handle_create_product(self):
        data = self.read_json_body()
        name = (data.get("name") or "").strip()
        category_id = (data.get("categoryId") or "").strip()
        price_val = data.get("price", 0)

        if not name:
            return self.send_json({"error": "Product name is required"}, 400)
        if not category_id:
            return self.send_json({"error": "Category is required"}, 400)

        try:
            price = float(price_val)
        except ValueError:
            return self.send_json({"error": "Price must be a valid number"}, 400)

        brand_id = data.get("brandId") or data.get("brand_id") or None
        if brand_id in ["", "none", "null", "normal"]:
            brand_id = None

        brand_name = None
        if brand_id:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM brands WHERE id = ?", (brand_id,))
            b_row = cursor.fetchone()
            if b_row:
                brand_name = b_row["name"]
            conn.close()

        prod_id = data.get("id") or f"prod_{uuid.uuid4().hex[:8]}"
        sku = (data.get("sku") or f"TR-{uuid.uuid4().hex[:6].upper()}").strip()
        subcategory = (data.get("subcategory") or "").strip()
        badge = (data.get("badge") or "").strip()
        in_stock = 1 if data.get("inStock", True) else 0
        image = (data.get("image") or "").strip()
        description = (data.get("description") or "").strip()
        specs = data.get("specs", {})
        specs_json = json.dumps(specs) if isinstance(specs, dict) else "{}"
        rating = float(data.get("rating") or 5.0)
        reviews = int(data.get("reviews") or 0)
        now = datetime.now().isoformat()

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO products (id, sku, name, brand_id, brand, category_id, subcategory, price, badge, in_stock, image, description, specs, rating, reviews, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (prod_id, sku, name, brand_id, brand_name, category_id, subcategory, price, badge, in_stock, image, description, specs_json, rating, reviews, now, now))
        conn.commit()
        conn.close()

        return self.send_json({"success": True, "id": prod_id, "message": f"Product '{name}' created successfully"}, 201)

    def handle_update_product(self, prod_id):
        data = self.read_json_body()
        name = (data.get("name") or "").strip()
        category_id = (data.get("categoryId") or "").strip()
        price_val = data.get("price", 0)

        if not name or not category_id:
            return self.send_json({"error": "Product name and category are required"}, 400)

        try:
            price = float(price_val)
        except ValueError:
            return self.send_json({"error": "Price must be a valid number"}, 400)

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id, brand_id FROM products WHERE id = ?", (prod_id,))
        p_row = cursor.fetchone()
        if not p_row:
            conn.close()
            return self.send_json({"error": "Product not found"}, 404)

        brand_id = data.get("brandId", data.get("brand_id", p_row["brand_id"]))
        if brand_id in ["", "none", "null", "normal"]:
            brand_id = None

        brand_name = None
        if brand_id:
            cursor.execute("SELECT name FROM brands WHERE id = ?", (brand_id,))
            b_row = cursor.fetchone()
            if b_row:
                brand_name = b_row["name"]

        sku = (data.get("sku") or "").strip()
        subcategory = (data.get("subcategory") or "").strip()
        badge = (data.get("badge") or "").strip()
        in_stock = 1 if data.get("inStock", True) else 0
        image = (data.get("image") or "").strip()
        description = (data.get("description") or "").strip()
        specs = data.get("specs", {})
        specs_json = json.dumps(specs) if isinstance(specs, dict) else "{}"
        rating = float(data.get("rating") or 5.0)
        reviews = int(data.get("reviews") or 0)
        now = datetime.now().isoformat()

        cursor.execute("""
            UPDATE products
            SET sku = ?, name = ?, brand_id = ?, brand = ?, category_id = ?, subcategory = ?, price = ?, badge = ?, in_stock = ?, image = ?, description = ?, specs = ?, rating = ?, reviews = ?, updated_at = ?
            WHERE id = ?
        """, (sku, name, brand_id, brand_name, category_id, subcategory, price, badge, in_stock, image, description, specs_json, rating, reviews, now, prod_id))
        conn.commit()
        conn.close()

        return self.send_json({"success": True, "message": f"Product '{name}' updated successfully"})

    def handle_delete_product(self, prod_id):
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM products WHERE id = ?", (prod_id,))
        conn.commit()
        conn.close()
        return self.send_json({"success": True, "message": "Product deleted successfully"})

    def handle_duplicate_product(self, prod_id):
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM products WHERE id = ?", (prod_id,))
        original = cursor.fetchone()
        if not original:
            conn.close()
            return self.send_json({"error": "Product not found"}, 404)

        new_id = f"prod_{uuid.uuid4().hex[:8]}"
        new_sku = f"{original['sku'] or 'TR'}-COPY"
        new_name = f"{original['name']} (Copy)"
        now = datetime.now().isoformat()

        cursor.execute("""
            INSERT INTO products (id, sku, name, brand_id, brand, category_id, subcategory, price, badge, in_stock, image, description, specs, rating, reviews, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (new_id, new_sku, new_name, original["brand_id"], original["brand"], original["category_id"], original["subcategory"], original["price"], original["badge"], original["in_stock"], original["image"], original["description"], original["specs"], original["rating"], original["reviews"], now, now))
        conn.commit()
        conn.close()

        return self.send_json({"success": True, "id": new_id, "message": f"Product '{new_name}' created successfully"}, 201)

    def handle_quick_price_update(self):
        data = self.read_json_body()
        prod_id = data.get("id")
        price_val = data.get("price")

        if not prod_id:
            return self.send_json({"error": "Product ID is required"}, 400)

        try:
            price = float(price_val)
            if price < 0:
                raise ValueError()
        except (ValueError, TypeError):
            return self.send_json({"error": "Invalid price value."}, 400)

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM products WHERE id = ?", (prod_id,))
        prod = cursor.fetchone()
        if not prod:
            conn.close()
            return self.send_json({"error": "Product not found"}, 404)

        now = datetime.now().isoformat()
        cursor.execute("UPDATE products SET price = ?, updated_at = ? WHERE id = ?", (price, now, prod_id))
        conn.commit()
        conn.close()

        return self.send_json({
            "success": True,
            "id": prod_id,
            "name": prod["name"],
            "newPrice": price,
            "message": f"Price updated to ₹{price:,.2f} successfully."
        })

    def handle_csv_template_download(self):
        csv_content = (
            "Product Name,Price,Brand,Category,Subcategory,SKU,Availability,Image Filename,Description\n"
            "3.7V Li-ion Battery 2600mAh,180,,Batteries & Power Supplies,18650 Li-ion Cells & Battery Holders,TR-BAT-01,In Stock,battery1.jpg,High quality rechargeable lithium cell\n"
            "HC-SR04 Ultrasonic Sensor,120,,Sensors & Modules,Ultrasonic Sensors,TR-SEN-01,In Stock,sensor1.jpg,Ultrasonic precision distance measuring sensor\n"
            "DVM 1.5mm Copper Wire Roll 90m,850,DVM,Wires,Copper Wires,DVM-WIR-01,In Stock,wire1.jpg,Pure electrolytic copper insulated flexible wire\n"
        ).encode("utf-8")

        self.send_response(200)
        self.send_header("Content-Type", "text/csv; charset=utf-8")
        self.send_header("Content-Disposition", 'attachment; filename="tarang_catalog_template.csv"')
        self.send_header("Content-Length", str(len(csv_content)))
        self.end_headers()
        self.wfile.write(csv_content)

    def handle_bulk_image_upload(self):
        content_type = self.headers.get("Content-Type", "")
        if "multipart/form-data" not in content_type:
            return self.send_json({"error": "Content-Type must be multipart/form-data"}, 400)

        content_length = int(self.headers.get("Content-Length", 0))
        boundary = content_type.split("boundary=")[1].strip()
        raw_data = self.rfile.read(content_length)

        boundary_bytes = ("--" + boundary).encode("latin-1")
        parts = raw_data.split(boundary_bytes)

        uploaded_files = []
        for part in parts:
            if not part or part == b"--\r\n" or part == b"--":
                continue

            if b"\r\n\r\n" in part:
                headers_part, body_part = part.split(b"\r\n\r\n", 1)
                if body_part.endswith(b"\r\n"):
                    body_part = body_part[:-2]

                headers_text = headers_part.decode("latin-1", errors="ignore")
                if "filename=" in headers_text:
                    filename_attr = headers_text.split('filename="')[1].split('"')[0]
                    clean_name = os.path.basename(filename_attr).replace(" ", "_")
                    if not clean_name:
                        continue

                    # Upload to Cloudinary (or local fallback if not configured)
                    upload_res = cloudinary_service.upload_image(
                        body_part,
                        filename=clean_name,
                        folder="tarang_radios/products"
                    )

                    uploaded_files.append({
                        "filename": upload_res.get("filename", clean_name),
                        "originalFilename": filename_attr,
                        "url": upload_res.get("url", f"uploads/{clean_name}"),
                        "is_cloud": upload_res.get("is_cloud", False),
                        "size": len(body_part)
                    })

        is_cloud_dest = any(f.get("is_cloud") for f in uploaded_files)
        dest_label = "Cloudinary CDN" if is_cloud_dest else "local storage"
        return self.send_json({
            "success": True,
            "count": len(uploaded_files),
            "files": uploaded_files,
            "is_cloud": is_cloud_dest,
            "message": f"Successfully uploaded {len(uploaded_files)} images to {dest_label}."
        })

    def handle_bulk_product_import(self):
        data = self.read_json_body()
        products_list = data.get("products", [])

        if not products_list or not isinstance(products_list, list):
            return self.send_json({"error": "A list of products is required for import."}, 400)

        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("SELECT id, name FROM brands")
        brands = cursor.fetchall()
        brand_by_name = {b["name"].lower().strip(): b["id"] for b in brands}

        cursor.execute("SELECT id, title, brand_id FROM categories")
        cats = cursor.fetchall()
        cat_by_id = {c["id"]: c["id"] for c in cats}
        cat_by_title = {c["title"].lower().strip(): c["id"] for c in cats}

        cursor.execute("SELECT id, category_id, name FROM subcategories")
        subs = cursor.fetchall()
        subs_by_cat_and_name = {(s["category_id"], s["name"].lower().strip()): s["name"] for s in subs}

        imported_count = 0
        now = datetime.now().isoformat()

        for item in products_list:
            name = (item.get("name") or item.get("Product Name") or "").strip()
            if not name:
                continue

            raw_brand = (item.get("brand") or item.get("Brand") or "").strip()
            brand_id = brand_by_name.get(raw_brand.lower()) if raw_brand else None

            raw_cat = (item.get("category") or item.get("Category") or item.get("categoryId") or "").strip()
            cat_id = None
            if raw_cat in cat_by_id:
                cat_id = raw_cat
            elif raw_cat.lower() in cat_by_title:
                cat_id = cat_by_title[raw_cat.lower()]
            else:
                new_cat_id = raw_cat.lower().replace(" ", "-").replace("&", "and")
                new_cat_id = "".join(c for c in new_cat_id if c.isalnum() or c in "-_") or f"cat_{uuid.uuid4().hex[:6]}"
                cursor.execute("""
                    INSERT INTO categories (id, brand_id, title, short_title, tagline, icon, image, color, display_order, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (new_cat_id, brand_id, raw_cat or "General", raw_cat or "General", "", "layers", "", "#D14B14", 99, now, now))
                cat_id = new_cat_id
                cat_by_id[cat_id] = cat_id
                cat_by_title[raw_cat.lower()] = cat_id

            raw_sub = (item.get("subcategory") or item.get("Subcategory") or "").strip()
            if raw_sub and (cat_id, raw_sub.lower()) not in subs_by_cat_and_name:
                sub_id = f"sub_{cat_id}_{uuid.uuid4().hex[:6]}"
                cursor.execute("""
                    INSERT INTO subcategories (id, category_id, name, display_order)
                    VALUES (?, ?, ?, ?)
                """, (sub_id, cat_id, raw_sub, 99))
                subs_by_cat_and_name[(cat_id, raw_sub.lower())] = raw_sub

            try:
                price = float(item.get("price") or item.get("Price") or 0)
            except Exception:
                price = 0.0

            sku = (item.get("sku") or item.get("SKU") or f"TR-{uuid.uuid4().hex[:6].upper()}").strip()
            avail = (item.get("availability") or item.get("Availability") or "In Stock").strip().lower()
            in_stock = 0 if avail in ["out of stock", "no", "false", "0"] else 1
            image = (item.get("image") or item.get("Image Filename") or "").strip()
            
            if image and not image.startswith("http") and not image.startswith("uploads/"):
                if os.path.exists(os.path.join(UPLOAD_DIR, image)):
                    image = f"uploads/{image}"

            description = (item.get("description") or item.get("Description") or "").strip()
            prod_id = f"prod_{uuid.uuid4().hex[:8]}"

            cursor.execute("""
                INSERT INTO products (id, sku, name, brand_id, brand, category_id, subcategory, price, badge, in_stock, image, description, specs, rating, reviews, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (prod_id, sku, name, brand_id, raw_brand or None, cat_id, raw_sub, price, "", in_stock, image, description, "{}", 5.0, 0, now, now))
            imported_count += 1

        conn.commit()
        conn.close()

        return self.send_json({
            "success": True,
            "count": imported_count,
            "message": f"Successfully imported {imported_count} products."
        })

    def handle_auth_login(self):
        data = self.read_json_body()
        username = (data.get("username") or "").strip()
        password = (data.get("password") or "").strip()

        if not username or not password:
            return self.send_json({"error": "Username and password required"}, 400)

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM admins WHERE username = ?", (username,))
        admin = cursor.fetchone()

        if not admin or not verify_password(password, admin["password_hash"], admin["salt"]):
            conn.close()
            return self.send_json({"error": "Invalid username or password"}, 401)

        token = secrets.token_urlsafe(32)
        expires_at = (datetime.now() + timedelta(days=7)).isoformat()
        cursor.execute(
            "INSERT INTO sessions (token, admin_id, expires_at) VALUES (?, ?, ?)",
            (token, admin["id"], expires_at)
        )
        conn.commit()
        conn.close()

        return self.send_json({
            "token": token,
            "user": {
                "id": admin["id"],
                "username": admin["username"],
                "name": admin["name"]
            },
            "expiresAt": expires_at
        })

    def handle_auth_logout(self):
        user = authenticate_request(self.headers)
        if user:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM sessions WHERE token = ?", (user["token"],))
            conn.commit()
            conn.close()
        return self.send_json({"success": True, "message": "Logged out successfully"})

    def handle_change_password(self, user):
        data = self.read_json_body()
        old_pwd = data.get("oldPassword", "").strip()
        new_pwd = data.get("newPassword", "").strip()

        if not old_pwd or not new_pwd:
            return self.send_json({"error": "Both current and new password are required"}, 400)
        if len(new_pwd) < 6:
            return self.send_json({"error": "New password must be at least 6 characters"}, 400)

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT password_hash, salt FROM admins WHERE id = ?", (user["id"],))
        admin = cursor.fetchone()

        if not admin or not verify_password(old_pwd, admin["password_hash"], admin["salt"]):
            conn.close()
            return self.send_json({"error": "Current password is incorrect"}, 400)

        new_hash, new_salt = hash_password(new_pwd)
        cursor.execute("UPDATE admins SET password_hash = ?, salt = ? WHERE id = ?", (new_hash, new_salt, user["id"]))
        conn.commit()
        conn.close()
        return self.send_json({"success": True, "message": "Password updated successfully"})


def run_server():
    run_all_migrations()
    db_status = get_db_status()
    cloud_status = cloudinary_service.get_status()

    engine_label = "PostgreSQL" if db_status.get("is_postgres") else "SQLite (tarang.db)"
    cloud_label = f"Cloudinary ({cloud_status['cloud_name']})" if cloud_status.get("configured") else "Local uploads/ fallback"

    handler = TarangRequestHandler
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), handler) as httpd:
        print(f"\n=======================================================")
        print(f" TARANG RADIOS SERVER RUNNING AT http://localhost:{PORT}")
        print(f" Database Engine : {engine_label}")
        print(f" Media Storage   : {cloud_label}")
        print(f" Admin Dashboard : http://localhost:{PORT}/admin/")
        admin_user = os.environ.get("ADMIN_USERNAME", "").strip()
        if admin_user:
            print(f" Admin User      : '{admin_user}' (from .env)")
        print(f"=======================================================\n")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server...")
            httpd.server_close()

if __name__ == "__main__":
    run_server()
