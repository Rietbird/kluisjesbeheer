#!/usr/bin/env python3
"""Import toewijzingen from the Magister CSV export for kluisjes that have no active assignment yet."""
import sys
import csv
import re
import sqlite3

CSV_PATH = sys.argv[1] if len(sys.argv) > 1 else 'Kluisgegevens.csv'
DB_PATH = 'kluisjesbeheer.db'

def parse_periode(text):
    """Parse 'van 1-1-2026 tot en met -' into (datum_van, datum_tot)."""
    m = re.match(r'van\s+(\d{1,2}-\d{1,2}-\d{4})\s+tot en met\s+(\d{1,2}-\d{1,2}-\d{4}|-)', text.strip())
    if not m:
        return None, None
    van = m.group(1)
    tot = m.group(2) if m.group(2) != '-' else None

    # Convert d-m-yyyy to yyyy-mm-dd
    def to_iso(d):
        if not d:
            return None
        parts = d.split('-')
        if len(parts) == 3:
            return f"{parts[2]}-{parts[1].zfill(2)}-{parts[0].zfill(2)}"
        return d

    return to_iso(van), to_iso(tot)

def parse_bedrag(text):
    """Parse '€ 10,00' or ' 10,00' to float."""
    text = text.strip().replace('€', '').replace('\u00a0', '').strip()
    text = text.replace(',', '.')
    try:
        return float(text)
    except (ValueError, TypeError):
        return 0.0

def main():
    print(f"=== IMPORT TOEWIJZINGEN UIT CSV ===")
    print(f"CSV: {CSV_PATH}")
    print()

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    # Read CSV
    rows = []
    with open(CSV_PATH, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f, delimiter=';')
        for row in reader:
            rows.append(row)

    print(f"CSV regels: {len(rows)}")

    # Only process rows that have a name (= assigned)
    assigned_rows = [r for r in rows if r.get('Naam', '').strip() and r.get('Status', '').strip() == 'Uitgeleend']
    print(f"Uitgeleend met naam: {len(assigned_rows)}")
    print()

    created = 0
    skipped_not_found = 0
    skipped_already = 0

    for r in assigned_rows:
        kluis_code = r['Kluis'].strip()
        naam = r['Naam'].strip()
        stamnr = r.get('Stamnummer', '').strip()
        klas = r.get('Klas', '').strip()
        periode_text = r.get('Uitleenperiode', '')
        borg_text = r.get('Borgbedrag', '0')
        status = r.get('Status', '').strip()

        if not kluis_code or not naam:
            continue

        # Find kluisje in DB
        kluisje = conn.execute(
            'SELECT id, vestiging_id, status FROM kluisjes WHERE kluisnummer = ? AND verwijderd = 0',
            (kluis_code,)
        ).fetchone()

        if not kluisje:
            skipped_not_found += 1
            continue

        # Check if already has active assignment
        active = conn.execute(
            'SELECT id FROM toewijzingen WHERE kluisje_id = ? AND actief = 1',
            (kluisje['id'],)
        ).fetchone()
        if active:
            skipped_already += 1
            continue

        # Parse data
        datum_van, datum_tot = parse_periode(periode_text)
        borg = parse_bedrag(borg_text)

        if not datum_van:
            # Use a default date if CSV has no valid date
            datum_van = '2026-01-01'

        # Create toewijzing
        conn.execute('''
            INSERT INTO toewijzingen
            (kluisje_id, leerling_stamnr, leerling_naam, leerling_klas,
             periode_van, periode_tot, borgbedrag, borg_betaald, actief, aangemaakt_door)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, ?)
        ''', (
            kluisje['id'], stamnr, naam, klas,
            datum_van, datum_tot or datum_van, borg,
            1 if borg > 0 else 0,
            'CSV Import',
        ))

        # Update kluisje status
        conn.execute(
            "UPDATE kluisjes SET status = 'uitgeleend', updated_at = datetime('now') WHERE id = ?",
            (kluisje['id'],)
        )
        created += 1

    conn.commit()
    conn.close()

    print(f"=== RESULTAAT ===")
    print(f"Toewijzingen aangemaakt: {created}")
    print(f"Kluisje niet gevonden:   {skipped_not_found}")
    print(f"Al een toewijzing:       {skipped_already}")

if __name__ == '__main__':
    main()
