#!/usr/bin/env python3
"""Full import from XLSX: create kluisjes and toewijzingen from Magister export.
Assumes vestigingen and clusters already exist."""
import sys
import re
import sqlite3
import openpyxl

XLSX_PATH = sys.argv[1] if len(sys.argv) > 1 else 'Kluisgegevens.xlsx'
DB_PATH = 'kluisjesbeheer.db'

# Prefix -> vestiging naam
PREFIX_TO_VESTIGING = {
    'N': 'MHV', 'V': 'MHV', 'O': 'MHV', 'X': 'MHV',
    'Z': 'Zuid',
    'ISK': 'ISK',
    'P': 'PRO',
}


def get_prefix(kluis_code):
    m = re.match(r'^(ISK\d?|[A-Z])', kluis_code)
    return m.group(1) if m else None


def get_vestiging_key(prefix):
    if prefix and prefix.startswith('ISK'):
        return 'ISK'
    return PREFIX_TO_VESTIGING.get(prefix)


def parse_periode(text):
    """Parse 'van 1-1-2026 tot en met 31-7-2026' into (datum_van, datum_tot)."""
    if not text:
        return None, None
    m = re.match(r'van\s+(\d{1,2}-\d{1,2}-\d{4})\s+tot en met\s+(\d{1,2}-\d{1,2}-\d{4}|-)', str(text).strip())
    if not m:
        return None, None

    def to_iso(d):
        if not d or d == '-':
            return None
        parts = d.split('-')
        if len(parts) == 3:
            return f"{parts[2]}-{parts[1].zfill(2)}-{parts[0].zfill(2)}"
        return d

    return to_iso(m.group(1)), to_iso(m.group(2))


def parse_bedrag(text):
    if not text:
        return 0.0
    text = str(text).replace('\u20ac', '').replace('\ufffd', '').replace('€', '').strip()
    text = text.replace(',', '.').strip()
    try:
        return float(text)
    except (ValueError, TypeError):
        return 0.0


def main():
    print(f"=== VOLLEDIGE IMPORT UIT XLSX ===")
    print(f"XLSX: {XLSX_PATH}")
    print()

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    # Load vestiging/cluster lookup
    vestiging_ids = {}
    for row in conn.execute('SELECT id, naam FROM vestigingen').fetchall():
        vestiging_ids[row['naam']] = row['id']

    cluster_ids = {}
    for row in conn.execute('SELECT id, naam FROM clusters').fetchall():
        # Cluster naam is "Cluster X", "Cluster ISK1", etc.
        prefix = row['naam'].replace('Cluster ', '')
        cluster_ids[prefix] = row['id']

    print(f"Vestigingen: {vestiging_ids}")
    print(f"Clusters: {cluster_ids}")
    print()

    wb = openpyxl.load_workbook(XLSX_PATH, read_only=True)
    ws = wb.active

    created_kluisjes = 0
    created_toewijzingen = 0
    skipped_no_cluster = 0

    for row in ws.iter_rows(min_row=2, values_only=True):
        kluis_code = str(row[1] or '').strip()
        naam = str(row[2] or '').strip()
        stamnr = str(row[3] or '').strip()
        klas = str(row[4] or '').strip()
        periode_text = str(row[5] or '')
        status_text = str(row[6] or '').strip()
        borg_text = str(row[7] or '')
        locatie = str(row[9] or '').strip()
        sleutel = str(row[10] or '').strip()

        if not kluis_code:
            continue

        # Determine vestiging and cluster
        prefix = get_prefix(kluis_code)
        vest_key = get_vestiging_key(prefix)
        if not vest_key or vest_key not in vestiging_ids:
            skipped_no_cluster += 1
            continue

        vest_id = vestiging_ids[vest_key]
        clust_id = cluster_ids.get(prefix)
        if not clust_id:
            skipped_no_cluster += 1
            continue

        # Determine status (defect is een aparte vlag, los van huurstatus)
        db_status = 'vrij'
        db_is_defect = 0
        if status_text == 'Uitgeleend':
            db_status = 'uitgeleend'
        elif status_text == 'Defect':
            db_is_defect = 1

        # Insert kluisje
        borg = parse_bedrag(borg_text)
        cur = conn.execute(
            "INSERT INTO kluisjes (cluster_id, vestiging_id, kluisnummer, sleutelnummer, locatie, status, is_defect, defect_sinds) VALUES (?, ?, ?, ?, ?, ?, ?, CASE WHEN ?=1 THEN datetime('now') ELSE NULL END)",
            (clust_id, vest_id, kluis_code, sleutel, locatie, db_status, db_is_defect, db_is_defect)
        )
        kluisje_id = cur.lastrowid
        created_kluisjes += 1

        # Create toewijzing if uitgeleend and has a name
        if status_text == 'Uitgeleend' and naam:
            datum_van, datum_tot = parse_periode(periode_text)
            if not datum_van:
                datum_van = '2026-01-01'

            conn.execute('''
                INSERT INTO toewijzingen
                (kluisje_id, leerling_stamnr, leerling_naam, leerling_klas,
                 periode_van, periode_tot, borgbedrag, borg_betaald, actief, aangemaakt_door)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, ?)
            ''', (
                kluisje_id, stamnr, naam, klas,
                datum_van, datum_tot or datum_van, borg,
                1 if borg > 0 else 0,
                'XLSX Import',
            ))
            created_toewijzingen += 1

    conn.commit()
    wb.close()

    # Summary per vestiging
    print(f"=== RESULTAAT ===")
    print(f"Kluisjes aangemaakt:     {created_kluisjes}")
    print(f"Toewijzingen aangemaakt: {created_toewijzingen}")
    print(f"Overgeslagen (cluster):  {skipped_no_cluster}")
    print()

    print("Per vestiging:")
    for v_naam, v_id in vestiging_ids.items():
        total = conn.execute('SELECT COUNT(*) as c FROM kluisjes WHERE vestiging_id = ? AND verwijderd = 0', (v_id,)).fetchone()['c']
        uit = conn.execute("SELECT COUNT(*) as c FROM kluisjes WHERE vestiging_id = ? AND status = 'uitgeleend' AND verwijderd = 0", (v_id,)).fetchone()['c']
        print(f"  {v_naam}: {total} kluisjes, {uit} uitgeleend")

    conn.close()
    print("\nDone!")


if __name__ == '__main__':
    main()
