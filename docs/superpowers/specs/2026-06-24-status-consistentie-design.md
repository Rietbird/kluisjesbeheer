# Spec: Statusfilter + legenda consistent (twee assen)

- **Datum:** 2026-06-24
- **Status:** ontwerp (goedgekeurd door Vincent) — frontend-only

## Probleem

De statusfilter voelde inconsistent: te veel platte chips met onderling
verschillende kleuren, en filter ↔ legenda ↔ tegel gebruikten drie
vocabulaires (bv. filter "Borg" = geel, tegel = oranje/rood; "Sleutel"-chip
rood maar bevatte de grijze "Geen sleutel"; "Vertrokken" had geen legenda).
Oorzaak: twee soorten begrippen door elkaar — *wat een kluisje is* en
*vlaggen die erop kunnen liggen*.

## Ontwerp (twee assen, één taal)

**As 1 — Status** (precies één, bepaalt tegelkleur): Vrij (groen) · Uitgeleend
(blauw) · Defect (amber) · Geen sleutel (grijs). → platte chips.

**As 2 — Aandachtspunten** (vlaggen, kunnen stapelen): Borg openstaand 💰 ·
Sleutel niet ingeleverd 🔑 · Vertrokken ⚠ · Reservesleutel 🔑. → één
**dropdown** "Aandachtspunten ▾" (houdt de balk kort).

Filterbalk, legenda en tegels gebruiken dezelfde namen, kleuren en iconen.
Legenda staat in twee gelabelde rijen (Status / Aandachtspunten). Kleur is
nooit de enige indicator (icoon + tekst erbij — a11y).

## Implementatie (frontend-only)
- `Toolbar.jsx`: `statusOptions` = de 4 statussen; nieuwe `AandachtspuntenDropdown`
  (verving `SleutelDropdown`); visuele divider tussen de twee groepen.
- `LockerGrid.jsx`: legenda → twee gelabelde rijen.
- Backend ongewijzigd: alle filterwaarden (`vrij/uitgeleend/defect/geen_sleutel`
  + `borg/sleutel_niet_ingeleverd/vertrokken/reservesleutel`) bestonden al.
- Docs (HANDLEIDING.md + in-app Handleiding.jsx) bijgewerkt.

## Niet-doel
- Tegel-render-semantiek (een vrij-maar-geblokkeerd kluisje kleurt nog steeds
  rood als attentiesignaal) blijft zoals het was; de legenda legt dit uit.
  Strikt "tegelkleur = alleen status" kan een latere stap zijn.

## Verificatie
Frontend klik-getest: status-chips filteren, Aandachtspunten-dropdown toont 4
items mét iconen en filtert (o.a. Vertrokken), legenda toont beide groepen.
