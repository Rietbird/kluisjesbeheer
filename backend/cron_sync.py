#!/usr/bin/env python3
"""Daily cron: refresh student list from Magister so new students are available for assignment.
Run via: /opt/kluisjesbeheer/.venv/bin/python /opt/kluisjesbeheer/backend/cron_sync.py
"""
import sys
sys.path.insert(0, '/opt/kluisjesbeheer/backend')
from magister_client import MagisterClient

def main():
    print('=== CRON MAGISTER LEERLINGEN SYNC ===')
    magister = MagisterClient()
    try:
        leerlingen = magister.get_leerlingen()
        klassen = sorted(set(l['klas'] for l in leerlingen if l['klas']))
        print(f'{len(leerlingen)} leerlingen opgehaald, {len(klassen)} klassen')
        print('Done!')
    except Exception as e:
        print(f'ERROR: Magister niet bereikbaar: {e}')
        sys.exit(1)

if __name__ == '__main__':
    main()
