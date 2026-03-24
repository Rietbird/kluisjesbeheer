from flask import Blueprint, request, jsonify, g, session
from auth import login_required

toewijzingen_bp = Blueprint('toewijzingen', __name__, url_prefix='/api')

@toewijzingen_bp.route('/kluisjes/<int:kid>/toewijzen', methods=['POST'])
@login_required
def toewijzen(kid):
    kluisje = g.db.execute('SELECT * FROM kluisjes WHERE id = ? AND verwijderd = 0', (kid,)).fetchone()
    if not kluisje:
        return jsonify({'error': 'Kluisje niet gevonden'}), 404
    if kluisje['status'] == 'uitgeleend':
        return jsonify({'error': 'Kluisje is al uitgeleend'}), 409

    data = request.get_json()
    user = session.get('user', {})
    cur = g.db.execute('''
        INSERT INTO toewijzingen
        (kluisje_id, leerling_stamnr, leerling_naam, leerling_klas,
         periode_van, periode_tot, borgbedrag, borg_betaald, actief, aangemaakt_door)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, ?)
    ''', (
        kid, data['leerling_stamnr'], data['leerling_naam'], data.get('leerling_klas', ''),
        data['periode_van'], data['periode_tot'], data.get('borgbedrag', 0),
        1 if data.get('borg_betaald') else 0,
        user.get('displayName', ''),
    ))
    g.db.execute("UPDATE kluisjes SET status='uitgeleend', updated_at=datetime('now') WHERE id=?", (kid,))
    g.db.commit()
    row = g.db.execute('SELECT * FROM toewijzingen WHERE id = ?', (cur.lastrowid,)).fetchone()
    return jsonify(dict(row)), 201

@toewijzingen_bp.route('/toewijzingen/<int:tid>/beeindigen', methods=['POST'])
@login_required
def beeindigen(tid):
    toewijzing = g.db.execute('SELECT * FROM toewijzingen WHERE id = ? AND actief = 1', (tid,)).fetchone()
    if not toewijzing:
        return jsonify({'error': 'Toewijzing niet gevonden of al beëindigd'}), 404

    data = request.get_json()
    sleutel = 1 if data.get('sleutel_ingeleverd') else 0
    borg_terug = 1 if data.get('borg_teruggestort') else 0
    einddatum = data.get('einddatum', '')
    opmerking = data.get('opmerking', '')

    g.db.execute('''
        UPDATE toewijzingen SET actief=0, sleutel_ingeleverd=?, borg_teruggestort=?,
        einddatum=?, opmerking=?, updated_at=datetime('now') WHERE id=?
    ''', (sleutel, borg_terug, einddatum, opmerking, tid))

    g.db.execute("UPDATE kluisjes SET status='vrij', updated_at=datetime('now') WHERE id=?",
                 (toewijzing['kluisje_id'],))
    g.db.commit()
    row = g.db.execute('SELECT * FROM toewijzingen WHERE id = ?', (tid,)).fetchone()
    return jsonify(dict(row))

@toewijzingen_bp.route('/kluisjes/<int:kid>/geschiedenis', methods=['GET'])
@login_required
def geschiedenis(kid):
    rows = g.db.execute(
        'SELECT * FROM toewijzingen WHERE kluisje_id = ? ORDER BY created_at DESC',
        (kid,)
    ).fetchall()
    return jsonify([dict(r) for r in rows])

@toewijzingen_bp.route('/toewijzingen/bulk', methods=['POST'])
@login_required
def bulk_toewijzen():
    data = request.get_json()
    toewijzingen = data.get('toewijzingen', [])
    periode_van = data['periode_van']
    periode_tot = data['periode_tot']
    borgbedrag = data.get('borgbedrag', 0)
    user = session.get('user', {})

    count = 0
    skipped = []
    for item in toewijzingen:
        kid = item['kluisje_id']
        kluisje = g.db.execute('SELECT * FROM kluisjes WHERE id = ? AND verwijderd = 0 AND status != ?',
                               (kid, 'uitgeleend')).fetchone()
        if not kluisje:
            skipped.append({'kluisje_id': kid, 'reden': 'Niet beschikbaar of al uitgeleend'})
            continue
        g.db.execute('''
            INSERT INTO toewijzingen
            (kluisje_id, leerling_stamnr, leerling_naam, leerling_klas,
             periode_van, periode_tot, borgbedrag, actief, aangemaakt_door)
            VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?)
        ''', (
            kid, item['leerling_stamnr'], item['leerling_naam'], item.get('leerling_klas', ''),
            periode_van, periode_tot, borgbedrag, user.get('displayName', ''),
        ))
        g.db.execute("UPDATE kluisjes SET status='uitgeleend', updated_at=datetime('now') WHERE id=?", (kid,))
        count += 1

    g.db.commit()
    return jsonify({'assigned': count, 'skipped': skipped}), 201
