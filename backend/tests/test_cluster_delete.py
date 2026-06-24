import pytest


@pytest.fixture(autouse=True)
def seed(client):
    client.post('/api/vestigingen', json={'naam': 'HG'})                       # vestiging 1
    client.post('/api/clusters', json={'vestiging_id': 1, 'naam': 'Gang A'})   # cluster 1
    client.post('/api/clusters/1/kluisjes', json={'kluisnummer': 'P001'})      # kluisje 1


def _assign(client, kid, stamnr):
    return client.post(f'/api/kluisjes/{kid}/toewijzen', json={
        'leerling_stamnr': stamnr, 'leerling_naam': 'X', 'leerling_klas': '1A',
        'periode_van': '2026-01-01', 'periode_tot': '2026-07-31',
    })


def test_delete_cluster_with_historical_toewijzing_succeeds(client):
    # toewijzen + beëindigen -> historische (inactieve) toewijzing
    _assign(client, 1, '1')
    tid = client.get('/api/toewijzingen/actief?vestiging_id=1').get_json()[0]['id']
    client.post(f'/api/toewijzingen/{tid}/beeindigen', json={
        'sleutel_ingeleverd': True, 'borg_teruggestort': True, 'einddatum': '2026-03-01'})
    rv = client.delete('/api/clusters/1')
    assert rv.status_code == 200
    # cluster verdwenen uit de lijst
    assert client.get('/api/vestigingen/1/clusters').get_json() == []
    # historie behouden: geschiedenis van het kluisje toont de toewijzing nog
    hist = client.get('/api/kluisjes/1/geschiedenis').get_json()
    assert len(hist) == 1


def test_delete_cluster_with_active_toewijzing_blocked(client):
    _assign(client, 1, '1')
    rv = client.delete('/api/clusters/1')
    assert rv.status_code == 409


def test_deleted_cluster_kluisjes_gone_from_overview(client):
    rv = client.delete('/api/clusters/1')
    assert rv.status_code == 200
    nummers = [k['kluisnummer'] for k in client.get('/api/kluisjes?vestiging_id=1').get_json()]
    assert 'P001' not in nummers
