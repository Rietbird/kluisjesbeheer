import pytest

@pytest.fixture(autouse=True)
def seed_data(client):
    """Seed 2 vestigingen + clusters + kluisjes for toewijzingen tests."""
    client.post('/api/vestigingen', json={'naam': 'HG'})          # vestiging 1
    client.post('/api/vestigingen', json={'naam': 'BL'})          # vestiging 2
    client.post('/api/clusters', json={'vestiging_id': 1, 'naam': 'Gang A', 'standaard_borg': 15.0})  # cluster 1
    client.post('/api/clusters', json={'vestiging_id': 2, 'naam': 'Gang B', 'standaard_borg': 15.0})  # cluster 2
    client.post('/api/clusters/1/kluisjes', json={'kluisnummer': 'P001', 'sleutelnummer': 'S-001'})   # kluisje 1, vest 1
    client.post('/api/clusters/1/kluisjes', json={'kluisnummer': 'P002', 'sleutelnummer': 'S-002'})   # kluisje 2, vest 1
    client.post('/api/clusters/2/kluisjes', json={'kluisnummer': 'B001', 'sleutelnummer': 'B-001'})   # kluisje 3, vest 2

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


def _wijs_toe(client, kid, stamnr, naam):
    return client.post(f'/api/kluisjes/{kid}/toewijzen', json={
        'leerling_stamnr': stamnr, 'leerling_naam': naam, 'leerling_klas': '2A',
        'periode_van': '2026-01-01', 'periode_tot': '2026-07-31',
        'borgbedrag': 15.0, 'borg_betaald': True,
    })


def test_ruilen_binnen_vestiging(client):
    a = _wijs_toe(client, 1, '22001', 'Emma Botter').get_json()   # kluisje 1
    b = _wijs_toe(client, 2, '22002', 'Jan de Vries').get_json()  # kluisje 2
    rv = client.post('/api/toewijzingen/ruilen', json={
        'toewijzing_a_id': a['id'], 'toewijzing_b_id': b['id'],
    })
    assert rv.status_code == 200
    body = rv.get_json()
    assert body['a']['kluisje_id'] == 2
    assert body['b']['kluisje_id'] == 1
    assert body['a']['leerling_stamnr'] == '22001'
    assert body['a']['periode_van'] == '2026-01-01'
    assert body['a']['borg_betaald'] == 1
    assert body['a']['actief'] == 1
    assert body['b']['leerling_stamnr'] == '22002'
    assert body['b']['actief'] == 1
    assert client.get('/api/kluisjes/1').get_json()['status'] == 'uitgeleend'
    assert client.get('/api/kluisjes/2').get_json()['status'] == 'uitgeleend'


def test_ruilen_cross_vestiging_geweigerd(client):
    a = _wijs_toe(client, 1, '22001', 'Emma').get_json()   # vestiging 1
    b = _wijs_toe(client, 3, '22002', 'Jan').get_json()     # kluisje 3 = vestiging 2
    rv = client.post('/api/toewijzingen/ruilen', json={
        'toewijzing_a_id': a['id'], 'toewijzing_b_id': b['id'],
    })
    assert rv.status_code == 409
    assert 'vestiging' in rv.get_json()['error'].lower()


def test_ruilen_niet_actieve_toewijzing_geweigerd(client):
    a = _wijs_toe(client, 1, '22001', 'Emma').get_json()
    b = _wijs_toe(client, 2, '22002', 'Jan').get_json()
    client.post(f'/api/toewijzingen/{b["id"]}/beeindigen', json={
        'sleutel_ingeleverd': True, 'borg_teruggestort': True, 'einddatum': '2026-03-24',
    })
    rv = client.post('/api/toewijzingen/ruilen', json={
        'toewijzing_a_id': a['id'], 'toewijzing_b_id': b['id'],
    })
    assert rv.status_code == 409


def test_ruilen_zelfde_id_geweigerd(client):
    a = _wijs_toe(client, 1, '22001', 'Emma').get_json()
    rv = client.post('/api/toewijzingen/ruilen', json={
        'toewijzing_a_id': a['id'], 'toewijzing_b_id': a['id'],
    })
    assert rv.status_code == 400


def test_ruilen_unique_index_blijft_intact(client):
    a = _wijs_toe(client, 1, '22001', 'Emma').get_json()
    b = _wijs_toe(client, 2, '22002', 'Jan').get_json()
    rv = client.post('/api/toewijzingen/ruilen', json={
        'toewijzing_a_id': a['id'], 'toewijzing_b_id': b['id'],
    })
    assert rv.status_code == 200
    actief = client.get('/api/toewijzingen/actief?vestiging_id=1').get_json()
    for kid in (1, 2):
        op_kluisje = [t for t in actief if t['kluisje_id'] == kid]
        assert len(op_kluisje) == 1, f'kluisje {kid} heeft {len(op_kluisje)} actieve toewijzingen'
    rv2 = client.post('/api/toewijzingen/ruilen', json={
        'toewijzing_a_id': a['id'], 'toewijzing_b_id': b['id'],
    })
    assert rv2.status_code == 200
    assert rv2.get_json()['a']['kluisje_id'] == 1  # weer terug
