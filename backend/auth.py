import msal
from functools import wraps
from flask import Blueprint, redirect, request, session, jsonify, url_for, g
from config import config

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

_msal_app = None

def _get_msal_app():
    global _msal_app
    if _msal_app is None:
        _msal_app = msal.ConfidentialClientApplication(
            config.get('ClientId', ''),
            authority=f"https://login.microsoftonline.com/{config.get('TenantId', '')}",
            client_credential=config.get('ClientSecret', ''),
        )
    return _msal_app

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user' not in session:
            return jsonify({'error': 'Niet ingelogd'}), 401
        return f(*args, **kwargs)
    return decorated

@auth_bp.route('/login')
def login():
    msal_app = _get_msal_app()
    flow = msal_app.initiate_auth_code_flow(
        scopes=['User.Read'],
        redirect_uri=config.get('RedirectUri', ''),
    )
    session['auth_flow'] = flow
    return redirect(flow['auth_uri'])

@auth_bp.route('/callback')
def callback():
    msal_app = _get_msal_app()
    flow = session.pop('auth_flow', {})
    result = msal_app.acquire_token_by_auth_code_flow(flow, dict(request.args))

    if 'error' in result:
        return jsonify({'error': result.get('error_description', 'Login mislukt')}), 403

    token = result.get('access_token')
    if not token:
        return jsonify({'error': 'Geen token ontvangen'}), 403

    import requests as http_requests

    # Check Entra group membership (single group for access)
    group_id = config.get('DashboardGroupId', '')
    if group_id:
        headers_auth = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
        resp = http_requests.post(
            'https://graph.microsoft.com/v1.0/me/checkMemberGroups',
            headers=headers_auth,
            json={'groupIds': [group_id]},
            timeout=10,
        )
        if resp.ok:
            member_groups = resp.json().get('value', [])
            if group_id not in member_groups:
                return jsonify({'error': 'Geen toegang — je bent geen lid van de juiste groep'}), 403
        else:
            return jsonify({'error': 'Groepscontrole mislukt'}), 403

    # Get user info from Microsoft Graph
    headers = {'Authorization': f'Bearer {token}'}
    user_resp = http_requests.get('https://graph.microsoft.com/v1.0/me', headers=headers, timeout=10)
    user_data = user_resp.json() if user_resp.ok else {}
    email = (user_data.get('mail') or user_data.get('userPrincipalName') or '').lower()

    # Look up user in local gebruikers table
    geb = g.db.execute('SELECT id, rol FROM gebruikers WHERE LOWER(email) = ? AND actief = 1', (email,)).fetchone()

    if not geb:
        # First user ever? Auto-create as beheerder
        has_any = g.db.execute('SELECT COUNT(*) as cnt FROM gebruikers').fetchone()['cnt']
        if has_any == 0:
            display = user_data.get('displayName', '')
            cur = g.db.execute(
                'INSERT INTO gebruikers (email, naam, rol) VALUES (?, ?, ?)',
                (email, display, 'beheerder')
            )
            g.db.commit()
            geb = g.db.execute('SELECT id, rol FROM gebruikers WHERE id = ?', (cur.lastrowid,)).fetchone()
        else:
            return jsonify({'error': 'Geen toegang — vraag je beheerder om je toe te voegen'}), 403

    is_beheerder = geb['rol'] == 'beheerder'

    # Get allowed vestiging IDs for non-beheerders
    allowed_vestiging_ids = []
    if not is_beheerder:
        rows = g.db.execute('SELECT vestiging_id FROM gebruiker_vestigingen WHERE gebruiker_id = ?', (geb['id'],)).fetchall()
        allowed_vestiging_ids = [r['vestiging_id'] for r in rows]
        if not allowed_vestiging_ids:
            return jsonify({'error': 'Geen vestigingen toegewezen — neem contact op met je beheerder'}), 403

    session.permanent = True
    session['user'] = {
        'displayName': user_data.get('displayName', ''),
        'email': email,
        'givenName': user_data.get('givenName', ''),
        'is_beheerder': is_beheerder,
        'allowed_vestiging_ids': allowed_vestiging_ids,
    }
    session['access_token'] = token

    return redirect('/')

@auth_bp.route('/me')
def me():
    user = session.get('user')
    if not user:
        return jsonify({'error': 'Niet ingelogd'}), 401
    return jsonify(user)

@auth_bp.route('/photo')
def photo():
    """Proxy the user's profile photo from Microsoft Graph."""
    token = session.get('access_token')
    if not token:
        return jsonify({'error': 'Niet ingelogd'}), 401
    import requests as http_requests
    try:
        resp = http_requests.get(
            'https://graph.microsoft.com/v1.0/me/photo/$value',
            headers={'Authorization': f'Bearer {token}'},
            timeout=10,
        )
        if resp.ok:
            from flask import Response
            return Response(resp.content, content_type=resp.headers.get('Content-Type', 'image/jpeg'))
    except Exception:
        pass
    # Return a 1x1 transparent PNG as fallback
    return '', 204

@auth_bp.route('/logout')
def logout():
    session.clear()
    tenant_id = config.get('TenantId', '')
    return redirect(f'https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/logout?post_logout_redirect_uri=/')
