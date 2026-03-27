#!/usr/bin/env python3
"""Initial import: create vestigingen, clusters, and import all kluisjes + toewijzingen from Magister."""
import sys
import re
sys.path.insert(0, '.')

from magister_client import magister
import sqlite3

DB_PATH = 'kluisjesbeheer.db'

# Vestigingen
VESTIGINGEN = [
    ('MHV', 'Mavo/Havo/Vwo'),
    ('Zuid', 'Kanaalschool Zuid'),
    ('ISK', 'ISK'),
    ('PRO', 'Praktijkonderwijs'),
]

# Prefix -> vestiging naam mapping
PREFIX_TO_VESTIGING = {
    'N': 'MHV',
    'V': 'MHV',
    'O': 'MHV',
    'X': 'MHV',
    'Z': 'Zuid',
    'ISK': 'ISK',
    'P': 'PRO',
}


def get_prefix(kluis_code):
    """Extract the letter prefix from a kluis_code (e.g. 'ISK1' from 'ISK1-0001', 'N' from 'N0001')."""
    m = re.match(r'^(ISK\d?|[A-Z])', kluis_code)
    if m:
        return m.group(1)
    return None


def get_vestiging_key(prefix):
    """Map a prefix to a vestiging key."""
    if prefix and prefix.startswith('ISK'):
        return 'ISK'
    return PREFIX_TO_VESTIGING.get(prefix)


def main():
    print('=== KLUISJESBEHEER INITIAL IMPORT ===')
    print()

    # Fetch Magister data
    print('Fetching kluisjes van Magister...')
    mag_kluisjes = magister.get_kluisjes()
    print(f'  {len(mag_kluisjes)} kluisjes ontvangen')

    print('Fetching leerlingen van Magister...')
    mag_leerlingen = magister.get_leerlingen()
    print(f'  {len(mag_leerlingen)} leerlingen ontvangen')
    print()

    leerling_map = {l['stamnr']: l for l in mag_leerlingen}

    # Connect to DB
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA journal_mode=WAL')

    # Check if DB already has data
    existing = conn.execute('SELECT COUNT(*) as c FROM vestigingen').fetchone()['c']
    if existing > 0:
        print(f'ERROR: Database heeft al {existing} vestigingen. Wis eerst de DB of gebruik sync.')
        conn.close()
        sys.exit(1)

    # 1. Create vestigingen
    print('Vestigingen aanmaken...')
    vestiging_ids = {}
    for naam, adres in VESTIGINGEN:
        cur = conn.execute(
            "INSERT INTO vestigingen (naam, adres) VALUES (?, ?)",
            (naam, adres)
        )
        vestiging_ids[naam] = cur.lastrowid
        print(f'  {naam} (id={cur.lastrowid})')
    print()

    # 2. Discover clusters from data
    print('Clusters detecteren uit kluisjes data...')
    cluster_prefixes = {}  # prefix -> set of kluis_codes (just for counting)
    for mk in mag_kluisjes:
        code = mk['kluis_code'].strip()
        if not code:
            continue
        prefix = get_prefix(code)
        if prefix:
            if prefix not in cluster_prefixes:
                cluster_prefixes[prefix] = 0
            cluster_prefixes[prefix] += 1

    # Create clusters
    cluster_ids = {}  # prefix -> cluster_id
    for prefix in sorted(cluster_prefixes.keys()):
        vest_key = get_vestiging_key(prefix)
        if not vest_key:
            print(f'  SKIP: prefix {prefix} heeft geen vestiging mapping')
            continue
        vest_id = vestiging_ids[vest_key]
        count = cluster_prefixes[prefix]
        cur = conn.execute(
            "INSERT INTO clusters (vestiging_id, naam, standaard_borg) VALUES (?, ?, ?)",
            (vest_id, f'Cluster {prefix}', 10.0)
        )
        cluster_ids[prefix] = cur.lastrowid
        print(f'  Cluster {prefix} -> vestiging {vest_key} (id={cur.lastrowid}, {count} kluisjes)')
    print()

    # 3. Import kluisjes + toewijzingen
    print('Kluisjes importeren...')
    created = 0
    assigned = 0
    skipped = 0

    for mk in mag_kluisjes:
        code = mk['kluis_code'].strip()
        if not code:
            skipped += 1
            continue

        prefix = get_prefix(code)
        vest_key = get_vestiging_key(prefix)
        if not vest_key or prefix not in cluster_ids:
            skipped += 1
            continue

        vest_id = vestiging_ids[vest_key]
        clust_id = cluster_ids[prefix]
        sleutel = mk.get('sleutel', '')
        omschrijving = mk.get('omschrijving', '')

        # Insert kluisje
        cur = conn.execute(
            'INSERT INTO kluisjes (cluster_id, vestiging_id, kluisnummer, sleutelnummer, locatie, status) VALUES (?, ?, ?, ?, ?, ?)',
            (clust_id, vest_id, code, sleutel, omschrijving, 'vrij')
        )
        kluisje_id = cur.lastrowid
        created += 1

        # Check for active student assignment
        stamnr = mk.get('stamnr', '').strip()
        if not stamnr:
            continue

        leerling = leerling_map.get(stamnr)
        if not leerling:
            continue

        # Parse dates
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

        if not datum_van:
            continue

        naam = leerling.get('naam', f"{leerling.get('achternaam', '')}, {leerling.get('roepnaam', '')}")
        klas = leerling.get('klas', '')

        conn.execute('''
            INSERT INTO toewijzingen
            (kluisje_id, leerling_stamnr, leerling_naam, leerling_klas,
             periode_van, periode_tot, borgbedrag, borg_betaald, actief, aangemaakt_door)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, ?)
        ''', (
            kluisje_id, stamnr, naam, klas,
            datum_van, datum_tot or datum_van, borg,
            1 if borg > 0 else 0,
            'Magister Import',
        ))
        conn.execute(
            "UPDATE kluisjes SET status = 'uitgeleend', updated_at = datetime('now') WHERE id = ?",
            (kluisje_id,)
        )
        assigned += 1

    conn.commit()

    print()
    print('=== IMPORT RESULTAAT ===')
    print(f'Vestigingen: {len(vestiging_ids)}')
    print(f'Clusters:    {len(cluster_ids)}')
    print(f'Kluisjes:    {created}')
    print(f'Toewijzingen:{assigned}')
    print(f'Skipped:     {skipped}')
    print(f'Totaal Mag:  {len(mag_kluisjes)}')

    # Summary per vestiging
    print()
    print('=== PER VESTIGING ===')
    for vest_naam, vest_id in vestiging_ids.items():
        row = conn.execute(
            'SELECT COUNT(*) as total FROM kluisjes WHERE vestiging_id = ? AND verwijderd = 0',
            (vest_id,)
        ).fetchone()
        row2 = conn.execute(
            "SELECT COUNT(*) as uit FROM kluisjes WHERE vestiging_id = ? AND status = 'uitgeleend' AND verwijderd = 0",
            (vest_id,)
        ).fetchone()
        print(f'  {vest_naam}: {row["total"]} kluisjes, {row2["uit"]} uitgeleend')

    conn.close()
    print()
    print('Done!')


if __name__ == '__main__':
    main()
