"""
TARANG RADIOS - Cloudinary Media Upload & CDN Delivery Service
Handles image uploads, on-the-fly transformations (f_auto, q_auto), and secure URL delivery.
Falls back to local uploads/ directory if Cloudinary credentials are not configured.
"""

import os
import sys
import uuid
import re
from io import BytesIO

# Try loading python-dotenv
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
except ImportError:
    pass

# Try importing cloudinary SDK
CLOUDINARY_AVAILABLE = False
try:
    import cloudinary
    import cloudinary.uploader
    import cloudinary.api
    CLOUDINARY_AVAILABLE = True
except ImportError:
    CLOUDINARY_AVAILABLE = False

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Read credentials
CLOUD_NAME = os.environ.get("CLOUDINARY_CLOUD_NAME", "").strip()
API_KEY = os.environ.get("CLOUDINARY_API_KEY", "").strip()
API_SECRET = os.environ.get("CLOUDINARY_API_SECRET", "").strip()
CLOUDINARY_URL = os.environ.get("CLOUDINARY_URL", "").strip()

def is_configured() -> bool:
    """Returns True if Cloudinary SDK is available and credentials are set."""
    if not CLOUDINARY_AVAILABLE:
        return False
    if CLOUDINARY_URL:
        return True
    return bool(CLOUD_NAME and API_KEY and API_SECRET)

def init_cloudinary():
    """Initializes Cloudinary configuration."""
    if not is_configured():
        return False
    
    if CLOUDINARY_URL:
        cloudinary.config(cloudinary_url=CLOUDINARY_URL, secure=True)
    else:
        cloudinary.config(
            cloud_name=CLOUD_NAME,
            api_key=API_KEY,
            api_secret=API_SECRET,
            secure=True
        )
    return True

# Initialize if available
if is_configured():
    init_cloudinary()

def upload_image(file_data, filename: str = None, folder: str = "tarang_radios/products") -> dict:
    """
    Uploads an image (bytes, file-like object, or filepath).
    Returns dict with { "success": True, "url": "...", "public_id": "...", "is_cloud": True/False }
    """
    clean_name = sanitize_filename(filename or f"img_{uuid.uuid4().hex[:8]}.jpg")

    if is_configured():
        try:
            init_cloudinary()
            upload_source = file_data
            if isinstance(file_data, bytes):
                upload_source = BytesIO(file_data)

            # Upload to Cloudinary with automatic optimization
            res = cloudinary.uploader.upload(
                upload_source,
                folder=folder,
                use_filename=True,
                unique_filename=True,
                overwrite=False,
                resource_type="image"
            )
            
            secure_url = res.get("secure_url") or res.get("url")
            public_id = res.get("public_id")

            # Format optimized URL (auto format, auto quality)
            # e.g., https://res.cloudinary.com/<cloud_name>/image/upload/f_auto,q_auto/v.../...
            optimized_url = secure_url
            if "res.cloudinary.com" in secure_url and "/upload/" in secure_url:
                optimized_url = secure_url.replace("/upload/", "/upload/f_auto,q_auto/")

            return {
                "success": True,
                "url": optimized_url,
                "public_id": public_id,
                "filename": clean_name,
                "is_cloud": True,
                "width": res.get("width"),
                "height": res.get("height"),
                "format": res.get("format"),
                "bytes": res.get("bytes")
            }
        except Exception as err:
            print(f"[CLOUDINARY WARNING] Cloud upload failed: {err}. Falling back to local storage.")

    # Fallback to local storage
    dest_path = os.path.join(UPLOAD_DIR, clean_name)
    if isinstance(file_data, bytes):
        with open(dest_path, "wb") as f:
            f.write(file_data)
    elif hasattr(file_data, "read"):
        with open(dest_path, "wb") as f:
            f.write(file_data.read())
    elif isinstance(file_data, str) and os.path.exists(file_data):
        with open(file_data, "rb") as src, open(dest_path, "wb") as dst:
            dst.write(src.read())
    
    file_size = os.path.getsize(dest_path) if os.path.exists(dest_path) else 0

    return {
        "success": True,
        "url": f"uploads/{clean_name}",
        "public_id": None,
        "filename": clean_name,
        "is_cloud": False,
        "bytes": file_size,
        "warning": "Stored locally because Cloudinary credentials are not configured in .env."
    }

def delete_image(public_id: str) -> bool:
    """Deletes image from Cloudinary by public_id."""
    if not is_configured() or not public_id:
        return False
    try:
        init_cloudinary()
        res = cloudinary.uploader.destroy(public_id)
        return res.get("result") == "ok"
    except Exception as e:
        print(f"[CLOUDINARY ERROR] Failed to delete {public_id}: {e}")
        return False

def sanitize_filename(name: str) -> str:
    """Removes invalid characters and spaces from filenames."""
    base = os.path.basename(name)
    base = re.sub(r'[^\w\.\-]', '_', base)
    return base or f"file_{uuid.uuid4().hex[:6]}.jpg"

def get_transformed_url(url: str, width: int = 400, height: int = 400, crop: str = "limit") -> str:
    """
    Returns an optimized Cloudinary delivery URL with dimensions, auto-format, and auto-quality.
    e.g. https://res.cloudinary.com/.../image/upload/f_auto,q_auto,w_400,c_limit/...
    """
    if not url or not isinstance(url, str) or not url.strip():
        return url or ""
    
    url = url.strip()
    if "res.cloudinary.com" in url and "/upload/" in url:
        transform = f"f_auto,q_auto,w_{width},c_{crop}"
        # If /upload/f_auto,q_auto/ or similar already exists, replace it cleanly
        parts = url.split("/upload/")
        if len(parts) == 2:
            second_part = parts[1]
            # Strip existing transform segment if present before v1...
            if second_part.startswith("f_auto") or second_part.startswith("w_") or second_part.startswith("q_"):
                sub_parts = second_part.split("/", 1)
                if len(sub_parts) == 2:
                    second_part = sub_parts[1]
            return f"{parts[0]}/upload/{transform}/{second_part}"
    return url

def get_status() -> dict:
    """Returns Cloudinary integration status."""
    return {
        "configured": is_configured(),
        "sdk_installed": CLOUDINARY_AVAILABLE,
        "cloud_name": CLOUD_NAME or ("configured_via_url" if CLOUDINARY_URL else None),
        "api_key_configured": bool(API_KEY or CLOUDINARY_URL),
        "api_secret_configured": bool(API_SECRET or CLOUDINARY_URL)
    }

if __name__ == "__main__":
    status = get_status()
    print("\n--- Cloudinary Integration Status ---")
    print(f"SDK Installed   : {'Yes' if status['sdk_installed'] else 'No (install with pip install cloudinary)'}")
    print(f"Configured      : {'Yes' if status['configured'] else 'No (add CLOUDINARY_* variables to .env)'}")
    print(f"Cloud Name      : {status['cloud_name'] or 'Not set'}")
    print()
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        if not is_configured():
            print("Cannot run test upload: Cloudinary is not configured.")
        else:
            print("Testing Cloudinary upload with a 1x1 test image...")
            # 1x1 transparent PNG bytes
            test_bytes = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\rIDATx\x9cc`\x00\x00\x00\x02\x00\x01H\xaf\xa4q\x00\x00\x00\x00IEND\xaeB`\x82'
            res = upload_image(test_bytes, "test_pixel.png", folder="tarang_radios/test")
            print(f"Test Upload Result:\n{res}")
