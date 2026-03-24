from flask import Blueprint, request, jsonify
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
