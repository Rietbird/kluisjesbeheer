import os
import re
import time
from flask import Blueprint, request, jsonify, g, send_from_directory
from auth import login_required

instellingen_bp = Blueprint('instellingen', __name__, url_prefix='/api')

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), 'uploads', 'img')

ALLOWED_SETTINGS_KEYS = {
    'schoolNaam', 'schoolSubtitel', 'schoolKleur', 'schoolLogo', 'regio',
    'standaard_periode_van', 'standaard_periode_tot',
}


def _sanitize_svg(data):
    """Strip dangerous elements/attributes from SVG to prevent stored XSS."""
    dangerous_tags = re.compile(r'<\s*(script|iframe|object|embed|foreignObject|use)[^>]*>.*?</\s*\1\s*>', re.IGNORECASE | re.DOTALL)
    dangerous_self = re.compile(r'<\s*(script|iframe|object|embed|foreignObject|use)[^>]*/\s*>', re.IGNORECASE)
    on_handlers = re.compile(r'\s+on\w+\s*=\s*["\'][^"\']*["\']', re.IGNORECASE)
    data = dangerous_tags.sub('', data)
    data = dangerous_self.sub('', data)
    data = on_handlers.sub('', data)
    return data


@instellingen_bp.route('/instellingen', methods=['GET'])
@login_required
def get_instellingen():
    rows = g.db.execute('SELECT key, value FROM instellingen').fetchall()
    return jsonify({r['key']: r['value'] for r in rows})

@instellingen_bp.route('/instellingen', methods=['PUT'])
@login_required
def update_instellingen():
    data = request.get_json()
    if not data or not isinstance(data, dict):
        return jsonify({'error': 'Ongeldig verzoek'}), 400
    unknown = set(data.keys()) - ALLOWED_SETTINGS_KEYS
    if unknown:
        return jsonify({'error': f'Ongeldige keys: {", ".join(sorted(unknown))}'}), 400
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
    save_path = os.path.join(UPLOAD_DIR, save_name)
    if ext == '.svg':
        content = file.read().decode('utf-8', errors='replace')
        content = _sanitize_svg(content)
        with open(save_path, 'w', encoding='utf-8') as f:
            f.write(content)
    else:
        file.save(save_path)
    logo_path = f'/uploads/img/{save_name}?v={int(time.time())}'
    g.db.execute(
        'INSERT INTO instellingen (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value=?',
        ('schoolLogo', logo_path, logo_path)
    )
    g.db.commit()
    return jsonify({'ok': True, 'schoolLogo': logo_path})


@instellingen_bp.route('/uploads/img/<path:filename>')
def serve_upload(filename):
    """Serve uploaded images with restrictive Content-Type."""
    return send_from_directory(UPLOAD_DIR, filename)
