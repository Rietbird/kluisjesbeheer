import json
import os
from datetime import date, timedelta
from flask import Blueprint, jsonify, g
from auth import login_required

schooljaar_bp = Blueprint('schooljaar', __name__, url_prefix='/api')

_vakanties = None

def _load_vakanties():
    global _vakanties
    if _vakanties is None:
        path = os.path.join(os.path.dirname(__file__), 'schoolvakanties.json')
        with open(path) as f:
            _vakanties = json.load(f)
    return _vakanties

def _huidig_schooljaar():
    today = date.today()
    if today.month >= 8:
        return f"{today.year}-{today.year + 1}"
    else:
        return f"{today.year - 1}-{today.year}"

@schooljaar_bp.route('/schooljaar/periode', methods=['GET'])
@login_required
def get_periode():
    regio_row = g.db.execute("SELECT value FROM instellingen WHERE key = 'regio'").fetchone()
    regio = regio_row['value'] if regio_row else 'noord'

    vakanties = _load_vakanties()
    schooljaar = _huidig_schooljaar()
    jaar_data = vakanties.get(schooljaar, {})
    regio_data = jaar_data.get(regio, {})

    start_jaar = int(schooljaar.split('-')[0])
    periode_van = f"{start_jaar}-09-01"

    if regio_data.get('zomer_start'):
        zomer = date.fromisoformat(regio_data['zomer_start'])
        periode_tot = (zomer - timedelta(days=1)).isoformat()
    else:
        eind_jaar = int(schooljaar.split('-')[1])
        periode_tot = f"{eind_jaar}-07-01"

    return jsonify({
        'schooljaar': schooljaar,
        'regio': regio,
        'periode_van': periode_van,
        'periode_tot': periode_tot,
    })
