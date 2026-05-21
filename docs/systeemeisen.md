# Systeemeisen

## Server

| Component | Minimaal | Aanbevolen |
|-----------|----------|------------|
| OS | Debian 12 / 13 | Debian 12 LTS |
| RAM | 1 GB (run-time); 2 GB tijdens install (Vite-build) | 2 GB |
| Opslag | 2 GB | 5 GB |
| Python | 3.11+ | 3.12 |
| Node.js | 18 LTS | 20 LTS |
| Webserver | NGINX (door `install.sh` automatisch geïnstalleerd) | NGINX met eigen TLS-cert |
| HTTPS | Vereist door Entra (self-signed is OK) | Eigen CA-cert of Let's Encrypt |

De app draait als systemd service via Gunicorn (2 workers) op poort 5000. `install.sh` zet zelf NGINX op (poort 80 → 443) met een self-signed cert. Voor productie kun je het cert vervangen.

## Entra ID (Azure AD)

De app gebruikt Microsoft Entra ID voor single sign-on (SSO). Gebruikers loggen in met hun Microsoft-account.

### App Registration

| Instelling | Waarde |
|------------|--------|
| Type | Web |
| Redirect URI | `https://[domein]/auth/callback` of `https://[ip-adres server]/auth/callback` |
| API permissions | `User.Read` (Delegated) — leest naam en e-mail bij login |
| Client Secret | 1 actief secret |

### Toegangscontrole — Assignment required

Wij gebruiken Entra's **"Assignment required"**-mechanisme. Microsoft regelt vóór onze app überhaupt iets ziet wie wel/niet binnen mag. Geen aparte groep-check in onze code; je wijst users en/of groepen toe aan de Enterprise Application.

De **eerste persoon die inlogt wordt automatisch beheerder**. Volgende collega's die inloggen worden automatisch als conciërge aangemaakt; de beheerder koppelt rol en vestiging(en) in de app via *Beheer → Gebruikers*.

### Stappen voor Entra ID configuratie

1. Ga naar [Azure Portal](https://portal.azure.com) > **App registrations** > **New registration**
2. Naam: `Kluisjesbeheer`
3. Redirect URI: `https://[domein]/auth/callback` of `https://[ip-adres server]/auth/callback` (type: **Web**)
4. Noteer: **Application (client) ID** en **Directory (tenant) ID**
5. Ga naar **Certificates & secrets** > **New client secret**
   - Kopieer de **Value** (deze is maar eenmalig zichtbaar!)
6. Ga naar **API permissions** > **Add a permission** > **Microsoft Graph**:
   - `User.Read` (Delegated) — leest naam en e-mail bij login
   - Klik **Grant admin consent for [tenant]**
7. Ga naar **Enterprise applications** > [jouw app] > **Properties**: zet *"Assignment required"* op **Yes**
8. Ga naar **Enterprise applications** > [jouw app] > **Users and groups**: voeg de medewerkers (of een security-groep) toe die toegang moeten hebben

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
| `graph.microsoft.com` | 443 | Microsoft Graph API (user info) |
| `github.com` | 443 | Voor `git pull` updates (alleen bij git-clone install) |
| Magister SOAP endpoint | 8800 (of 443) | Leerlingensynchronisatie |
