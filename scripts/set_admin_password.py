"""
TARANG RADIOS - Admin Credential Management Utility
Allows setting or updating the admin username and password securely.
Usage:
    python scripts/set_admin_password.py
    python scripts/set_admin_password.py --username myuser --password mysecurepassword123!
"""

import os
import sys
import uuid
import hashlib
import secrets
import getpass
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from db import get_db, get_engine_type

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

def set_admin_credentials(username: str, password: str, full_name: str = "Super Administrator"):
    username = username.strip()
    password = password.strip()

    if not username:
        print("[ERROR] Username cannot be empty.")
        return False
    if len(password) < 8:
        print("[ERROR] Password must be at least 8 characters long for security.")
        return False

    pwd_hash, salt = hash_password(password)
    now = datetime.now().isoformat()

    engine = get_engine_type().upper()

    with get_db() as db:
        # Check if an admin exists
        existing = db.fetchone("SELECT id, username FROM admins LIMIT 1")

        if existing:
            # Update existing admin
            db.execute(
                "UPDATE admins SET username = ?, password_hash = ?, salt = ?, name = ? WHERE id = ?",
                (username, pwd_hash, salt, full_name, existing["id"])
            )
            # Clear existing active sessions so re-login with new password is required
            db.execute("DELETE FROM sessions WHERE admin_id = ?", (existing["id"],))
            db.commit()
            print(f"[OK] Admin credentials updated successfully on {engine}!")
            print(f"     Username: '{username}'")
            print(f"     Password: (updated securely with SHA256 PBKDF2)")
        else:
            # Create new admin
            admin_id = str(uuid.uuid4())
            db.execute(
                "INSERT INTO admins (id, username, password_hash, salt, name, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (admin_id, username, pwd_hash, salt, full_name, now)
            )
            db.commit()
            print(f"[OK] Admin account created successfully on {engine}!")
            print(f"     Username: '{username}'")

    return True

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Set or update Tarang Radios admin credentials.")
    parser.add_argument("--username", "-u", help="Admin username")
    parser.add_argument("--password", "-p", help="Admin password")
    parser.add_argument("--name", "-n", default="Super Administrator", help="Admin display name")

    args = parser.parse_args()

    username = args.username
    password = args.password
    name = args.name

    if not username:
        username = input("Enter new Admin Username: ").strip()
    if not password:
        password = getpass.getpass("Enter new Admin Password (min 8 chars): ").strip()

    if username and password:
        set_admin_credentials(username, password, name)
    else:
        print("[ERROR] Both username and password are required.")
