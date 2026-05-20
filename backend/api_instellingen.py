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

MAGISTER_SETTINGS_KEYS = {'magister_url', 'magister_user', 'magister_pass'}


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
    logo_path = f'/api/uploads/img/{save_name}?v={int(time.time())}'
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


def _beheerder_required():
    from flask import session
    user = session.get('user', {})
    if not user.get('is_beheerder'):
        return jsonify({'error': 'Alleen beheerders'}), 403
    return None


@instellingen_bp.route('/magister/config', methods=['GET'])
@login_required
def get_magister_config():
    """Return Magister API config. Password is masked."""
    err = _beheerder_required()
    if err:
        return err
    rows = g.db.execute(
        "SELECT key, value FROM instellingen WHERE key IN ('magister_url', 'magister_user', 'magister_pass')"
    ).fetchall()
    cfg = {r['key']: r['value'] for r in rows}
    has_pass = bool(cfg.get('magister_pass'))
    return jsonify({
        'magister_url': cfg.get('magister_url', ''),
        'magister_user': cfg.get('magister_user', ''),
        'magister_pass_set': has_pass,
        'configured': bool(cfg.get('magister_url') and cfg.get('magister_user') and has_pass),
    })


@instellingen_bp.route('/magister/config', methods=['PUT'])
@login_required
def update_magister_config():
    """Save Magister API config. Password is encrypted."""
    err = _beheerder_required()
    if err:
        return err
    from crypto_util import encrypt
    data = request.get_json()
    if not data or not isinstance(data, dict):
        return jsonify({'error': 'Ongeldig verzoek'}), 400

    for key in ('magister_url', 'magister_user'):
        if key in data:
            val = str(data[key]).strip()
            g.db.execute(
                'INSERT INTO instellingen (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value=?',
                (key, val, val)
            )

    if 'magister_pass' in data and data['magister_pass']:
        encrypted = encrypt(data['magister_pass'])
        g.db.execute(
            'INSERT INTO instellingen (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value=?',
            ('magister_pass', encrypted, encrypted)
        )

    g.db.commit()

    # Flush the cached Magister session-token in this worker -- otherwise the
    # next sync attempt may still use the old credentials (TTL 60s). Note:
    # under multi-worker Gunicorn this only flushes the current worker; other
    # workers' tokens still expire naturally within CACHE_TTL.
    from magister_client import magister
    magister.flush_cache()

    return jsonify({'ok': True})
