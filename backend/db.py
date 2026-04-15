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
    # Migration: add kleur to vestigingen if not yet present
    try:
        conn.execute("ALTER TABLE vestigingen ADD COLUMN kleur TEXT DEFAULT NULL")
        conn.commit()
    except Exception:
        pass  # kolom bestaat al
    # Migration: vestigingen_klassen koppeltabel
    try:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS vestigingen_klassen (
                vestiging_id INTEGER NOT NULL REFERENCES vestigingen(id) ON DELETE CASCADE,
                klas TEXT NOT NULL,
                PRIMARY KEY (vestiging_id, klas)
            )
        ''')
        conn.commit()
    except Exception:
        pass
    # Migration: vestigingen_locaties koppeltabel (Magister locatie → vestiging)
    try:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS vestigingen_locaties (
                vestiging_id INTEGER NOT NULL REFERENCES vestigingen(id) ON DELETE CASCADE,
                locatie TEXT NOT NULL,
                PRIMARY KEY (vestiging_id, locatie)
            )
        ''')
        conn.commit()
    except Exception:
        pass
    # Migration: gebruikers (in-app user management)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS gebruikers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            naam TEXT NOT NULL DEFAULT '',
            rol TEXT NOT NULL DEFAULT 'concierge',
            actief INTEGER NOT NULL DEFAULT 1,
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now'))
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS gebruiker_vestigingen (
            gebruiker_id INTEGER NOT NULL REFERENCES gebruikers(id) ON DELETE CASCADE,
            vestiging_id INTEGER NOT NULL REFERENCES vestigingen(id) ON DELETE CASCADE,
            PRIMARY KEY (gebruiker_id, vestiging_id)
        )
    ''')
    conn.commit()
    return conn

def get_db(db_path):
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys=ON")
    conn.row_factory = sqlite3.Row
    return conn

def close_db(conn):
    if conn:
        conn.close()
