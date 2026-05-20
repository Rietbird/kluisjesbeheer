# Kluisjesbeheer — Installatie op een eigen server

Deze handleiding beschrijft hoe je kluisjesbeheer installeert op een eigen
VMware-VM of LXC-container. Het installatiescript (`install.sh`) regelt de
techniek; deze handleiding beschrijft wat je vooraf nodig hebt, hoe je het
draait, en wat je daarna nog handmatig moet doen.

---

## 1. Wat je nodig hebt vóór je begint

### 1.1 De server

- **VMware-VM of LXC-container** met een verse installatie van **Debian 12**
  ("Bookworm") of **Debian 13** ("Trixie"). Beide werken; het script
  detecteert de versie en past zich aan.
- **Minimaal:** 2 vCPU, 2 GB RAM, 20 GB disk. Voor een gemiddelde school
  ruim voldoende.
- **Root-toegang** (direct of via `sudo`).
- **Internet-verbinding** (voor `apt` en `npm`).
- **Statisch intern IP-adres** of een interne DNS-naam waarmee de app
  bereikbaar wordt vanaf het schoolnetwerk (de app luistert standaard op
  TCP-poort `5000`).

### 1.2 De bestanden

Je krijgt van ons een **bundel** met daarin:

```
kluisjesbeheer-install/
├── install.sh
├── backend/
├── frontend/
└── docs/
```

Pak die uit op een werkmap op de server, bijvoorbeeld `/root/kb-install/`.

### 1.3 Microsoft Entra ID (voor inloggen)

De app gebruikt Entra ID single-sign-on. Je hebt nodig (aan te vragen bij
de Microsoft-tenantbeheerder van de school):

- **TenantId** — GUID van de Entra-tenant
- **ClientId** — GUID van de Entra app-registratie
- **ClientSecret** — geheim bij de app-registratie
- **DashboardGroupId** — GUID van een Entra-beveiligingsgroep met de
  gebruikers die toegang krijgen
- **RedirectUri** — de URL waarop de app draait, eindigend op
  `/auth/callback` (bijv. `https://kluisjes.intern.school.nl/auth/callback`)

> ⚠️ **Belangrijk over de RedirectUri:** Entra ID vereist HTTPS, behalve
> voor `http://localhost`. Als je de app via een interne IP of HTTP-only
> hostname benadert, regel dan een interne TLS-certificaat (interne CA of
> reverse-proxy met cert) of een publiek bereikbaar subdomein. Het
> installatiescript regelt dit **niet** — bespreek dit met je
> netwerkbeheerder vooraf.

### 1.4 Magister (voor leerling-sync)

- **Medius SOAP/XML-webservice URL** (formaat
  `https://<jouwschool>.swp.nl:8800/doc`)
- **Service-account** (apart account, niet persoonlijk) met leestoegang
  op `Algemeen.Login` en `ADFuncties.GetActiveStudents`
- ⚠️ **IP-whitelist:** SWP blokkeert poort 8800 standaard. Het uitgaande
  publieke IP van de server moet door de Magister-/SWP-beheerder van de
  school op de whitelist worden gezet. Het installatiescript toont na
  afloop dit IP-adres.

---

## 2. Het installatiescript draaien

```bash
# 1. Pak de bundel uit
tar xzf kluisjesbeheer-install.tgz
cd kluisjesbeheer-install

# 2. Draai het script als root
sudo bash install.sh
```

Het script is **idempotent** — opnieuw draaien is veilig en overschrijft
géén bestaande database of `config.json`.

### 2.1 Wat het script doet

1. **Pre-flight checks** — controleert Debian-versie, of de bundel
   compleet is, en internet-toegang
2. **Systeem-packages** — installeert `python3`, `nodejs`, `npm`, `cron`,
   `sqlite3` via apt
3. **App-gebruiker `kluisjes`** — wordt aangemaakt als die nog niet
   bestaat (systeem-account zonder shell)
4. **Code uitrollen** naar `/opt/kluisjesbeheer/` (overschrijft géén
   database, `config.json`, of backups)
5. **Python-omgeving** — virtuele env in `/opt/kluisjesbeheer/.venv/` +
   pip-dependencies
6. **Frontend bouwen** — `npm ci && npm run build` (Vite)
7. **config.json** — wordt aangemaakt met een **automatisch
   gegenereerde willekeurige SecretKey** als hij nog niet bestaat. Bestaande
   `config.json` blijft staan.
8. **Permissies** — alles eigendom van `kluisjes`; `config.json` op `600`
   (alleen `kluisjes` mag het lezen)
9. **systemd-service** — `kluisjesbeheer.service` op poort 5000,
   automatisch starten bij boot
10. **Cron-job** — dagelijkse leerling-sync om 06:00 via
    `/etc/cron.d/kluisjesbeheer-sync`, log naar
    `/var/log/kluisjes-sync.log` (rechten 640 — niet wereld-leesbaar)
11. **Service starten** + **smoketest** (curl localhost:5000)
12. **Eindrapport** met server-IP en vervolgstappen

### 2.2 De automatische SecretKey

> 🔑 De `SecretKey` in `config.json` wordt gebruikt om het Magister-
> wachtwoord versleuteld in de database op te slaan (Fernet / AES-128-CBC
> + HMAC). Het script genereert deze automatisch (64 hex chars uit
> `/dev/urandom`).
>
> **Wijzig deze sleutel NIET nadat je de Magister-credentials hebt
> ingevuld** — je verliest dan het versleutelde wachtwoord en de cron
> kan niet meer inloggen. Bewaar `config.json` met je back-ups.

---

## 3. Wat je hierna nog moet doen

### 3.1 `config.json` invullen

```bash
sudo nano /opt/kluisjesbeheer/backend/config.json
```

Vervang de `VUL_IN_*`-velden:

| Veld | Waarde |
|---|---|
| `TenantId` | Entra Tenant-GUID |
| `ClientId` | Entra App Registration GUID |
| `ClientSecret` | Entra Client Secret |
| `DashboardGroupId` | Entra-groep-GUID met toegestane gebruikers |
| `RedirectUri` | Volledige URL incl. `/auth/callback` |
| `AllowedOrigins` | Lijst met frontend-URLs, bv. `["https://kluisjes.intern.school.nl"]` |
| `SchoolNaam` | Naam van de school (zichtbaar in UI) |
| `SchoolSubtitel` | Optioneel subtitel onder de naam |
| `SchoolLogo` | Pad naar logo (default `/img/logo.png`) |
| `SchoolKleur` | Hex-kleur voor branding, bv. `#FF8200` |

**Niet wijzigen:** `SecretKey` (zie 2.2).

Daarna herstarten:

```bash
sudo systemctl restart kluisjesbeheer
```

### 3.2 Eerste login

Open de app in de browser via de URL die je in `RedirectUri` hebt opgegeven
(zonder het `/auth/callback`-deel). De **eerste gebruiker die inlogt
wordt automatisch beheerder**. Daarna kun je via *Beheer → Gebruikers*
extra beheerders en conciërges toevoegen.

### 3.3 Magister-koppeling invullen

Ga naar **Beheer → Import** en vul de Magister-koppeling in:

- **URL:** `https://<jouwschool>.swp.nl:8800/doc`
- **Account:** het service-account
- **Wachtwoord:** wordt versleuteld in de database opgeslagen

Klik *Opslaan*. De cache wordt direct ververst, dus je kunt meteen testen.

### 3.4 IP-whitelist aanvragen bij SWP

In het eindrapport van het script staat het **uitgaande publieke IP-
adres** van de server. Geef dat aan de Magister-/SWP-beheerder van de
school met het verzoek dit te whitelisten voor de Medius-webservice op
poort 8800.

Het IP kun je later ook ophalen met:

```bash
curl -s https://ifconfig.me
```

> Bij verhuizing naar een andere server moet het nieuwe IP opnieuw
> aangevraagd worden.

### 3.5 Test de leerling-sync handmatig

```bash
sudo -u kluisjes /opt/kluisjesbeheer/.venv/bin/python /opt/kluisjesbeheer/backend/cron_sync.py
```

Verwachte uitvoer (na succesvolle whitelist):

```
=== CRON MAGISTER LEERLINGEN SYNC ===
Magister-config uit database: https://<jouwschool>.swp.nl:8800/doc
1234 leerlingen opgehaald, 56 klassen
Database bijgewerkt. Done!
```

Krijg je deze melding:

> *"Geen verbinding met de Magister-webservice (poort 8800). Controleer
> of het server-IP op de SWP-whitelist staat en of de URL klopt."*

…dan is de whitelist nog niet actief. Verifieer met:

```bash
openssl s_client -connect <jouwschool>.swp.nl:8800 </dev/null
```

Geen TLS-handshake = poort dicht / whitelist niet actief.

---

## 4. Eerste data binnenkrijgen

### 4.1 Leerlingen

Komt automatisch binnen via de cron om 06:00, of handmatig via *Beheer →
Import → "Leerlingen ophalen uit Magister"*.

### 4.2 Kluisjes

Komen **eenmalig** binnen via een Excel-export uit Magister:

1. In Magister → kluisjesmodule → export naar Excel
2. In kluisjesbeheer → *Beheer → Import* → upload de xlsx
3. Vestigingen en clusters worden automatisch aangemaakt
4. Optioneel: vink "kluisnummers normaliseren" aan als je nummers van
   wisselende lengte hebt (MO-1, MO-100, MO-1000 → MO-0001, MO-0100,
   MO-1000)

---

## 5. Onderhoud

| Wat | Commando |
|---|---|
| Service-status | `systemctl status kluisjesbeheer` |
| App-logs (live) | `journalctl -u kluisjesbeheer -f` |
| Cron-logs | `tail -f /var/log/kluisjes-sync.log` |
| Herstarten | `systemctl restart kluisjesbeheer` |
| Backups | in `/opt/kluisjesbeheer/backend/backups/` (7 daily + 4 weekly) |
| Handmatige backup | via de app: *Beheer → Backup → Maak backup* |
| Update (nieuwe versie) | nieuwe bundel uitpakken, `sudo bash install.sh` opnieuw |

> 🔒 Het cron-logbestand `/var/log/kluisjes-sync.log` heeft standaard
> rechten `640 root:root`. Wijzig dit niet — de app saneert wachtwoorden
> uit foutmeldingen, maar een wereld-leesbare log is altijd een onnodig
> risico.

---

## 6. Troubleshooting

| Symptoom | Oorzaak / oplossing |
|---|---|
| `systemctl status` toont `failed` | Check `journalctl -u kluisjesbeheer -n 100` — meestal ontbreekt of klopt iets in `config.json` |
| Login werkt niet, "redirect_uri_mismatch" | RedirectUri in `config.json` moet exact matchen met wat in Entra app-registration staat |
| Cron-sync faalt met "Geen verbinding ... poort 8800" | IP-whitelist nog niet actief bij SWP — zie 3.4 |
| Cron-sync faalt met "kan magister_pass niet ontsleutelen" | `SecretKey` is gewijzigd na het invullen van de Magister-credentials — vul het wachtwoord opnieuw in via de UI |
| Frontend toont blanco pagina | Build mislukt — `cd /opt/kluisjesbeheer/frontend && npm run build` en kijk naar foutmeldingen |
| Browser geeft "Mixed content"-fout | App draait op HTTP, RedirectUri is HTTPS (of andersom) — kies één en pas `config.json` aan |

Voor diepere problemen: `journalctl -u kluisjesbeheer -n 200 --no-pager`
en `tail -50 /var/log/kluisjes-sync.log`.
