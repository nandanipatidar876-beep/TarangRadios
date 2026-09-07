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

# PostgreSQL Driver & Pool Import
PSYCOPG2_AVAILABLE = False
try:
    import psycopg2
    import psycopg2.extras
    import psycopg2.pool
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

_PG_POOL = None

def get_engine_type():
    """Returns 'postgres' if DATABASE_URL is configured, else 'sqlite'."""
    url = os.environ.get("DATABASE_URL", "").strip()
    if url and (url.startswith("postgres://") or url.startswith("postgresql://")):
        return "postgres"
    return "sqlite"

def _get_pg_pool():
    global _PG_POOL
    if _PG_POOL is None or _PG_POOL.closed:
        db_url = os.environ.get("DATABASE_URL", "").strip()
        if db_url.startswith("postgres://"):
            db_url = db_url.replace("postgres://", "postgresql://", 1)
        try:
            _PG_POOL = psycopg2.pool.ThreadedConnectionPool(
                minconn=2,
                maxconn=15,
                dsn=db_url,
                cursor_factory=psycopg2.extras.RealDictCursor,
                connect_timeout=10,
                keepalives=1,
                keepalives_idle=30,
                keepalives_interval=10,
                keepalives_count=5
            )
        except Exception as e:
            print(f"[DB ERROR] Could not initialize PostgreSQL pool: {e}")
            _PG_POOL = None
    return _PG_POOL

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
        if self.engine_type == "postgres" and PSYCOPG2_AVAILABLE:
            try:
                import psycopg2.extras
                return psycopg2.extras.execute_batch(self.cursor, formatted_sql, params_seq, page_size=200)
            except Exception as e:
                pass
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
    def __init__(self, raw_conn, engine_type, from_pool=False):
        self.conn = raw_conn
        self.engine_type = engine_type
        self.from_pool = from_pool

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
            if self.from_pool and self.engine_type == "postgres":
                pool = _get_pg_pool()
                if pool and not pool.closed:
                    pool.putconn(self.conn)
                    return
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

def _is_pg_alive(conn):
    """Verifies that a PostgreSQL connection is truly alive and responsive."""
    try:
        if conn is None or conn.closed != 0:
            return False
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
        conn.commit()
        return True
    except Exception:
        try:
            conn.rollback()
        except Exception:
            pass
        return False

def create_connection():
    """Creates a raw DB connection or retrieves from pool with automatic liveness verification."""
    engine = get_engine_type()

    if engine == "postgres":
        if not PSYCOPG2_AVAILABLE:
            return _create_sqlite_connection(), "sqlite", False
        pool = _get_pg_pool()
        if pool:
            try:
                conn = pool.getconn()
                if not _is_pg_alive(conn):
                    try:
                        pool.putconn(conn, close=True)
                    except Exception:
                        pass
                    conn = pool.getconn()
                    if not _is_pg_alive(conn):
                        try:
                            pool.putconn(conn, close=True)
                        except Exception:
                            pass
                        raise Exception("Pooled connection failed liveness check")
                conn.autocommit = False
                return conn, "postgres", True
            except Exception as err:
                print(f"[DB POOL] Reconnecting: {err}")
        
        # Direct fallback if pool fails
        try:
            db_url = os.environ.get("DATABASE_URL", "").strip()
            if db_url.startswith("postgres://"):
                db_url = db_url.replace("postgres://", "postgresql://", 1)
            conn = psycopg2.connect(
                db_url,
                cursor_factory=psycopg2.extras.RealDictCursor,
                connect_timeout=8
            )
            conn.autocommit = False
            return conn, "postgres", False
        except Exception as err:
            print(f"[DB ERROR] PostgreSQL connection failed: {err}. Falling back to SQLite.")
            return _create_sqlite_connection(), "sqlite", False
    else:
        return _create_sqlite_connection(), "sqlite", False

def _create_sqlite_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def get_db():
    """Returns a unified DBConnectionWrapper instance."""
    raw_conn, engine, from_pool = create_connection()
    return DBConnectionWrapper(raw_conn, engine, from_pool)

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
