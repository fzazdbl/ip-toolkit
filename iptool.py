#!/usr/bin/env python3
"""
iptool.py — Suite d'outils IP CLI (pur stdlib)
Auteur : Mohamed Chahid Echattioui (@fzazdbl)
"""

import argparse
import ipaddress
import os
import platform
import socket
import struct
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

# ── ANSI ──────────────────────────────────────────────────────────────────────
R = "\033[0m"
BOLD = "\033[1m"
RED = "\033[91m"
YEL = "\033[93m"
GRN = "\033[92m"
CYN = "\033[96m"
MAG = "\033[95m"
BLU = "\033[94m"
DIM = "\033[2m"


def c(text, code):
    return f"{code}{text}{R}"


def label(text):
    return c(f"  {text:<20}", BLU + BOLD)


# ── Connus TCP ─────────────────────────────────────────────────────────────────
KNOWN_PORTS = {
    21: "FTP", 22: "SSH", 23: "Telnet", 25: "SMTP", 53: "DNS",
    80: "HTTP", 110: "POP3", 111: "RPC", 135: "MSRPC", 139: "NetBIOS",
    143: "IMAP", 161: "SNMP", 389: "LDAP", 443: "HTTPS", 445: "SMB",
    465: "SMTPS", 587: "SMTP-TLS", 636: "LDAPS", 993: "IMAPS", 995: "POP3S",
    1433: "MSSQL", 1521: "Oracle", 2049: "NFS", 3306: "MySQL",
    3389: "RDP", 5432: "PostgreSQL", 5900: "VNC", 6379: "Redis",
    8080: "HTTP-Alt", 8443: "HTTPS-Alt", 8888: "Jupyter", 9200: "Elasticsearch",
    27017: "MongoDB",
}


def banner():
    print(f"""
{MAG}{BOLD}
  ██╗██████╗       ████████╗ ██████╗  ██████╗ ██╗      ██╗  ██╗██╗████████╗
  ██║██╔══██╗      ╚══██╔══╝██╔═══██╗██╔═══██╗██║      ██║ ██╔╝██║╚══██╔══╝
  ██║██████╔╝         ██║   ██║   ██║██║   ██║██║      █████╔╝ ██║   ██║
  ██║██╔═══╝          ██║   ██║   ██║██║   ██║██║      ██╔═██╗ ██║   ██║
  ██║██║              ██║   ╚██████╔╝╚██████╔╝███████╗ ██║  ██╗██║   ██║
  ╚═╝╚═╝              ╚═╝    ╚═════╝  ╚═════╝ ╚══════╝ ╚═╝  ╚═╝╚═╝   ╚═╝
{R}{CYN}  Suite d'outils IP  |  @fzazdbl{R}
""")


# ── info ──────────────────────────────────────────────────────────────────────
def cmd_info(args):
    target = args.target
    print(c(f"\n  ── Informations : {target} ──\n", YEL + BOLD))

    try:
        ip = ipaddress.ip_address(target)
        rows = [
            ("Adresse IP",   str(ip)),
            ("Version",      f"IPv{ip.version}"),
            ("Privée",       str(ip.is_private)),
            ("Loopback",     str(ip.is_loopback)),
            ("Multicast",    str(ip.is_multicast)),
            ("Global",       str(ip.is_global)),
        ]
        if ip.version == 4:
            packed = struct.pack("!I", int(ip))
            rows.append(("Entier",       str(int(ip))))
            rows.append(("Hex",          hex(int(ip))))
            rows.append(("Binaire",      ".".join(f"{b:08b}" for b in packed)))
        for k, v in rows:
            print(f"{label(k)}: {c(v, GRN)}")
    except ValueError:
        # C'est un hostname
        try:
            info = socket.getaddrinfo(target, None)
            seen = set()
            for res in info:
                ip_str = res[4][0]
                if ip_str not in seen:
                    seen.add(ip_str)
                    print(f"{label('IP résolue')}: {c(ip_str, GRN)}")
            # PTR
            try:
                host = socket.gethostbyaddr(list(seen)[0])[0]
                print(f"{label('Hostname')}: {c(host, CYN)}")
            except Exception:
                pass
        except socket.gaierror as e:
            print(c(f"  ✗ Résolution échouée : {e}", RED))
    print()


# ── dns ───────────────────────────────────────────────────────────────────────
def cmd_dns(args):
    host = args.target
    print(c(f"\n  ── DNS : {host} → IP ──\n", YEL + BOLD))
    try:
        results = socket.getaddrinfo(host, None)
        seen = set()
        for r in results:
            ip = r[4][0]
            fam = "IPv6" if r[0] == socket.AF_INET6 else "IPv4"
            if ip not in seen:
                seen.add(ip)
                print(f"  {c(fam, DIM):<20}  {c(ip, GRN + BOLD)}")
    except socket.gaierror as e:
        print(c(f"  ✗ {e}", RED))
    print()


# ── reverse ───────────────────────────────────────────────────────────────────
def cmd_reverse(args):
    ip = args.target
    print(c(f"\n  ── Reverse DNS : {ip} → Hostname ──\n", YEL + BOLD))
    try:
        hostname, aliases, _ = socket.gethostbyaddr(ip)
        print(f"{label('Hostname')}: {c(hostname, GRN + BOLD)}")
        for a in aliases:
            print(f"{label('Alias')}: {c(a, CYN)}")
    except socket.herror as e:
        print(c(f"  ✗ Pas d'enregistrement PTR : {e}", YEL))
    except socket.gaierror as e:
        print(c(f"  ✗ Erreur : {e}", RED))
    print()


# ── ping ──────────────────────────────────────────────────────────────────────
def cmd_ping(args):
    target = args.target
    count = getattr(args, "count", 4)
    print(c(f"\n  ── Ping : {target} ──\n", YEL + BOLD))

    system = platform.system().lower()
    if system == "windows":
        cmd = ["ping", "-n", str(count), target]
    else:
        cmd = ["ping", "-c", str(count), target]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        lines = (result.stdout or result.stderr or "").splitlines()
        for line in lines:
            if any(k in line.lower() for k in ("reply", "bytes", "time", "ttl", "rtt", "paquets", "packet", "ms", "loss", "perdu")):
                print(f"  {c(line, GRN)}")
            elif "unreachable" in line.lower() or "timed out" in line.lower() or "100%" in line:
                print(f"  {c(line, RED)}")
            else:
                print(f"  {DIM}{line}{R}")
    except subprocess.TimeoutExpired:
        print(c("  ✗ Timeout", RED))
    except FileNotFoundError:
        print(c("  ✗ Commande ping non trouvée", RED))
    print()


# ── sweep ─────────────────────────────────────────────────────────────────────
def ping_host(ip: str) -> tuple[str, bool]:
    system = platform.system().lower()
    if system == "windows":
        cmd = ["ping", "-n", "1", "-w", "500", ip]
    else:
        cmd = ["ping", "-c", "1", "-W", "1", ip]
    try:
        r = subprocess.run(cmd, capture_output=True, timeout=3)
        return ip, r.returncode == 0
    except Exception:
        return ip, False


def cmd_sweep(args):
    target = args.target
    # Autorise IP ou CIDR
    try:
        net = ipaddress.IPv4Network(target, strict=False)
    except ValueError:
        # Essaie en /24
        base = ".".join(target.split(".")[:3]) + ".0/24"
        try:
            net = ipaddress.IPv4Network(base, strict=False)
        except ValueError:
            print(c(f"  ✗ Cible invalide : {target}", RED))
            sys.exit(1)

    hosts = list(net.hosts())
    print(c(f"\n  ── Ping sweep : {net} ({len(hosts)} hôtes) ──\n", YEL + BOLD))

    alive = []
    with ThreadPoolExecutor(max_workers=64) as ex:
        futures = {ex.submit(ping_host, str(h)): str(h) for h in hosts}
        for fut in as_completed(futures):
            ip, up = fut.result()
            if up:
                alive.append(ip)
                print(f"  {c('●', GRN)} {c(ip, GRN + BOLD)}")

    print(c(f"\n  {len(alive)} hôte(s) actif(s) sur {len(hosts)}\n", CYN))


# ── scan ──────────────────────────────────────────────────────────────────────
def scan_port(ip: str, port: int, timeout: float = 1.0) -> tuple[int, bool, str]:
    try:
        with socket.create_connection((ip, port), timeout=timeout) as s:
            s.settimeout(1.0)
            banner_data = ""
            try:
                s.sendall(b"HEAD / HTTP/1.0\r\n\r\n")
                raw = s.recv(256)
                banner_data = raw.decode("utf-8", errors="replace").splitlines()[0][:80]
            except Exception:
                pass
            return port, True, banner_data
    except (ConnectionRefusedError, OSError, socket.timeout):
        return port, False, ""


def cmd_scan(args):
    target = args.target
    ports_arg = getattr(args, "ports", "1-1024")

    # Parser la plage de ports
    ports = []
    for part in ports_arg.split(","):
        if "-" in part:
            a, b = part.split("-", 1)
            ports.extend(range(int(a), int(b) + 1))
        else:
            ports.append(int(part))

    print(c(f"\n  ── Port scan TCP : {target} ─ {len(ports)} ports ──\n", YEL + BOLD))

    open_ports = []
    with ThreadPoolExecutor(max_workers=200) as ex:
        futures = {ex.submit(scan_port, target, p): p for p in ports}
        for fut in as_completed(futures):
            port, is_open, banner_str = fut.result()
            if is_open:
                open_ports.append((port, banner_str))

    open_ports.sort()

    if not open_ports:
        print(c("  Aucun port ouvert détecté.\n", YEL))
        return

    print(f"  {c('PORT', BLU + BOLD):<30} {c('SERVICE', BLU + BOLD):<20} {c('BANNER', BLU + BOLD)}")
    print(f"  {'─'*70}")
    for port, banner_str in open_ports:
        svc = KNOWN_PORTS.get(port, "?")
        banner_display = banner_str[:50] if banner_str else ""
        print(
            f"  {c(str(port), GRN + BOLD):<20} {c(svc, CYN):<20} {c(banner_display, DIM)}"
        )
    print(f"\n  {c(str(len(open_ports)), BOLD)} port(s) ouvert(s)\n")


# ── trace ─────────────────────────────────────────────────────────────────────
def cmd_trace(args):
    target = args.target
    print(c(f"\n  ── Traceroute : {target} ──\n", YEL + BOLD))

    system = platform.system().lower()
    if system == "windows":
        cmd = ["tracert", "-d", "-h", "30", target]
    else:
        cmd = ["traceroute", "-n", "-m", "30", target]

    try:
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        for line in proc.stdout:
            line = line.rstrip()
            if not line:
                continue
            if "*" in line:
                print(f"  {c(line, YEL)}")
            elif any(c_ in line for c_ in ["ms", "msec"]):
                print(f"  {c(line, GRN)}")
            else:
                print(f"  {DIM}{line}{R}")
        proc.wait()
    except FileNotFoundError:
        print(c(f"  ✗ tracert/traceroute non trouvé", RED))
    print()


# ── CLI ───────────────────────────────────────────────────────────────────────
def build_parser():
    p = argparse.ArgumentParser(
        prog="iptool",
        description="Suite d'outils IP CLI — pur Python stdlib",
    )
    p.add_argument("--no-banner", action="store_true")
    sub = p.add_subparsers(dest="command", required=True, metavar="<commande>")

    def add_target(sp, help_text="IP ou hostname cible"):
        sp.add_argument("target", help=help_text)

    # info
    s = sub.add_parser("info", help="Détails sur une IP ou hostname")
    add_target(s)

    # dns
    s = sub.add_parser("dns", help="Résolution hostname → IP")
    add_target(s, "Hostname à résoudre")

    # reverse
    s = sub.add_parser("reverse", help="Reverse DNS : IP → hostname")
    add_target(s, "IP à résoudre")

    # ping
    s = sub.add_parser("ping", help="Ping ICMP")
    add_target(s)
    s.add_argument("--count", "-c", type=int, default=4, help="Nombre de pings")

    # sweep
    s = sub.add_parser("sweep", help="Ping sweep d'un réseau /24 ou CIDR")
    add_target(s, "IP ou réseau CIDR (ex: 192.168.1.0/24)")

    # scan
    s = sub.add_parser("scan", help="Port scan TCP")
    add_target(s)
    s.add_argument("--ports", "-p", default="1-1024",
                   help="Plage de ports (ex: 22,80,443 ou 1-65535, défaut: 1-1024)")

    # trace
    s = sub.add_parser("trace", help="Traceroute")
    add_target(s)

    return p


COMMANDS = {
    "info": cmd_info,
    "dns": cmd_dns,
    "reverse": cmd_reverse,
    "ping": cmd_ping,
    "sweep": cmd_sweep,
    "scan": cmd_scan,
    "trace": cmd_trace,
}


def main():
    parser = build_parser()
    args = parser.parse_args()

    if not args.no_banner:
        banner()

    fn = COMMANDS.get(args.command)
    if fn:
        fn(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
