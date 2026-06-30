# Voorinschrijving volgend schooljaar - instructie voor de Magister-beheerder

Met de functie **Voorinschrijving volgend schooljaar** kun je de leerlingen die voor het
**komende** schooljaar zijn geplaatst (bijvoorbeeld de nieuwe brugklassers) nu al in
Kluisjesbeheer zetten, zodat de concierges ze alvast aan een vrij kluisje kunnen koppelen.

Ze komen er **klasloos** in, met een markering "voorinschrijving <schooljaar>". Op 1 augustus,
zodra ze actief in Magister staan, neemt de dagelijkse sync hun echte klas automatisch over en
valt de markering weg. Tot 1 augustus worden deze leerlingen beschermd: de sync markeert ze niet
per ongeluk als "vertrokken".

Er zijn **twee manieren** om de leerlingen op te halen. Kies er een:

- **Optie A - Magister-opzoeklijst (Decibel).** Eenmalig instellen; daarna werkt de knop
  "Importeer via Magister" elk jaar. Aanbevolen als je met Decibel/DD-lijsten kunt werken.
- **Optie B - Excel-export.** Geen Decibel nodig. Je exporteert de leerlingen naar een
  `.xlsx`-bestand en uploadt dat. Handig als je geen opzoeklijst kunt of wilt aanmaken.

De bestaande Magister-koppeling (dagelijkse leerling-sync) blijft ongewijzigd. Deze functie is
een aanvulling daarop.

---

## Optie A - Magister-opzoeklijst (Decibel)

De gewone leerling-sync gebruikt `ADFuncties.GetActiveStudents`, en die geeft alleen de
**huidige** leerlingen. Voor de **volgend-jaars** leerlingen is een aparte opzoeklijst (een
Decibel DD-lijst) nodig die filtert op een toekomstige peildatum (1 augustus van het komende
schooljaar).

### Stappen

1. Open **Decibel** (de query-/DD-lijst-omgeving van Magister).
2. Maak een nieuwe DD-lijst met **exact** de naam:

   ```
   sql-get-kluisjes-voorinschrijving
   ```

   (De naam is in de app instelbaar via de instelling `voorinschrijving_lijst`; standaard is het
   bovenstaande. Houd het op de standaardnaam tenzij je een reden hebt om af te wijken.)

3. Plak de SQL uit het blok onderaan deze instructie (zie **Bijlage: SQL**). **Pas de peildatum
   aan:** vervang alle drie de `'2026-08-01'` door **1 augustus van het komende schooljaar**.
4. Test in Decibel (toets **F9**). Je hoort de volgend-jaars leerlingen te zien, met de kolommen
   `Leerlingnummer`, `Voornaam`, `Tussenvoegsel`, `Achternaam`, `Email`, `Locatie`, `Klas`.
5. Geef het **kluisjes-webservice-account** leesrecht op deze lijst/layout. Dat is hetzelfde
   account dat in de app onder **Beheer -> Import** als Magister-account is ingevuld (per school
   verschillend, bijvoorbeeld `webuser` of `Kluisjesmodule`). Zonder dit recht geeft de
   webservice foutcode **10**: "Gebruikersaccount heeft geen recht op deze layout".
6. Ga in de app naar **Beheer -> Import**, onderaan het paneel **Voorinschrijving volgend
   schooljaar**. Vul het schooljaar in (bijvoorbeeld `2026-2027`) en klik op **Importeer via
   Magister**.

> ℹ️ Het account heeft naast deze lijst nog steeds `Algemeen.Login` en
> `ADFuncties.GetActiveStudents` nodig voor de gewone dagelijkse sync. De opzoeklijst komt daar
> bovenop.

> ℹ️ De webservice loopt over poort 8800. Als de sync al werkt, is de IP-whitelist voor de
> kluisjes-server al geregeld en werkt deze knop ook. Zo niet, zie de IP-whitelist-stap in
> [HANDLEIDING.md, hoofdstuk 13](HANDLEIDING.md).

> 🔧 **Tip voor volgend jaar:** de peildatum staat nu hard in de SQL. Pas hem elk schooljaar aan
> (stap 3). Wie het netjes wil, kan de drie datums vervangen door de placeholder `#peildatum#`;
> de app stuurt namelijk al een `peildatum`-parameter mee. Dat is optioneel.

---

## Optie B - Excel-export (geen Decibel nodig)

1. Maak in Magister een selectie of overzicht van de leerlingen die voor het **komende**
   schooljaar zijn geplaatst (peildatum 1 augustus van dat schooljaar).
2. Exporteer die naar **Excel (`.xlsx`)** met minimaal deze kolommen in de **kopregel** (eerste
   rij):
   - **`Leerlingnummer`** (of `Stamnummer`) - verplicht
   - **`Naam`** - verplicht (de volledige naam in een kolom)
   - `Locatie` en `Email` mogen erbij, maar zijn optioneel.

   Hoofdletters in de kolomnamen maken niet uit.
3. Ga in de app naar **Beheer -> Import**, paneel **Voorinschrijving volgend schooljaar**. Vul het
   schooljaar in, kies via **Bestand kiezen** je `.xlsx`, en klik op **Importeer uit Excel**.

---

## Wat er daarna gebeurt (beide opties)

- De leerlingen komen **klasloos** binnen, met de markering "voorinschrijving <schooljaar>"
  (zichtbaar als een klein chipje, bijvoorbeeld `'26-'27`, in de zoekresultaten en op het kluisje).
- Concierges kunnen ze meteen aan vrije kluisjes koppelen.
- **Op 1 augustus** neemt de gewone dagelijkse sync hun echte klas over en verdwijnt de markering
  automatisch, zodra ze als actieve leerling in Magister verschijnen.
- **Tot 1 augustus** worden deze leerlingen beschermd: ze worden niet als "vertrokken" gemarkeerd,
  ook al staan ze nog niet in de lijst met actieve leerlingen.
- Je kunt de import meerdere keren draaien; bestaande voorinschrijvingen worden bijgewerkt, niet
  gedupliceerd.

---

## Bijlage: SQL (voor Optie A)

De canonieke versie staat in de repository onder
[`docs/decibel/sql-get-kluisjes-voorinschrijving.sql`](../decibel/sql-get-kluisjes-voorinschrijving.sql).
Vervang de drie peildatums (`'2026-08-01'`) door 1 augustus van het komende schooljaar.

```sql
SELECT DISTINCT
    sis_leer.stamnr       AS Leerlingnummer,
    sis_leer.roepnaam     AS Voornaam,
    sis_leer.tussenvoeg   AS Tussenvoegsel,
    sis_leer.achternaam   AS Achternaam,
    sis_leer.email        AS Email,
    sis_blok.omschr       AS Locatie,
    sis_bgrp.groep        AS Klas          -- alleen ter controle, NIET importeren in de app
FROM sis_leer sis_leer
    INNER JOIN sis_aanm sis_aanm ON sis_leer.stamnr    = sis_aanm.stamnr
    LEFT  JOIN sis_bgrp sis_bgrp ON sis_aanm.idBgrp    = sis_bgrp.idBgrp
    LEFT  JOIN sis_blok sis_blok ON sis_bgrp.c_lokatie = sis_blok.c_lokatie
WHERE
    -- Peildatum in het KOMENDE schooljaar (pas alle drie de datums aan):
    sis_aanm.dBegin    <= '2026-08-01'
    AND sis_aanm.dEinde    >= '2026-08-01'
    AND (sis_aanm.dVertrek >= '2026-08-01' OR sis_aanm.dVertrek IS NULL)
ORDER BY sis_leer.stamnr;
```

> De kolom `Klas` bevat de **nieuwe** klas van volgend jaar. Die wordt bewust **niet**
> geimporteerd (de leerling komt klasloos binnen); hij staat er alleen ter controle in. De echte
> klas komt op 1 augustus via de gewone sync.
