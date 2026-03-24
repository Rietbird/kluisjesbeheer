import json
import os

_CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'config.json')

def load_config():
    try:
        with open(_CONFIG_PATH) as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

config = load_config()
