# Notitie: "1 overgeslagen" bij de kluisjes-import

**Datum:** 19 mei 2026
**Betreft:** Demo testimport (`Kluisjes Demo 180526.xlsx`)

## Samenvatting

Bij het importeren van de kluisjes verschijnt de melding:

> Import geslaagd (Magister Desktop): **2574 kluisjes aangemaakt, 2098
> toewijzingen, 1 overgeslagen (al bestaand)**.

De "1 overgeslagen" is **verwacht en correct gedrag** — er is geen kluisje
en geen leerling verloren gegaan. Hieronder de uitleg.

## Wat er aan de hand is

Het Excel-bestand bevat **2575 regels**, maar **2574 unieke kluisnummers**.
Eén kluisnummer komt twee keer voor:

| Kluis | Slot | Leerling | Stamnr | Periode |
|-------|------|----------|--------|---------|
| MO-1304 | 36224-718 | Luana Krasniqi | 17588 | 01-08-2023 t/m 01-08-2026 |
| MO-1304 | 36224-718 | Luana Krasniqi | 17588 | 23-01-2025 t/m 01-08-2029 |

Het gaat dus om **hetzelfde kluisje en dezelfde leerling**, alleen met
**twee verschillende huurperiodes**. Magister heeft beide periodes als
aparte regels in de export gezet (bijvoorbeeld een verlenging of een
nieuwe inschrijving op hetzelfde kluisje).

## Hoe de applicatie hiermee omgaat

Een kluisnummer moet uniek zijn binnen een vestiging. De import:

1. Maakt **MO-1304** één keer aan, gekoppeld aan **Luana Krasniqi**, met
   de **eerste** periode (01-08-2023 t/m 01-08-2026).
2. Slaat de tweede regel over → vandaar "1 overgeslagen".

Het kluisje en de leerling staan dus gewoon correct in het systeem.

## Aandachtspunt voor de definitieve cutover

Bij deze test is dit geen probleem. Punt van aandacht voor de échte
overgang van Magister naar de applicatie:

- MO-1304 krijgt nu de **oudste** periode (t/m 2026), niet de meest
  recente (t/m 2029).
- Wens dat bij dubbele regels juist de **meest recente** periode wordt
  overgenomen? Dat kan als kleine aanpassing worden ingebouwd. Alternatief:
  Magister een schonere export laten maken (één regel per kluisje).

Voor de testfase is geen actie nodig — de import werkt zoals bedoeld.
