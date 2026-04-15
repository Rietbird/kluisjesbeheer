"""Backup management API — beheerder only."""
import os
from datetime import datetime
from flask import Blueprint, jsonify, g, send_from_directory, session
from auth import login_required
from backup import BACKUP_DIR, create_backup, cleanup_backups

backup_bp = Blueprint('backup', __name__, url_prefix='/api')

DB_PATH = os.path.join(os.path.dirname(__file__), 'kluisjesbeheer.db')


def _beheerder_required():
    user = session.get('user', {})
    if not user.get('is_beheerder'):
        return jsonify({'error': 'Alleen beheerders'}), 403
    return None


@backup_bp.route('/backups', methods=['GET'])
@login_required
def list_backups():
    err = _beheerder_required()
    if err:
        return err

    os.makedirs(BACKUP_DIR, exist_ok=True)
    files = sorted([
        f for f in os.listdir(BACKUP_DIR)
        if f.startswith('kluisjesbeheer_') and f.endswith('.db')
    ], reverse=True)

    backups = []
    for f in files:
        path = os.path.join(BACKUP_DIR, f)
        stat = os.stat(path)
        backups.append({
            'naam': f,
            'grootte': stat.st_size,
            'datum': datetime.fromtimestamp(stat.st_mtime).isoformat(),
        })
    return jsonify(backups)


@backup_bp.route('/backups/create', methods=['POST'])
@login_required
def trigger_backup():
    err = _beheerder_required()
    if err:
        return err

    path = create_backup(DB_PATH, label='handmatig')
    cleanup_backups()
    naam = os.path.basename(path)
    return jsonify({'ok': True, 'naam': naam})


@backup_bp.route('/backups/<naam>/download', methods=['GET'])
@login_required
def download_backup(naam):
    err = _beheerder_required()
    if err:
        return err

    # Prevent path traversal
    if '/' in naam or '\\' in naam or '..' in naam:
        return jsonify({'error': 'Ongeldige bestandsnaam'}), 400

    path = os.path.join(BACKUP_DIR, naam)
    if not os.path.isfile(path):
        return jsonify({'error': 'Backup niet gevonden'}), 404

    return send_from_directory(BACKUP_DIR, naam, as_attachment=True)


@backup_bp.route('/backups/<naam>/restore', methods=['POST'])
@login_required
def restore_backup(naam):
    import sqlite3
    from flask import request
    err = _beheerder_required()
    if err:
        return err

    # Require an explicit confirmation phrase to prevent accidents
    data = request.get_json(silent=True) or {}
    if data.get('bevestiging') != 'RESTORE':
        return jsonify({'error': 'Bevestig door "RESTORE" te sturen in het veld bevestiging'}), 400

    if '/' in naam or '\\' in naam or '..' in naam:
        return jsonify({'error': 'Ongeldige bestandsnaam'}), 400

    src_path = os.path.join(BACKUP_DIR, naam)
    if not os.path.isfile(src_path):
        return jsonify({'error': 'Backup niet gevonden'}), 404

    # Safety backup of the current live DB before overwriting
    safety = create_backup(DB_PATH, label='pre-restore')

    # Use SQLite backup API: safe while app has open connections
    src = sqlite3.connect(src_path)
    dst = sqlite3.connect(DB_PATH)
    try:
        src.backup(dst)
    finally:
        dst.close()
        src.close()

    cleanup_backups()
    return jsonify({
        'ok': True,
        'restored_from': naam,
        'safety_backup': os.path.basename(safety),
    })
