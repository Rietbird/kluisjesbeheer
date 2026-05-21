import html
import msal
from functools import wraps
from flask import Blueprint, redirect, request, session, jsonify, url_for, g, Response
from config import config

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


def _error_page(title, message, status=403):
    """Render a styled error page consistent with the application design.
    Alle user-input wordt HTML-escaped (defensief — message kan in theorie
    error_description van Entra bevatten)."""
    session.clear()
    kleur = html.escape(config.get('SchoolKleur', '#FF8200'))
    school = html.escape(config.get('SchoolNaam', 'Kluisjesbeheer'))
    title = html.escape(title)
    message = html.escape(message)
    html = f'''<!DOCTYPE html>
<html lang="nl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} — {school}</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
         background: #f1f5f9; color: #1e293b; min-height: 100vh;
         display: flex; flex-direction: column; align-items: center; justify-content: center; }}
  .card {{ background: white; border-radius: 12px; box-shadow: 0 4px 24px rgba(0,0,0,.08);
           max-width: 440px; width: 90%; padding: 40px 32px; text-align: center; }}
  .icon {{ width: 56px; height: 56px; border-radius: 50%; background: #fef2f2;
           display: flex; align-items: center; justify-content: center;
           margin: 0 auto 20px; font-size: 24px; }}
  h1 {{ font-size: 20px; color: #1e3a5f; margin-bottom: 12px; }}
  p {{ font-size: 14px; color: #64748b; line-height: 1.6; margin-bottom: 24px; }}
  .btn {{ display: inline-block; background: {kleur}; color: white; padding: 10px 28px;
          border-radius: 8px; text-decoration: none; font-size: 14px; font-weight: 600;
          transition: opacity .15s; }}
  .btn:hover {{ opacity: .85; }}
  .footer {{ margin-top: 24px; font-size: 11px; color: #94a3b8; }}
</style>
</head>
<body>
  <div class="card">
    <div class="icon">&#128274;</div>
    <h1>{title}</h1>
    <p>{message}</p>
    <a href="/auth/logout" class="btn">Opnieuw inloggen</a>
    <div class="footer">{school}</div>
  </div>
</body>
</html>'''
    return Response(html, status=status, mimetype='text/html')

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


def beheerder_required(f):
    """Decorator: alleen beheerders. Voor config-routes (vestigingen,
    clusters, gebruikers, instellingen, backups, magister-config, sync).
    Gebruik na @login_required (of in plaats van — beheerder is ook ingelogd)."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user' not in session:
            return jsonify({'error': 'Niet ingelogd'}), 401
        if not session.get('user', {}).get('is_beheerder'):
            return jsonify({'error': 'Alleen beheerders'}), 403
        return f(*args, **kwargs)
    return decorated


def user_vestiging_ids():
    """Geef de set van vestiging-IDs die de huidige user mag zien.
    Beheerders zien alle vestigingen (returnt None — niet filteren).
    Conciërges zien alleen toegewezen vestigingen."""
    user = session.get('user', {})
    if user.get('is_beheerder'):
        return None  # geen filter
    return set(user.get('allowed_vestiging_ids', []))


def assert_vestiging_access(vestiging_id):
    """Raise 403 als de huidige user geen toegang heeft tot deze vestiging.
    Beheerders mogen alles. Conciërges alleen hun toegewezen vestiging(en).
    Return: None (OK) of Flask Response (403)."""
    allowed = user_vestiging_ids()
    if allowed is None:
        return None  # beheerder
    try:
        vid = int(vestiging_id)
    except (TypeError, ValueError):
        return jsonify({'error': 'Ongeldige vestiging'}), 400
    if vid not in allowed:
        return jsonify({'error': 'Geen toegang tot deze vestiging'}), 403
    return None

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
        return _error_page('Inloggen mislukt', result.get('error_description', 'Er ging iets mis bij het inloggen. Probeer het opnieuw.'))

    token = result.get('access_token')
    if not token:
        return _error_page('Inloggen mislukt', 'Er is geen token ontvangen van Microsoft. Probeer het opnieuw.')

    import requests as http_requests

    # Toegangscontrole gebeurt in Entra zelf via "Assignment required: Yes"
    # op de Enterprise Application (Microsoft regelt vóór we hier komen).
    # Onze gebruikers-tabel hieronder bepaalt vervolgens rol + vestigingen.
    # (DashboardGroupId-config wordt genegeerd; was de oude flow.)

    # Get user info from Microsoft Graph
    headers = {'Authorization': f'Bearer {token}'}
    user_resp = http_requests.get('https://graph.microsoft.com/v1.0/me', headers=headers, timeout=10)
    user_data = user_resp.json() if user_resp.ok else {}
    email = (user_data.get('mail') or user_data.get('userPrincipalName') or '').lower()

    # Look up user in local gebruikers table
    geb = g.db.execute('SELECT id, rol FROM gebruikers WHERE LOWER(email) = ? AND actief = 1', (email,)).fetchone()

    if not geb:
        # Auto-create user op basis van Entra-login. Toegang is op dit punt
        # al gevalideerd door Entra ("Assignment required" op de Enterprise
        # App), dus iedereen die hier komt mag in principe binnen.
        #   - Eerste gebruiker ooit -> beheerder (bootstrap)
        #   - Daarna -> concierge zonder vestiging
        # De foutpagina "Geen vestigingen" hieronder dwingt af dat een
        # bestaande beheerder de nieuwe user nog aan een vestiging koppelt
        # voor hij iets kan doen.
        #
        # Race-veilig: BEGIN IMMEDIATE pakt write-lock op de DB zodat twee
        # parallelle eerste-logins niet beide tot beheerder promoveren.
        display = user_data.get('displayName', '')
        g.db.execute('BEGIN IMMEDIATE')
        try:
            has_any = g.db.execute('SELECT COUNT(*) as cnt FROM gebruikers').fetchone()['cnt']
            nieuwe_rol = 'beheerder' if has_any == 0 else 'concierge'
            cur = g.db.execute(
                'INSERT INTO gebruikers (email, naam, rol) VALUES (?, ?, ?)',
                (email, display, nieuwe_rol)
            )
            g.db.commit()
        except Exception:
            g.db.rollback()
            raise
        geb = g.db.execute('SELECT id, rol FROM gebruikers WHERE id = ?', (cur.lastrowid,)).fetchone()

    is_beheerder = geb['rol'] == 'beheerder'

    # Get allowed vestiging IDs for non-beheerders
    allowed_vestiging_ids = []
    if not is_beheerder:
        rows = g.db.execute('SELECT vestiging_id FROM gebruiker_vestigingen WHERE gebruiker_id = ?', (geb['id'],)).fetchall()
        allowed_vestiging_ids = [r['vestiging_id'] for r in rows]
        if not allowed_vestiging_ids:
            return _error_page('Geen vestigingen', 'Er zijn nog geen vestigingen aan je account gekoppeld. Neem contact op met je beheerder.')

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

@auth_bp.route('/logout', methods=['GET', 'POST'])
def logout():
    """Log de gebruiker uit. POST (frontend-knop) is voorkeur — voorkomt
    forced-logout via `<img src="/auth/logout">` van een derde site.
    GET-variant is voor backward-compat (bookmarks, oude tabs); doet ook
    session.clear() maar Microsoft-redirect alleen bij POST."""
    session.clear()
    if request.method == 'POST':
        tenant_id = config.get('TenantId', '')
        # Microsoft requires an absolute URI for post_logout_redirect_uri
        from urllib.parse import urlparse
        parsed = urlparse(config.get('RedirectUri', ''))
        base_url = f'{parsed.scheme}://{parsed.netloc}'
        return redirect(f'https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/logout?post_logout_redirect_uri={base_url}/')
    # GET: alleen sessie wissen, terug naar app-root (geen Microsoft-redirect
    # om CSRF-forced-logout te beperken tot lokale flow).
    return redirect('/')
