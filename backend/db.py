import os
import sqlite3

_SCHEMA_PATH = os.path.join(os.path.dirname(__file__), 'schema.sql')

def init_db(db_path):
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.row_factory = sqlite3.Row
    with open(_SCHEMA_PATH) as f:
        conn.executescript(f.read())
    # Migration: add borg_actief to vestigingen if not yet present
    try:
        conn.execute("ALTER TABLE vestigingen ADD COLUMN borg_actief INTEGER DEFAULT 1")
        conn.commit()
    except Exception:
        pass  # kolom bestaat al
    return conn

def get_db(db_path):
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys=ON")
    conn.row_factory = sqlite3.Row
    return conn

def close_db(conn):
    if conn:
        conn.close()
