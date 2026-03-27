#!/usr/bin/env python3
import sys
sys.path.insert(0, '.')
from magister_client import magister
import sqlite3

print('=== MAGISTER SYNC ===')
print('Fetching kluisjes van Magister...')

try:
    kluisjes = magister.get_kluisjes()
    leerlingen = magister.get_leerlingen()

    print(f'✓ {len(kluisjes)} kluisjes ontvangen')
    print(f'✓ {len(leerlingen)} leerlingen ontvangen')

    # Database sync
    conn = sqlite3.connect('kluisjesbeheer.db')
    conn.row_factory = sqlite3.Row

    leerling_map = {l['stamnr']: l for l in leerlingen}

    created = 0
    updated = 0
    assigned = 0
    skipped = 0

    for mk in kluisjes:
        kluis_code = mk['kluis_code'].strip()
        if not kluis_code:
            skipped += 1
            continue

        existing = conn.execute(
            'SELECT id, status FROM kluisjes WHERE vestiging_id = ? AND kluisnummer = ? AND verwijderd = 0',
            (1, kluis_code)
        ).fetchone()

        if existing:
            kluisje_id = existing['id']
            sleutel = mk.get('sleutel', '')
            if sleutel:
                conn.execute(
                    "UPDATE kluisjes SET sleutelnummer = ?, updated_at = datetime('now') WHERE id = ?",
                    (sleutel, kluisje_id)
                )
            updated += 1
        else:
            sleutel = mk.get('sleutel', '')
            omschrijving = mk.get('omschrijving', '')
            cur = conn.execute(
                'INSERT INTO kluisjes (cluster_id, vestiging_id, kluisnummer, sleutelnummer, locatie, status) VALUES (?, ?, ?, ?, ?, ?)',
                (1, 1, kluis_code, sleutel, omschrijving, 'vrij')
            )
            kluisje_id = cur.lastrowid
            created += 1

        stamnr = mk.get('stamnr', '').strip()
        if not stamnr:
            continue

        leerling = leerling_map.get(stamnr)
        if not leerling:
            continue

        active = conn.execute(
            'SELECT id FROM toewijzingen WHERE kluisje_id = ? AND actief = 1',
            (kluisje_id,)
        ).fetchone()
        if active:
            continue

        naam = leerling.get('naam', f"{leerling.get('achternaam', '')}, {leerling.get('roepnaam', '')}")
        klas = leerling.get('klas', '')
        datum_van = mk.get('datum_van', '').replace('/', '-')
        datum_tot = mk.get('datum_tot', '').replace('/', '-')
        borg = 0
        try:
            borg = float(mk.get('borg', 0) or 0)
        except (ValueError, TypeError):
            pass

        if datum_van.startswith('1899'):
            datum_van = ''
        if datum_tot.startswith('1899'):
            datum_tot = ''

        if datum_van:
            conn.execute('''
                INSERT INTO toewijzingen
                (kluisje_id, leerling_stamnr, leerling_naam, leerling_klas,
                 periode_van, periode_tot, borgbedrag, borg_betaald, actief, aangemaakt_door)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, ?)
            ''', (
                kluisje_id, stamnr, naam, klas,
                datum_van, datum_tot or datum_van, borg,
                1 if borg > 0 else 0,
                'Magister Sync',
            ))
            conn.execute(
                "UPDATE kluisjes SET status = 'uitgeleend', updated_at = datetime('now') WHERE id = ?",
                (kluisje_id,)
            )
            assigned += 1

    conn.commit()

    print(f'\n=== SYNC RESULTAAT ===')
    print(f'Created:  {created}')
    print(f'Updated:  {updated}')
    print(f'Assigned: {assigned}')
    print(f'Skipped:  {skipped}')
    print(f'Total:    {len(kluisjes)}')

    conn.close()

except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc()
