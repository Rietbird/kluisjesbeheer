"""'Vrij' moet betekenen: dit kluisje kun je nu uitgeven.

`status` en de vlaggen `is_defect` / `geen_sleutel` staan los van elkaar: een
defect kluisje houdt gewoon status 'vrij' zolang er niemand in zit. Filteren op
status alleen laat defecte kluisjes dus tussen de vrije staan, en dat is precies
waar de conciergerie op afgaat bij het uitdelen.
"""
import pytest


@pytest.fixture(autouse=True)
def seed(client):
    client.post('/api/vestigingen', json={'naam': 'MHV'})
    client.post('/api/clusters', json={'vestiging_id': 1, 'naam': 'Gang A'})
    for nr in ('O053A', 'O053B', 'O053C'):
        client.post('/api/clusters/1/kluisjes', json={'kluisnummer': nr})


def _vrij(client):
    rv = client.get('/api/kluisjes?vestiging_id=1&status=vrij')
    return [k['kluisnummer'] for k in rv.get_json()]


def _stat_vrij(client):
    return client.get('/api/dashboard/stats').get_json()[0]['vrij']


def test_defect_kluisje_valt_buiten_het_vrij_filter(client):
    client.put('/api/kluisjes/1', json={'is_defect': True})

    assert _vrij(client) == ['O053B', 'O053C']


def test_kluisje_zonder_sleutel_valt_buiten_het_vrij_filter(client):
    client.put('/api/kluisjes/1', json={'geen_sleutel': True})

    assert _vrij(client) == ['O053B', 'O053C']


def test_defect_kluisje_telt_niet_mee_als_vrij_op_het_dashboard(client):
    assert _stat_vrij(client) == 3

    client.put('/api/kluisjes/1', json={'is_defect': True})

    assert _stat_vrij(client) == 2


def test_opgeheven_defect_telt_weer_mee(client):
    client.put('/api/kluisjes/1', json={'is_defect': True})
    client.put('/api/kluisjes/1', json={'is_defect': False})

    assert _vrij(client) == ['O053A', 'O053B', 'O053C']
    assert _stat_vrij(client) == 3
