def test_create_vestiging(client):
    rv = client.post('/api/vestigingen', json={'naam': 'Hoofdgebouw', 'adres': 'Schoolstraat 1'})
    assert rv.status_code == 201
    data = rv.get_json()
    assert data['naam'] == 'Hoofdgebouw'
    assert data['id'] == 1

def test_list_vestigingen(client):
    client.post('/api/vestigingen', json={'naam': 'Hoofdgebouw'})
    client.post('/api/vestigingen', json={'naam': 'Dependance'})
    rv = client.get('/api/vestigingen')
    assert rv.status_code == 200
    assert len(rv.get_json()) == 2

def test_update_vestiging(client):
    client.post('/api/vestigingen', json={'naam': 'Oud'})
    rv = client.put('/api/vestigingen/1', json={'naam': 'Nieuw'})
    assert rv.status_code == 200
    assert rv.get_json()['naam'] == 'Nieuw'

def test_delete_vestiging(client):
    client.post('/api/vestigingen', json={'naam': 'Test'})
    rv = client.delete('/api/vestigingen/1')
    assert rv.status_code == 200
    rv = client.get('/api/vestigingen')
    assert len(rv.get_json()) == 0
