import pytest


@pytest.fixture(autouse=True)
def seed(client):
    client.post('/api/vestigingen', json={'naam': 'HG'})            # vestiging 1
    client.post('/api/vestigingen', json={'naam': 'BL'})            # vestiging 2
    client.post('/api/clusters', json={'vestiging_id': 1, 'naam': 'Standaard'})   # cluster 1
    client.post('/api/clusters', json={'vestiging_id': 1, 'naam': '1e verd'})     # cluster 2
    client.post('/api/clusters', json={'vestiging_id': 2, 'naam': 'Anders'})      # cluster 3
    for n in range(1, 6):  # MO-1..MO-5 in cluster 1 (vestiging 1)
        client.post('/api/clusters/1/kluisjes', json={'kluisnummer': f'MO-{n}'})


def test_verplaats_reeks_binnen_vestiging(client):
    rv = client.post('/api/clusters/2/verplaats-reeks',
                      json={'prefix': 'MO-', 'van': 1, 'tot': 3})
    assert rv.status_code == 200
    assert rv.get_json()['verplaatst'] == 3
    cl2 = client.get('/api/clusters/2/kluisjes').get_json()
    assert sorted(k['kluisnummer'] for k in cl2) == ['MO-1', 'MO-2', 'MO-3']
    cl1 = client.get('/api/clusters/1/kluisjes').get_json()
    assert sorted(k['kluisnummer'] for k in cl1) == ['MO-4', 'MO-5']


def test_verplaats_reeks_cross_vestiging_geweigerd(client):
    rv = client.post('/api/clusters/3/verplaats-reeks',
                      json={'prefix': 'MO-', 'van': 1, 'tot': 3})
    assert rv.status_code == 409


def test_verplaats_reeks_ongeldige_getallen(client):
    rv = client.post('/api/clusters/2/verplaats-reeks',
                      json={'prefix': 'MO-', 'van': 'x', 'tot': 3})
    assert rv.status_code == 400


def test_verplaats_selectie_binnen_vestiging(client):
    cl1 = client.get('/api/clusters/1/kluisjes').get_json()
    ids = [k['id'] for k in cl1[:2]]
    rv = client.post('/api/clusters/2/verplaats-selectie',
                      json={'kluisje_ids': ids})
    assert rv.status_code == 200
    assert rv.get_json()['verplaatst'] == 2
    cl2 = client.get('/api/clusters/2/kluisjes').get_json()
    assert len(cl2) == 2


def test_verplaats_selectie_cross_vestiging_geweigerd(client):
    cl1 = client.get('/api/clusters/1/kluisjes').get_json()
    ids = [k['id'] for k in cl1[:2]]
    rv = client.post('/api/clusters/3/verplaats-selectie',
                      json={'kluisje_ids': ids})
    assert rv.status_code == 409


def test_verplaats_selectie_leeg_geweigerd(client):
    rv = client.post('/api/clusters/2/verplaats-selectie', json={'kluisje_ids': []})
    assert rv.status_code == 400
