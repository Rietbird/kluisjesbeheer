import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


def test_nieuw_voor_schooljaar_column_exists(db):
    cols = [r[1] for r in db.execute("PRAGMA table_info(leerlingen)").fetchall()]
    assert 'nieuw_voor_schooljaar' in cols


from leerling_sync import import_voorinschrijvingen, sync_leerlingen_to_db


def _vi(stamnr, naam='Brugklasser', **kw):
    return dict(stamnr=stamnr, naam=naam, locatie='Hoofd', **kw)


def _ll(stamnr, naam='Naam', klas='1A'):
    return dict(stamnr=stamnr, naam=naam, roepnaam='', tussenvoegsel='',
               achternaam=naam, email='', klas=klas, leerjaar='1', studie='', locatie='Hoofd')


def test_import_sets_flag_klasloos_no_vertrokken(db):
    res = import_voorinschrijvingen(db, [_vi('9001')], '2026-2027')
    row = db.execute("SELECT klas, nieuw_voor_schooljaar, vertrokken_op, locatie "
                     "FROM leerlingen WHERE stamnr='9001'").fetchone()
    assert row['klas'] == ''
    assert row['nieuw_voor_schooljaar'] == '2026-2027'
    assert row['vertrokken_op'] is None
    assert row['locatie'] == 'Hoofd'
    assert res['imported'] == 1


def test_import_does_not_mark_existing_vertrokken(db):
    sync_leerlingen_to_db(db, [_ll('1'), _ll('2')])
    import_voorinschrijvingen(db, [_vi('9001')], '2026-2027')
    n = db.execute("SELECT COUNT(*) AS n FROM leerlingen WHERE vertrokken_op IS NOT NULL").fetchone()['n']
    assert n == 0


def test_import_preserves_klas_of_existing_student(db):
    sync_leerlingen_to_db(db, [_ll('1', klas='3A')])
    import_voorinschrijvingen(db, [dict(stamnr='1', naam='X', locatie='Hoofd')], '2026-2027')
    assert db.execute("SELECT klas FROM leerlingen WHERE stamnr='1'").fetchone()['klas'] == '3A'
