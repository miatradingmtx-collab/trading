#!/bin/bash
# ==============================================================================
# MIA HERDS CLI - Script de Aprovisionamiento Automático (Termux & Linux)
# ==============================================================================
# Instala el comando global 'herds' en tu sistema.
# Uso: curl -sL https://raw.githubusercontent.com/miatradingmtx-collab/trading/main/install_herds.sh | bash
# ==============================================================================

set -e

echo -e "\033[96m[*] Iniciando aprovisionamiento de MIA Herds CLI...\033[0m"

# 1. Detectar entorno (Termux vs Linux estándar)
if [ -d "/data/data/com.termux/files/usr/bin" ]; then
    BIN_DIR="/data/data/com.termux/files/usr/bin"
    MIA_DIR="/data/data/com.termux/files/home/.mia"
    IS_TERMUX=true
else
    BIN_DIR="/usr/local/bin"
    MIA_DIR="$HOME/.mia"
    IS_TERMUX=false
fi

mkdir -p "$MIA_DIR"

# 2. Instalar dependencias esenciales
echo -e "\033[93m[*] Verificando dependencias (python, websockets)...\033[0m"
if ! command -v python3 &> /dev/null; then
    if [ "$IS_TERMUX" = true ]; then
        pkg update -y && pkg install python -y
    else
        sudo apt-get update && sudo apt-get install python3 python3-pip -y
    fi
fi

# Instalar websockets si falta
python3 -c "import websockets" 2>/dev/null || pip install websockets --quiet || true

# 3. Descargar el script principal de Herds
echo -e "\033[93m[*] Descargando núcleo de Herds CLI (Malla 7 Herds)...\033[0m"
curl -sL -H "Cache-Control: no-cache, no-store, must-revalidate" "https://raw.githubusercontent.com/miatradingmtx-collab/trading/main/mia_herds_cli.py?nocache=$(date +%s)" -o "$MIA_DIR/mia_herds_cli.py"

# 4. Crear el comando ejecutable global 'herds'
HERDS_EXEC="$BIN_DIR/herds"

cat << 'EOF' > "$HERDS_EXEC"
#!/bin/bash
# MIA Herds CLI - Wrapper con auto-actualización silenciosa y refresco APN/ARP

MIA_DIR="$HOME/.mia"
if [ -d "/data/data/com.termux/files/home/.mia" ]; then
    MIA_DIR="/data/data/com.termux/files/home/.mia"
fi

# Comando explícito de refresco de tablas APN / ARP y actualización a 7 Herds
if [ "$1" == "update" ] || [ "$1" == "refresh" ] || [ "$1" == "--refresh" ] || [ "$1" == "-u" ]; then
    echo -e "\033[93m[*] Refrescando tablas APN / ARP y descargando Malla de 7 Herds...\033[0m"
    ip neigh flush all 2>/dev/null || true
    curl -sL -H "Cache-Control: no-cache, no-store, must-revalidate" "https://raw.githubusercontent.com/miatradingmtx-collab/trading/main/mia_herds_cli.py?nocache=$(date +%s)" -o "$MIA_DIR/mia_herds_cli.py"
    echo -e "\033[92m[OK] Malla de 7 Herds actualizada exitosamente en Termux.\033[0m"
    python3 "$MIA_DIR/mia_herds_cli.py" --once
    exit 0
fi

# Soporte para colgar en segundo plano (Background Daemon)
if [ "$1" == "bg" ] || [ "$1" == "--bg" ] || [ "$1" == "daemon" ]; then
    echo -e "\033[92m[*] Colgando Herds en segundo plano (Background Daemon)...\033[0m"
    if command -v termux-wake-lock &> /dev/null; then
        termux-wake-lock
        echo -e "\033[93m[OK] Termux Wake-Lock activado (Android no suspenderá el proceso).\033[0m"
    fi
    shift
    nohup python3 "$MIA_DIR/mia_herds_cli.py" "$@" > "$MIA_DIR/herds.log" 2>&1 &
    echo -e "\033[96m[OK] Herds corriendo con PID $!. Para ver logs en vivo: herds logs\033[0m"
    exit 0
fi

if [ "$1" == "logs" ] || [ "$1" == "--logs" ]; then
    tail -f "$MIA_DIR/herds.log"
    exit 0
fi

if [ "$1" == "stop" ]; then
    pkill -f "mia_herds_cli.py" && echo -e "\033[91m[OK] Herds detenido.\033[0m" || echo "No había procesos activos."
    if command -v termux-wake-unlock &> /dev/null; then
        termux-wake-unlock
    fi
    exit 0
fi

# Auto-actualización silenciosa con bypass de caché de proxy APN
(curl -s -m 4 -H "Cache-Control: no-cache" "https://raw.githubusercontent.com/miatradingmtx-collab/trading/main/mia_herds_cli.py?nocache=$(date +%s)" -o "$MIA_DIR/mia_herds_cli.py.tmp" && mv "$MIA_DIR/mia_herds_cli.py.tmp" "$MIA_DIR/mia_herds_cli.py" 2>/dev/null) &

# Evitar que Android duerma la conexión mientras el CLI esté abierto
if command -v termux-wake-lock &> /dev/null; then
    termux-wake-lock 2>/dev/null || true
fi

python3 "$MIA_DIR/mia_herds_cli.py" "$@"
EOF

chmod +x "$HERDS_EXEC"

echo -e "\033[92m"
echo "============================================================================="
echo " ✔ APROVISIONAMIENTO EXITOSO: Comando global 'herds' instalado"
echo "============================================================================="
echo -e "\033[0m"
echo -e "A partir de ahora, solo escribe: \033[96mherds\033[0m en tu terminal."
echo ""
echo -e "Comandos disponibles:"
echo -e "  \033[96mherds\033[0m            -> Abre la terminal en vivo de los agentes."
echo -e "  \033[96mherds bg\033[0m         -> Cuelga a Herds en segundo plano (Daemon permanente)."
echo -e "  \033[96mherds logs\033[0m       -> Muestra el registro en vivo del proceso en segundo plano."
echo -e "  \033[96mherds stop\033[0m       -> Detiene el proceso en segundo plano."
echo -e "  \033[96mherds --once\033[0m     -> Muestra snapshot rápido y sale."
echo ""
