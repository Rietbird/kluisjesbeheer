# Kluisjesbeheer — Documentatie

Kluisjesbeheer is een webapplicatie voor het beheren van schoolkluisjes. Gebouwd als vervanging van de Magister kluismodule, met ondersteuning voor meerdere vestigingen, rolverdeling en automatische leerlingensynchronisatie.

## Inhoud

| Pagina | Beschrijving |
|--------|-------------|
| [Systeemeisen](systeemeisen.md) | Server, Entra ID en Magister API vereisten |
| [Installatie](installatie.md) | Drie installatiepaden (Proxmox helper / klassiek / Docker) + wat install.sh voor je doet |
| [Configuratie](configuratie.md) | Eerste gebruik via de app: instellingen, import, gebruikers |
| [Architectuur](architectuur.md) | Technisch overzicht, stack, database, encryptie |
| [Onderhoud](onderhoud.md) | Logs, updates, cronjobs, troubleshooting |

## Quickstart

```
1. Verse Debian 12/13 server (LXC of VM)
2. git clone https://github.com/Rietbird/kluisjesbeheer.git /root/kluisjesbeheer
3. cd /root/kluisjesbeheer && bash install.sh
   → installeert Python+Node+NGINX, bouwt frontend, zet systemd-service +
     self-signed TLS-cert + cron op, genereert config.json met random SecretKey
4. Vul Entra-velden in: nano /opt/kluisjesbeheer/backend/config.json
   → TenantId / ClientId / ClientSecret / RedirectUri / AllowedOrigins
5. systemctl restart kluisjesbeheer
6. Open https://<server-ip>/ → log in via Entra; eerste user = automatisch beheerder
7. Beheer → Import: Magister-koppeling instellen, daarna kluisjes-XLSX importeren
```

Zie [Installatie](installatie.md) voor de volledige stappen en alternatieve paden (Proxmox helper-script of Docker compose).
