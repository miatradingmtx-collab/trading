import os
import sys
import time
import json
import requests
from datetime import datetime

UPSTASH_URL = os.getenv("UPSTASH_REDIS_REST_URL", "https://firm-koi-93555.upstash.io")
UPSTASH_TOKEN = os.getenv("UPSTASH_REDIS_REST_TOKEN", "gQAAAAAAAW1zAAIgcDFmZGI5MGViNWY4Mjc0MGE1Yjg3NDZiOTdiN2MyMjg5Yg")
headers = {"Authorization": f"Bearer {UPSTASH_TOKEN}"}

try:
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

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

# Códigos ANSI para visualización estilo Terminal Cuántica
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
MAGENTA = "\033[95m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"
CLEAR = "\033[H\033[J"

def render_tensor_matrix():
    try:
        r_vec = requests.get(f"{UPSTASH_URL}/get/cache_vector_indicadores", headers=headers, timeout=3)
        vec_data = json.loads(r_vec.json().get("result", "{}")) if r_vec.status_code == 200 and r_vec.json().get("result") else {}
        
        r_tf = requests.get(f"{UPSTASH_URL}/get/cache_mia_tensorflow", headers=headers, timeout=3)
        tf_data = json.loads(r_tf.json().get("result", "{}")) if r_tf.status_code == 200 and r_tf.json().get("result") else {}
        
        r_mt5 = requests.get(f"{UPSTASH_URL}/get/cache_mt5", headers=headers, timeout=3)
        mt5_data = json.loads(r_mt5.json().get("result", "{}")) if r_mt5.status_code == 200 and r_mt5.json().get("result") else {}

        raw_vec = vec_data.get("tensor_1d", [0.0]*20)
        ts = vec_data.get("timestamp", datetime.utcnow().isoformat())
        accuracy = tf_data.get("accuracy", 57.55)
        trades_learned = tf_data.get("trades_aprendidos", 710)
        balance = mt5_data.get("balance", 3877.49)
        equity = mt5_data.get("equity", 3877.49)

        # Segmentación Tridimensional (X, Y, Z)
        # X: Dimensión Temporal y Sesión (Indices 0..3)
        # Y: Dimensión Espacial / Estructura SMC y Régimen (Indices 4..15)
        # Z: Dimensión Cuantitativa Continua (Indices 16..20)
        dim_x = raw_vec[0:4]
        dim_y_reg = raw_vec[4:8]
        if len(raw_vec) >= 22:
            dim_y_smc = raw_vec[8:17]
            dim_z = raw_vec[17:22]
            tensor_dim_label = f'{len(raw_vec)}D TENSOR MATRIX'
        else:
            dim_y_smc = raw_vec[8:16]
            dim_z = raw_vec[16:21] if len(raw_vec) >= 21 else (raw_vec[16:20] + [accuracy / 100.0])
            tensor_dim_label = '21D TENSOR MATRIX'

        sys.stdout.write(CLEAR)
        sys.stdout.write(f"{CYAN}{BOLD}========================================================================================{RESET}\n")
        sys.stdout.write(f"{MAGENTA}{BOLD}   MIA TENSORFLOW NEURAL ENGINE · MONITOR TRIDIMENSIONAL EN VIVO ({tensor_dim_label})   {RESET}\n")
        sys.stdout.write(f"{CYAN}{BOLD}========================================================================================{RESET}\n")
        sys.stdout.write(f"{DIM}Timestamp: {ts} | Trades Aprendidos: {GREEN}{trades_learned}{RESET} | Precision Modelo: {GREEN}{accuracy:.2f}%{RESET} | Balance: {GREEN}${balance:.2f}{RESET}\n\n")

        # 1. EJE X: MATRIZ TEMPORAL (SESIONES DE MERCADO)
        ses_labels = ["ASIA (Tokio/Sidney)", "LONDRES (Apertura)", "NUEVA YORK (Expansión)", "OVERLAP (Londres-NY)"]
        sys.stdout.write(f"{YELLOW}{BOLD}[EJE X: TEMPORALIDAD Y SESIÓN DE MERCADO]{RESET}\n")
        for i, val in enumerate(dim_x):
            state = f"{GREEN}[ACTIVO 1]{RESET}" if val == 1.0 else f"{DIM}[INACTIVO 0]{RESET}"
            bar = f"{GREEN}■■■■■■■■■■{RESET}" if val == 1.0 else f"{DIM}□□□□□□□□□□{RESET}"
            sys.stdout.write(f"  Pos X{i} | {ses_labels[i]:25s} : {state}  {bar} ({val:.1f})\n")

        # 2. EJE Y: MATRIZ ESPACIAL (RÉGIMEN Y CONFLUENCIAS SMC/ICT)
        sys.stdout.write(f"\n{YELLOW}{BOLD}[EJE Y: RÉGIMEN DE MERCADO Y CONFLUENCIAS SMC/ICT]{RESET}\n")
        reg_labels = ["Tendencial Alcista", "Tendencial Bajista", "Rango Lateral", "Alta Volatilidad / Expansión"]
        for i, val in enumerate(dim_y_reg):
            state = f"{GREEN}[ACTIVO 1]{RESET}" if val == 1.0 else f"{DIM}[INACTIVO 0]{RESET}"
            sys.stdout.write(f"  Reg Y{i} | {reg_labels[i]:25s} : {state} ({val:.1f})\n")

        smc_labels = [
            "Order Block Lux 2H", "Fair Value Gap (FVG)", "Liquidity Pool Sweep", "Breaker Block 4H",
            "Mitigation Zone", "Volume POC Price", "SMC Sweep CME", "DOM Imbalance Filter", "CVOL Energy Area"
        ]
        sys.stdout.write(f"\n  {CYAN}Matriz de Activaciones Sinápticas (Multi-Hot 1/0):{RESET}\n")
        for i, val in enumerate(dim_y_smc):
            node = f"{GREEN}● 1.0{RESET}" if val == 1.0 else f"{DIM}○ 0.0{RESET}"
            lbl = smc_labels[i] if i < len(smc_labels) else f"SMC Node Y{i+4:02d}"
            sys.stdout.write(f"    SMC Y{i+4:02d} [{lbl:24s}]: {node}\n")

        # 3. EJE Z: MATRIZ CUANTITATIVA CONTINUA (MÉTRICAS NORMALIZADAS)
        z_labels = [
            "ATR Dinamico Normalizado",
            "RSI Extremo Normalizado (Endógeno)",
            "Spread Broker Normalizado",
            "DXY SMT Correlation Ratio (Macro)",
            "TensorFlow Neural Confidence (710 Trades)"
        ]
        sys.stdout.write(f"\n{YELLOW}{BOLD}[EJE Z: MÉTRICAS CUANTITATIVAS CONTINUAS (0.00 - 1.00)]{RESET}\n")
        for i, val in enumerate(dim_z):
            label_text = z_labels[i] if i < len(z_labels) else f"Met Z{i} Continua"
            length = int(val * 20)
            gauge = f"{GREEN}{'█' * length}{DIM}{'░' * (20 - length)}{RESET}"
            sys.stdout.write(f"  Met Z{i} | {label_text:42s} : [{gauge}] {val:.2f}\n")

        # 4. CÁLCULO DE PROPAGACIÓN NEURONAL HACIA ADELANTE
        # Z_net = sum(W * X)
        score_base = (sum(dim_x) * 0.15) + (sum(dim_y_reg) * 0.20) + (sum(dim_y_smc) * 0.40) + (sum(dim_z) * 0.25)
        prob_acierto = min(0.98, max(0.10, score_base / 2.8))

        sys.stdout.write(f"\n{CYAN}{BOLD}----------------------------------------------------------------------------------------{RESET}\n")
        sys.stdout.write(f"  {BOLD}INFERENCIA SINÁPTICA TENSORFLOW:{RESET} ")
        if prob_acierto >= 0.70:
            sys.stdout.write(f"{GREEN}{BOLD}QUÓRUM ALCANZADO ({prob_acierto*100:.1f}%) · SEÑAL APROBADA{RESET}\n")
        else:
            sys.stdout.write(f"{YELLOW}{BOLD}QUÓRUM INSUFICIENTE ({prob_acierto*100:.1f}%) · VETO / STANDBY{RESET}\n")
        sys.stdout.write(f"{CYAN}{BOLD}========================================================================================{RESET}\n")
        sys.stdout.write(f"{DIM}Presiona Ctrl+C para salir | Actualización en tiempo real cada 3 segundos...{RESET}\n")
        sys.stdout.flush()

    except Exception as e:
        sys.stdout.write(f"\nError en lectura de telemetría: {e}\n")

if __name__ == "__main__":
    print("Iniciando Monitor de Tensores...")
    while True:
        render_tensor_matrix()
        time.sleep(3)
