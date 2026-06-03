"""C1 autorisatie-sweep: een conciërge mag NIET bij data/mutaties van een
andere vestiging. Beheerder (user_vestiging_ids() == None) houdt volledige toegang.

Seed: 2 vestigingen, elk 1 cluster met 2 kluisjes.
  vestiging 1 → kluisjes 1, 2
  vestiging 2 → kluisjes 3, 4
"""
import pytest


@pytest.fixture(autouse=True)
def seed(client):
    client.post('/api/vestigingen', json={'naam': 'HG'})  # vestiging 1
    client.post('/api/vestigingen', json={'naam': 'BL'})  # vestiging 2
    client.post('/api/clusters', json={'vestiging_id': 1, 'naam': 'Gang A', 'standaard_borg': 15.0})  # cluster 1
    client.post('/api/clusters', json={'vestiging_id': 2, 'naam': 'Gang B', 'standaard_borg': 15.0})  # cluster 2
    client.post('/api/clusters/1/kluisjes', json={'kluisnummer': 'P001', 'sleutelnummer': 'S-001'})   # kluisje 1, vest 1
    client.post('/api/clusters/1/kluisjes', json={'kluisnummer': 'P002', 'sleutelnummer': 'S-002'})   # kluisje 2, vest 1
    client.post('/api/clusters/2/kluisjes', json={'kluisnummer': 'B001', 'sleutelnummer': 'B-001'})   # kluisje 3, vest 2
    client.post('/api/clusters/2/kluisjes', json={'kluisnummer': 'B002', 'sleutelnummer': 'B-002'})   # kluisje 4, vest 2


def _assign(client, kid, stamnr, naam, borg_betaald=True):
    return client.post(f'/api/kluisjes/{kid}/toewijzen', json={
        'leerling_stamnr': stamnr, 'leerling_naam': naam, 'leerling_klas': '2A',
        'periode_van': '2026-01-01', 'periode_tot': '2026-07-31',
        'borgbedrag': 15.0, 'borg_betaald': borg_betaald,
    })


def _concierge(client, vestiging_ids):
    """Schakel de sessie om naar een conciërge met toegang tot vestiging_ids."""
    with client.session_transaction() as sess:
        sess['user'] = {
            'displayName': 'Concierge', 'email': 'c@school.nl',
            'is_beheerder': False, 'allowed_vestiging_ids': list(vestiging_ids),
        }


# ---------- READ: leerling-PII van andere vestiging ----------

def test_concierge_geschiedenis_andere_vestiging_403(client):
    _assign(client, 3, '99001', 'Vreemde Leerling')   # vest 2
    _concierge(client, [1])
    assert client.get('/api/kluisjes/3/geschiedenis').status_code == 403


def test_concierge_geschiedenis_eigen_vestiging_ok(client):
    _assign(client, 1, '11001', 'Eigen Leerling')     # vest 1
    _concierge(client, [1])
    assert client.get('/api/kluisjes/1/geschiedenis').status_code == 200


def test_concierge_actief_alleen_eigen_vestiging(client):
    _assign(client, 1, '11001', 'Eigen')    # vest 1
    _assign(client, 3, '99001', 'Vreemde')  # vest 2
    _concierge(client, [1])
    rows = client.get('/api/toewijzingen/actief').get_json()
    assert rows, 'conciërge hoort eigen vestiging wel te zien'
    assert all(r['vestiging_id'] == 1 for r in rows), 'lek: andere vestiging zichtbaar'


def test_concierge_stats_alleen_eigen_vestiging(client):
    _concierge(client, [1])
    rows = client.get('/api/dashboard/stats').get_json()
    assert {r['vestiging_id'] for r in rows} == {1}


def test_concierge_rapport_preview_geen_andere_vestiging(client):
    _assign(client, 1, '11001', 'Eigen Kind')    # vest 1
    _assign(client, 3, '99001', 'Vreemd Kind')   # vest 2
    _concierge(client, [1])
    html = client.get('/api/dashboard/rapport/preview?type=toewijzingen').get_data(as_text=True)
    assert 'Vreemd Kind' not in html, 'PII-lek: leerling van andere vestiging in rapport'
    assert 'Eigen Kind' in html


def test_concierge_rapport_preview_expliciete_andere_vestiging_403(client):
    _concierge(client, [1])
    rv = client.get('/api/dashboard/rapport/preview?type=toewijzingen&vestiging_id=2')
    assert rv.status_code == 403


def test_concierge_rapport_pdf_andere_vestiging_403(client):
    _concierge(client, [1])
    rv = client.get('/api/dashboard/rapport?type=toewijzingen&vestiging_id=2')
    assert rv.status_code == 403


# ---------- WRITE: muteren in andere vestiging ----------

def test_concierge_ruilen_andere_vestiging_403(client):
    a = _assign(client, 3, '99001', 'A').get_json()  # vest 2
    b = _assign(client, 4, '99002', 'B').get_json()  # vest 2
    _concierge(client, [1])
    rv = client.post('/api/toewijzingen/ruilen', json={
        'toewijzing_a_id': a['id'], 'toewijzing_b_id': b['id'],
    })
    assert rv.status_code == 403


def test_concierge_borg_teruggestort_andere_vestiging_403(client):
    t = _assign(client, 3, '99001', 'A', borg_betaald=True).get_json()  # vest 2
    client.post(f'/api/toewijzingen/{t["id"]}/beeindigen', json={
        'sleutel_ingeleverd': True, 'borg_teruggestort': False, 'einddatum': '2026-03-24',
    })
    _concierge(client, [1])
    rv = client.post(f'/api/toewijzingen/{t["id"]}/borg-teruggestort', json={})
    assert rv.status_code == 403


def test_concierge_bulk_toewijzen_andere_vestiging_403(client):
    _concierge(client, [1])
    rv = client.post('/api/toewijzingen/bulk', json={
        'toewijzingen': [
            {'kluisje_id': 3, 'leerling_stamnr': '99001', 'leerling_naam': 'X', 'leerling_klas': '2A'},
        ],
        'periode_van': '2026-01-01', 'periode_tot': '2026-07-31', 'borgbedrag': 15.0,
    })
    assert rv.status_code == 403


# ---------- positief: eigen vestiging blijft werken ----------

def test_concierge_bulk_toewijzen_eigen_vestiging_ok(client):
    _concierge(client, [1])
    rv = client.post('/api/toewijzingen/bulk', json={
        'toewijzingen': [
            {'kluisje_id': 1, 'leerling_stamnr': '11001', 'leerling_naam': 'Eigen', 'leerling_klas': '2A'},
        ],
        'periode_van': '2026-01-01', 'periode_tot': '2026-07-31', 'borgbedrag': 15.0,
    })
    assert rv.status_code == 201
    assert rv.get_json()['assigned'] == 1
