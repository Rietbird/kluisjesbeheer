import json
import os

# config.json wordt eerst in backend/data/ gezocht (Docker-volume-aanpak),
# daarna backend/ zelf (bestaande installs / install.sh). Eerste hit wint.
_BACKEND_DIR = os.path.dirname(__file__)
_CONFIG_CANDIDATES = [
    os.path.join(_BACKEND_DIR, 'data', 'config.json'),
    os.path.join(_BACKEND_DIR, 'config.json'),
]

def _config_path():
    for p in _CONFIG_CANDIDATES:
        if os.path.exists(p):
            return p
    return _CONFIG_CANDIDATES[-1]  # fallback voor foutmeldingen

def load_config():
    try:
        with open(_config_path()) as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

config = load_config()
