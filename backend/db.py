import os
import sqlite3

_SCHEMA_PATH = os.path.join(os.path.dirname(__file__), 'schema.sql')


def default_db_path():
    """Bepaal het standaard DB-pad. Voorkeur: backend/data/ (Docker-volume-
    aanpak); fallback: backend/ zelf (klassieke install.sh). Bestaat geen
    van beide: kies data/ als die dir bestaat, anders legacy."""
    backend_dir = os.path.dirname(__file__)
    data_path = os.path.join(backend_dir, 'data', 'kluisjesbeheer.db')
    legacy_path = os.path.join(backend_dir, 'kluisjesbeheer.db')
    if os.path.exists(data_path):
        return data_path
    if os.path.exists(legacy_path):
        return legacy_path
    if os.path.isdir(os.path.join(backend_dir, 'data')):
        return data_path
    return legacy_path


def default_backups_dir():
    """Idem voor backups: data/backups/ heeft voorkeur."""
    backend_dir = os.path.dirname(__file__)
    data_backups = os.path.join(backend_dir, 'data', 'backups')
    legacy_backups = os.path.join(backend_dir, 'backups')
    if os.path.isdir(os.path.join(backend_dir, 'data')):
        return data_backups
    return legacy_backups

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
    # Migration: vertrokken_op kolom voor leerlingen die van school zijn
    try:
        conn.execute("ALTER TABLE leerlingen ADD COLUMN vertrokken_op DATE DEFAULT NULL")
        conn.commit()
    except Exception:
        pass  # kolom bestaat al
    # Migration: is_defect + defect_sinds op kluisjes (defect los van huurstatus)
    try:
        conn.execute("ALTER TABLE kluisjes ADD COLUMN is_defect INTEGER NOT NULL DEFAULT 0")
        conn.commit()
    except Exception:
        pass
    try:
        conn.execute("ALTER TABLE kluisjes ADD COLUMN defect_sinds DATETIME DEFAULT NULL")
        conn.commit()
    except Exception:
        pass
    # Migration: reservesleutel velden op toewijzingen
    try:
        conn.execute("ALTER TABLE toewijzingen ADD COLUMN reservesleutel_uitgegeven INTEGER NOT NULL DEFAULT 0")
        conn.commit()
    except Exception:
        pass
    try:
        conn.execute("ALTER TABLE toewijzingen ADD COLUMN reservesleutel_datum DATE DEFAULT NULL")
        conn.commit()
    except Exception:
        pass
    # Data-migratie: status='defect' -> is_defect=1, status terug naar 'vrij' of 'uitgeleend'
    # Eenmalige conversie, idempotent (kluisje met status='defect' bestaat na conversie niet meer)
    row = conn.execute("SELECT value FROM instellingen WHERE key='defect_split_done'").fetchone()
    if not row:
        # Kluisjes met actieve toewijzing -> uitgeleend, anders vrij
        conn.execute('''
            UPDATE kluisjes SET is_defect = 1, defect_sinds = COALESCE(updated_at, datetime('now')),
                                status = CASE
                                    WHEN EXISTS (SELECT 1 FROM toewijzingen t WHERE t.kluisje_id = kluisjes.id AND t.actief = 1)
                                    THEN 'uitgeleend' ELSE 'vrij' END
            WHERE status = 'defect'
        ''')
        conn.execute("INSERT OR REPLACE INTO instellingen (key, value) VALUES ('defect_split_done', '1')")
        conn.commit()
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
