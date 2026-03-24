def test_set_and_get_instelling(client):
    rv = client.put('/api/instellingen', json={'standaard_periode_van': '09-01', 'standaard_periode_tot': '07-31'})
    assert rv.status_code == 200
    rv = client.get('/api/instellingen')
    data = rv.get_json()
    assert data['standaard_periode_van'] == '09-01'
    assert data['standaard_periode_tot'] == '07-31'
