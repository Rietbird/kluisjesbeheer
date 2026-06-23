import pytest
from db import get_db


@pytest.fixture(autouse=True)
def seed(client):
    client.post('/api/vestigingen', json={'naam': 'HG'})              # vestiging 1
    client.post('/api/clusters', json={'vestiging_id': 1, 'naam': 'Gang A'})  # cluster 1
    client.post('/api/clusters/1/kluisjes', json={'kluisnummer': 'P001'})     # kluisje 1
    client.post('/api/clusters/1/kluisjes', json={'kluisnummer': 'P002'})     # kluisje 2


def _assign(client, kid, stamnr, naam):
    return client.post(f'/api/kluisjes/{kid}/toewijzen', json={
        'leerling_stamnr': stamnr, 'leerling_naam': naam, 'leerling_klas': '2A',
        'periode_van': '2026-01-01', 'periode_tot': '2026-07-31', 'borgbedrag': 0,
    })


def _leerling_row(db_path, stamnr, vertrokken=False):
    conn = get_db(db_path)
    conn.execute(
        "INSERT INTO leerlingen (stamnr, naam, klas, vertrokken_op) VALUES (?, 'X', '2A', %s)"
        % ("date('now')" if vertrokken else 'NULL'),
        (stamnr,),
    )
    conn.commit()
    conn.close()


def test_vertrokken_filter_shows_only_departed_occupants(client, db_path):
    _assign(client, 1, '22001', 'Emma')   # wordt vertrokken
    _assign(client, 2, '22002', 'Jan')    # blijft
    _leerling_row(db_path, '22001', vertrokken=True)
    _leerling_row(db_path, '22002', vertrokken=False)

    rows = client.get('/api/kluisjes?status=vertrokken').get_json()
    nummers = [r['kluisnummer'] for r in rows]
    assert 'P001' in nummers
    assert 'P002' not in nummers


def test_vrij_kluisje_not_in_vertrokken_filter(client, db_path):
    # kluisje 2 blijft vrij; mag nooit in het vertrokken-filter opduiken
    _assign(client, 1, '22001', 'Emma')
    _leerling_row(db_path, '22001', vertrokken=True)
    rows = client.get('/api/kluisjes?status=vertrokken').get_json()
    nummers = [r['kluisnummer'] for r in rows]
    assert 'P002' not in nummers


def test_actieve_toewijzingen_includes_vertrokken_op(client, db_path):
    _assign(client, 1, '22001', 'Emma')
    _leerling_row(db_path, '22001', vertrokken=True)
    rows = client.get('/api/toewijzingen/actief?vestiging_id=1').get_json()
    assert len(rows) == 1
    assert rows[0]['leerling_vertrokken_op'] is not None


def test_manual_sync_route_marks_absent_vertrokken(client, db_path):
    """Regressie: de handmatige sync-knop markeert afwezige leerlingen als
    vertrokken (deelt nu dezelfde code als de cron)."""
    from unittest.mock import patch
    conn = get_db(db_path)
    for s in ('A', 'B', 'C', 'D'):
        conn.execute("INSERT INTO leerlingen (stamnr, naam, klas) VALUES (?, 'X', '1A')", (s,))
    conn.commit()
    conn.close()
    # Magister levert nog 3 van de 4 (D is weg) -> ruim boven de 50%-rem
    nieuw = [{'stamnr': s, 'naam': 'X', 'klas': '1A'} for s in ('A', 'B', 'C')]
    with patch('api_magister.magister') as m:
        m.get_leerlingen.return_value = nieuw
        m.flush_cache.return_value = None
        rv = client.post('/api/magister/sync-leerlingen')
    assert rv.status_code == 200
    assert rv.get_json()['vertrokken_gemarkeerd'] == 1
    conn = get_db(db_path)
    assert conn.execute("SELECT vertrokken_op FROM leerlingen WHERE stamnr='D'").fetchone()['vertrokken_op'] is not None
    assert conn.execute("SELECT vertrokken_op FROM leerlingen WHERE stamnr='A'").fetchone()['vertrokken_op'] is None
    conn.close()
