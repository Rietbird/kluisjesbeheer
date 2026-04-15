# Architectuur

## Overzicht

```
                         HTTPS (443)
Browser  ──────────>  NGINX  ──────────>  Gunicorn (5000)  ──────>  Flask app
                        |                                              |
                   statische files                              SQLite DB (WAL)
                  (frontend/dist)                                      |
                                                               Magister SOAP API
                                                                 (poort 8800)
```

## Stack

| Laag | Technologie | Versie |
|------|-------------|--------|
| Frontend | React, Vite, TailwindCSS | 18, 6, 3 |
| Backend | Flask, Gunicorn | 3.x, 22.x |
| Database | SQLite | WAL mode |
| Auth | MSAL (Microsoft Authentication Library) | Python |
| Encryptie | cryptography (Fernet) | AES-128-CBC + HMAC |
| Leerlingdata | Magister Medius SOAP/XML | - |
| Webserver | NGINX | Reverse proxy |
| Process manager | systemd | - |

## Backend structuur

```
backend/
  app.py                 # Flask app factory, middleware, route registratie
  auth.py                # Entra ID SSO, login/callback/logout, gebruikerscheck
  config.py              # Leest config.json
  crypto_util.py         # Fernet encryptie voor API credentials
  db.py                  # SQLite init, migraties, connectie
  magister_client.py     # Medius SOAP/XML client
  cron_sync.py           # Standalone sync script voor cronjob
  api_vestigingen.py     # CRUD vestigingen + locatiekoppelingen
  api_clusters.py        # CRUD clusters
  api_kluisjes.py        # CRUD kluisjes, import (preview + execute)
  api_toewijzingen.py    # Toewijzen, beeindigen, bulk operaties
  api_magister.py        # Leerlingen zoeken, klassen, sync
  api_dashboard.py       # Statistieken, rapportages, PDF
  api_instellingen.py    # School settings, logo upload, Magister config
  api_gebruikers.py      # Gebruikersbeheer (CRUD, rollen, vestigingen)
  api_schooljaar.py      # Schooljaar/vakantie logica
  api_backup.py          # Backup endpoints (lijst, aanmaken, downloaden)
  backup.py              # Backup scheduler + sqlite3.backup() implementatie
  backups/               # Dagelijkse/wekelijkse SQLite backups (rolling retention)
```

## Frontend structuur

```
frontend/src/
  App.jsx                # Root component
  api.js                 # API client met deduplicatie en CSRF header
  hooks/
    useAuth.jsx          # Auth context + provider
    useKluisjes.jsx      # Kluisjes data + filters
    useDarkMode.jsx      # Dark mode toggle
  context/
    BrandingContext.jsx   # School branding (naam, logo, kleur)
    InstellingenContext.jsx # Borg, kleuren per vestiging
  pages/
    Uitleenoverzicht.jsx  # Hoofdpagina: vestigingpicker + kluisjesoverzicht
    Beheer.jsx            # Beheer: 4 tabs (Instellingen, Import, Vestigingen, Gebruikers)
  components/
    TopNav.jsx            # Header met logo, dark mode, gebruikersinfo
    Toolbar.jsx           # Filter/zoekbalk + actieknoppen
    LockerGrid.jsx        # Kaartweergave kluisjes
    LockerTable.jsx       # Lijstweergave kluisjes
    LockerModal.jsx       # Detail/toewijzing modal
    BulkWizard.jsx        # Collectief toekennen (6 stappen)
    BulkEndWizard.jsx     # Collectief beeindigen
```

## Database

SQLite met WAL (Write-Ahead Logging) mode voor concurrency. Schema wordt automatisch aangemaakt bij eerste start. Migraties draaien als `CREATE TABLE IF NOT EXISTS` en `ALTER TABLE ... ADD COLUMN` in `db.py`.

### Tabellen

| Tabel | Doel |
|-------|------|
| `vestigingen` | Schoolvestigingen (naam, adres, borg_actief, kleur) |
| `clusters` | Groepen kluisjes binnen een vestiging (naam, standaard_borg) |
| `kluisjes` | Individuele kluisjes (nummer, sleutel, status, locatie) |
| `toewijzingen` | Koppeling kluisje-leerling (actief flag, periode, borg, sleutel) |
| `leerlingen` | Gesynchroniseerd uit Magister (stamnr, naam, klas, locatie) |
| `instellingen` | Key-value store voor app settings |
| `vestigingen_locaties` | Koppeling Magister-locatie -> vestiging |
| `vestigingen_klassen` | Legacy: koppeling klas -> vestiging |
| `gebruikers` | App-gebruikers (email, naam, rol, actief) |
| `gebruiker_vestigingen` | Koppeling gebruiker -> vestiging(en) |

### Soft deletes

Kluisjes gebruiken een `verwijderd` flag. Queries moeten altijd `AND verwijderd = 0` bevatten. Er geldt een partial unique index op `kluisnummer` waar `verwijderd = 0`.

### Toewijzing state machine

```
Vrij  -->  Uitgeleend  -->  Sleutel ingeleverd  -->  Borg teruggestort  -->  Vrij
```

- Maximaal 1 actieve toewijzing per kluisje (unique index `WHERE actief = 1`)
- Nieuwe toewijzing pas mogelijk als vorige is afgerond (sleutel + borg)

## Authenticatie

```
Browser  -->  /auth/login  -->  Entra ID  -->  /auth/callback
                                                     |
                                              1. Token ophalen (MSAL)
                                              2. Groepscheck (Graph API)
                                              3. Gebruiker opzoeken in DB
                                              4. Rol + vestigingen in sessie
                                              5. Redirect naar /
```

- Sessies: server-side Flask session (8 uur lifetime)
- CSRF: custom `X-Requested-With` header vereist op POST/PUT/DELETE
- Eerste gebruiker bij lege database wordt automatisch beheerder

## Encryptie

Magister API credentials worden versleuteld opgeslagen met Fernet (AES-128-CBC + HMAC-SHA256). De encryptiesleutel wordt afgeleid van de `SecretKey` uit config.json via SHA-256.

## Theming

Schoolkleuren worden dynamisch toegepast via CSS custom properties op `:root`. De Tailwind `primary` kleur refereert naar deze CSS variabelen, zodat alle componenten automatisch de schoolkleur gebruiken.

```
/api/branding  -->  BrandingContext  -->  CSS variabelen  -->  Tailwind classes
                                          --color-primary
                                          --color-primary-50
                                          --color-primary-100
                                          --color-primary-600
                                          --color-primary-700
```

## Backup architectuur

Na een incident op 2026-04-15 waarbij de productiedatabase overschreven werd door een deploy, zijn drie lagen van backupbescherming ingericht:

### Laag 1: In-app backup (backend/backup.py)

```
App startup  -->  BackupScheduler (background thread)
                       |
                  Dagelijks: sqlite3.backup() API
                       |
                  backend/backups/
                    kluisjesbeheer_dagelijks_2026-04-15.db  (7 bewaard)
                    kluisjesbeheer_wekelijks_2026-04-13.db  (4 bewaard)
```

- Gebruikt de Python `sqlite3.backup()` API — veilig tijdens schrijfoperaties (geen corrupte backups)
- Retentie: 7 dagelijkse + 4 wekelijkse backups, rolling
- API endpoints (alleen beheerder): `GET /api/backups`, `POST /api/backups/create`, `GET /api/backups/<naam>/download`
- Blueprint `backup_bp` geregistreerd in `app.py`

### Laag 2: Proxmox host cronjob

```
Proxmox host (10.40.0.10)
  /usr/local/bin/backup-kluisjes.sh  (cron: dagelijks 02:00)
       |
  pct exec 101 -- cat kluisjesbeheer.db  -->  /var/lib/vz/dump/kluisjes-db/ct101/
  pct exec 102 -- cat kluisjesbeheer.db  -->  /var/lib/vz/dump/kluisjes-db/ct102/
       |
  Zondag: vzdump 101 102  -->  /var/lib/vz/dump/ (4 weken bewaard)
```

- Dagelijks: database van CT101 en CT102 opgehaald via `pct exec` + `pct pull`
- 7 dagelijkse backups per container bewaard
- Zondag: volledige `vzdump` snapshot van beide containers (4 weken retentie)

### Laag 3: Deploy-bescherming

- `tar` commando **moet altijd** `--exclude='*.db'` en `--exclude='config.json'` bevatten
- Zie [onderhoud.md](onderhoud.md) voor de exacte deploy-procedure
