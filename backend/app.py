import os
from datetime import timedelta
from flask import Flask, g, send_from_directory
from flask_cors import CORS
from config import config
from db import init_db, get_db, close_db

FRONTEND_DIST = os.path.join(os.path.dirname(__file__), '..', 'frontend', 'dist')

DB_PATH = os.path.join(os.path.dirname(__file__), 'kluisjesbeheer.db')

def create_app(test_config=None):
    app = Flask(__name__)

    app.secret_key = config.get('SecretKey', 'dev-secret-key')
    app.permanent_session_lifetime = timedelta(hours=8)
    app.config.update(
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE='Lax',
        # SESSION_COOKIE_SECURE is not set: Cloudflare tunnel does HTTPS termination,
        # Flask sees HTTP. Same pattern as ICT Dashboard.
    )

    CORS(app)

    db_path = DB_PATH
    if test_config:
        db_path = test_config.get('DB_PATH', db_path)

    # Initialize database on first run
    init_db(db_path)

    @app.before_request
    def before_request():
        g.db = get_db(db_path)

    @app.teardown_request
    def teardown_request(exception):
        db = g.pop('db', None)
        close_db(db)

    @app.route('/api/health')
    def health():
        return {'status': 'ok'}

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

    # SPA catch-all: serve frontend dist for non-API/auth routes
    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def serve_frontend(path):
        # Serve static assets (js, css, etc.)
        full_path = os.path.join(FRONTEND_DIST, path)
        if path and os.path.isfile(full_path):
            return send_from_directory(FRONTEND_DIST, path)
        # All other routes: serve index.html (SPA routing)
        index = os.path.join(FRONTEND_DIST, 'index.html')
        if os.path.isfile(index):
            return send_from_directory(FRONTEND_DIST, 'index.html')
        return {'error': 'Frontend not built. Run: cd frontend && npm run build'}, 404

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, port=5000)
