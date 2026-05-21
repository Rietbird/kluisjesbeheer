# Kluisjesbeheer op Proxmox — helper-script

Eén commando op je Proxmox host. Het script maakt automatisch een verse
Debian 12 LXC container aan, installeert kluisjesbeheer erin (klassiek
of via Docker) en geeft je het IP-adres + URL.

## Gebruik

Op de **Proxmox host** als root:

```bash
bash -c "$(curl -fsSL https://raw.githubusercontent.com/Rietbird/kluisjesbeheer/master/proxmox/install-ct.sh)"
```

Daarna kun je interactief kiezen:

1. **Installatie-modus** — klassiek (`install.sh` op de CT) of Docker (`docker compose` in de CT)
2. **CT-parameters** — CT-ID, hostname, cores, RAM, disk, storage, bridge
3. **Netwerk** — DHCP of statisch IP
4. **Privileged** — standaard onprivileged (aanbevolen)

Het script accepteert Enter voor alle defaults. Geschatte tijd:
- Klassiek: ~5 minuten (template download + install.sh)
- Docker: ~7 minuten (template + Docker-install + image build)

## Wat doet het script

1. **Pre-flight checks** — root op Proxmox host, `pct`+`pveam` aanwezig
2. **Debian 12 template** downloaden als die nog niet lokaal staat
3. **CT aanmaken** met opgegeven parameters (volgende vrije CT-ID, willekeurig root-wachtwoord)
4. **CT starten** + wachten tot netwerk up is
5. **Per modus:**
   - **Klassiek** → `git clone https://github.com/Rietbird/kluisjesbeheer.git` + `bash install.sh`
   - **Docker** → Docker repo + `apt install docker-ce` + `git clone` + `docker compose up -d --build`
6. **Eindrapport** met CT-IP, root-wachtwoord, app-URL, volgende stappen

## Defaults per modus

|  | Klassiek | Docker |
|---|---|---|
| Cores | 2 | 2 |
| RAM | 1024 MB | 2048 MB |
| Disk | 8 GB | 12 GB |
| Features | nesting=1 | nesting=1, keyctl=1 |
| Unprivileged | ja | ja |

De Docker-modus heeft meer RAM en disk nodig vanwege de Docker-daemon
en image-cache.

## Na de installatie

1. **Entra-credentials invullen** in `config.json` (commando staat in eindrapport)
2. **App-container/service herstarten**
3. **Browser openen** → eerste login = automatisch beheerder
4. **Magister-koppeling** invullen via *Beheer → Import*
5. **SWP IP-whitelist** aanvragen met het uitgaande IP

Het volledige eindrapport van het script geeft de exacte commando's
voor stappen 1-2 per modus.

## Voorbeelden

### Klassieke installatie met defaults

```
$ bash -c "$(curl -fsSL https://raw.githubusercontent.com/Rietbird/kluisjesbeheer/master/proxmox/install-ct.sh)"

  Proxmox helper-script — install-ct.sh

 ✓ Draait op Proxmox host
 ✓ Template aanwezig: debian-12-standard_12.12-1_amd64.tar.zst

Kies installatie-modus:
  1) Klassiek  — install.sh in de CT
  2) Docker    — docker compose stack in de CT
  Q) Stoppen
 > 1
 ✓ Modus: classic

Container-parameters (Enter = default)
 ? CT-ID [200]:
 ? Hostname [kluisjesbeheer]:
 ? Cores [2]:
 ? Memory (MB) [1024]:
 ? Disk (GB) [8]:
 ? Bridge [vmbr0]:
 ? Storage [local-lvm]:
 ? DHCP gebruiken voor IP-adres? [j]:
 ? Onprivileged container? [j]:

Samenvatting:
  CT-ID         : 200
  Hostname      : kluisjesbeheer
  Modus         : classic
  Cores / RAM   : 2 / 1024MB
  Disk          : 8GB op local-lvm
  Network       : vmbr0, dhcp

 ? Doorgaan met aanmaken? [j]: j
 > Container 200 aanmaken...
 ✓ Container aangemaakt + gestart
 > Wachten tot netwerk up is...
 ✓ Netwerk werkt
 > Container-IP: 192.168.1.50
 > Klassieke installatie via install.sh ...
 ✓ Klassieke installatie afgerond

================================================================
  Kluisjesbeheer geïnstalleerd in CT 200
================================================================
  App-URL  : https://192.168.1.50/
  ...
```

## Niet-interactief gebruik

Voor automation kun je antwoorden injecteren via stdin:

```bash
# Klassiek, alle defaults, DHCP, onprivileged, ja:
printf '1\n\n\n\n\n\n\n\nj\nj\nj\n' | bash <(curl -fsSL https://raw.githubusercontent.com/Rietbird/kluisjesbeheer/master/proxmox/install-ct.sh)
```

## Troubleshooting

| Symptoom | Oplossing |
|---|---|
| `'pct' niet gevonden` | Script draait niet op een Proxmox host — log eerst in op de host |
| `Geen Debian 12 template beschikbaar` | `pveam update` op de Proxmox host om de templates-lijst te verversen |
| `Netwerk komt niet up binnen 30s` | Check of de bridge bestaat (`ip link show vmbr0`), DHCP-server beschikbaar is, of VLAN-tag klopt |
| `install.sh in CT X is gefaald` | `pct enter X` + `tail -50 /root/kluisjesbeheer/install.log` (handmatig debuggen) |
| Apt-fouten in CT | CT heeft geen internet — check DNS (`pct exec X -- ping -c1 8.8.8.8`) en bridge-config |

Voor het verwijderen van een test-CT:

```bash
pct stop 200 && pct destroy 200 --purge
```
