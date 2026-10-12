"""
=============================================================================
MIA HERDS MASTER ORCHESTRATOR · MONITOR DE DELIBERACIÓN INTER-AGENTE EN VIVO
=============================================================================
Consola en tiempo real del Master Orchestrator que supervisa a los 7 Herds:
1. TIDAL (Macro / Sesiones)
2. NORO (Matemáticas Cuantitativas / POC / Markov)
3. ZEPHR (Probabilidad Bayesiana / Expected Value)
4. LUMEN (Smart Money Concepts / Order Blocks LuxAlgo)
5. RUNE (Gestión de Riesgo Defensivo / Trailing 3 Fases)
6. TENSORFLOW (Inferencia Neuronal Continua 20D)
7. ATLAS (Microestructura DOM CME / CVD Delta / Absorción)
+ MASTER ORCHESTRATOR (Quórum Ponderado y Veredicto Final de Ejecución)
+ BIFURCACIÓN A/B (Monitoreo de Muestra Champion vs Challenger en Cuarentena)
=============================================================================
"""

import sys
import os
import time
import json
import requests
from datetime import datetime, timezone

# Soporte ANSI para Windows CMD
def enable_vt_mode():
    if os.name == 'nt':
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            h_out = kernel32.GetStdHandle(-11)
            mode = ctypes.c_ulong()
            if kernel32.GetConsoleMode(h_out, ctypes.byref(mode)):
                kernel32.SetConsoleMode(h_out, mode.value | 0x0004)
        except Exception:
            pass
        try:
            os.system('')
        except Exception:
            pass

enable_vt_mode()

try:
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

UPSTASH_URL = os.getenv("UPSTASH_REDIS_REST_URL", "https://certain-gnat-160816.upstash.io")
UPSTASH_TOKEN = os.getenv("UPSTASH_REDIS_REST_TOKEN", "gQAAAAAAAnQwAAIgcDI2YTA5YjRlZDU2MDM0OWU5ODhlZjBlYTk4ODYyZDg0OA")
HEADERS = {"Authorization": f"Bearer {UPSTASH_TOKEN}"}

# Códigos de Color ANSI
CYAN    = "\033[96m"
GREEN   = "\033[92m"
YELLOW  = "\033[93m"
RED     = "\033[91m"
MAGENTA = "\033[95m"
BLUE    = "\033[94m"
WHITE   = "\033[97m"
BOLD    = "\033[1m"
DIM     = "\033[2m"
RESET   = "\033[0m"
CLEAR   = "\033[H\033[2J"

def render_herds_master():
    try:
        # MGET Atómico a Upstash Redis
        slots = [
            "cache_herd_debate_latest",
            "cache_herds_ab_evaluation",
            "cache_mt5",
            "cache_mia_tensorflow",
            "cache_regla_de_3"
        ]
        mget_url = f"{UPSTASH_URL}/mget/" + "/".join(slots)
        r = requests.get(mget_url, headers=HEADERS, timeout=3.0)
        
        raw_results = r.json().get("result", []) if r.status_code == 200 else []
        
        # Parsear slots
        def parse_slot(idx):
            if idx < len(raw_results) and raw_results[idx]:
                val = raw_results[idx]
                return json.loads(val) if isinstance(val, str) else val
            return {}

        debate_data = parse_slot(0)
        ab_data     = parse_slot(1)
        mt5_data    = parse_slot(2)
        tf_data     = parse_slot(3)
        r3_data     = parse_slot(4)

        debate = debate_data.get("debate", {})
        ts = debate_data.get("timestamp", datetime.now(timezone.utc).isoformat())
        title = debate_data.get("title", "REST_HFT_Cycle")
        
        h1 = debate.get("herd_1_tidal", "Esperando telemetría de TIDAL...")
        h2 = debate.get("herd_2_noro", "Esperando telemetría de NORO...")
        h3 = debate.get("herd_3_zephr", "Esperando telemetría de ZEPHR...")
        h4 = debate.get("herd_4_lumen", "Esperando telemetría de LUMEN...")
        h5 = debate.get("herd_5_rune", "Esperando telemetría de RUNE...")
        h6 = debate.get("herd_6_tensorflow", "Esperando telemetría de TENSORFLOW...")
        h7 = debate.get("herd_7_atlas", "Esperando telemetría de ATLAS...")
        master_quorum = debate.get("master_quorum", debate.get("estado", "SIN_VEREDICTO"))
        estado = debate.get("estado", "EN_CURSO")

        balance = mt5_data.get("balance_actual", mt5_data.get("balance", 3877.49))
        equity = mt5_data.get("equity", balance)
        floating_pnl = mt5_data.get("floating_pnl", 0.0)

        tf_acc_raw = tf_data.get("accuracy", 57.61)
        tf_acc = tf_acc_raw * 100 if tf_acc_raw <= 1.0 else tf_acc_raw
        tf_trades = tf_data.get("trades_aprendidos", 710)

        # Muestra A/B
        champ = ab_data.get("champion_control", {})
        chal = ab_data.get("challenger_herds", {})
        perdidas_evitadas = chal.get("perdidas_evitadas_por_veto", 0.0)

        # Determinar Sesión Activa
        hora_utc = datetime.now(timezone.utc).hour
        if 7 <= hora_utc < 12: sesion_str = "LONDRES (Apertura)"
        elif 12 <= hora_utc < 19: sesion_str = "NUEVA YORK (Expansión)"
        elif 19 <= hora_utc < 22: sesion_str = "CIERRE NY / OVERLAP"
        else: sesion_str = "ASIA (Tokio / Sídney)"

        sys.stdout.write(CLEAR)
        sys.stdout.write(f"{CYAN}{BOLD}========================================================================================{RESET}\n")
        sys.stdout.write(f"{MAGENTA}{BOLD}          MIA HERDS MASTER ORCHESTRATOR · PANEL DE DELIBERACIÓN INTER-AGENTE EN VIVO    {RESET}\n")
        sys.stdout.write(f"{CYAN}{BOLD}========================================================================================{RESET}\n")
        sys.stdout.write(f"  {BOLD}Sesión:{RESET} {YELLOW}{sesion_str}{RESET} | {BOLD}Balance MT5:{RESET} {GREEN}${balance:.2f}{RESET} | {BOLD}Equity:{RESET} {GREEN}${equity:.2f}{RESET} | {BOLD}PnL Flotante:{RESET} {GREEN if floating_pnl >= 0 else RED}${floating_pnl:.2f}{RESET}\n")
        sys.stdout.write(f"  {BOLD}Ciclo HFT:{RESET} {DIM}{title}{RESET} | {BOLD}Timestamp:{RESET} {DIM}{ts[:19]} UTC{RESET} | {BOLD}Tensores TF:{RESET} {GREEN}{tf_trades} trades ({tf_acc:.1f}% Acc){RESET}\n")
        sys.stdout.write(f"{CYAN}{BOLD}========================================================================================{RESET}\n\n")

        # RENDERIZADO DE LOS 7 HERDS
        def format_herd(tag, name, color, text):
            sys.stdout.write(f"  {color}{BOLD}[{tag} · {name}]{RESET}\n")
            # Envolver texto a maximo 80 columnas
            words = text.split()
            current_line = "    "
            for w in words:
                if len(current_line) + len(w) + 1 > 84:
                    sys.stdout.write(f"{current_line}\n")
                    current_line = "    " + w
                else:
                    current_line += (" " if current_line != "    " else "") + w
            sys.stdout.write(f"{current_line}\n\n")

        format_herd("HERD 1", "TIDAL (Flujo Macro & Sesiones)", CYAN, h1)
        format_herd("HERD 2", "NORO (Matemáticas Cuantitativas & POC Markov)", BLUE, h2)
        format_herd("HERD 3", "ZEPHR (Probabilidad Bayesiana & Expected Value)", YELLOW, h3)
        format_herd("HERD 4", "LUMEN (Smart Money Concepts & Order Blocks 2H)", MAGENTA, h4)
        format_herd("HERD 5", "RUNE (Gestión de Riesgo Defensiva & Trailing 3 Fases)", GREEN if "VETO" not in h5.upper() else RED, h5)
        format_herd("HERD 6", "TENSORFLOW (Inferencia Neuronal Continua 20D)", WHITE, h6)
        format_herd("HERD 7", "ATLAS (Microestructura DOM CME & CVD Delta)", CYAN, h7)

        sys.stdout.write(f"{CYAN}{BOLD}----------------------------------------------------------------------------------------{RESET}\n")
        # RENDERIZADO DEL MASTER ORCHESTRATOR
        quorum_color = GREEN if ("APROBADO" in str(estado).upper() or "APROBADO" in str(master_quorum).upper()) else RED
        sys.stdout.write(f"  {quorum_color}{BOLD}★ VEREDICTO MASTER ORCHESTRATOR [{estado.strip()}]:{RESET}\n")
        words_m = str(master_quorum).split()
        cur_m = "    "
        for w in words_m:
            if len(cur_m) + len(w) + 1 > 84:
                sys.stdout.write(f"{cur_m}\n")
                cur_m = "    " + w
            else:
                cur_m += (" " if cur_m != "    " else "") + w
        sys.stdout.write(f"{cur_m}\n\n")

        # PANEL DE BIFURCACIÓN A/B
        sys.stdout.write(f"{CYAN}{BOLD}----------------------------------------------------------------------------------------{RESET}\n")
        sys.stdout.write(f"  {YELLOW}{BOLD}[TELEMETRÍA DE BIFURCACIÓN A/B · TRADES 710 -> 750 EN CUARENTENA]{RESET}\n")
        sys.stdout.write(f"  * Muestra A (Champion / Sin Enjambres): {champ.get('total_trades', 0)} trades | WinRate: {champ.get('win_rate', 0.0):.1f}% | PnL: ${champ.get('pnl_acumulado', 0.0):.2f}\n")
        sys.stdout.write(f"  * Muestra B (Challenger / 7 Herds + ATLAS): {chal.get('total_trades', 0)} evaluados | {chal.get('trades_ejecutados', 0)} tomados | {chal.get('trades_vetados', 0)} vetados\n")
        sys.stdout.write(f"  * Capital Salvado por Vetos Institucionales: {GREEN}${perdidas_evitadas:.2f} USD{RESET} | Cuarentena TF: {GREEN}ACTIVA (710 Trades Blindados){RESET}\n")
        sys.stdout.write(f"{CYAN}{BOLD}========================================================================================{RESET}\n")
        sys.stdout.write(f"{DIM}Refresco automático cada 3 segundos | Presiona Ctrl+C para salir al menú...{RESET}\n")
        sys.stdout.flush()

    except Exception as e:
        sys.stdout.write(f"\nError en telemetría de Herds Master: {e}\n")

if __name__ == "__main__":
    print("Iniciando Herds Master Orchestrator Monitor...")
    try:
        while True:
            render_herds_master()
            time.sleep(3.0)
    except KeyboardInterrupt:
        sys.stdout.write(f"\n{YELLOW}Herds Master Monitor cerrado por el usuario.{RESET}\n")
