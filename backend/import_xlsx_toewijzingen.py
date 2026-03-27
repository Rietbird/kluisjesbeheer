#!/usr/bin/env python3
"""Import toewijzingen from the Magister XLSX export for kluisjes that have no active assignment yet."""
import sys
import re
import sqlite3
import openpyxl

XLSX_PATH = sys.argv[1] if len(sys.argv) > 1 else 'Kluisgegevens.xlsx'
DB_PATH = 'kluisjesbeheer.db'


def parse_periode(text):
    """Parse 'van 1-1-2026 tot en met -' into (datum_van, datum_tot)."""
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
    """Parse '€ 10,00' to float."""
    if not text:
        return 0.0
    text = str(text).replace('\u20ac', '').replace('\ufffd', '').replace('€', '').strip()
    text = text.replace(',', '.').strip()
    try:
        return float(text)
    except (ValueError, TypeError):
        return 0.0


def main():
    print(f"=== IMPORT TOEWIJZINGEN UIT XLSX ===")
    print(f"XLSX: {XLSX_PATH}")
    print()

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    wb = openpyxl.load_workbook(XLSX_PATH, read_only=True)
    ws = wb.active

    created = 0
    skipped_not_found = 0
    skipped_already = 0
    skipped_no_name = 0

    for row in ws.iter_rows(min_row=2, values_only=True):
        kluis_code = str(row[1] or '').strip()
        naam = str(row[2] or '').strip()
        stamnr = str(row[3] or '').strip()
        klas = str(row[4] or '').strip()
        periode_text = str(row[5] or '')
        status = str(row[6] or '').strip()
        borg_text = str(row[7] or '')

        if not kluis_code or not naam or status != 'Uitgeleend':
            skipped_no_name += 1
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

        datum_van, datum_tot = parse_periode(periode_text)
        borg = parse_bedrag(borg_text)

        if not datum_van:
            datum_van = '2026-01-01'

        conn.execute('''
            INSERT INTO toewijzingen
            (kluisje_id, leerling_stamnr, leerling_naam, leerling_klas,
             periode_van, periode_tot, borgbedrag, borg_betaald, actief, aangemaakt_door)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, ?)
        ''', (
            kluisje['id'], stamnr, naam, klas,
            datum_van, datum_tot or datum_van, borg,
            1 if borg > 0 else 0,
            'XLSX Import',
        ))

        conn.execute(
            "UPDATE kluisjes SET status = 'uitgeleend', updated_at = datetime('now') WHERE id = ?",
            (kluisje['id'],)
        )
        created += 1

    conn.commit()
    conn.close()
    wb.close()

    print(f"=== RESULTAAT ===")
    print(f"Toewijzingen aangemaakt: {created}")
    print(f"Al een toewijzing:       {skipped_already}")
    print(f"Kluisje niet in DB:      {skipped_not_found}")
    print(f"Geen naam/niet uitgel.:  {skipped_no_name}")


if __name__ == '__main__':
    main()
