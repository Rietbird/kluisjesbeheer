# Kluisjesbeheer — uitrol-stappenplan

Voor jezelf (Vincent). Stap-voor-stap copy-paste vanaf een **kale Debian
12/13 installatie** tot een draaiende app.

> 📋 **Werkwijze:** vul stap 0 één keer in (variabelen), daarna kun je de
> commando's letterlijk plakken in de juiste shell. Markering:
> 🖥️ = jouw werkstation · 🐧 = Demo-server (via console of SSH).

---

## Stap 0 — variabelen invullen (eenmalig)

Bepaal vooraf en houd bij de hand. Pas de waarden ná `export` aan voor
jouw situatie en plak deze export-blokken in de juiste shell **voor je
verder gaat**.

🖥️ **Werkstation** (Git Bash / WSL):

```bash
export SERVER_IP="10.x.x.x"             # IP van de Demo-VM
export SSH_PORT="22"                    # of 2222 als poort 22 geblokkeerd is
export SSH_USER="root"                  # of debian / Demo
```

🐧 **Demo-server** (in de console-sessie zodra je ingelogd bent):

```bash
export ADMIN_USER="Demo"             # nieuw aan te maken admin-account
                                        # (als de VM al een sudo-user heeft, sla 1.4-1.6 over)
```

---

## Stap 1 — Kale Debian voorbereiden (op de Demo-server)

> Demo levert een verse Debian 12/13 VM op via VMware. Vermoedelijk
> alleen root-toegang via de console (geen SSH nog).

### 1.1 Op de VMware-console: inloggen en netwerk verifiëren

Log in als `root` op de console van de VM. Eerste check:

```bash
ip -4 addr show | grep inet
ping -c 2 8.8.8.8
cat /etc/debian_version
```

Je moet zien: een statisch intern IP, werkende internetverbinding, en
versie `12.x` of `13.x`. Werkt internet niet, los dat eerst op met
Demo IT — verder zonder internet kan niet (apt + npm-install).

### 1.2 Apt updaten + basistools installeren

```bash
apt-get update && apt-get upgrade -y
apt-get install -y openssh-server sudo curl nano less ca-certificates
```

### 1.3 SSH-daemon controleren / starten

```bash
systemctl enable --now ssh
systemctl status ssh --no-pager | head -3
ss -tlnp | grep :22 || echo "ssh luistert NIET op poort 22"
```

> Als Demo poort 22 geblokkeerd heeft en je 2222 wilt: bewerk
> `/etc/ssh/sshd_config`, regel `#Port 22` → `Port 2222`, dan
> `systemctl restart ssh`. Update dan ook `SSH_PORT` in stap 0.

### 1.4 Admin-account aanmaken (alleen als de VM nog geen sudo-user heeft)

```bash
adduser "$ADMIN_USER"                   # vraagt om wachtwoord
usermod -aG sudo "$ADMIN_USER"
```

### 1.5 SSH key-based login aanzetten voor `$ADMIN_USER`

Veiliger en handiger dan steeds een wachtwoord typen.

🖥️ **Werkstation** — public key vinden (of nieuw genereren):

```bash
ls -la ~/.ssh/id_*.pub 2>/dev/null || ssh-keygen -t ed25519 -C "vincent-werkstation"
cat ~/.ssh/id_ed25519.pub             # kopieer de hele regel
```

🐧 **Server** — public key plakken in `authorized_keys`:

```bash
mkdir -p /home/$ADMIN_USER/.ssh
nano /home/$ADMIN_USER/.ssh/authorized_keys
# plak de regel uit ~/.ssh/id_ed25519.pub, sla op (Ctrl+O, Enter, Ctrl+X)
chmod 700 /home/$ADMIN_USER/.ssh
chmod 600 /home/$ADMIN_USER/.ssh/authorized_keys
chown -R "$ADMIN_USER:$ADMIN_USER" /home/$ADMIN_USER/.ssh
```

### 1.6 (Optioneel maar aanbevolen) Root-login over SSH uitschakelen

```bash
sed -i 's/^#*PermitRootLogin.*/PermitRootLogin no/' /etc/ssh/sshd_config
sed -i 's/^#*PasswordAuthentication.*/PasswordAuthentication no/' /etc/ssh/sshd_config
systemctl restart ssh
```

> ⚠️ Doe deze stap **pas nadat je hebt getest dat key-based login als
> `$ADMIN_USER` werkt** (volgende stap), anders sluit je jezelf buiten.

### 1.7 SSH-verbinding testen vanaf je werkstation

🖥️ **Werkstation**:

```bash
ssh -p "$SSH_PORT" "$ADMIN_USER@$SERVER_IP" "echo 'SSH werkt'; cat /etc/debian_version"
```

Verwacht: `SSH werkt` + versie-nummer. Werkt het? Door naar stap 2.
Werkt het niet? Niet verder gaan — eerst dit oplossen.

---

## Stap 2 — Tarball bouwen en kopiëren (werkstation)

🖥️ **Werkstation** — vanuit de kluisjesbeheer repo-root:

```bash
cd /c/Projects/kluisjesbeheer            # of jouw pad naar de repo
bash install/build-bundle.sh
```

Verwacht: `==> Klaar. .../install/dist/kluisjesbeheer-install.tgz`
(~150 KB, met "kern-bestanden OK"-rijtje).

Kopieer naar de server:

```bash
scp -P "$SSH_PORT" \
    install/dist/kluisjesbeheer-install.tgz \
    "$ADMIN_USER@$SERVER_IP:/tmp/"
```

---

## Stap 3 — Installatiescript draaien (Demo-server)

🐧 **Server** — log in via SSH:

```bash
ssh -p "$SSH_PORT" "$ADMIN_USER@$SERVER_IP"
```

Eenmaal binnen — naar root + uitpakken + installeren:

```bash
sudo -i                                  # word root
cd /root
tar xzf /tmp/kluisjesbeheer-install.tgz
cd kluisjesbeheer-install
bash install.sh
```

Het script draait nu ~3-5 minuten. Aan het eind toont het:
- Pad naar `config.json`
- Het **uitgaande publieke IP** van de server (noteer dit — voor de
  SWP-whitelist)
- De vervolgstappen die hieronder staan

> 💡 Het script is **idempotent** — als er iets misgaat kun je 'm
> gewoon opnieuw draaien. `config.json` en de database worden nooit
> overschreven.

---

## Stap 4 — `config.json` invullen (Demo-server, nog steeds root)

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
| `DashboardGroupId` | Entra-groep-GUID met toegang |
| `RedirectUri` | bv. `https://kluisjes.intern.Demo.nl/auth/callback` |
| `AllowedOrigins` | lijst: `["https://kluisjes.intern.Demo.nl"]` |
| `SchoolNaam` | `OSG Demo` (of wat zij willen) |
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

## Stap 5 — Reverse proxy of TLS regelen (door Demo netwerkbeheer)

⚠️ **Aandachtspunt:** Entra ID vereist HTTPS voor de RedirectUri
(behalve `http://localhost`). Het installatiescript regelt **geen** TLS.

Demo netwerkbeheer moet één van twee regelen voordat SSO werkt:

- **A.** Interne reverse-proxy (NGINX / IIS / F5) met intern CA-cert
  die `https://kluisjes.intern.Demo.nl` proxied naar
  `http://<server-ip>:5000`
- **B.** Publiek bereikbaar subdomein met Let's Encrypt, eveneens via
  reverse-proxy

De `RedirectUri` in `config.json` (stap 4) moet **exact** matchen met
wat in de Entra app-registration staat — dus eerst eens worden met
Entra-beheerder welke URL gebruikt wordt.

---

## Stap 6 — Eerste login + Magister-koppeling (browser)

Open `https://kluisjes.intern.Demo.nl` (of de URL die in
`RedirectUri` staat) in een browser. Log in met een beheerderaccount.

> 🔑 De **eerste gebruiker die inlogt wordt automatisch beheerder**.
> Daarna kun je via *Beheer → Gebruikers* extra beheerders en
> conciërges toevoegen.

Ga naar **Beheer → Import → Magister-koppeling**:
- URL: `https://school.swp.nl:8800/doc`
- Account: het service-account (door Demo aangevraagd)
- Wachtwoord: het service-account-wachtwoord

Klik *Opslaan*. Het wachtwoord wordt versleuteld (Fernet / AES-128-CBC
+ HMAC) in de database opgeslagen.

---

## Stap 7 — IP-whitelist bij SWP aanvragen

🐧 **Server** — bepaal het uitgaande IP (stond ook in het script-rapport):

```bash
curl -s https://ifconfig.me
```

Geef dit IP-adres door aan de Magister-/SWP-beheerder van Demo
met het verzoek: *"Whitelisten voor toegang tot
`school.swp.nl` op poort 8800."*

Bij verhuizing naar een ander netwerk moet dit opnieuw aangevraagd
worden.

---

## Stap 8 — Test de leerling-sync

🐧 **Server** (als root of via sudo):

```bash
sudo -u kluisjes /opt/kluisjesbeheer/.venv/bin/python /opt/kluisjesbeheer/backend/cron_sync.py
```

**Werkt het?** Verwachte output:
```
=== CRON MAGISTER LEERLINGEN SYNC ===
Magister-config uit database: https://school.swp.nl:8800/doc
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
openssl s_client -connect school.swp.nl:8800 </dev/null 2>&1 | head -5
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
scp -P "$SSH_PORT" install/dist/kluisjesbeheer-install.tgz "$ADMIN_USER@$SERVER_IP:/tmp/"
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
| `scp`: "Permission denied (publickey)" | SSH-key nog niet in `authorized_keys` (stap 1.5) of `PasswordAuthentication no` zonder key (stap 1.6) |
| `bash install.sh`: crasht direct | Vergeten `cd kluisjesbeheer-install`? Pwd moet eindigen op `/kluisjesbeheer-install` |
| `npm ci` faalt | Geen internet naar `registry.npmjs.org` — proxy/firewall check |
| Service start niet (`failed`) | `journalctl -u kluisjesbeheer -n 50` — meestal ontbreekt een veld in `config.json` of klopt `RedirectUri` niet |
| Browser: `redirect_uri_mismatch` | `RedirectUri` in `config.json` moet **letterlijk** matchen met de URL in de Entra app-registration |
| Browser: blanco pagina, geen errors | Frontend build leeg — `cd /opt/kluisjesbeheer/frontend && npm run build` met foutmelding tonen |

Voor diepere problemen: `journalctl -u kluisjesbeheer -n 200 --no-pager`
+ `tail -50 /var/log/kluisjes-sync.log`.

---

## Voor Demo IT (overhandig na uitrol)

Geef hen:
1. `install/dist/kluisjesbeheer-install.tgz` — voor toekomstige updates
2. `docs/installatie-vmware.md` — uitgebreide handleiding (hun versie)
3. De `RedirectUri` die je in `config.json` hebt gezet (moeten ze in
   de Entra app-registration controleren)
4. Het uitgaande server-IP — voor whitelisting bij SWP
