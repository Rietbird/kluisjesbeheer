# Demo Kluisjesbeheer — OSG Demo

**Datum:** maandag, ±45 min
**Publiek:** conciërges + hoofd ICT OSG Demo
**Spreker:** Vincent (ICT School / Almelo)
**Toon:** collegiaal, "wij hebben dit gebouwd voor onszelf, jullie kunnen mee"
**Demo-omgeving:** CT102 — `https://10.20.0.16` (self-signed cert, je moet bij "Geavanceerd → toch doorgaan")
**Data:** echte OSG Demo-import — Bataafs Lyceum (969 kluisjes) + Montessori College (1605 kluisjes)

---

## Voorbereiding (15 min voor je start)

- [ ] Beamer/scherm aansluiten, op 1440×900 of hoger
- [ ] Browser openen, ga naar `https://10.20.0.16`, klik door de cert-waarschuwing, log in
- [ ] **Open een tweede tab** naar `https://kluisjes.school.nl` (achterhand: als CT102 tijdens demo wegvalt kun je live School-data laten zien)
- [ ] Telefoon op stil
- [ ] Demo-import-bestand bij de hand: `c:\Projects\kluisjesbeheer\Kluisjes ISK - import.xlsx` (alleen voor het tonen van het uploadscherm — niet daadwerkelijk importeren in CT102!)
- [ ] Slide-deck `PRESENTATIE.html` open op een tweede tab voor de zaal
- [ ] Watertje 💧

> **Backup-plan als de demo vastloopt:** schakel naar productie-tab (School-data). Je verhaal werkt dan nog steeds, alleen ziet de zaal echte data van een andere school.

---

## Opening (3 min) — "Waarom dit bestaat"

**Hardop:**

> "Wat jullie zo gaan zien hebben we vorig jaar bij School gebouwd toen Magister hun kluismodule duurder maakte. Geen ingewikkeld verhaal — gewoon een webapp die doet wat een conciërge nodig heeft: kluisjes uitdelen, sleutels terug innemen, weten welk kluisje stuk is. Het draait nu een jaar zonder gedoe, en omdat we binnen één SLB-organisatie zitten kan Demo dit gewoon mee gaan gebruiken."

**Talking points:**

- Het draait nu een jaar in productie op School (~3385 kluisjes, ~680 actieve toewijzingen)
- Multi-school: dezelfde codebase, andere database, eigen branding (logo + kleur)
- Login met Microsoft-account (Entra) — geen extra wachtwoord onthouden
- Leerlinggegevens komen elke nacht uit Magister — je hoeft nooit handmatig namen of klassen bij te werken

**Open de browser nu** → `https://10.20.0.16` → toon **landingspagina**.

> "Dit is wat jullie zouden zien als jullie inloggen. Bovenaan jullie eigen logo, en de twee vestigingen die jullie hebben — Bataafs Lyceum en Montessori. Bezettingsgraad meteen zichtbaar: 79% en 84% in gebruik. Geen defecten, geen openstaande sleutels — schoon."

**Verwacht een vraag:** *"Waar komen die getallen vandaan?"*
**Antwoord:** "Uit jullie eigen kluis-spreadsheet die jullie ooit hebben aangeleverd. Die hebben we eenmalig geïmporteerd. Vanaf dat moment beheert het systeem alles zelf."

---

## DEMO Deel 1 — Dagelijks gebruik (15 min)

### 1a. Het overzicht

**Klik:** Bataafs Lyceum.

> "Dit is het hart. Elk vakje is één kluisje. Blauw = uitgeleend, je ziet meteen wie er huurt. Groen = vrij. Geel = defect. Rood randje zou betekenen 'sleutel niet ingeleverd', maar dat hebben jullie nog niet."

**Loop door de filterbalk:**

> "Bovenin kun je filteren op cluster — als jullie kluisjes verdeeld zijn over verschillende vleugels of verdiepingen — én zoeken. Probeer 's een naam te zoeken."

**Klik in zoekveld** → typ bv. `Anna` of een willekeurige veelvoorkomende naam → toon hoe de grid filtert.

> "Of een stamnummer, of een kluisnummer — alles wat je intypt zoekt 'ie meteen. Handig als een leerling bij je staat en zegt 'mijn sleutel is kwijt' en jij wilt weten welk kluisje van wie is."

**Klik door de status-chips:** Alles → Vrij → Uitgeleend → Defect → Sleutel.

> "Met die chips trek je een sectie eruit. Als de conciërge wil weten 'welke kluisjes staan leeg', één klik. 'Welke zijn nooit teruggebracht', één klik."

**Toggle naar tabel-weergave** (icoontje rechts naast de chips).

> "En als je liever een lijst hebt: hier is dezelfde data als tabel. Sorteerbaar op alle kolommen. Handig om door te scrollen of te exporteren."

**Verwacht:** *"Kunnen we dit uitprinten?"*
**Antwoord:** "Ja — rechtsboven de Rapport-knop maakt er een PDF van. En het rapport respecteert je filter, dus 'alle openstaande sleutels op het Bataafs' is drie klikken."

### 1b. Een leerling helpen

**Schakel terug naar grid.** Klik op een willekeurig blauw (uitgeleend) kluisje.

> "Stel een leerling komt aan de balie. Je klikt op zijn kluisje. Hier zie je alles: sleutelnummer, huidige huurder, klas, huurperiode. Eronder z'n geschiedenis, en eventuele opmerkingen die jij als conciërge erbij hebt gezet."

**Wijs het op:**

- Sleutelnummer (vaak iets anders dan kluisnummer — fysiek genummerd)
- Huurder + klas + stamnummer + periode
- Reservesleutel-checkbox (komen we zo op)
- Opmerkingen — vrije tekst, slaat zichzelf op
- Geschiedenis — wie zat hier eerder

> "Twee knoppen onderin. 'Huur beëindigen' voor als de leerling de sleutel inlevert. 'Markeer als defect' voor als het slot stuk is."

### 1c. Huur beëindigen

**Klik:** Huur beëindigen.

> "Standaard scenario: leerling brengt z'n sleutel terug. Je vinkt 'Sleutel ingeleverd' aan, einddatum is vandaag, klaar. Klik Bevestigen."

**⚠️ Klik op Annuleren** — niet daadwerkelijk beëindigen want we werken in CT102 met echte koppelingen.

> "Wat ik niet daadwerkelijk ga doen want dit is jullie testomgeving, maar je begrijpt het idee. Wat je hier óók ziet: als een leerling z'n sleutel kwijt is laat je dit vinkje uit. Het kluisje gaat dan wel 'vrij' staan voor een volgende huurder, maar je houdt zichtbaar dat hier nog iets openstaat — komt terug in de Sleutel-filter."

**Mogelijke vraag:** *"En als we borg vragen? Waar leg ik vast dat hij €5 heeft betaald?"*
**Antwoord:** "In het opmerkingen-veld. Geen los borg-bedrag-veld omdat scholen er heel verschillend mee omgaan. Schrijf erbij wat je wilt onthouden — bij teruggave zie je het meteen weer."

### 1d. Een kluisje toewijzen

**Sluit modal, klik op een groen (vrij) kluisje.**

> "Andere kant: leerling komt en wil een kluisje. Klik vrij kluisje, klik Toewijzen."

**Klik:** Toewijzen.

> "Type een paar letters van z'n naam — kan ook stamnummer."

**Type:** `Anna` (of een naam waarvan je weet dat 'ie veel voorkomt).

> "Suggesties verschijnen meteen met klas erachter. Klik, datums staan goed, klik Toewijzen — klaar. Twee seconden werk."

**⚠️ Klik Annuleren** — niet daadwerkelijk toewijzen.

**Mogelijke vragen:**

- *"Wat als die leerling al een kluisje heeft?"* → "Krijg je een waarschuwing. Eén kluisje per leerling regel."
- *"Wat als de leerling niet in de lijst staat?"* → "Dan staat 'ie ook niet in Magister. Magister is leidend. Eerst daar aanmaken, dan synct het 's nachts."
- *"En een externe — bv. een gastouder of stagiair?"* → "Dat ondersteunt 't systeem nu niet — het gaat uit van Magister-leerlingen. Als jullie dat veel hebben moeten we even kijken."

### 1e. Defect melden

**Klik op een willekeurig kluisje (vrij of uitgeleend).**

> "Slot stuk. Klik 'Markeer als defect'. Het kluisje wordt geel. Belangrijk: in onze versie blijft de huurder gewoon zitten — een defect kluisje kan tegelijk uitgeleend zijn, want het kan zijn dat het slot vastloopt terwijl er nog spullen in zitten. De conciërge weet meteen 'hier moet ik aan de slag' zonder dat de huurder verdwijnt."

**⚠️ Niet daadwerkelijk klikken.** Of wel — defect is een toggle, je kunt 'm meteen weer ongedaan maken. Aan jou.

> "Defect opheffen doe je door nogmaals op die knop te klikken. Toggle."

### 1f. Reservesleutel

**Klik op een uitgeleend kluisje** → wijs de checkbox aan.

> "Conciërge-feature: als jullie reservesleutels uitgeven kun je dat hier vastleggen. Vink aan, datum erbij, klaar. Op het overzicht zie je dan een sleutel-icoon op het kluisje — in één oogopslag weet je 'hier heb ik al een tweede sleutel uitgegeven'. Komt vooral van pas als die reserve ook weer terug moet."

**Mogelijke vraag:** *"En het bedrag dat we vragen voor een reservesleutel?"* → "Idem aan borg: in opmerkingen."

### Korte pauze voor vragen (3 min)

> "Even pauze. Dit was het dagelijkse werk — kluisje openen, toewijzen, beëindigen, defect, reserve. Vragen tot nu toe?"

---

## DEMO Deel 2 — Bulk-acties (10 min)

### 2a. Collectief toekennen (start schooljaar)

**Klik rechtsboven:** Collectief toekennen.

> "Het tweede grote gebruiksmoment: begin schooljaar. Een hele brugklas krijgt kluisjes. Niemand wil 30 keer dezelfde modal openen. Daarom een wizard."

**Stap 1 — Klas:**

> "Kies de klas. Lijst komt uit Magister."

**Kies een klas** (bv. `H2A` of welke er bij Demo is).

> "Volgende."

**Stap 2 — Leerlingen:**

> "Standaard staat iedereen aangevinkt. Vink uit wie geen kluisje krijgt — bijvoorbeeld omdat ze er al één hebben."

**Stap 3 — Periode & Kluisjes:**

> "Datums: start vandaag, einde schooljaar. Vestiging spreekt voor zich. En dan kies je een cluster waaruit het systeem vrije kluisjes mag pakken — als je een hele rij in de buurt van een klaslokaal wilt gebruiken bijvoorbeeld."

**Kies een cluster.**

**Stap 4 — Toekenning:**

> "Het systeem stelt nu zelf een koppeling voor: leerling X krijgt kluisje Y. Je kunt handmatig swappen voor je doorgaat — soms vraagt een leerling 'kan ik dat ene kluisje krijgen waar mijn zusje vorig jaar in zat', dat soort dingen."

**Stap 5 — Bevestigen:**

> "Hier is de last chance. Lijst van alles wat 'ie gaat doen. Een klik op Bevestigen en alles staat erin."

**⚠️ Klik Annuleren** in plaats van bevestigen.

> "Voor jullie testomgeving doe ik 'm niet door. Maar voor een brugklas van 28 leerlingen is dit drie minuten werk in plaats van een hele middag."

### 2b. Collectief beëindigen (einde schooljaar)

**Sluit wizard, klik:** Collectief beëindigen.

> "Andere kant van het jaar. Eind juli wil je niet 600 kluisjes handmatig vrijgeven. Dezelfde aanpak."

**Wijs op de filters:**

> "Hier zie je álle actieve toewijzingen. Je kunt filteren op cluster, op klas. Vink aan wie je wilt beëindigen — of klik 'Alles selecteren' voor de hele lijst."

> "Stap 2: einddatum, en een belangrijke vraag — 'sleutels standaard als ingeleverd markeren'. Als jullie een inleverdag plannen waarop alle leerlingen tegelijk komen kun je dat aanvinken. Wie z'n sleutel níét inlevert handel je individueel af. Of, andere strategie: bulk-beëindigen met sleutels níét op ingeleverd, en daarna stuk voor stuk afhandelen. Aan jullie."

> "Stap 3 bevestigt en je bent klaar."

**⚠️ Niet daadwerkelijk uitvoeren.** Klik Annuleren.

**Mogelijke vraag:** *"En wat als ergens halverwege de internetverbinding wegvalt?"*
**Antwoord:** "Eerlijk: de bulk-acties zijn niet 100% atomair. In de praktijk hebben we het nog nooit zien misgaan, maar bij twijfel check je in het Sleutel-filter wat er nog open staat."

### Korte pauze voor vragen (2 min)

---

## DEMO Deel 3 — Beheer & uitrol (10 min)

### 3a. Beheer-paneel

**Klik rechtsboven:** Beheer.

> "Voor de hoofd-ICT'er en de beheerder onder jullie: hier zit de inrichting van het systeem. Vier tabs."

### 3b. Vestigingen / clusters

**Tab:** Vestigingen.

> "Drie kolommen: vestigingen, clusters per vestiging, kluisjes per cluster. Klik vestiging — middenkolom toont z'n clusters. Klik cluster — rechts zie je z'n kluisjes."

> "Hier voeg je vestigingen toe of hernoem je ze, idem voor clusters. Verwijderen is een 'soft delete' — kluisjes verdwijnen van het scherm maar de geschiedenis blijft."

> "Belangrijk onderaan: locatie-koppeling. Magister levert leerlingen mee mét een locatie. Hier vertel je het systeem: 'de Magister-locatie Bataafs Lyceum hoort bij onze vestiging Bataafs'. Daardoor weet de zoekfunctie welke leerlingen op welke vestiging zitten."

### 3c. Gebruikers

**Tab:** Gebruikers.

> "Wie heeft toegang tot Kluisjesbeheer en in welke rol. Twee rollen: beheerder en medewerker. Beheerders zien alles, medewerkers alleen vestigingen die jullie aan ze koppelen."

> "Toevoegen is een e-mailadres invoeren. Die persoon moet óók in de Entra-groep zitten die toegang heeft — anders blokkeert Microsoft 'm voordat 'ie hier komt."

### 3d. Instellingen / branding

**Tab:** Instellingen.

> "Hier zit jullie eigen kleur, logo, schoolnaam. Bij jullie staat er nu nog School-default in — bij uitrol kunnen we dit zo aanpassen naar OSG Demo's kleur en logo."

> "Ook standaard huurperiode (datum t/m datum) — handig om de default 'einde schooljaar' goed te zetten."

### 3e. Import

**Tab:** Import.

> "En dan de import-tab. Dit ga ik **niet** doorlopen tot het einde — jullie data staat er al — maar ik laat zien hoe het ging."

**Klik:** Bestand kiezen → kies `Kluisjes ISK - import.xlsx` (of welk demo-bestand je ook hebt).

> "Stap één: upload een xlsx. Het systeem scant 'm: welke prefixen kom ik tegen (O, Z, ISK...), welke locaties, welke clusters."

**Toon preview-resultaat.**

> "Stap twee: je vertelt het systeem welke prefix bij welke vestiging hoort. Bij jullie was dat BL voor Bataafs en MO voor Montessori. Volgende klik = importeren. ±30 seconden voor 2500 kluisjes, inclusief leerling-koppeling als de stamnummers in Magister staan."

**⚠️ Klik niet op 'Importeren' — je krijgt duplicate-errors.**

> "Dit is dus letterlijk hoe jullie hier zijn gekomen. Eén xlsx, één keer doorlopen, klaar."

**Mogelijke vraag:** *"En als we een fout maken in de mapping?"*
**Antwoord:** "Hele import wordt teruggedraaid bij een duplicaat. Je krijgt een melding en kunt 'm opnieuw doen na correctie."

---

## Onder de motorkap (3 min) — kort, alleen als ze het willen weten

> "Heel kort voor de techneuten — wat draait er onder?"

- **Backend:** Python (Flask) op een Linux-container in onze Proxmox
- **Frontend:** React + Tailwind, single-page app
- **Database:** SQLite — klein, robuust, makkelijk te backuppen
- **Login:** Microsoft Entra (Azure AD) via OAuth, geen wachtwoorden in onze database
- **Magister:** elke nacht een sync via hun SOAP-webservice — leerlingen, klassen, locaties
- **Backups:** drie lagen — in-app dagelijks, Proxmox-host dagelijks naar Synology, en wekelijks een full snapshot. Hebben we ingericht na een incident vorig jaar waar we 5 dagen data kwijt waren door een onhandige deploy.
- **PDF-rapporten:** server-side gerenderd

**Mogelijke vragen:**

- *"Open source?"* → "Code staat lokaal in een git-repo bij mij. Niet publiek, maar binnen onze organisatie deelbaar."
- *"Wie onderhoudt het?"* → "Ik, op dit moment. Komt een patch uit Magister-kant, of een security-update, dan rol ik die uit op beide containers."

---

## Hoe verder als jullie het willen (5 min)

> "Stel jullie zien dit zitten. Wat hebben we nodig?"

**Drie dingen aan jullie kant:**

1. **Microsoft / Entra:**
   - Een app-registratie in jullie Entra-tenant
   - Een toegangsgroep waar de gebruikers in komen
   - 10 min werk voor jullie hoofd-ICT, of voor mij als jullie mij toegang geven
2. **Magister:**
   - Een service-account met leestoegang op `ADFuncties` (de webservice)
   - De URL van jullie Medius-instantie
3. **Subdomein:**
   - Bv. `kluisjes.osg-Demo.nl` of `kluisjes.bataafs.nl` — wat jullie willen
   - Wijst dan naar de container die ik klaarzet

**Drie dingen aan mijn kant:**

1. Nieuwe container opzetten met productie-config
2. Logo + kleur instellen
3. Eerste keer xlsx-import en daarna dagelijkse Magister-sync inrichten

> "Bij elkaar een dag werk. Daarna draait het. Inhoudelijke vragen tussendoor kunnen jullie altijd bij mij terecht — we zitten in dezelfde organisatie."

---

## Q&A (open eind)

### Veelgestelde vragen die je waarschijnlijk gaat krijgen

| Vraag | Antwoord |
|---|---|
| *"Kan een leerling z'n eigen kluisje online zien?"* | "Nee, bewust niet — alleen voor conciërges en beheer. Houdt het simpel en geen extra account-beheer voor leerlingen." |
| *"Kunnen we exports/rapporten mailen?"* | "Nu nog niet automatisch — wel download als PDF. Als jullie dat veel willen kan ik dat maken." |
| *"Wat als jouw container omvalt?"* | "Daarom de drie backup-lagen. Worst case: ik draai een container van vannacht terug, vijf minuten. We hebben nu een jaar uptime zonder noemenswaardig incident." |
| *"En de AVG / privacy?"* | "Leerlinggegevens staan op een server in onze eigen Proxmox in Almelo, in jullie geval kan dat op jullie eigen infra of bij ons. Geen externe cloud, geen Amerikaanse provider. Magister blijft de bron — wij houden alleen een sync-kopie van wat we nodig hebben." |
| *"Wat kost het?"* | "Daar gaan we het binnen de SLB nog over hebben. Vandaag gaat het over of het past." |
| *"Wat als jij weggaat?"* | "Code staat in git, alles is gedocumenteerd, een Python-developer kan het overnemen. Maar dat is wel een terechte vraag — we kunnen kijken naar een tweede beheerder." |
| *"Komt er nog functionaliteit bij?"* | "Op wensenlijst staan o.a.: zelf-bedienings-portal voor leerlingen, e-mailnotificaties bij sleutel-niet-ingeleverd, en QR-codes op kluisjes voor snel scannen. Niets dringend, kan op verzoek." |
| *"Kan ik even iets uitproberen?"* | "Ja, kom maar naar voren. Ik blijf bij de laptop." |

### Als je het wilt afsluiten

> "Dat was 'm. Ik laat de browser open staan — als jullie zelf nog wat willen klikken, of als er nog vragen zijn — kom maar."

---

## Tijdsindeling cheat-sheet

| Onderdeel | Tijd | Cumulatief |
|---|---|---|
| Opening + landingspagina | 3 min | 3 |
| Demo 1: dagelijks gebruik | 15 min | 18 |
| Pauze voor vragen | 3 min | 21 |
| Demo 2: bulk-acties | 10 min | 31 |
| Pauze voor vragen | 2 min | 33 |
| Demo 3: beheer + import | 10 min | 43 |
| Onder de motorkap | 3 min | 46 |
| Hoe verder | 5 min | 51 |
| **Totaal exclusief Q&A** | | **~50 min** |

Bij Q&A erbij makkelijk 60-75 min. Pas tempo aan op signalen uit de zaal.

---

## Praktische do's en don'ts

**Do:**
- Houd de muis stil als je iets uitlegt — niet rondzwiepen
- Klik in modals altijd **Annuleren** in plaats van Bevestigen
- Bij twijfel: vraag terug ("zou dit voor jullie werken?")
- Zoek tijdens demo iemand in de zaal die meedoet — laat ze een naam roepen die je kunt zoeken

**Don't:**
- Niet werkelijk een toewijzing/bulk-actie afronden in CT102 (data van Demo staat er, blijft staan)
- Niet beloven wat je niet weet ("kost €X" → "daar moeten we het binnen de SLB nog over hebben")
- Niet diep in technische details duiken voor conciërges — die willen weten "kan ik er morgen mee werken"
