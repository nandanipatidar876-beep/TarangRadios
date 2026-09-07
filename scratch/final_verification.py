import urllib.request
import json

print("--- STARTING VERIFICATION ---")

# 1. Test Server API
url = "http://localhost:8000/api/public-data"
req = urllib.request.urlopen(url)
data = json.loads(req.read().decode('utf-8'))

assert "offers" not in data, "Offers should not be in public-data response"
print("OK API check passed: /api/public-data has no 'offers' field.")

# 2. Check index.html
with open("index.html", "r", encoding="utf-8") as f:
    index_html = f.read()

assert "offersSection" not in index_html, "offersSection should be removed from index.html"
assert 'href="#offersSection"' not in index_html, "Offers nav links should be removed from index.html"
assert 'z-index: 99999' in open("css/styles.css", encoding="utf-8").read(), "Modal wrapper z-index must be 99999"
assert 'position: sticky' in open("css/styles.css", encoding="utf-8").read(), "Modal close button must be sticky"
print("OK Storefront HTML & CSS check passed.")

# 3. Check admin/index.html
with open("admin/index.html", "r", encoding="utf-8") as f:
    admin_html = f.read()

assert 'data-tab="offers"' not in admin_html, "Offers tab should be removed from admin sidebar"
assert 'offerModalOverlay' not in admin_html, "offerModalOverlay should be removed from admin HTML"
assert 'view-offers' not in admin_html, "view-offers section should be removed from admin HTML"
print("OK Admin HTML check passed.")

# 4. Check admin/admin.js
with open("admin/admin.js", "r", encoding="utf-8") as f:
    admin_js = f.read()

assert 'loadOffersTable' not in admin_js, "loadOffersTable should be removed from admin.js"
assert 'openOfferModal' not in admin_js, "openOfferModal should be removed from admin.js"
print("OK Admin JS check passed.")

# 5. Check js/app.js
with open("js/app.js", "r", encoding="utf-8") as f:
    app_js = f.read()

assert 'renderOffersSection' not in app_js, "renderOffersSection should be removed from app.js"
assert 'e.target === subcategoryModal' in app_js, "Backdrop click listener must be in app.js"
assert "e.key === 'Escape'" in app_js, "Escape key listener must be in app.js"
print("OK Storefront JS check passed.")

print("--- ALL VERIFICATION TESTS PASSED SUCCESSFULLY! ---")

# 6. Check INGCO Brand Products in API & DB
conn = urllib.request.urlopen("http://localhost:8000/api/public-data")
public_data = json.loads(conn.read().decode('utf-8'))

ingco_brand = next((b for b in public_data.get('brands', []) if b.get('id') == 'brand_ingco' or b.get('name') == 'INGCO'), None)
assert ingco_brand is not None, "INGCO brand should exist in public-data brands"

ingco_products = [p for p in public_data.get('products', []) if p.get('brandId') == 'brand_ingco' or p.get('brand_id') == 'brand_ingco' or p.get('brand') == 'INGCO']
assert len(ingco_products) == 5, f"Expected 5 INGCO products, found {len(ingco_products)}"

# Ensure NONE of INGCO products are in main categories
main_categories = [c for c in public_data.get('categories', []) if not (c.get('brandId') or c.get('brand_id'))]
brand_categories = public_data.get('brandCategories', [])
ingco_category_ids = {c['id'] for c in brand_categories if (c.get('brandId') == 'brand_ingco' or c.get('brand_id') == 'brand_ingco')}

assert len(ingco_category_ids) > 0, "Expected INGCO brand categories in brandCategories"

for p in ingco_products:
    cat_id = p.get('categoryId') or p.get('category_id') or p.get('category')
    assert cat_id not in {c['id'] for c in main_categories}, f"Product {p['name']} found in main categories!"
    assert cat_id in ingco_category_ids, f"Product {p['name']} is not in an INGCO brand category!"

print(f"OK INGCO Integration check passed: {len(ingco_products)} INGCO products verified, strictly isolated from main categories and placed in brandCategories.")



