# Installatie

Drie installatiepaden — kies wat past:

- **Proxmox helper-script** (snelste, all-in-one) — zie de [README](../README.md#1-proxmox-helper-script-snelste-all-in-one) of [docs/proxmox.md](proxmox.md).
- **Klassieke install op verse Debian-VM** (`git clone` + `bash install.sh`) — zie het uitgebreide stappenplan in [install/README.md](../install/README.md). Voor een uitgebreidere VMware-specifieke uitleg met Entra/SWP-context: [installatie-vmware.md](installatie-vmware.md).
- **Docker compose** — zie [docs/docker.md](docker.md).

## Wat `install.sh` voor je doet

- Installeert systeem-packages (Python, Node, NGINX, cron, sqlite3)
- Maakt app-gebruiker `kluisjes` aan
- Rolt code uit naar `/opt/kluisjesbeheer/`
- Zet Python venv op + installeert dependencies
- Bouwt de frontend (Vite)
- Genereert `config.json` met willekeurige SecretKey (alleen bij eerste run)
- Zet systemd-service op (poort 5000, autostart)
- Zet NGINX op met self-signed TLS-cert (poort 80→443 redirect)
- Plant cron voor dagelijkse Magister leerling-sync (06:00)
- Voert smoketest uit + toont uitgaand IP voor SWP-whitelist

Het script is **idempotent** — opnieuw draaien is veilig en overschrijft géén database of `config.json`.

## Na de install

1. `nano /opt/kluisjesbeheer/backend/config.json` — vul Entra-velden in (TenantId/ClientId/ClientSecret/RedirectUri/AllowedOrigins)
2. `systemctl restart kluisjesbeheer`
3. Open `https://<server-ip>/` in browser — **eerste login wordt automatisch beheerder**
4. Magister-koppeling instellen via Beheer → Import (URL + service-account + wachtwoord wordt versleuteld opgeslagen)
5. SWP-whitelist aanvragen voor het server-IP (voor poort 8800 naar Medius)

## Updaten van een bestaande installatie

Als je via `git clone` hebt geïnstalleerd:

```bash
cd /root/kluisjesbeheer
git pull
bash install.sh
```

`config.json` en de database blijven onaangeroerd; alleen code wordt vervangen, frontend wordt opnieuw gebouwd, service herstart automatisch.

Voor de tarball-flow en troubleshooting tijdens uitrol: zie [install/README.md](../install/README.md).

## Volgende stap

Eerste inrichting via de app: [Configuratie](configuratie.md).
