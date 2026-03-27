from flask import Blueprint, request, jsonify, g
from auth import login_required
from magister_client import magister

magister_bp = Blueprint('magister', __name__, url_prefix='/api')

@magister_bp.route('/magister/leerlingen', methods=['GET'])
@login_required
def search_leerlingen():
    q = request.args.get('q', '').strip()
    if len(q) < 2:
        return jsonify([])
    return jsonify(magister.search_leerlingen(q))

@magister_bp.route('/magister/klassen', methods=['GET'])
@login_required
def get_klassen():
    return jsonify(magister.get_klassen())

@magister_bp.route('/magister/flush-cache', methods=['POST'])
@login_required
def flush_cache():
    """Clear Magister API cache, forcing fresh data on next request."""
    magister.flush_cache()
    return jsonify({'ok': True})

@magister_bp.route('/magister/sync-leerlingen', methods=['POST'])
@login_required
def sync_leerlingen():
    """Refresh the student list from Magister. Flushes cache and fetches fresh data."""
    try:
        magister.flush_cache()
        leerlingen = magister.get_leerlingen()
        klassen = sorted(set(l['klas'] for l in leerlingen if l['klas']))
    except ConnectionError as e:
        return jsonify({'error': f'Magister niet bereikbaar: {e}'}), 502

    return jsonify({
        'leerlingen': len(leerlingen),
        'klassen': len(klassen),
    })
