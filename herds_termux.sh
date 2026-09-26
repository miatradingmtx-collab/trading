#!/bin/bash
# ==============================================================================
# MIA HERDS CLI - Lanzador para Termux (Android) y Linux / macOS
# ==============================================================================
# Instrucciones en Termux:
# 1. pkg update && pkg install python git -y
# 2. pip install websockets
# 3. bash herds_termux.sh
# ==============================================================================

if ! command -v python3 &> /dev/null; then
    echo "[*] Instalando Python..."
    if command -v pkg &> /dev/null; then
        pkg install python -y
    elif command -v apt-get &> /dev/null; then
        sudo apt-get install python3 python3-pip -y
    fi
fi

# Instalar websockets si no está presente
python3 -c "import websockets" 2>/dev/null || pip install websockets --quiet

# Ejecutar CLI de Herds
python3 mia_herds_cli.py "$@"
