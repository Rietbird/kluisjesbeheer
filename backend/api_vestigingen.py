from flask import Blueprint, request, jsonify, g
from auth import login_required

vestigingen_bp = Blueprint('vestigingen', __name__, url_prefix='/api')

@vestigingen_bp.route('/vestigingen', methods=['GET'])
@login_required
def list_vestigingen():
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
