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


@magister_bp.route('/magister/leerlingen', methods=['GET'])
@login_required
def search_leerlingen():
    """Search students from database. ?klas= for exact match, ?q= for substring search."""
    klas = request.args.get('klas', '').strip()
    if klas:
        rows = g.db.execute(
            'SELECT * FROM leerlingen WHERE klas = ? ORDER BY naam', (klas,)
        ).fetchall()
        return jsonify([dict(r) for r in rows])

    q = request.args.get('q', '').strip()
    if len(q) < 2:
        return jsonify([])

    like = f'%{q}%'
    rows = g.db.execute('''
        SELECT * FROM leerlingen
        WHERE naam LIKE ? OR klas LIKE ? OR stamnr LIKE ? OR email LIKE ?
        ORDER BY naam LIMIT 50
    ''', (like, like, like, like)).fetchall()
    return jsonify([dict(r) for r in rows])


@magister_bp.route('/magister/klassen', methods=['GET'])
@login_required
def get_klassen():
    """Get unique class list from database."""
    rows = g.db.execute(
        "SELECT DISTINCT klas FROM leerlingen WHERE klas != '' ORDER BY klas"
    ).fetchall()
    return jsonify([{'naam': r['klas']} for r in rows])


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
