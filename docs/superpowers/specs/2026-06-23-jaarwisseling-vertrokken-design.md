# Spec: Jaarwisseling — betrouwbare vertrokken-markering + uitstroom afhandelen

- **Datum:** 2026-06-23
- **Status:** ontwerp (goedgekeurd door Vincent)
- **Scope:** optie B — vlaggen betrouwbaar maken + makkelijke handmatige afhandeling. GEEN auto-vrijgave.

## Probleem

- De dagelijkse cron (`cron_sync.py`, 06:00 CT101) synct leerlingen maar markeert
  afwezige leerlingen **niet** als vertrokken. Alleen de handmatige knop
  (`POST /api/magister/sync-leerlingen` → `_sync_to_db`) doet dat.
- **Empirisch bevestigd op CT101 (2026-06-23):** 1619 leerlingen, 28 vertrokken —
  allemaal gemarkeerd op 19–20 mei (handmatige sync). Cron draaide vanochtend 06:00
  (`updated_at` = vandaag) maar markeerde 34 dagen lang **0** vertrokken. Er staan nu
  al **13** actieve kluisjes bezet door reeds-vertrokken leerlingen.
- Magister schakelt op **1-8-2026 in één klap** om (bevestigd door Vincent). Zonder fix
  wordt de uitstroomgolf niet gevlagd: leavers houden hun oude klas én bezetten hun kluisje.
- Documentatie ([HANDLEIDING.md:443](../../handleiding/HANDLEIDING.md)) beweert al
  onterecht dat de cron dit doet.

## Doel

1. Vertrokken-markering betrouwbaar in de dagelijkse cron (identiek aan de handmatige knop).
2. De gevlagde uitstroom makkelijk handmatig kunnen afhandelen.

## Niet-doel

- Automatisch kluisjes vrijgeven op 1-8 (sleutel nog niet terug → bewust niet).
- Pre-toewijzen volgend schooljaar (apart traject "C").
- De features "geen-sleutel-filter" (A) en "clusters verwijderen" (B-origineel) — die volgen hierna.

## Ontwerp

### Deel 1 — Gedeelde sync-functie (cron + handmatig identiek)

Nieuwe functie `sync_leerlingen_to_db(db, leerlingen)` in een gedeeld module
`backend/leerling_sync.py` (neemt een db-connectie als parameter — géén `flask.g`,
zodat de cron 'm óók kan gebruiken):

1. **Upsert** van alle aangeleverde leerlingen (klas/naam/etc., `vertrokken_op = NULL`).
2. **Markeer afwezigen als vertrokken:**
   `UPDATE leerlingen SET vertrokken_op = date('now') WHERE stamnr NOT IN (...) AND vertrokken_op IS NULL`.
   Regel: **één keer afwezig → vertrokken** (atomische Magister-omschakeling, bevestigd).
3. **Veiligheidsrem:** als de aangeleverde lijst < **50%** is van het huidige aantal
   niet-vertrokken leerlingen → sla stap 2 over en **log luid** (`print('WAARSCHUWING: ...')`).
   De upsert (stap 1) gaat wél door. Beschermt tegen een onbewaakte cron die op een halve
   API-respons honderden leerlingen wegzet. Cron is onbewaakt → de skip moet zichtbaar zijn
   in `/var/log/kluisjes-sync.log`.

Aanpassingen:
- `api_magister.py::_sync_to_db` → thin wrapper die `sync_leerlingen_to_db(g.db, leerlingen)`
  aanroept. Handmatige route (`POST /api/magister/sync-leerlingen`) gedraagt zich gelijk, krijgt nu óók de rem.
- `cron_sync.py` → vervangt z'n inline upsert (regels ~67–82) door `sync_leerlingen_to_db(db, leerlingen)`.
- `HANDLEIDING.md:443`-claim klopt daarna (geen tekstwijziging nodig, of licht aanscherpen).

### Deel 2 — Uitstroom afhandelen

**a) Overzicht-filter "Vertrokken"**
- `Toolbar.jsx` `statusOptions`: nieuwe optie `{ value: 'vertrokken', label: 'Vertrokken', dot: 'bg-red-500' }`.
- `api_kluisjes.py` `GET /api/kluisjes`: nieuwe tak `status == 'vertrokken'` →
  `AND t.actief = 1 AND l.vertrokken_op IS NOT NULL` (leerlingen wordt al gejoined; het
  veld `leerling_vertrokken_op` wordt al teruggegeven).
- Badge ⚠ bestaat al in `LockerGrid.getLabel` — geen visuele wijziging nodig.

**b) "Alleen vertrokken"-toggle in Collectief beëindigen (stap 1)**
- `api_toewijzingen.py` `GET /api/toewijzingen/actief`: **LEFT JOIN leerlingen** toevoegen +
  `l.vertrokken_op AS leerling_vertrokken_op` teruggeven (endpoint joint leerlingen nu níet).
- `BulkEndWizard.jsx` stap 0 (Selectie): extra checkbox **"Alleen vertrokken leerlingen"**,
  toegepast in de `filtered`-useMemo. Zo selecteer + beëindig je de hele uitstroom in één keer.
- **Beslissing:** als "alleen vertrokken" aan staat → default `sleutelMap = false`
  (sleutel níet ingeleverd; vertrokken leerlingen leveren niets meer in). Anders blijft de
  huidige default (true). Sluit aan op de "naloop"-tip in de handleiding.

## Datamodel

Geen schemawijziging. `vertrokken_op` bestaat al op `leerlingen`.

## Tests (`backend/tests`)

- Cron-pad: sync met één leerling minder → die wordt vertrokken, aanwezigen niet.
- Handmatige route: identiek gedrag (regressie — niet alleen de cron).
- Veiligheidsrem: lijst < 50% → geen markering, wél upsert, waarschuwing gelogd.
- Filter: `status=vertrokken` geeft alleen kluisjes met vertrokken huurder.
- `/api/toewijzingen/actief` geeft `leerling_vertrokken_op` terug.

## Deploy

1. Pre-deploy backup (Beheer → Onderhoud → "Nu backup maken").
2. **Eerst CT102 (test)** — controleer de eerste catch-up-golf: de cron markeert dan in
   één keer de uitstroom van de afgelopen 34 dagen. Verwacht en correct; de datums staan
   op deploy-dag (cosmetisch). Eyeball dat het aantal logisch is.
3. Daarna **CT101 (prod)** via de update-knop.

## Open / te bevestigen

- Niets blokkerends. De sleutel-default-beslissing (Deel 2b) graag even bevestigen.
