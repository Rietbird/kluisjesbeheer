import time
import xml.etree.ElementTree as ET
import requests
from config import config


class MagisterClient:
    """Client for Medius (Magister/SOMtoday SWP) XML webservice."""

    CACHE_TTL = 60  # 1 minute

    def __init__(self, url=None, user=None, password=None):
        self.url = url or config.get('MagisterUrl', '')
        self.user = user or config.get('MagisterUser', '')
        self.password = password or config.get('MagisterPass', '')
        self._session_token = None
        self._token_time = 0
        self._cache = {}

    def _login(self):
        """Get a session token from the Medius webservice."""
        if self._session_token and time.time() - self._token_time < self.CACHE_TTL:
            return self._session_token

        params = {
            'Library': 'Algemeen',
            'Function': 'Login',
            'UserName': self.user,
            'Password': self.password,
            'Type': 'XML',
        }
        try:
            resp = requests.get(self.url, params=params, timeout=10, verify=False)
            root = ET.fromstring(resp.text)
            result = root.findtext('Result')
            if result != 'True':
                msg = root.findtext('ResultMessage') or 'Login mislukt'
                raise ConnectionError(f'Medius login mislukt: {msg}')
            self._session_token = root.findtext('SessionToken')
            self._token_time = time.time()
            return self._session_token
        except (requests.RequestException, Exception) as e:
            raise ConnectionError(f'Medius niet bereikbaar: {e}')

    def _call(self, function, stamnr=None):
        """Call an ADFuncties function and return the parsed XML Data element."""
        cache_key = f"{function}:{stamnr}"
        cached = self._cache.get(cache_key)
        if cached and time.time() - cached['time'] < self.CACHE_TTL:
            return cached['data']

        token = self._login()
        params = {
            'library': 'ADFuncties',
            'function': function,
            'SessionToken': token,
            'LesPeriode': '',
            'Type': 'XML',
        }
        if stamnr:
            params['StamNr'] = stamnr

        resp = requests.get(self.url, params=params, timeout=15, verify=False)
        root = ET.fromstring(resp.text)

        # Check for exceptions in the response
        exc = root.findtext('Exception')
        if exc:
            raise ConnectionError(f'Medius fout: {exc}: {root.findtext("ExceptionMsg")}')

        data = root.find('Data')
        self._cache[cache_key] = {'data': data, 'time': time.time()}
        return data

    def _call_data(self, layout):
        """Call the Data/GetData function with a named layout (ddlijsten).
        Returns the root element; caller should use .iter() or .findall() to find rows."""
        cache_key = f"GetData:{layout}"
        cached = self._cache.get(cache_key)
        if cached and time.time() - cached['time'] < self.CACHE_TTL:
            return cached['data']

        token = self._login()
        params = {
            'Library': 'Data',
            'Function': 'GetData',
            'SessionToken': token,
            'Layout': layout,
            'Type': 'XML',
        }
        resp = requests.get(self.url, params=params, timeout=60, verify=False)
        root = ET.fromstring(resp.text)

        result = root.findtext('Result')
        if result == 'False':
            msg = root.findtext('.//Fout_omschrijving') or 'Onbekende fout'
            raise ConnectionError(f'Medius GetData fout: {msg}')

        exc = root.findtext('Exception')
        if exc:
            raise ConnectionError(f'Medius fout: {exc}: {root.findtext("ExceptionMsg")}')

        self._cache[cache_key] = {'data': root, 'time': time.time()}
        return root

    def get_kluisjes(self):
        """Get all current locker data from Magister via GetData layout 'kluisjes-actueel'."""
        root = self._call_data('kluisjes-actueel')
        if root is None:
            return []

        kluisjes = []
        for node in root.findall('.//Kluisje'):
            kluisjes.append({
                'kluis_code': node.findtext('KluisCode', ''),
                'omschrijving': node.findtext('Omschrijving', ''),
                'slotnummer': node.findtext('Slotnummer_def', ''),
                'volgnr': node.findtext('Volgnr', ''),
                'stamnr': node.findtext('Leerlingnummer', ''),
                'datum_van': node.findtext('DatumVan', ''),
                'datum_tot': node.findtext('DatumTot', ''),
                'borg': node.findtext('Borg', ''),
                'huur': node.findtext('Huur', ''),
                'borg_ontvangen': node.findtext('BorgOntvangen', ''),
                'borg_retour': node.findtext('BorgRetour', ''),
                'sleutel': node.findtext('Sleutel_toew', '') or node.findtext('Sleutel_def', ''),
                'hangslotnr': node.findtext('Hangslotnr_toew', '') or node.findtext('Hangslotnr_def', ''),
                'info': node.findtext('Info', ''),
                'ingeleverd': node.findtext('Ingeleverd', ''),
            })
        return kluisjes

    def get_leerlingen(self):
        """Get all active students, returns list of dicts."""
        data = self._call('GetActiveStudents')
        if data is None:
            return []

        leerlingen = []
        for node in data.findall('.//Leerling'):
            leerlingen.append({
                'stamnr': node.findtext('stamnr_str', ''),
                'roepnaam': node.findtext('Roepnaam', ''),
                'tussenvoegsel': node.findtext('Tussenv', ''),
                'achternaam': node.findtext('Achternaam', ''),
                'naam': node.findtext('Volledige_naam', ''),
                'email': node.findtext('Email', ''),
                'login': node.findtext('Loginaccount.Naam', ''),
                'klas': node.findtext('Klas', ''),
                'leerjaar': node.findtext('Leerfase.Leerjaar', ''),
                'studie': node.findtext('Studie', ''),
                'locatie': node.findtext('Administratieve_eenheid.Omschrijving', ''),
            })
        return leerlingen

    def search_leerlingen(self, query):
        """Search students by name, class, or stamnr. Uses cached full list."""
        all_leerlingen = self.get_leerlingen()
        q = query.lower()
        return [
            l for l in all_leerlingen
            if q in l['naam'].lower()
            or q in l['klas'].lower()
            or q in l['stamnr'].lower()
            or q in l.get('email', '').lower()
        ]

    def get_klassen(self):
        """Get unique class list from all active students."""
        all_leerlingen = self.get_leerlingen()
        klassen = sorted(set(l['klas'] for l in all_leerlingen if l['klas']))
        return [{'naam': k} for k in klassen]

    def flush_cache(self):
        """Clear all cached data, forcing fresh API calls."""
        self._cache = {}
        self._session_token = None
        self._token_time = 0


# Singleton instance
magister = MagisterClient()
