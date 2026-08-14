"""Report: which keys are still out with students who left.

Used as the chase-up list at the counter, so it is grouped per klas and shows
the key number. Students with no stamnr are included: they are unmatchable in
Magister and would otherwise fall outside every vertrokken-filter in the app.
"""
import pytest


@pytest.fixture(autouse=True)
def seed_data(client):
    client.post('/api/vestigingen', json={'naam': 'Zuid'})
    client.post('/api/clusters', json={'vestiging_id': 1, 'naam': 'Standaard'})


def _kluisje(client, kluisnummer, sleutelnummer):
    return client.post('/api/clusters/1/kluisjes',
                       json={'kluisnummer': kluisnummer, 'sleutelnummer': sleutelnummer}
                       ).get_json()['id']


def _verhuur(client, kid, naam, stamnr, klas='M4A'):
    return client.post(f'/api/kluisjes/{kid}/toewijzen', json={
        'leerling_stamnr': stamnr, 'leerling_naam': naam, 'leerling_klas': klas,
        'periode_van': '2025-08-01', 'periode_tot': '2026-07-31', 'borgbedrag': 0,
    })


def _leerling(client, db, stamnr, naam, klas, vertrokken=None):
    db.execute(
        'INSERT INTO leerlingen (stamnr, naam, klas, vertrokken_op) VALUES (?, ?, ?, ?)',
        (stamnr, naam, klas, vertrokken))
    db.commit()


def _preview(client):
    return client.get('/api/dashboard/rapport/preview?type=vertrokken&vestiging_id=1').get_data(as_text=True)


def test_vertrokken_leerling_met_kluisje_staat_in_het_rapport(client, db):
    _leerling(client, db, '100', 'Weg Gegaan', 'M4A', vertrokken='2026-08-01')
    kid = _kluisje(client, 'Z013', '2983 D')
    _verhuur(client, kid, 'Weg Gegaan', '100')

    html = _preview(client)

    assert 'Weg Gegaan' in html
    assert '2983 D' in html


def test_leerling_die_er_nog_zit_staat_er_niet_in(client, db):
    _leerling(client, db, '200', 'Nog Aanwezig', 'M3B')
    kid = _kluisje(client, 'Z014', '1111 D')
    _verhuur(client, kid, 'Nog Aanwezig', '200')

    html = _preview(client)

    assert 'Nog Aanwezig' not in html


def test_rapport_groepeert_per_klas(client, db):
    _leerling(client, db, '100', 'Weg Uit M4A', 'M4A', vertrokken='2026-08-01')
    _leerling(client, db, '101', 'Weg Uit H5C', 'H5C', vertrokken='2026-08-01')
    _verhuur(client, _kluisje(client, 'Z013', '2983 D'), 'Weg Uit M4A', '100', klas='M4A')
    _verhuur(client, _kluisje(client, 'Z014', '1111 D'), 'Weg Uit H5C', '101', klas='H5C')

    html = _preview(client)

    assert 'Klas: M4A' in html
    assert 'Klas: H5C' in html


def test_huurder_zonder_stamnr_staat_er_ook_in(client, db):
    """These 64 ISK rows match no leerling at all and are invisible elsewhere.

    Inserted straight into the table: the toewijzen route requires a stamnr, so
    rows like this can only come from the XLSX import, which is where they did.
    """
    kid = _kluisje(client, 'Z015', '2222 D')
    db.execute('''INSERT INTO toewijzingen
                  (kluisje_id, leerling_stamnr, leerling_naam, leerling_klas,
                   periode_van, periode_tot, actief)
                  VALUES (?, '', 'Naamloos Zonder Stamnr', '', '2025-08-01', '2026-07-31', 1)''', (kid,))
    db.execute("UPDATE kluisjes SET status = 'uitgeleend' WHERE id = ?", (kid,))
    db.commit()

    html = _preview(client)

    assert 'Naamloos Zonder Stamnr' in html
    assert 'niet in Magister' in html


def test_pdf_van_het_rapport_werkt(client, db):
    _leerling(client, db, '100', 'Weg Gegaan', 'M4A', vertrokken='2026-08-01')
    _verhuur(client, _kluisje(client, 'Z013', '2983 D'), 'Weg Gegaan', '100')

    rv = client.get('/api/dashboard/rapport?type=vertrokken&vestiging_id=1')

    # Smoke test: the PDF branch renders without blowing up. ReportLab
    # compresses its text streams, so asserting on the content is not possible
    # here; what the report actually contains is covered by the preview tests.
    assert rv.status_code == 200
    assert rv.headers['Content-Type'].startswith('application/pdf')
    assert 'vertrokken' in rv.headers['Content-Disposition']
    assert len(rv.get_data()) > 1000


def _beeindig(client, kid, sleutel_ingeleverd):
    tid = client.get(f'/api/kluisjes/{kid}/geschiedenis').get_json()[0]['id']
    return client.post(f'/api/toewijzingen/{tid}/beeindigen',
                       json={'sleutel_ingeleverd': sleutel_ingeleverd,
                             'einddatum': '2026-08-01'})


def test_ingeleverde_sleutel_staat_er_ook_in_als_historie(client, db):
    """Het rapport is de historie van vertrekkers, niet alleen de werklijst."""
    _leerling(client, db, '100', 'Netjes Ingeleverd', 'M4A', vertrokken='2026-08-01')
    kid = _kluisje(client, 'Z013', '2983 D')
    _verhuur(client, kid, 'Netjes Ingeleverd', '100')
    _beeindig(client, kid, True)

    html = _preview(client)

    assert 'Netjes Ingeleverd' in html
    # 'ingeleverd' zit ook in 'NIET ingeleverd', dus dat alleen bewijst niets.
    assert 'NIET ingeleverd' not in html


def test_lopende_huur_telt_als_niet_ingeleverd(client, db):
    _leerling(client, db, '100', 'Sleutel Kwijt', 'M4A', vertrokken='2026-08-01')
    _verhuur(client, _kluisje(client, 'Z013', '2983 D'), 'Sleutel Kwijt', '100')

    html = _preview(client)

    assert 'NIET ingeleverd' in html


def test_afgesloten_zonder_sleutel_telt_ook_als_niet_ingeleverd(client, db):
    _leerling(client, db, '100', 'Zonder Sleutel', 'M4A', vertrokken='2026-08-01')
    kid = _kluisje(client, 'Z013', '2983 D')
    _verhuur(client, kid, 'Zonder Sleutel', '100')
    _beeindig(client, kid, False)

    html = _preview(client)

    assert 'NIET ingeleverd' in html


def test_gegroepeerd_per_schooljaar_van_vertrek(client, db):
    _leerling(client, db, '100', 'Weg In Augustus', 'M4A', vertrokken='2026-08-01')
    _leerling(client, db, '101', 'Weg In November', 'M4A', vertrokken='2026-11-15')
    _verhuur(client, _kluisje(client, 'Z013', '2983 D'), 'Weg In Augustus', '100')
    _verhuur(client, _kluisje(client, 'Z014', '1111 D'), 'Weg In November', '101')

    html = _preview(client)

    assert 'Schooljaar 2025-2026' in html
    assert 'Schooljaar 2026-2027' in html
