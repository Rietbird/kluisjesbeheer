from flask import Blueprint, request, jsonify, g, session
from auth import login_required, assert_vestiging_access, user_vestiging_ids
from klas import KLAS_SQL

toewijzingen_bp = Blueprint('toewijzingen', __name__, url_prefix='/api')


def _kluisje_access(kid):
    row = g.db.execute('SELECT vestiging_id FROM kluisjes WHERE id = ?', (int(kid),)).fetchone()
    if not row:
        return jsonify({'error': 'Kluisje niet gevonden'}), 404
    return assert_vestiging_access(row['vestiging_id'])


def _toewijzing_access(tid):
    row = g.db.execute(
        'SELECT k.vestiging_id FROM toewijzingen t JOIN kluisjes k ON t.kluisje_id = k.id WHERE t.id = ?',
        (int(tid),)
    ).fetchone()
    if not row:
        return jsonify({'error': 'Toewijzing niet gevonden'}), 404
    return assert_vestiging_access(row['vestiging_id'])

@toewijzingen_bp.route('/kluisjes/<int:kid>/toewijzen', methods=['POST'])
@login_required
def toewijzen(kid):
    err = _kluisje_access(kid)
    if err: return err
    kluisje = g.db.execute('SELECT * FROM kluisjes WHERE id = ? AND verwijderd = 0', (kid,)).fetchone()
    if not kluisje:
        return jsonify({'error': 'Kluisje niet gevonden'}), 404
    if kluisje['status'] == 'uitgeleend':
        return jsonify({'error': 'Kluisje is al uitgeleend'}), 409
    if kluisje['is_defect']:
        return jsonify({'error': 'Kluisje is defect — hef het defect eerst op'}), 409
    if kluisje['geen_sleutel']:
        return jsonify({'error': 'Kluisje heeft geen sleutel — markeer eerst weer als sleutel aanwezig'}), 409

    # Blokkeer toewijzing als er openstaande borg of sleutel is van de vorige verhuur
    laatste = g.db.execute(
        'SELECT * FROM toewijzingen WHERE kluisje_id = ? ORDER BY id DESC LIMIT 1', (kid,)
    ).fetchone()
    if laatste and not laatste['actief']:
        if not laatste['sleutel_ingeleverd']:
            return jsonify({'error': 'Kluisje heeft een openstaande sleutel — lever eerst de sleutel in'}), 409
        if laatste['borg_betaald'] and not laatste['borg_teruggestort']:
            return jsonify({'error': 'Kluisje heeft openstaande borg — stort eerst de borg terug'}), 409

    data = request.get_json() or {}
    for field in ('leerling_stamnr', 'leerling_naam', 'periode_van', 'periode_tot'):
        if not data.get(field):
            return jsonify({'error': f'{field} is verplicht'}), 400

    # Blokkeer als leerling al een actief kluisje heeft in dezelfde vestiging
    stamnr = str(data['leerling_stamnr']).strip()
    bestaand = g.db.execute('''
        SELECT k.kluisnummer FROM toewijzingen t
        JOIN kluisjes k ON t.kluisje_id = k.id
        WHERE t.leerling_stamnr = ? AND t.actief = 1 AND k.vestiging_id = ?
    ''', (stamnr, kluisje['vestiging_id'])).fetchone()
    if bestaand:
        return jsonify({'error': f'Leerling heeft al kluisje {bestaand["kluisnummer"]} in deze vestiging'}), 409
    user = session.get('user', {})
    cur = g.db.execute('''
        INSERT INTO toewijzingen
        (kluisje_id, leerling_stamnr, leerling_naam, leerling_klas,
         periode_van, periode_tot, borgbedrag, borg_betaald, borg_teruggestort, actief, aangemaakt_door)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?)
    ''', (
        kid, str(data['leerling_stamnr']).strip(), str(data['leerling_naam']).strip(),
        str(data.get('leerling_klas', '')).strip(),
        data['periode_van'], data['periode_tot'], data.get('borgbedrag', 0),
        1 if data.get('borg_betaald') else 0,
        1 if data.get('borg_teruggestort') else 0,
        user.get('displayName', ''),
    ))
    g.db.execute("UPDATE kluisjes SET status='uitgeleend', updated_at=datetime('now') WHERE id=?", (kid,))
    g.db.commit()
    row = g.db.execute('SELECT * FROM toewijzingen WHERE id = ?', (cur.lastrowid,)).fetchone()
    return jsonify(dict(row)), 201

@toewijzingen_bp.route('/toewijzingen/<int:tid>/beeindigen', methods=['POST'])
@login_required
def beeindigen(tid):
    err = _toewijzing_access(tid)
    if err: return err
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

@toewijzingen_bp.route('/toewijzingen/bulk-beeindigen', methods=['POST'])
@login_required
def bulk_beeindigen():
    """Bulk end assignments. Body: { toewijzing_ids: [...], sleutel_ingeleverd, borg_teruggestort, einddatum }"""
    data = request.get_json() or {}
    ids = data.get('toewijzing_ids', [])
    if not ids or len(ids) > 5000:
        return jsonify({'error': 'Maximaal 5000 toewijzingen per keer'}), 400
    # Vestiging-scope: filter IDs naar wat de user mag (beheerder mag alles)
    allowed = user_vestiging_ids()
    if allowed is not None:
        if not allowed:
            return jsonify({'error': 'Geen vestiging-toegang'}), 403
        placeholders = ','.join('?' * len(ids))
        v_placeholders = ','.join('?' * len(allowed))
        rows = g.db.execute(
            f'SELECT t.id FROM toewijzingen t JOIN kluisjes k ON t.kluisje_id = k.id '
            f'WHERE t.id IN ({placeholders}) AND k.vestiging_id IN ({v_placeholders})',
            list(ids) + list(allowed)
        ).fetchall()
        scoped_ids = {r['id'] for r in rows}
        if len(scoped_ids) < len(ids):
            return jsonify({'error': 'Een of meer toewijzingen vallen buiten je vestiging-toegang'}), 403
    borg_terug = 1 if data.get('borg_teruggestort') else 0
    einddatum = data.get('einddatum', '')
    opmerking = data.get('opmerking', '')
    # Per-toewijzing sleutel_ingeleverd override: { toewijzing_id: bool }
    sleutel_map = {int(k): v for k, v in data.get('sleutel_map', {}).items()}
    globaal_sleutel = 1 if data.get('sleutel_ingeleverd') else 0

    count = 0
    for tid in ids:
        toewijzing = g.db.execute('SELECT * FROM toewijzingen WHERE id = ? AND actief = 1', (tid,)).fetchone()
        if not toewijzing:
            continue
        sleutel = 1 if sleutel_map.get(tid, globaal_sleutel) else 0
        g.db.execute('''
            UPDATE toewijzingen SET actief=0, sleutel_ingeleverd=?, borg_teruggestort=?,
            einddatum=?, opmerking=?, updated_at=datetime('now') WHERE id=?
        ''', (sleutel, borg_terug, einddatum, opmerking, tid))
        g.db.execute("UPDATE kluisjes SET status='vrij', updated_at=datetime('now') WHERE id=?",
                     (toewijzing['kluisje_id'],))
        count += 1

    g.db.commit()
    return jsonify({'ended': count, 'total': len(ids)})

@toewijzingen_bp.route('/toewijzingen/<int:tid>/sleutel-ingeleverd', methods=['POST'])
@login_required
def sleutel_ingeleverd(tid):
    """Mark key as returned on a finished assignment.
    Audit-integriteit: alleen op afgesloten toewijzingen (actief=0).
    Een actieve toewijzing zonder einddatum mag geen sleutel-ingeleverd-
    vlag krijgen — dat zou de audit-trail verwarren."""
    err = _toewijzing_access(tid)
    if err: return err
    row = g.db.execute('SELECT actief FROM toewijzingen WHERE id = ?', (tid,)).fetchone()
    if not row:
        return jsonify({'error': 'Toewijzing niet gevonden'}), 404
    if row['actief']:
        return jsonify({'error': 'Toewijzing is nog actief — beëindig eerst de toewijzing'}), 409
    g.db.execute(
        "UPDATE toewijzingen SET sleutel_ingeleverd=1, updated_at=datetime('now') WHERE id=? AND actief=0",
        (tid,)
    )
    g.db.commit()
    return jsonify({'ok': True})

@toewijzingen_bp.route('/toewijzingen/<int:tid>', methods=['PATCH'])
@login_required
def patch_toewijzing(tid):
    err = _toewijzing_access(tid)
    if err: return err
    """Update specific fields on an active assignment (currently: reservesleutel)."""
    row = g.db.execute('SELECT * FROM toewijzingen WHERE id = ? AND actief = 1', (tid,)).fetchone()
    if not row:
        return jsonify({'error': 'Toewijzing niet gevonden of niet actief'}), 404
    data = request.get_json() or {}

    fields = []
    params = []
    if 'reservesleutel_uitgegeven' in data:
        uitgegeven = 1 if data.get('reservesleutel_uitgegeven') else 0
        fields.append('reservesleutel_uitgegeven=?')
        params.append(uitgegeven)
        # Datum auto-zetten als uitgegeven en nog geen datum, leegmaken bij intrekken
        if uitgegeven and not row['reservesleutel_datum'] and 'reservesleutel_datum' not in data:
            fields.append("reservesleutel_datum=date('now')")
        elif not uitgegeven:
            fields.append('reservesleutel_datum=NULL')
    if 'reservesleutel_datum' in data:
        datum = data.get('reservesleutel_datum') or None
        fields.append('reservesleutel_datum=?')
        params.append(datum)

    if not fields:
        return jsonify({'error': 'Geen velden om bij te werken'}), 400

    fields.append("updated_at=datetime('now')")
    params.append(tid)
    g.db.execute(f"UPDATE toewijzingen SET {', '.join(fields)} WHERE id=?", params)
    g.db.commit()
    row = g.db.execute('SELECT * FROM toewijzingen WHERE id = ?', (tid,)).fetchone()
    return jsonify(dict(row))


@toewijzingen_bp.route('/toewijzingen/ruilen', methods=['POST'])
@login_required
def ruilen():
    """Wissel het kluisje van twee actieve toewijzingen binnen dezelfde vestiging.

    Body: { toewijzing_a_id, toewijzing_b_id }
    Beide huren lopen ongewijzigd door; alleen kluisje_id wordt gewisseld.
    """
    data = request.get_json() or {}
    a_id = data.get('toewijzing_a_id')
    b_id = data.get('toewijzing_b_id')
    if not a_id or not b_id:
        return jsonify({'error': 'toewijzing_a_id en toewijzing_b_id zijn verplicht'}), 400
    if a_id == b_id:
        return jsonify({'error': 'Kan een kluisje niet met zichzelf ruilen'}), 400

    a = g.db.execute('SELECT * FROM toewijzingen WHERE id = ? AND actief = 1', (a_id,)).fetchone()
    b = g.db.execute('SELECT * FROM toewijzingen WHERE id = ? AND actief = 1', (b_id,)).fetchone()
    if not a or not b:
        return jsonify({'error': 'Een van beide toewijzingen is niet (meer) actief'}), 409

    kluisje_a = g.db.execute('SELECT vestiging_id FROM kluisjes WHERE id = ?', (a['kluisje_id'],)).fetchone()
    kluisje_b = g.db.execute('SELECT vestiging_id FROM kluisjes WHERE id = ?', (b['kluisje_id'],)).fetchone()
    if not kluisje_a or not kluisje_b:
        return jsonify({'error': 'Kluisje niet gevonden'}), 404
    if kluisje_a['vestiging_id'] != kluisje_b['vestiging_id']:
        return jsonify({'error': 'Ruilen kan alleen binnen dezelfde vestiging'}), 409

    # Vestiging-scope: user moet toegang hebben tot deze vestiging (A==B gecheckt)
    err = assert_vestiging_access(kluisje_a['vestiging_id'])
    if err: return err

    kid_a = a['kluisje_id']
    kid_b = b['kluisje_id']
    # 3-staps swap: A tijdelijk inactief zodat de partiele unique index
    # idx_active_toewijzing_per_kluisje (WHERE actief=1) nooit twee actieve
    # rijen op hetzelfde kluisje ziet.
    g.db.execute("UPDATE toewijzingen SET actief = 0 WHERE id = ?", (a_id,))
    g.db.execute("UPDATE toewijzingen SET kluisje_id = ?, updated_at = datetime('now') WHERE id = ?", (kid_a, b_id))
    g.db.execute("UPDATE toewijzingen SET kluisje_id = ?, actief = 1, updated_at = datetime('now') WHERE id = ?", (kid_b, a_id))
    g.db.commit()

    a_new = g.db.execute('SELECT * FROM toewijzingen WHERE id = ?', (a_id,)).fetchone()
    b_new = g.db.execute('SELECT * FROM toewijzingen WHERE id = ?', (b_id,)).fetchone()
    return jsonify({'a': dict(a_new), 'b': dict(b_new)}), 200


@toewijzingen_bp.route('/toewijzingen/<int:tid>/borg-teruggestort', methods=['POST'])
@login_required
def borg_teruggestort(tid):
    """Mark deposit as refunded on a finished assignment.
    Audit-integriteit: alleen op afgesloten toewijzingen (actief=0)."""
    err = _toewijzing_access(tid)
    if err: return err
    row = g.db.execute('SELECT actief FROM toewijzingen WHERE id = ?', (tid,)).fetchone()
    if not row:
        return jsonify({'error': 'Toewijzing niet gevonden'}), 404
    if row['actief']:
        return jsonify({'error': 'Toewijzing is nog actief — beëindig eerst de toewijzing'}), 409
    g.db.execute(
        "UPDATE toewijzingen SET borg_teruggestort=1, updated_at=datetime('now') WHERE id=? AND actief=0",
        (tid,)
    )
    g.db.commit()
    return jsonify({'ok': True})


@toewijzingen_bp.route('/toewijzingen/actief', methods=['GET'])
@login_required
def actieve_toewijzingen():
    """Get all active assignments, optionally filtered by vestiging_id and/or cluster_id."""
    vestiging_id = request.args.get('vestiging_id')
    cluster_id = request.args.get('cluster_id')
    stamnr = request.args.get('stamnr', '').strip()
    query = f'''
        SELECT t.*, k.kluisnummer, k.sleutelnummer, k.cluster_id, k.vestiging_id, c.naam as cluster_naam,
               l.vertrokken_op AS leerling_vertrokken_op,
               l.nieuw_voor_schooljaar AS leerling_nieuw_voor_schooljaar,
               {KLAS_SQL} AS leerling_klas_effectief
        FROM toewijzingen t
        JOIN kluisjes k ON t.kluisje_id = k.id
        JOIN clusters c ON k.cluster_id = c.id
        LEFT JOIN leerlingen l ON t.leerling_stamnr = l.stamnr
        WHERE t.actief = 1 AND k.verwijderd = 0
    '''
    params = []
    if stamnr:
        query += ' AND t.leerling_stamnr = ?'
        params.append(stamnr)
    if vestiging_id:
        query += ' AND k.vestiging_id = ?'
        params.append(int(vestiging_id))
    if cluster_id:
        query += ' AND k.cluster_id = ?'
        params.append(int(cluster_id))
    # Vestiging-scope: conciërge ziet alleen eigen vestiging(en); beheerder = alles
    allowed = user_vestiging_ids()
    if allowed is not None:
        if not allowed:
            return jsonify([])
        if vestiging_id and int(vestiging_id) not in allowed:
            return jsonify({'error': 'Geen toegang tot deze vestiging'}), 403
        ph = ','.join('?' * len(allowed))
        query += f' AND k.vestiging_id IN ({ph})'
        params += list(allowed)
    query += ' ORDER BY k.kluisnummer'
    rows = g.db.execute(query, params).fetchall()
    return jsonify([dict(r) for r in rows])

@toewijzingen_bp.route('/kluisjes/<int:kid>/geschiedenis', methods=['GET'])
@login_required
def geschiedenis(kid):
    err = _kluisje_access(kid)
    if err: return err
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

    # Vestiging-scope: alle kluisjes moeten binnen de toegang van de user vallen
    allowed = user_vestiging_ids()
    if allowed is not None:
        if not allowed:
            return jsonify({'error': 'Geen vestiging-toegang'}), 403
        kids = [it['kluisje_id'] for it in toewijzingen]
        if kids:
            ph = ','.join('?' * len(kids))
            vph = ','.join('?' * len(allowed))
            rows = g.db.execute(
                f'SELECT id FROM kluisjes WHERE id IN ({ph}) AND vestiging_id IN ({vph})',
                list(kids) + list(allowed)
            ).fetchall()
            if {r['id'] for r in rows} != set(kids):
                return jsonify({'error': 'Een of meer kluisjes vallen buiten je vestiging-toegang'}), 403

    count = 0
    skipped = []
    assigned_stamnrs = {}  # stamnr -> kluisnummer, bijhouden binnen deze batch
    for item in toewijzingen:
        kid = item['kluisje_id']
        stamnr = str(item.get('leerling_stamnr', '')).strip()
        # Check of leerling al in deze batch is toegewezen
        if stamnr and stamnr in assigned_stamnrs:
            skipped.append({'kluisje_id': kid, 'leerling_stamnr': stamnr, 'reden': f'Leerling heeft al kluisje {assigned_stamnrs[stamnr]} (in deze batch)'})
            continue
        # Check of leerling al een actief kluisje heeft in dezelfde vestiging
        if stamnr:
            actief_leerling = g.db.execute('''
                SELECT k.kluisnummer FROM toewijzingen t
                JOIN kluisjes k ON t.kluisje_id = k.id
                WHERE t.leerling_stamnr = ? AND t.actief = 1 AND k.vestiging_id = (
                    SELECT vestiging_id FROM kluisjes WHERE id = ?
                )
            ''', (stamnr, kid)).fetchone()
            if actief_leerling:
                skipped.append({'kluisje_id': kid, 'leerling_stamnr': stamnr, 'reden': f'Leerling heeft al kluisje {actief_leerling["kluisnummer"]} in deze vestiging'})
                continue
        kluisje = g.db.execute('SELECT * FROM kluisjes WHERE id = ? AND verwijderd = 0 AND status != ?',
                               (kid, 'uitgeleend')).fetchone()
        if not kluisje:
            skipped.append({'kluisje_id': kid, 'reden': 'Niet beschikbaar of al uitgeleend'})
            continue
        if kluisje['is_defect']:
            skipped.append({'kluisje_id': kid, 'reden': 'Kluisje is defect'})
            continue
        laatste = g.db.execute(
            'SELECT * FROM toewijzingen WHERE kluisje_id = ? ORDER BY id DESC LIMIT 1', (kid,)
        ).fetchone()
        if laatste and not laatste['actief']:
            if not laatste['sleutel_ingeleverd']:
                skipped.append({'kluisje_id': kid, 'reden': 'Openstaande sleutel'})
                continue
            if laatste['borg_betaald'] and not laatste['borg_teruggestort']:
                skipped.append({'kluisje_id': kid, 'reden': 'Openstaande borg'})
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
        if stamnr:
            assigned_stamnrs[stamnr] = item['leerling_stamnr']
        count += 1

    g.db.commit()
    return jsonify({'assigned': count, 'skipped': skipped}), 201
