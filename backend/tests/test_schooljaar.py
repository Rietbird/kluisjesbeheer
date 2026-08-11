"""The school year runs 1 August to 31 July.

That is the boundary the rest of the system already uses: Magister flips the
classes on 1 August, the student sync marks leavers then, and the
voorinschrijving protection expires then. It also always falls in the summer
holiday, so a rental period never changes while pupils are in the building.
"""
import pytest


@pytest.fixture(autouse=True)
def seed_data(client):
    client.post('/api/vestigingen', json={'naam': 'Zuid'})


def _periode(client):
    rv = client.get('/api/schooljaar/periode')
    assert rv.status_code == 200
    return rv.get_json()


def test_periode_loopt_van_1_augustus_tot_31_juli(client):
    p = _periode(client)

    assert p['periode_van'].endswith('-08-01')
    assert p['periode_tot'].endswith('-07-31')


def test_periode_sluit_aan_op_het_schooljaar(client):
    p = _periode(client)

    start, eind = p['schooljaar'].split('-')
    assert p['periode_van'] == f'{start}-08-01'
    assert p['periode_tot'] == f'{eind}-07-31'


def test_instelling_overschrijft_de_standaardperiode(client):
    """A school with a different boundary sets it in Beheer, MM-DD."""
    client.put('/api/instellingen', json={
        'standaard_periode_van': '10-15',
        'standaard_periode_tot': '06-20',
    })

    p = _periode(client)

    start, eind = p['schooljaar'].split('-')
    assert p['periode_van'] == f'{start}-10-15'
    assert p['periode_tot'] == f'{eind}-06-20'


def test_lege_instelling_valt_terug_op_de_standaard(client):
    client.put('/api/instellingen', json={
        'standaard_periode_van': '',
        'standaard_periode_tot': '',
    })

    p = _periode(client)

    assert p['periode_van'].endswith('-08-01')
    assert p['periode_tot'].endswith('-07-31')


def test_onzinnige_instelling_wordt_genegeerd(client):
    """Never hand a broken date to the assign form."""
    client.put('/api/instellingen', json={
        'standaard_periode_van': 'kwartaal 3',
        'standaard_periode_tot': '31-07',
    })

    p = _periode(client)

    assert p['periode_van'].endswith('-08-01')
    assert p['periode_tot'].endswith('-07-31')
