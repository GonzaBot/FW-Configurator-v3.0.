#!/bin/bash
# Enterprise FW Configurator v3.0 - Linux Setup
set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

echo -e "${GREEN}[*] Iniciando instalación de Enterprise FW Configurator...${NC}"

# 1. Detectar Distro y actualizar paquetes
if command -v apt-get &>/dev/null; then
    echo -e "[*] Detectado sistema basado en Debian/Ubuntu"
    sudo apt-get update -y
    sudo apt-get install -y python3 python3-pip python3-venv iptables ufw
elif command -v dnf &>/dev/null; then
    echo -e "[*] Detectado sistema basado en RHEL/CentOS/Fedora"
    sudo dnf install -y python3 python3-pip iptables
else
    echo -e "${RED}[!] Gestor de paquetes no soportado automáticamente. Instale python3 y pip manualmente.${NC}"
fi

# 2. Instalar dependencias de Python
echo -e "[*] Instalando librería Rich..."
# Se usa --break-system-packages para entornos modernos de Python (PEP 668) 
# o se asume ejecución en entorno controlado.
python3 -m pip install rich --break-system-packages || python3 -m pip install rich

# 3. Verificar herramientas de red
echo -e "[*] Verificando backends de red..."
if command -v iptables &>/dev/null; then
    echo -e "  - iptables: ${GREEN}OK${NC}"
else
    echo -e "  - iptables: ${RED}NO ENCONTRADO${NC}"
fi

if command -v ufw &>/dev/null; then
    echo -e "  - ufw: ${GREEN}OK${NC}"
else
    echo -e "  - ufw: ${RED}NO ENCONTRADO (Opcional)${NC}"
fi

echo -e "\n${GREEN}✔ Resumen: Entorno preparado correctamente.${NC}"
echo -e "Ejecute: sudo python3 enterprise_fw.py --help"
exit 0