from flask import Blueprint, request, jsonify, g
from auth import login_required

clusters_bp = Blueprint('clusters', __name__, url_prefix='/api')

@clusters_bp.route('/vestigingen/<int:vid>/clusters', methods=['GET'])
@login_required
def list_clusters(vid):
    rows = g.db.execute('SELECT * FROM clusters WHERE vestiging_id = ? ORDER BY naam', (vid,)).fetchall()
    return jsonify([dict(r) for r in rows])

@clusters_bp.route('/clusters', methods=['POST'])
@login_required
def create_cluster():
    data = request.get_json()
    vestiging_id = data.get('vestiging_id')
    naam = data.get('naam', '').strip()
    if not naam or not vestiging_id:
        return jsonify({'error': 'vestiging_id en naam zijn verplicht'}), 400
    standaard_borg = data.get('standaard_borg', 0.0)
    cur = g.db.execute(
        'INSERT INTO clusters (vestiging_id, naam, standaard_borg) VALUES (?, ?, ?)',
        (vestiging_id, naam, standaard_borg)
    )
    g.db.commit()
    row = g.db.execute('SELECT * FROM clusters WHERE id = ?', (cur.lastrowid,)).fetchone()
    return jsonify(dict(row)), 201

@clusters_bp.route('/clusters/<int:cid>', methods=['PUT'])
@login_required
def update_cluster(cid):
    row = g.db.execute('SELECT * FROM clusters WHERE id = ?', (cid,)).fetchone()
    if not row:
        return jsonify({'error': 'Niet gevonden'}), 404
    data = request.get_json()
    naam = data.get('naam', '').strip() if 'naam' in data else row['naam']
    if not naam:
        return jsonify({'error': 'Naam is verplicht'}), 400
    standaard_borg = data.get('standaard_borg', row['standaard_borg'])
    g.db.execute(
        "UPDATE clusters SET naam=?, standaard_borg=?, updated_at=datetime('now') WHERE id=?",
        (naam, standaard_borg, cid)
    )
    g.db.commit()
    row = g.db.execute('SELECT * FROM clusters WHERE id = ?', (cid,)).fetchone()
    return jsonify(dict(row))

@clusters_bp.route('/clusters/<int:cid>', methods=['DELETE'])
@login_required
def delete_cluster(cid):
    row = g.db.execute('SELECT id FROM clusters WHERE id = ?', (cid,)).fetchone()
    if not row:
        return jsonify({'error': 'Niet gevonden'}), 404
    has_toewijzingen = g.db.execute('''
        SELECT COUNT(*) as cnt FROM toewijzingen t
        JOIN kluisjes k ON t.kluisje_id = k.id
        WHERE k.cluster_id = ?
    ''', (cid,)).fetchone()['cnt']
    if has_toewijzingen > 0:
        return jsonify({'error': 'Kan niet verwijderen: er zijn (historische) toewijzingen'}), 409
    g.db.execute('DELETE FROM kluisjes WHERE cluster_id = ?', (cid,))
    g.db.execute('DELETE FROM clusters WHERE id = ?', (cid,))
    g.db.commit()
    return jsonify({'ok': True})


@clusters_bp.route('/clusters/<int:cid>/verplaats-reeks', methods=['POST'])
@login_required
def verplaats_reeks(cid):
    """Verplaats bestaande kluisjes (op numeriek bereik) naar dit cluster.

    Body: { prefix, van, tot }. Alleen binnen dezelfde vestiging.
    """
    doel = g.db.execute('SELECT id, vestiging_id FROM clusters WHERE id = ?', (cid,)).fetchone()
    if not doel:
        return jsonify({'error': 'Doelcluster niet gevonden'}), 404
    data = request.get_json() or {}
    prefix = str(data.get('prefix', ''))
    try:
        van = int(data.get('van'))
        tot = int(data.get('tot'))
    except (TypeError, ValueError):
        return jsonify({'error': 'van en tot moeten getallen zijn'}), 400
    if van > tot:
        return jsonify({'error': 'van mag niet groter zijn dan tot'}), 400

    import re
    rows = g.db.execute(
        'SELECT id, kluisnummer, vestiging_id FROM kluisjes WHERE verwijderd = 0'
    ).fetchall()
    te_verplaatsen = []
    for r in rows:
        m = re.match(r'^(.*?)(\d+)(.*)$', r['kluisnummer'] or '')
        if not m:
            continue
        if m.group(1) != prefix:
            continue
        getal = int(m.group(2))
        if not (van <= getal <= tot):
            continue
        if r['vestiging_id'] != doel['vestiging_id']:
            return jsonify({'error': 'Kluisje hoort bij een andere vestiging dan het doelcluster'}), 409
        te_verplaatsen.append(r['id'])

    for kid in te_verplaatsen:
        g.db.execute(
            "UPDATE kluisjes SET cluster_id = ?, updated_at = datetime('now') WHERE id = ?",
            (cid, kid)
        )
    g.db.commit()
    return jsonify({'verplaatst': len(te_verplaatsen)}), 200


@clusters_bp.route('/clusters/<int:cid>/verplaats-selectie', methods=['POST'])
@login_required
def verplaats_selectie(cid):
    """Verplaats geselecteerde kluisjes naar dit cluster (zelfde vestiging)."""
    doel = g.db.execute('SELECT id, vestiging_id FROM clusters WHERE id = ?', (cid,)).fetchone()
    if not doel:
        return jsonify({'error': 'Doelcluster niet gevonden'}), 404
    data = request.get_json() or {}
    ids = data.get('kluisje_ids', [])
    if not ids:
        return jsonify({'error': 'Geen kluisjes geselecteerd'}), 400
    rows = g.db.execute(
        'SELECT id, vestiging_id FROM kluisjes WHERE id IN (%s) AND verwijderd = 0'
        % ','.join('?' * len(ids)), ids
    ).fetchall()
    for r in rows:
        if r['vestiging_id'] != doel['vestiging_id']:
            return jsonify({'error': 'Kluisje hoort bij een andere vestiging dan het doelcluster'}), 409
    for r in rows:
        g.db.execute(
            "UPDATE kluisjes SET cluster_id = ?, updated_at = datetime('now') WHERE id = ?",
            (cid, r['id'])
        )
    g.db.commit()
    return jsonify({'verplaatst': len(rows)}), 200
