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
    assert stats[0]['vrij'] == 2  # P002 + P003 (defect blijft 'vrij' qua huurstatus)
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
