#!/usr/bin/env python3
"""Inspect Magister data to determine prefix/cluster structure."""
import re
from magister_client import magister

kluisjes = magister.get_kluisjes()

prefixes = {}
for k in kluisjes:
    code = k["kluis_code"].strip()
    if not code:
        continue
    match = re.match(r"^([A-Za-z]+\d?)", code)
    if match:
        prefix = match.group(1)
        if prefix not in prefixes:
            prefixes[prefix] = {"count": 0, "samples": []}
        prefixes[prefix]["count"] += 1
        if len(prefixes[prefix]["samples"]) < 3:
            prefixes[prefix]["samples"].append(
                code + " -> " + k["omschrijving"]
            )

print("Gedetailleerde prefixes:")
for p in sorted(prefixes.keys()):
    info = prefixes[p]
    print(f"  {p}: {info['count']} kluisjes")
    for s in info["samples"]:
        print(f"    voorbeeld: {s}")
