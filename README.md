# ip-toolkit

> Suite d'outils IP CLI — info, DNS, reverse, ping, sweep, scan, traceroute — pur Python stdlib

![Python](https://img.shields.io/badge/Python-3.8%2B-blue?logo=python&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey)

## Fonctionnalités

| Sous-commande | Description |
|---------------|-------------|
| `info` | Détails complets d'une IP (version, privé/public, loopback, hex, binaire) ou hostname |
| `dns` | Résolution hostname → IP (IPv4 + IPv6) |
| `reverse` | Reverse DNS : IP → hostname (enregistrement PTR) |
| `ping` | Ping ICMP avec N paquets |
| `sweep` | Ping sweep sur un réseau /24 ou CIDR — multithreadé (64 workers) |
| `scan` | Port scan TCP connect avec banner grabbing et 30+ services connus |
| `trace` | Traceroute (tracert Windows / traceroute Linux) |

Pur Python stdlib — aucune dépendance externe.

## Installation

```bash
git clone https://github.com/fzazdbl/ip-toolkit.git
cd ip-toolkit
python iptool.py --help
```

## Utilisation

```bash
# Informations sur une IP
python iptool.py info 8.8.8.8

# Résolution DNS
python iptool.py dns google.com

# Reverse DNS
python iptool.py reverse 1.1.1.1

# Ping (4 paquets par défaut)
python iptool.py ping 192.168.1.1 --count 8

# Ping sweep d'un /24
python iptool.py sweep 192.168.1.0/24

# Port scan TCP (ports 1–1024)
python iptool.py scan 192.168.1.1

# Port scan personnalisé
python iptool.py scan 10.0.0.1 --ports 22,80,443,3389,8080

# Traceroute
python iptool.py trace 8.8.8.8
```

## Exemple — port scan

```
  PORT                 SERVICE              BANNER/INFO
  ──────────────────────────────────────────────────────────────────
  22                   SSH                  SSH-2.0-OpenSSH_8.9p1
  80                   HTTP                 HTTP/1.1 200 OK
  443                  HTTPS
  3306                 MySQL
```

## Options par sous-commande

| Commande | Option | Défaut | Description |
|----------|--------|--------|-------------|
| `ping` | `--count N` | `4` | Nombre de paquets ICMP |
| `scan` | `--ports` | `1-1024` | Plage de ports (ex: `22,80` ou `1-65535`) |
| Toutes | `--no-banner` | — | Désactiver la bannière ASCII |

## Auteur

**Mohamed Chahid Echattioui** — [@fzazdbl](https://github.com/fzazdbl)

## Licence

MIT
