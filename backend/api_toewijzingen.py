from flask import Blueprint, request, jsonify, g, session
from auth import login_required

toewijzingen_bp = Blueprint('toewijzingen', __name__, url_prefix='/api')

@toewijzingen_bp.route('/kluisjes/<int:kid>/toewijzen', methods=['POST'])
@login_required
def toewijzen(kid):
    kluisje = g.db.execute('SELECT * FROM kluisjes WHERE id = ? AND verwijderd = 0', (kid,)).fetchone()
    if not kluisje:
        return jsonify({'error': 'Kluisje niet gevonden'}), 404
    if kluisje['status'] == 'uitgeleend':
        return jsonify({'error': 'Kluisje is al uitgeleend'}), 409

    data = request.get_json() or {}
    for field in ('leerling_stamnr', 'leerling_naam', 'periode_van', 'periode_tot'):
        if not data.get(field):
            return jsonify({'error': f'{field} is verplicht'}), 400
    user = session.get('user', {})
    cur = g.db.execute('''
        INSERT INTO toewijzingen
        (kluisje_id, leerling_stamnr, leerling_naam, leerling_klas,
         periode_van, periode_tot, borgbedrag, borg_betaald, actief, aangemaakt_door)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, ?)
    ''', (
        kid, str(data['leerling_stamnr']).strip(), str(data['leerling_naam']).strip(),
        str(data.get('leerling_klas', '')).strip(),
        data['periode_van'], data['periode_tot'], data.get('borgbedrag', 0),
        1 if data.get('borg_betaald') else 0,
        user.get('displayName', ''),
    ))
    g.db.execute("UPDATE kluisjes SET status='uitgeleend', updated_at=datetime('now') WHERE id=?", (kid,))
    g.db.commit()
    row = g.db.execute('SELECT * FROM toewijzingen WHERE id = ?', (cur.lastrowid,)).fetchone()
    return jsonify(dict(row)), 201

@toewijzingen_bp.route('/toewijzingen/<int:tid>/beeindigen', methods=['POST'])
@login_required
def beeindigen(tid):
    toewijzing = g.db.execute('SELECT * FROM toewijzingen WHERE id = ? AND actief = 1', (tid,)).fetchone()
    if not toewijzing:
        return jsonify({'error': 'Toewijzing niet gevonden of al beëindigd'}), 404

    data = request.get_json()
    sleutel = 1 if data.get('sleutel_ingeleverd') else 0
    borg_terug = 1 if data.get('borg_teruggestort') else 0
    einddatum = data.get('einddatum', '')
    opmerking = data.get('opmerking', '')

    g.db.execute('''
        UPDATE toewijzingen SET actief=0, sleutel_ingeleverd=?, borg_teruggestort=?,
        einddatum=?, opmerking=?, updated_at=datetime('now') WHERE id=?
    ''', (sleutel, borg_terug, einddatum, opmerking, tid))

    g.db.execute("UPDATE kluisjes SET status='vrij', updated_at=datetime('now') WHERE id=?",
                 (toewijzing['kluisje_id'],))
    g.db.commit()
    row = g.db.execute('SELECT * FROM toewijzingen WHERE id = ?', (tid,)).fetchone()
    return jsonify(dict(row))

@toewijzingen_bp.route('/toewijzingen/bulk-beeindigen', methods=['POST'])
@login_required
def bulk_beeindigen():
    """Bulk end assignments. Body: { toewijzing_ids: [...], sleutel_ingeleverd, borg_teruggestort, einddatum }"""
    data = request.get_json() or {}
    ids = data.get('toewijzing_ids', [])
    if not ids or len(ids) > 500:
        return jsonify({'error': 'Maximaal 500 toewijzingen per keer'}), 400
    sleutel = 1 if data.get('sleutel_ingeleverd') else 0
    borg_terug = 1 if data.get('borg_teruggestort') else 0
    einddatum = data.get('einddatum', '')
    opmerking = data.get('opmerking', '')

    count = 0
    for tid in ids:
        toewijzing = g.db.execute('SELECT * FROM toewijzingen WHERE id = ? AND actief = 1', (tid,)).fetchone()
        if not toewijzing:
            continue
        g.db.execute('''
            UPDATE toewijzingen SET actief=0, sleutel_ingeleverd=?, borg_teruggestort=?,
            einddatum=?, opmerking=?, updated_at=datetime('now') WHERE id=?
        ''', (sleutel, borg_terug, einddatum, opmerking, tid))
        g.db.execute("UPDATE kluisjes SET status='vrij', updated_at=datetime('now') WHERE id=?",
                     (toewijzing['kluisje_id'],))
        count += 1

    g.db.commit()
    return jsonify({'ended': count, 'total': len(ids)})

@toewijzingen_bp.route('/toewijzingen/actief', methods=['GET'])
@login_required
def actieve_toewijzingen():
    """Get all active assignments, optionally filtered by vestiging_id and/or cluster_id."""
    vestiging_id = request.args.get('vestiging_id')
    cluster_id = request.args.get('cluster_id')
    query = '''
        SELECT t.*, k.kluisnummer, k.cluster_id, k.vestiging_id, c.naam as cluster_naam
        FROM toewijzingen t
        JOIN kluisjes k ON t.kluisje_id = k.id
        JOIN clusters c ON k.cluster_id = c.id
        WHERE t.actief = 1 AND k.verwijderd = 0
    '''
    params = []
    if vestiging_id:
        query += ' AND k.vestiging_id = ?'
        params.append(int(vestiging_id))
    if cluster_id:
        query += ' AND k.cluster_id = ?'
        params.append(int(cluster_id))
    query += ' ORDER BY k.kluisnummer'
    rows = g.db.execute(query, params).fetchall()
    return jsonify([dict(r) for r in rows])

@toewijzingen_bp.route('/kluisjes/<int:kid>/geschiedenis', methods=['GET'])
@login_required
def geschiedenis(kid):
    rows = g.db.execute(
        'SELECT * FROM toewijzingen WHERE kluisje_id = ? ORDER BY created_at DESC',
        (kid,)
    ).fetchall()
    return jsonify([dict(r) for r in rows])

@toewijzingen_bp.route('/toewijzingen/bulk', methods=['POST'])
@login_required
def bulk_toewijzen():
    data = request.get_json()
    toewijzingen = data.get('toewijzingen', [])
    periode_van = data['periode_van']
    periode_tot = data['periode_tot']
    borgbedrag = data.get('borgbedrag', 0)
    user = session.get('user', {})

    count = 0
    skipped = []
    for item in toewijzingen:
        kid = item['kluisje_id']
        kluisje = g.db.execute('SELECT * FROM kluisjes WHERE id = ? AND verwijderd = 0 AND status != ?',
                               (kid, 'uitgeleend')).fetchone()
        if not kluisje:
            skipped.append({'kluisje_id': kid, 'reden': 'Niet beschikbaar of al uitgeleend'})
            continue
        g.db.execute('''
            INSERT INTO toewijzingen
            (kluisje_id, leerling_stamnr, leerling_naam, leerling_klas,
             periode_van, periode_tot, borgbedrag, actief, aangemaakt_door)
            VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?)
        ''', (
            kid, item['leerling_stamnr'], item['leerling_naam'], item.get('leerling_klas', ''),
            periode_van, periode_tot, borgbedrag, user.get('displayName', ''),
        ))
        g.db.execute("UPDATE kluisjes SET status='uitgeleend', updated_at=datetime('now') WHERE id=?", (kid,))
        count += 1

    g.db.commit()
    return jsonify({'assigned': count, 'skipped': skipped}), 201
