"""
TARANG RADIOS - SQLite to PostgreSQL Data Migration Tool
Transfers all existing catalog data from tarang.db into a PostgreSQL instance.
Usage:
    python scripts/migrate_sqlite_to_postgres.py [--dry-run]
"""

import os
import sys
import sqlite3

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))
except ImportError:
    pass

import psycopg2
import psycopg2.extras
from migrate import run_all_migrations

SQLITE_PATH = os.path.join(os.path.dirname(__file__), "..", "tarang.db")
DATABASE_URL = os.environ.get("DATABASE_URL", "").strip()

TABLES_TO_MIGRATE = [
    "admins",
    "brands",
    "categories",
    "subcategories",
    "products",
    "sessions"
]

def migrate_data(dry_run: bool = False):
    if not os.path.exists(SQLITE_PATH):
        print(f"[ERROR] SQLite database not found at {SQLITE_PATH}")
        return False

    if not DATABASE_URL:
        print("[ERROR] DATABASE_URL is not set in .env or environment.")
        print("Please set DATABASE_URL=postgresql://user:pass@host:port/dbname in your .env file.")
        return False

    print("=================================================================")
    print("      TARANG RADIOS - SQLITE TO POSTGRESQL DATA MIGRATION        ")
    print("=================================================================")
    print(f"Source DB      : SQLite ({SQLITE_PATH})")
    print(f"Destination DB : PostgreSQL ({DATABASE_URL.split('@')[-1] if '@' in DATABASE_URL else 'configured'})")
    print(f"Dry Run Mode   : {'YES (no writes will be committed)' if dry_run else 'NO (live migration)'}")
    print("-----------------------------------------------------------------")

    # Connect to SQLite
    sqlite_conn = sqlite3.connect(SQLITE_PATH)
    sqlite_conn.row_factory = sqlite3.Row
    sqlite_cursor = sqlite_conn.cursor()

    # Connect to PostgreSQL
    pg_url = DATABASE_URL
    if pg_url.startswith("postgres://"):
        pg_url = pg_url.replace("postgres://", "postgresql://", 1)

    try:
        pg_conn = psycopg2.connect(pg_url, cursor_factory=psycopg2.extras.RealDictCursor)
    except Exception as e:
        print(f"[ERROR] Could not connect to PostgreSQL: {e}")
        return False

    # Apply all migrations on Postgres first
    if not dry_run:
        print("\n[STEP 1] Ensuring PostgreSQL schema is initialized...")
        # Override env to ensure migrate runs on postgres
        os.environ["DATABASE_URL"] = DATABASE_URL
        run_all_migrations()

    print("\n[STEP 2] Migrating table contents...")
    pg_cursor = pg_conn.cursor()

    total_records = 0

    for table in TABLES_TO_MIGRATE:
        try:
            sqlite_cursor.execute(f"SELECT * FROM {table}")
            rows = sqlite_cursor.fetchall()
            row_count = len(rows)
            print(f"  -> Table '{table}': found {row_count} records in SQLite.")

            if row_count == 0 or dry_run:
                continue

            # Get columns
            sqlite_cursor.execute(f"PRAGMA table_info({table})")
            columns = [col["name"] for col in sqlite_cursor.fetchall()]
            col_names = ", ".join(columns)
            placeholders = ", ".join(["%s"] * len(columns))

            # Upsert into PostgreSQL
            upsert_sql = f"""
            INSERT INTO {table} ({col_names})
            VALUES ({placeholders})
            ON CONFLICT (id) DO NOTHING
            """

            for row in rows:
                values = [row[col] for col in columns]
                pg_cursor.execute(upsert_sql, values)

            pg_conn.commit()
            total_records += row_count
            print(f"     [OK] Successfully migrated {row_count} records into PostgreSQL '{table}'.")

        except Exception as err:
            print(f"     [ERROR] Failed to migrate table '{table}': {err}")
            pg_conn.rollback()

    sqlite_conn.close()
    pg_conn.close()

    print("\n-----------------------------------------------------------------")
    if dry_run:
        print("[DRY RUN COMPLETE] Verified SQLite data. Run without --dry-run to commit.")
    else:
        print(f"[MIGRATION COMPLETE] Successfully migrated {total_records} records to PostgreSQL!")
    print("=================================================================\n")
    return True

if __name__ == "__main__":
    is_dry = "--dry-run" in sys.argv
    migrate_data(dry_run=is_dry)
