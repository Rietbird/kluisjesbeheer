"""TLS-cert beheer via Beheer -> Certificaat.

Endpoints (alleen beheerder):
  GET  /api/cert/info     - huidige cert metadata (issuer, CN, SAN, expiry)
  POST /api/cert/install  - upload nieuw cert+key, valideer, installeer via sudo helper
"""
import os
import subprocess
import tempfile
from datetime import datetime, timezone

from flask import Blueprint, request, jsonify
from auth import beheerder_required

cert_bp = Blueprint('cert', __name__, url_prefix='/api/cert')

NGINX_CERT_PATH = '/etc/nginx/ssl/self.crt'
STAGING_DIR = '/var/lib/kluisjesbeheer/cert-staging'
HELPER_CMD = ['sudo', '-n', '/usr/local/sbin/kluisjes-install-cert']


def _parse_cert(pem_bytes):
    """Parse PEM cert -> dict with issuer/subject/expiry/SAN. cryptography is
    al beschikbaar (transitive dep van msal/requests)."""
    from cryptography import x509
    from cryptography.hazmat.backends import default_backend
    cert = x509.load_pem_x509_certificate(pem_bytes, default_backend())

    def _cn(name):
        try:
            return name.get_attributes_for_oid(x509.NameOID.COMMON_NAME)[0].value
        except (IndexError, AttributeError):
            return ''

    sans = []
    try:
        ext = cert.extensions.get_extension_for_class(x509.SubjectAlternativeName)
        sans = [str(n.value) for n in ext.value]
    except x509.ExtensionNotFound:
        pass

    not_after = cert.not_valid_after_utc if hasattr(cert, 'not_valid_after_utc') else cert.not_valid_after.replace(tzinfo=timezone.utc)
    not_before = cert.not_valid_before_utc if hasattr(cert, 'not_valid_before_utc') else cert.not_valid_before.replace(tzinfo=timezone.utc)
    days_left = (not_after - datetime.now(timezone.utc)).days

    return {
        'cn': _cn(cert.subject),
        'issuer_cn': _cn(cert.issuer),
        'sans': sans,
        'valid_from': not_before.isoformat(),
        'valid_until': not_after.isoformat(),
        'days_left': days_left,
        'self_signed': cert.issuer == cert.subject,
    }


@cert_bp.route('/info', methods=['GET'])
@beheerder_required
def cert_info():
    if not os.path.exists(NGINX_CERT_PATH):
        return jsonify({'installed': False})
    try:
        with open(NGINX_CERT_PATH, 'rb') as f:
            info = _parse_cert(f.read())
        info['installed'] = True
        return jsonify(info)
    except Exception as e:
        return jsonify({'installed': False, 'error': str(e)}), 500


@cert_bp.route('/install', methods=['POST'])
@beheerder_required
def cert_install():
    cert_file = request.files.get('cert')
    key_file = request.files.get('key')
    if not cert_file or not key_file:
        return jsonify({'error': 'Upload zowel cert (.crt/.pem) als key (.key/.pem)'}), 400

    cert_bytes = cert_file.read()
    key_bytes = key_file.read()

    if len(cert_bytes) > 256 * 1024 or len(key_bytes) > 256 * 1024:
        return jsonify({'error': 'Bestand te groot (max 256 KB)'}), 400
    if b'-----BEGIN CERTIFICATE-----' not in cert_bytes:
        return jsonify({'error': 'Cert-bestand bevat geen PEM-certificaat'}), 400
    if b'-----BEGIN' not in key_bytes or b'PRIVATE KEY-----' not in key_bytes:
        return jsonify({'error': 'Key-bestand bevat geen PEM-private-key'}), 400

    # Parse cert om vroege fouten op te vangen
    try:
        info = _parse_cert(cert_bytes)
    except Exception as e:
        return jsonify({'error': f'Cert niet parsebaar: {e}'}), 400
    if info['days_left'] < 0:
        return jsonify({'error': 'Certificaat is verlopen'}), 400

    # Schrijf naar staging (atomair: tmp -> rename binnen dezelfde dir)
    if not os.path.isdir(STAGING_DIR):
        return jsonify({'error': f'Staging-map ontbreekt ({STAGING_DIR}). Draai install.sh opnieuw.'}), 500
    try:
        for name, data in (('cert.pem', cert_bytes), ('key.pem', key_bytes)):
            target = os.path.join(STAGING_DIR, name)
            with tempfile.NamedTemporaryFile(dir=STAGING_DIR, delete=False) as tmp:
                tmp.write(data)
                tmp_path = tmp.name
            os.chmod(tmp_path, 0o600)
            os.replace(tmp_path, target)
    except OSError as e:
        return jsonify({'error': f'Kan staging-bestanden niet schrijven: {e}'}), 500

    # Roep de helper aan via sudo (NOPASSWD voor exact dit commando)
    try:
        proc = subprocess.run(HELPER_CMD, capture_output=True, text=True, timeout=30)
    except FileNotFoundError:
        return jsonify({'error': 'sudo of helper-script ontbreekt'}), 500
    except subprocess.TimeoutExpired:
        return jsonify({'error': 'Cert-install duurde te lang (timeout)'}), 500

    if proc.returncode != 0:
        # Combineer stdout+stderr maar strip pad-info uit foutmeldingen
        msg = (proc.stderr or proc.stdout or 'Onbekende fout').strip()
        return jsonify({'error': f'Installatie mislukt: {msg}'}), 500

    return jsonify({'ok': True, 'message': proc.stdout.strip(), 'cert': info})
