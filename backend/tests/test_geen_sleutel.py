import pytest
from db import get_db


@pytest.fixture(autouse=True)
def seed(client):
    client.post('/api/vestigingen', json={'naam': 'HG'})              # vestiging 1
    client.post('/api/clusters', json={'vestiging_id': 1, 'naam': 'Gang A'})  # cluster 1
    client.post('/api/clusters/1/kluisjes', json={'kluisnummer': 'P001'})     # kluisje 1
    client.post('/api/clusters/1/kluisjes', json={'kluisnummer': 'P002'})     # kluisje 2
    client.post('/api/clusters/1/kluisjes', json={'kluisnummer': 'P003'})     # kluisje 3


def _assign(client, kid, stamnr):
    return client.post(f'/api/kluisjes/{kid}/toewijzen', json={
        'leerling_stamnr': stamnr, 'leerling_naam': 'X', 'leerling_klas': '1A',
        'periode_van': '2026-01-01', 'periode_tot': '2026-07-31',
    })


def _set_reservesleutel(db_path, kid):
    conn = get_db(db_path)
    conn.execute("UPDATE toewijzingen SET reservesleutel_uitgegeven = 1 WHERE kluisje_id = ? AND actief = 1", (kid,))
    conn.commit()
    conn.close()


def test_put_sets_and_clears_geen_sleutel(client):
    client.put('/api/kluisjes/1', json={'geen_sleutel': True})
    assert client.get('/api/kluisjes/1').get_json()['geen_sleutel'] == 1
    client.put('/api/kluisjes/1', json={'geen_sleutel': False})
    assert client.get('/api/kluisjes/1').get_json()['geen_sleutel'] == 0


def test_toewijzen_blocked_when_geen_sleutel(client):
    client.put('/api/kluisjes/1', json={'geen_sleutel': True})
    rv = _assign(client, 1, '1')
    assert rv.status_code == 409


def test_filter_geen_sleutel(client):
    client.put('/api/kluisjes/1', json={'geen_sleutel': True})
    rows = client.get('/api/kluisjes?status=geen_sleutel').get_json()
    assert [r['kluisnummer'] for r in rows] == ['P001']


def test_vrij_excludes_geen_sleutel(client):
    client.put('/api/kluisjes/1', json={'geen_sleutel': True})
    nummers = [r['kluisnummer'] for r in client.get('/api/kluisjes?status=vrij').get_json()]
    assert 'P001' not in nummers
    assert 'P002' in nummers and 'P003' in nummers


def test_filter_reservesleutel(client, db_path):
    _assign(client, 2, '2')
    _set_reservesleutel(db_path, 2)
    nummers = [r['kluisnummer'] for r in client.get('/api/kluisjes?status=reservesleutel').get_json()]
    assert nummers == ['P002']


def test_filter_sleutel_niet_ingeleverd(client):
    _assign(client, 3, '3')
    tw = client.get('/api/toewijzingen/actief?vestiging_id=1').get_json()
    tid = [t for t in tw if t['kluisje_id'] == 3][0]['id']
    client.post(f'/api/toewijzingen/{tid}/beeindigen', json={'sleutel_ingeleverd': False, 'einddatum': '2026-03-01'})
    nummers = [r['kluisnummer'] for r in client.get('/api/kluisjes?status=sleutel_niet_ingeleverd').get_json()]
    assert nummers == ['P003']


def test_stats_vrij_excludes_geen_sleutel(client):
    # De vestigingskaart-teller "Vrij" moet gelijk lopen met de "Vrij"-filter
    before = next(v for v in client.get('/api/dashboard/stats').get_json() if v['vestiging_id'] == 1)['vrij']
    client.put('/api/kluisjes/1', json={'geen_sleutel': True})
    after = next(v for v in client.get('/api/dashboard/stats').get_json() if v['vestiging_id'] == 1)['vrij']
    assert after == before - 1


def test_filter_sleutel_all_combines(client, db_path):
    client.put('/api/kluisjes/1', json={'geen_sleutel': True})   # geen_sleutel
    _assign(client, 2, '2')
    _set_reservesleutel(db_path, 2)                              # reservesleutel
    nummers = sorted(r['kluisnummer'] for r in client.get('/api/kluisjes?status=sleutel').get_json())
    assert 'P001' in nummers
    assert 'P002' in nummers
