from flask import Blueprint, request, jsonify, g
from auth import login_required
from magister_client import magister

magister_bp = Blueprint('magister', __name__, url_prefix='/api')


def _sync_to_db(leerlingen):
    """Upsert leerlingen list into the database."""
    for l in leerlingen:
        g.db.execute('''
            INSERT INTO leerlingen (stamnr, naam, roepnaam, tussenvoegsel, achternaam, email, klas, leerjaar, studie, locatie, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
            ON CONFLICT(stamnr) DO UPDATE SET
                naam=excluded.naam, roepnaam=excluded.roepnaam, tussenvoegsel=excluded.tussenvoegsel,
                achternaam=excluded.achternaam, email=excluded.email, klas=excluded.klas,
                leerjaar=excluded.leerjaar, studie=excluded.studie, locatie=excluded.locatie,
                updated_at=datetime('now')
        ''', (
            l['stamnr'], l['naam'], l.get('roepnaam', ''), l.get('tussenvoegsel', ''),
            l.get('achternaam', ''), l.get('email', ''), l['klas'],
            l.get('leerjaar', ''), l.get('studie', ''), l.get('locatie', ''),
        ))
    g.db.commit()


@magister_bp.route('/magister/locaties', methods=['GET'])
@login_required
def get_locaties():
    """Get unique Magister locatie values from leerlingen table."""
    rows = g.db.execute(
        "SELECT DISTINCT locatie FROM leerlingen WHERE locatie != '' ORDER BY locatie"
    ).fetchall()
    return jsonify([r['locatie'] for r in rows])


def _get_vestiging_locaties(vestiging_id):
    """Get Magister locaties linked to a vestiging, or None if not configured."""
    rows = g.db.execute(
        'SELECT locatie FROM vestigingen_locaties WHERE vestiging_id = ?', (int(vestiging_id),)
    ).fetchall()
    return [r['locatie'] for r in rows] if rows else None


@magister_bp.route('/magister/leerlingen', methods=['GET'])
@login_required
def search_leerlingen():
    """Search students from database. ?klas= for exact match, ?q= for substring search, ?vestiging_id= to filter."""
    vestiging_id = request.args.get('vestiging_id', '').strip()
    vestiging_locaties = _get_vestiging_locaties(vestiging_id) if vestiging_id else None

    klas = request.args.get('klas', '').strip()
    if klas:
        if vestiging_locaties is not None:
            placeholders = ','.join('?' * len(vestiging_locaties))
            rows = g.db.execute(f'''
                SELECT * FROM leerlingen WHERE klas = ? AND locatie IN ({placeholders}) ORDER BY naam
            ''', (klas, *vestiging_locaties)).fetchall()
        else:
            rows = g.db.execute(
                'SELECT * FROM leerlingen WHERE klas = ? ORDER BY naam', (klas,)
            ).fetchall()
        return jsonify([dict(r) for r in rows])

    q = request.args.get('q', '').strip()
    if len(q) < 2:
        return jsonify([])

    like = f'%{q}%'
    if vestiging_locaties is not None:
        placeholders = ','.join('?' * len(vestiging_locaties))
        rows = g.db.execute(f'''
            SELECT * FROM leerlingen
            WHERE (naam LIKE ? OR stamnr LIKE ? OR email LIKE ?)
              AND locatie IN ({placeholders})
            ORDER BY naam LIMIT 50
        ''', (like, like, like, *vestiging_locaties)).fetchall()
    else:
        rows = g.db.execute('''
            SELECT * FROM leerlingen
            WHERE naam LIKE ? OR klas LIKE ? OR stamnr LIKE ? OR email LIKE ?
            ORDER BY naam LIMIT 50
        ''', (like, like, like, like)).fetchall()
    return jsonify([dict(r) for r in rows])


@magister_bp.route('/magister/klassen', methods=['GET'])
@login_required
def get_klassen():
    """Get unique class list from database. ?vestiging_id= to filter by vestiging locaties."""
    vestiging_id = request.args.get('vestiging_id', '').strip()
    if vestiging_id:
        vestiging_locaties = _get_vestiging_locaties(vestiging_id)
        if vestiging_locaties:
            placeholders = ','.join('?' * len(vestiging_locaties))
            rows = g.db.execute(f'''
                SELECT DISTINCT klas FROM leerlingen
                WHERE klas != '' AND locatie IN ({placeholders})
                ORDER BY klas
            ''', vestiging_locaties).fetchall()
            return jsonify([{'naam': r['klas']} for r in rows])
    rows = g.db.execute(
        "SELECT DISTINCT klas FROM leerlingen WHERE klas != '' ORDER BY klas"
    ).fetchall()
    return jsonify([{'naam': r['klas']} for r in rows])


@magister_bp.route('/vestigingen/<int:vid>/klassen', methods=['GET'])
@login_required
def get_vestiging_klassen(vid):
    rows = g.db.execute(
        'SELECT klas FROM vestigingen_klassen WHERE vestiging_id = ? ORDER BY klas', (vid,)
    ).fetchall()
    return jsonify([r['klas'] for r in rows])


@magister_bp.route('/vestigingen/<int:vid>/klassen', methods=['PUT'])
@login_required
def set_vestiging_klassen(vid):
    """Stel in welke klassen bij een vestiging horen. Body: { klassen: ['1A', '1B', ...] }"""
    data = request.get_json() or {}
    klassen = data.get('klassen', [])
    if isinstance(klassen, str):
        klassen = [k.strip() for k in klassen.split(',') if k.strip()]
    if not g.db.execute('SELECT id FROM vestigingen WHERE id = ?', (vid,)).fetchone():
        return jsonify({'error': 'Vestiging niet gevonden'}), 404
    g.db.execute('DELETE FROM vestigingen_klassen WHERE vestiging_id = ?', (vid,))
    for klas in klassen:
        g.db.execute(
            'INSERT OR IGNORE INTO vestigingen_klassen (vestiging_id, klas) VALUES (?, ?)',
            (vid, klas)
        )
    g.db.commit()
    return jsonify({'vestiging_id': vid, 'klassen': klassen})


@magister_bp.route('/magister/flush-cache', methods=['POST'])
@login_required
def flush_cache():
    """Clear Magister API cache, forcing fresh data on next request."""
    magister.flush_cache()
    return jsonify({'ok': True})


@magister_bp.route('/magister/sync-leerlingen', methods=['POST'])
@login_required
def sync_leerlingen():
    """Fetch students from Magister SOAP API and store in database."""
    try:
        magister.flush_cache()
        leerlingen = magister.get_leerlingen()
        klassen = sorted(set(l['klas'] for l in leerlingen if l['klas']))
    except ConnectionError as e:
        return jsonify({'error': f'Magister niet bereikbaar: {e}'}), 502

    _sync_to_db(leerlingen)

    return jsonify({
        'leerlingen': len(leerlingen),
        'klassen': len(klassen),
    })
