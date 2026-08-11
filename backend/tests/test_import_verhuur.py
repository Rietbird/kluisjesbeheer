"""Import of a Magister Desktop 'Verhuuroverzicht' export.

Two things are covered here:

1. The Desktop export uses the column 'Code\nKluisje' (with a hard line break)
   and a single 'Leerling' column. The original parser looked for
   'Omschrijving Kluisje' plus separate Roepnaam/Tussenv/Achternaam columns,
   so a real export yielded zero lockers.
2. All lockers already exist after the one-time migration, so a plain import
   skips every row. The 'verhuur' mode matches on an existing kluisnummer and
   creates the assignment instead.
"""
import io
from datetime import datetime

import openpyxl
import pytest


@pytest.fixture(autouse=True)
def seed_data(client):
    """Seed the vestiging the import writes into."""
    client.post('/api/vestigingen', json={'naam': 'Zuid'})
    client.post('/api/clusters', json={'vestiging_id': 1, 'naam': 'Standaard'})


DESKTOP_HEADERS = [
    'Stamnr', 'Leerling', 'Code\nKluisje', 'Sleutelnummer', 'Categorie\nKluisje',
    'Verhuur vanaf', 'Verhuur tot/met', 'Borgbedrag ontvangen',
    'Borgbedrag geretourneerd', 'Sleutel ingeleverd',
]


def _desktop_xlsx(rows):
    """Build an xlsx shaped exactly like the Magister Desktop export."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(DESKTOP_HEADERS)
    for r in rows:
        ws.append(r)
    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf


def _vrij(code):
    return [None, None, code, None, None, None, None, None, None, None]


def _verhuurd(stamnr, naam, code, sleutel='6435 D'):
    return [
        stamnr, naam, code, sleutel, None,
        datetime(2026, 8, 1), datetime(2027, 7, 31), 'Nee', 'Nee', 'Nee',
    ]


def _import(client, xlsx, **extra):
    data = {'file': (xlsx, 'export.xlsx'), 'vestiging_id': '1'}
    data.update(extra)
    return client.post('/api/kluisjes/import', data=data,
                       content_type='multipart/form-data')


def _kluisje(client, kluisnummer):
    kl = client.get('/api/kluisjes?vestiging_id=1').get_json()
    return next(k for k in kl if k['kluisnummer'] == kluisnummer)


# --- parser -----------------------------------------------------------------

def test_desktop_export_met_code_kluisje_wordt_gelezen(client):
    """'Code\nKluisje' is the real column name; the old parser found nothing."""
    xlsx = _desktop_xlsx([_vrij('Z001'), _verhuurd(22899, 'Dexx Zweers', 'Z236')])

    rv = _import(client, xlsx)

    assert rv.status_code == 201
    body = rv.get_json()
    assert body['format'] == 'desktop'
    assert body['imported'] == 2
    assert body['toewijzingen'] == 1


def test_desktop_export_leest_naam_uit_enkele_leerling_kolom(client):
    xlsx = _desktop_xlsx([_verhuurd(22899, 'Dexx Zweers', 'Z236')])

    _import(client, xlsx)

    assert _kluisje(client, 'Z236')['leerling_naam'] == 'Dexx Zweers'


def test_preview_telt_kluisjes_uit_desktop_export(client):
    xlsx = _desktop_xlsx([_vrij('Z001'), _vrij('Z002')])

    rv = client.post('/api/kluisjes/import/preview',
                     data={'file': (xlsx, 'export.xlsx')},
                     content_type='multipart/form-data')

    assert rv.status_code == 200
    assert rv.get_json()['total'] == 2


# --- verhuur mode -----------------------------------------------------------

def test_verhuur_modus_wijst_toe_op_bestaand_kluisje(client):
    """The whole point: every kluisnummer already exists after the migration."""
    _import(client, _desktop_xlsx([_vrij('Z236')]))

    rv = _import(client, _desktop_xlsx([_verhuurd(22899, 'Dexx Zweers', 'Z236')]),
                 modus='verhuur')

    assert rv.status_code == 201
    assert rv.get_json()['toegewezen'] == 1
    k = _kluisje(client, 'Z236')
    assert k['status'] == 'uitgeleend'
    assert k['leerling_naam'] == 'Dexx Zweers'
    assert k['periode_van'] == '2026-08-01'
    assert k['periode_tot'] == '2027-07-31'


def test_verhuur_modus_slaat_zelfde_leerling_over(client):
    """Re-running the import while Bart works on must not churn the data."""
    _import(client, _desktop_xlsx([_vrij('Z236')]))
    _import(client, _desktop_xlsx([_verhuurd(22899, 'Dexx Zweers', 'Z236')]), modus='verhuur')

    rv = _import(client, _desktop_xlsx([_verhuurd(22899, 'Dexx Zweers', 'Z236')]), modus='verhuur')

    body = rv.get_json()
    assert body['toegewezen'] == 0
    assert body['ongewijzigd'] == 1


def test_verhuur_modus_meldt_conflict_en_muteert_niet(client):
    """A locker still rented to last year's student is reported, not silently taken."""
    _import(client, _desktop_xlsx([_verhuurd(11111, 'Vorig Jaar', 'Z013')]))

    rv = _import(client, _desktop_xlsx([_verhuurd(22899, 'Joas Bosch', 'Z013')]),
                 modus='verhuur')

    body = rv.get_json()
    assert body['conflicten'] == 1
    assert body['toegewezen'] == 0
    assert _kluisje(client, 'Z013')['leerling_naam'] == 'Vorig Jaar'


def test_verhuur_modus_lost_conflict_op_met_vlag(client):
    """With the explicit flag the running huur ends and the new one starts."""
    _import(client, _desktop_xlsx([_verhuurd(11111, 'Vorig Jaar', 'Z013')]))

    rv = _import(client, _desktop_xlsx([_verhuurd(22899, 'Joas Bosch', 'Z013')]),
                 modus='verhuur', beeindig_conflicten='1')

    body = rv.get_json()
    assert body['toegewezen'] == 1
    assert body['beeindigd'] == 1
    assert _kluisje(client, 'Z013')['leerling_naam'] == 'Joas Bosch'


def test_beeindigde_conflicthuur_telt_sleutel_als_ingeleverd(client):
    """Bart could only reassign the locker because the key came back."""
    _import(client, _desktop_xlsx([_verhuurd(11111, 'Vorig Jaar', 'Z013')]))

    _import(client, _desktop_xlsx([_verhuurd(22899, 'Joas Bosch', 'Z013')]),
            modus='verhuur', beeindig_conflicten='1')

    hist = client.get('/api/kluisjes/1/geschiedenis').get_json()
    oud = next(h for h in hist if h['leerling_naam'] == 'Vorig Jaar')
    assert oud['sleutel_ingeleverd'] == 1


def test_regel_zonder_stamnr_beeindigt_nooit_een_huur(client):
    """Magister's locker data is stale: a blank row does not mean 'free'."""
    _import(client, _desktop_xlsx([_verhuurd(11111, 'Vorig Jaar', 'Z013')]))

    rv = _import(client, _desktop_xlsx([_vrij('Z013')]),
                 modus='verhuur', beeindig_conflicten='1')

    assert rv.status_code == 201
    assert rv.get_json()['beeindigd'] == 0
    assert _kluisje(client, 'Z013')['leerling_naam'] == 'Vorig Jaar'


def test_verhuur_modus_meldt_onbekend_kluisnummer(client):
    rv = _import(client, _desktop_xlsx([_verhuurd(22899, 'Dexx Zweers', 'Q999')]),
                 modus='verhuur')

    assert rv.get_json()['onbekend'] == 1


def test_dry_run_telt_wel_maar_schrijft_niet(client):
    """Preview must be the real run, minus the commit."""
    _import(client, _desktop_xlsx([_vrij('Z236')]))

    rv = _import(client, _desktop_xlsx([_verhuurd(22899, 'Dexx Zweers', 'Z236')]),
                 modus='verhuur', dry_run='1')

    assert rv.get_json()['toegewezen'] == 1
    assert _kluisje(client, 'Z236')['status'] == 'vrij'


def test_dry_run_beeindigt_geen_lopende_huur(client):
    _import(client, _desktop_xlsx([_verhuurd(11111, 'Vorig Jaar', 'Z013')]))

    rv = _import(client, _desktop_xlsx([_verhuurd(22899, 'Joas Bosch', 'Z013')]),
                 modus='verhuur', beeindig_conflicten='1', dry_run='1')

    assert rv.get_json()['beeindigd'] == 1
    assert _kluisje(client, 'Z013')['leerling_naam'] == 'Vorig Jaar'


def test_verhuur_modus_normaliseert_kluisnummer(client):
    """The export writes Z01-01, the migration stored Z001-01."""
    _import(client, _desktop_xlsx([_vrij('Z001-01'), _vrij('Z705')]))

    rv = _import(client, _desktop_xlsx([_verhuurd(22899, 'Dexx Zweers', 'Z01-01'),
                                        _vrij('Z705')]),
                 modus='verhuur', normaliseer='1')

    assert rv.get_json()['toegewezen'] == 1
    assert _kluisje(client, 'Z001-01')['leerling_naam'] == 'Dexx Zweers'
