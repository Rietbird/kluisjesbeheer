import csv
import io
from flask import Blueprint, request, jsonify, g
from auth import login_required

kluisjes_bp = Blueprint('kluisjes', __name__, url_prefix='/api')

@kluisjes_bp.route('/clusters/<int:cid>/kluisjes', methods=['GET'])
@login_required
def list_kluisjes(cid):
    rows = g.db.execute(
        'SELECT * FROM kluisjes WHERE cluster_id = ? AND verwijderd = 0 ORDER BY kluisnummer',
        (cid,)
    ).fetchall()
    return jsonify([dict(r) for r in rows])

@kluisjes_bp.route('/kluisjes', methods=['GET'])
@login_required
def search_kluisjes():
    q = request.args.get('q', '').strip()
    vestiging_id = request.args.get('vestiging_id')
    status = request.args.get('status')

    query = '''
        SELECT k.*, c.naam as cluster_naam, c.standaard_borg,
               t.id as toewijzing_id,
               t.leerling_naam, t.leerling_stamnr, t.leerling_klas,
               t.periode_van, t.periode_tot, t.borgbedrag, t.borg_betaald,
               CASE
                 WHEN k.status = 'vrij' AND EXISTS (
                   SELECT 1 FROM toewijzingen t2
                   WHERE t2.kluisje_id = k.id AND t2.actief = 0 AND t2.sleutel_ingeleverd = 0
                   AND t2.id = (SELECT MAX(t3.id) FROM toewijzingen t3 WHERE t3.kluisje_id = k.id)
                 ) THEN 1 ELSE 0
               END as _sleutel_niet_ingeleverd,
               CASE
                 WHEN k.status = 'vrij' AND EXISTS (
                   SELECT 1 FROM toewijzingen t2
                   WHERE t2.kluisje_id = k.id AND t2.actief = 0
                   AND t2.borg_betaald = 1 AND t2.borg_teruggestort = 0
                   AND t2.id = (SELECT MAX(t3.id) FROM toewijzingen t3 WHERE t3.kluisje_id = k.id)
                 ) THEN 1 ELSE 0
               END as _borg_niet_teruggestort
        FROM kluisjes k
        JOIN clusters c ON k.cluster_id = c.id
        LEFT JOIN toewijzingen t ON k.id = t.kluisje_id AND t.actief = 1
        WHERE k.verwijderd = 0
    '''
    params = []

    if vestiging_id:
        query += ' AND k.vestiging_id = ?'
        params.append(int(vestiging_id))
    if status:
        query += ' AND k.status = ?'
        params.append(status)
    if q:
        # Escape LIKE wildcards in user input
        q_escaped = q.replace('%', '\\%').replace('_', '\\_')
        query += """ AND (k.kluisnummer LIKE ? ESCAPE '\\' OR k.sleutelnummer LIKE ? ESCAPE '\\'
                     OR t.leerling_naam LIKE ? ESCAPE '\\' OR t.leerling_stamnr LIKE ? ESCAPE '\\')"""
        like = f'%{q_escaped}%'
        params.extend([like, like, like, like])

    query += ' ORDER BY k.kluisnummer'
    rows = g.db.execute(query, params).fetchall()
    return jsonify([dict(r) for r in rows])

@kluisjes_bp.route('/kluisjes/<int:kid>', methods=['GET'])
@login_required
def get_kluisje(kid):
    row = g.db.execute('SELECT * FROM kluisjes WHERE id = ? AND verwijderd = 0', (kid,)).fetchone()
    if not row:
        return jsonify({'error': 'Niet gevonden'}), 404
    return jsonify(dict(row))

@kluisjes_bp.route('/clusters/<int:cid>/kluisjes', methods=['POST'])
@login_required
def create_kluisje(cid):
    data = request.get_json()
    kluisnummer = data.get('kluisnummer', '').strip()
    if not kluisnummer:
        return jsonify({'error': 'Kluisnummer is verplicht'}), 400

    cluster = g.db.execute('SELECT vestiging_id FROM clusters WHERE id = ?', (cid,)).fetchone()
    if not cluster:
        return jsonify({'error': 'Cluster niet gevonden'}), 404

    vestiging_id = cluster['vestiging_id']
    sleutelnummer = data.get('sleutelnummer', '')
    locatie = data.get('locatie', '')

    try:
        cur = g.db.execute(
            'INSERT INTO kluisjes (cluster_id, vestiging_id, kluisnummer, sleutelnummer, locatie, status) VALUES (?, ?, ?, ?, ?, ?)',
            (cid, vestiging_id, kluisnummer, sleutelnummer, locatie, 'vrij')
        )
        g.db.commit()
    except Exception as e:
        if 'UNIQUE' in str(e):
            return jsonify({'error': f'Kluisnummer {kluisnummer} bestaat al in deze vestiging'}), 409
        raise

    row = g.db.execute('SELECT * FROM kluisjes WHERE id = ?', (cur.lastrowid,)).fetchone()
    return jsonify(dict(row)), 201

@kluisjes_bp.route('/kluisjes/<int:kid>', methods=['PUT'])
@login_required
def update_kluisje(kid):
    data = request.get_json()
    row = g.db.execute('SELECT * FROM kluisjes WHERE id = ? AND verwijderd = 0', (kid,)).fetchone()
    if not row:
        return jsonify({'error': 'Niet gevonden'}), 404

    sleutelnummer = data.get('sleutelnummer', row['sleutelnummer'])
    locatie = data.get('locatie', row['locatie'])
    opmerkingen = data.get('opmerkingen', row['opmerkingen'])
    status = data.get('status', row['status'])
    if status not in ('vrij', 'uitgeleend', 'defect'):
        return jsonify({'error': 'Ongeldige status'}), 400

    g.db.execute(
        "UPDATE kluisjes SET sleutelnummer=?, locatie=?, opmerkingen=?, status=?, updated_at=datetime('now') WHERE id=?",
        (sleutelnummer, locatie, opmerkingen, status, kid)
    )
    g.db.commit()
    row = g.db.execute('SELECT * FROM kluisjes WHERE id = ?', (kid,)).fetchone()
    return jsonify(dict(row))

@kluisjes_bp.route('/kluisjes/<int:kid>', methods=['DELETE'])
@login_required
def delete_kluisje(kid):
    row = g.db.execute('SELECT id FROM kluisjes WHERE id = ? AND verwijderd = 0', (kid,)).fetchone()
    if not row:
        return jsonify({'error': 'Niet gevonden'}), 404
    active = g.db.execute(
        'SELECT COUNT(*) as cnt FROM toewijzingen WHERE kluisje_id = ? AND actief = 1', (kid,)
    ).fetchone()['cnt']
    if active > 0:
        return jsonify({'error': 'Kan niet verwijderen: er is een actieve toewijzing'}), 409
    g.db.execute("UPDATE kluisjes SET verwijderd = 1, updated_at = datetime('now') WHERE id = ?", (kid,))
    g.db.commit()
    return jsonify({'ok': True})

@kluisjes_bp.route('/clusters/<int:cid>/kluisjes/bulk', methods=['POST'])
@login_required
def bulk_create_kluisjes(cid):
    """Bulk aanmaken van kluisjes. Body: { kluisjes: [{kluisnummer, sleutelnummer, locatie}, ...] }"""
    cluster = g.db.execute('SELECT vestiging_id FROM clusters WHERE id = ?', (cid,)).fetchone()
    if not cluster:
        return jsonify({'error': 'Cluster niet gevonden'}), 404

    vestiging_id = cluster['vestiging_id']
    data = request.get_json() or {}
    items = data.get('kluisjes', [])
    if not items or len(items) > 500:
        return jsonify({'error': 'Geef 1–500 kluisjes op'}), 400

    created = []
    skipped = []
    for item in items:
        kluisnummer = str(item.get('kluisnummer', '')).strip()
        if not kluisnummer:
            continue
        sleutelnummer = str(item.get('sleutelnummer', '')).strip()
        locatie = str(item.get('locatie', '')).strip()
        try:
            cur = g.db.execute(
                'INSERT INTO kluisjes (cluster_id, vestiging_id, kluisnummer, sleutelnummer, locatie, status) VALUES (?, ?, ?, ?, ?, ?)',
                (cid, vestiging_id, kluisnummer, sleutelnummer, locatie, 'vrij')
            )
            created.append({'id': cur.lastrowid, 'kluisnummer': kluisnummer})
        except Exception as e:
            if 'UNIQUE' in str(e):
                skipped.append({'kluisnummer': kluisnummer, 'reden': 'Al bestaat'})
            else:
                g.db.rollback()
                raise

    g.db.commit()
    return jsonify({'created': len(created), 'skipped': skipped}), 201


@kluisjes_bp.route('/kluisjes/bulk-verwijderen', methods=['POST'])
@login_required
def bulk_delete_kluisjes():
    """Bulk verwijderen van kluisjes. Body: { kluisje_ids: [...] }"""
    data = request.get_json() or {}
    ids = data.get('kluisje_ids', [])
    if not ids or len(ids) > 500:
        return jsonify({'error': 'Geef 1–500 kluisje IDs op'}), 400

    deleted = 0
    skipped = []
    for kid in ids:
        row = g.db.execute('SELECT id FROM kluisjes WHERE id = ? AND verwijderd = 0', (kid,)).fetchone()
        if not row:
            skipped.append({'kluisje_id': kid, 'reden': 'Niet gevonden'})
            continue
        active = g.db.execute(
            'SELECT COUNT(*) as cnt FROM toewijzingen WHERE kluisje_id = ? AND actief = 1', (kid,)
        ).fetchone()['cnt']
        if active > 0:
            skipped.append({'kluisje_id': kid, 'reden': 'Actieve toewijzing'})
            continue
        g.db.execute("UPDATE kluisjes SET verwijderd = 1, updated_at = datetime('now') WHERE id = ?", (kid,))
        deleted += 1

    g.db.commit()
    return jsonify({'deleted': deleted, 'skipped': skipped})


def _parse_bedrag(text):
    """Parse '€ 10,00' or '10.00' to float."""
    if not text:
        return 0.0
    text = str(text).replace('\u20ac', '').replace('\ufffd', '').replace('€', '').strip()
    text = text.replace(',', '.').strip()
    try:
        return float(text)
    except (ValueError, TypeError):
        return 0.0


def _parse_periode_mx(text):
    """Parse MX format: 'van 1-8-2025 tot en met 31-7-2026' -> (iso_van, iso_tot)."""
    import re
    if not text:
        return None, None
    m = re.match(r'van\s+(\d{1,2}-\d{1,2}-\d{4})\s+tot en met\s+(\d{1,2}-\d{1,2}-\d{4}|-)', str(text).strip())
    if not m:
        return None, None
    def to_iso(d):
        if not d or d == '-':
            return None
        parts = d.split('-')
        return f"{parts[2]}-{parts[1].zfill(2)}-{parts[0].zfill(2)}" if len(parts) == 3 else d
    return to_iso(m.group(1)), to_iso(m.group(2))


def _parse_date_desktop(text):
    """Parse Desktop date format (d-m-yyyy or dd-mm-yyyy) to ISO."""
    if not text:
        return None
    text = str(text).strip()
    if not text or text == '-':
        return None
    parts = text.split('-')
    if len(parts) == 3:
        return f"{parts[2]}-{parts[1].zfill(2)}-{parts[0].zfill(2)}"
    return text


def _detect_format(headers):
    """Detect whether the XLSX is Magister MX or Desktop format."""
    h_set = set(headers)
    if 'kluis' in h_set or 'uitleenperiode' in h_set or 'borgbedrag' in h_set:
        return 'mx'
    if 'omschrijving kluisje' in h_set or 'verhuur vanaf' in h_set or 'stamnr' in h_set:
        return 'desktop'
    # Fallback: simple format (kluisnummer only)
    if 'kluisnummer' in h_set:
        return 'simple'
    return None


def _extract_prefix(kluisnummer):
    """Extract prefix from locker number (e.g. 'BL-001' -> 'BL', 'ISK1-0003' -> 'ISK1')."""
    import re
    m = re.match(r'^([A-Za-z]+\d*)', kluisnummer)
    return m.group(1) if m else 'Overig'


@kluisjes_bp.route('/kluisjes/import/preview', methods=['POST'])
@login_required
def import_preview():
    """Scan an XLSX file and return a summary of prefixes, clusters, and locaties found."""
    file = request.files.get('file')
    if not file:
        return jsonify({'error': 'Bestand is verplicht'}), 400

    filename = file.filename or ''
    if not filename.lower().endswith('.xlsx'):
        return jsonify({'error': 'Alleen .xlsx bestanden worden geaccepteerd'}), 400

    import openpyxl
    try:
        wb = openpyxl.load_workbook(file, read_only=True)
        ws = wb.active
        headers = None
        fmt = None
        prefixes = {}  # prefix -> count
        locaties = {}  # locatie -> count
        clusters = {}  # cluster -> count
        total = 0

        for i, row in enumerate(ws.iter_rows(values_only=True), start=1):
            if i == 1:
                headers = [str(c or '').strip().lower() for c in row]
                fmt = _detect_format(headers)
                if not fmt:
                    wb.close()
                    return jsonify({'error': f'Onbekend bestandsformaat'}), 400
                continue

            row_dict = dict(zip(headers, [str(c or '').strip() for c in row]))

            if fmt == 'mx':
                kluisnummer = row_dict.get('kluis', '')
                locatie = row_dict.get('locatie', '')
                cluster = row_dict.get('cluster', '')
            elif fmt == 'desktop':
                kluisnummer = row_dict.get('omschrijving kluisje', '') or row_dict.get('omschrijving\nkluisje', '')
                locatie = ''
                cluster = ''
            else:
                kluisnummer = row_dict.get('kluisnummer', '') or row_dict.get('kluis', '')
                locatie = ''
                cluster = ''

            if not kluisnummer:
                continue

            total += 1
            prefix = _extract_prefix(kluisnummer)
            prefixes[prefix] = prefixes.get(prefix, 0) + 1
            if locatie:
                locaties[locatie] = locaties.get(locatie, 0) + 1
            if cluster and cluster.lower() != 'zonder cluster':
                clusters[cluster] = clusters.get(cluster, 0) + 1

        wb.close()
    except Exception as e:
        return jsonify({'error': str(e)}), 400

    return jsonify({
        'format': fmt,
        'total': total,
        'prefixes': [{'prefix': k, 'count': v} for k, v in sorted(prefixes.items())],
        'locaties': [{'locatie': k, 'count': v} for k, v in sorted(locaties.items())],
        'clusters': [{'cluster': k, 'count': v} for k, v in sorted(clusters.items())],
        'has_locaties': len(locaties) > 0,
    })


def _get_or_create_vestiging(naam):
    """Find existing vestiging by name, or create it."""
    row = g.db.execute('SELECT id FROM vestigingen WHERE naam = ?', (naam,)).fetchone()
    if row:
        return row['id']
    cur = g.db.execute('INSERT INTO vestigingen (naam) VALUES (?)', (naam,))
    return cur.lastrowid


def _get_or_create_cluster(vestiging_id, cluster_naam):
    """Find existing cluster by name + vestiging, or create it."""
    row = g.db.execute(
        'SELECT id FROM clusters WHERE vestiging_id = ? AND naam = ?',
        (vestiging_id, cluster_naam)
    ).fetchone()
    if row:
        return row['id']
    cur = g.db.execute(
        'INSERT INTO clusters (vestiging_id, naam) VALUES (?, ?)',
        (vestiging_id, cluster_naam)
    )
    return cur.lastrowid


@kluisjes_bp.route('/kluisjes/import', methods=['POST'])
@login_required
def import_kluisjes():
    import json as json_mod
    cluster_id = request.form.get('cluster_id') or None
    vestiging_id = request.form.get('vestiging_id') or None
    auto_vestiging = request.form.get('auto_vestiging') == '1'
    # prefix_mapping: JSON string {"BL": "Blauwlaken", "MO": "Molenstraat"}
    prefix_mapping = {}
    pm_raw = request.form.get('prefix_mapping', '')
    if pm_raw:
        try:
            prefix_mapping = json_mod.loads(pm_raw)
        except Exception:
            pass

    if not auto_vestiging and not vestiging_id and not prefix_mapping:
        if not cluster_id:
            return jsonify({'error': 'Kies een vestiging of gebruik automatisch uit bestand'}), 400
        cluster = g.db.execute('SELECT vestiging_id FROM clusters WHERE id = ?', (int(cluster_id),)).fetchone()
        if not cluster:
            return jsonify({'error': 'Cluster niet gevonden'}), 404
        vestiging_id = cluster['vestiging_id']
    elif vestiging_id:
        vestiging_id = int(vestiging_id)

    file = request.files.get('file')
    if not file:
        return jsonify({'error': 'Bestand is verplicht'}), 400

    filename = file.filename or ''
    if not filename.lower().endswith('.xlsx'):
        return jsonify({'error': 'Alleen .xlsx bestanden worden geaccepteerd'}), 400

    import openpyxl
    from datetime import date

    try:
        wb = openpyxl.load_workbook(file, read_only=True)
        ws = wb.active
        headers = None
        fmt = None
        kluisjes_created = 0
        toewijzingen_created = 0
        skipped = 0

        for i, row in enumerate(ws.iter_rows(values_only=True), start=1):
            if i == 1:
                headers = [str(c or '').strip().lower() for c in row]
                fmt = _detect_format(headers)
                if not fmt:
                    wb.close()
                    return jsonify({'error': f'Onbekend bestandsformaat. Verwachte kolommen niet gevonden. Gevonden: {", ".join(headers[:5])}...'}), 400
                continue

            row_dict = dict(zip(headers, [str(c or '').strip() for c in row]))

            if fmt == 'mx':
                kluisnummer = row_dict.get('kluis', '')
                sleutelnummer = row_dict.get('sleutel', '')
                locatie = row_dict.get('locatie', '')
                status_text = row_dict.get('status', '')
                naam = row_dict.get('naam', '')
                stamnr = row_dict.get('stamnummer', '')
                klas = row_dict.get('klas', '')
                borg = _parse_bedrag(row_dict.get('borgbedrag', ''))
                datum_van, datum_tot = _parse_periode_mx(row_dict.get('uitleenperiode', ''))
                is_uitgeleend = status_text.lower() == 'uitgeleend'
                is_defect = status_text.lower() == 'defect'

            elif fmt == 'desktop':
                kluisnummer = row_dict.get('omschrijving kluisje', '') or row_dict.get('omschrijving\nkluisje', '')
                sleutelnummer = row_dict.get('slotnummer', '')
                locatie = ''
                stamnr = row_dict.get('stamnr', '')
                achternaam = row_dict.get('achternaam', '')
                tussenv = row_dict.get('tussenv', '')
                roepnaam = row_dict.get('roepnaam', '')
                naam = f"{roepnaam} {tussenv} {achternaam}".replace('  ', ' ').strip() if achternaam else ''
                klas = ''
                borg = 0.0
                datum_van = _parse_date_desktop(row_dict.get('verhuur vanaf', ''))
                datum_tot = _parse_date_desktop(row_dict.get('verhuur tot/met', ''))
                is_uitgeleend = bool(naam and stamnr)
                is_defect = False

            else:  # simple
                kluisnummer = row_dict.get('kluisnummer', '') or row_dict.get('kluis', '')
                sleutelnummer = row_dict.get('sleutelnummer', '') or row_dict.get('sleutel', '')
                locatie = row_dict.get('locatie', '')
                naam = ''
                stamnr = ''
                klas = ''
                borg = 0.0
                datum_van = None
                datum_tot = None
                is_uitgeleend = False
                is_defect = False

            if not kluisnummer:
                continue

            # Determine vestiging for this row
            if prefix_mapping:
                prefix = _extract_prefix(kluisnummer)
                vest_naam = prefix_mapping.get(prefix, prefix_mapping.get('_default', ''))
                if vest_naam:
                    row_vestiging_id = _get_or_create_vestiging(vest_naam)
                elif vestiging_id:
                    row_vestiging_id = int(vestiging_id)
                else:
                    row_vestiging_id = _get_or_create_vestiging(prefix)
            elif auto_vestiging:
                row_locatie = row_dict.get('locatie', '').strip() if fmt == 'mx' else ''
                if row_locatie:
                    row_vestiging_id = _get_or_create_vestiging(row_locatie)
                elif vestiging_id:
                    row_vestiging_id = int(vestiging_id)
                else:
                    row_vestiging_id = _get_or_create_vestiging('Onbekend')
            elif vestiging_id:
                row_vestiging_id = int(vestiging_id)
            else:
                row_vestiging_id = _get_or_create_vestiging('Onbekend')

            # Determine cluster for this row
            row_cluster_naam = row_dict.get('cluster', '').strip() if fmt == 'mx' else ''
            if row_cluster_naam and row_cluster_naam.lower() != 'zonder cluster':
                row_cluster_id = _get_or_create_cluster(row_vestiging_id, row_cluster_naam)
            elif cluster_id:
                row_cluster_id = int(cluster_id)
            else:
                row_cluster_id = _get_or_create_cluster(row_vestiging_id, 'Standaard')

            # Determine status
            db_status = 'defect' if is_defect else ('uitgeleend' if is_uitgeleend else 'vrij')

            # Check for duplicate kluisnummer in this vestiging
            existing = g.db.execute(
                'SELECT id FROM kluisjes WHERE kluisnummer = ? AND vestiging_id = ? AND verwijderd = 0',
                (kluisnummer, row_vestiging_id)
            ).fetchone()
            if existing:
                skipped += 1
                continue

            # Insert kluisje
            cur = g.db.execute(
                'INSERT INTO kluisjes (cluster_id, vestiging_id, kluisnummer, sleutelnummer, locatie, status) VALUES (?, ?, ?, ?, ?, ?)',
                (row_cluster_id, row_vestiging_id, kluisnummer, sleutelnummer, locatie, db_status)
            )
            kluisjes_created += 1

            # Create toewijzing if uitgeleend
            if is_uitgeleend and naam:
                kluisje_id = cur.lastrowid
                if not datum_van:
                    datum_van = date.today().isoformat()
                if not datum_tot:
                    datum_tot = datum_van
                g.db.execute('''
                    INSERT INTO toewijzingen
                    (kluisje_id, leerling_stamnr, leerling_naam, leerling_klas,
                     periode_van, periode_tot, borgbedrag, borg_betaald, actief, aangemaakt_door)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, ?)
                ''', (
                    kluisje_id, stamnr, naam, klas,
                    datum_van, datum_tot, borg,
                    1 if borg > 0 else 0,
                    'XLSX Import',
                ))
                toewijzingen_created += 1

        wb.close()
        g.db.commit()
    except Exception as e:
        g.db.rollback()
        if 'UNIQUE' in str(e):
            return jsonify({'error': 'Duplicaat kluisnummer gevonden — import afgebroken'}), 400
        raise

    return jsonify({
        'imported': kluisjes_created,
        'toewijzingen': toewijzingen_created,
        'skipped': skipped,
        'format': fmt,
    }), 201
