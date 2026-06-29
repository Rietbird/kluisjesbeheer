import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


def test_nieuw_voor_schooljaar_column_exists(db):
    cols = [r[1] for r in db.execute("PRAGMA table_info(leerlingen)").fetchall()]
    assert 'nieuw_voor_schooljaar' in cols


from leerling_sync import import_voorinschrijvingen, sync_leerlingen_to_db


def _vi(stamnr, naam='Brugklasser', **kw):
    return dict(stamnr=stamnr, naam=naam, locatie='Hoofd', **kw)


def _ll(stamnr, naam='Naam', klas='1A'):
    return dict(stamnr=stamnr, naam=naam, roepnaam='', tussenvoegsel='',
               achternaam=naam, email='', klas=klas, leerjaar='1', studie='', locatie='Hoofd')


def test_import_sets_flag_klasloos_no_vertrokken(db):
    res = import_voorinschrijvingen(db, [_vi('9001')], '2026-2027')
    row = db.execute("SELECT klas, nieuw_voor_schooljaar, vertrokken_op, locatie "
                     "FROM leerlingen WHERE stamnr='9001'").fetchone()
    assert row['klas'] == ''
    assert row['nieuw_voor_schooljaar'] == '2026-2027'
    assert row['vertrokken_op'] is None
    assert row['locatie'] == 'Hoofd'
    assert res['imported'] == 1


def test_import_does_not_mark_existing_vertrokken(db):
    sync_leerlingen_to_db(db, [_ll('1'), _ll('2')])
    import_voorinschrijvingen(db, [_vi('9001')], '2026-2027')
    n = db.execute("SELECT COUNT(*) AS n FROM leerlingen WHERE vertrokken_op IS NOT NULL").fetchone()['n']
    assert n == 0


def test_import_preserves_klas_of_existing_student(db):
    sync_leerlingen_to_db(db, [_ll('1', klas='3A')])
    import_voorinschrijvingen(db, [dict(stamnr='1', naam='X', locatie='Hoofd')], '2026-2027')
    assert db.execute("SELECT klas FROM leerlingen WHERE stamnr='1'").fetchone()['klas'] == '3A'


def test_voorinschrijving_protected_before_rollover(db):
    # doel-schooljaar ver in de toekomst -> altijd "vóór 1-8"
    import_voorinschrijvingen(db, [_vi('9001')], '2099-2100')
    # gewone sync zonder 9001 mag 'm NIET vertrokken-markeren
    sync_leerlingen_to_db(db, [_ll('1'), _ll('2')])
    assert db.execute("SELECT vertrokken_op FROM leerlingen WHERE stamnr='9001'").fetchone()['vertrokken_op'] is None


def test_flag_cleared_and_klas_set_when_active(db):
    import_voorinschrijvingen(db, [_vi('9001')], '2026-2027')
    # leerling komt nu actief binnen met echte klas
    sync_leerlingen_to_db(db, [_ll('9001', klas='1A'), _ll('1')])
    row = db.execute("SELECT klas, nieuw_voor_schooljaar FROM leerlingen WHERE stamnr='9001'").fetchone()
    assert row['nieuw_voor_schooljaar'] is None
    assert row['klas'] == '1A'


def test_noshow_marked_vertrokken_after_rollover(db):
    # doel-schooljaar in het verleden -> bescherming is vervallen
    import_voorinschrijvingen(db, [_vi('9001')], '2000-2001')
    sync_leerlingen_to_db(db, [_ll('1'), _ll('2')])
    assert db.execute("SELECT vertrokken_op FROM leerlingen WHERE stamnr='9001'").fetchone()['vertrokken_op'] is not None


def _seed_kluisje_met_toewijzing(db, stamnr, snapshot_klas=''):
    db.execute("INSERT INTO vestigingen (id, naam) VALUES (1, 'Hoofd')")
    db.execute("INSERT INTO clusters (id, vestiging_id, naam) VALUES (1, 1, 'C1')")
    db.execute("INSERT INTO kluisjes (id, cluster_id, vestiging_id, kluisnummer, status) "
               "VALUES (1, 1, 1, 'A001', 'uitgeleend')")
    db.execute("INSERT INTO toewijzingen (kluisje_id, leerling_stamnr, leerling_naam, leerling_klas, "
               "periode_van, periode_tot, actief) VALUES (1, ?, 'Brug', ?, '2026-08-01', '2027-07-31', 1)",
               (stamnr, snapshot_klas))
    db.commit()


def test_actieve_toewijzingen_effective_klas_and_flag(client, db, db_path):
    # voorinschrijving (klasloos) + lege snapshot, daarna krijgt de leerling z'n live klas
    import_voorinschrijvingen(db, [_vi('9001')], '2026-2027')
    _seed_kluisje_met_toewijzing(db, '9001', snapshot_klas='')
    db.execute("UPDATE leerlingen SET klas='1A' WHERE stamnr='9001'")  # alsof 1-8 voorbij is
    db.commit()
    rows = client.get('/api/toewijzingen/actief').get_json()
    row = next(r for r in rows if r['leerling_stamnr'] == '9001')
    assert row['leerling_klas'] == ''                       # snapshot ongewijzigd
    assert row['leerling_klas_effectief'] == '1A'           # valt terug op live klas
    assert row['leerling_nieuw_voor_schooljaar'] == '2026-2027'


def test_import_voorinschrijving_route(client, monkeypatch):
    import magister_client
    captured = {}

    def fake_get_data(layout, parameters=''):
        captured['layout'] = layout
        captured['parameters'] = parameters
        return [
            {'Leerlingnummer': '9001', 'Voornaam': 'Bo', 'Tussenvoegsel': '',
             'Achternaam': 'Jansen', 'Email': '9001@school.nl', 'Locatie': 'Hoofd'},
            {'Leerlingnummer': '9002', 'Voornaam': 'Sam', 'Tussenvoegsel': 'de',
             'Achternaam': 'Vos', 'Email': '9002@school.nl', 'Locatie': 'Hoofd'},
        ]

    monkeypatch.setattr(magister_client.magister, 'get_data', fake_get_data)
    monkeypatch.setattr(magister_client.magister, 'flush_cache', lambda: None)

    resp = client.post('/api/leerlingen/import-voorinschrijving', json={'schooljaar': '2026-2027'})
    assert resp.status_code == 200
    body = resp.get_json()
    assert body['geimporteerd'] == 2
    assert captured['layout'] == 'sql-get-kluisjes-voorinschrijving'
    assert captured['parameters'] == 'peildatum=2026-08-01'

    # end-to-end: vindbaar in de zoek, met vlag, klasloos
    found = client.get('/api/magister/leerlingen?q=Jansen').get_json()
    bo = next(l for l in found if l['stamnr'] == '9001')
    assert bo['nieuw_voor_schooljaar'] == '2026-2027'
    assert bo['naam'] == 'Bo Jansen'
    assert bo['klas'] == ''


def test_import_voorinschrijving_requires_schooljaar(client):
    resp = client.post('/api/leerlingen/import-voorinschrijving', json={})
    assert resp.status_code == 400


def test_get_data_parses_records(monkeypatch):
    import magister_client as mc
    client = mc.MagisterClient(url='http://x', user='u', password='p')
    monkeypatch.setattr(client, '_login', lambda: 'TOKEN')
    xml = (
        '<Response><Result>True</Result><Table><Voorinschrijvingen>'
        '<Voorinschrijving><Leerlingnummer>9001</Leerlingnummer><Voornaam>Bo</Voornaam>'
        '<Tussenvoegsel></Tussenvoegsel><Achternaam>Jansen</Achternaam>'
        '<Locatie>HET ERASMUS vestiging PrO</Locatie></Voorinschrijving>'
        '<Voorinschrijving><Leerlingnummer>9002</Leerlingnummer><Voornaam>Sam</Voornaam>'
        '<Tussenvoegsel>de</Tussenvoegsel><Achternaam>Vos</Achternaam>'
        '<Locatie>HET ERASMUS vestiging PrO</Locatie></Voorinschrijving>'
        '</Voorinschrijvingen></Table></Response>'
    )

    class FakeResp:
        text = xml

    monkeypatch.setattr(mc.requests, 'get', lambda *a, **k: FakeResp())
    records = client.get_data('sql-get-kluisjes-voorinschrijving')
    assert len(records) == 2
    assert records[0]['Leerlingnummer'] == '9001'
    assert records[0]['Voornaam'] == 'Bo'
    assert records[1]['Tussenvoegsel'] == 'de'


# ---------------------------------------------------------------------------
# XLSX fallback import
# ---------------------------------------------------------------------------

import io
import openpyxl


def _xlsx_bytes(rows):
    """Build an in-memory .xlsx from a list of row-tuples."""
    wb = openpyxl.Workbook()
    ws = wb.active
    for r in rows:
        ws.append(r)
    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf


def test_xlsx_import_happy_path(client):
    """Headers + 2 rows (one with numeric leerlingnummer) -> 200, geimporteerd==2."""
    xlsx = _xlsx_bytes([
        ('Leerlingnummer', 'Naam'),
        (19951, 'De Vries Anja'),       # numeric - tests int/float->str conversion
        ('9002', 'Bakker Sam'),
    ])
    resp = client.post(
        '/api/leerlingen/import-voorinschrijving-xlsx',
        data={'schooljaar': '2026-2027', 'file': (xlsx, 'leerlingen.xlsx')},
        content_type='multipart/form-data',
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body['geimporteerd'] == 2
    assert body['schooljaar'] == '2026-2027'
    assert body['bron'] == 'xlsx'

    # end-to-end: student should be findable, klasloos, and flagged
    found = client.get('/api/magister/leerlingen?q=Vries').get_json()
    anja = next((l for l in found if l['stamnr'] == '19951'), None)
    assert anja is not None
    assert anja['nieuw_voor_schooljaar'] == '2026-2027'
    assert anja['klas'] == ''


def test_xlsx_import_synonym_stamnummer(client):
    """'Stamnummer' header is accepted as synonym for 'Leerlingnummer'."""
    xlsx = _xlsx_bytes([
        ('Stamnummer', 'Naam'),
        ('9003', 'Pietersen Kees'),
    ])
    resp = client.post(
        '/api/leerlingen/import-voorinschrijving-xlsx',
        data={'schooljaar': '2026-2027', 'file': (xlsx, 'leerlingen.xlsx')},
        content_type='multipart/form-data',
    )
    assert resp.status_code == 200
    assert resp.get_json()['geimporteerd'] == 1


def test_xlsx_import_missing_file(client):
    """No file uploaded -> 400."""
    resp = client.post(
        '/api/leerlingen/import-voorinschrijving-xlsx',
        data={'schooljaar': '2026-2027'},
        content_type='multipart/form-data',
    )
    assert resp.status_code == 400
    assert 'Bestand' in resp.get_json()['error']


def test_xlsx_import_missing_schooljaar(client):
    """No schooljaar -> 400."""
    xlsx = _xlsx_bytes([('Leerlingnummer', 'Naam'), ('9001', 'Test')])
    resp = client.post(
        '/api/leerlingen/import-voorinschrijving-xlsx',
        data={'file': (xlsx, 'leerlingen.xlsx')},
        content_type='multipart/form-data',
    )
    assert resp.status_code == 400
    assert 'schooljaar' in resp.get_json()['error']


def test_xlsx_import_missing_naam_column(client):
    """Excel without a Naam column -> 400 with the verplicht-message."""
    xlsx = _xlsx_bytes([
        ('Leerlingnummer', 'Klas'),
        ('9001', '1A'),
    ])
    resp = client.post(
        '/api/leerlingen/import-voorinschrijving-xlsx',
        data={'schooljaar': '2026-2027', 'file': (xlsx, 'leerlingen.xlsx')},
        content_type='multipart/form-data',
    )
    assert resp.status_code == 400
    assert 'Leerlingnummer' in resp.get_json()['error']
    assert 'Naam' in resp.get_json()['error']
