import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


def test_nieuw_voor_schooljaar_column_exists(db):
    cols = [r[1] for r in db.execute("PRAGMA table_info(leerlingen)").fetchall()]
    assert 'nieuw_voor_schooljaar' in cols
