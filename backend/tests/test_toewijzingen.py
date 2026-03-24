import pytest

@pytest.fixture(autouse=True)
def seed_data(client):
    """Seed vestiging + cluster + 2 kluisjes for toewijzingen tests."""
    client.post('/api/vestigingen', json={'naam': 'HG'})
    client.post('/api/clusters', json={'vestiging_id': 1, 'naam': 'Gang A', 'standaard_borg': 15.0})
    client.post('/api/clusters/1/kluisjes', json={'kluisnummer': 'P001', 'sleutelnummer': 'S-001'})
    client.post('/api/clusters/1/kluisjes', json={'kluisnummer': 'P002', 'sleutelnummer': 'S-002'})

def test_toewijzen(client):
    rv = client.post('/api/kluisjes/1/toewijzen', json={
        'leerling_stamnr': '22001', 'leerling_naam': 'Emma Botter', 'leerling_klas': '2A',
        'periode_van': '2026-01-01', 'periode_tot': '2026-07-31', 'borgbedrag': 15.0, 'borg_betaald': True
    })
    assert rv.status_code == 201
    assert rv.get_json()['actief'] == 1
    # Kluisje status should be 'uitgeleend'
    kluisje = client.get('/api/kluisjes/1').get_json()
    assert kluisje['status'] == 'uitgeleend'

def test_cannot_assign_occupied_kluisje(client):
    client.post('/api/kluisjes/1/toewijzen', json={
        'leerling_stamnr': '22001', 'leerling_naam': 'Emma', 'leerling_klas': '2A',
        'periode_van': '2026-01-01', 'periode_tot': '2026-07-31', 'borgbedrag': 15.0
    })
    rv = client.post('/api/kluisjes/1/toewijzen', json={
        'leerling_stamnr': '22002', 'leerling_naam': 'Jan', 'leerling_klas': '3B',
        'periode_van': '2026-01-01', 'periode_tot': '2026-07-31', 'borgbedrag': 15.0
    })
    assert rv.status_code == 409

def test_beeindigen(client):
    client.post('/api/kluisjes/1/toewijzen', json={
        'leerling_stamnr': '22001', 'leerling_naam': 'Emma', 'leerling_klas': '2A',
        'periode_van': '2026-01-01', 'periode_tot': '2026-07-31', 'borgbedrag': 15.0
    })
    rv = client.post('/api/toewijzingen/1/beeindigen', json={
        'sleutel_ingeleverd': True, 'borg_teruggestort': True, 'einddatum': '2026-03-24'
    })
    assert rv.status_code == 200
    assert rv.get_json()['actief'] == 0
    # Kluisje should be vrij again
    kluisje = client.get('/api/kluisjes/1').get_json()
    assert kluisje['status'] == 'vrij'

def test_beeindigen_without_key(client):
    client.post('/api/kluisjes/1/toewijzen', json={
        'leerling_stamnr': '22001', 'leerling_naam': 'Emma', 'leerling_klas': '2A',
        'periode_van': '2026-01-01', 'periode_tot': '2026-07-31', 'borgbedrag': 15.0
    })
    rv = client.post('/api/toewijzingen/1/beeindigen', json={
        'sleutel_ingeleverd': False, 'borg_teruggestort': False, 'einddatum': '2026-03-24'
    })
    assert rv.status_code == 200
    assert rv.get_json()['sleutel_ingeleverd'] == 0

def test_geschiedenis(client):
    client.post('/api/kluisjes/1/toewijzen', json={
        'leerling_stamnr': '22001', 'leerling_naam': 'Emma', 'leerling_klas': '2A',
        'periode_van': '2026-01-01', 'periode_tot': '2026-07-31', 'borgbedrag': 15.0
    })
    client.post('/api/toewijzingen/1/beeindigen', json={
        'sleutel_ingeleverd': True, 'borg_teruggestort': True, 'einddatum': '2026-03-24'
    })
    rv = client.get('/api/kluisjes/1/geschiedenis')
    assert rv.status_code == 200
    assert len(rv.get_json()) == 1
    assert rv.get_json()[0]['leerling_naam'] == 'Emma'

def test_bulk_toewijzen(client):
    rv = client.post('/api/toewijzingen/bulk', json={
        'toewijzingen': [
            {'kluisje_id': 1, 'leerling_stamnr': '22001', 'leerling_naam': 'Emma', 'leerling_klas': '2A'},
            {'kluisje_id': 2, 'leerling_stamnr': '22002', 'leerling_naam': 'Jan', 'leerling_klas': '3B'},
        ],
        'periode_van': '2026-01-01', 'periode_tot': '2026-07-31', 'borgbedrag': 15.0
    })
    assert rv.status_code == 201
    assert rv.get_json()['assigned'] == 2

def test_delete_vestiging_blocked_with_active_toewijzing(client):
    """Cross-entity test: vestiging cannot be deleted when active toewijzingen exist."""
    client.post('/api/kluisjes/1/toewijzen', json={
        'leerling_stamnr': '22001', 'leerling_naam': 'Test', 'leerling_klas': '2A',
        'periode_van': '2026-01-01', 'periode_tot': '2026-07-31', 'borgbedrag': 15.0
    })
    rv = client.delete('/api/vestigingen/1')
    assert rv.status_code == 409
