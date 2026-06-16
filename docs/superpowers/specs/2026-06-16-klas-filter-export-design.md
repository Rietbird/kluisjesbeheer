# Spec: Klas-filter in overzicht + per-klas PDF-export

**Datum:** 2026-06-16
**Status:** Goedgekeurd (Vincent, 2026-06-16)

## Doel

Het MCT wil kluisjes per klas kunnen bekijken en per klas een overzicht uitdraaien.
Dat kan nu niet: de toolbar filtert op vestiging/cluster/status/vrije tekst (niet op
klas), en de rapporten hebben geen klas-filter of per-klas variant.

## Achtergrond

- De "Klas" in het detailpaneel/overzicht komt sinds commit `57fbcb3` via
  `COALESCE(NULLIF(TRIM(t.leerling_klas),''), l.klas)` — de live Magister-klas uit de
  `leerlingen`-tabel als de toewijzing-snapshot leeg is. Dezelfde logica gebruiken we
  hier overal.
- De `leerlingen`-tabel wordt gevuld door de Magister-leerling-sync (`cron_sync.py` /
  knop "Leerlingen ophalen"). XLSX-import vult die tabel NIET.

## Scope

### A. Klas-filter in het overzicht (scherm)
- Dropdown "Alle klassen" + klassen, in `Toolbar.jsx` naast cluster/status.
- Klassenlijst = klassen die in de geselecteerde vestiging een **huidige huurder**
  hebben (afgeleid uit de actieve toewijzingen via de COALESCE-klas), alfabetisch
  gesorteerd, geen lege waarde.
- Nieuw endpoint (of uitbreiding) levert die klassenlijst per vestiging.
- `GET /api/kluisjes` krijgt een optionele `klas`-param en filtert op
  `COALESCE(NULLIF(TRIM(t.leerling_klas),''), l.klas) = :klas`.
- Filter-state `klas` toevoegen in `useKluisjes.jsx` (meesturen in de query).

### B. Per-klas PDF-export
- Nieuw blok "Per klas" in de Rapport-dropdown (`Toolbar.jsx`):
  - **"Huidige klas (X)"** — alleen actief als er een klas-filter staat; exporteert die ene klas.
  - **"Alle klassen"** — één PDF, per klas een sectie.
- Elke klas-sectie bevat twee lijstjes:
  1. **Mét kluisje** — leerling · kluisnr · sleutelnr · periode (actieve toewijzingen in die klas).
  2. **Zonder kluisje** — leerlingen in die klas (vestiging-gescoped) zonder actieve toewijzing.
- Backend: nieuw rapport-type `klas` op `GET /api/dashboard/rapport` (+ `/preview`) met
  optionele `klas=`-param. Zonder `klas` = alle klassen. PDF via de bestaande
  reportlab-infra (`_register_font`, bestaande PDF-opbouw hergebruiken).
- "Mét kluisje" gebruikt de COALESCE-klas; "zonder kluisje" filtert `leerlingen.klas`
  + vestiging via `vestigingen_locaties` (zoals het bestaande `zonder_kluisje`-rapport).

### C. Meegenomen verbetering
- De bestaande rapporten die `t.leerling_klas` tonen/sorteren (`toewijzingen`/`inname`,
  `sleutels`, `borg`) overzetten op de COALESCE-klas, zodat hun klas-kolom en -sortering
  ook kloppen waar de snapshot leeg is.

## Buiten scope
- Excel/CSV-export (mogelijk later).
- Aparte "Klassen"-pagina/tab (de toolbar + Rapport-knop volstaan).

## Caveat
"Zonder kluisje" en de volledigheid van de klassenlijst leunen op de `leerlingen`-tabel
(de Magister-sync). Waar de sync draait → compleet; waar alleen XLSX-import is gebruikt →
toont alleen wat bekend is. Geen blokker, wel gedocumenteerd gedrag.

## Tests
- Backend: `klas`-param op `/api/kluisjes` filtert correct (incl. COALESCE-fallback);
  rapport-type `klas` levert juiste rijen voor één klas en voor alle klassen, inclusief
  de "zonder kluisje"-lijst. Bestaande suite blijft groen (`pytest`).
- Handmatig: klas-dropdown vult zich per vestiging; PDF "huidige klas" + "alle klassen"
  ogen goed.

## Bestanden (verwacht)
- Frontend: `Toolbar.jsx` (klas-dropdown + Rapport-blok), `useKluisjes.jsx` (klas-state),
  evt. `Uitleenoverzicht.jsx`.
- Backend: `api_kluisjes.py` (`klas`-param + klassenlijst-endpoint),
  `api_dashboard.py` (rapport-type `klas` + COALESCE op bestaande rapporten).
