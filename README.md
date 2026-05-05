
# Enterprise FW Configurator v3.0 🌐🔒

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/Platform-Linux%20%7C%20Windows-green.svg)](#)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 📖 Overview

**Enterprise FW Configurator v3.0** is a production-grade CLI tool designed to securely deploy firewall configurations across Linux and Windows environments using predefined security profiles.

It enforces **role-based firewall policies**, ensuring each system receives a configuration aligned with its real-world role:

* Workstation
* Web Server
* Database Server

> ⚠️ Built with DevSecOps principles: security, auditability, and operational safety (zero downtime).

---

## 🎯 Key Features

* 🔐 Role-based firewall profiles
* ⚙️ Cross-platform support:

  * Linux: `ufw` (preferred) / `iptables` (fallback)
  * Windows: `netsh advfirewall`
* 🧠 Safe rule ordering (prevents lockouts)
* 💾 Backup support (iptables)
* 🧪 Dry-run mode
* 📜 Centralized logging
* 🎨 Rich CLI interface (tables, progress bars)

---

## 🧱 Architecture

```
CLI → Orchestrator → Profiles → Backends → Executor
```

### Layers

1. CLI (argparse + rich)
2. Orchestrator (OS detection + privileges)
3. Profiles (business logic)
4. Backends (Linux / Windows)
5. Executor (secure command execution)

---

## 🔐 Security Model

| Profile     | Security Level | Description                |
| ----------- | -------------- | -------------------------- |
| workstation | 🔴 ~95%        | Blocks all inbound traffic |
| web-server  | 🟡 ~80%        | Exposes HTTP/HTTPS only    |
| db-server   | 🟢 ~90%        | Internal access only       |

---

## 🌐 RFC1918 Networks

Admin access is restricted to:

* 10.0.0.0/8
* 172.16.0.0/12
* 192.168.0.0/16

---

## 📦 Installation

### Linux

```bash
chmod +x setup.sh
./setup.sh
```

### Windows

```cmd
setup.bat
```

---

## 🚀 Usage

### Help

```bash
python3 enterprise_fw.py --help
```

---

### Dry Run (RECOMMENDED)

```bash
sudo python3 enterprise_fw.py --profile workstation --dry-run
```

---

### Apply Configuration

```bash
sudo python3 enterprise_fw.py --profile workstation
```

---

# 🧭 Profile Usage Guide (IMPORTANT)

Elegir bien el perfil **es lo más importante de toda la herramienta**.

> ❗ Si elegís mal el perfil, podés romper el acceso o abrir vulnerabilidades.

---

## 🖥️ workstation — Máxima seguridad (~95%)

### ✅ Usar cuando:

* PC personal
* Laptop
* Equipo de oficina
* Máquina de desarrollo
* Cualquier equipo que NO deba recibir conexiones

### 🔐 Qué hace:

* Permite tráfico saliente
* Permite conexiones establecidas
* Bloquea TODO el tráfico entrante

### 🧠 Mentalidad:

> “Esta máquina usa servicios, no los ofrece”

### ❌ NO usar si:

* Necesitás conectarte por SSH
* Corre un servidor

### 💻 Ejemplo

```bash
sudo python3 enterprise_fw.py --profile workstation
```

---

## 🌍 web-server — Exposición controlada (~80%)

### ✅ Usar cuando:

* Tenés una web pública
* API pública
* Servidor accesible desde internet

### 🔐 Qué hace:

* Abre:

  * 80 (HTTP)
  * 443 (HTTPS)
* Permite:

  * ICMP (ping)
  * SSH (22) desde red interna
  * RDP (3389) desde red interna
* Bloquea todo lo demás

### 🧠 Mentalidad:

> “Expongo lo necesario, administro desde adentro”

### ❌ NO usar si:

* Es una PC personal
* Es un servidor de base de datos

### 💻 Ejemplo

```bash
sudo python3 enterprise_fw.py --profile web-server
```

---

## 🗄️ db-server — Solo red interna (~90%)

### ✅ Usar cuando:

* Servidor MySQL o PostgreSQL
* Backend interno
* Infraestructura privada

### 🔐 Qué hace:

* Permite:

  * MySQL (3306) desde red interna
  * PostgreSQL (5432) desde red interna
  * SSH (22) desde red interna
* Bloquea TODO acceso desde internet

### 🧠 Mentalidad:

> “Los datos nunca deben estar expuestos”

### ❌ NO usar si:

* Necesitás acceso público (mala práctica igual)

### 💻 Ejemplo

```bash
sudo python3 enterprise_fw.py --profile db-server
```

---

## 🧠 Cómo elegir rápido

| Pregunta                           | Perfil      |
| ---------------------------------- | ----------- |
| ¿Recibe conexiones de internet? NO | workstation |
| ¿Es una web pública?               | web-server  |
| ¿Solo acceso interno?              | db-server   |

---

## ⚠️ Errores comunes

### ❌ workstation en servidor

→ Rompe acceso

### ❌ web-server en PC

→ Abre puertos innecesarios

### ❌ DB expuesta a internet

→ Riesgo crítico de seguridad

---

## 🔁 Flujo recomendado

```bash
# 1. Simular
sudo python3 enterprise_fw.py --profile web-server --dry-run

# 2. Revisar

# 3. Aplicar
sudo python3 enterprise_fw.py --profile web-server
```

---

## 🧩 Escenarios reales

### Empresa

| Equipo        | Perfil      |
| ------------- | ----------- |
| PCs empleados | workstation |
| Servidor web  | web-server  |
| Base de datos | db-server   |

---

### Cloud

| Componente | Perfil     |
| ---------- | ---------- |
| Frontend   | web-server |
| Backend    | web-server |
| DB         | db-server  |

---

## 🔄 Restore

```bash
sudo iptables-restore fw_backup.rules
```

---

## 📜 Logs

```bash
tail -f ~/enterprise_fw.log
```

---

## ⚠️ Advertencias

* Requiere root/admin
* Siempre usar dry-run
* Mala configuración = pérdida de acceso

---

## ✅ Verificación

```bash
sudo iptables -L -v -n
```

o

```bash
sudo ufw status verbose
```

---

## 📈 Contribuir

1. Fork
2. Branch
3. Commit
4. Push
5. PR

---

## 📄 Licencia

MIT License

---

## 🧠 Final

Este proyecto no es solo un script.

Es una forma de:

* Reducir errores humanos
* Estandarizar seguridad
* Aplicar buenas prácticas reales

>
