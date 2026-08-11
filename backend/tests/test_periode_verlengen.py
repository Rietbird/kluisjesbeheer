"""Doorlopende huren schuiven bij de jaarwisseling mee naar het nieuwe schooljaar.

Op 1 augustus kantelt Magister de klassen. Wie blijft, houdt zijn kluisje, maar
de huurperiode bleef tot nu toe op het oude schooljaar staan. Dat gebeurt nu
automatisch in dezelfde dagelijkse sync die ook de vertrekkers markeert.
"""
import pytest

from leerling_sync import sync_leerlingen_to_db
from schooljaar import huidig_schooljaar


def _eind_huidig_schooljaar():
    return huidig_schooljaar().split('-')[1] + '-07-31'


def _leerling(db, stamnr, naam='Leerling', klas='H2B'):
    return {'stamnr': stamnr, 'naam': naam, 'klas': klas}


def _kluisje_met_huur(db, kluisnummer, stamnr, periode_van, periode_tot):
    db.execute("INSERT OR IGNORE INTO vestigingen (id, naam) VALUES (1, 'Zuid')")
    db.execute("INSERT OR IGNORE INTO clusters (id, vestiging_id, naam) VALUES (1, 1, 'Standaard')")
    cur = db.execute(
        "INSERT INTO kluisjes (cluster_id, vestiging_id, kluisnummer, status) VALUES (1, 1, ?, 'uitgeleend')",
        (kluisnummer,))
    kid = cur.lastrowid
    db.execute('''INSERT INTO toewijzingen
                  (kluisje_id, leerling_stamnr, leerling_naam, periode_van, periode_tot, actief)
                  VALUES (?, ?, 'Leerling', ?, ?, 1)''', (kid, stamnr, periode_van, periode_tot))
    db.commit()
    return db.execute('SELECT id FROM toewijzingen WHERE kluisje_id = ?', (kid,)).fetchone()['id']


def _periode(db, tid):
    r = db.execute('SELECT periode_van, periode_tot FROM toewijzingen WHERE id = ?', (tid,)).fetchone()
    return r['periode_van'], r['periode_tot']


def test_huur_van_blijvende_leerling_schuift_mee(db):
    tid = _kluisje_met_huur(db, 'Z001', '100', '2025-08-01', '2026-07-31')

    summary = sync_leerlingen_to_db(db, [_leerling(db, '100')])

    van, tot = _periode(db, tid)
    assert tot == _eind_huidig_schooljaar()
    assert summary['periodes_verlengd'] == 1


def test_startdatum_blijft_staan(db):
    """periode_van vertelt wanneer de leerling het kluisje kreeg; dat blijft waar."""
    tid = _kluisje_met_huur(db, 'Z001', '100', '2026-03-02', '2026-07-31')

    sync_leerlingen_to_db(db, [_leerling(db, '100')])

    van, tot = _periode(db, tid)
    assert van == '2026-03-02'


def test_huur_van_vertrokken_leerling_blijft_ongemoeid(db):
    tid = _kluisje_met_huur(db, 'Z001', '100', '2025-08-01', '2026-07-31')
    # Leerling zit niet in de Magister-lijst en wordt dus vertrokken gemarkeerd.
    db.execute("INSERT INTO leerlingen (stamnr, naam, klas) VALUES ('100', 'Weg', 'H2B')")
    db.execute("INSERT INTO leerlingen (stamnr, naam, klas) VALUES ('200', 'Blijft', 'H2B')")
    db.commit()

    summary = sync_leerlingen_to_db(db, [_leerling(db, '200')])

    assert _periode(db, tid)[1] == '2026-07-31'
    assert summary['periodes_verlengd'] == 0


def test_huurder_zonder_leerlingrij_blijft_ongemoeid(db):
    """De 64 kluisjes zonder stamnr: niet te verifieren, dus niet aanraken."""
    tid = _kluisje_met_huur(db, 'Z001', '', '2025-08-01', '2026-07-31')

    sync_leerlingen_to_db(db, [_leerling(db, '100')])

    assert _periode(db, tid)[1] == '2026-07-31'


def test_periode_die_al_goed_staat_wordt_niet_aangeraakt(db):
    eind = _eind_huidig_schooljaar()
    tid = _kluisje_met_huur(db, 'Z001', '100', '2026-08-01', eind)

    summary = sync_leerlingen_to_db(db, [_leerling(db, '100')])

    assert summary['periodes_verlengd'] == 0
    assert _periode(db, tid)[1] == eind


def test_beeindigde_huur_schuift_niet_mee(db):
    tid = _kluisje_met_huur(db, 'Z001', '100', '2025-08-01', '2026-07-31')
    db.execute('UPDATE toewijzingen SET actief = 0 WHERE id = ?', (tid,))
    db.commit()

    sync_leerlingen_to_db(db, [_leerling(db, '100')])

    assert _periode(db, tid)[1] == '2026-07-31'


def test_veiligheidsrem_slaat_ook_het_verlengen_over(db):
    """Bij een verdacht korte Magister-lijst klopt de vertrokken-status niet,
    dus dan ook niet aan de periodes zitten."""
    for i in range(10):
        db.execute("INSERT INTO leerlingen (stamnr, naam, klas) VALUES (?, 'X', 'H2B')", (str(i),))
    db.commit()
    tid = _kluisje_met_huur(db, 'Z001', '0', '2025-08-01', '2026-07-31')

    summary = sync_leerlingen_to_db(db, [_leerling(db, '0')])

    assert summary['brake_triggered'] is True
    assert summary['periodes_verlengd'] == 0
    assert _periode(db, tid)[1] == '2026-07-31'
