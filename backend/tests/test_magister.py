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

MOCK_KLUISJES_XML = '''<?xml version="1.0"?>
<Response>
    <Result>True</Result>
    <Table>
        <Kluisjes>
            <Kluisje>
                <KluisCode>O054A</KluisCode>
                <Omschrijving>Kluisje O054A</Omschrijving>
                <Slotnummer_def></Slotnummer_def>
                <Volgnr>3</Volgnr>
                <Hangslotnr_def></Hangslotnr_def>
                <Sleutel_def>4884 D</Sleutel_def>
                <Leerlingnummer>22001</Leerlingnummer>
                <DatumVan>2025/08/01</DatumVan>
                <DatumTot>2026/07/31</DatumTot>
                <Borg>5</Borg>
                <Huur>10</Huur>
                <BorgOntvangen></BorgOntvangen>
                <BorgRetour></BorgRetour>
                <Slotnummer_toew></Slotnummer_toew>
                <Hangslotnr_toew></Hangslotnr_toew>
                <Sleutel_toew></Sleutel_toew>
                <Info></Info>
                <Ingeleverd>False</Ingeleverd>
            </Kluisje>
            <Kluisje>
                <KluisCode>O055A</KluisCode>
                <Omschrijving>Kluisje O055A</Omschrijving>
                <Slotnummer_def></Slotnummer_def>
                <Volgnr>4</Volgnr>
                <Hangslotnr_def></Hangslotnr_def>
                <Sleutel_def>1234 D</Sleutel_def>
                <Leerlingnummer></Leerlingnummer>
                <DatumVan>1899/12/30</DatumVan>
                <DatumTot>1899/12/30</DatumTot>
                <Borg></Borg>
                <Huur></Huur>
                <BorgOntvangen></BorgOntvangen>
                <BorgRetour></BorgRetour>
                <Slotnummer_toew></Slotnummer_toew>
                <Hangslotnr_toew></Hangslotnr_toew>
                <Sleutel_toew></Sleutel_toew>
                <Info></Info>
                <Ingeleverd></Ingeleverd>
            </Kluisje>
        </Kluisjes>
    </Table>
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


def test_get_kluisjes(mag_client):
    with patch('magister_client.requests.get', side_effect=_mock_get([MOCK_LOGIN_XML, MOCK_KLUISJES_XML])):
        result = mag_client.get_kluisjes()
        assert len(result) == 2
        assert result[0]['kluis_code'] == 'O054A'
        assert result[0]['stamnr'] == '22001'
        assert result[0]['sleutel'] == '4884 D'
        assert result[0]['borg'] == '5'
        assert result[0]['ingeleverd'] == 'False'
        # Second kluisje has no student
        assert result[1]['kluis_code'] == 'O055A'
        assert result[1]['stamnr'] == ''
        assert result[1]['sleutel'] == '1234 D'


def test_login_failed(mag_client):
    with patch('magister_client.requests.get', side_effect=_mock_get([MOCK_LOGIN_FAILED_XML])):
        with pytest.raises(ConnectionError, match='login mislukt|Ongeldige'):
            mag_client.search_leerlingen('test')
