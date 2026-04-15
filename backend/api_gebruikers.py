from flask import Blueprint, request, jsonify, g, session
from auth import login_required

gebruikers_bp = Blueprint('gebruikers', __name__, url_prefix='/api')


def _beheerder_required():
    """Return error response if current user is not a beheerder, else None."""
    user = session.get('user', {})
    if not user.get('is_beheerder'):
        return jsonify({'error': 'Alleen beheerders mogen gebruikers beheren'}), 403
    return None


@gebruikers_bp.route('/gebruikers', methods=['GET'])
@login_required
def list_gebruikers():
    err = _beheerder_required()
    if err:
        return err
    rows = g.db.execute('''
        SELECT g.id, g.email, g.naam, g.rol, g.actief,
               GROUP_CONCAT(gv.vestiging_id) as vestiging_ids
        FROM gebruikers g
        LEFT JOIN gebruiker_vestigingen gv ON gv.gebruiker_id = g.id
        GROUP BY g.id
        ORDER BY g.naam, g.email
    ''').fetchall()
    result = []
    for r in rows:
        d = dict(r)
        d['vestiging_ids'] = [int(x) for x in d['vestiging_ids'].split(',') if x] if d['vestiging_ids'] else []
        result.append(d)
    return jsonify(result)


@gebruikers_bp.route('/gebruikers', methods=['POST'])
@login_required
def create_gebruiker():
    err = _beheerder_required()
    if err:
        return err
    data = request.get_json() or {}
    email = (data.get('email') or '').strip().lower()
    naam = (data.get('naam') or '').strip()
    rol = data.get('rol', 'concierge')
    vestiging_ids = data.get('vestiging_ids', [])

    if not email:
        return jsonify({'error': 'E-mailadres is verplicht'}), 400
    if rol not in ('beheerder', 'concierge'):
        return jsonify({'error': 'Rol moet "beheerder" of "concierge" zijn'}), 400

    existing = g.db.execute('SELECT id FROM gebruikers WHERE LOWER(email) = ?', (email,)).fetchone()
    if existing:
        return jsonify({'error': 'Dit e-mailadres is al geregistreerd'}), 409

    cur = g.db.execute(
        'INSERT INTO gebruikers (email, naam, rol) VALUES (?, ?, ?)',
        (email, naam, rol)
    )
    geb_id = cur.lastrowid

    for vid in vestiging_ids:
        g.db.execute(
            'INSERT OR IGNORE INTO gebruiker_vestigingen (gebruiker_id, vestiging_id) VALUES (?, ?)',
            (geb_id, int(vid))
        )
    g.db.commit()

    return jsonify({'id': geb_id, 'email': email, 'naam': naam, 'rol': rol, 'vestiging_ids': vestiging_ids}), 201


@gebruikers_bp.route('/gebruikers/<int:gid>', methods=['PUT'])
@login_required
def update_gebruiker(gid):
    err = _beheerder_required()
    if err:
        return err
    data = request.get_json() or {}
    row = g.db.execute('SELECT * FROM gebruikers WHERE id = ?', (gid,)).fetchone()
    if not row:
        return jsonify({'error': 'Gebruiker niet gevonden'}), 404

    naam = (data.get('naam') or '').strip()
    rol = data.get('rol', row['rol'])
    actief = data.get('actief', row['actief'])
    vestiging_ids = data.get('vestiging_ids')

    if rol not in ('beheerder', 'concierge'):
        return jsonify({'error': 'Rol moet "beheerder" of "concierge" zijn'}), 400

    g.db.execute(
        "UPDATE gebruikers SET naam=?, rol=?, actief=?, updated_at=datetime('now') WHERE id=?",
        (naam, rol, 1 if actief else 0, gid)
    )

    if vestiging_ids is not None:
        g.db.execute('DELETE FROM gebruiker_vestigingen WHERE gebruiker_id = ?', (gid,))
        for vid in vestiging_ids:
            g.db.execute(
                'INSERT OR IGNORE INTO gebruiker_vestigingen (gebruiker_id, vestiging_id) VALUES (?, ?)',
                (gid, int(vid))
            )
    g.db.commit()

    return jsonify({'ok': True})


@gebruikers_bp.route('/gebruikers/<int:gid>', methods=['DELETE'])
@login_required
def delete_gebruiker(gid):
    err = _beheerder_required()
    if err:
        return err
    # Prevent deleting yourself
    user = session.get('user', {})
    row = g.db.execute('SELECT email FROM gebruikers WHERE id = ?', (gid,)).fetchone()
    if not row:
        return jsonify({'error': 'Gebruiker niet gevonden'}), 404
    if row['email'] == user.get('email', '').lower():
        return jsonify({'error': 'Je kunt jezelf niet verwijderen'}), 400

    g.db.execute('DELETE FROM gebruiker_vestigingen WHERE gebruiker_id = ?', (gid,))
    g.db.execute('DELETE FROM gebruikers WHERE id = ?', (gid,))
    g.db.commit()
    return jsonify({'ok': True})
