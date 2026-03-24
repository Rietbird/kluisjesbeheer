import pytest
from unittest.mock import patch, MagicMock
from magister_client import MagisterClient

@pytest.fixture
def mag_client():
    return MagisterClient(base_url='https://magister.example.com/api', token='test-token')

def test_search_leerlingen(mag_client):
    mock_resp = MagicMock()
    mock_resp.ok = True
    mock_resp.json.return_value = [
        {'stamnummer': '22001', 'naam': 'Emma Botter', 'klas': '2A'},
        {'stamnummer': '22002', 'naam': 'Emmanuel Osei', 'klas': '1C'},
    ]
    with patch('magister_client.requests.get', return_value=mock_resp):
        result = mag_client.search_leerlingen('Emma')
        assert len(result) == 2
        assert result[0]['naam'] == 'Emma Botter'

def test_search_leerlingen_cached(mag_client):
    mock_resp = MagicMock()
    mock_resp.ok = True
    mock_resp.json.return_value = [{'stamnummer': '22001', 'naam': 'Emma', 'klas': '2A'}]
    with patch('magister_client.requests.get', return_value=mock_resp) as mock_get:
        mag_client.search_leerlingen('Emma')
        mag_client.search_leerlingen('Emma')
        assert mock_get.call_count == 1  # second call served from cache

def test_magister_timeout(mag_client):
    with patch('magister_client.requests.get', side_effect=Exception('Timeout')):
        result = mag_client.search_leerlingen('test')
        assert result == []

def test_get_klassen(mag_client):
    mock_resp = MagicMock()
    mock_resp.ok = True
    mock_resp.json.return_value = [{'id': '1', 'naam': '1A'}, {'id': '2', 'naam': '2B'}]
    with patch('magister_client.requests.get', return_value=mock_resp):
        result = mag_client.get_klassen()
        assert len(result) == 2
