"""Shared student-sync logic, used by both the manual route (api_magister) and
the daily cron (cron_sync.py).

Takes an explicit db connection so it works inside a Flask request context
(g.db) and outside one (cron). Keeps the two paths identical -- before this
existed, the cron upserted students but never marked departed ones, so
graduates/leavers kept their lockers after the 1-8 school-year switch.
"""

# Safety brake: if the incoming list is smaller than this fraction of the
# current (non-departed) student population, skip the vertrokken-marking and
# warn. Protects the unattended cron against a partial Magister response that
# would otherwise flag hundreds of students as departed in one run.
VERTROKKEN_BRAKE_FRACTION = 0.5


def sync_leerlingen_to_db(db, leerlingen):
    """Upsert students and mark absent ones as departed (vertrokken).

    Returns a summary dict: {upserted, vertrokken_marked, brake_triggered}.
    The caller is responsible for logging the summary (loudly when the brake
    triggers, since the cron is unattended).
    """
    # Count the current population BEFORE upserting, for the safety brake.
    prior_active = db.execute(
        'SELECT COUNT(*) AS n FROM leerlingen WHERE vertrokken_op IS NULL'
    ).fetchone()['n']

    synced_stamnrs = set()
    for l in leerlingen:
        synced_stamnrs.add(l['stamnr'])
        db.execute('''
            INSERT INTO leerlingen (stamnr, naam, roepnaam, tussenvoegsel, achternaam, email, klas, leerjaar, studie, locatie, vertrokken_op, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, datetime('now'))
            ON CONFLICT(stamnr) DO UPDATE SET
                naam=excluded.naam, roepnaam=excluded.roepnaam, tussenvoegsel=excluded.tussenvoegsel,
                achternaam=excluded.achternaam, email=excluded.email, klas=excluded.klas,
                leerjaar=excluded.leerjaar, studie=excluded.studie, locatie=excluded.locatie,
                vertrokken_op=NULL, updated_at=datetime('now')
        ''', (
            l['stamnr'], l['naam'], l.get('roepnaam', ''), l.get('tussenvoegsel', ''),
            l.get('achternaam', ''), l.get('email', ''), l['klas'],
            l.get('leerjaar', ''), l.get('studie', ''), l.get('locatie', ''),
        ))

    summary = {'upserted': len(synced_stamnrs), 'vertrokken_marked': 0, 'brake_triggered': False}

    # Brake: empty list, or suspiciously small vs the prior population.
    if not synced_stamnrs or (prior_active > 0 and len(synced_stamnrs) < VERTROKKEN_BRAKE_FRACTION * prior_active):
        summary['brake_triggered'] = True
        db.commit()
        return summary

    placeholders = ','.join('?' * len(synced_stamnrs))
    cur = db.execute(f'''
        UPDATE leerlingen SET vertrokken_op = date('now'), updated_at = datetime('now')
        WHERE stamnr NOT IN ({placeholders}) AND vertrokken_op IS NULL
    ''', list(synced_stamnrs))
    summary['vertrokken_marked'] = cur.rowcount
    db.commit()
    return summary


def import_voorinschrijvingen(db, leerlingen, schooljaar):
    """Upsert pre-registration students for an upcoming school year.

    Writes klasloos (klas='') with nieuw_voor_schooljaar=schooljaar set. Does NOT
    mark anyone vertrokken (unlike sync_leerlingen_to_db) and leaves the existing
    klas of an already-known student untouched (a doorstromer keeps its current
    class). Returns {'imported': <count>}.
    """
    imported = 0
    for l in leerlingen:
        db.execute('''
            INSERT INTO leerlingen
                (stamnr, naam, roepnaam, tussenvoegsel, achternaam, email,
                 klas, leerjaar, studie, locatie, nieuw_voor_schooljaar, vertrokken_op, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, '', '', '', ?, ?, NULL, datetime('now'))
            ON CONFLICT(stamnr) DO UPDATE SET
                naam=excluded.naam, roepnaam=excluded.roepnaam, tussenvoegsel=excluded.tussenvoegsel,
                achternaam=excluded.achternaam, email=excluded.email, locatie=excluded.locatie,
                nieuw_voor_schooljaar=excluded.nieuw_voor_schooljaar,
                vertrokken_op=NULL, updated_at=datetime('now')
        ''', (
            l['stamnr'], l['naam'], l.get('roepnaam', ''), l.get('tussenvoegsel', ''),
            l.get('achternaam', ''), l.get('email', ''), l.get('locatie', ''), schooljaar,
        ))
        imported += 1
    db.commit()
    return {'imported': imported}
