import pytest

@pytest.fixture(autouse=True)
def seed_data(client):
    """Seed vestiging + cluster + 3 kluisjes for dashboard tests."""
    client.post('/api/vestigingen', json={'naam': 'HG'})
    client.post('/api/clusters', json={'vestiging_id': 1, 'naam': 'Gang A', 'standaard_borg': 15.0})
    client.post('/api/clusters/1/kluisjes', json={'kluisnummer': 'P001', 'sleutelnummer': 'S-001'})
    client.post('/api/clusters/1/kluisjes', json={'kluisnummer': 'P002', 'sleutelnummer': 'S-002'})
    client.post('/api/clusters/1/kluisjes', json={'kluisnummer': 'P003', 'sleutelnummer': 'S-003'})

def test_dashboard_stats(client):
    # Assign P001
    client.post('/api/kluisjes/1/toewijzen', json={
        'leerling_stamnr': '22001', 'leerling_naam': 'Emma', 'leerling_klas': '2A',
        'periode_van': '2026-01-01', 'periode_tot': '2026-07-31', 'borgbedrag': 15.0
    })
    # Mark P003 as defect (apart van huurstatus)
    client.put('/api/kluisjes/3', json={'is_defect': True})

    rv = client.get('/api/dashboard/stats')
    assert rv.status_code == 200
    stats = rv.get_json()
    assert len(stats) == 1  # one vestiging
    assert stats[0]['totaal'] == 3
    assert stats[0]['uitgeleend'] == 1
    # Alleen P002: 'Vrij' op de kaart betekent uitleenbaar, en een defect
    # kluisje kun je niet uitgeven. Het telt in de kolom Defect ernaast.
    assert stats[0]['vrij'] == 1
    assert stats[0]['defect'] == 1

def test_dashboard_sleutel_niet_ingeleverd(client):
    """Verify sleutel_niet_ingeleverd count appears in stats."""
    # Assign P001
    client.post('/api/kluisjes/1/toewijzen', json={
        'leerling_stamnr': '22001', 'leerling_naam': 'Emma', 'leerling_klas': '2A',
        'periode_van': '2026-01-01', 'periode_tot': '2026-07-31', 'borgbedrag': 15.0
    })
    # End rental WITHOUT key return
    client.post('/api/toewijzingen/1/beeindigen', json={
        'sleutel_ingeleverd': False, 'borg_teruggestort': False, 'einddatum': '2026-03-24'
    })
    rv = client.get('/api/dashboard/stats')
    stats = rv.get_json()
    assert stats[0]['sleutel_niet_ingeleverd'] == 1

def test_rapport_toewijzingen_gebruikt_live_klas(client, db):
    """Rapport toont de live klas als de toewijzing-snapshot leeg is."""
    client.post('/api/kluisjes/1/toewijzen', json={
        'leerling_stamnr': '500', 'leerling_naam': 'Dirk', 'leerling_klas': '',
        'periode_van': '2026-01-01', 'periode_tot': '2026-07-31', 'borgbedrag': 0})
    db.execute("INSERT INTO leerlingen (stamnr, naam, klas) VALUES ('500', 'Dirk', '4VWO')")
    db.commit()
    rv = client.get('/api/dashboard/rapport/preview?type=toewijzingen&vestiging_id=1')
    assert rv.status_code == 200
    assert 'Klas: 4VWO' in rv.get_data(as_text=True)

def test_klas_rapport_preview_met_en_zonder(client, db):
    # Eén leerling MET kluisje in klas 2A
    client.post('/api/kluisjes/1/toewijzen', json={
        'leerling_stamnr': '10', 'leerling_naam': 'Eva Met', 'leerling_klas': '2A',
        'periode_van': '2026-01-01', 'periode_tot': '2026-07-31', 'borgbedrag': 0})
    # Eén leerling ZONDER kluisje in klas 2A (alleen in leerlingen-tabel)
    db.execute("INSERT INTO leerlingen (stamnr, naam, klas) VALUES ('11', 'Finn Zonder', '2A')")
    db.commit()
    rv = client.get('/api/dashboard/rapport/preview?type=klas&vestiging_id=1')
    body = rv.get_data(as_text=True)
    assert rv.status_code == 200
    assert 'Eva Met' in body
    assert 'Finn Zonder' in body
    assert 'Klas: 2A' in body

def test_klas_rapport_filtert_op_klas(client, db):
    client.post('/api/kluisjes/1/toewijzen', json={
        'leerling_stamnr': '10', 'leerling_naam': 'Eva 2A', 'leerling_klas': '2A',
        'periode_van': '2026-01-01', 'periode_tot': '2026-07-31', 'borgbedrag': 0})
    client.post('/api/kluisjes/2/toewijzen', json={
        'leerling_stamnr': '20', 'leerling_naam': 'Gijs 3B', 'leerling_klas': '3B',
        'periode_van': '2026-01-01', 'periode_tot': '2026-07-31', 'borgbedrag': 0})
    rv = client.get('/api/dashboard/rapport/preview?type=klas&vestiging_id=1&klas=2A')
    body = rv.get_data(as_text=True)
    assert 'Eva 2A' in body
    assert 'Gijs 3B' not in body

def test_klas_rapport_pdf_download(client):
    client.post('/api/kluisjes/1/toewijzen', json={
        'leerling_stamnr': '10', 'leerling_naam': 'Eva', 'leerling_klas': '2A',
        'periode_van': '2026-01-01', 'periode_tot': '2026-07-31', 'borgbedrag': 0})
    rv = client.get('/api/dashboard/rapport?type=klas&vestiging_id=1')
    assert rv.status_code == 200
    assert rv.mimetype == 'application/pdf'
    assert rv.get_data().startswith(b'%PDF')
