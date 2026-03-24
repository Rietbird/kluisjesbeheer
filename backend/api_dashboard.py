from flask import Blueprint, jsonify, g
from auth import login_required

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/api')

@dashboard_bp.route('/dashboard/stats', methods=['GET'])
@login_required
def stats():
    rows = g.db.execute('''
        SELECT v.id, v.naam,
            COUNT(k.id) as totaal,
            SUM(CASE WHEN k.status='uitgeleend' THEN 1 ELSE 0 END) as uitgeleend,
            SUM(CASE WHEN k.status='vrij' THEN 1 ELSE 0 END) as vrij,
            SUM(CASE WHEN k.status='defect' THEN 1 ELSE 0 END) as defect
        FROM vestigingen v
        LEFT JOIN kluisjes k ON k.vestiging_id = v.id AND k.verwijderd = 0
        GROUP BY v.id
        ORDER BY v.naam
    ''').fetchall()

    result = []
    for r in rows:
        # Count lockers where key was not returned
        sleutel_count = g.db.execute('''
            SELECT COUNT(DISTINCT k.id) as cnt
            FROM kluisjes k
            JOIN toewijzingen t ON k.id = t.kluisje_id
            WHERE k.vestiging_id = ? AND k.verwijderd = 0
              AND k.status = 'vrij' AND t.actief = 0
              AND t.sleutel_ingeleverd = 0
              AND t.id = (SELECT MAX(t2.id) FROM toewijzingen t2 WHERE t2.kluisje_id = k.id)
        ''', (r['id'],)).fetchone()['cnt']

        result.append({
            'vestiging_id': r['id'],
            'vestiging_naam': r['naam'],
            'totaal': r['totaal'] or 0,
            'uitgeleend': r['uitgeleend'] or 0,
            'vrij': r['vrij'] or 0,
            'defect': r['defect'] or 0,
            'sleutel_niet_ingeleverd': sleutel_count,
        })
    return jsonify(result)
