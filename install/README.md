# Kluisjesbeheer — uitrol-stappenplan

Stap-voor-stap copy-paste vanaf een **kale Debian 12/13 installatie**
tot een draaiende app.

> 📋 **Werkwijze:** vul stap 0 één keer in (variabelen), daarna kun je de
> commando's letterlijk plakken in de juiste shell. Markering:
> 🖥️ = jouw werkstation · 🐧 = doelserver (via console of SSH).

---

## Stap 0 — variabelen invullen (eenmalig)

Bepaal vooraf en houd bij de hand. Pas de waarden ná `export` aan voor
jouw situatie en plak deze export-blokken in de juiste shell **voor je
verder gaat**.

🖥️ **Werkstation** (Git Bash / WSL):

```bash
export SERVER_IP="10.x.x.x"             # intern IP van de doelserver
export SSH_PORT="22"                    # of 2222 als poort 22 geblokkeerd is
export SSH_USER="root"                  # of de standaard sudo-user op de VM
```

> 🔒 Dit stappenplan kiest voor `root` + wachtwoord — snel en prima
> voor een server op een intern beheernet. Wil je productie-veilig
> (admin-account + SSH-key)? Zie de tip onderaan stap 1.5.

---

## Stap 0.5 — Entra ID voorbereiden (vóór de uitrol)

Dit hoeft niet op de server, maar wil je vóór stap 1 geregeld hebben.
Toegang tot de app loopt 100% via Microsoft Entra ID (single sign-on).
De wachttijd zit in de Entra-acties, niet in de code — dus regel dit
vooraf, dan is de uitrol zelf vlot.

> 🔑 **Toegangsbeleid:** wij gebruiken Entra's **"Assignment required"**.
> Microsoft regelt vóór onze app überhaupt iets ziet wie wel/niet
> binnen mag. Geen aparte groep-check in onze code; je wijst gewoon
> users en/of groepen toe aan de Enterprise Application. De eerste
> persoon die inlogt wordt automatisch lokale beheerder; rollen +
> vestigingen beheer je daarna in *Beheer → Gebruikers* in de app
> zelf.

### Checklist (vraag dit aan de tenant-beheerder)

| # | Wat | Waar in Entra | Resultaat |
|---|---|---|---|
| 1 | App-registratie aanmaken | Entra → App registrations → New registration | `ClientId` (GUID) + `TenantId` (GUID) |
| 2 | Redirect URI toevoegen | App registration → Authentication → Web platform → Add URI | URL eindigend op `/auth/callback`, bv. `https://<server-ip>/auth/callback` of `https://kluisjes.intern.<school>.nl/auth/callback` |
| 3 | Client-secret aanmaken | App registration → Certificates & secrets → New client secret | `ClientSecret` (string — **direct kopiëren**, na 1× tonen onleesbaar) |
| 4 | API permissions | App registration → API permissions | `Microsoft Graph → Delegated → User.Read` + **"Grant admin consent"** |
| 5 | Assignment required = Yes | Enterprise applications → [jouw app] → Properties | "Assignment required" op **Yes** |
| 6 | Users toewijzen | Enterprise applications → [jouw app] → Users and groups → Add user/group | Voeg jezelf + de Demo-beheerders toe (later kun je daar groepen aan koppelen) |

> 💡 **Stap 6 mag ook met een Security-groep** — handiger als je veel
> users hebt en het beheer bij iemand anders ligt. Maak dan een groep
> aan, voeg de groep toe in *Users and groups*, en beheer members in
> de groep i.p.v. in de app-registratie.

### Variabelen voor `config.json` (stap 4 van de installatie)

Vul tijdens de Entra-setup deze tabel in, dan kun je 'm morgen letterlijk
overnemen:

```
TenantId      = ________________________________
ClientId      = ________________________________
ClientSecret  = ________________________________
RedirectUri   = https://________________/auth/callback
```

`DashboardGroupId` is **verouderd** en hoef je niet meer in te vullen
(toegangscontrole zit nu in Entra Assignment, niet in onze code).

### Aandachtspunt — HTTPS vereiste

Entra accepteert geen HTTP-RedirectUri (behalve `http://localhost`).
Self-signed cert is wel OK — `install.sh` genereert er zelf één bij
installatie. Browser geeft 1× "Niet beveiligd"-waarschuwing
("Geavanceerd → Doorgaan"), daarna werkt SSO normaal. Voor productie
met een echt cert: zie stap 7.

---

## Stap 1 — Kale Debian voorbereiden (op de doelserver)

> Uitgangspunt: een verse Debian 12/13 VM (VMware / LXC / VPS), waarop
> alleen root-toegang via de console beschikbaar is (geen SSH nog).

### 1.1 Op de VMware-console: inloggen en netwerk verifiëren

Log in als `root` op de console van de VM. Eerste check:

```bash
ip -4 addr show | grep inet
ping -c 2 8.8.8.8
cat /etc/debian_version
```

Je moet zien: een statisch intern IP, werkende internetverbinding, en
versie `12.x` of `13.x`. Werkt internet niet, los dat eerst op met
de netwerkbeheerder — verder zonder internet kan niet (apt + npm-install).

### 1.2 Apt updaten + basistools installeren

```bash
apt-get update && apt-get upgrade -y
apt-get install -y openssh-server sudo curl nano less ca-certificates
```

### 1.3 SWP-whitelist alvast aanvragen

> ⏱️ SWP heeft soms 1-2 werkdagen nodig om een IP te whitelisten. Door
> dit hier al te doen, loopt de aanvraag parallel aan de rest van de
> installatie — in stap 7 hoef je alleen nog te verifiëren.

```bash
curl -s https://ifconfig.me ; echo
```

Noteer dit IP en mail het direct naar de Magister-/SWP-beheerder van
de school met het verzoek: *"Whitelisten voor toegang tot
`<jouwschool>.swp.nl` op poort 8800."*

### 1.4 SSH-daemon controleren + root-login toestaan

```bash
systemctl enable --now ssh
systemctl status ssh --no-pager | head -3
ss -tlnp | grep :22 || echo "ssh luistert NIET op poort 22"
```

Standaard staat Debian 12/13 op `PermitRootLogin prohibit-password`
(root mag in, maar **alleen met SSH-key**). Voor wachtwoord-auth als
root moet dit op `yes`:

```bash
sed -i 's/^#*PermitRootLogin.*/PermitRootLogin yes/' /etc/ssh/sshd_config
systemctl restart ssh
grep -E '^PermitRootLogin' /etc/ssh/sshd_config       # controle: yes
```

> 💡 Als poort 22 geblokkeerd is en je 2222 wilt: bewerk
> `/etc/ssh/sshd_config`, regel `#Port 22` → `Port 2222`, dan
> `systemctl restart ssh`. Update dan ook `SSH_PORT` in stap 0.

### 1.5 SSH-verbinding testen vanaf je werkstation

🖥️ **Werkstation**:

```bash
ssh -p "$SSH_PORT" "$SSH_USER@$SERVER_IP" "echo 'SSH werkt'; cat /etc/debian_version"
```

Eerste keer: SSH vraagt om host-key bevestiging (`yes`) + het root-
wachtwoord. Verwacht: `SSH werkt` + versie-nummer. Werkt het? Door naar
stap 2. Werkt het niet? Niet verder gaan — eerst dit oplossen.

> 🔒 **Productie-tip:** voor een server die ook van buiten het beheernet
> bereikbaar is, schakel root + wachtwoord-auth ná de installatie uit en
> gebruik een admin-account met SSH-key. Dit stappenplan kiest voor de
> snelle weg (root + wachtwoord) omdat het in de meeste school-uitrollen
> om een server op een intern beheernet gaat.

---

## Stap 2 — Code op de server krijgen

Twee paden — kies wat past:

### Pad A — Git clone (aanbevolen, makkelijkste updates)

Vereist toegang tot de privé GitHub-repo via een **Deploy Key**.

🐧 **Server** — log in en genereer een SSH-key:

```bash
ssh -p "$SSH_PORT" "$SSH_USER@$SERVER_IP"
sudo -i                                          # word root
apt-get update && apt-get install -y git
ssh-keygen -t ed25519 -N "" -f /root/.ssh/id_ed25519 -C "kluisjes-deploy-$(hostname)"
cat /root/.ssh/id_ed25519.pub                    # ← kopieer deze regel
```

🌐 **In GitHub** (eenmalig per server):
- Ga naar `https://github.com/Rietbird/kluisjesbeheer/settings/keys`
- Klik *"Add deploy key"*
- Title: bv. `kluisjesbeheer-<schoolnaam>`
- Key: plak de regel uit `id_ed25519.pub`
- "Allow write access" UIT laten (read-only is genoeg)
- Klik *"Add key"*

🐧 **Server** — clone + installeer:

```bash
ssh-keyscan -t ed25519 github.com >> /root/.ssh/known_hosts
git clone git@github.com:Rietbird/kluisjesbeheer.git /root/kluisjesbeheer
cd /root/kluisjesbeheer
bash install.sh
```

**Update later** is dan triviaal:

```bash
cd /root/kluisjesbeheer && git pull && bash install.sh
```

### Pad B — Tarball (geen GitHub-toegang nodig)

🖥️ **Werkstation** — vanuit de kluisjesbeheer repo-root:

```bash
cd /c/Projects/kluisjesbeheer            # of jouw pad naar de repo
bash install/build-bundle.sh
```

Verwacht: `==> Klaar. .../install/dist/kluisjesbeheer-install.tgz`
(~150 KB, met "kern-bestanden OK"-rijtje). Kopieer naar de server:

```bash
scp -P "$SSH_PORT" \
    install/dist/kluisjesbeheer-install.tgz \
    "$SSH_USER@$SERVER_IP:/tmp/"
```

🐧 **Server** — log in, uitpakken, installeren:

```bash
ssh -p "$SSH_PORT" "$SSH_USER@$SERVER_IP"
sudo -i                                  # word root
cd /root
tar xzf /tmp/kluisjesbeheer-install.tgz
cd kluisjesbeheer-install
bash install.sh
```

---

## Stap 3 — Wat install.sh doet

Het script draait nu ~3-5 minuten. Aan het eind toont het:
- Pad naar `config.json`
- Het **uitgaande publieke IP** van de server (noteer dit — voor de
  SWP-whitelist)
- De vervolgstappen die hieronder staan

> 💡 Het script is **idempotent** — als er iets misgaat kun je 'm
> gewoon opnieuw draaien. `config.json` en de database worden nooit
> overschreven.

---

## Stap 4 — `config.json` invullen (doelserver, nog steeds root)

🐧 **Server**:

```bash
nano /opt/kluisjesbeheer/backend/config.json
```

Vervang de `VUL_IN_*`-velden:

| Veld | Waarde |
|---|---|
| `TenantId` | Entra Tenant-GUID |
| `ClientId` | Entra App Registration GUID |
| `ClientSecret` | Entra Client Secret |
| `RedirectUri` | bv. `https://kluisjes.intern.<school>.nl/auth/callback` |
| `AllowedOrigins` | lijst: `["https://kluisjes.intern.<school>.nl"]` |
| `SchoolNaam` | naam van de school (zichtbaar in UI) |
| `SchoolSubtitel` | optioneel |
| `SchoolLogo` | `/img/logo.png` (vervang via Beheer later) |
| `SchoolKleur` | hex, bv. `#0066CC` |

> ⚠️ `SecretKey` is al automatisch ingevuld — **NIET wijzigen** na
> gebruik (versleutelt het Magister-wachtwoord in de DB).

Opslaan (Ctrl+O, Enter, Ctrl+X) en herstarten:

```bash
systemctl restart kluisjesbeheer
systemctl status kluisjesbeheer --no-pager | head -5
curl -sS -o /dev/null -w "HTTP %{http_code}\n" http://127.0.0.1:5000/
```

Verwacht: `active (running)` + `HTTP 200`.

---

## Stap 5 — Reverse proxy of TLS regelen (door netwerkbeheer)

⚠️ **Aandachtspunt:** Entra ID vereist HTTPS voor de RedirectUri
(behalve `http://localhost`). Het installatiescript regelt **geen** TLS.

De netwerkbeheerder van de school moet één van twee regelen voordat
SSO werkt:

- **A.** Interne reverse-proxy (NGINX / IIS / F5) met intern CA-cert
  die `https://kluisjes.intern.<school>.nl` proxied naar
  `http://<server-ip>:5000`
- **B.** Publiek bereikbaar subdomein met Let's Encrypt, eveneens via
  reverse-proxy

De `RedirectUri` in `config.json` (stap 4) moet **exact** matchen met
wat in de Entra app-registration staat — dus eerst eens worden met de
Entra-beheerder welke URL gebruikt wordt.

---

## Stap 6 — Eerste login + Magister-koppeling (browser)

Open `https://kluisjes.intern.<school>.nl` (of de URL die in
`RedirectUri` staat) in een browser. Log in met een beheerderaccount.

> 🔑 De **eerste gebruiker die inlogt wordt automatisch beheerder**.
> Daarna kun je via *Beheer → Gebruikers* extra beheerders en
> conciërges toevoegen.

Ga naar **Beheer → Import → Magister-koppeling**:
- URL: `https://<jouwschool>.swp.nl:8800/doc`
- Account: het service-account (door de Magister-beheerder aangevraagd)
- Wachtwoord: het service-account-wachtwoord

Klik *Opslaan*. Het wachtwoord wordt versleuteld (Fernet / AES-128-CBC
+ HMAC) in de database opgeslagen.

---

## Stap 7 — IP-whitelist verifiëren (aangevraagd in 1.4)

🐧 **Server** — controleer dat het uitgaande IP nog hetzelfde is als
wat je in stap 1.4 hebt doorgegeven:

```bash
curl -s https://ifconfig.me ; echo
```

Wijkt het af van wat je gemaild hebt? Stuur de SWP-beheerder een
correctie. Bij verhuizing naar een ander netwerk moet de whitelist-
aanvraag herhaald worden.

> Niet aangevraagd in 1.4 (vergeten / overgeslagen)? Doe het nu —
> verwerking duurt 1-2 werkdagen.

---

## Stap 8 — Test de leerling-sync

🐧 **Server** (als root of via sudo):

```bash
sudo -u kluisjes /opt/kluisjesbeheer/.venv/bin/python /opt/kluisjesbeheer/backend/cron_sync.py
```

**Werkt het?** Verwachte output:
```
=== CRON MAGISTER LEERLINGEN SYNC ===
Magister-config uit database: https://<jouwschool>.swp.nl:8800/doc
1234 leerlingen opgehaald, 56 klassen
Database bijgewerkt. Done!
```

De cron staat al ingepland voor 06:00 dagelijks
(`/etc/cron.d/kluisjesbeheer-sync`).

**Werkt het niet?** Symptomen + oplossing:

| Melding | Oorzaak |
|---|---|
| `Geen verbinding met de Magister-webservice (poort 8800)` | IP-whitelist nog niet actief — vraag bij SWP na (stap 7) |
| `Medius login mislukt` | Verkeerd account/wachtwoord in *Beheer → Import* |
| `kan magister_pass niet ontsleutelen` | `SecretKey` in `config.json` is gewijzigd na het opslaan van het wachtwoord — vul het wachtwoord opnieuw in via de UI |

Test de netwerkverbinding los van credentials:
```bash
openssl s_client -connect <jouwschool>.swp.nl:8800 </dev/null 2>&1 | head -5
```
Krijg je geen TLS-handshake = poort dicht = whitelist niet actief.

---

## Stap 9 — Kluisjes importeren (eenmalig)

Excel-export uit Magister (kluisjesmodule) → uploaden via *Beheer →
Import* in kluisjesbeheer. Vestigingen en clusters worden automatisch
aangemaakt.

Bij kromme nummering (MO-1 / MO-100 / MO-1000): vink "kluisnummers
normaliseren" aan → wordt automatisch MO-0001 / MO-0100 / MO-1000.

---

## Onderhoud — daily commands

🐧 **Server**:

| Wat | Commando |
|---|---|
| Service-status | `systemctl status kluisjesbeheer` |
| App-logs (live) | `journalctl -u kluisjesbeheer -f` |
| Cron-logs | `tail -f /var/log/kluisjes-sync.log` |
| Herstarten | `systemctl restart kluisjesbeheer` |
| Backups | `ls -lt /opt/kluisjesbeheer/backend/backups/ \| head` |
| Handmatige backup | via app: *Beheer → Backup* |

---

## Updaten van een bestaande installatie

Zelfde procedure als stap 2-3:

🖥️ **Werkstation**:
```bash
cd /c/Projects/kluisjesbeheer
git pull                                 # nieuwste code
bash install/build-bundle.sh
scp -P "$SSH_PORT" install/dist/kluisjesbeheer-install.tgz "$SSH_USER@$SERVER_IP:/tmp/"
```

🐧 **Server**:
```bash
sudo -i
cd /root && rm -rf kluisjesbeheer-install
tar xzf /tmp/kluisjesbeheer-install.tgz
cd kluisjesbeheer-install
bash install.sh
```

`config.json` en database blijven onaangeroerd; code wordt vervangen,
frontend opnieuw gebouwd, service herstart.

---

## Troubleshooting tijdens uitrol

| Symptoom | Oplossing |
|---|---|
| `scp`: "Connection refused" | Check `SSH_PORT` (22 vs 2222) en `systemctl status ssh` op de server |
| `scp`: "Permission denied" | Wachtwoord-auth uit / wrong user / `PermitRootLogin` niet op `yes` (stap 1.4) |
| `bash install.sh`: crasht direct | Vergeten `cd kluisjesbeheer-install`? Pwd moet eindigen op `/kluisjesbeheer-install` |
| `npm ci` faalt | Geen internet naar `registry.npmjs.org` — proxy/firewall check |
| Service start niet (`failed`) | `journalctl -u kluisjesbeheer -n 50` — meestal ontbreekt een veld in `config.json` of klopt `RedirectUri` niet |
| Browser: `redirect_uri_mismatch` | `RedirectUri` in `config.json` moet **letterlijk** matchen met de URL in de Entra app-registration |
| Browser: blanco pagina, geen errors | Frontend build leeg — `cd /opt/kluisjesbeheer/frontend && npm run build` met foutmelding tonen |

Voor diepere problemen: `journalctl -u kluisjesbeheer -n 200 --no-pager`
+ `tail -50 /var/log/kluisjes-sync.log`.

---

## Voor school-IT (overhandig na uitrol)

Geef hen:
1. `install/dist/kluisjesbeheer-install.tgz` — voor toekomstige updates
2. `docs/installatie-vmware.md` — uitgebreide handleiding (hun versie)
3. De `RedirectUri` die je in `config.json` hebt gezet (moeten ze in
   de Entra app-registration controleren)
4. Het uitgaande server-IP — voor whitelisting bij SWP
