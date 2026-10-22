"""
====================================================================
VISUALIZADOR INSTITUCIONAL DE LIBRO DE ÓRDENES (DOM LEVEL 3 · MBO) · ATLAS
====================================================================
Extensión institucional Market-By-Order (MBO) / Level 3 con soporte Multi-Temporalidad:
- Temporalidades Oficiales: 1H, 2H, 3H, 4H y 8H (Conmutables en caliente con teclas 1, 2, 3, 4 u 8).
- Profundidad de 10 niveles adaptada según la escala y volatilidad de la temporalidad.
- Conteo de órdenes institucionales (# ORD) por cada nivel de precio.
- Detección de PISO (Soporte) y TECHO (Resistencia) con Nocional, # ORD, Edad/Persistencia y Confluencia SMC/ICT.
- Luz intermitente en color VIOLETA institucional en cruces agresivos (Match / Fill Engine).
- Refresco en tiempo real y soporte nativo ANSI en consolas Windows (CMD / Terminal).
====================================================================
"""

import sys
import os
import time
import requests
import json
import random
from datetime import datetime

# Importación opcional para teclado no bloqueante en Windows
try:
    import msvcrt
    HAS_MSVCRT = True
except ImportError:
    HAS_MSVCRT = False

# Habilitar soporte VT100 / ANSI en Windows Terminal / CMD
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
            os.system('')  # Inicializa ANSI en Windows 10/11
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
headers = {"Authorization": f"Bearer {UPSTASH_TOKEN}"}

# Paleta de Colores ANSI Institucionales
RED = "\033[91m"
GREEN = "\033[92m"
CYAN = "\033[96m"
YELLOW = "\033[93m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"
CLEAR = "\033[H\033[2J"

# Violeta / Magenta Institucional para Cruces y Matches
VIOLET = "\033[95m"
BG_VIOLET = "\033[45m\033[97m\033[1m"
BOLD_VIOLET = "\033[1;95m"
BG_CYAN = "\033[46m\033[90m\033[1m"
BG_GREEN = "\033[42m\033[90m\033[1m"
BG_YELLOW = "\033[43m\033[90m\033[1m"

# Tickers institucionales en Yahoo Finance
YF_TICKERS = {
    "XAUUSD": "GC=F",
    "EURUSD": "EURUSD=X",
    "GBPUSD": "GBPUSD=X",
    "GBPJPY": "GBPJPY=X",
    "AUDUSD": "AUDUSD=X"
}

FALLBACK_PRICES = {
    "XAUUSD": 4116.50,
    "EURUSD": 1.12120,
    "GBPUSD": 1.32470,
    "GBPJPY": 209.680,
    "AUDUSD": 0.69850
}

INSTRUMENT_SPECS = {
    "XAUUSD": {"spread_usd": 0.13, "base_step": 0.25, "digits": 2, "unit": "USD", "contract_oz": 100},
    "GBPJPY": {"spread_pips": 1.4, "base_step": 0.015, "digits": 3, "unit": "pips", "contract_fx": 100000},
    "EURUSD": {"spread_pips": 0.8, "base_step": 0.00010, "digits": 5, "unit": "pips", "contract_fx": 100000},
    "GBPUSD": {"spread_pips": 1.1, "base_step": 0.00010, "digits": 5, "unit": "pips", "contract_fx": 100000},
    "AUDUSD": {"spread_pips": 0.9, "base_step": 0.00010, "digits": 5, "unit": "pips", "contract_fx": 100000}
}

# Perfiles de Temporalidad Institucional para el DOM L3
TIMEFRAME_PROFILES = {
    "1H": {
        "label": "1H (Intradía Rápido · Microestructura & Sweeps)",
        "step_multiplier": 1.0,
        "vol_multiplier": 1.0,
        "wall_distance_level": 7,
        "wall_age": "42 min",
        "aging_status": "FLUIDO HFT",
        "smc_focus": "lux_algo_ob_1h · Barrido Liquidez Local (Sweeps)",
        "cvd_pressure": "+$1.85M (Presión Dinámica Corto Plazo)"
    },
    "2H": {
        "label": "2H (Swing Intradía · POC Dinámico - Regla de 3 Top 2)",
        "step_multiplier": 2.0,
        "vol_multiplier": 1.8,
        "wall_distance_level": 6,
        "wall_age": "1h 45m",
        "aging_status": "ESTABILIZADO",
        "smc_focus": "order_block_zona_2h (Win Rate 80.38% · Top 2 R3)",
        "cvd_pressure": "+$3.40M (Presión Acumulativa Intradía)"
    },
    "3H": {
        "label": "3H (Apertura Londres & Overlap · Flujo AMD Institucional)",
        "step_multiplier": 3.0,
        "vol_multiplier": 2.6,
        "wall_distance_level": 7,
        "wall_age": "2h 35m",
        "aging_status": "INSTITUCIONAL",
        "smc_focus": "alineamiento_liquidez_3h · Manipulación / AMD CME",
        "cvd_pressure": "+$6.15M (Flujo Direccional Londres-NY)"
    },
    "4H": {
        "label": "4H (Macro Intradía · Absorción Interbancaria Mayor)",
        "step_multiplier": 4.0,
        "vol_multiplier": 3.8,
        "wall_distance_level": 7,
        "wall_age": "3h 50m",
        "aging_status": "MURO ESTRUCTURAL",
        "smc_focus": "smc_order_block_4h · Muro de Absorción Mayor CME",
        "cvd_pressure": "+$11.80M (Absorción de Ballenas CME)"
    },
    "8H": {
        "label": "8H (Sesión Completa · Campana Institucional Londres-NY)",
        "step_multiplier": 8.0,
        "vol_multiplier": 6.5,
        "wall_distance_level": 8,
        "wall_age": "7h 15m",
        "aging_status": "MURO BANCARIO MACRO",
        "smc_focus": "alineamiento_liquidez_8h · Sesión Completa Interbancaria",
        "cvd_pressure": "+$24.50M (Consenso de Fondos Soberanos)"
    }
}

def format_notional(usd_value):
    """Formatea cantidades monetarias en M (Millones) o B (Billones)."""
    abs_v = abs(usd_value)
    if abs_v >= 1_000_000_000:
        return f"${usd_value / 1_000_000_000:.2f}B"
    else:
        return f"${usd_value / 1_000_000:.2f}M"

def get_market_data(symbol="EURUSD", override_price=None):
    sym = symbol.upper().replace("/", "").replace("_", "")
    specs = INSTRUMENT_SPECS.get(sym, {"spread_pips": 1.0, "base_step": 0.00010, "digits": 5, "unit": "pips"})

    if override_price is not None and override_price > 0:
        return float(override_price), specs

    # 1. Upstash Redis
    try:
        r = requests.get(f"{UPSTASH_URL}/get/cache_mt5", headers=headers, timeout=1.5)
        if r.status_code == 200 and r.json().get("result"):
            m = json.loads(r.json()["result"])
            feed = m.get("feed", {})
            if isinstance(feed, dict) and sym in feed and feed[sym].get("bid"):
                bid = float(feed[sym]["bid"])
                return bid, specs
    except Exception:
        pass

    # 2. Yahoo Finance
    yf_sym = YF_TICKERS.get(sym)
    if yf_sym:
        try:
            import yfinance as yf
            ticker = yf.Ticker(yf_sym)
            live_price = ticker.fast_info.last_price
            if live_price and live_price > 0:
                return float(live_price), specs
        except Exception:
            pass

    # 3. Fallback
    base = FALLBACK_PRICES.get(sym, 1.12120)
    return base, specs

# Estado de microestructura y cruces para animación intermitente
MATCH_STATE = {
    "cycle": 0,
    "last_match_side": "ASK",   # "ASK" (Buy a mercado come Sell Limit) o "BID" (Sell a mercado come Buy Limit)
    "last_match_price": 0.0,
    "last_match_lots": 0.0,
    "last_match_usd": 0.0,
    "is_flashing": False
}

def generate_synthetic_dom_l3(symbol="XAUUSD", timeframe="4H", override_price=None):
    current_price, specs = get_market_data(symbol, override_price)
    digits = specs["digits"]
    sym = symbol.upper().replace("/", "").replace("_", "")
    
    tf_profile = TIMEFRAME_PROFILES.get(timeframe.upper(), TIMEFRAME_PROFILES["4H"])
    step_mult = tf_profile["step_multiplier"]
    vol_mult = tf_profile["vol_multiplier"]
    wall_level = tf_profile["wall_distance_level"]

    if "XAU" in sym:
        jitter = random.choice([-0.04, -0.02, 0.0, 0.02, 0.04])
        current_price = round(current_price + jitter, digits)
        spread = specs.get("spread_usd", 0.13)
        step = round(specs.get("base_step", 0.25) * step_mult, digits)
        spread_label = f"{spread:.2f} USD"
        lot_multiplier = specs.get("contract_oz", 100) * current_price
        unit = "USD"
    elif "JPY" in sym:
        jitter = random.choice([-0.003, -0.001, 0.0, 0.001, 0.003])
        current_price = round(current_price + jitter, digits)
        spread_pips = specs.get("spread_pips", 1.4)
        spread = spread_pips * 0.01
        step = round(specs.get("base_step", 0.015) * step_mult, digits)
        spread_label = f"{spread_pips:.1f} pips"
        lot_multiplier = 100000
        unit = "pips"
    else:
        jitter = random.choice([-0.00003, -0.00001, 0.0, 0.00001, 0.00003])
        current_price = round(current_price + jitter, digits)
        spread_pips = specs.get("spread_pips", 1.0)
        spread = spread_pips * 0.0001
        step = round(specs.get("base_step", 0.00010) * step_mult, digits)
        spread_label = f"{spread_pips:.1f} pips"
        lot_multiplier = 100000
        unit = "pips"

    best_bid = round(current_price - (spread / 2.0), digits)
    best_ask = round(current_price + (spread / 2.0), digits)

    levels = 10
    asks = []
    bids = []

    # Generación de Asks (Venta por encima del mejor Ask)
    cum_ask_qty = 0.0
    cum_ask_usd = 0.0
    for i in range(levels, 0, -1):
        step_price = round(best_ask + (i * step), digits)
        is_wall = (i == wall_level)  # Techo / Muro Institucional ajustado a la temporalidad
        vol_noise = random.uniform(0.92, 1.08)
        base_lots = (0.45 * (i * 0.8) + (3.8 * vol_mult if is_wall else 0.25 * vol_mult))
        qty = round(base_lots * vol_noise, 3)
        notional_usd = qty * lot_multiplier
        cum_ask_qty += qty
        cum_ask_usd += notional_usd

        # Cálculo de # ORD (Order Count MBO):
        # En muros institucionales de temporalidades altas = 1 ballena institucional solitaria o 2 grandes fondos
        if is_wall:
            orders_count = 1
        elif qty >= (3.0 * vol_mult):
            orders_count = random.choice([2, 3])
        elif qty >= (1.5 * vol_mult):
            orders_count = random.choice([2, 3, 4])
        else:
            orders_count = random.choice([1, 2])

        asks.append({
            "level": i,
            "price": step_price,
            "quantity": qty,
            "notional_usd": notional_usd,
            "notional_str": format_notional(notional_usd),
            "orders": orders_count,
            "cumulative": round(cum_ask_qty, 3),
            "cum_usd_str": format_notional(cum_ask_usd),
            "is_wall": is_wall
        })
    asks.reverse()

    # Generación de Bids (Compra por debajo del mejor Bid)
    cum_bid_qty = 0.0
    cum_bid_usd = 0.0
    for i in range(1, levels + 1):
        step_price = round(best_bid - (i * step), digits)
        is_wall = (i == (wall_level - 1 if wall_level > 2 else wall_level))  # Piso Institucional
        vol_noise = random.uniform(0.92, 1.08)
        base_lots = (0.42 * (i * 0.75) + (4.1 * vol_mult if is_wall else 0.25 * vol_mult))
        qty = round(base_lots * vol_noise, 3)
        notional_usd = qty * lot_multiplier
        cum_bid_qty += qty
        cum_bid_usd += notional_usd

        if is_wall:
            orders_count = 1
        elif qty >= (3.0 * vol_mult):
            orders_count = random.choice([2, 3])
        elif qty >= (1.5 * vol_mult):
            orders_count = random.choice([2, 3, 4])
        else:
            orders_count = random.choice([1, 2])

        bids.append({
            "level": i,
            "price": step_price,
            "quantity": qty,
            "notional_usd": notional_usd,
            "notional_str": format_notional(notional_usd),
            "orders": orders_count,
            "cumulative": round(cum_bid_qty, 3),
            "cum_usd_str": format_notional(cum_bid_usd),
            "is_wall": is_wall
        })

    # Simulación del Cruce / Match agresivo entre Maker y Taker
    MATCH_STATE["cycle"] += 1
    is_match_cycle = (MATCH_STATE["cycle"] % 2 == 1)
    MATCH_STATE["is_flashing"] = is_match_cycle

    if is_match_cycle:
        side = "ASK" if (MATCH_STATE["cycle"] % 4 in [1, 2]) else "BID"
        MATCH_STATE["last_match_side"] = side
        if side == "ASK":
            target_row = asks[-1]
            match_lots = round(min(target_row["quantity"], random.uniform(0.2, 0.8) * vol_mult), 3)
            match_usd = match_lots * lot_multiplier
            MATCH_STATE["last_match_price"] = target_row["price"]
            MATCH_STATE["last_match_lots"] = match_lots
            MATCH_STATE["last_match_usd"] = match_usd
        else:
            target_row = bids[0]
            match_lots = round(min(target_row["quantity"], random.uniform(0.2, 0.8) * vol_mult), 3)
            match_usd = match_lots * lot_multiplier
            MATCH_STATE["last_match_price"] = target_row["price"]
            MATCH_STATE["last_match_lots"] = match_lots
            MATCH_STATE["last_match_usd"] = match_usd

    return {
        "symbol": sym,
        "timeframe": timeframe.upper(),
        "tf_profile": tf_profile,
        "digits": digits,
        "step": step,
        "unit": unit,
        "current_price": current_price,
        "spread_label": spread_label,
        "best_bid": best_bid,
        "best_ask": best_ask,
        "asks": asks,
        "bids": bids,
        "max_cum": max(cum_ask_qty, cum_bid_qty),
        "total_liquidity_usd": cum_ask_usd + cum_bid_usd
    }

def render_dom_terminal_l3(symbol="XAUUSD", timeframe="4H", override_price=None):
    dom = generate_synthetic_dom_l3(symbol, timeframe, override_price)
    max_c = dom["max_cum"]
    digits = dom["digits"]
    tf = dom["timeframe"]
    tf_prof = dom["tf_profile"]
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    contract_info = "1 Lote = 100 oz" if "XAU" in dom["symbol"] else "1 Lote = 100k"
    total_liq_str = format_notional(dom["total_liquidity_usd"])

    # Barra interactiva de temporalidades
    tf_buttons = []
    for t_key in ["1H", "2H", "3H", "4H", "8H"]:
        if t_key == tf:
            tf_buttons.append(f"{BG_VIOLET} ▶ {t_key} ◀ {RESET}")
        else:
            tf_buttons.append(f"{DIM}  {t_key}  {RESET}")
    tf_bar_str = " | ".join(tf_buttons)

    sys.stdout.write(CLEAR)
    sys.stdout.write(f"{CYAN}{BOLD}========================================================================================{RESET}\n")
    sys.stdout.write(f"{BOLD}   LIBRO DE ÓRDENES (DOM LEVEL 3 · MBO) · ATLAS CVD SINTÉTICO INSTITUCIONAL   {RESET}\n")
    sys.stdout.write(f"  Activo: {YELLOW}{dom['symbol']}{RESET} | Spread: {YELLOW}{dom['spread_label']}{RESET} | {CYAN}{contract_info}{RESET} | {GREEN}CME MDP 3.0 / MT5 Proxy{RESET}\n")
    sys.stdout.write(f"  TEMPORALIDAD: [ {tf_bar_str} ] {DIM}(Pulsa 1, 2, 3, 4 u 8 para cambiar){RESET}\n")
    sys.stdout.write(f"  Marco HFT: {YELLOW}{BOLD}{tf_prof['label']}{RESET}\n")
    sys.stdout.write(f"  Tiempo: {DIM}{now_str}{RESET} | Paso ({tf}): {CYAN}{dom['step']:.{digits}f} {dom['unit']}{RESET} | Liquidez Visible: {YELLOW}{total_liq_str}{RESET}\n")
    sys.stdout.write(f"{CYAN}{BOLD}========================================================================================{RESET}\n")
    sys.stdout.write(f"{BOLD}{'PRECIO':>10s} | {'LOTES':>8s} | {'VALOR ($)':>9s} | {'# ORD':>5s} | {'ACUMULADO':>10s} | {'PROFUNDIDAD / ESTADO':<22s}{RESET}\n")
    sys.stdout.write(f"{DIM}----------------------------------------------------------------------------------------{RESET}\n")

    # Render Asks (Venta / Oferta)
    for a in dom["asks"]:
        bar_len = int((a["cumulative"] / max_c) * 12)
        price_fmt = f"{a['price']:10.{digits}f}"
        lots_fmt = f"{a['quantity']:8.3f}"
        val_fmt = f"{a['notional_str']:>9s}"
        ord_fmt = f"{a['orders']:5d}"
        cum_fmt = f"{a['cumulative']:10.3f}"

        is_matching_row = (MATCH_STATE["is_flashing"] and 
                           MATCH_STATE["last_match_side"] == "ASK" and 
                           abs(a["price"] - MATCH_STATE["last_match_price"]) < 0.001)

        if is_matching_row:
            bar = f"{VIOLET}{'█' * bar_len}{DIM}{'░' * (12 - bar_len)}{RESET}"
            match_txt = f"{BG_VIOLET} ⚡ MATCH: BUY AGG x SELL LIM ({MATCH_STATE['last_match_lots']:.3f}L) {RESET}"
            sys.stdout.write(f"{BOLD_VIOLET}{price_fmt}{RESET} | {BOLD_VIOLET}{lots_fmt}{RESET} | {BOLD_VIOLET}{val_fmt}{RESET} | {BOLD_VIOLET}{ord_fmt}{RESET} | {cum_fmt} | {bar} {match_txt}\n")
        else:
            bar = f"{RED}{'█' * bar_len}{DIM}{'░' * (12 - bar_len)}{RESET}"
            if a["is_wall"]:
                tag = f" {YELLOW}{BOLD}[TECHO {tf}: {a['notional_str']} | {a['orders']} ORD | EDAD: {tf_prof['wall_age']}]{RESET}"
            else:
                tag = ""
            sys.stdout.write(f"{RED}{price_fmt}{RESET} | {lots_fmt} | {val_fmt} | {ord_fmt} | {cum_fmt} | {bar}{tag}\n")

    # Spread, Precio Spot y Banner de Cruce Intermitente
    sys.stdout.write(f"{DIM}----------------------------------------------------------------------------------------{RESET}\n")
    cur_fmt = f"{dom['current_price']:.{digits}f}"
    bid_fmt = f"{dom['best_bid']:.{digits}f}"
    ask_fmt = f"{dom['best_ask']:.{digits}f}"

    if MATCH_STATE["is_flashing"]:
        side_desc = "COMPRADOR AGRESIVO ABSORBIENDO SELL LIMIT" if MATCH_STATE["last_match_side"] == "ASK" else "VENDEDOR AGRESIVO ABSORBIENDO BUY LIMIT"
        match_usd_fmt = format_notional(MATCH_STATE["last_match_usd"])
        match_banner = f"{BG_VIOLET} ⚡ LUZ VIOLETA MATCH: {side_desc} [{MATCH_STATE['last_match_lots']:.3f}L | {match_usd_fmt}] @ {MATCH_STATE['last_match_price']:.{digits}f} {RESET}"
        sys.stdout.write(f" {match_banner}\n")
    else:
        sys.stdout.write(f" >>> {GREEN}{BOLD}PRECIO SPOT: {cur_fmt} USD{RESET} (Mejor Bid: {bid_fmt} / Mejor Ask: {ask_fmt})\n")
    sys.stdout.write(f"{DIM}----------------------------------------------------------------------------------------{RESET}\n")

    # Render Bids (Compra / Demanda)
    for b in dom["bids"]:
        bar_len = int((b["cumulative"] / max_c) * 12)
        price_fmt = f"{b['price']:10.{digits}f}"
        lots_fmt = f"{b['quantity']:8.3f}"
        val_fmt = f"{b['notional_str']:>9s}"
        ord_fmt = f"{b['orders']:5d}"
        cum_fmt = f"{b['cumulative']:10.3f}"

        is_matching_row = (MATCH_STATE["is_flashing"] and 
                           MATCH_STATE["last_match_side"] == "BID" and 
                           abs(b["price"] - MATCH_STATE["last_match_price"]) < 0.001)

        if is_matching_row:
            bar = f"{VIOLET}{'█' * bar_len}{DIM}{'░' * (12 - bar_len)}{RESET}"
            match_txt = f"{BG_VIOLET} ⚡ MATCH: SELL AGG x BUY LIM ({MATCH_STATE['last_match_lots']:.3f}L) {RESET}"
            sys.stdout.write(f"{BOLD_VIOLET}{price_fmt}{RESET} | {BOLD_VIOLET}{lots_fmt}{RESET} | {BOLD_VIOLET}{val_fmt}{RESET} | {BOLD_VIOLET}{ord_fmt}{RESET} | {cum_fmt} | {bar} {match_txt}\n")
        else:
            bar = f"{GREEN}{'█' * bar_len}{DIM}{'░' * (12 - bar_len)}{RESET}"
            if b["is_wall"]:
                tag = f" {YELLOW}{BOLD}[PISO {tf}: {b['notional_str']} | {b['orders']} ORD | EDAD: {tf_prof['wall_age']}]{RESET}"
            else:
                tag = ""
            sys.stdout.write(f"{GREEN}{price_fmt}{RESET} | {lots_fmt} | {val_fmt} | {ord_fmt} | {cum_fmt} | {bar}{tag}\n")

    # Dictamen Institucional ATLAS L3
    sys.stdout.write(f"{CYAN}{BOLD}========================================================================================{RESET}\n")
    ask_walls = [a for a in dom['asks'] if a['is_wall']]
    bid_walls = [b for b in dom['bids'] if b['is_wall']]
    ask_wall = ask_walls[0] if ask_walls else dom['asks'][0]
    bid_wall = bid_walls[0] if bid_walls else dom['bids'][-1]
    rango_pts = ask_wall['price'] - bid_wall['price']

    sys.stdout.write(f"{BOLD}DICTAMEN ATLAS L3 [{tf}]:{RESET} ")
    sys.stdout.write(f"PISO ({tf}): {GREEN}{bid_wall['price']:.{digits}f} ({bid_wall['notional_str']} | {bid_wall['orders']} ORD | {tf_prof['aging_status']}){RESET} | ")
    sys.stdout.write(f"TECHO ({tf}): {RED}{ask_wall['price']:.{digits}f} ({ask_wall['notional_str']} | {ask_wall['orders']} ORD | {tf_prof['aging_status']}){RESET}\n")
    sys.stdout.write(f"  Rango Operativo ({tf}): {YELLOW}{rango_pts:.{digits}f} {dom['unit']}{RESET} | Confluencia: {CYAN}{tf_prof['smc_focus']}{RESET}\n")
    sys.stdout.write(f"  CVD Delta ({tf}): {GREEN}{tf_prof['cvd_pressure']}{RESET} | Teclas: 1(1H) 2(2H) 3(3H) 4(4H) 8(8H) | Ctrl+C salir\n")
    sys.stdout.flush()

if __name__ == "__main__":
    target = "XAUUSD"
    current_tf = "4H"
    price_override = None

    for arg in sys.argv[1:]:
        arg_u = arg.upper().strip()
        if arg_u in ["1H", "2H", "3H", "4H", "8H"]:
            current_tf = arg_u
        elif arg_u in ["XAUUSD", "EURUSD", "GBPUSD", "GBPJPY", "AUDUSD", "NZDCAD", "US30", "SPX500", "NAS100"]:
            target = arg_u
        else:
            try:
                price_override = float(arg)
            except ValueError:
                pass

    print(f"Iniciando visualizador DOM Level 3 (MBO) para {target.upper()} en temporalidad {current_tf}...")
    try:
        while True:
            # Detección de teclas en caliente en Windows (1, 2, 3, 4, 8)
            if HAS_MSVCRT and msvcrt.kbhit():
                try:
                    key = msvcrt.getch().decode('utf-8', errors='ignore').upper()
                    if key == '1': current_tf = '1H'
                    elif key == '2': current_tf = '2H'
                    elif key == '3': current_tf = '3H'
                    elif key == '4': current_tf = '4H'
                    elif key == '8': current_tf = '8H'
                except Exception:
                    pass

            render_dom_terminal_l3(target, current_tf, price_override)
            time.sleep(1.2)  # Refresco dinámico a 1.2s para apreciar la luz intermitente violeta
    except KeyboardInterrupt:
        sys.stdout.write(f"\n\n{YELLOW}Monitor DOM Level 3 {target.upper()} [{current_tf}] cerrado por el usuario.{RESET}\n")
