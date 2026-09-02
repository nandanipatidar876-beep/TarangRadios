"""
TARANG RADIOS - Database Migration Runner
Scans migrations/*.sql, applies pending migrations, and tracks them in schema_migrations table.
"""

import os
import sys
import glob
import uuid
import hashlib
import secrets
from datetime import datetime
from db import get_db, get_engine_type

MIGRATIONS_DIR = os.path.join(os.path.dirname(__file__), "migrations")

def init_migrations_table(db):
    """Ensures schema_migrations table exists."""
    db.execute("""
    CREATE TABLE IF NOT EXISTS schema_migrations (
        version VARCHAR(64) PRIMARY KEY,
        filename VARCHAR(255) NOT NULL,
        applied_at VARCHAR(64) NOT NULL
    )
    """)
    db.commit()

def get_applied_migrations(db):
    """Returns set of applied migration versions."""
    init_migrations_table(db)
    rows = db.fetchall("SELECT version FROM schema_migrations")
    return {r["version"] for r in rows}

def get_migration_files():
    """Returns list of (version, filename, full_path) sorted by version."""
    if not os.path.exists(MIGRATIONS_DIR):
        return []
    
    files = []
    for fpath in glob.glob(os.path.join(MIGRATIONS_DIR, "*.sql")):
        fname = os.path.basename(fpath)
        version = fname.split("_")[0]
        files.append((version, fname, fpath))
    
    files.sort(key=lambda x: x[0])
    return files

def split_sql_statements(sql_text: str) -> list[str]:
    """Splits SQL script into individual statements for execution."""
    statements = []
    # Remove comment-only lines and split on semicolon
    lines = []
    for line in sql_text.splitlines():
        trimmed = line.strip()
        if trimmed.startswith("--") or not trimmed:
            continue
        lines.append(line)
    
    cleaned_sql = "\n".join(lines)
    for stmt in cleaned_sql.split(";"):
        stmt = stmt.strip()
        if stmt:
            statements.append(stmt)
    return statements

def run_all_migrations():
    """Applies all pending migrations. Safe to run on every server startup."""
    with get_db() as db:
        init_migrations_table(db)
        applied = get_applied_migrations(db)
        migration_files = get_migration_files()

        engine = get_engine_type()
        applied_count = 0

        for version, fname, fpath in migration_files:
            if version in applied:
                continue

            print(f"[MIGRATION] Applying {fname} on {engine.upper()}...")
            with open(fpath, "r", encoding="utf-8") as f:
                content = f.read()

            statements = split_sql_statements(content)
            for stmt in statements:
                db.execute(stmt)

            now_str = datetime.now().isoformat()
            db.execute(
                "INSERT INTO schema_migrations (version, filename, applied_at) VALUES (?, ?, ?)",
                (version, fname, now_str)
            )
            db.commit()
            print(f"[MIGRATION] [OK] {fname} applied successfully.")
            applied_count += 1

        # Check default admin creation if empty
        ensure_default_admin(db)

        if applied_count == 0:
            print(f"[MIGRATION] Database ({engine.upper()}) is already up to date.")
        else:
            print(f"[MIGRATION] Successfully applied {applied_count} migrations to {engine.upper()}.")

def ensure_default_admin(db):
    """Ensures at least one admin account exists using env vars or default."""
    try:
        admin_row = db.fetchone("SELECT COUNT(*) as count FROM admins")
        if not admin_row or admin_row.get("count", 0) == 0:
            admin_user = os.environ.get("ADMIN_USERNAME", "admin").strip() or "admin"
            admin_pwd = os.environ.get("ADMIN_PASSWORD", "admin123").strip() or "admin123"

            admin_id = str(uuid.uuid4())
            salt = secrets.token_hex(16)
            pwd_hash = hashlib.pbkdf2_hmac(
                'sha256',
                admin_pwd.encode('utf-8'),
                salt.encode('utf-8'),
                100000
            ).hex()
            now = datetime.now().isoformat()
            db.execute(
                "INSERT INTO admins (id, username, password_hash, salt, name, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (admin_id, admin_user, pwd_hash, salt, "Super Administrator", now)
            )
            db.commit()
            print(f"[MIGRATION] Admin account initialized (username: '{admin_user}').")
    except Exception as e:
        print(f"[MIGRATION WARNING] Could not verify admin account: {e}")

def print_migration_status():
    """Prints migration status table."""
    engine = get_engine_type()
    print(f"\n--- Tarang Radios Migration Status [{engine.upper()}] ---")
    with get_db() as db:
        applied = get_applied_migrations(db)
        migration_files = get_migration_files()

        if not migration_files:
            print("No migration files found in migrations/ folder.")
            return

        print(f"{'Version':<10} | {'Status':<12} | {'Filename':<35}")
        print("-" * 65)
        for version, fname, _ in migration_files:
            status = "APPLIED" if version in applied else "PENDING"
            print(f"{version:<10} | {status:<12} | {fname:<35}")
    print()

if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 else "up"
    if action == "status":
        print_migration_status()
    elif action in ("up", "run"):
        run_all_migrations()
    elif action == "init-admin":
        with get_db() as db:
            ensure_default_admin(db)
    else:
        print(f"Unknown command: {action}")
        print("Usage: python migrate.py [up|status|init-admin]")
