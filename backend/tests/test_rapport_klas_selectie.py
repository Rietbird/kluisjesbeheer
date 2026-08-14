"""Per-klas rapport: een selectie van klassen in een PDF, elke klas op een bladzijde.

De conciergerie legt de uitdraai naast de papieren klassenlijsten om de
ingevoerde toewijzingen met de hand na te lopen. Daarvoor moeten meerdere
klassen in een keer mee, en moet elke klas op een eigen bladzijde beginnen.
"""
import re

import pytest


@pytest.fixture(autouse=True)
def seed_data(client):
    client.post('/api/vestigingen', json={'naam': 'MHV'})
    client.post('/api/clusters', json={'vestiging_id': 1, 'naam': 'Standaard'})


def _kluisje(client, kluisnummer):
    return client.post('/api/clusters/1/kluisjes',
                       json={'kluisnummer': kluisnummer, 'sleutelnummer': ''}
                       ).get_json()['id']


def _leerling(client, db, stamnr, naam, klas):
    db.execute('INSERT INTO leerlingen (stamnr, naam, klas) VALUES (?, ?, ?)',
               (stamnr, naam, klas))
    db.commit()


def _verhuur(client, db, kluisnummer, stamnr, naam, klas):
    _leerling(client, db, stamnr, naam, klas)
    kid = _kluisje(client, kluisnummer)
    client.post(f'/api/kluisjes/{kid}/toewijzen', json={
        'leerling_stamnr': stamnr, 'leerling_naam': naam, 'leerling_klas': klas,
        'periode_van': '2026-08-01', 'periode_tot': '2027-07-31', 'borgbedrag': 0,
    })


def _preview(client, query=''):
    return client.get(
        '/api/dashboard/rapport/preview?type=klas&vestiging_id=1' + query
    ).get_data(as_text=True)


def _pdf(client, query=''):
    return client.get('/api/dashboard/rapport?type=klas&vestiging_id=1' + query)


def _paginas(pdf_bytes):
    """Aantal bladzijden uit de /Count van de Pages-node."""
    return max(int(n) for n in re.findall(rb'/Count\s+(\d+)', pdf_bytes))


def test_twee_geselecteerde_klassen_tonen_alleen_die_twee(client, db):
    _verhuur(client, db, 'X0011', '1', 'Stan Hannink', 'M4A')
    _verhuur(client, db, 'X0369', '2', 'Roslin Ahmad', 'M4B')
    _verhuur(client, db, 'X0654', '3', 'Anne Bulter', 'M4C')

    html = _preview(client, '&klas=M4A&klas=M4B')

    assert 'Stan Hannink' in html
    assert 'Roslin Ahmad' in html
    assert 'Anne Bulter' not in html


def test_een_klas_blijft_werken(client, db):
    _verhuur(client, db, 'X0011', '1', 'Stan Hannink', 'M4A')
    _verhuur(client, db, 'X0369', '2', 'Roslin Ahmad', 'M4B')

    html = _preview(client, '&klas=M4A')

    assert 'Stan Hannink' in html
    assert 'Roslin Ahmad' not in html


def test_zonder_klasparameter_komen_alle_klassen_mee(client, db):
    _verhuur(client, db, 'X0011', '1', 'Stan Hannink', 'M4A')
    _verhuur(client, db, 'X0369', '2', 'Roslin Ahmad', 'M4B')

    html = _preview(client)

    assert 'Stan Hannink' in html
    assert 'Roslin Ahmad' in html


def test_gekozen_klas_zonder_huurders_krijgt_toch_een_sectie(client, db):
    """Anders lijkt een klas waar niemand een kluisje heeft simpelweg te ontbreken."""
    _verhuur(client, db, 'X0011', '1', 'Stan Hannink', 'M4A')
    _leerling(client, db, '9', 'Luna Woldemichael', 'M4B')

    html = _preview(client, '&klas=M4A&klas=M4B')

    assert 'M4B' in html
    assert 'Luna Woldemichael' in html


def test_pdf_zet_elke_klas_op_een_eigen_bladzijde(client, db):
    _verhuur(client, db, 'X0011', '1', 'Stan Hannink', 'M4A')
    _verhuur(client, db, 'X0369', '2', 'Roslin Ahmad', 'M4B')
    _verhuur(client, db, 'X0654', '3', 'Anne Bulter', 'M4C')

    resp = _pdf(client, '&klas=M4A&klas=M4B&klas=M4C')

    assert resp.status_code == 200
    assert _paginas(resp.get_data()) == 3


def test_pdf_van_een_enkele_klas_is_een_bladzijde(client, db):
    _verhuur(client, db, 'X0011', '1', 'Stan Hannink', 'M4A')

    resp = _pdf(client, '&klas=M4A')

    assert _paginas(resp.get_data()) == 1


def test_preview_breekt_bij_printen_af_per_klas(client, db):
    """Printen vanuit de preview moet dezelfde indeling geven als de PDF."""
    _verhuur(client, db, 'X0011', '1', 'Stan Hannink', 'M4A')
    _verhuur(client, db, 'X0369', '2', 'Roslin Ahmad', 'M4B')

    html = _preview(client, '&klas=M4A&klas=M4B')

    assert html.count('<section class="klas">') == 2
    assert 'page-break-before: always' in html


def test_bestandsnaam_noemt_het_aantal_bij_een_selectie(client, db):
    _verhuur(client, db, 'X0011', '1', 'Stan Hannink', 'M4A')
    _verhuur(client, db, 'X0369', '2', 'Roslin Ahmad', 'M4B')

    resp = _pdf(client, '&klas=M4A&klas=M4B')

    assert '2klassen' in resp.headers['Content-Disposition']
