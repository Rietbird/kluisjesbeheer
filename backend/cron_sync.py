#!/usr/bin/env python3
"""Daily cron: refresh student list from Magister and store in database.
Run via: /opt/kluisjesbeheer/.venv/bin/python /opt/kluisjesbeheer/backend/cron_sync.py
"""
import os
import sys
sys.path.insert(0, os.path.dirname(__file__))
from magister_client import MagisterClient, safe_error
from db import get_db


def _magister_from_db(db):
    """Read Magister credentials from the instellingen table.
    cron_sync runs outside a Flask request context, so MagisterClient's own
    flask.g-based DB lookup is unavailable here -- read directly and pass as
    an explicit override.
    Returns (url, user, password) on full config, 'partial' when 1-2 of 3
    fields are filled (sync should fail loudly, not silently fall back), or
    None when nothing is configured (legacy config.json fallback is OK)."""
    rows = db.execute(
        "SELECT key, value FROM instellingen WHERE key IN ('magister_url', 'magister_user', 'magister_pass')"
    ).fetchall()
    cfg = {r['key']: r['value'] for r in rows}
    filled = sum(1 for k in ('magister_url', 'magister_user', 'magister_pass') if cfg.get(k))
    if filled == 3:
        from crypto_util import decrypt
        try:
            pw = decrypt(cfg['magister_pass'])
        except Exception:
            # Likely a SecretKey mismatch (e.g. DB restored from another env).
            # Do NOT fall back silently -- that masks the real problem.
            print('FOUT: kan magister_pass niet ontsleutelen (SecretKey klopt niet?).')
            return 'invalid'
        return cfg['magister_url'], cfg['magister_user'], pw
    if filled > 0:
        missing = [k for k in ('magister_url', 'magister_user', 'magister_pass') if not cfg.get(k)]
        print(f'FOUT: Magister-config in DB is onvolledig, ontbreekt: {", ".join(missing)}')
        return 'partial'
    return None


def main():
    print('=== CRON MAGISTER LEERLINGEN SYNC ===')
    db_path = os.path.join(os.path.dirname(__file__), 'kluisjesbeheer.db')
    db = get_db(db_path)

    db_creds = _magister_from_db(db)
    if db_creds in ('invalid', 'partial'):
        # Loud failure on bad config -- do not silently fall back.
        db.close()
        sys.exit(1)
    if db_creds:
        url, user, password = db_creds
        print(f'Magister-config uit database: {url}')
        magister = MagisterClient(url, user, password)
    else:
        # Fallback: config.json (legacy installs zonder DB-credentials)
        print('Geen Magister-config in database, val terug op config.json')
        magister = MagisterClient()
        password = magister.password  # for safe_error literal-strip below

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
        # NEVER print {e} directly -- requests exceptions contain the full URL
        # incl. Password=... query param. Strip it via safe_error before logging
        # (logs go to /var/log/kluisjes-sync.log on production).
        print(f'ERROR: {safe_error(e, password=password)}')
        sys.exit(1)
    finally:
        db.close()


if __name__ == '__main__':
    main()
