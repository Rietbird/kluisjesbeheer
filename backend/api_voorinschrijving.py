import re
from flask import Blueprint, request, jsonify, g
from auth import beheerder_required
from magister_client import magister, safe_error as _safe_error
from leerling_sync import import_voorinschrijvingen
from api_kluisjes import _safe_load_xlsx

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
    if not re.match(r'^\d{4}-\d{4}$', schooljaar):
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


def _cell_to_str(val):
    """Convert an openpyxl cell value to a clean string.
    Numbers (int/float) are formatted without a decimal point when integral."""
    if val is None:
        return ''
    if isinstance(val, float):
        if val == int(val):
            return str(int(val))
        return str(val)
    return str(val).strip()


@voorinschrijving_bp.route('/leerlingen/import-voorinschrijving-xlsx', methods=['POST'])
@beheerder_required
def import_voorinschrijving_xlsx():
    """Excel fallback: upload a .xlsx with columns Leerlingnummer/Stamnummer and Naam."""
    schooljaar = (request.form.get('schooljaar') or '').strip()
    if not re.match(r'^\d{4}-\d{4}$', schooljaar):
        return jsonify({'error': 'schooljaar is verplicht (vorm "2026-2027")'}), 400

    file = request.files.get('file')
    if not file:
        return jsonify({'error': 'Bestand is verplicht'}), 400

    filename = file.filename or ''
    if not filename.lower().endswith('.xlsx'):
        return jsonify({'error': 'Alleen .xlsx bestanden worden geaccepteerd'}), 400

    try:
        wb = _safe_load_xlsx(file)
    except Exception:
        return jsonify({'error': 'Kan bestand niet verwerken. Controleer het formaat.'}), 400

    try:
        ws = wb.active

        # Find the header row (first non-empty row) and map column indices
        col_stamnr = None
        col_naam = None
        col_locatie = None
        col_email = None
        header_row_idx = None

        for i, row in enumerate(ws.iter_rows(values_only=True), start=1):
            # Skip empty rows
            if not any(c is not None for c in row):
                continue
            # This is the header row
            header_row_idx = i
            for j, cell in enumerate(row):
                label = str(cell).strip().lower() if cell is not None else ''
                if label in ('leerlingnummer', 'stamnummer'):
                    col_stamnr = j
                elif label == 'naam':
                    col_naam = j
                elif label == 'locatie':
                    col_locatie = j
                elif label == 'email':
                    col_email = j
            break

        if col_stamnr is None or col_naam is None:
            return jsonify({'error': 'Kolommen "Leerlingnummer" en "Naam" zijn verplicht'}), 400

        leerlingen = []
        for i, row in enumerate(ws.iter_rows(values_only=True), start=1):
            if i <= header_row_idx:
                continue
            stamnr = _cell_to_str(row[col_stamnr] if col_stamnr < len(row) else None)
            naam = _cell_to_str(row[col_naam] if col_naam < len(row) else None)
            if not stamnr or not naam:
                continue
            locatie = _cell_to_str(row[col_locatie] if col_locatie is not None and col_locatie < len(row) else None)
            email = _cell_to_str(row[col_email] if col_email is not None and col_email < len(row) else None)
            leerlingen.append({
                'stamnr': stamnr,
                'naam': naam,
                'locatie': locatie,
                'email': email,
            })
    finally:
        wb.close()

    summary = import_voorinschrijvingen(g.db, leerlingen, schooljaar)
    return jsonify({'geimporteerd': summary['imported'], 'schooljaar': schooljaar, 'bron': 'xlsx'})
