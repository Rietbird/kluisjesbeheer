"""Fast key intake: type a sleutelnummer, the huur ends with the key returned.

The conciergerie processes a physical pile of returned keys. Doing that through
the normal flow costs four actions per key (search, open locker, end huur, tick
the box), which does not scale to a hundred keys.
"""
import pytest


@pytest.fixture(autouse=True)
def seed_data(client):
    client.post('/api/vestigingen', json={'naam': 'Zuid'})
    client.post('/api/clusters', json={'vestiging_id': 1, 'naam': 'Standaard'})


def _kluisje(client, kluisnummer, sleutelnummer, cluster_id=1):
    rv = client.post(f'/api/clusters/{cluster_id}/kluisjes',
                     json={'kluisnummer': kluisnummer, 'sleutelnummer': sleutelnummer})
    return rv.get_json()['id']


def _verhuur(client, kid, naam='Jesse Bootsma', stamnr='22871', klas='M3B'):
    return client.post(f'/api/kluisjes/{kid}/toewijzen', json={
        'leerling_stamnr': stamnr, 'leerling_naam': naam, 'leerling_klas': klas,
        'periode_van': '2025-08-01', 'periode_tot': '2026-07-31', 'borgbedrag': 0,
    })


def _innemen(client, sleutelnummer, **extra):
    body = {'sleutelnummer': sleutelnummer}
    body.update(extra)
    return client.post('/api/sleutels/innemen', json=body)


def _detail(client, kid):
    return client.get(f'/api/kluisjes/{kid}').get_json()


def test_innemen_beeindigt_huur_met_sleutel_ingeleverd(client):
    kid = _kluisje(client, 'Z013', '2983 D')
    _verhuur(client, kid)

    rv = _innemen(client, '2983 D')

    assert rv.status_code == 200
    body = rv.get_json()
    assert body['kluisnummer'] == 'Z013'
    assert body['leerling_naam'] == 'Jesse Bootsma'
    assert body['leerling_klas'] == 'M3B'


def test_kluisje_is_daarna_vrij(client):
    kid = _kluisje(client, 'Z013', '2983 D')
    _verhuur(client, kid)

    _innemen(client, '2983 D')

    assert _detail(client, kid)['status'] == 'vrij'


def test_sleutel_staat_als_ingeleverd_in_de_historie(client):
    kid = _kluisje(client, 'Z013', '2983 D')
    _verhuur(client, kid)

    _innemen(client, '2983 D')

    hist = client.get(f'/api/kluisjes/{kid}/geschiedenis').get_json()
    assert hist[0]['sleutel_ingeleverd'] == 1
    assert hist[0]['einddatum']


def test_spaties_en_hoofdletters_maken_niet_uit(client):
    kid = _kluisje(client, 'Z013', '2983 d')
    _verhuur(client, kid)

    rv = _innemen(client, '  2983 D  ')

    assert rv.status_code == 200


def test_onbekend_sleutelnummer_verandert_niets(client):
    kid = _kluisje(client, 'Z013', '2983 D')
    _verhuur(client, kid)

    rv = _innemen(client, '9999 X')

    assert rv.status_code == 404
    assert _detail(client, kid)['status'] == 'uitgeleend'


def test_sleutel_van_niet_verhuurd_kluisje_noemt_het_kluisje(client):
    """Happens a lot at MHV, where many rentals never made it into the app.

    "niets gevonden" would suggest a typo; naming the locker tells the truth:
    the key exists, the app just does not know it was rented.
    """
    _kluisje(client, 'Z013', '2983 D')

    rv = _innemen(client, '2983 D')

    assert rv.status_code == 404
    melding = rv.get_json()['error']
    assert 'Z013' in melding
    assert 'niet' in melding.lower()


def test_gedeeltelijke_treffer_op_een_vrij_kluisje_noemt_het_ook(client):
    _kluisje(client, 'O059E', 'O059E')

    rv = _innemen(client, '59e')

    assert rv.status_code == 404
    assert 'O059E' in rv.get_json()['error']


def test_dubbel_sleutelnummer_vraagt_om_een_keuze(client):
    """Sleutelnummers zijn bewust niet uniek (Eraspas, hergebruikte sleutels)."""
    k1 = _kluisje(client, 'Z013', 'Eraspas')
    k2 = _kluisje(client, 'Z014', 'Eraspas')
    _verhuur(client, k1, naam='Jesse Bootsma', stamnr='1')
    _verhuur(client, k2, naam='Isis Boom', stamnr='2')

    rv = _innemen(client, 'Eraspas')

    assert rv.status_code == 409
    keuzes = rv.get_json()['keuzes']
    assert {k['kluisnummer'] for k in keuzes} == {'Z013', 'Z014'}
    assert _detail(client, k1)['status'] == 'uitgeleend'
    assert _detail(client, k2)['status'] == 'uitgeleend'


def test_keuze_via_kluisje_id_neemt_de_juiste_in(client):
    k1 = _kluisje(client, 'Z013', 'Eraspas')
    k2 = _kluisje(client, 'Z014', 'Eraspas')
    _verhuur(client, k1, naam='Jesse Bootsma', stamnr='1')
    _verhuur(client, k2, naam='Isis Boom', stamnr='2')

    rv = _innemen(client, 'Eraspas', kluisje_id=k2)

    assert rv.status_code == 200
    assert _detail(client, k1)['status'] == 'uitgeleend'
    assert _detail(client, k2)['status'] == 'vrij'


def test_ongedaan_maken_zet_de_huur_terug(client):
    """A typo in a fast flow must be recoverable."""
    kid = _kluisje(client, 'Z013', '2983 D')
    _verhuur(client, kid)
    tid = _innemen(client, '2983 D').get_json()['toewijzing_id']

    rv = client.post(f'/api/sleutels/innemen/{tid}/ongedaan')

    assert rv.status_code == 200
    assert _detail(client, kid)['status'] == 'uitgeleend'
    kluisjes = client.get('/api/kluisjes?vestiging_id=1').get_json()
    zicht = next(k for k in kluisjes if k['id'] == kid)
    assert zicht['leerling_naam'] == 'Jesse Bootsma'


def test_gedeeltelijk_sleutelnummer_geeft_keuzelijst(client):
    """Typing part of a number must find it, but never end a huur by guess."""
    kid = _kluisje(client, 'O059E', 'O059E')
    _verhuur(client, kid)

    rv = _innemen(client, '59e')

    assert rv.status_code == 409
    keuzes = rv.get_json()['keuzes']
    assert [k['kluisnummer'] for k in keuzes] == ['O059E']
    assert _detail(client, kid)['status'] == 'uitgeleend'


def test_gedeeltelijk_kluisnummer_werkt_ook(client):
    """The tag on the key often carries the kluisnummer, not the key number."""
    kid = _kluisje(client, 'O059E', '2072 D')
    _verhuur(client, kid)

    rv = _innemen(client, '59e')

    assert rv.status_code == 409
    assert [k['kluisnummer'] for k in rv.get_json()['keuzes']] == ['O059E']


def test_keuze_uit_gedeeltelijke_treffer_neemt_in(client):
    kid = _kluisje(client, 'O059E', 'O059E')
    _verhuur(client, kid)

    rv = _innemen(client, '59e', kluisje_id=kid)

    assert rv.status_code == 200
    assert _detail(client, kid)['status'] == 'vrij'


def test_exacte_treffer_gaat_direct_door_ook_al_lijkt_hij_op_anderen(client):
    """The fast path must stay fast: an exact hit is not turned into a choice."""
    k1 = _kluisje(client, 'O059E', '2072 D')
    k2 = _kluisje(client, 'O159E', '2072 D2')
    _verhuur(client, k1, stamnr='1')
    _verhuur(client, k2, stamnr='2')

    rv = _innemen(client, '2072 D')

    assert rv.status_code == 200
    assert _detail(client, k1)['status'] == 'vrij'
    assert _detail(client, k2)['status'] == 'uitgeleend'


def test_te_korte_zoekterm_vraagt_om_meer(client):
    """A single character would match half the building."""
    for n in range(12):
        kid = _kluisje(client, f'O10{n}A', f'20{n}1 D')
        _verhuur(client, kid, stamnr=str(n))

    rv = _innemen(client, '0')

    assert rv.status_code == 409
    body = rv.get_json()
    assert body.get('te_veel') is True
    assert 'verfijn' in body['error'].lower()


def test_conciergerie_kan_geen_kluisje_van_andere_vestiging_innemen(client):
    client.post('/api/vestigingen', json={'naam': 'MHV'})
    client.post('/api/clusters', json={'vestiging_id': 2, 'naam': 'Standaard'})
    kid = _kluisje(client, 'X001', '1234 D', cluster_id=2)
    _verhuur(client, kid)

    with client.session_transaction() as sess:
        sess['user'] = {'displayName': 'Concierge Zuid', 'email': 'c@school.nl',
                        'is_beheerder': False, 'allowed_vestiging_ids': [1]}
    rv = _innemen(client, '1234 D')

    assert rv.status_code in (403, 404)
    with client.session_transaction() as sess:
        sess['user'] = {'displayName': 'Test', 'email': 'test@school.nl',
                        'is_beheerder': True, 'allowed_vestiging_ids': []}
    assert _detail(client, kid)['status'] == 'uitgeleend'
