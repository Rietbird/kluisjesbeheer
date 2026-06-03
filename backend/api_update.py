"""Self-update vanuit Beheer -> Onderhoud (alleen beheerder).

  GET  /api/update/check  - git fetch + vergelijk lokale HEAD met origin/master
  POST /api/update/apply  - pre-update backup + git pull + deps/build + restart
                            via root-helper (sudo), net als de cert-install.

Werkt alleen als de install een git-checkout is; anders een nette melding zodat
de UI gewoon geen update-knop toont (geen harde fout).
"""
import os
import subprocess

from flask import Blueprint, jsonify
from auth import beheerder_required

update_bp = Blueprint('update', __name__, url_prefix='/api/update')

# Repo-root = de map boven backend/ (daar staat .git bij een git-checkout install)
REPO_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BRANCH = 'master'
HELPER_CMD = ['sudo', '-n', '/usr/local/sbin/kluisjes-update']


def _git(*args, timeout=30):
    return subprocess.run(['git', '-C', REPO_DIR, *args],
                          capture_output=True, text=True, timeout=timeout)


def _is_git_checkout():
    return os.path.isdir(os.path.join(REPO_DIR, '.git'))


@update_bp.route('/check', methods=['GET'])
@beheerder_required
def check():
    """Hoeveel commits loopt de install achter op origin/master?"""
    if not _is_git_checkout():
        return jsonify({
            'git': False, 'available': False,
            'message': 'Deze installatie is geen git-checkout; automatisch updaten staat uit.',
        })
    try:
        fetch = _git('fetch', '--quiet', 'origin', BRANCH, timeout=45)
        if fetch.returncode != 0:
            return jsonify({'git': True, 'available': False,
                            'error': (fetch.stderr or 'git fetch faalde').strip()[:300]})
        local = _git('rev-parse', 'HEAD').stdout.strip()
        remote = _git('rev-parse', f'origin/{BRANCH}').stdout.strip()
        try:
            behind = int(_git('rev-list', '--count', f'HEAD..origin/{BRANCH}').stdout.strip())
        except ValueError:
            behind = 0
        try:
            build_current = int(_git('rev-list', '--count', 'HEAD').stdout.strip())
            build_latest = build_current + behind
        except ValueError:
            build_current = build_latest = 0
        commits = []
        if behind:
            log = _git('log', '--format=%h %s', f'HEAD..origin/{BRANCH}', '-n', '10')
            commits = [line for line in log.stdout.splitlines() if line.strip()]
        return jsonify({
            'git': True,
            'available': behind > 0,
            'behind': behind,
            'build': build_current,
            'build_latest': build_latest,
            'current': local[:7],
            'latest': remote[:7],
            'commits': commits,
        })
    except subprocess.TimeoutExpired:
        return jsonify({'git': True, 'available': False, 'error': 'git-bewerking duurde te lang'})
    except FileNotFoundError:
        return jsonify({'git': True, 'available': False, 'error': 'git niet gevonden op de server'})


@update_bp.route('/apply', methods=['POST'])
@beheerder_required
def apply():
    """Voer de update uit via de root-helper (backup + pull + deps/build + restart).

    De helper zet de service-herstart op de achtergrond (kleine delay), zodat
    dit antwoord de UI nog bereikt voordat gunicorn herstart."""
    if not _is_git_checkout():
        return jsonify({'error': 'Geen git-checkout — automatisch updaten is niet beschikbaar'}), 400
    try:
        proc = subprocess.run(HELPER_CMD, capture_output=True, text=True, timeout=300)
    except FileNotFoundError:
        return jsonify({'error': 'sudo of update-helper ontbreekt op de server'}), 500
    except subprocess.TimeoutExpired:
        return jsonify({'error': 'Update duurde te lang (timeout)'}), 500
    if proc.returncode != 0:
        msg = (proc.stderr or proc.stdout or 'Onbekende fout').strip()
        return jsonify({'error': f'Update mislukt: {msg[:500]}'}), 500
    return jsonify({'ok': True, 'message': proc.stdout.strip()[:800]})
