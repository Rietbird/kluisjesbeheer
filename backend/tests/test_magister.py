import pytest
from unittest.mock import patch, MagicMock
from magister_client import MagisterClient

MOCK_LOGIN_XML = '''<?xml version="1.0"?>
<Response>
    <Result>True</Result>
    <SessionToken>test-token-123</SessionToken>
</Response>'''

MOCK_STUDENTS_XML = '''<?xml version="1.0"?>
<Response>
    <Data>
        <Leerlingen>
            <Leerling>
                <stamnr_str>22001</stamnr_str>
                <Roepnaam>Emma</Roepnaam>
                <Tussenv></Tussenv>
                <Achternaam>Botter</Achternaam>
                <Volledige_naam>Botter, Emma</Volledige_naam>
                <Email>emma.botter@leerling.School.nl</Email>
                <Loginaccount.Naam>ebotter</Loginaccount.Naam>
                <Klas>2A</Klas>
                <Leerfase.Leerjaar>2</Leerfase.Leerjaar>
                <Studie>HAVO</Studie>
                <Administratieve_eenheid.Omschrijving>Hoofdlocatie</Administratieve_eenheid.Omschrijving>
            </Leerling>
            <Leerling>
                <stamnr_str>22002</stamnr_str>
                <Roepnaam>Lucas</Roepnaam>
                <Tussenv>de</Tussenv>
                <Achternaam>Vries</Achternaam>
                <Volledige_naam>Vries, Lucas de</Volledige_naam>
                <Email>lucas.devries@leerling.School.nl</Email>
                <Loginaccount.Naam>ldevries</Loginaccount.Naam>
                <Klas>1C</Klas>
                <Leerfase.Leerjaar>1</Leerfase.Leerjaar>
                <Studie>VWO</Studie>
                <Administratieve_eenheid.Omschrijving>Hoofdlocatie</Administratieve_eenheid.Omschrijving>
            </Leerling>
        </Leerlingen>
    </Data>
</Response>'''

MOCK_LOGIN_FAILED_XML = '''<?xml version="1.0"?>
<Response>
    <Result>False</Result>
    <ResultMessage>Ongeldige gebruikersnaam of wachtwoord</ResultMessage>
</Response>'''


@pytest.fixture
def mag_client():
    return MagisterClient(url='https://test.swp.nl/doc', user='testuser', password='testpass')


def _mock_get(responses):
    """Create a mock requests.get that returns different responses per call."""
    call_count = [0]
    def side_effect(*args, **kwargs):
        mock_resp = MagicMock()
        mock_resp.ok = True
        mock_resp.text = responses[min(call_count[0], len(responses) - 1)]
        call_count[0] += 1
        return mock_resp
    return side_effect


def test_search_leerlingen(mag_client):
    with patch('magister_client.requests.get', side_effect=_mock_get([MOCK_LOGIN_XML, MOCK_STUDENTS_XML])):
        result = mag_client.search_leerlingen('Emma')
        assert len(result) == 1
        assert result[0]['naam'] == 'Botter, Emma'
        assert result[0]['klas'] == '2A'
        assert result[0]['stamnr'] == '22001'


def test_search_leerlingen_cached(mag_client):
    with patch('magister_client.requests.get', side_effect=_mock_get([MOCK_LOGIN_XML, MOCK_STUDENTS_XML])) as mock_get:
        mag_client.search_leerlingen('Emma')
        mag_client.search_leerlingen('Lucas')
        # Login + GetActiveStudents = 2 calls; second search uses cache
        assert mock_get.call_count == 2


def test_magister_timeout(mag_client):
    with patch('magister_client.requests.get', side_effect=Exception('Timeout')):
        with pytest.raises(ConnectionError):
            mag_client.search_leerlingen('test')


def test_get_klassen(mag_client):
    with patch('magister_client.requests.get', side_effect=_mock_get([MOCK_LOGIN_XML, MOCK_STUDENTS_XML])):
        result = mag_client.get_klassen()
        assert len(result) == 2
        namen = [k['naam'] for k in result]
        assert '1C' in namen
        assert '2A' in namen


def test_login_failed(mag_client):
    with patch('magister_client.requests.get', side_effect=_mock_get([MOCK_LOGIN_FAILED_XML])):
        with pytest.raises(ConnectionError, match='login mislukt|Ongeldige'):
            mag_client.search_leerlingen('test')


def test_timeout_error_does_not_leak_password(mag_client):
    """A network timeout must produce a friendly message WITHOUT the password.
    The SWP webservice sends credentials as URL query params, so a raw requests
    exception would otherwise leak the Magister password into the UI."""
    import requests
    # requests' real exception text includes the full request URL incl. password
    boom = requests.ConnectionError(
        "HTTPSConnectionPool(host='test.swp.nl', port=8800): Max retries exceeded "
        "with url: /doc?Library=Algemeen&Function=Login&UserName=testuser"
        "&Password=testpass&Type=XML (Caused by ConnectTimeoutError(...))"
    )
    with patch('magister_client.requests.get', side_effect=boom):
        with pytest.raises(ConnectionError) as ei:
            mag_client.search_leerlingen('test')
    msg = str(ei.value)
    assert 'testpass' not in msg
    assert 'Password=' not in msg
    assert 'poort 8800' in msg and 'whitelist' in msg


def test_safe_error_strips_password():
    """api_magister._safe_error masks any Password=... query param."""
    from api_magister import _safe_error
    raw = ("Max retries exceeded with url: /doc?UserName=u&Password=REMOVED-PW1"
           "REMOVED-PW2&Type=XML")
    cleaned = _safe_error(ConnectionError(raw))
    assert '***REMOVED-Demo-PW***' not in cleaned
    assert 'Password=***' in cleaned
