import time
import requests
from config import config

class MagisterClient:
    CACHE_TTL = 300  # 5 minutes

    def __init__(self, base_url=None, token=None):
        self.base_url = base_url or config.get('MagisterBaseUrl', '')
        self.token = token or config.get('MagisterApiToken', '')
        self._cache = {}

    def _get(self, path, params=None):
        cache_key = f"{path}:{params}"
        cached = self._cache.get(cache_key)
        if cached and time.time() - cached['time'] < self.CACHE_TTL:
            return cached['data']

        try:
            headers = {'Authorization': f'Bearer {self.token}'} if self.token else {}
            resp = requests.get(
                f"{self.base_url}{path}",
                params=params,
                headers=headers,
                timeout=10,
            )
            if resp.ok:
                data = resp.json()
                self._cache[cache_key] = {'data': data, 'time': time.time()}
                return data
            return []
        except Exception:
            return []

    def search_leerlingen(self, query):
        return self._get('/leerlingen', params={'q': query})

    def get_klassen(self):
        return self._get('/klassen')

# Singleton instance
magister = MagisterClient()
