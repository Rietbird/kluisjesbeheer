import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from leerling_sync import sync_leerlingen_to_db


def _leerling(stamnr, naam='Naam', klas='1A', **kw):
    base = dict(stamnr=stamnr, naam=naam, roepnaam='', tussenvoegsel='',
                achternaam=naam, email='', klas=klas, leerjaar='1',
                studie='', locatie='Hoofd')
    base.update(kw)
    return base


def test_upsert_inserts_new_students(db):
    summary = sync_leerlingen_to_db(db, [_leerling('1'), _leerling('2')])
    rows = db.execute('SELECT stamnr, vertrokken_op FROM leerlingen ORDER BY stamnr').fetchall()
    assert [r['stamnr'] for r in rows] == ['1', '2']
    assert all(r['vertrokken_op'] is None for r in rows)
    assert summary['upserted'] == 2


def test_klas_updated_on_resync(db):
    sync_leerlingen_to_db(db, [_leerling('1', klas='1A')])
    sync_leerlingen_to_db(db, [_leerling('1', klas='2A')])
    assert db.execute("SELECT klas FROM leerlingen WHERE stamnr='1'").fetchone()['klas'] == '2A'


def test_absent_student_marked_vertrokken(db):
    sync_leerlingen_to_db(db, [_leerling('1'), _leerling('2'), _leerling('3')])
    summary = sync_leerlingen_to_db(db, [_leerling('1'), _leerling('2')])
    assert db.execute("SELECT vertrokken_op FROM leerlingen WHERE stamnr='3'").fetchone()['vertrokken_op'] is not None
    assert db.execute("SELECT vertrokken_op FROM leerlingen WHERE stamnr='1'").fetchone()['vertrokken_op'] is None
    assert summary['vertrokken_marked'] == 1
    assert summary['brake_triggered'] is False


def test_already_vertrokken_not_redated(db):
    sync_leerlingen_to_db(db, [_leerling('1'), _leerling('2')])
    db.execute("UPDATE leerlingen SET vertrokken_op='2020-01-01' WHERE stamnr='2'")
    db.commit()
    sync_leerlingen_to_db(db, [_leerling('1')])
    assert db.execute("SELECT vertrokken_op FROM leerlingen WHERE stamnr='2'").fetchone()['vertrokken_op'] == '2020-01-01'


def test_returning_student_unmarked(db):
    sync_leerlingen_to_db(db, [_leerling('1')])
    db.execute("UPDATE leerlingen SET vertrokken_op='2020-01-01' WHERE stamnr='1'")
    db.commit()
    sync_leerlingen_to_db(db, [_leerling('1')])
    assert db.execute("SELECT vertrokken_op FROM leerlingen WHERE stamnr='1'").fetchone()['vertrokken_op'] is None


def test_safety_brake_skips_marking_on_small_list(db):
    sync_leerlingen_to_db(db, [_leerling(str(i)) for i in range(10)])
    summary = sync_leerlingen_to_db(db, [_leerling('0'), _leerling('1')])
    assert summary['brake_triggered'] is True
    assert summary['vertrokken_marked'] == 0
    assert db.execute('SELECT COUNT(*) AS n FROM leerlingen WHERE vertrokken_op IS NOT NULL').fetchone()['n'] == 0
    # present students are still upserted
    assert db.execute('SELECT COUNT(*) AS n FROM leerlingen').fetchone()['n'] == 10


def test_empty_list_does_not_mark_everyone(db):
    sync_leerlingen_to_db(db, [_leerling('1'), _leerling('2')])
    summary = sync_leerlingen_to_db(db, [])
    assert summary['brake_triggered'] is True
    assert db.execute('SELECT COUNT(*) AS n FROM leerlingen WHERE vertrokken_op IS NOT NULL').fetchone()['n'] == 0


def test_brake_just_above_threshold_marks(db):
    sync_leerlingen_to_db(db, [_leerling(str(i)) for i in range(10)])
    summary = sync_leerlingen_to_db(db, [_leerling(str(i)) for i in range(6)])
    assert summary['brake_triggered'] is False
    assert summary['vertrokken_marked'] == 4


def test_first_import_on_empty_db_no_brake(db):
    summary = sync_leerlingen_to_db(db, [_leerling('1'), _leerling('2')])
    assert summary['brake_triggered'] is False
    assert summary['vertrokken_marked'] == 0
