import os
from flask import Blueprint, request, jsonify, g, send_from_directory
from auth import login_required

instellingen_bp = Blueprint('instellingen', __name__, url_prefix='/api')

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), '..', 'frontend', 'dist', 'img')

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

@instellingen_bp.route('/instellingen/logo', methods=['POST'])
@login_required
def upload_logo():
    file = request.files.get('file')
    if not file:
        return jsonify({'error': 'Bestand is verplicht'}), 400
    filename = file.filename or ''
    if not filename.lower().endswith(('.png', '.jpg', '.jpeg', '.svg')):
        return jsonify({'error': 'Alleen .png, .jpg of .svg bestanden'}), 400
    ext = os.path.splitext(filename)[1].lower()
    save_name = f'school-logo{ext}'
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    import time
    file.save(os.path.join(UPLOAD_DIR, save_name))
    logo_path = f'/img/{save_name}?v={int(time.time())}'
    g.db.execute(
        'INSERT INTO instellingen (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value=?',
        ('schoolLogo', logo_path, logo_path)
    )
    g.db.commit()
    return jsonify({'ok': True, 'schoolLogo': logo_path})
