import csv
import io
from flask import Blueprint, request, jsonify, g
from auth import login_required

kluisjes_bp = Blueprint('kluisjes', __name__, url_prefix='/api')

@kluisjes_bp.route('/clusters/<int:cid>/kluisjes', methods=['GET'])
@login_required
def list_kluisjes(cid):
    rows = g.db.execute(
        'SELECT * FROM kluisjes WHERE cluster_id = ? AND verwijderd = 0 ORDER BY kluisnummer',
        (cid,)
    ).fetchall()
    return jsonify([dict(r) for r in rows])

@kluisjes_bp.route('/kluisjes', methods=['GET'])
@login_required
def search_kluisjes():
    q = request.args.get('q', '').strip()
    vestiging_id = request.args.get('vestiging_id')
    status = request.args.get('status')

    query = '''
        SELECT k.*, c.naam as cluster_naam,
               t.leerling_naam, t.leerling_stamnr, t.leerling_klas,
               t.periode_van, t.periode_tot,
               CASE
                 WHEN k.status = 'vrij' AND EXISTS (
                   SELECT 1 FROM toewijzingen t2
                   WHERE t2.kluisje_id = k.id AND t2.actief = 0 AND t2.sleutel_ingeleverd = 0
                   AND t2.id = (SELECT MAX(t3.id) FROM toewijzingen t3 WHERE t3.kluisje_id = k.id)
                 ) THEN 1 ELSE 0
               END as _sleutel_niet_ingeleverd
        FROM kluisjes k
        JOIN clusters c ON k.cluster_id = c.id
        LEFT JOIN toewijzingen t ON k.id = t.kluisje_id AND t.actief = 1
        WHERE k.verwijderd = 0
    '''
    params = []

    if vestiging_id:
        query += ' AND k.vestiging_id = ?'
        params.append(int(vestiging_id))
    if status:
        query += ' AND k.status = ?'
        params.append(status)
    if q:
        # Escape LIKE wildcards in user input
        q_escaped = q.replace('%', '\\%').replace('_', '\\_')
        query += """ AND (k.kluisnummer LIKE ? ESCAPE '\\' OR k.sleutelnummer LIKE ? ESCAPE '\\'
                     OR t.leerling_naam LIKE ? ESCAPE '\\' OR t.leerling_stamnr LIKE ? ESCAPE '\\')"""
        like = f'%{q_escaped}%'
        params.extend([like, like, like, like])

    query += ' ORDER BY k.kluisnummer'
    rows = g.db.execute(query, params).fetchall()
    return jsonify([dict(r) for r in rows])

@kluisjes_bp.route('/kluisjes/<int:kid>', methods=['GET'])
@login_required
def get_kluisje(kid):
    row = g.db.execute('SELECT * FROM kluisjes WHERE id = ? AND verwijderd = 0', (kid,)).fetchone()
    if not row:
        return jsonify({'error': 'Niet gevonden'}), 404
    return jsonify(dict(row))

@kluisjes_bp.route('/clusters/<int:cid>/kluisjes', methods=['POST'])
@login_required
def create_kluisje(cid):
    data = request.get_json()
    kluisnummer = data.get('kluisnummer', '').strip()
    if not kluisnummer:
        return jsonify({'error': 'Kluisnummer is verplicht'}), 400

    cluster = g.db.execute('SELECT vestiging_id FROM clusters WHERE id = ?', (cid,)).fetchone()
    if not cluster:
        return jsonify({'error': 'Cluster niet gevonden'}), 404

    vestiging_id = cluster['vestiging_id']
    sleutelnummer = data.get('sleutelnummer', '')
    locatie = data.get('locatie', '')

    try:
        cur = g.db.execute(
            'INSERT INTO kluisjes (cluster_id, vestiging_id, kluisnummer, sleutelnummer, locatie, status) VALUES (?, ?, ?, ?, ?, ?)',
            (cid, vestiging_id, kluisnummer, sleutelnummer, locatie, 'vrij')
        )
        g.db.commit()
    except Exception as e:
        if 'UNIQUE' in str(e):
            return jsonify({'error': f'Kluisnummer {kluisnummer} bestaat al in deze vestiging'}), 409
        raise

    row = g.db.execute('SELECT * FROM kluisjes WHERE id = ?', (cur.lastrowid,)).fetchone()
    return jsonify(dict(row)), 201

@kluisjes_bp.route('/kluisjes/<int:kid>', methods=['PUT'])
@login_required
def update_kluisje(kid):
    data = request.get_json()
    row = g.db.execute('SELECT * FROM kluisjes WHERE id = ? AND verwijderd = 0', (kid,)).fetchone()
    if not row:
        return jsonify({'error': 'Niet gevonden'}), 404

    sleutelnummer = data.get('sleutelnummer', row['sleutelnummer'])
    locatie = data.get('locatie', row['locatie'])
    opmerkingen = data.get('opmerkingen', row['opmerkingen'])
    status = data.get('status', row['status'])

    g.db.execute(
        "UPDATE kluisjes SET sleutelnummer=?, locatie=?, opmerkingen=?, status=?, updated_at=datetime('now') WHERE id=?",
        (sleutelnummer, locatie, opmerkingen, status, kid)
    )
    g.db.commit()
    row = g.db.execute('SELECT * FROM kluisjes WHERE id = ?', (kid,)).fetchone()
    return jsonify(dict(row))

@kluisjes_bp.route('/kluisjes/<int:kid>', methods=['DELETE'])
@login_required
def delete_kluisje(kid):
    row = g.db.execute('SELECT id FROM kluisjes WHERE id = ? AND verwijderd = 0', (kid,)).fetchone()
    if not row:
        return jsonify({'error': 'Niet gevonden'}), 404
    active = g.db.execute(
        'SELECT COUNT(*) as cnt FROM toewijzingen WHERE kluisje_id = ? AND actief = 1', (kid,)
    ).fetchone()['cnt']
    if active > 0:
        return jsonify({'error': 'Kan niet verwijderen: er is een actieve toewijzing'}), 409
    g.db.execute("UPDATE kluisjes SET verwijderd = 1, updated_at = datetime('now') WHERE id = ?", (kid,))
    g.db.commit()
    return jsonify({'ok': True})

@kluisjes_bp.route('/kluisjes/import', methods=['POST'])
@login_required
def import_kluisjes():
    cluster_id = request.form.get('cluster_id')
    if not cluster_id:
        return jsonify({'error': 'cluster_id is verplicht'}), 400

    cluster = g.db.execute('SELECT vestiging_id FROM clusters WHERE id = ?', (int(cluster_id),)).fetchone()
    if not cluster:
        return jsonify({'error': 'Cluster niet gevonden'}), 404

    vestiging_id = cluster['vestiging_id']
    file = request.files.get('file')
    if not file:
        return jsonify({'error': 'CSV-bestand is verplicht'}), 400

    content = file.read().decode('utf-8')
    reader = csv.DictReader(io.StringIO(content), delimiter=';')

    count = 0
    try:
        for i, row in enumerate(reader, start=2):
            kluisnummer = row.get('kluisnummer', '').strip()
            sleutelnummer = row.get('sleutelnummer', '').strip()
            locatie = row.get('locatie', '').strip()
            if not kluisnummer:
                g.db.rollback()
                return jsonify({'error': f'Regel {i}: kluisnummer is leeg'}), 400
            g.db.execute(
                'INSERT INTO kluisjes (cluster_id, vestiging_id, kluisnummer, sleutelnummer, locatie, status) VALUES (?, ?, ?, ?, ?, ?)',
                (int(cluster_id), vestiging_id, kluisnummer, sleutelnummer, locatie, 'vrij')
            )
            count += 1
        g.db.commit()
    except Exception as e:
        g.db.rollback()
        if 'UNIQUE' in str(e):
            return jsonify({'error': f'Duplicaat kluisnummer gevonden'}), 400
        raise

    return jsonify({'imported': count}), 201
