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

# Sincronizar última versión de la Malla 7 Herds evitando caché de APN / CDN
if command -v ip &> /dev/null; then
    ip neigh flush all 2>/dev/null || true
fi

echo "[*] Sincronizando Malla de 7 Herds (Bypass APN Cache)..."
curl -sL -H "Cache-Control: no-cache, no-store, must-revalidate" "https://raw.githubusercontent.com/miatradingmtx-collab/trading/main/mia_herds_cli.py?nocache=$(date +%s)" -o mia_herds_cli.py 2>/dev/null || true

# Ejecutar CLI de Herds
python3 mia_herds_cli.py "$@"
