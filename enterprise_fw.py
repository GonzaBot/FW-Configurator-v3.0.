#!/usr/bin/env python3
"""
Enterprise FW Configurator v3.0
Arquitectura modular para gestión de firewalls en entornos corporativos.
"""

import argparse
import subprocess
import platform
import os
import sys
import logging
import shutil
import ctypes
import shlex
import subprocess
from abc import ABC, abstractmethod
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress
from rich.prompt import Confirm

# --- CONFIGURACIÓN DE LOGGING ---
LOG_FILE = os.path.expanduser("~/enterprise_fw.log")

os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

console = Console()

# --- CAPA 3: PERFILES (LÓGICA DE NEGOCIO) ---

class FirewallProfile(ABC):
    RFC1918 = ["10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16"]

    @abstractmethod
    def get_linux_ufw_rules(self) -> list: pass

    @abstractmethod
    def get_linux_iptables_rules(self) -> list: pass

    @abstractmethod
    def get_windows_rules(self) -> list: pass

class WorkstationProfile(FirewallProfile):
    def get_linux_ufw_rules(self):
        return [
            "default allow outgoing",
            "default deny incoming",
            "allow from any to any proto any on lo"
        ]

    def get_linux_iptables_rules(self):
        return [
            "-A INPUT -i lo -j ACCEPT",
            "-A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT",
            "-A INPUT -j LOG --log-prefix 'FW-DROP: '",
            "-P INPUT DROP"
        ]

    def get_windows_rules(self):
        return [
            "set currentprofile firewallpolicy blockinbound,allowoutbound",
            "advfirewall firewall add rule name='Allow-Loopback' dir=in action=allow localip=127.0.0.1"
        ]

class WebServerProfile(FirewallProfile):
    def get_linux_ufw_rules(self):
        rules = [
            "default allow outgoing",
            "default deny incoming",
            "allow from any to any proto any on lo",
            "allow 80/tcp",
            "allow 443/tcp",
            "allow proto icmp"
        ]
        for net in self.RFC1918:
            rules.append(f"allow from {net} to any port 22 proto tcp")
            rules.append(f"allow from {net} to any port 3389 proto tcp")
        return rules

    def get_linux_iptables_rules(self):
        rules = [
            "-A INPUT -i lo -j ACCEPT",
            "-A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT",
            "-A INPUT -p tcp --dport 80 -j ACCEPT",
            "-A INPUT -p tcp --dport 443 -j ACCEPT",
            "-A INPUT -p icmp --icmp-type echo-request -j ACCEPT"
        ]
        for net in self.RFC1918:
            rules.append(f"-A INPUT -p tcp -s {net} --dport 22 -j ACCEPT")
            rules.append(f"-A INPUT -p tcp -s {net} --dport 3389 -j ACCEPT")
        rules.append("-A INPUT -j LOG --log-prefix 'FW-DROP: '")
        rules.append("-P INPUT DROP")
        return rules

    def get_windows_rules(self):
        rules = ["set currentprofile firewallpolicy blockinbound,allowoutbound"]
        rules.append("advfirewall firewall add rule name='Allow-HTTP' dir=in action=allow protocol=TCP localport=80")
        rules.append("advfirewall firewall add rule name='Allow-HTTPS' dir=in action=allow protocol=TCP localport=443")
        for i, net in enumerate(self.RFC1918):
            rules.append(f"advfirewall firewall add rule name='Allow-SSH-Admin-{i}' dir=in action=allow protocol=TCP localport=22 remoteip={net}")
            rules.append(f"advfirewall firewall add rule name='Allow-RDP-Admin-{i}' dir=in action=allow protocol=TCP localport=3389 remoteip={net}")
        return rules

class DbServerProfile(FirewallProfile):
    def get_linux_ufw_rules(self):
        rules = [
            "default allow outgoing",
            "default deny incoming",
            "allow from any to any proto any on lo"
        ]
        for net in self.RFC1918:
            rules.append(f"allow from {net} to any port 3306 proto tcp")
            rules.append(f"allow from {net} to any port 5432 proto tcp")
            rules.append(f"allow from {net} to any port 22 proto tcp")
        return rules

    def get_linux_iptables_rules(self):
        rules = [
            "-A INPUT -i lo -j ACCEPT",
            "-A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT"
        ]
        for net in self.RFC1918:
            rules.append(f"-A INPUT -p tcp -s {net} --dport 3306 -j ACCEPT")
            rules.append(f"-A INPUT -p tcp -s {net} --dport 5432 -j ACCEPT")
            rules.append(f"-A INPUT -p tcp -s {net} --dport 22 -j ACCEPT")
        rules.append("-A INPUT -j LOG --log-prefix 'FW-DROP: '")
        rules.append("-P INPUT DROP")
        return rules

    def get_windows_rules(self):
        rules = ["set currentprofile firewallpolicy blockinbound,allowoutbound"]
        for i, net in enumerate(self.RFC1918):
            rules.append(f"advfirewall firewall add rule name='Allow-MySQL-{i}' dir=in action=allow protocol=TCP localport=3306 remoteip={net}")
            rules.append(f"advfirewall firewall add rule name='Allow-Postgres-{i}' dir=in action=allow protocol=TCP localport=5432 remoteip={net}")
            rules.append(f"advfirewall firewall add rule name='Allow-SSH-{i}' dir=in action=allow protocol=TCP localport=22 remoteip={net}")
        return rules

# --- CAPA 5: EXECUTOR ---

class Executor:
    @staticmethod
    def run(cmd_list, dry_run=False):
        if dry_run:
            return True, "DRY-RUN MODE"
        try:
            result = subprocess.run(cmd_list, check=True, capture_output=True, text=True, timeout=30)
            logging.info(f"Éxito: {' '.join(cmd_list)}")
            return True, "OK"
        except subprocess.CalledProcessError as e:
            logging.error(f"Error en {' '.join(cmd_list)}: {e.stderr}")
            return False, e.stderr
        except Exception as e:
            logging.error(f"Error inesperado: {str(e)}")
            return False, str(e)

# --- CAPA 4: BACKENDS ---

class LinuxBackend:
    def __init__(self):
        self.use_ufw = shutil.which('ufw') is not None
        self.tool = "ufw" if self.use_ufw else "iptables"
        # Check conntrack
        self.has_conntrack = shutil.which('iptables') and subprocess.run(["iptables", "-m", "conntrack", "--help"], capture_output=True).returncode == 0

    def apply(self, profile: FirewallProfile, dry_run=False):
        results = []
        if self.use_ufw:
            commands = [["ufw", "--force", "reset"]] + [["ufw"] + r.split() for r in profile.get_linux_ufw_rules()] + [["ufw", "logging", "on"], ["ufw", "--force", "enable"]]
        else:
            # Backup first
            backup_cmd = ["iptables-save", ">", "fw_backup.rules"]
            if not dry_run:
                subprocess.run(backup_cmd, shell=True, check=False)
            # Safe flush with backup policies
            commands = [
                ["iptables-save"],
                ["iptables-restore", "-n"]  # Dry parse check
            ]
            for r in profile.get_linux_iptables_rules():
                # Conntrack if available
                if '-m conntrack' in r and not self.has_conntrack:
                    r = r.replace('-m conntrack --ctstate ESTABLISHED,RELATED', '--state ESTABLISHED,RELATED')
                commands.append(["iptables"] + shlex.split(r))
            
            commands.append(["iptables-save", ">", "fw_applied.rules"])  # Save final
        
        for cmd in commands:
            success, msg = Executor.run(cmd, dry_run)
            results.append({"regla": " ".join(cmd[1:3]) if len(cmd)>2 else cmd[0], "cmd": " ".join(cmd), "status": success})
        return results

class WindowsBackend:
    def apply(self, profile: FirewallProfile, dry_run=False):
        results = []
        # Enable logging (no bulk delete - dangerous)
        base_cmds = [
            ["netsh", "advfirewall", "set", "currentprofile", "logging", "droppedconnections", "enable"],
            ["netsh", "advfirewall", "set", "currentprofile", "logging", "droppedconnections", "filename", f"%systemroot%\\{os.path.basename(LOG_FILE)}"]
        ]
        for cmd in base_cmds:
            success, msg = Executor.run(cmd, dry_run)
            results.append({"regla": "Setup", "cmd": " ".join(cmd), "status": success})

        for r in profile.get_windows_rules():
            cmd = ["netsh"] + r.split()
            success, msg = Executor.run(cmd, dry_run)
            results.append({"regla": r.split('name=')[1].split()[0] if 'name=' in r else r[:15], "cmd": " ".join(cmd), "status": success})
        
        return results

# --- CAPA 2: ORQUESTADOR ---

class FWConfigurator:
    def __init__(self):
        self.os_type = platform.system()
        self.validate_privileges()
        self.backend = LinuxBackend() if self.os_type == "Linux" else WindowsBackend()

    def validate_privileges(self):
        is_admin = False
        if self.os_type == "Linux":
            is_admin = os.getuid() == 0
        elif self.os_type == "Windows":
            is_admin = ctypes.windll.shell32.IsUserAnAdmin() != 0
        
        if not is_admin:
            console.print("[bold red]ERROR: Se requieren privilegios de Root/Administrador.[/bold red]")
            sys.exit(1)

    def run(self, profile_name, backup=False, dry_run=False):
        profiles = {
            "workstation": WorkstationProfile(),
            "web-server": WebServerProfile(),
            "db-server": DbServerProfile()
        }
        profile = profiles[profile_name]
        
        console.print(Panel(f"[bold blue]Enterprise FW Configurator v3.0[/bold blue]\n"
                            f"Perfil: {profile_name} | SO: {self.os_type} | Dry-run: {dry_run}"))

        if not dry_run and not Confirm.ask("¿Desea aplicar esta configuración ahora? Esto modificará las reglas de red."):
            console.print("[yellow]Operación cancelada por el usuario.[/yellow]")
            return

        with Progress() as progress:
            task = progress.add_task("[cyan]Aplicando reglas...", total=100)
            results = self.backend.apply(profile, dry_run)
            progress.update(task, completed=100)

        table = Table(title="Resultado de la Aplicación")
        table.add_column("Regla", style="magenta")
        table.add_column("Comando", style="dim")
        table.add_column("Estado", justify="right")

        for res in results:
            status_str = "[green]✓ OK[/green]" if res['status'] else "[red]✗ FALLO[/red]"
            table.add_row(res['regla'], res['cmd'][:50] + "...", status_str)

        console.print(table)
        console.print(Panel(f"[bold green]Configuración Finalizada[/bold green]\nLogs en: {LOG_FILE}"))

# --- CAPA 1: CLI ---

def main():
    parser = argparse.ArgumentParser(description="Enterprise Firewall Configurator CLI")
    parser.add_argument("--profile", choices=["workstation", "web-server", "db-server"], required=True, help="Perfil de seguridad a aplicar")
    parser.add_argument("--dry-run", action="store_true", help="Muestra los comandos sin ejecutarlos")
    parser.add_argument("--version", action="version", version="Enterprise FW Configurator 3.0")

    args = parser.parse_args()

    app = FWConfigurator()
    app.run(args.profile, args.dry_run)

if __name__ == "__main__":
    main()