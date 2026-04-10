import os
from datetime import timedelta
from flask import Flask, g, send_from_directory, request
from flask_cors import CORS
from config import config
from db import init_db, get_db, close_db

FRONTEND_DIST = os.path.join(os.path.dirname(__file__), '..', 'frontend', 'dist')

DB_PATH = os.path.join(os.path.dirname(__file__), 'kluisjesbeheer.db')

def create_app(test_config=None):
    app = Flask(__name__)

    secret_key = config.get('SecretKey', '')
    if not secret_key:
        raise RuntimeError('SecretKey is niet geconfigureerd in config.json')
    app.secret_key = secret_key

    app.permanent_session_lifetime = timedelta(hours=8)
    app.config.update(
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE='Lax',
        SESSION_COOKIE_SECURE=True,
        MAX_CONTENT_LENGTH=16 * 1024 * 1024,  # 16MB max upload
    )

    # CORS: configurable origins from config.json, always allow localhost dev server
    allowed_origins = config.get('AllowedOrigins', [])
    if 'http://localhost:5173' not in allowed_origins:
        allowed_origins.append('http://localhost:5173')
    CORS(app, origins=allowed_origins)

    db_path = DB_PATH
    if test_config:
        db_path = test_config.get('DB_PATH', db_path)

    init_db(db_path)

    @app.before_request
    def before_request():
        g.db = get_db(db_path)

    @app.teardown_request
    def teardown_request(exception):
        db = g.pop('db', None)
        close_db(db)

    # CSRF protection: require X-Requested-With header on state-changing requests.
    # Browsers enforce CORS preflight for custom headers, blocking cross-origin POST/PUT/DELETE.
    @app.before_request
    def csrf_check():
        if app.config.get('TESTING'):
            return
        if request.method in ('POST', 'PUT', 'DELETE') and request.path.startswith('/api/'):
            if not request.headers.get('X-Requested-With'):
                from flask import jsonify as _jsonify
                return _jsonify({'error': 'CSRF check failed'}), 403

    # Security headers
    @app.after_request
    def add_security_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response.headers['Permissions-Policy'] = 'camera=(), microphone=(), geolocation=()'
        if request.is_secure or request.headers.get('X-Forwarded-Proto') == 'https':
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        return response

    @app.route('/api/health')
    def health():
        return {'status': 'ok'}

    @app.route('/api/branding')
    def branding():
        # No login_required: branding must be visible on the login page
        try:
            rows = g.db.execute('SELECT key, value FROM instellingen').fetchall()
            inst = {r['key']: r['value'] for r in rows}
        except Exception:
            inst = {}
        return {
            'schoolNaam': inst.get('schoolNaam') or config.get('SchoolNaam', 'Kluisjesbeheer'),
            'schoolSubtitel': inst.get('schoolSubtitel') or config.get('SchoolSubtitel', ''),
            'schoolLogo': inst.get('schoolLogo') or config.get('SchoolLogo', '/img/logo.png'),
            'schoolKleur': inst.get('schoolKleur') or config.get('SchoolKleur', '#FF8200'),
        }

    # Register blueprints
    from auth import auth_bp
    app.register_blueprint(auth_bp)

    from api_vestigingen import vestigingen_bp
    app.register_blueprint(vestigingen_bp)

    from api_clusters import clusters_bp
    app.register_blueprint(clusters_bp)

    from api_kluisjes import kluisjes_bp
    app.register_blueprint(kluisjes_bp)

    from api_toewijzingen import toewijzingen_bp
    app.register_blueprint(toewijzingen_bp)

    from api_magister import magister_bp
    app.register_blueprint(magister_bp)

    from api_dashboard import dashboard_bp
    app.register_blueprint(dashboard_bp)

    from api_instellingen import instellingen_bp
    app.register_blueprint(instellingen_bp)

    from api_schooljaar import schooljaar_bp
    app.register_blueprint(schooljaar_bp)

    # SPA catch-all
    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def serve_frontend(path):
        if path and os.path.isfile(os.path.join(FRONTEND_DIST, path)):
            return send_from_directory(FRONTEND_DIST, path)
        index = os.path.join(FRONTEND_DIST, 'index.html')
        if os.path.isfile(index):
            return send_from_directory(FRONTEND_DIST, 'index.html')
        return {'error': 'Frontend not built'}, 404

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(port=5000)
