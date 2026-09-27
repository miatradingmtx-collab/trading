#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
MIA CORE - ANTOPUS TERMINAL CLI (Cross-Platform: Termux, CMD, PowerShell, Bash)
================================================================================
Consola de Monitoreo Inter-Agente en Tiempo Real.
Permite visualizar la deliberacion de los 3 Sub-Enjambres (Antopus), el Consenso
de RUNE, la inferencia de TensorFlow y el estado del mercado directamente en
cualquier terminal (Android Termux, Windows CMD/PowerShell, Linux, macOS).
"""

import sys
import os
import time
import json
import argparse
import datetime
import urllib.request
import io
import asyncio

# Asegurar codificacion UTF-8 universal en terminales (Windows CMD, PowerShell, Termux)
if sys.stdout and hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True)
if sys.stderr and hasattr(sys.stderr, "buffer"):
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace", line_buffering=True)

# Configuracion de Endpoints
WS_URL = "wss://trading-production-1fd4.up.railway.app/ws"
UPSTASH_URL = "https://certain-gnat-160816.upstash.io"
UPSTASH_TOKEN = "gQAAAAAAAnQwAAIgcDI2YTA5YjRlZDU2MDM0OWU5ODhlZjBlYTk4ODYyZDg0OA"

# Codigos de Color ANSI Universales
C_RESET   = "\033[0m"
C_BOLD    = "\033[1m"
C_DIM     = "\033[2m"
C_CYAN    = "\033[96m"
C_YELLOW  = "\033[93m"
C_GREEN   = "\033[92m"
C_RED     = "\033[91m"
C_MAGENTA = "\033[95m"
C_BLUE    = "\033[94m"
C_WHITE   = "\033[97m"
C_ORANGE  = "\033[38;5;208m"
C_BG_DARK = "\033[40m"

# Habilitar colores en Windows CMD clasico si es necesario
if os.name == "nt":
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
    except Exception:
        pass


def fetch_upstash(key: str) -> dict:
    """Lee un slot de Upstash Redis via REST nativo (cero dependencias externas)."""
    try:
        headers = {
            "Authorization": f"Bearer {UPSTASH_TOKEN}",
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache"
        }
        req = urllib.request.Request(
            f"{UPSTASH_URL}/get/{key}",
            headers=headers
        )
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode("utf-8"))
            res_val = data.get("result")
            if not res_val:
                return {}
            if isinstance(res_val, str):
                try:
                    return json.loads(res_val)
                except Exception:
                    return {"raw": res_val}
            return res_val
    except Exception as e:
        return {"error": str(e)}


def print_banner():
    banner = rf"""{C_CYAN}{C_BOLD}
  __  __ ___    _       _   _  _ _____ ___  ___ _   _ ___ 
 |  \/  |_ _|  /_\     /_\ | \| |_   _/ _ \| _ \ | | / __|  {C_ORANGE}🐙{C_CYAN}
 | |\/| || |  / _ \   / _ \| .` | | || (_) |  _/ |_| \__ \
 |_|  |_|___|/_/ \_\ /_/ \_\_|\_| |_| \___/|_|  \___/|___/
{C_RESET}{C_WHITE}   >>> PROTOCOLO DE DELIBERACION INTER-AGENTE (ANTOPUS CLI) <<<{C_RESET}
{C_DIM}-----------------------------------------------------------------------------{C_RESET}"""
    print(banner)


def print_status_bar():
    # Obtener TensorFlow info
    tf_data = fetch_upstash("cache_mia_tensorflow")
    acc = tf_data.get("accuracy", 0.9787)
    acc_pct = f"{acc*100:.2f}%" if acc <= 1.0 else f"{acc:.2f}%"
    trades = tf_data.get("trades_aprendidos", 47)

    # Estado del mercado
    now_utc = datetime.datetime.now(datetime.timezone.utc)
    is_weekend = False
    if now_utc.weekday() == 4 and now_utc.hour >= 21:
        is_weekend = True
    elif now_utc.weekday() == 5:
        is_weekend = True
    elif now_utc.weekday() == 6 and now_utc.hour < 21:
        is_weekend = True

    if is_weekend:
        days_ahead = 6 - now_utc.weekday()
        target_date = now_utc + datetime.timedelta(days=days_ahead)
        target_time = target_date.replace(hour=21, minute=0, second=0, microsecond=0)
        horas_rest = round(max(0, (target_time - now_utc).total_seconds()) / 3600, 1)
        market_badge = f"{C_YELLOW}CRIOSUENO ({horas_rest}h para apertura dom 21:00 UTC){C_RESET}"
    else:
        market_badge = f"{C_GREEN}EN VIVO (HFT OpenRouter / MT5){C_RESET}"

    status_line = (
        f"{C_BOLD}[MERCADO]{C_RESET} {market_badge} | "
        f"{C_BOLD}[TENSORFLOW]{C_RESET} {C_GREEN}Acc: {acc_pct}{C_RESET} ({trades} trades) | "
        f"{C_BOLD}[HOST]{C_RESET} {C_CYAN}Railway Cloud{C_RESET}"
    )
    print(status_line)
    print(f"{C_DIM}-----------------------------------------------------------------------------{C_RESET}\n")


def format_agent_event(agent: str, action: str, data: str):
    """Aplica formato visual con colores segun el agente y su Herd (1 al 7 + Master)."""
    now_str = datetime.datetime.now().strftime("%H:%M:%S")
    agent_up = agent.upper()
    action_up = action.upper()

    if "HERD 1" in agent_up or "TIDAL" in agent_up:
        badge = f"{C_CYAN}{C_BOLD}[HERD 1 (TIDAL)]{C_RESET}"
        content_color = C_CYAN
    elif "HERD 2" in agent_up or "NORO" in agent_up:
        badge = f"{C_ORANGE}{C_BOLD}[HERD 2 (NORO)]{C_RESET}"
        content_color = C_ORANGE
    elif "HERD 3" in agent_up or "ZEPHR" in agent_up:
        badge = f"{C_BLUE}{C_BOLD}[HERD 3 (ZEPHR)]{C_RESET}"
        content_color = C_BLUE
    elif "HERD 4" in agent_up or "LUMEN" in agent_up:
        badge = f"{C_YELLOW}{C_BOLD}[HERD 4 (LUMEN)]{C_RESET}"
        content_color = C_YELLOW
    elif "HERD 5" in agent_up or "RUNE" in agent_up:
        if "VETO" in data.upper() or "VETADO" in data.upper() or "ERROR" in action_up:
            badge = f"{C_RED}{C_BOLD}[HERD 5 (RUNE)]{C_RESET}"
            content_color = C_RED
        else:
            badge = f"{C_GREEN}{C_BOLD}[HERD 5 (RUNE)]{C_RESET}"
            content_color = C_GREEN
    elif "HERD 6" in agent_up or "TENSORFLOW" in agent_up or "TF" in agent_up:
        badge = f"{C_MAGENTA}{C_BOLD}[HERD 6 (TF)]{C_RESET}"
        content_color = C_MAGENTA
    elif "HERD 7" in agent_up or "ATLAS" in agent_up:
        badge = f"{C_CYAN}{C_BOLD}[HERD 7 (ATLAS)]{C_RESET}"
        content_color = C_CYAN
    elif "MASTER" in agent_up:
        if "VETO" in data.upper() or "VETADO" in data.upper():
            badge = f"{C_RED}{C_BOLD}[MASTER QUORUM]{C_RESET}"
            content_color = C_RED
        else:
            badge = f"{C_GREEN}{C_BOLD}[MASTER QUORUM]{C_RESET}"
            content_color = C_WHITE
    else:
        badge = f"{C_MAGENTA}{C_BOLD}[{agent_up}]{C_RESET}"
        content_color = C_WHITE

    action_badge = f"{C_DIM}({action_up}){C_RESET}" if action else ""
    return f"{C_DIM}[{now_str}]{C_RESET} {badge} {action_badge}\n  {content_color}{data}{C_RESET}\n"


def display_latest_debate():
    """Muestra el ultimo debate almacenado en Upstash Redis con soporte para 7 Herds Desacoplados."""
    print(f"{C_BOLD}{C_MAGENTA}>>> ULTIMO DEBATE DE LAS MANADAS (7 HERDS DESACOPLADOS + MASTER):{C_RESET}")
    debate_payload = fetch_upstash("cache_herd_debate_latest")
    
    if not debate_payload or "content" not in debate_payload:
        print(f"  {C_DIM}No hay debates recientes registrados en Upstash.{C_RESET}\n")
        return

    content = debate_payload.get("content", "")
    title = debate_payload.get("title", "Desconocido")
    timestamp = debate_payload.get("timestamp", "N/A")
    print(f"  {C_DIM}Reporte: {title} | Timestamp: {timestamp}{C_RESET}")
    print(f"{C_DIM}----------------------------------------------------------{C_RESET}")

    lines = content.split("\n")
    for line in lines:
        line_clean = line.strip()
        if not line_clean:
            continue
        if "HERD 1" in line_clean.upper() or "TIDAL" in line_clean.upper():
            print(f"  {C_CYAN}{C_BOLD}{line_clean}{C_RESET}")
        elif "HERD 2" in line_clean.upper() or "NORO" in line_clean.upper():
            print(f"  {C_ORANGE}{C_BOLD}{line_clean}{C_RESET}")
        elif "HERD 3" in line_clean.upper() or "ZEPHR" in line_clean.upper():
            print(f"  {C_BLUE}{C_BOLD}{line_clean}{C_RESET}")
        elif "HERD 4" in line_clean.upper() or "LUMEN" in line_clean.upper():
            print(f"  {C_YELLOW}{C_BOLD}{line_clean}{C_RESET}")
        elif "HERD 5" in line_clean.upper() or "RUNE" in line_clean.upper():
            if "VETO" in line_clean.upper() or "VETADO" in line_clean.upper():
                print(f"  {C_RED}{C_BOLD}{line_clean}{C_RESET}")
            else:
                print(f"  {C_GREEN}{C_BOLD}{line_clean}{C_RESET}")
        elif "HERD 6" in line_clean.upper() or "TENSORFLOW" in line_clean.upper():
            print(f"  {C_MAGENTA}{C_BOLD}{line_clean}{C_RESET}")
        elif "HERD 7" in line_clean.upper() or "ATLAS" in line_clean.upper():
            print(f"  {C_CYAN}{C_BOLD}{line_clean}{C_RESET}")
        elif "MASTER" in line_clean.upper():
            if "VETO" in line_clean.upper() or "VETADO" in line_clean.upper():
                print(f"  {C_RED}{C_BOLD}{line_clean}{C_RESET}")
            else:
                print(f"  {C_GREEN}{C_BOLD}{line_clean}{C_RESET}")
        else:
            print(f"    {C_WHITE}{line_clean}{C_RESET}")
    print()


async def stream_live_websocket():
    """Conecta en vivo al WebSocket de Railway para transmitir el debate segundo a segundo."""
    import websockets
    print(f"{C_GREEN}[*] Conectando al Piso de Trading en Vivo ({WS_URL})...{C_RESET}\n")
    
    reconnect_delay = 3
    while True:
        try:
            async with websockets.connect(WS_URL, ping_interval=20, ping_timeout=20) as ws:
                print(f"{C_GREEN}[OK] Conexion WebSocket Establecida.{C_RESET} Escuchando dialogo de los agentes...\n")
                reconnect_delay = 3
                while True:
                    raw_msg = await ws.recv()
                    try:
                        data = json.loads(raw_msg)
                        if data.get("type") == "HEARTBEAT":
                            continue
                        agent = data.get("agent", "SYSTEM")
                        action = data.get("action", "")
                        msg_text = data.get("data") or data.get("msg") or data.get("texto") or str(data)
                        print(format_agent_event(agent, action, msg_text))
                    except Exception:
                        print(f"{C_DIM}{raw_msg}{C_RESET}")
        except (websockets.exceptions.ConnectionClosed, websockets.exceptions.WebSocketException, OSError, TimeoutError, asyncio.TimeoutError) as e:
            print(f"{C_YELLOW}[!] Conexion en espera o reconectando ({e}). Reintento en {int(reconnect_delay)}s...{C_RESET}")
            await asyncio.sleep(reconnect_delay)
            reconnect_delay = min(reconnect_delay * 1.5, 30)
        except Exception as e:
            print(f"{C_RED}[X] Conexion pausada ({e}). Reconectando en 5s...{C_RESET}")
            await asyncio.sleep(5)


def poll_upstash_fallback():
    """Modo de respaldo por sondeo en caso de que websockets no este disponible."""
    print(f"{C_YELLOW}[*] Modo Respaldo: Sondeando Upstash Redis cada 4 segundos...{C_RESET}\n")
    last_title = ""
    while True:
        try:
            data = fetch_upstash("cache_herd_debate_latest")
            title = data.get("title", "")
            if title and title != last_title:
                last_title = title
                print(f"{C_BOLD}{C_GREEN}[>] NUEVO DEBATE ANTOPUS DETECTADO ({title}):{C_RESET}")
                content = data.get("content", "")
                for line in content.split("\n"):
                    if line.strip():
                        print(f"  {line}")
                print()
            time.sleep(4)
        except KeyboardInterrupt:
            print("\nFinalizado por usuario.")
            break
        except Exception as e:
            time.sleep(5)


def main():
    parser = argparse.ArgumentParser(description="MIA Antopus Terminal CLI - Monitor Inter-Agente")
    parser.add_argument("--once", action="store_true", help="Muestra el estado actual y ultimo debate y finaliza.")
    parser.add_argument("--status", action="store_true", help="Solo muestra el estado de mercado y metricas de TensorFlow.")
    parser.add_argument("--poll", action="store_true", help="Fuerza el modo sondeo via Upstash en lugar de WebSocket.")
    args = parser.parse_args()

    print_banner()
    print_status_bar()

    if args.status:
        return

    display_latest_debate()

    if args.once:
        return

    # Verificar si websockets esta disponible para streaming en tiempo real
    if not args.poll:
        try:
            import websockets
            import asyncio
            asyncio.run(stream_live_websocket())
        except ImportError:
            print(f"{C_YELLOW}Nota: Libreria 'websockets' no instalada. Usando sondeo automatico a Upstash.{C_RESET}")
            print(f"{C_DIM}(Para streaming ultra-rapido ejecuta: pip install websockets){C_RESET}\n")
            poll_upstash_fallback()
        except KeyboardInterrupt:
            print(f"\n{C_CYAN}MIA Antopus CLI desconectado con exito.{C_RESET}")
    else:
        poll_upstash_fallback()


if __name__ == "__main__":
    main()

