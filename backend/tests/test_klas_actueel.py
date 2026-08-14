"""Welke klas hoort er bij een lopende huur: de actuele, niet die van toen.

Het klasveld op de toewijzing is een momentopname van het moment van uitgifte.
Bij de jaarwisseling kantelt Magister de klassen, maar dat veld blijft staan.
Daardoor liep de HV1D van vorig jaar door in de HV1D van dit jaar: 49 regels
voor een klas van 24. De actuele Magister-klas hoort dus te winnen, met het
vastgelegde veld als terugval voor installaties zonder leerling-sync.
"""
import pytest


@pytest.fixture(autouse=True)
def seed_data(client):
    client.post('/api/vestigingen', json={'naam': 'MHV'})
    client.post('/api/clusters', json={'vestiging_id': 1, 'naam': 'Standaard'})


def _kluisje(client, kluisnummer):
    return client.post('/api/clusters/1/kluisjes',
                       json={'kluisnummer': kluisnummer, 'sleutelnummer': ''}
                       ).get_json()['id']


def _verhuur(client, kluisnummer, stamnr, naam, klas_toen):
    kid = _kluisje(client, kluisnummer)
    client.post(f'/api/kluisjes/{kid}/toewijzen', json={
        'leerling_stamnr': stamnr, 'leerling_naam': naam, 'leerling_klas': klas_toen,
        'periode_van': '2025-08-01', 'periode_tot': '2027-07-31', 'borgbedrag': 0,
    })
    return kid


def _leerling(db, stamnr, naam, klas):
    db.execute('INSERT INTO leerlingen (stamnr, naam, klas) VALUES (?, ?, ?)',
               (stamnr, naam, klas))
    db.commit()


def test_klassenlijst_toont_de_actuele_klas_niet_die_van_de_uitgifte(client, db):
    _leerling(db, '1', 'Dex Nijland', 'HV2A')
    _verhuur(client, 'X0530', '1', 'Dex Nijland', 'HV1D')

    klassen = client.get('/api/vestigingen/1/klassen').get_json()

    assert klassen == ['HV2A']


def test_filter_op_klas_gebruikt_de_actuele_klas(client, db):
    _leerling(db, '1', 'Dex Nijland', 'HV2A')
    _verhuur(client, 'X0530', '1', 'Dex Nijland', 'HV1D')

    nu = client.get('/api/kluisjes?vestiging_id=1&klas=HV2A').get_json()
    toen = client.get('/api/kluisjes?vestiging_id=1&klas=HV1D').get_json()

    assert [r['kluisnummer'] for r in nu] == ['X0530']
    assert toen == []


def test_kluisjeslijst_toont_de_actuele_klas(client, db):
    _leerling(db, '1', 'Dex Nijland', 'HV2A')
    _verhuur(client, 'X0530', '1', 'Dex Nijland', 'HV1D')

    rows = client.get('/api/kluisjes?vestiging_id=1').get_json()

    assert rows[0]['leerling_klas'] == 'HV2A'


def test_zonder_leerlingrij_geldt_het_vastgelegde_klasveld(client, db):
    """Hengelo draait zonder Magister-sync, en er zijn huurders zonder stamnummer."""
    _verhuur(client, 'X0530', '999', 'Onbekend In Magister', 'HV1D')

    rows = client.get('/api/kluisjes?vestiging_id=1').get_json()
    klassen = client.get('/api/vestigingen/1/klassen').get_json()

    assert rows[0]['leerling_klas'] == 'HV1D'
    assert klassen == ['HV1D']


def test_lege_klas_in_magister_valt_terug_op_het_vastgelegde_veld(client, db):
    """De leerling is bekend maar zonder klas; dan is het oude veld nog het beste dat er is."""
    _leerling(db, '1', 'Dex Nijland', '')
    _verhuur(client, 'X0530', '1', 'Dex Nijland', 'HV1D')

    rows = client.get('/api/kluisjes?vestiging_id=1').get_json()

    assert rows[0]['leerling_klas'] == 'HV1D'


def test_rapport_groepeert_op_de_actuele_klas(client, db):
    _leerling(db, '1', 'Dex Nijland', 'HV2A')
    _verhuur(client, 'X0530', '1', 'Dex Nijland', 'HV1D')
    _leerling(db, '2', 'Nina Goselink', 'HV1D')
    _verhuur(client, 'X0412', '2', 'Nina Goselink', 'HV1D')

    html = client.get(
        '/api/dashboard/rapport/preview?type=klas&vestiging_id=1&klas=HV1D'
    ).get_data(as_text=True)

    assert 'Nina Goselink' in html
    assert 'Dex Nijland' not in html
