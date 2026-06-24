# Spec: "Geen sleutel" + sleutel-submenu

- **Datum:** 2026-06-24
- **Status:** ontwerp (goedgekeurd door Vincent)

## Probleem

Er zijn veel kluisjes waar geen sleutel (meer) van is. Die staan nu tussen de
vrije kluisjes terwijl je ze niet kunt uitlenen. Daarnaast is de losse
"Sleutel"-chip dubbelzinnig: hij betekent "niet ingeleverd", maar het woord
suggereert dat de sleutel er juist wél is.

## Doel

1. Een per-kluisje vlag `geen_sleutel` (handmatig), zoals `is_defect`.
2. Eén "Sleutel"-chip die uitklapt naar een submenu met alle sleutel-statussen.

## Ontwerp

### Datamodel
- Nieuwe kolom `kluisjes.geen_sleutel INTEGER NOT NULL DEFAULT 0` (migratie in `db.py`, idempotent).

### Backend (`api_kluisjes.py`)
- `PUT /api/kluisjes/<id>`: accepteert `geen_sleutel` (1/0), net als `is_defect`.
- Toewijzen blokkeren: `POST /api/kluisjes/<id>/toewijzen` (in `api_toewijzingen.py`)
  geeft 409 als `geen_sleutel = 1` ("Kluisje heeft geen sleutel — markeer eerst weer als sleutel aanwezig").
- Filter `status=` krijgt vier sleutel-waarden:
  - `sleutel` — **alle** sleutelkwesties: niet-ingeleverd OF `geen_sleutel=1` OF (actief + reservesleutel uitgegeven).
  - `sleutel_niet_ingeleverd` — bestaande "niet ingeleverd"-conditie.
  - `geen_sleutel` — `k.geen_sleutel = 1`.
  - `reservesleutel` — `t.actief = 1 AND t.reservesleutel_uitgegeven = 1`.
- Filter `vrij` sluit `geen_sleutel = 1` uit (de kern: weg uit "Vrij"). Bestaande
  niet-ingeleverd blijft ongewijzigd (alleen nu óók via sub-filter bereikbaar).

### Frontend
- `LockerGrid.getLabel`/`getColor`: badge + kleur voor `geen_sleutel` op een vrij
  kluisje (bv. rode achtergrond + tekst "🔑✗ Geen sleutel").
- `LockerModal`: knop "Geen sleutel" / "Sleutel weer aanwezig" naast de defect-knop
  (PUT `geen_sleutel`).
- `Toolbar`: de "Sleutel"-chip wordt een dropdown (patroon van `RapportDropdown`)
  met: Alle sleutelkwesties · Niet ingeleverd · Geen sleutel · Reservesleutel
  uitgegeven. Chip toont actief bij elk van die vier statuswaarden.

## Niet-doel
- Bulk-markeren van `geen_sleutel` (kan later; nu per kluisje via de modal).
- Niet-ingeleverd uit "Vrij" halen (blijft zoals het is).

## Tests
- PUT zet/haalt `geen_sleutel`; toewijzen aan `geen_sleutel`-kluisje → 409.
- Filters: `geen_sleutel`, `reservesleutel`, `sleutel_niet_ingeleverd`, `sleutel` (alle), en `vrij` sluit geen_sleutel uit.

## Deploy
Migratie draait bij startup. Eerst CT102, dan CT101.
