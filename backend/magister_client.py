import os
import time
import urllib3
import xml.etree.ElementTree as ET
import requests
from config import config

# Magister/SWP servers often have self-signed or outdated certificates.
# Set MAGISTER_VERIFY_SSL=1 to enable verification, or provide a CA bundle path.
_verify_ssl = os.environ.get('MAGISTER_VERIFY_SSL', '')
if _verify_ssl == '1' or _verify_ssl.lower() == 'true':
    MAGISTER_SSL_VERIFY = True
elif _verify_ssl and os.path.isfile(_verify_ssl):
    MAGISTER_SSL_VERIFY = _verify_ssl  # path to CA bundle
else:
    MAGISTER_SSL_VERIFY = False
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class MagisterClient:
    """Client for Medius (Magister/SOMtoday SWP) XML webservice."""

    CACHE_TTL = 60  # 1 minute

    def __init__(self, url=None, user=None, password=None):
        self._override_url = url
        self._override_user = user
        self._override_password = password
        self._session_token = None
        self._token_time = 0
        self._cache = {}

    def _load_credentials(self):
        """Load Magister credentials: DB settings take priority, then config.json."""
        if self._override_url:
            return self._override_url, self._override_user, self._override_password
        try:
            from flask import g
            rows = g.db.execute(
                "SELECT key, value FROM instellingen WHERE key IN ('magister_url', 'magister_user', 'magister_pass')"
            ).fetchall()
            db_cfg = {r['key']: r['value'] for r in rows}
            if db_cfg.get('magister_url') and db_cfg.get('magister_user') and db_cfg.get('magister_pass'):
                from crypto_util import decrypt
                return db_cfg['magister_url'], db_cfg['magister_user'], decrypt(db_cfg['magister_pass'])
        except Exception:
            pass
        return config.get('MagisterUrl', ''), config.get('MagisterUser', ''), config.get('MagisterPass', '')

    @property
    def url(self):
        return self._load_credentials()[0]

    @property
    def user(self):
        return self._load_credentials()[1]

    @property
    def password(self):
        return self._load_credentials()[2]

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
            resp = requests.get(self.url, params=params, timeout=10, verify=MAGISTER_SSL_VERIFY)
            root = ET.fromstring(resp.text)
            result = root.findtext('Result')
            if result != 'True':
                msg = root.findtext('ResultMessage') or 'Login mislukt'
                raise ConnectionError(f'Medius login mislukt: {msg}')
            self._session_token = root.findtext('SessionToken')
            self._token_time = time.time()
            return self._session_token
        except (requests.Timeout, requests.ConnectionError):
            # Network-level failure (port blocked / not whitelisted / DNS).
            # Never include the request URL: it carries the password as a query param.
            raise ConnectionError(
                'Geen verbinding met de Magister-webservice (poort 8800). '
                'Controleer of het server-IP op de SWP-whitelist staat en of de URL klopt.'
            )
        except ConnectionError:
            # Our own 'login mislukt' message -- pass through unchanged.
            raise
        except requests.RequestException:
            raise ConnectionError('Magister-webservice gaf een onverwacht antwoord (HTTP-fout).')
        except ET.ParseError:
            raise ConnectionError('Magister-webservice gaf een ongeldig antwoord (geen geldige XML).')
        except Exception:
            # Catch-all so an unexpected error never escapes as a raw exception
            # (which could leak the request URL incl. password). No {e}.
            raise ConnectionError('Onverwachte fout bij het benaderen van de Magister-webservice.')

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

        resp = requests.get(self.url, params=params, timeout=15, verify=MAGISTER_SSL_VERIFY)
        root = ET.fromstring(resp.text)

        # Check for exceptions in the response
        exc = root.findtext('Exception')
        if exc:
            raise ConnectionError(f'Medius fout: {exc}: {root.findtext("ExceptionMsg")}')

        data = root.find('Data')
        self._cache[cache_key] = {'data': data, 'time': time.time()}
        return data

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

    def get_leerlingen_by_klas(self, klas):
        """Get students by exact class match."""
        all_leerlingen = self.get_leerlingen()
        return [l for l in all_leerlingen if l['klas'] == klas]

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
