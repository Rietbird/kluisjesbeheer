import pytest, io

@pytest.fixture(autouse=True)
def seed_data(client):
    """Seed vestiging + cluster for kluisjes tests."""
    client.post('/api/vestigingen', json={'naam': 'HG'})
    client.post('/api/clusters', json={'vestiging_id': 1, 'naam': 'Gang A', 'standaard_borg': 15.0})

def test_create_kluisje(client):
    rv = client.post('/api/clusters/1/kluisjes', json={'kluisnummer': 'P001', 'sleutelnummer': 'S-001'})
    assert rv.status_code == 201
    assert rv.get_json()['kluisnummer'] == 'P001'
    assert rv.get_json()['status'] == 'vrij'

def test_list_kluisjes_by_cluster(client):
    client.post('/api/clusters/1/kluisjes', json={'kluisnummer': 'P001', 'sleutelnummer': 'S-001'})
    client.post('/api/clusters/1/kluisjes', json={'kluisnummer': 'P002', 'sleutelnummer': 'S-002'})
    rv = client.get('/api/clusters/1/kluisjes')
    assert len(rv.get_json()) == 2

def test_search_kluisjes(client):
    client.post('/api/clusters/1/kluisjes', json={'kluisnummer': 'P001', 'sleutelnummer': 'S-001'})
    client.post('/api/clusters/1/kluisjes', json={'kluisnummer': 'P002', 'sleutelnummer': 'S-002'})
    rv = client.get('/api/kluisjes?q=P001&vestiging_id=1')
    data = rv.get_json()
    assert len(data) == 1
    assert data[0]['kluisnummer'] == 'P001'

def test_search_filter_op_klas_snapshot(client):
    """Filter op klas die op de toewijzing zelf staat (snapshot)."""
    client.post('/api/clusters/1/kluisjes', json={'kluisnummer': 'P001', 'sleutelnummer': 'S-001'})
    client.post('/api/clusters/1/kluisjes', json={'kluisnummer': 'P002', 'sleutelnummer': 'S-002'})
    client.post('/api/kluisjes/1/toewijzen', json={
        'leerling_stamnr': '100', 'leerling_naam': 'Anna', 'leerling_klas': '2A',
        'periode_van': '2026-01-01', 'periode_tot': '2026-07-31', 'borgbedrag': 0
    })
    client.post('/api/kluisjes/2/toewijzen', json={
        'leerling_stamnr': '200', 'leerling_naam': 'Bram', 'leerling_klas': '3B',
        'periode_van': '2026-01-01', 'periode_tot': '2026-07-31', 'borgbedrag': 0
    })
    rv = client.get('/api/kluisjes?vestiging_id=1&klas=2A')
    data = rv.get_json()
    assert rv.status_code == 200
    assert [d['kluisnummer'] for d in data] == ['P001']

def test_search_filter_op_klas_live_fallback(client, db):
    """Lege snapshot-klas -> klas komt uit de live leerlingen-tabel."""
    client.post('/api/clusters/1/kluisjes', json={'kluisnummer': 'P001', 'sleutelnummer': 'S-001'})
    client.post('/api/kluisjes/1/toewijzen', json={
        'leerling_stamnr': '300', 'leerling_naam': 'Cara', 'leerling_klas': '',
        'periode_van': '2026-01-01', 'periode_tot': '2026-07-31', 'borgbedrag': 0
    })
    db.execute("INSERT INTO leerlingen (stamnr, naam, klas) VALUES ('300', 'Cara', 'M2HV1')")
    db.commit()
    rv = client.get('/api/kluisjes?vestiging_id=1&klas=M2HV1')
    data = rv.get_json()
    assert [d['kluisnummer'] for d in data] == ['P001']

def test_klassen_per_vestiging(client):
    client.post('/api/clusters/1/kluisjes', json={'kluisnummer': 'P001'})
    client.post('/api/clusters/1/kluisjes', json={'kluisnummer': 'P002'})
    client.post('/api/clusters/1/kluisjes', json={'kluisnummer': 'P003'})
    client.post('/api/kluisjes/1/toewijzen', json={
        'leerling_stamnr': '1', 'leerling_naam': 'A', 'leerling_klas': '3B',
        'periode_van': '2026-01-01', 'periode_tot': '2026-07-31', 'borgbedrag': 0})
    client.post('/api/kluisjes/2/toewijzen', json={
        'leerling_stamnr': '2', 'leerling_naam': 'B', 'leerling_klas': '2A',
        'periode_van': '2026-01-01', 'periode_tot': '2026-07-31', 'borgbedrag': 0})
    # P003 blijft vrij -> levert geen klas
    rv = client.get('/api/vestigingen/1/klassen')
    assert rv.status_code == 200
    assert rv.get_json() == ['2A', '3B']  # uniek + gesorteerd, geen lege

def test_update_kluisje(client):
    client.post('/api/clusters/1/kluisjes', json={'kluisnummer': 'P001', 'sleutelnummer': 'S-001'})
    rv = client.put('/api/kluisjes/1', json={'sleutelnummer': 'S-999', 'opmerkingen': 'Test notitie'})
    assert rv.status_code == 200
    assert rv.get_json()['sleutelnummer'] == 'S-999'

def test_soft_delete_kluisje(client):
    client.post('/api/clusters/1/kluisjes', json={'kluisnummer': 'P001', 'sleutelnummer': 'S-001'})
    rv = client.delete('/api/kluisjes/1')
    assert rv.status_code == 200
    # Should not appear in listings
    rv = client.get('/api/clusters/1/kluisjes')
    assert len(rv.get_json()) == 0

def test_csv_import(client):
    csv_data = "kluisnummer;sleutelnummer;locatie\nP010;S-010;Gang B\nP011;S-011;Gang B\n"
    rv = client.post('/api/kluisjes/import',
        data={'cluster_id': '1', 'file': (io.BytesIO(csv_data.encode('utf-8')), 'import.csv')},
        content_type='multipart/form-data')
    assert rv.status_code == 201
    assert rv.get_json()['imported'] == 2

def test_csv_import_rollback_on_duplicate(client):
    client.post('/api/clusters/1/kluisjes', json={'kluisnummer': 'P001', 'sleutelnummer': 'S-001'})
    csv_data = "kluisnummer;sleutelnummer;locatie\nP002;S-002;Gang B\nP001;S-003;Gang B\n"
    rv = client.post('/api/kluisjes/import',
        data={'cluster_id': '1', 'file': (io.BytesIO(csv_data.encode('utf-8')), 'import.csv')},
        content_type='multipart/form-data')
    assert rv.status_code == 400
    # P002 should NOT be imported (rollback)
    rv = client.get('/api/clusters/1/kluisjes')
    assert len(rv.get_json()) == 1  # only original P001


from api_kluisjes import _normaliseer_kluisnummer

def test_normaliseer_padt_numeriek_blok():
    assert _normaliseer_kluisnummer('MO-7', 4) == 'MO-0007'

def test_normaliseer_idempotent():
    assert _normaliseer_kluisnummer('BL-001', 3) == 'BL-001'

def test_normaliseer_behoudt_suffix():
    assert _normaliseer_kluisnummer('MO-7B', 4) == 'MO-0007B'

def test_normaliseer_zonder_getal_ongewijzigd():
    assert _normaliseer_kluisnummer('XYZ', 4) == 'XYZ'

def test_normaliseer_lege_invoer():
    assert _normaliseer_kluisnummer('', 4) == ''


from api_kluisjes import _analyseer_nummering

def test_analyse_detecteert_krom_en_consistent():
    nummers = ['MO-1', 'MO-10', 'MO-100', 'MO-1000', 'BL-001', 'BL-002']
    res = _analyseer_nummering(nummers)
    mo = next(p for p in res['prefixes'] if p['prefix'] == 'MO-')
    bl = next(p for p in res['prefixes'] if p['prefix'] == 'BL-')
    assert mo['krom'] is True
    assert mo['breedte'] == 4          # hoogste = 1000 -> 4 cijfers
    assert mo['collision'] is False
    assert bl['krom'] is False
    assert res['heeft_krom'] is True
    assert res['heeft_collision'] is False

def test_analyse_detecteert_collision():
    # MO-1 en MO-001 zouden beide MO-001 worden bij breedte 3
    nummers = ['MO-1', 'MO-001', 'MO-50']
    res = _analyseer_nummering(nummers)
    mo = next(p for p in res['prefixes'] if p['prefix'] == 'MO-')
    assert mo['collision'] is True
    assert res['heeft_collision'] is True


def _maak_xlsx(rows, headers):
    import io, openpyxl
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(headers)
    for r in rows:
        ws.append(r)
    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf

def test_preview_geeft_normalisatie_advies(client):
    rows = [[f'MO-{n}'] for n in (1, 10, 100, 1000)]
    xlsx = _maak_xlsx(rows, ['omschrijving kluisje'])
    rv = client.post('/api/kluisjes/import/preview',
        data={'file': (xlsx, 'k.xlsx')}, content_type='multipart/form-data')
    assert rv.status_code == 200
    body = rv.get_json()
    assert 'normalisatie' in body
    assert body['normalisatie']['heeft_krom'] is True
    assert body['normalisatie']['heeft_collision'] is False
    mo = next(p for p in body['normalisatie']['prefixes'] if p['prefix'] == 'MO-')
    assert mo['breedte'] == 4


def test_import_normaliseert_bij_vlag(client):
    rows = [['MO-1'], ['MO-10'], ['MO-100']]
    xlsx = _maak_xlsx(rows, ['omschrijving kluisje'])
    rv = client.post('/api/kluisjes/import', data={
        'file': (xlsx, 'k.xlsx'),
        'vestiging_id': '1',
        'normaliseer': '1',
    }, content_type='multipart/form-data')
    assert rv.status_code == 201
    kl = client.get('/api/kluisjes?vestiging_id=1').get_json()
    nummers = sorted(k['kluisnummer'] for k in kl)
    assert nummers == ['MO-001', 'MO-010', 'MO-100']

def test_import_normaliseert_niet_zonder_vlag(client):
    rows = [['MO-1'], ['MO-10']]
    xlsx = _maak_xlsx(rows, ['omschrijving kluisje'])
    rv = client.post('/api/kluisjes/import', data={
        'file': (xlsx, 'k.xlsx'),
        'vestiging_id': '1',
    }, content_type='multipart/form-data')
    assert rv.status_code == 201
    kl = client.get('/api/kluisjes?vestiging_id=1').get_json()
    nummers = sorted(k['kluisnummer'] for k in kl)
    assert nummers == ['MO-1', 'MO-10']

def test_extract_prefix_scheme_variants():
    from api_kluisjes import _extract_prefix
    # The prefix is the leading run of letters; everything from the first digit
    # on is the locker id. Works with or without a separator.
    assert _extract_prefix('MO-0001') == 'MO'
    assert _extract_prefix('BL-001') == 'BL'
    assert _extract_prefix('O053A') == 'O'    # letter + digits + trailing letter
    assert _extract_prefix('X001') == 'X'     # letter + digits, no trailing letter
    assert _extract_prefix('Z01-A') == 'Z'    # letter + digits + separator (the tricky one)
    assert _extract_prefix('Z417E') == 'Z'
    assert _extract_prefix('123') == 'Overig'  # no leading letter

def test_import_normaliseert_twee_prefixes_gemixt(client):
    rows = [['MO-1'], ['MO-10'], ['MO-100'], ['BL-001'], ['BL-002'], ['BL-050']]
    xlsx = _maak_xlsx(rows, ['omschrijving kluisje'])
    rv = client.post('/api/kluisjes/import', data={
        'file': (xlsx, 'k.xlsx'), 'vestiging_id': '1', 'normaliseer': '1',
    }, content_type='multipart/form-data')
    assert rv.status_code == 201
    nummers = sorted(k['kluisnummer'] for k in client.get('/api/kluisjes?vestiging_id=1').get_json())
    assert nummers == ['BL-001', 'BL-002', 'BL-050', 'MO-001', 'MO-010', 'MO-100']
