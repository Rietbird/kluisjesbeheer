# Systeemeisen

## Server

| Component | Minimaal | Aanbevolen |
|-----------|----------|------------|
| OS | Debian 12 / Ubuntu 22.04+ | Debian 12 LTS |
| RAM | 512 MB | 1 GB |
| Opslag | 1 GB | 2 GB |
| Python | 3.11+ | 3.12 |
| Node.js | 18 LTS | 20 LTS |
| Webserver | NGINX (reverse proxy) | NGINX |
| HTTPS | Vereist | SSL-certificaat of Cloudflare tunnel |

De app draait als systemd service via Gunicorn (2 workers) op poort 5000. NGINX proxyt HTTPS-verkeer naar Gunicorn.

## Entra ID (Azure AD)

De app gebruikt Microsoft Entra ID voor single sign-on (SSO). Gebruikers loggen in met hun Microsoft-account.

### App Registration

| Instelling | Waarde |
|------------|--------|
| Type | Web |
| Redirect URI | `https://[domein]/auth/callback` |
| API permissions | `User.Read` (Delegated) |
| | `GroupMember.Read.All` (Delegated) + Admin Consent |
| Client Secret | 1 actief secret |

### Security Group

Maak **1** security group aan (bijv. `Concierges-Kluisbeheer`). Alle medewerkers die de app mogen gebruiken moeten lid zijn van deze groep.

Er is maar 1 groep nodig. De rolverdeling (beheerder vs. concierge) en vestigingskoppelingen worden in de app zelf geregeld via Beheer > Gebruikers.

### Stappen voor Entra ID configuratie

1. Ga naar [Azure Portal](https://portal.azure.com) > **App registrations** > **New registration**
2. Naam: `Kluisjesbeheer`
3. Redirect URI: `https://[domein]/auth/callback` (type: **Web**)
4. Noteer: **Application (client) ID** en **Directory (tenant) ID**
5. Ga naar **Certificates & secrets** > **New client secret**
   - Kopieer de **Value** (deze is maar eenmalig zichtbaar!)
6. Ga naar **API permissions** > **Add a permission** > **Microsoft Graph**:
   - `User.Read` (Delegated) — leest naam en e-mail bij login
   - `GroupMember.Read.All` (Delegated) — checkt groepslidmaatschap
   - Klik **Grant admin consent for [tenant]**
7. Ga naar **Entra ID** > **Groups** > **New group**
   - Type: Security
   - Naam: bijv. `Concierges-Kluisbeheer`
8. Voeg medewerkers toe die toegang moeten hebben
9. Noteer de **Object ID** van deze groep

### Benodigde gegevens voor config.json

Na bovenstaande stappen heb je deze 3 waarden nodig:

| Veld in config.json | Waar te vinden |
|---------------------|----------------|
| `TenantId` | App Registration > Overview > Directory (tenant) ID |
| `ClientId` | App Registration > Overview > Application (client) ID |
| `ClientSecret` | App Registration > Certificates & secrets > Value |

> 🔑 **Toegangscontrole** loopt via *"Assignment required: Yes"* op de
> Enterprise App, niet via een groep in `config.json`. Wijs users (of
> een security-groep) toe via *Enterprise applications → [jouw app] →
> Users and groups*.

## Magister API

De Magister-koppeling is **optioneel bij installatie**. Je kunt de app eerst uitrollen en later de koppeling instellen via Beheer > Instellingen > Magister API koppeling.

De koppeling is nodig voor:
- Automatische synchronisatie van leerlinggegevens (naam, klas, e-mail)
- Filteren van leerlingen per vestiging op basis van Magister-locatie
- Zoeken van leerlingen bij het toewijzen van kluisjes

### Webservice vereisten

| Component | Details |
|-----------|---------|
| Webservice type | Medius SOAP/XML |
| URL-formaat | `https://[school].swp.nl:8800/doc` |
| Protocol | HTTPS (poort 8800, soms 443) |
| SSL | Self-signed certificaten worden ondersteund |
| Account type | Service account (niet persoonlijk) |

### Benodigde functies en rechten

| Functie | Bibliotheek | Doel |
|---------|-------------|------|
| `Login` | `Algemeen` | Authenticatie bij de webservice |
| `GetActiveStudents` | `ADFuncties` | Ophalen van alle actieve leerlingen |

### Leerlingvelden die opgehaald worden

| Veld | Beschrijving | Gebruik in de app |
|------|-------------|-------------------|
| `stamnr` | Uniek leerlingnummer | Koppeling bij toewijzing |
| `naam` | Volledige naam | Weergave |
| `roepnaam` | Roepnaam | Weergave |
| `tussenvoegsel` | Tussenvoegsel | Weergave |
| `achternaam` | Achternaam | Weergave + zoeken |
| `email` | E-mailadres | Weergave |
| `klas` | Huidige klas | Filteren + bulk toewijzen |
| `leerjaar` | Leerjaar | Weergave |
| `studie` | Studierichting | Weergave |
| `locatie` | Administratieve eenheid | Koppeling vestiging |

Het `locatie`-veld is essentieel voor multi-vestigingsscholen. Hiermee worden leerlingen automatisch aan de juiste vestiging gekoppeld in Beheer > Vestigingen > Locaties.

### Aanvragen bij Magister-beheerder

1. Controleer of de Medius webservice actief is (vaak al ingeschakeld voor andere koppelingen)
2. Maak een service account aan met leestoegang op `Algemeen` en `ADFuncties`
3. Lever de **URL**, **gebruikersnaam** en **wachtwoord** aan

De credentials worden via de app ingevoerd (Beheer > Instellingen) en versleuteld (AES-128-CBC + HMAC) opgeslagen in de database. Ze zijn niet uitleesbaar via de interface.

## Netwerk

De server moet de volgende uitgaande verbindingen kunnen maken:

| Bestemming | Poort | Doel |
|------------|-------|------|
| `login.microsoftonline.com` | 443 | Entra ID SSO |
| `graph.microsoft.com` | 443 | Microsoft Graph API (user info, groepscheck) |
| Magister SOAP endpoint | 8800 (of 443) | Leerlingensynchronisatie |
