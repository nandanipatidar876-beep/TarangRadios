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

# Try loading python-dotenv
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
except ImportError:
    pass

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
                try:
                    db.execute(stmt)
                except Exception as stmt_err:
                    if engine == "sqlite" and "ALTER COLUMN" in stmt.upper():
                        # SQLite does not enforce VARCHAR length and doesn't support ALTER COLUMN
                        pass
                    else:
                        raise stmt_err

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
    """Initializes or updates admin account strictly from environment variables (ADMIN_USERNAME, ADMIN_PASSWORD)."""
    try:
        admin_user = os.environ.get("ADMIN_USERNAME", "").strip()
        admin_pwd = os.environ.get("ADMIN_PASSWORD", "").strip()

        if not admin_user or not admin_pwd:
            return

        admin_row = db.fetchone("SELECT id, username FROM admins LIMIT 1")
        now = datetime.now().isoformat()
        salt = secrets.token_hex(16)
        pwd_hash = hashlib.pbkdf2_hmac(
            'sha256',
            admin_pwd.encode('utf-8'),
            salt.encode('utf-8'),
            100000
        ).hex()

        if not admin_row:
            admin_id = str(uuid.uuid4())
            db.execute(
                "INSERT INTO admins (id, username, password_hash, salt, name, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (admin_id, admin_user, pwd_hash, salt, "Super Administrator", now)
            )
            db.commit()
            print(f"[MIGRATION] Admin account initialized from environment (username: '{admin_user}').")
        else:
            db.execute(
                "UPDATE admins SET username = ?, password_hash = ?, salt = ? WHERE id = ?",
                (admin_user, pwd_hash, salt, admin_row["id"])
            )
            db.commit()
            print(f"[MIGRATION] Admin credentials synchronized from environment.")
    except Exception as e:
        print(f"[MIGRATION WARNING] Could not sync admin account: {e}")

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
    import argparse

    parser = argparse.ArgumentParser(description="Tarang Radios - Database Migration & Production Catalog Sync Runner")
    parser.add_argument("command", nargs="?", default="up", choices=["up", "status", "init-admin", "sync-prod", "sync-noel"], help="Command to run (default: up)")
    parser.add_argument("--sync-prod", action="store_true", help="Sync local scraped catalog & images directly to production")
    parser.add_argument("--sync-noel", action="store_true", help="Scrape Noel India (noelindia.com) and sync under Brand: Noel")
    parser.add_argument("--catalog", default=r"D:\scrapping\products_catalog.json", help="Path to products_catalog.json")
    parser.add_argument("--images-dir", default=r"D:\scrapping\product_images", help="Path to product images root directory")
    parser.add_argument("--db-url", help="Override database connection URL (PostgreSQL / SQLite)")
    parser.add_argument("--workers", type=int, default=15, help="Concurrent upload threads (default: 15)")
    parser.add_argument("--dry-run", action="store_true", help="Preview sync and verify files without writing")
    parser.add_argument("--skip-images", action="store_true", help="Seed database without uploading new images")

    args = parser.parse_args()

    if args.sync_noel or args.command == "sync-noel":
        from scrap_noel import sync_noel_catalog
        sync_noel_catalog(
            db_url=args.db_url,
            workers=args.workers,
            dry_run=args.dry_run,
            skip_images=args.skip_images
        )
    elif args.sync_prod or args.command == "sync-prod":
        from sync_catalog import sync_production
        sync_production(
            catalog_path=args.catalog,
            images_dir=args.images_dir,
            db_url=args.db_url,
            workers=args.workers,
            dry_run=args.dry_run,
            skip_images=args.skip_images
        )
    elif args.command == "status":
        print_migration_status()
    elif args.command in ("up", "run"):
        if args.db_url:
            os.environ["DATABASE_URL"] = args.db_url
        run_all_migrations()
    elif args.command == "init-admin":
        if args.db_url:
            os.environ["DATABASE_URL"] = args.db_url
        with get_db() as db:
            ensure_default_admin(db)


