from flask import Blueprint, request, jsonify, g
from auth import beheerder_required
from magister_client import magister, safe_error as _safe_error
from leerling_sync import import_voorinschrijvingen

voorinschrijving_bp = Blueprint('voorinschrijving', __name__, url_prefix='/api')

DEFAULT_LIST = 'sql-get-kluisjes-voorinschrijving'


def _peildatum_voor(schooljaar):
    """'2026-2027' -> '2026-08-01' (1 augustus = schooljaarwissel)."""
    start = schooljaar.split('-')[0]
    return f'{start}-08-01'


def _map_record(rec):
    """DD-lijst-record -> leerling-dict; stelt de volledige naam samen."""
    roepnaam = (rec.get('Voornaam') or '').strip()
    tussenvoegsel = (rec.get('Tussenvoegsel') or '').strip()
    achternaam = (rec.get('Achternaam') or '').strip()
    naam = ' '.join(p for p in [roepnaam, tussenvoegsel, achternaam] if p)
    return {
        'stamnr': (rec.get('Leerlingnummer') or '').strip(),
        'naam': naam,
        'roepnaam': roepnaam,
        'tussenvoegsel': tussenvoegsel,
        'achternaam': achternaam,
        'email': (rec.get('Email') or '').strip(),
        'locatie': (rec.get('Locatie') or '').strip(),
    }


@voorinschrijving_bp.route('/leerlingen/import-voorinschrijving', methods=['POST'])
@beheerder_required
def import_voorinschrijving():
    data = request.get_json() or {}
    schooljaar = (data.get('schooljaar') or '').strip()
    if not schooljaar or '-' not in schooljaar:
        return jsonify({'error': 'schooljaar is verplicht (vorm "2026-2027")'}), 400

    row = g.db.execute("SELECT value FROM instellingen WHERE key='voorinschrijving_lijst'").fetchone()
    layout = row['value'] if row and row['value'] else DEFAULT_LIST
    parameters = f'peildatum={_peildatum_voor(schooljaar)}'

    try:
        magister.flush_cache()
        records = magister.get_data(layout, parameters)
    except ConnectionError as e:
        return jsonify({'error': _safe_error(e)}), 502

    leerlingen = [_map_record(r) for r in records if (r.get('Leerlingnummer') or '').strip()]
    summary = import_voorinschrijvingen(g.db, leerlingen, schooljaar)
    return jsonify({'geimporteerd': summary['imported'], 'schooljaar': schooljaar, 'bron': 'webservice'})
