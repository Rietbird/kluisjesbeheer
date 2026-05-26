# Configuratie

Na de [installatie](../install/README.md) wordt de app volledig via de webinterface geconfigureerd.

## Eerste login

Ga naar `https://kluisjes.jouwschool.nl` (of `https://[ip-adres server]/`) en log in met je Microsoft-account. De **eerste gebruiker** die inlogt wordt automatisch beheerder.

Latere collega's loggen ook gewoon zelf in via Entra (mits ze op de Enterprise App zijn *Assigned*). Zij worden automatisch aangemaakt als conciërge zonder vestiging. De beheerder koppelt ze daarna in *Beheer → Gebruikers* aan een rol + vestiging(en).

## Stap 1: Instellingen

Ga naar **Beheer** (tandwiel rechtsbovenin) > **Instellingen**.

### School branding

| Veld | Beschrijving |
|------|-------------|
| Schoolnaam | Wordt getoond in de header en als paginatitel |
| Subtitel | Optionele subtitel onder "Kluisjesbeheer" |
| Schoolkleur | Hoofdkleur van de app (hex, bijv. `#FF8200`) |
| Logo | Upload als .png, .jpg of .svg |

### Periode en regio

| Veld | Beschrijving |
|------|-------------|
| Standaard uitleenperiode | Van/tot datum (MM-DD) voor nieuwe toewijzingen |
| Regio | Noord / Midden / Zuid — bepaalt schoolvakanties |

### Magister API koppeling

| Veld | Beschrijving |
|------|-------------|
| Webservice URL | Bijv. `https://jouwschool.swp.nl:8800/doc` |
| Gebruikersnaam | Service account gebruikersnaam |
| Wachtwoord | Wordt versleuteld opgeslagen |

Dit is optioneel. Zonder Magister-koppeling kun je leerlingen handmatig zoeken en kluisjes handmatig importeren.

## Stap 2: Kluisjes importeren

Ga naar **Beheer** > **Import**.

### Excel-import

1. Exporteer kluisjes uit Magister als .xlsx
2. Upload het bestand
3. De app herkent automatisch het formaat (MX of Desktop)
4. Bij MX-formaat worden vestigingen uit de `Locatie`-kolom gehaald
5. Bij Desktop-formaat worden prefixen uit kluisnummers gehaald — geef per prefix een vestigingnaam op
6. Klik "Importeren"

Vestigingen en clusters worden automatisch aangemaakt. Kluisjes die al uitgeleend zijn worden inclusief toewijzing geimporteerd.

### Ondersteunde formaten

**Magister MX:**

| Kolom | Beschrijving |
|-------|-------------|
| Cluster | Naam van het cluster (bijv. "Begane grond") |
| Kluis | Kluisnummer |
| Naam | Naam leerling (bij uitgeleend) |
| Stamnummer | Leerlingnummer (bij uitgeleend) |
| Klas | Klas leerling |
| Uitleenperiode | Periode (bijv. "01-09-2025 / 31-07-2026") |
| Status | "Uitgeleend" of leeg |
| Borgbedrag | Bedrag in euro's |
| Locatie | Vestigingsnaam |
| Sleutel | Sleutelnummer |

**Magister Desktop:**

| Kolom | Beschrijving |
|-------|-------------|
| Stamnr | Leerlingnummer |
| Omschrijving Kluisje | Kluisnummer |
| Slotnummer | Sleutelnummer |
| Achternaam | Achternaam leerling |
| Tussenv | Tussenvoegsel |
| Roepnaam | Roepnaam |
| Verhuur vanaf | Startdatum |
| Verhuur tot/met | Einddatum |

### Magister-sync

Als de Magister API geconfigureerd is, klik op **"Leerlingen ophalen uit Magister"** om de leerlingenlijst te synchroniseren. Dit kan ook automatisch via een cronjob (zie [Onderhoud](onderhoud.md)).

## Stap 3: Vestigingen configureren

Ga naar **Beheer** > **Vestigingen**.

Klik op een vestiging om de instellingen te openen:

### Kleur

Wijs een kleur toe per vestiging. Deze wordt gebruikt in de kaartjes op het hoofdscherm.

### Borg

Schakel borg in/uit per vestiging. Als borg actief is, stel per cluster het standaard borgbedrag in.

### Magister-locaties

> **Optioneel.** Zonder koppeling werkt de app gewoon — alle leerlingen zijn doorzoekbaar bij uitleen, maar zonder filter per vestiging. Alleen relevant als je meerdere vestigingen hebt én wilt dat conciërges alleen leerlingen van hun eigen vestiging zien.

Koppel Magister-locaties aan vestigingen. Hierdoor worden bij het zoeken van een leerling alleen leerlingen van de gekoppelde locatie(s) getoond.

Voorbeeld:

| Vestiging | Magister-locatie |
|-----------|-----------------|
| Hoofdlocatie | "Vestiging Hoofdgebouw" |
| Dependance Noord | "Vestiging Noord" |
| Dependance Zuid | "Vestiging Zuid" |

## Stap 4: Gebruikers koppelen

Ga naar **Beheer** > **Gebruikers**.

### Rollen

| Rol | Ziet | Mag | Beheer-menu |
|-----|------|-----|-------------|
| **Beheerder** | Alle vestigingen | Alles | Ja |
| **Conciërge** | Eigen vestiging(en) | Toewijzen, beëindigen, rapportages | Nee |

### Hoe gebruikers verschijnen

Nieuwe gebruikers worden **automatisch aangemaakt** zodra ze voor het eerst inloggen via Entra (mits ze op de Enterprise App zijn toegewezen via *Assignment*). Daar hoef je niets handmatig voor te doen. De gebruiker verschijnt in de lijst zodra Microsoft ze toegelaten heeft.

### Rol en vestiging(en) toewijzen

Een nieuwe conciërge ziet bij eerste login een melding *"Er zijn nog geen vestigingen aan je account gekoppeld"*. Jij koppelt 'm dan zo:

1. Klik op het pen-icoon achter de naam
2. Kies de rol (Beheerder of Conciërge)
3. Bij conciërge: vink de vestiging(en) aan
4. Klik **Opslaan**

De conciërge kan daarna direct inloggen.

### Wat de conciërge ziet

- Bij 1 vestiging: gaat direct naar het kluisjesoverzicht (geen vestigingkeuze)
- Bij meerdere vestigingen: ziet de vestigingpicker met alleen eigen vestigingen
- Geen tandwiel-icoon (geen toegang tot Beheer)
