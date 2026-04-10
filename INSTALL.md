# Kluisjesbeheer — Installatiehandleiding

Stappen om Kluisjesbeheer uit te rollen op een nieuwe school.

## Vereisten

### Van de school nodig

| Wat | Waarom | Wie levert dit |
|-----|--------|----------------|
| **Entra ID App Registration** | SSO login voor medewerkers | ICT-beheerder school |
| — Tenant ID (UUID) | Azure AD tenant identifier | |
| — Client ID + Client Secret | App Registration credentials | |
| — Redirect URI | `https://[domein]/auth/callback` | |
| — Security Group ID (UUID) | Bepaalt wie mag inloggen | |
| **Magister API-toegang** | Dagelijkse leerlingen-sync | Magister-beheerder |
| — SOAP endpoint URL | bijv. `https://school.swp.nl:8800/doc` | |
| — Service account (user/pass) | Leesrechten op leerling- en kluisjesdata | |
| **Excel export uit Magister** | Eenmalige import van kluisjes + toewijzingen | Concierge/admin |
| — Export uit MX of Desktop | Formaat wordt automatisch herkend | |
| **Schoollogo** (.png, .jpg of .svg) | Branding in de app | School |

### Entra ID App Registration aanmaken

1. Ga naar [Azure Portal](https://portal.azure.com) > App registrations > New registration
2. Naam: `Kluisjesbeheer`
3. Redirect URI: `https://[domein]/auth/callback` (type: Web)
4. Noteer: **Application (client) ID** en **Directory (tenant) ID**
5. Certificates & secrets > New client secret > kopieer de **Value**
6. API permissions > Add permission > Microsoft Graph:
   - `User.Read` (Delegated)
   - `GroupMember.Read.All` (Delegated)
   - Grant admin consent
7. Maak een Security Group aan in Entra ID met de medewerkers die toegang moeten hebben
8. Noteer de **Object ID** van deze groep

### Infrastructuur

- Linux server: Debian 12 (of Ubuntu 22.04+), minimaal 512MB RAM
- Python 3.11+, Node.js LTS, npm (worden geinstalleerd door deploy.sh)
- HTTPS domein (via Cloudflare tunnel of eigen SSL-certificaat)
- NGINX als reverse proxy

## Installatie

### 1. Bestanden op de server zetten

```bash
# Kopieer het project naar de server
scp -r kluisjesbeheer/ root@[server-ip]:/opt/

# Of via git
cd /opt
git clone [repo-url] kluisjesbeheer
```

### 2. Deploy script draaien

```bash
cd /opt/kluisjesbeheer
bash deploy.sh
```

Dit installeert alle dependencies, bouwt de frontend, maakt een systemd service aan en start de app.

### 3. Config invullen

```bash
nano /opt/kluisjesbeheer/backend/config.json
```

Vul de velden in met de gegevens van de school:

```json
{
  "TenantId": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "ClientId": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "ClientSecret": "je-client-secret",
  "DashboardGroupId": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "RedirectUri": "https://kluisjes.jouwschool.nl/auth/callback",
  "SecretKey": "willekeurige-lange-string",
  "MagisterUrl": "https://jouwschool.swp.nl:8800/doc",
  "MagisterUser": "webuser",
  "MagisterPass": "wachtwoord",
  "SchoolNaam": "Naam van de school",
  "SchoolSubtitel": "Optioneel",
  "SchoolLogo": "/img/logo.png",
  "SchoolKleur": "#FF8200",
  "AllowedOrigins": ["https://kluisjes.jouwschool.nl"]
}
```

> **Tip:** Genereer een SecretKey met `python3 -c "import secrets; print(secrets.token_hex(32))"`

### 4. NGINX configureren

Maak `/etc/nginx/sites-enabled/kluisjesbeheer`:

```nginx
server {
    listen 80;
    server_name kluisjes.jouwschool.nl;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    server_name kluisjes.jouwschool.nl;

    ssl_certificate /etc/nginx/ssl/cert.crt;
    ssl_certificate_key /etc/nginx/ssl/cert.key;

    client_max_body_size 16M;

    location /img/ {
        root /opt/kluisjesbeheer/frontend/dist;
        expires 1h;
        add_header Cache-Control "public";
    }

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
nginx -t && systemctl reload nginx
```

**Alternatief:** gebruik een Cloudflare tunnel naar `http://127.0.0.1:5000`.

### 5. Service herstarten

```bash
systemctl restart kluisjesbeheer
```

## Eerste configuratie via de app

Ga naar `https://kluisjes.jouwschool.nl` en log in met een account uit de Security Group.

### Stap 1: Vestigingen aanmaken

Beheer > Vestigingen & Kluisjes > vestigingen toevoegen (bijv. "Hoofdgebouw", "Dependance").

### Stap 2: Clusters aanmaken

Per vestiging clusters aanmaken (bijv. "Begane grond", "1e verdieping"). Stel per cluster het standaard borgbedrag in.

### Stap 3: Kluisjes importeren

Beheer > Import > kies vestiging en cluster, upload de Magister Excel-export.

Ondersteunde formaten (automatisch herkend):

**Magister MX:**
```
Cluster | Kluis | Naam | Stamnummer | Klas | Uitleenperiode | Status | Borgbedrag | Locatie | Sleutel
```

**Magister Desktop:**
```
Stamnr | Omschrijving Kluisje | Slotnummer | Achternaam | Tussenv | Roepnaam | Verhuur vanaf | Verhuur tot/met
```

Kluisjes met status "Uitgeleend" worden inclusief toewijzing geimporteerd.

### Stap 4: Magister-locaties koppelen

Beheer > Locaties > koppel per vestiging de Magister-locaties. Dit zorgt ervoor dat bij het zoeken van leerlingen alleen leerlingen van de juiste locatie worden getoond.

### Stap 5: Leerlingen synchroniseren

Beheer > Import > klik op "Synchroniseren met Magister". Dit haalt alle actieve leerlingen op uit Magister.

### Stap 6: Branding instellen

Beheer > Instellingen > School branding:
- Schoolnaam en subtitel
- Schoolkleur (kleurpicker)
- Logo uploaden

### Stap 7: Overige instellingen

- **Borg:** Beheer > Borg > per vestiging borg aan/uit zetten
- **Regio:** Beheer > Instellingen > regio instellen (bepaalt schoolvakanties)
- **Kleuren:** Beheer > Kleuren > per vestiging een kleur toewijzen

## Onderhoud

### Dagelijkse Magister-sync

De leerlingendata (klas, naam, etc.) wijzigt gedurende het schooljaar. Synchroniseer regelmatig via Beheer > Import > Synchroniseren, of stel een cron-job in:

```bash
# /etc/cron.d/kluisjesbeheer-sync
0 6 * * 1-5 kluisjes /opt/kluisjesbeheer/.venv/bin/python /opt/kluisjesbeheer/backend/cron_sync.py
```

### Schoolvakanties

Het bestand `backend/schoolvakanties.json` bevat vakantiedata per regio. Dit moet jaarlijks handmatig bijgewerkt worden.

### Logs bekijken

```bash
journalctl -u kluisjesbeheer -f
```

### Service beheren

```bash
systemctl status kluisjesbeheer
systemctl restart kluisjesbeheer
systemctl stop kluisjesbeheer
```

## Veelvoorkomende problemen

| Probleem | Oorzaak | Oplossing |
|----------|---------|-----------|
| Login redirect loop | Verkeerde RedirectUri of ClientId | Check config.json, moet exact matchen met App Registration |
| 403 na login | Account niet in Security Group | Voeg gebruiker toe aan de DashboardGroupId groep |
| Magister sync mislukt | Verkeerde URL of credentials | Check MagisterUrl/User/Pass in config.json |
| Logo laadt niet | Browsercache | Hard refresh (Ctrl+Shift+R) of wis cache |
| 413 bij upload | NGINX upload limiet | Voeg `client_max_body_size 16M;` toe aan NGINX config |
| CRLF problemen na deploy | Windows line endings in binaire bestanden | deploy.sh converteert alleen tekstbestanden |
