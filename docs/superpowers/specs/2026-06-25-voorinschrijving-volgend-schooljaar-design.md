# Spec: Voorinschrijving leerlingen volgend schooljaar

- **Datum:** 2026-06-25
- **Status:** ontwerp (goedgekeurd door Vincent; bron herzien na spike)
- **Scope:** leerlingen van het volgende schooljaar vooraf in de app zetten zodat ze nu al aan een vrij kluisje gekoppeld kunnen worden, zonder dat de dagelijkse sync ze als vertrokken markeert.
- **Aanleiding:** Hengelo wil brugklassers van 2026-27 vóór de zomer aan kluisjes koppelen. Voortzetting van het geparkeerde traject "volgend schooljaar".

## Probleem

Conciërges willen vrije kluisjes nu al toewijzen aan leerlingen die volgend schooljaar instromen. Dat kan op dit moment niet:

1. **De leerlingen staan nog niet in de app.** De gewone Magister-sync (`magister_client.get_leerlingen` → `GetActiveStudents`, [magister_client.py:184-205](../../../backend/magister_client.py#L184)) levert alleen de nú actieve leerlingen. Brugklassers verschijnen daar pas als Magister op 1-8 omschakelt.
2. **De kluisjes-XLSX-import lost dit niet op.** Die koppelt alleen leerlingen aan kluisjes die hij zélf nieuw aanmaakt; bestaande kluisnummers worden overgeslagen vóór de toewijzing wordt gemaakt ([api_kluisjes.py:844-878](../../../backend/api_kluisjes.py#L844)). Voor het koppelen aan reeds bestaande vrije kluisjes is dat onbruikbaar.
3. **De dagelijkse sync zou ze meteen wegzetten.** Een leerling die niet in `GetActiveStudents` zit, wordt door `sync_leerlingen_to_db` als vertrokken gemarkeerd ([leerling_sync.py:54-59](../../../backend/leerling_sync.py#L54)). Vooraf-geïmporteerde leerlingen zouden dus de eerstvolgende cron al sneuvelen.

## Bron-onderzoek (spike CT102, 2026-06-25)

Empirisch getest tegen Hengelo's live SWP-webservice:

- `GetActiveStudents` met een schooljaar-string (`"2026-2027"`, `"2026"`, óók huidig `"2025-2026"`) geeft **0** leerlingen; lege `LesPeriode` geeft de huidige 2166. De vaste `ADFuncties`-functies (`GetActiveStudents`/`GetLeerlingen`/`GetInactieveLeerlingen`) kunnen dus **geen** volgend-jaars leerlingen leveren.
- **Wél mogelijk via een custom Decibel-lijst.** De webservice heeft `GetData(SessionToken, Layout, Parameters)` - "Een in Magister gedefiniëerd overzicht ophalen". `Layout` = lijstnaam; `Parameters` = `naam=waarde;...` die `#naam#`-placeholders in de querydefinitie vervangen. Custom lijsten worden **per service-account** toegewezen (Decibel).
- **De app logt in als service-account `Kluisjesmodule`** (instelling `magister_user`). De bestaande lijsten `kluisjes-actueel`/`zoek-kluiscode` zijn aan een ander account (`webuser`) gekoppeld; vandaar dat een testaanroep `EMGeneralFailure` gaf. Dit is account-scoping, geen blokkade.

**Conclusie: bron = een custom Decibel-lijst, opgehaald via `GetData`, toegewezen aan de account `Kluisjesmodule`.** Excel-upload blijft als simpele achtervang/alternatief.

## Doel

1. Een beheerder haalt met een knop de volgend-jaars leerlingen op (stamnr + naam + locatie) en zet ze in de `leerlingen`-tabel.
2. Die leerlingen krijgen een vlag "voorinschrijving" zodat de sync ze **niet** als vertrokken markeert, maar ze wél normaal koppelbaar zijn.
3. Op 1-8 nemen ze automatisch hun echte klas over (en de vlag vervalt) zodra de gewone sync ze als actief ziet - inclusief de klas op een al gekoppeld kluisje.

## Niet-doel

- **Klas meeleveren bij de import.** Bewust niet: de nieuwe klas (bijv. "1A") botst met de huidige "1A" vol zittende leerlingen. We importeren klasloos; de klas komt op 1-8 via de gewone sync.
- **Automatisch koppelen.** De conciërge koppelt zelf via de bestaande toewijs-flow.
- **De Decibel-querydefinitie zelf.** Het schrijven van de lijst (welke velden, welk schooljaar-filter) is Vincents domein in Decibel. De spec legt alleen het contract vast (kolommen + parameters).
- **Reserveren op cluster/rij-niveau.** Ander, eerder geopperd traject.

## Ontwerp

### Deel 1 - Datamodel

Eén nullable kolom op `leerlingen` ([schema.sql:64-78](../../../backend/schema.sql#L64)):

```sql
nieuw_voor_schooljaar TEXT DEFAULT NULL   -- bijv. "2026-2027"; NULL = gewone leerling
```

Idempotente migratie via `ALTER TABLE ... ADD COLUMN` in `init_db`, in dezelfde stijl als de bestaande migraties ([db.py:127-167](../../../backend/db.py#L127)).

Bewust géén aparte tabel: de voorinschrijvingen moeten in dezelfde `leerlingen`-tabel staan, want dan vindt de bestaande toewijs-zoek ([api_magister.py:41-86](../../../backend/api_magister.py#L41)) ze meteen en zijn ze koppelbaar zonder verdere wijziging (hun `vertrokken_op` is `NULL`, dus ze vallen al binnen het `_vertrokken_filter`).

### Deel 2 - Ophalen + importeren (beheerder)

**Bron A - webservice (primair):**
- Nieuwe methode `magister_client.get_data(layout, parameters)` → roept `GetData` aan (library `ADFuncties`), parse de `Table`-rijen tot dicts op kolomnaam.
- Nieuwe methode `get_voorinschrijvingen(schooljaar)` → roept `get_data` aan met de geconfigureerde lijstnaam en `Parameters="schooljaar=<schooljaar>"`, mapt de kolommen naar `{stamnr, naam, locatie}`.
- **Contract met de Decibel-lijst** (Vincent maakt deze, toegewezen aan account `Kluisjesmodule`): output-kolommen voor stamnr, naam, locatie; filter op het komende schooljaar via een `#schooljaar#`- of `#peildatum#`-parameter. Lijstnaam + kolom-mapping configureerbaar in `instellingen` (bijv. `voorinschrijving_lijst`, default `voorinschrijving-volgend-jaar`).

**Bron B - Excel-upload (achtervang):** zelfde verwerking, maar gevoed door een geüpload XLSX met kolommen `Stamnummer`, `Naam`, `Locatie`. Hergebruik `_safe_load_xlsx` uit `api_kluisjes.py`.

**Route:** `POST /api/leerlingen/import-voorinschrijving` (`@beheerder_required`), in een klein nieuw `api_voorinschrijving.py`. Body: doel-schooljaar + bron (webservice of bestand).

**Verwerking - eigen functie, NIET `sync_leerlingen_to_db`:**
```sql
INSERT INTO leerlingen (stamnr, naam, locatie, klas, nieuw_voor_schooljaar, vertrokken_op, updated_at)
VALUES (?, ?, ?, '', ?, NULL, datetime('now'))
ON CONFLICT(stamnr) DO UPDATE SET
    naam=excluded.naam, locatie=excluded.locatie,
    nieuw_voor_schooljaar=excluded.nieuw_voor_schooljaar,
    vertrokken_op=NULL, updated_at=datetime('now')
```
- **Géén vertrokken-markering** (dat is precies wat we willen vermijden).
- Klas blijft leeg (`''`); locatie wél (nodig voor de vestiging-scoping in de zoek).

Retourneert `{ geimporteerd, schooljaar, bron }`.

### Deel 3 - Sync-aanpassing (`leerling_sync.py`)

Twee kleine ingrepen in `sync_leerlingen_to_db`:

**a) Vertrokken-bescherming.** De vertrokken-`UPDATE` ([leerling_sync.py:54-59](../../../backend/leerling_sync.py#L54)) slaat een beschermde voorinschrijving over: niet markeren zolang de vlag gezet is én we vóór 1-8 van dat schooljaar zitten.
```sql
... AND NOT (
    nieuw_voor_schooljaar IS NOT NULL
    AND date('now') < (substr(nieuw_voor_schooljaar, 1, 4) || '-08-01')
)
```

**b) Activatie op 1-8 (vlag weg + klas + snapshot).** In de upsert-lus: als een binnenkomende (actieve) leerling een gezette `nieuw_voor_schooljaar` had, dan:
- `nieuw_voor_schooljaar = NULL` (via de bestaande upsert die we uitbreiden met dit veld in de `ON CONFLICT ... SET`), en
- werk de **klas op de actieve toewijzing** bij naar de nu binnengekomen klas:
  ```sql
  UPDATE toewijzingen SET leerling_klas = ?, updated_at = datetime('now')
  WHERE leerling_stamnr = ? AND actief = 1
  ```
  Alleen voor leerlingen die een voorinschrijving wáren - gewone leerlingen houden hun snapshot zoals nu (audit-gedrag ongewijzigd).

> **NB (ontdekt 2026-06-25 tijdens de trifecta):** `GET /api/kluisjes` toont de klas al via `COALESCE(NULLIF(TRIM(t.leerling_klas),''), l.klas)` (klas-fix 16-17 juni). Voor een klasloze voorinschrijving verschijnt de live klas daar dus ná 1-8 al vanzelf. `GET /api/toewijzingen/actief` ([api_toewijzingen.py:287-294](../../../backend/api_toewijzingen.py#L287)) gebruikt echter nog de rauwe `t.leerling_klas`. **Overweeg Deel 3b te vervangen door dezelfde COALESCE ook in `actieve_toewijzingen`** - eenvoudiger en consistent dan een snapshot-update. Eerst verifiëren welke weergave de conciërge daadwerkelijk gebruikt.

### Deel 4 - No-show (optie 1)

Een voorinschrijving die zich uiteindelijk niet inschrijft, verschijnt ook ná 1-8 niet in `GetActiveStudents`. De bescherming uit Deel 3a vervalt vanzelf zodra `date('now') >= 1-8` van het doel-schooljaar, dus de eerstvolgende sync markeert de no-show alsnog als vertrokken. Die valt dan op via het bestaande "vertrokken mét actief kluisje"-signaal (jaarwisseling-spec). Geen extra code nodig.

### Deel 5 - UI

- **Import-knop** in Beheer → Onderhoud, naast "Synchroniseer leerlingen": kies doel-schooljaar + bron (webservice / bestand), toont `{geimporteerd}` als resultaat.
- **Badge** `'26-'27` (chip met tooltip "voorinschrijving volgend schooljaar") in de leerling-zoekresultaten en op het kluisje, voor leerlingen met `nieuw_voor_schooljaar` gezet. De zoek- en toewijzing-endpoints geven het veld al mee zodra de kolom bestaat (`SELECT *` / `t.*`); de frontend rendert de chip conditioneel (let op int/string-bool valkuil → expliciete check).

## Data flow

```
juni 2026   beheerder klikt "Importeer voorinschrijvingen 2026-2027"
            -> app: GetData(token, "voorinschrijving-volgend-jaar", "schooljaar=2026-2027")
            -> leerlingen-rij: nieuw_voor_schooljaar="2026-2027", klas="", locatie gezet
            conciërge koppelt leerling aan vrij kluisje -> toewijzing.leerling_klas = "" (snapshot)

juni-juli   dagelijkse cron draait GetActiveStudents (huidig jaar)
            -> voorinschrijving NIET in lijst, maar beschermd (vlag + vóór 1-8) -> blijft staan

1-8-2026    Magister schakelt om; GetActiveStudents bevat nu de brugklasser als actief, klas "1A"
            -> sync upsert: klas="1A", vlag weg, EN actieve toewijzing.leerling_klas := "1A"
            -> kluisje toont de juiste klas

no-show     leerling schreef zich niet in -> ná 1-8 niet meer beschermd
            -> eerstvolgende sync markeert vertrokken -> valt op via bestaand signaal
```

## Edge cases

- **Doorstromer per ongeluk in de lijst.** Een al-actieve leerling die ook in de Decibel-lijst zit, krijgt de vlag, maar de eerstvolgende cron ziet 'm als actief → vlag valt direct weg. Onschadelijk.
- **Locatie-naamgeving.** De locatie uit de lijst moet overeenkomen met de bestaande `vestigingen_locaties`-mapping, anders ziet een vestiging-gebonden conciërge de voorinschrijving niet. Beheerder controleert; beheerder zonder vestiging-scope vindt ze hoe dan ook.
- **Dubbele import.** Idempotent via `ON CONFLICT(stamnr)`; opnieuw ophalen werkt veilig bij.
- **Klas verandert tussen juni en september.** De snapshot wordt pas op activatie (1-8) gezet vanuit de dan-actieve klas, dus dat klopt vanzelf.
- **Lijst niet toegewezen / leeg.** `GetData` geeft `EMGeneralFailure` of 0 rijen → route geeft nette foutmelding ("lijst niet bereikbaar voor account Kluisjesmodule of leeg"), géén leerlingen weggezet.

## Tests

Uitbreiding van [test_leerling_sync.py](../../../backend/tests/test_leerling_sync.py) + een nieuwe `test_voorinschrijving.py`:

1. Import zet `nieuw_voor_schooljaar` + locatie, klas leeg, géén vertrokken-markering (bron gemockt).
2. Beschermde voorinschrijving overleeft een gewone sync vóór 1-8 (niet vertrokken-gemarkeerd).
3. Op/na 1-8: voorinschrijving die actief binnenkomt → vlag weg, klas gezet, en de actieve toewijzing krijgt de nieuwe klas op de snapshot.
4. No-show ná 1-8 → wél vertrokken-gemarkeerd.
5. Koppelen aan een vrij kluisje werkt en de voorinschrijving is vindbaar in de zoek (ook vestiging-gescoped via locatie).
6. `get_data`-parser: TTable-XML → lijst van dicts op kolomnaam (sample-respons als fixture).

## Open punten / afhankelijkheden (Vincent, in Decibel)

1. **Decibel-lijst maken** die de volgend-jaars leerlingen teruggeeft (kolommen stamnr/naam/locatie, filter op komend schooljaar via `#schooljaar#` of `#peildatum#`).
2. **Lijst toewijzen aan account `Kluisjesmodule`** (niet webuser).
3. Daarna **end-to-end test** van `GetData` tegen die lijst (nu nog niet bewezen omdat er geen lijst op Kluisjesmodule stond).
