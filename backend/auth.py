import html
import json
import os
import msal
from functools import wraps
from flask import Blueprint, redirect, request, session, jsonify, url_for, g, Response
from config import config, _config_path

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
    body = f'''<!DOCTYPE html>
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
    return Response(body, status=status, mimetype='text/html')

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

def _config_complete():
    """Check of de Entra-velden in config.json daadwerkelijk zijn ingevuld
    (niet leeg, niet de VUL_IN_*-placeholders uit install.sh)."""
    for veld in ('TenantId', 'ClientId', 'ClientSecret', 'RedirectUri'):
        waarde = config.get(veld, '').strip()
        if not waarde or waarde.startswith('VUL_IN'):
            return False, veld
    return True, None


def _setup_page(error=None):
    """Render de setup-wizard pagina (server-side HTML, geen Entra nodig)."""
    kleur = '#FF8200'
    err_html = f'<div class="error">{html.escape(error)}</div>' if error else ''
    # Vul bestaande waarden in als die er al zijn (VUL_IN_* tonen we leeg)
    def _val(k):
        v = config.get(k, '')
        return '' if (not v or str(v).startswith('VUL_IN')) else html.escape(str(v))
    page = f'''<!DOCTYPE html>
<html lang="nl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Eerste instelling — Kluisjesbeheer</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
         background: #f1f5f9; color: #1e293b; min-height: 100vh;
         display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 24px; }}
  .card {{ background: white; border-radius: 16px; box-shadow: 0 4px 24px rgba(0,0,0,.08);
           max-width: 520px; width: 100%; padding: 40px 36px; }}
  .logo {{ font-size: 28px; margin-bottom: 6px; }}
  h1 {{ font-size: 22px; color: #1e3a5f; margin-bottom: 6px; }}
  .sub {{ font-size: 14px; color: #64748b; margin-bottom: 28px; line-height: 1.5; }}
  .field {{ margin-bottom: 18px; }}
  label {{ display: block; font-size: 13px; font-weight: 600; color: #374151; margin-bottom: 5px; }}
  .hint {{ font-size: 12px; color: #94a3b8; margin-bottom: 5px; }}
  input {{ width: 100%; border: 1.5px solid #e2e8f0; border-radius: 8px;
           padding: 10px 14px; font-size: 14px; color: #1e293b; outline: none;
           transition: border-color .15s; }}
  input:focus {{ border-color: {kleur}; }}
  .btn {{ width: 100%; background: {kleur}; color: white; border: none;
          border-radius: 8px; padding: 13px; font-size: 15px; font-weight: 600;
          cursor: pointer; margin-top: 8px; transition: opacity .15s; }}
  .btn:hover {{ opacity: .88; }}
  .error {{ background: #fef2f2; border: 1px solid #fecaca; color: #dc2626;
            border-radius: 8px; padding: 10px 14px; font-size: 13px; margin-bottom: 18px; }}
  .footer {{ margin-top: 20px; font-size: 11px; color: #94a3b8; text-align: center; }}
  .section {{ font-size: 11px; font-weight: 700; color: #94a3b8; letter-spacing: .08em;
              text-transform: uppercase; margin: 24px 0 14px; border-top: 1px solid #f1f5f9; padding-top: 18px; }}
</style>
</head>
<body>
  <div class="card">
    <div class="logo">🔐</div>
    <h1>Welkom bij Kluisjesbeheer</h1>
    <p class="sub">Vul de Entra ID-gegevens in om de app te activeren. Je vindt deze in de Azure Portal onder <strong>App registrations → jouw app</strong>.</p>
    {err_html}
    <form method="post" action="/auth/setup">
      <div class="field">
        <label>Tenant ID</label>
        <div class="hint">Azure Portal → Azure Active Directory → Tenant ID</div>
        <input type="text" name="TenantId" value="{_val('TenantId')}" placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx" required>
      </div>
      <div class="field">
        <label>Client ID (Application ID)</label>
        <div class="hint">App registrations → jouw app → Application (client) ID</div>
        <input type="text" name="ClientId" value="{_val('ClientId')}" placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx" required>
      </div>
      <div class="field">
        <label>Client Secret</label>
        <div class="hint">App registrations → jouw app → Certificates &amp; secrets → Client secrets</div>
        <input type="password" name="ClientSecret" value="{_val('ClientSecret')}" placeholder="Plak hier de secret value" required>
      </div>
      <div class="section">Redirect URI</div>
      <div class="field">
        <label>Redirect URI</label>
        <div class="hint">Moet exact overeenkomen met wat je in Entra hebt ingevuld onder Authentication → Redirect URIs</div>
        <input type="text" name="RedirectUri" value="{_val('RedirectUri') or f'https://{request.host}/auth/callback'}" required>
      </div>
      <button type="submit" class="btn">Opslaan en inloggen →</button>
    </form>
    <div class="footer">Kluisjesbeheer — eerste instelling</div>
  </div>
</body>
</html>'''
    return Response(page, status=200, mimetype='text/html')


@auth_bp.route('/setup', methods=['GET', 'POST'])
def setup():
    """Setup-wizard: alleen toegankelijk als de Entra-config nog niet compleet is."""
    ok, _ = _config_complete()
    if ok:
        return redirect('/')

    if request.method == 'GET':
        return _setup_page()

    # POST — valideer en sla op
    tenant = request.form.get('TenantId', '').strip()
    client_id = request.form.get('ClientId', '').strip()
    client_secret = request.form.get('ClientSecret', '').strip()
    redirect_uri = request.form.get('RedirectUri', '').strip()

    if not all([tenant, client_id, client_secret, redirect_uri]):
        return _setup_page(error='Vul alle velden in.')
    if not redirect_uri.startswith('http'):
        return _setup_page(error='Redirect URI moet beginnen met http:// of https://')

    # Lees bestaande config zodat we SecretKey etc. bewaren
    cfg_path = _config_path()
    try:
        with open(cfg_path) as f:
            existing = json.load(f)
    except Exception:
        existing = {}

    existing['TenantId'] = tenant
    existing['ClientId'] = client_id
    existing['ClientSecret'] = client_secret
    existing['RedirectUri'] = redirect_uri

    try:
        with open(cfg_path, 'w') as f:
            json.dump(existing, f, indent=2)
    except Exception as e:
        return _setup_page(error=f'Kan config.json niet schrijven: {e}')

    # Herlaad config in geheugen en reset MSAL
    import config as config_module
    new_cfg = config_module.load_config()
    config_module.config.clear()
    config_module.config.update(new_cfg)
    # Ook de lokale referentie in dit module bijwerken
    config.clear()
    config.update(new_cfg)
    global _msal_app
    _msal_app = None

    return redirect('/auth/login')


@auth_bp.route('/login')
def login():
    ok, missend = _config_complete()
    if not ok:
        return redirect('/auth/setup')
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

@auth_bp.route('/dev-login')
def dev_login():
    """Bypass MSAL/Entra voor lokale ontwikkeling en screenshot-generatie.
    Alleen actief als FLASK_ENV=development of app.testing — anders 404."""
    from flask import current_app
    if not (os.environ.get('FLASK_ENV') == 'development' or current_app.config.get('TESTING')):
        return jsonify({'error': 'Not found'}), 404
    email = request.args.get('email', 'demo@kluisjesbeheer.local')
    naam = request.args.get('naam', 'Demo Beheerder')
    session.permanent = True
    session['user'] = {
        'displayName': naam,
        'email': email,
        'givenName': naam.split(' ')[0],
        'is_beheerder': True,
        'allowed_vestiging_ids': [],
    }
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
