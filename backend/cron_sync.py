#!/usr/bin/env python3
"""Daily cron: refresh student list from Magister and store in database.
Run via: /opt/kluisjesbeheer/.venv/bin/python /opt/kluisjesbeheer/backend/cron_sync.py
"""
import os
import sys
sys.path.insert(0, os.path.dirname(__file__))
from magister_client import MagisterClient
from db import get_db


def _magister_from_db(db):
    """Read Magister credentials from the instellingen table.
    cron_sync runs outside a Flask request context, so MagisterClient's own
    flask.g-based DB lookup is unavailable here -- read directly and pass as
    an explicit override. Returns (url, user, password) or None if incomplete.
    """
    rows = db.execute(
        "SELECT key, value FROM instellingen WHERE key IN ('magister_url', 'magister_user', 'magister_pass')"
    ).fetchall()
    cfg = {r['key']: r['value'] for r in rows}
    if cfg.get('magister_url') and cfg.get('magister_user') and cfg.get('magister_pass'):
        from crypto_util import decrypt
        return cfg['magister_url'], cfg['magister_user'], decrypt(cfg['magister_pass'])
    return None


def main():
    print('=== CRON MAGISTER LEERLINGEN SYNC ===')
    db_path = os.path.join(os.path.dirname(__file__), 'kluisjesbeheer.db')
    db = get_db(db_path)

    db_creds = _magister_from_db(db)
    if db_creds:
        url, user, password = db_creds
        print(f'Magister-config uit database: {url}')
        magister = MagisterClient(url, user, password)
    else:
        # Fallback: config.json (legacy installs zoals School)
        print('Geen volledige Magister-config in database, val terug op config.json')
        magister = MagisterClient()

    try:
        leerlingen = magister.get_leerlingen()
        klassen = sorted(set(l['klas'] for l in leerlingen if l['klas']))
        print(f'{len(leerlingen)} leerlingen opgehaald, {len(klassen)} klassen')

        for l in leerlingen:
            db.execute('''
                INSERT INTO leerlingen (stamnr, naam, roepnaam, tussenvoegsel, achternaam, email, klas, leerjaar, studie, locatie, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
                ON CONFLICT(stamnr) DO UPDATE SET
                    naam=excluded.naam, roepnaam=excluded.roepnaam, tussenvoegsel=excluded.tussenvoegsel,
                    achternaam=excluded.achternaam, email=excluded.email, klas=excluded.klas,
                    leerjaar=excluded.leerjaar, studie=excluded.studie, locatie=excluded.locatie,
                    updated_at=datetime('now')
            ''', (
                l['stamnr'], l['naam'], l.get('roepnaam', ''), l.get('tussenvoegsel', ''),
                l.get('achternaam', ''), l.get('email', ''), l['klas'],
                l.get('leerjaar', ''), l.get('studie', ''), l.get('locatie', ''),
            ))
        db.commit()
        print(f'Database bijgewerkt. Done!')
    except Exception as e:
        print(f'ERROR: {e}')
        sys.exit(1)
    finally:
        db.close()


if __name__ == '__main__':
    main()
