import pytest
import tempfile, os
from app import create_app

@pytest.fixture
def unauth_client():
    """Unauthenticated client for auth tests."""
    fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    app = create_app(test_config={'DB_PATH': db_path})
    app.config['TESTING'] = True
    with app.test_client() as c:
        yield c
    try:
        os.unlink(db_path)
    except OSError:
        pass  # Windows may keep a file lock briefly; ignore on cleanup

def test_health(unauth_client):
    rv = unauth_client.get('/api/health')
    assert rv.status_code == 200
    assert rv.get_json()['status'] == 'ok'

def test_me_unauthenticated(unauth_client):
    rv = unauth_client.get('/auth/me')
    assert rv.status_code == 401

def test_me_authenticated(unauth_client):
    with unauth_client.session_transaction() as sess:
        sess['user'] = {'displayName': 'Jan', 'email': 'jan@school.nl'}
    rv = unauth_client.get('/auth/me')
    assert rv.status_code == 200
    assert rv.get_json()['displayName'] == 'Jan'

def test_protected_endpoint_requires_login(unauth_client):
    rv = unauth_client.get('/api/vestigingen')
    assert rv.status_code == 401
