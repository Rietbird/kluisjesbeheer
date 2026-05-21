#!/usr/bin/env python3
"""
Seed een lege demo-database met neutrale dummy-data voor screenshot-generatie.
Gebruikt NIET de productie-DB; schrijft naar een aparte path die je meegeeft.

Run:
    python seed_demo.py demo.db

Daarna start je de backend met deze DB:
    set KLUISJES_DB=demo.db
    set FLASK_ENV=development
    python app.py
"""
import os
import sys
import sqlite3
from datetime import date, timedelta

from db import init_db

# Neutrale dummy-leerlingen — bewust niet-ISK-achtig
LEERLINGEN = [
    ('100001', 'Anna B.',       'B1A'),
    ('100002', 'Bram C.',       'B1A'),
    ('100003', 'Carla D.',      'B1A'),
    ('100004', 'Daan E.',       'B1A'),
    ('100005', 'Eva F.',        'B1A'),
    ('100006', 'Finn G.',       'B1B'),
    ('100007', 'Gita H.',       'B1B'),
    ('100008', 'Hugo I.',       'B1B'),
    ('100009', 'Iris J.',       'B1B'),
    ('100010', 'Jens K.',       'B1B'),
    ('100011', 'Kim L.',        'B2A'),
    ('100012', 'Lars M.',       'B2A'),
    ('100013', 'Mila N.',       'B2A'),
    ('100014', 'Noah O.',       'B2A'),
    ('100015', 'Olivia P.',     'B2A'),
    ('100016', 'Pim Q.',        'B2B'),
    ('100017', 'Quinn R.',      'B2B'),
    ('100018', 'Roos S.',       'B2B'),
    ('100019', 'Sam T.',        'B2B'),
    ('100020', 'Tess U.',       'B2B'),
    ('100021', 'Ulf V.',        'B3A'),
    ('100022', 'Vera W.',       'B3A'),
    ('100023', 'Wout X.',       'B3A'),
    ('100024', 'Xara Y.',       'B3A'),
    ('100025', 'Yuri Z.',       'B3A'),
    ('100026', 'Zoë A.',        'B3B'),
    ('100027', 'Aaron B.',      'B3B'),
    ('100028', 'Bo C.',         'B3B'),
    ('100029', 'Cas D.',        'B3B'),
    ('100030', 'Dina E.',       'B3B'),
]


def seed(db_path):
    # init_db maakt schema + draait migraties
    init_db(db_path)
    db = sqlite3.connect(db_path)
    db.row_factory = sqlite3.Row
    db.execute('PRAGMA foreign_keys = ON')

    # Cleanup voor idempotency
    for t in ('toewijzingen', 'kluisjes', 'clusters', 'vestigingen_klassen',
              'vestigingen_locaties', 'vestigingen', 'leerlingen'):
        try:
            db.execute(f'DELETE FROM {t}')
        except sqlite3.OperationalError:
            pass

    # 3 vestigingen — neutrale namen
    vest_ids = {}
    for naam in ['Hoofdlocatie', 'Dependance Noord', 'Dependance Zuid']:
        cur = db.execute(
            'INSERT INTO vestigingen (naam, borg_actief) VALUES (?, 1)', (naam,)
        )
        vest_ids[naam] = cur.lastrowid

    # 3 clusters per vestiging
    cluster_ids = {}
    for vnaam, vid in vest_ids.items():
        for cnaam in ['Vleugel A', 'Vleugel B', 'Vleugel C']:
            cur = db.execute(
                'INSERT INTO clusters (vestiging_id, naam, standaard_borg) VALUES (?, ?, 10.0)',
                (vid, cnaam)
            )
            cluster_ids[(vnaam, cnaam)] = cur.lastrowid

    # Leerlingen
    for stamnr, naam, klas in LEERLINGEN:
        roep, achter = naam.split(' ', 1) if ' ' in naam else (naam, '')
        db.execute(
            '''INSERT INTO leerlingen
               (stamnr, naam, roepnaam, achternaam, klas, leerjaar, locatie)
               VALUES (?, ?, ?, ?, ?, ?, ?)''',
            (stamnr, naam, roep, achter, klas, klas[1], 'Hoofdlocatie')
        )

    # Klassen per vestiging
    klassen_set = sorted(set(l[2] for l in LEERLINGEN))
    for vnaam, vid in vest_ids.items():
        for k in klassen_set:
            db.execute(
                'INSERT INTO vestigingen_klassen (vestiging_id, klas) VALUES (?, ?)',
                (vid, k)
            )

    # 80 kluisjes per vestiging — verdeeld over de 3 clusters
    today = date.today().isoformat()
    eind = (date.today() + timedelta(days=180)).isoformat()
    kluisje_data = []

    for vnaam, vid in vest_ids.items():
        prefix = {'Hoofdlocatie': 'HL', 'Dependance Noord': 'DN', 'Dependance Zuid': 'DZ'}[vnaam]
        for i in range(1, 81):
            cluster_naam = ['Vleugel A', 'Vleugel B', 'Vleugel C'][(i - 1) // 27]
            cid = cluster_ids[(vnaam, cluster_naam)]
            kluisnr = f'{prefix}-{i:03d}'
            sleutelnr = f'K{i:04d}'
            kluisje_data.append((cid, vid, kluisnr, sleutelnr, vnaam))

    kluisje_ids = []
    for cid, vid, kluisnr, sleutelnr, vnaam in kluisje_data:
        cur = db.execute(
            '''INSERT INTO kluisjes
               (cluster_id, vestiging_id, kluisnummer, sleutelnummer, locatie, status, is_defect)
               VALUES (?, ?, ?, ?, ?, ?, ?)''',
            (cid, vid, kluisnr, sleutelnr, vnaam, 'vrij', 0)
        )
        kluisje_ids.append(cur.lastrowid)

    # Eerste vestiging: ~50% uitgeleend met leerlingen
    # Maak in de eerste 30 kluisjes van Hoofdlocatie toewijzingen aan de 30 leerlingen
    hl_kluisjes = [k for (cid, vid, *_), k in zip(kluisje_data, kluisje_ids)
                   if vid == vest_ids['Hoofdlocatie']][:30]
    for klid, (stamnr, naam, klas) in zip(hl_kluisjes, LEERLINGEN):
        db.execute(
            'UPDATE kluisjes SET status = ? WHERE id = ?', ('uitgeleend', klid)
        )
        db.execute(
            '''INSERT INTO toewijzingen
               (kluisje_id, leerling_stamnr, leerling_naam, leerling_klas,
                periode_van, periode_tot, borgbedrag, borg_betaald, actief, aangemaakt_door)
               VALUES (?, ?, ?, ?, ?, ?, 10.0, 1, 1, ?)''',
            (klid, stamnr, naam, klas, today, eind, 'Demo seed')
        )

    # 1 defect kluisje in Hoofdlocatie (vrij)
    db.execute(
        "UPDATE kluisjes SET is_defect = 1, defect_sinds = datetime('now') WHERE id = ?",
        (hl_kluisjes[-1] + 1 if hl_kluisjes else kluisje_ids[40],)
    )

    # 1 defect + uitgeleend kluisje
    if hl_kluisjes:
        db.execute(
            "UPDATE kluisjes SET is_defect = 1, defect_sinds = datetime('now', '-3 days') WHERE id = ?",
            (hl_kluisjes[5],)
        )

    # 1 sleutel-niet-ingeleverd (oude toewijzing, niet actief, sleutel_ingeleverd=0)
    if hl_kluisjes:
        oude_kluis = hl_kluisjes[10]
        db.execute('UPDATE kluisjes SET status = ? WHERE id = ?', ('vrij', oude_kluis))
        db.execute('UPDATE toewijzingen SET actief = 0 WHERE kluisje_id = ?', (oude_kluis,))
        db.execute(
            '''INSERT INTO toewijzingen
               (kluisje_id, leerling_stamnr, leerling_naam, leerling_klas,
                periode_van, periode_tot, borgbedrag, borg_betaald, borg_teruggestort,
                sleutel_ingeleverd, einddatum, actief, aangemaakt_door)
               VALUES (?, ?, ?, ?, ?, ?, 10.0, 1, 1, 0, ?, 0, ?)''',
            (oude_kluis, '099999', 'Oud-leerling X.', 'B3A',
             (date.today() - timedelta(days=365)).isoformat(),
             (date.today() - timedelta(days=14)).isoformat(),
             (date.today() - timedelta(days=14)).isoformat(),
             'Demo seed')
        )

    # Instellingen: schoolnaam neutraal
    for k, v in [('schoolNaam', 'Demoschool'), ('schoolSubtitel', 'Kluisjesbeheer'),
                 ('schoolKleur', '#FF8200')]:
        db.execute(
            'INSERT OR REPLACE INTO instellingen (key, value) VALUES (?, ?)', (k, v)
        )

    db.commit()
    db.close()

    # Counts
    db = sqlite3.connect(db_path)
    n_kluisjes = db.execute('SELECT COUNT(*) FROM kluisjes').fetchone()[0]
    n_toewijzingen = db.execute('SELECT COUNT(*) FROM toewijzingen WHERE actief=1').fetchone()[0]
    n_defect = db.execute('SELECT COUNT(*) FROM kluisjes WHERE is_defect=1').fetchone()[0]
    n_leerlingen = db.execute('SELECT COUNT(*) FROM leerlingen').fetchone()[0]
    db.close()
    print(f'Seeded {db_path}: {n_kluisjes} kluisjes, {n_toewijzingen} actief, '
          f'{n_defect} defect, {n_leerlingen} leerlingen, 3 vestigingen.')


if __name__ == '__main__':
    target = sys.argv[1] if len(sys.argv) > 1 else 'demo.db'
    # Verwijder eventuele oude demo.db zodat we schoon beginnen
    if os.path.exists(target):
        os.unlink(target)
    seed(target)
