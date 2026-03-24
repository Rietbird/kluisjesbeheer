from flask import Blueprint, request, jsonify, g
from auth import login_required

instellingen_bp = Blueprint('instellingen', __name__, url_prefix='/api')

@instellingen_bp.route('/instellingen', methods=['GET'])
@login_required
def get_instellingen():
    rows = g.db.execute('SELECT key, value FROM instellingen').fetchall()
    return jsonify({r['key']: r['value'] for r in rows})

@instellingen_bp.route('/instellingen', methods=['PUT'])
@login_required
def update_instellingen():
    data = request.get_json()
    for key, value in data.items():
        g.db.execute(
            'INSERT INTO instellingen (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value=?',
            (key, str(value), str(value))
        )
    g.db.commit()
    return jsonify({'ok': True})
