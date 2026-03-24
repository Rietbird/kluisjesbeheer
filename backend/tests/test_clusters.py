import pytest

@pytest.fixture(autouse=True)
def seed_vestiging(client):
    """Seed a vestiging for cluster tests."""
    client.post('/api/vestigingen', json={'naam': 'Hoofdgebouw'})

def test_create_cluster(client):
    rv = client.post('/api/clusters', json={'vestiging_id': 1, 'naam': 'Gang A', 'standaard_borg': 15.0})
    assert rv.status_code == 201
    assert rv.get_json()['naam'] == 'Gang A'
    assert rv.get_json()['standaard_borg'] == 15.0

def test_list_clusters_by_vestiging(client):
    client.post('/api/clusters', json={'vestiging_id': 1, 'naam': 'Gang A'})
    client.post('/api/clusters', json={'vestiging_id': 1, 'naam': 'Gang B'})
    rv = client.get('/api/vestigingen/1/clusters')
    assert rv.status_code == 200
    assert len(rv.get_json()) == 2

def test_update_cluster(client):
    client.post('/api/clusters', json={'vestiging_id': 1, 'naam': 'Oud'})
    rv = client.put('/api/clusters/1', json={'naam': 'Nieuw', 'standaard_borg': 20.0})
    assert rv.status_code == 200
    assert rv.get_json()['naam'] == 'Nieuw'

def test_delete_cluster(client):
    client.post('/api/clusters', json={'vestiging_id': 1, 'naam': 'Test'})
    rv = client.delete('/api/clusters/1')
    assert rv.status_code == 200
