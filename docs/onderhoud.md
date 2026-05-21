# Onderhoud

## Service beheren

```bash
systemctl status kluisjesbeheer    # Status bekijken
systemctl restart kluisjesbeheer   # Herstarten
systemctl stop kluisjesbeheer      # Stoppen
```

## Logs

```bash
journalctl -u kluisjesbeheer -f           # Live logs volgen
journalctl -u kluisjesbeheer --since today # Logs van vandaag
```

## Dagelijkse leerlingensync

Leerlinggegevens (klas, naam, locatie) wijzigen gedurende het schooljaar. Stel een cronjob in voor automatische synchronisatie:

```bash
# /etc/cron.d/kluisjesbeheer-sync
0 6 * * 1-5 kluisjes /opt/kluisjesbeheer/.venv/bin/python /opt/kluisjesbeheer/backend/cron_sync.py
```

Dit draait elke werkdag om 06:00. Handmatig synchroniseren kan via Beheer > Import > "Leerlingen ophalen uit Magister".

## Schoolvakanties

Het bestand `backend/schoolvakanties.json` bevat vakantieperiodes per regio (Noord, Midden, Zuid). Dit moet **jaarlijks handmatig bijgewerkt** worden met de nieuwe vakantiedata van de Rijksoverheid.

## Updates deployen

### Standaard (git clone install)

```bash
# Voor de update: handmatige backup (extra zekerheid)
curl -X POST https://<server>/api/backups/create -H "X-Requested-With: XMLHttpRequest" --cookie "..."
# (Of via Beheer → Backups → Nieuwe backup)

# Update zelf
cd /root/kluisjesbeheer
git pull
bash install.sh
```

`install.sh` is idempotent: bestaande `config.json` en database blijven onaangeroerd, alleen code wordt vervangen, frontend wordt opnieuw gebouwd, service herstart automatisch.

### Tarball-update (offline omgevingen)

Voor servers zonder GitHub-toegang: maak op een werkstation met toegang een bundel met `bash install/build-bundle.sh`, kopieer naar de server, pak uit en draai `bash install.sh` opnieuw.

### Pre-deploy checklist (bij handmatige tar-deploys voor productie-CT's)

> ⚠️ **KRITIEK: Gebruik ALTIJD `--exclude='*.db'` en `--exclude='config.json'` bij handmatige deploy-tarballs!**
> Op 2026-04-15 is de productiedatabase overschreven door een deploy zonder deze excludes. 5 dagen data verloren.

1. **Maak een handmatige backup:** `POST /api/backups/create` of via Beheer > Backups
2. **Bouw de frontend:** `cd frontend && npm run build`
3. **CRLF → LF converteren** (alleen tekstbestanden, niet binair)
4. **Tar maken met excludes:**
   ```bash
   tar --exclude='venv' --exclude='node_modules' --exclude='__pycache__' \
       --exclude='.pytest_cache' --exclude='*.db' --exclude='config.json' \
       --exclude='.git' --exclude='frontend/src' --exclude='frontend/package-lock.json' \
       -cf /tmp/kluisjes-deploy.tar backend/ frontend/dist/ frontend/public/
   ```
5. **Verifieer de tar:** `tar tf /tmp/kluisjes-deploy.tar | grep -E '\.db|config\.json'` — moet leeg zijn
6. **Deploy en restart** via scp + tar extract + `systemctl restart kluisjesbeheer`

De database wordt automatisch gemigreerd bij het opstarten (nieuwe tabellen en kolommen worden aangemaakt).

> **Let op:** `config.json` en de database (`*.db`) mogen NOOIT in de tar zitten. Elke server heeft zijn eigen config en database.

## Backup

> **Achtergrond:** Op 2026-04-15 is de productiedatabase overschreven door een deploy zonder `--exclude='*.db'`. 5 dagen data verloren. Sindsdien zijn drie backuplagen actief.

De volledige applicatiestate zit in twee bestanden:

| Bestand | Inhoud |
|---------|--------|
| `backend/kluisjesbeheer.db` | Alle data (kluisjes, toewijzingen, leerlingen, instellingen, gebruikers) |
| `backend/config.json` | Entra ID credentials en SecretKey |

### Laag 1: In-app backup (automatisch)

De app maakt automatisch dagelijkse backups via een background thread. Backups worden aangemaakt met de `sqlite3.backup()` API (veilig tijdens schrijfoperaties).

- **Locatie:** `backend/backups/` op elke CT
- **Retentie:** 7 dagelijkse + 4 wekelijkse backups (rolling)
- **Handmatig:** Beheer > Backups, of `POST /api/backups/create`
- **Downloaden:** `GET /api/backups/<naam>/download` (alleen beheerder)

### Laag 2: Proxmox host cronjob (optioneel, alleen bij LXC-deployment)

Het script `/usr/local/bin/backup-kluisjes.sh` op de Proxmox host draait dagelijks om 02:00:

- Haalt de database op uit elke kluisjes-container via `pct exec` + `pct pull`
- Opslag: `/var/lib/vz/dump/kluisjes-db/` (7 dagelijkse per container)
- Zondag: volledige `vzdump` snapshot van elke kluisjes-container (4 weken bewaard)

Niet relevant bij Docker- of VM-deploys — daar is laag 1 (in-app backup) plus reguliere VM-snapshots voldoende.

### Laag 3: Deploy-bescherming

De deploy-tar **moet altijd** deze excludes bevatten:
```bash
--exclude='*.db' --exclude='config.json'
```

### Restore procedure

**Vanuit in-app backup:**
```bash
# 1. Stop de service
systemctl stop kluisjesbeheer

# 2. Kopieer backup over huidige database
cp /opt/kluisjesbeheer/backend/backups/kluisjesbeheer_dagelijks_YYYY-MM-DD.db \
   /opt/kluisjesbeheer/backend/kluisjesbeheer.db

# 3. Verwijder WAL/SHM bestanden (worden opnieuw aangemaakt)
rm -f /opt/kluisjesbeheer/backend/kluisjesbeheer.db-wal
rm -f /opt/kluisjesbeheer/backend/kluisjesbeheer.db-shm

# 4. Eigenaar herstellen en service starten
chown kluisjes:kluisjes /opt/kluisjesbeheer/backend/kluisjesbeheer.db
systemctl start kluisjesbeheer
```

**Vanuit Proxmox host backup:**
```bash
# Op de Proxmox host (vervang <CTID> door je container-ID):
pct push <CTID> /var/lib/vz/dump/kluisjes-db/<CTID>/kluisjesbeheer_YYYY-MM-DD.db \
  /opt/kluisjesbeheer/backend/kluisjesbeheer.db

pct exec <CTID> -- bash -c '
  rm -f /opt/kluisjesbeheer/backend/kluisjesbeheer.db-wal
  rm -f /opt/kluisjesbeheer/backend/kluisjesbeheer.db-shm
  chown kluisjes:kluisjes /opt/kluisjesbeheer/backend/kluisjesbeheer.db
  systemctl restart kluisjesbeheer
'
```

> **Let op:** Na een restore worden automatisch database-migraties gedraaid bij startup. Controleer de logs (`journalctl -u kluisjesbeheer`) na een restore.

## Veelvoorkomende problemen

| Probleem | Oorzaak | Oplossing |
|----------|---------|-----------|
| Login redirect loop | Verkeerde RedirectUri of ClientId | Check config.json, moet exact matchen met App Registration |
| "Er zijn nog geen vestigingen aan je account gekoppeld" | Nieuwe conciërge zonder vestiging | Beheerder koppelt vestiging(en) via Beheer → Gebruikers |
| Microsoft: "you can't access this app" | Account niet toegewezen aan de Enterprise App | Entra → Enterprise applications → [app] → Users and groups → Add |
| Login geeft 503 met "Configuratie nog niet voltooid" | `config.json` bevat nog `VUL_IN_*`-placeholders | Bewerk `/opt/kluisjesbeheer/backend/config.json` en restart de service |
| Magister sync mislukt | Verkeerde URL of credentials | Check via Beheer > Instellingen > Magister API koppeling |
| "Magister niet bereikbaar" | Firewall blokkeert poort 8800 | Controleer uitgaand verkeer naar Magister-server |
| Logo laadt niet | Browsercache | Hard refresh (Ctrl+Shift+R) |
| 413 bij upload | NGINX upload limiet | Voeg `client_max_body_size 16M;` toe aan NGINX config |
| Concierge ziet geen vestigingen | Geen vestigingen gekoppeld | Beheerder wijst toe via Beheer > Gebruikers |
| 500 bij logo upload | Schrijfrechten uploads/ map | `chown -R kluisjes:kluisjes /opt/kluisjesbeheer/backend/uploads` |
| Leerlingen niet gefilterd per vestiging | Locaties niet gekoppeld (optioneel) | Beheer > Vestigingen > klik vestiging > Locaties |
