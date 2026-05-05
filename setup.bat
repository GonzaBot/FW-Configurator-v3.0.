@echo off
:: Enterprise FW Configurator v3.0 - Windows Setup
echo [*] Iniciando configuracion para Windows...

:: 1. Verificar Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python no esta instalado o no esta en el PATH.
    exit /b 1
)

:: 2. Instalar Rich
echo [*] Instalando libreria Rich...
pip install rich

:: 3. Verificar Netsh
where netsh >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] netsh no esta disponible en este sistema.
    exit /b 1
)

echo.
echo [OK] Entorno de Windows preparado.
echo Ejecute: python enterprise_fw.py --help (Como Administrador)
exit /b 0