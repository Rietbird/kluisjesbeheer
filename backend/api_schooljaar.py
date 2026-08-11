from flask import Blueprint, jsonify, g
from auth import login_required
from schooljaar import periode_voor

schooljaar_bp = Blueprint('schooljaar', __name__, url_prefix='/api')


@schooljaar_bp.route('/schooljaar/periode', methods=['GET'])
@login_required
def get_periode():
    sj, van, tot = periode_voor(g.db)
    return jsonify({
        'schooljaar': sj,
        'periode_van': van,
        'periode_tot': tot,
    })
