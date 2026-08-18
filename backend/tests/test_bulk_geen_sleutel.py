"""Collectief toekennen mag alleen uitleenbare kluisjes uitdelen.

De losse toewijsroute weigert een kluisje zonder sleutel met een 409, maar de
bulkroute controleerde alleen `is_defect`. Daardoor kon een collectieve ronde
een kluisje uitdelen waar geen sleutel bij hoort.
"""
import pytest


@pytest.fixture(autouse=True)
def seed(client):
    client.post('/api/vestigingen', json={'naam': 'MHV'})
    client.post('/api/clusters', json={'vestiging_id': 1, 'naam': 'Gang A'})
    for nr in ('X0001', 'X0002'):
        client.post('/api/clusters/1/kluisjes', json={'kluisnummer': nr})


def _bulk(client, paren):
    return client.post('/api/toewijzingen/bulk', json={
        'toewijzingen': [{'kluisje_id': kid, 'leerling_stamnr': st,
                          'leerling_naam': 'Leerling ' + st, 'leerling_klas': 'M4A'}
                         for kid, st in paren],
        'periode_van': '2026-08-01', 'periode_tot': '2027-07-31', 'borgbedrag': 0,
    }).get_json()


def test_kluisje_zonder_sleutel_wordt_niet_collectief_toegekend(client):
    client.put('/api/kluisjes/1', json={'geen_sleutel': True})

    res = _bulk(client, [(1, '100')])

    assert res['assigned'] == 0
    assert res['skipped'][0]['reden'] == 'Kluisje heeft geen sleutel'
    assert client.get('/api/kluisjes/1').get_json()['status'] == 'vrij'


def test_de_rest_van_de_batch_gaat_gewoon_door(client):
    client.put('/api/kluisjes/1', json={'geen_sleutel': True})

    res = _bulk(client, [(1, '100'), (2, '101')])

    assert res['assigned'] == 1
    assert client.get('/api/kluisjes/2').get_json()['status'] == 'uitgeleend'
