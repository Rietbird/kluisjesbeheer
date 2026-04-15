from flask import Blueprint, request, jsonify, g
from auth import login_required

vestigingen_bp = Blueprint('vestigingen', __name__, url_prefix='/api')

@vestigingen_bp.route('/vestigingen', methods=['GET'])
@login_required
def list_vestigingen():
    from flask import session
    user = session.get('user', {})
    allowed_ids = user.get('allowed_vestiging_ids', [])
    if not user.get('is_beheerder') and allowed_ids:
        placeholders = ','.join('?' * len(allowed_ids))
        rows = g.db.execute(
            f'SELECT * FROM vestigingen WHERE id IN ({placeholders}) ORDER BY naam', allowed_ids
        ).fetchall()
    else:
        rows = g.db.execute('SELECT * FROM vestigingen ORDER BY naam').fetchall()
    return jsonify([dict(r) for r in rows])

@vestigingen_bp.route('/vestigingen', methods=['POST'])
@login_required
def create_vestiging():
    data = request.get_json()
    naam = data.get('naam', '').strip()
    if not naam:
        return jsonify({'error': 'Naam is verplicht'}), 400
    adres = data.get('adres', '')
    cur = g.db.execute('INSERT INTO vestigingen (naam, adres) VALUES (?, ?)', (naam, adres))
    g.db.commit()
    row = g.db.execute('SELECT * FROM vestigingen WHERE id = ?', (cur.lastrowid,)).fetchone()
    return jsonify(dict(row)), 201

@vestigingen_bp.route('/vestigingen/<int:vid>', methods=['PUT'])
@login_required
def update_vestiging(vid):
    row = g.db.execute('SELECT * FROM vestigingen WHERE id = ?', (vid,)).fetchone()
    if not row:
        return jsonify({'error': 'Niet gevonden'}), 404
    data = request.get_json()
    naam = data.get('naam', '').strip()
    if not naam:
        return jsonify({'error': 'Naam is verplicht'}), 400
    adres = data.get('adres', '')
    g.db.execute("UPDATE vestigingen SET naam=?, adres=?, updated_at=datetime('now') WHERE id=?", (naam, adres, vid))
    g.db.commit()
    row = g.db.execute('SELECT * FROM vestigingen WHERE id = ?', (vid,)).fetchone()
    return jsonify(dict(row))

@vestigingen_bp.route('/vestigingen/<int:vid>/borg', methods=['PUT'])
@login_required
def update_borg(vid):
    data = request.get_json()
    borg_actief = 1 if data.get('borg_actief') else 0
    g.db.execute('UPDATE vestigingen SET borg_actief=? WHERE id=?', (borg_actief, vid))
    g.db.commit()
    return jsonify({'ok': True, 'borg_actief': bool(borg_actief)})

@vestigingen_bp.route('/vestigingen/<int:vid>/kleur', methods=['PUT'])
@login_required
def update_kleur(vid):
    data = request.get_json()
    kleur = (data.get('kleur') or '').strip()
    # Valideer: leeg (reset) of een hex kleur
    import re
    if kleur and not re.match(r'^#[0-9a-fA-F]{6}$', kleur):
        return jsonify({'error': 'Ongeldige kleurwaarde'}), 400
    g.db.execute('UPDATE vestigingen SET kleur=? WHERE id=?', (kleur or None, vid))
    g.db.commit()
    return jsonify({'ok': True, 'kleur': kleur or None})

@vestigingen_bp.route('/vestigingen/<int:vid>/locaties', methods=['GET'])
@login_required
def get_vestiging_locaties(vid):
    rows = g.db.execute(
        'SELECT locatie FROM vestigingen_locaties WHERE vestiging_id = ? ORDER BY locatie', (vid,)
    ).fetchall()
    return jsonify([r['locatie'] for r in rows])

@vestigingen_bp.route('/vestigingen/<int:vid>/locaties', methods=['PUT'])
@login_required
def set_vestiging_locaties(vid):
    """Stel in welke Magister-locaties bij een vestiging horen. Body: { locaties: [...] }"""
    data = request.get_json() or {}
    locaties = data.get('locaties', [])
    if not g.db.execute('SELECT id FROM vestigingen WHERE id = ?', (vid,)).fetchone():
        return jsonify({'error': 'Vestiging niet gevonden'}), 404
    g.db.execute('DELETE FROM vestigingen_locaties WHERE vestiging_id = ?', (vid,))
    for loc in locaties:
        g.db.execute(
            'INSERT OR IGNORE INTO vestigingen_locaties (vestiging_id, locatie) VALUES (?, ?)',
            (vid, loc)
        )
    g.db.commit()
    return jsonify({'vestiging_id': vid, 'locaties': locaties})

@vestigingen_bp.route('/vestigingen/<int:vid>/reset', methods=['POST'])
@login_required
def reset_vestiging(vid):
    """Delete all kluisjes + toewijzingen for a vestiging, keep vestiging + clusters."""
    from flask import session
    user = session.get('user', {})
    if not user.get('is_beheerder'):
        return jsonify({'error': 'Alleen beheerders'}), 403
    row = g.db.execute('SELECT id, naam FROM vestigingen WHERE id = ?', (vid,)).fetchone()
    if not row:
        return jsonify({'error': 'Niet gevonden'}), 404
    # Delete toewijzingen for kluisjes in this vestiging
    deleted_toewijzingen = g.db.execute('''
        DELETE FROM toewijzingen WHERE kluisje_id IN (
            SELECT id FROM kluisjes WHERE vestiging_id = ?
        )
    ''', (vid,)).rowcount
    # Delete all kluisjes (including soft-deleted)
    deleted_kluisjes = g.db.execute(
        'DELETE FROM kluisjes WHERE vestiging_id = ?', (vid,)
    ).rowcount
    g.db.commit()
    return jsonify({
        'ok': True,
        'deleted_kluisjes': deleted_kluisjes,
        'deleted_toewijzingen': deleted_toewijzingen,
    })


@vestigingen_bp.route('/vestigingen/<int:vid>', methods=['DELETE'])
@login_required
def delete_vestiging(vid):
    row = g.db.execute('SELECT id FROM vestigingen WHERE id = ?', (vid,)).fetchone()
    if not row:
        return jsonify({'error': 'Niet gevonden'}), 404
    # Check for ANY toewijzingen (active or historical) — FK constraints prevent deletion otherwise
    has_toewijzingen = g.db.execute('''
        SELECT COUNT(*) as cnt FROM toewijzingen t
        JOIN kluisjes k ON t.kluisje_id = k.id
        WHERE k.vestiging_id = ?
    ''', (vid,)).fetchone()['cnt']
    if has_toewijzingen > 0:
        # Check if any are active
        active = g.db.execute('''
            SELECT COUNT(*) as cnt FROM toewijzingen t
            JOIN kluisjes k ON t.kluisje_id = k.id
            WHERE k.vestiging_id = ? AND t.actief = 1
        ''', (vid,)).fetchone()['cnt']
        if active > 0:
            return jsonify({'error': 'Kan niet verwijderen: er zijn actieve toewijzingen'}), 409
        return jsonify({'error': 'Kan niet verwijderen: er zijn historische toewijzingen. Verwijder eerst de kluisjes.'}), 409
    g.db.execute('DELETE FROM kluisjes WHERE vestiging_id = ?', (vid,))
    g.db.execute('DELETE FROM clusters WHERE vestiging_id = ?', (vid,))
    g.db.execute('DELETE FROM vestigingen WHERE id = ?', (vid,))
    g.db.commit()
    return jsonify({'ok': True})
