import os
import sys
import pytest
import tempfile

# Ensure backend/ is on the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from db import get_db, init_db, close_db

@pytest.fixture
def db_path():
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    yield path
    try:
        os.unlink(path)
    except OSError:
        pass  # Windows may keep SQLite file locked briefly

@pytest.fixture
def db(db_path):
    conn = init_db(db_path)
    yield conn
    close_db(conn)

@pytest.fixture
def client(db_path):
    """Shared Flask test client with authenticated session."""
    from app import create_app
    app = create_app(test_config={'DB_PATH': db_path})
    app.config['TESTING'] = True
    with app.test_client() as c:
        with c.session_transaction() as sess:
            sess['user'] = {'displayName': 'Test', 'email': 'test@school.nl'}
        yield c
