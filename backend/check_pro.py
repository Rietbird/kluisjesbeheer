#!/usr/bin/env python3
import sys
sys.path.insert(0, '.')
from magister_client import magister

kluisjes = magister.get_kluisjes()
leerlingen = magister.get_leerlingen()
leerling_map = {l['stamnr']: l for l in leerlingen}

p_kluisjes = [k for k in kluisjes if k['kluis_code'].startswith('P')]
with_stamnr = [k for k in p_kluisjes if k.get('stamnr', '').strip()]

print(f"Magister P-kluisjes totaal: {len(p_kluisjes)}")
print(f"P-kluisjes met stamnr: {len(with_stamnr)}")
print()

# Check why they were skipped
skipped_no_leerling = 0
skipped_no_date = 0
skipped_1899 = 0
ok = 0

for k in with_stamnr:
    stamnr = k['stamnr'].strip()
    datum_van = k.get('datum_van', '').replace('/', '-')
    datum_tot = k.get('datum_tot', '').replace('/', '-')

    if datum_van.startswith('1899'):
        datum_van = ''
    if datum_tot.startswith('1899'):
        datum_tot = ''

    leerling = leerling_map.get(stamnr)

    if not leerling:
        skipped_no_leerling += 1
        continue
    if not datum_van:
        skipped_no_date += 1
        continue
    ok += 1

print(f"Resultaat:")
print(f"  OK (zou geimporteerd moeten zijn): {ok}")
print(f"  Geen datum_van: {skipped_no_date}")
print(f"  Leerling niet in actieve lijst: {skipped_no_leerling}")
print()

# Show first 10 with stamnr
print("Eerste 10 P-kluisjes met stamnr:")
for k in with_stamnr[:10]:
    stamnr = k['stamnr'].strip()
    ll = leerling_map.get(stamnr)
    print(f"  {k['kluis_code']}: stamnr={stamnr}, van={k['datum_van']}, tot={k['datum_tot']}, "
          f"leerling={'JA' if ll else 'NEE'}")
