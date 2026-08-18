"""De klassen-dropdown moet ook klassen tonen waar nog niemand een kluisje heeft.

De lijst werd opgebouwd uit klassen die al een actieve huurder hadden. Daarmee
verdwijnt precies de klas die je zoekt als je wilt zien wie er nog een kluisje
moet krijgen: op MHV misten zo MH1A, MH1B, MH1C en V6B.

Klassen komen erbij via de Magister-locaties van de vestiging. Is die koppeling
niet ingesteld, dan valt de lijst terug op klassen met een huurder: alle klassen
van de school erin trekken zou een dropdown van een andere vestiging vervuilen.
"""
import pytest


@pytest.fixture(autouse=True)
def seed(client):
    client.post('/api/vestigingen', json={'naam': 'MHV'})
    client.post('/api/clusters', json={'vestiging_id': 1, 'naam': 'Gang A'})
    client.post('/api/clusters/1/kluisjes', json={'kluisnummer': 'X0001'})


def _leerling(db, stamnr, klas, locatie):
    db.execute('INSERT INTO leerlingen (stamnr, naam, klas, locatie) VALUES (?, ?, ?, ?)',
               (stamnr, 'Leerling ' + stamnr, klas, locatie))
    db.commit()


def _koppel_locatie(db, locatie):
    db.execute('INSERT INTO vestigingen_locaties (vestiging_id, locatie) VALUES (1, ?)',
               (locatie,))
    db.commit()


def _verhuur(client, kid, stamnr, klas):
    client.post(f'/api/kluisjes/{kid}/toewijzen', json={
        'leerling_stamnr': stamnr, 'leerling_naam': 'Leerling ' + stamnr,
        'leerling_klas': klas, 'periode_van': '2026-08-01', 'periode_tot': '2027-07-31',
    })


def _klassen(client):
    return client.get('/api/vestigingen/1/klassen').get_json()


def test_klas_zonder_huurder_staat_er_toch_in(client, db):
    _koppel_locatie(db, 'MAVO/HAVO/VWO')
    _leerling(db, '1', 'M4A', 'MAVO/HAVO/VWO')
    _leerling(db, '2', 'MH1A', 'MAVO/HAVO/VWO')
    _verhuur(client, 1, '1', 'M4A')

    assert _klassen(client) == ['M4A', 'MH1A']


def test_klas_van_een_andere_locatie_komt_er_niet_bij(client, db):
    _koppel_locatie(db, 'MAVO/HAVO/VWO')
    _leerling(db, '1', 'M4A', 'MAVO/HAVO/VWO')
    _leerling(db, '2', 'ISK3', 'Vestiging ISK')

    assert _klassen(client) == ['M4A']


def test_zonder_locatiekoppeling_blijft_het_bij_klassen_met_een_huurder(client, db):
    _leerling(db, '1', 'M4A', 'MAVO/HAVO/VWO')
    _leerling(db, '2', 'MH1A', 'MAVO/HAVO/VWO')
    _verhuur(client, 1, '1', 'M4A')

    assert _klassen(client) == ['M4A']


def test_vertrokken_leerling_levert_geen_klas_op(client, db):
    _koppel_locatie(db, 'MAVO/HAVO/VWO')
    _leerling(db, '1', 'M4A', 'MAVO/HAVO/VWO')
    db.execute("UPDATE leerlingen SET vertrokken_op = '2026-08-01' WHERE stamnr = '1'")
    db.commit()

    assert _klassen(client) == []
