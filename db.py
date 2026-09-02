"""
TARANG RADIOS - Database Access Layer
Supports PostgreSQL (Production/Cloud) and SQLite (Offline/Local Fallback) with a unified API.
"""

import os
import re
import sys
import sqlite3
from contextlib import contextmanager

# Try loading python-dotenv if installed
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
except ImportError:
    pass

# PostgreSQL Driver Import
PSYCOPG2_AVAILABLE = False
try:
    import psycopg2
    import psycopg2.extras
    PSYCOPG2_AVAILABLE = True
except ImportError:
    try:
        import psycopg as psycopg2
        import psycopg.rows
        PSYCOPG2_AVAILABLE = True
    except ImportError:
        PSYCOPG2_AVAILABLE = False

DB_FILE = os.path.join(os.path.dirname(__file__), "tarang.db")
DATABASE_URL = os.environ.get("DATABASE_URL", "").strip()

def get_engine_type():
    """Returns 'postgres' if DATABASE_URL is configured, else 'sqlite'."""
    url = os.environ.get("DATABASE_URL", "").strip()
    if url and (url.startswith("postgres://") or url.startswith("postgresql://")):
        return "postgres"
    return "sqlite"

class DBCursorWrapper:
    """Cursor wrapper that normalizes parameter placeholders and row access."""
    def __init__(self, raw_cursor, engine_type):
        self.cursor = raw_cursor
        self.engine_type = engine_type

    def _format_sql(self, sql: str) -> str:
        if self.engine_type == "postgres":
            return re.sub(r'\?', '%s', sql)
        return sql

    def execute(self, sql: str, params=None):
        formatted_sql = self._format_sql(sql)
        if params is not None:
            return self.cursor.execute(formatted_sql, params)
        return self.cursor.execute(formatted_sql)

    def executemany(self, sql: str, params_seq):
        formatted_sql = self._format_sql(sql)
        return self.cursor.executemany(formatted_sql, params_seq)

    def fetchone(self):
        row = self.cursor.fetchone()
        if row is None:
            return None
        if self.engine_type == "sqlite":
            return dict(row)
        if isinstance(row, dict):
            return row
        return dict(row)

    def fetchall(self):
        rows = self.cursor.fetchall()
        if self.engine_type == "sqlite":
            return [dict(r) for r in rows]
        if rows and isinstance(rows[0], dict):
            return list(rows)
        return [dict(r) for r in rows]

    @property
    def rowcount(self):
        return self.cursor.rowcount

    @property
    def description(self):
        return self.cursor.description

    def close(self):
        try:
            self.cursor.close()
        except Exception:
            pass

class DBConnectionWrapper:
    """Unified wrapper around PostgreSQL and SQLite connections."""
    def __init__(self, raw_conn, engine_type):
        self.conn = raw_conn
        self.engine_type = engine_type

    def cursor(self):
        raw_cur = self.conn.cursor()
        return DBCursorWrapper(raw_cur, self.engine_type)

    def execute(self, sql: str, params=None):
        cur = self.cursor()
        try:
            cur.execute(sql, params)
            return cur
        except Exception as e:
            self.conn.rollback()
            raise e

    def executemany(self, sql: str, params_seq):
        cur = self.cursor()
        try:
            cur.executemany(sql, params_seq)
            return cur
        except Exception as e:
            self.conn.rollback()
            raise e

    def fetchone(self, sql: str, params=None):
        cur = self.execute(sql, params)
        res = cur.fetchone()
        cur.close()
        return res

    def fetchall(self, sql: str, params=None):
        cur = self.execute(sql, params)
        res = cur.fetchall()
        cur.close()
        return res

    def commit(self):
        self.conn.commit()

    def rollback(self):
        try:
            self.conn.rollback()
        except Exception:
            pass

    def close(self):
        try:
            self.conn.close()
        except Exception:
            pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.rollback()
        else:
            self.commit()
        self.close()

def create_connection():
    """Creates a raw DB connection based on configuration."""
    engine = get_engine_type()
    db_url = os.environ.get("DATABASE_URL", "").strip()

    if engine == "postgres":
        if not PSYCOPG2_AVAILABLE:
            print("[DB WARNING] DATABASE_URL is set, but 'psycopg2-binary' is not installed. Falling back to SQLite.")
            return _create_sqlite_connection(), "sqlite"
        try:
            if db_url.startswith("postgres://"):
                db_url = db_url.replace("postgres://", "postgresql://", 1)
            
            conn = psycopg2.connect(db_url, cursor_factory=psycopg2.extras.RealDictCursor)
            conn.autocommit = False
            return conn, "postgres"
        except Exception as err:
            print(f"[DB ERROR] Failed to connect to PostgreSQL: {err}. Falling back to SQLite.")
            return _create_sqlite_connection(), "sqlite"
    else:
        return _create_sqlite_connection(), "sqlite"

def _create_sqlite_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def get_db():
    """Returns a unified DBConnectionWrapper instance."""
    raw_conn, engine = create_connection()
    return DBConnectionWrapper(raw_conn, engine)

def get_status():
    """Returns status info about the current active database."""
    engine = get_engine_type()
    db_url = os.environ.get("DATABASE_URL", "").strip()
    status = {
        "engine": engine,
        "is_postgres": engine == "postgres",
        "psycopg2_available": PSYCOPG2_AVAILABLE,
        "database_url_configured": bool(db_url),
        "db_file": DB_FILE if engine == "sqlite" else None
    }
    try:
        with get_db() as db:
            prod_count = db.fetchone("SELECT COUNT(*) as count FROM products")
            status["connected"] = True
            status["products_count"] = prod_count["count"] if prod_count else 0
    except Exception as e:
        status["connected"] = False
        status["error"] = str(e)
    return status
