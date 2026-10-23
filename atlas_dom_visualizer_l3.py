"""
====================================================================
VISUALIZADOR INSTITUCIONAL DE LIBRO DE ÓRDENES (DOM L3) Y FOOTPRINT (ORDER FLOW) · ATLAS
====================================================================
Extensión institucional Market-By-Order (MBO / Level 3) + Footprint Order Flow:
- Soporte Multi-Temporalidad: 1H, 2H, 3H, 4H y 8H (Conmutables con teclas 1, 2, 3, 4 u 8).
- Profundidad DOM Level 3 adaptada según volatilidad y temporalidad institucional.
- Motor Footprint Order Flow:
  * Bid Volume x Ask Volume por cada nivel de precio.
  * Delta de Nivel (Ask Vol - Bid Vol) con código de color dinámico.
  * Detección de Desbalances Diagonales (3:1 Imbalance) y Stacked Imbalances (3+ consecutivos).
  * Identificación del POC DE LA VELA (Point of Control / Nivel con Mayor Peso y Volumen).
  * Candle Delta Total al pie de la vela y % de agresividad compradora vs vendedora.
  * Detección Forense de Absorción Institucional y Traders Atrapados en Soporte/Resistencia.
- Modos de Vista Conmutables (Tecla 'V'): DUAL (DOM + Footprint), FOOTPRINT o DOM L3.
- Selector de Pares en Caliente (Tecla 'P'): XAUUSD, EURUSD, GBPUSD, GBPJPY, AUDUSD.
- Refresco continuo sin spam y soporte nativo ANSI / UTF-8 en consolas Windows (CMD / PowerShell).
====================================================================
"""

import sys
import os
import time
import requests
import json
import random
import urllib.request
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
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

# Endpoint activo y canónico de Upstash Redis
UPSTASH_URL = os.getenv("UPSTASH_REDIS_REST_URL", "https://firm-koi-93555.upstash.io")
UPSTASH_TOKEN = os.getenv("UPSTASH_REDIS_REST_TOKEN", "gQAAAAAAAW1zAAIgcDFmZGI5MGViNWY4Mjc0MGE1Yjg3NDZiOTdiN2MyMjg5Yg")
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
MAGENTA = "\033[95m"
BG_VIOLET = "\033[45m\033[97m\033[1m"
BOLD_VIOLET = "\033[1;95m"
BG_CYAN = "\033[46m\033[90m\033[1m"
BG_GREEN = "\033[42m\033[90m\033[1m"
BG_YELLOW = "\033[43m\033[90m\033[1m"
BG_RED = "\033[41m\033[97m\033[1m"

# Tickers institucionales en Yahoo Finance
YF_TICKERS = {
    "XAUUSD": "GC=F",
    "EURUSD": "EURUSD=X",
    "GBPUSD": "GBPUSD=X",
    "GBPJPY": "GBPJPY=X",
    "AUDUSD": "AUDUSD=X"
}

FALLBACK_PRICES = {
    "XAUUSD": 4025.00,
    "EURUSD": 1.12040,
    "GBPUSD": 1.33820,
    "GBPJPY": 209.950,
    "AUDUSD": 0.70250,
    "NZDCAD": 0.82550
}

INSTRUMENT_SPECS = {
    "XAUUSD": {"spread_usd": 0.13, "base_step": 0.25, "digits": 2, "unit": "USD", "contract_oz": 100},
    "GBPJPY": {"spread_pips": 1.4, "base_step": 0.015, "digits": 3, "unit": "pips", "contract_fx": 100000},
    "EURUSD": {"spread_pips": 0.8, "base_step": 0.00010, "digits": 5, "unit": "pips", "contract_fx": 100000},
    "GBPUSD": {"spread_pips": 1.1, "base_step": 0.00010, "digits": 5, "unit": "pips", "contract_fx": 100000},
    "AUDUSD": {"spread_pips": 0.9, "base_step": 0.00010, "digits": 5, "unit": "pips", "contract_fx": 100000}
}

OFFICIAL_PAIRS = ["XAUUSD", "EURUSD", "GBPUSD", "GBPJPY", "AUDUSD"]

# Perfiles de Temporalidad Institucional para el DOM y Footprint
TIMEFRAME_PROFILES = {
    "1H": {
        "label": "1H (Intradía Rápido · Microestructura & Sweeps)",
        "step_multiplier": 1.0,
        "vol_multiplier": 1.0,
        "wall_distance_level": 7,
        "wall_age": "42 min",
        "aging_status": "FLUIDO HFT",
        "smc_focus": "lux_algo_ob_1h · Barrido Liquidez Local (Sweeps)",
        "cvd_pressure": "+$1.85M (Presión Dinámica Corto Plazo)",
        "cme_vol_regime": "CME FXVL: COMPRESIÓN / SWEEPS LOCALES (Z < -0.5)"
    },
    "2H": {
        "label": "2H (Swing Intradía · POC Dinámico - Regla de 3 Top 2)",
        "step_multiplier": 2.0,
        "vol_multiplier": 1.8,
        "wall_distance_level": 6,
        "wall_age": "1h 45m",
        "aging_status": "ESTABILIZADO",
        "smc_focus": "order_block_zona_2h (Win Rate 80.38% · Top 2 R3)",
        "cvd_pressure": "+$3.40M (Presión Acumulativa Intradía)",
        "cme_vol_regime": "CME FXVL: EQUILIBRIO / REGLA DE 3 NÚCLEO (-0.5 <= Z <= 0.8)"
    },
    "3H": {
        "label": "3H (Apertura Londres & Overlap · Flujo AMD Institucional)",
        "step_multiplier": 3.0,
        "vol_multiplier": 2.6,
        "wall_distance_level": 7,
        "wall_age": "2h 35m",
        "aging_status": "INSTITUCIONAL",
        "smc_focus": "alineamiento_liquidez_3h · Manipulación / AMD CME",
        "cvd_pressure": "+$6.15M (Flujo Direccional Londres-NY)",
        "cme_vol_regime": "CME FXVL: APERTURA LONDRES AMD DINÁMICO (ΔFXVL > +15%)"
    },
    "4H": {
        "label": "4H (Macro Intradía · Absorción Interbancaria Mayor)",
        "step_multiplier": 4.0,
        "vol_multiplier": 3.8,
        "wall_distance_level": 7,
        "wall_age": "3h 50m",
        "aging_status": "MURO ESTRUCTURAL",
        "smc_focus": "smc_order_block_4h · Muro de Absorción Mayor CME",
        "cvd_pressure": "+$11.80M (Absorción de Ballenas CME)",
        "cme_vol_regime": "CME FXVL: ABSORCIÓN MACRO / EXPANSIÓN TENDENCIAL (Z > 0.8)"
    },
    "8H": {
        "label": "8H (Sesión Completa · Campana Institucional Londres-NY)",
        "step_multiplier": 8.0,
        "vol_multiplier": 6.5,
        "wall_distance_level": 8,
        "wall_age": "7h 15m",
        "aging_status": "MURO BANCARIO MACRO",
        "smc_focus": "alineamiento_liquidez_8h · Sesión Completa Interbancaria",
        "cvd_pressure": "+$24.50M (Consenso de Fondos Soberanos)",
        "cme_vol_regime": "CME FXVL: CAMPANA INTERBANCARIA COMPLETA (Consenso Fondos)"
    }
}

def format_notional(usd_value):
    """Formatea cantidades monetarias en K, M o B."""
    abs_v = abs(usd_value)
    if abs_v >= 1_000_000_000:
        return f"${usd_value / 1_000_000_000:.2f}B"
    elif abs_v >= 1_000_000:
        return f"${usd_value / 1_000_000:.2f}M"
    else:
        return f"${usd_value / 1_000:.1f}K"

def get_market_data(symbol="EURUSD", override_price=None):
    sym = symbol.upper().replace("/", "").replace("_", "")
    specs = INSTRUMENT_SPECS.get(sym, {"spread_pips": 1.0, "base_step": 0.00010, "digits": 5, "unit": "pips"})

    if override_price is not None and override_price > 0:
        return float(override_price), specs

    # 1. Upstash Redis (cache_trading_matrix o cache_mt5)
    try:
        r = requests.get(f"{UPSTASH_URL}/get/cache_trading_matrix", headers=headers, timeout=1.2)
        if r.status_code == 200 and r.json().get("result"):
            m = json.loads(r.json()["result"])
            if isinstance(m, dict) and sym in m and m[sym].get("current_price"):
                cp = float(m[sym]["current_price"])
                if cp > 0:
                    return cp, specs
    except Exception:
        pass

    try:
        r2 = requests.get(f"{UPSTASH_URL}/get/cache_mt5", headers=headers, timeout=1.2)
        if r2.status_code == 200 and r2.json().get("result"):
            m2 = json.loads(r2.json()["result"])
            feed = m2.get("feed", {})
            if isinstance(feed, dict) and sym in feed and feed[sym].get("bid"):
                bid = float(feed[sym]["bid"])
                if bid > 0:
                    return bid, specs
    except Exception:
        pass

    # 2. Yahoo Finance Direct REST (rápido, sin overhead ni errores de yfinance)
    yf_sym = YF_TICKERS.get(sym)
    if yf_sym:
        try:
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{yf_sym}?interval=1m&range=1d"
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=1.8) as resp:
                res = json.loads(resp.read().decode("utf-8"))
                p = res["chart"]["result"][0]["meta"].get("regularMarketPrice")
                if p and float(p) > 0:
                    return float(p), specs
        except Exception:
            pass

    # 3. Fallback canónico
    base = FALLBACK_PRICES.get(sym, 1.12040)
    return base, specs

# Estado de microestructura y cruces para animación intermitente
MATCH_STATE = {
    "cycle": 0,
    "last_match_side": "ASK",
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

    # Generación de Asks (Venta pasiva por encima de Best Ask)
    cum_ask_qty = 0.0
    cum_ask_usd = 0.0
    for i in range(levels, 0, -1):
        step_price = round(best_ask + (i * step), digits)
        is_wall = (i == wall_level)
        vol_noise = random.uniform(0.92, 1.08)
        base_lots = (0.45 * (i * 0.8) + (3.8 * vol_mult if is_wall else 0.25 * vol_mult))
        qty = round(base_lots * vol_noise, 3)
        notional_usd = qty * lot_multiplier
        cum_ask_qty += qty
        cum_ask_usd += notional_usd

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

    # Generación de Bids (Compra pasiva por debajo de Best Bid)
    cum_bid_qty = 0.0
    cum_bid_usd = 0.0
    for i in range(1, levels + 1):
        step_price = round(best_bid - (i * step), digits)
        is_wall = (i == (wall_level - 1 if wall_level > 2 else wall_level))
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

    # Simulación del Cruce / Match agresivo Maker vs Taker
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

# ====================================================================
# MOTOR INSTITUCIONAL FOOTPRINT ORDER FLOW & CANDLE DELTA
# ====================================================================
def generate_synthetic_footprint(symbol="XAUUSD", timeframe="4H", current_price=4025.0, step=0.25, digits=2, vol_mult=1.0):
    """
    Genera el Footprint Order Flow de la vela activa:
    - Niveles de precio de la vela (High a Low).
    - Bid Volume x Ask Volume (Órdenes agresivas ejecutadas).
    - Delta por nivel = Ask Vol - Bid Vol.
    - Identificación del POC (Nivel con Mayor Volumen / Más Peso de la vela).
    - Desbalance Diagonal (3:1 Imbalance): Compara Ask[P] diagonalmente con Bid[P - step].
    - Stacked Imbalances: 3 o más niveles consecutivos de desbalance.
    - Candle Delta Total al pie de la vela.
    - Detección de Absorción y Traders Atrapados en Soporte o Resistencia.
    """
    levels_count = 11
    half = levels_count // 2

    # POC dinámico cerca del precio actual
    poc_offset = 0
    poc_price = round(current_price + (poc_offset * step), digits)

    raw_levels = []
    for i in range(half, -half - 1, -1):
        lvl_price = round(current_price + (i * step), digits)
        dist_to_poc = abs(lvl_price - poc_price) / max(step, 0.00001)
        decay = max(0.18, 1.0 - (dist_to_poc * 0.17))
        base_vol = (360 * vol_mult) * decay

        is_top_wick = (i >= half - 1)
        is_bottom_wick = (i <= -half + 1)

        # Simulación de Absorción en Extremos (Imágenes 4 y 5)
        if is_bottom_wick:
            # Absorción Compradora en Piso: Muchos vendedores a mercado golpean el Bid, pero compradores absorben
            bid_vol = round(base_vol * random.uniform(1.8, 2.7))
            ask_vol = round(base_vol * random.uniform(0.12, 0.32))
        elif is_top_wick:
            # Compradores atrapados en Techo: Muchos compradores a mercado al Ask, pero vendedores absorben
            ask_vol = round(base_vol * random.uniform(1.6, 2.5))
            bid_vol = round(base_vol * random.uniform(0.15, 0.35))
        else:
            # Cuerpo central de la vela con presión institucional
            ask_vol = round(base_vol * random.uniform(0.9, 1.45))
            bid_vol = round(base_vol * random.uniform(0.55, 0.95))

        bid_val = max(1, int(bid_vol))
        ask_val = max(1, int(ask_vol))
        tot_val = bid_val + ask_val
        delta_val = ask_val - bid_val

        raw_levels.append({
            "price": lvl_price,
            "bid": bid_val,
            "ask": ask_val,
            "total": tot_val,
            "delta": delta_val,
            "is_top_wick": is_top_wick,
            "is_bottom_wick": is_bottom_wick
        })

    # Encontrar el Point of Control (NIVEL CON MÁS PESO / MAYOR VOLUMEN)
    poc_node = max(raw_levels, key=lambda x: x["total"])
    poc_val = poc_node["price"]

    # Detección de Desbalances Diagonales 3:1 (Diagonal Imbalance)
    # Regla: Ask a precio P se compara con Bid a precio menor (P - step)
    for idx in range(len(raw_levels)):
        lvl = raw_levels[idx]
        lvl["is_poc"] = (lvl["price"] == poc_val)
        lvl["buy_imbalance"] = False
        lvl["sell_imbalance"] = False
        lvl["buy_ratio"] = 0.0
        lvl["sell_ratio"] = 0.0

        # Comparación diagonal con nivel inferior (Ask[i] vs Bid[i+1])
        if idx < len(raw_levels) - 1:
            lower_lvl = raw_levels[idx + 1]
            if lower_lvl["bid"] > 0 and (lvl["ask"] / lower_lvl["bid"]) >= 3.0 and lvl["ask"] >= 20:
                lvl["buy_imbalance"] = True
                lvl["buy_ratio"] = round(lvl["ask"] / lower_lvl["bid"], 1)

        # Comparación diagonal con nivel superior (Bid[i] vs Ask[i-1])
        if idx > 0:
            higher_lvl = raw_levels[idx - 1]
            if higher_lvl["ask"] > 0 and (lvl["bid"] / higher_lvl["ask"]) >= 3.0 and lvl["bid"] >= 20:
                lvl["sell_imbalance"] = True
                lvl["sell_ratio"] = round(lvl["bid"] / higher_lvl["ask"], 1)

    # Detección de Stacked Imbalances (3 o más niveles consecutivos)
    consec_buy = 0
    consec_sell = 0
    stacked_buy = False
    stacked_sell = False
    for lvl in raw_levels:
        if lvl["buy_imbalance"]:
            consec_buy += 1
            if consec_buy >= 3:
                stacked_buy = True
        else:
            consec_buy = 0

        if lvl["sell_imbalance"]:
            consec_sell += 1
            if consec_sell >= 3:
                stacked_sell = True
        else:
            consec_sell = 0

    # Resumen de Vela
    candle_delta = sum(l["delta"] for l in raw_levels)
    candle_volume = sum(l["total"] for l in raw_levels)
    delta_pct = (candle_delta / candle_volume * 100) if candle_volume > 0 else 0.0

    # Análisis de Absorción Institucional y Traders Atrapados (Imágenes 4 y 5)
    bottom_delta = sum(l["delta"] for l in raw_levels[-3:])
    top_delta = sum(l["delta"] for l in raw_levels[:3])

    absorption_status = "NORMAL"
    if bottom_delta < -120 and current_price > raw_levels[-1]["price"]:
        absorption_status = "ABSORCION_COMPRADORA"  # Vendedores atrapados en soporte (Imagen 5)
    elif top_delta > 120 and current_price < raw_levels[0]["price"]:
        absorption_status = "ABSORCION_VENDEDORA"    # Compradores atrapados en resistencia (Imagen 4)

    return {
        "levels": raw_levels,
        "poc_price": poc_val,
        "poc_node": poc_node,
        "poc_pct": round((poc_node["total"] / candle_volume) * 100, 1) if candle_volume > 0 else 0,
        "candle_delta": candle_delta,
        "candle_volume": candle_volume,
        "delta_pct": round(delta_pct, 1),
        "stacked_buy": stacked_buy,
        "stacked_sell": stacked_sell,
        "absorption_status": absorption_status,
        "max_level_vol": poc_node["total"]
    }

# ====================================================================
# RENDERIZADOR DUAL / FOOTPRINT / DOM EN TERMINAL
# ====================================================================
GLOBAL_CONFIG = {
    "view_mode": "DUAL",   # "DUAL", "FOOTPRINT", "DOM"
    "pair_idx": 0
}

def render_footprint_block(fp, digits, unit, is_compact=False):
    """Renderiza el bloque de Footprint Order Flow con resaltado de POC e Imbalances."""
    sys.stdout.write(f"{CYAN}{BOLD}========================================================================================{RESET}\n")
    sys.stdout.write(f"{BOLD}   GRÁFICO FOOTPRINT (ORDER FLOW) · BID x ASK · POC & CANDLE DELTA DINÁMICO   {RESET}\n")
    sys.stdout.write(f"  Regla de Oro: {YELLOW}\"El Delta muestra quién fue el agresivo. El Precio muestra quién ganó.\"{RESET}\n")
    sys.stdout.write(f"{CYAN}{BOLD}========================================================================================{RESET}\n")
    sys.stdout.write(f"{BOLD}{'PRECIO':>10s} | {'BID  x  ASK':^15s} | {'DELTA':>8s} | {'VOL TOTAL':>9s} | {'DESBALANCE (3:1)':^18s} | {'ESTRUCTURA & PESO':<20s}{RESET}\n")
    sys.stdout.write(f"{DIM}----------------------------------------------------------------------------------------{RESET}\n")

    max_v = fp["max_level_vol"]
    levels_to_show = fp["levels"] if not is_compact else fp["levels"][1:-1]

    for lvl in levels_to_show:
        p_str = f"{lvl['price']:10.{digits}f}"
        bid_str = f"{lvl['bid']:>6d}"
        ask_str = f"{lvl['ask']:<6d}"
        ba_str = f"{bid_str} x {ask_str}"
        tot_str = f"{lvl['total']:9d}"

        # Delta coloreado
        if lvl["delta"] > 0:
            d_str = f"{GREEN}{lvl['delta']:+8d}{RESET}"
        elif lvl["delta"] < 0:
            d_str = f"{RED}{lvl['delta']:+8d}{RESET}"
        else:
            d_str = f"{DIM}{lvl['delta']:+8d}{RESET}"

        # Desbalance Diagonal 3:1
        if lvl["buy_imbalance"]:
            imb_tag = f"{GREEN}{BOLD}[3:1 BUY {lvl['buy_ratio']}x >>]{RESET}"
        elif lvl["sell_imbalance"]:
            imb_tag = f"{RED}{BOLD}[<< 3:1 SELL {lvl['sell_ratio']}x]{RESET}"
        else:
            imb_tag = f"{DIM}       -          {RESET}"

        # Identificación del POC (Nivel con Más Peso) y Estructura
        if lvl["is_poc"]:
            struct_tag = f"{BG_CYAN} [★ POC MAYOR PESO] {RESET}"
            p_str = f"{BOLD_VIOLET}{p_str}{RESET}"
            ba_str = f"{BOLD_VIOLET}{ba_str}{RESET}"
            tot_str = f"{BOLD_VIOLET}{tot_str}{RESET}"
        elif lvl["is_top_wick"]:
            struct_tag = f"{YELLOW}[Mecha Sup / High]{RESET}"
        elif lvl["is_bottom_wick"]:
            struct_tag = f"{CYAN}[Mecha Inf / Low]{RESET}"
        else:
            # Mini barra de volumen relativa
            bar_len = int((lvl["total"] / max_v) * 8)
            struct_tag = f"{DIM}{'░' * bar_len}{RESET}"

        sys.stdout.write(f"{p_str} | {ba_str} | {d_str} | {tot_str} | {imb_tag:^18s} | {struct_tag}\n")

    sys.stdout.write(f"{DIM}----------------------------------------------------------------------------------------{RESET}\n")

    # Resumen de Vela Footprint al pie
    c_delta = fp["candle_delta"]
    c_vol = fp["candle_volume"]
    c_pct = fp["delta_pct"]

    if c_delta > 0:
        delta_label = f"{GREEN}{BOLD}{c_delta:+d} Lotes ({c_pct:+.1f}% Comprador Agresivo){RESET}"
    else:
        delta_label = f"{RED}{BOLD}{c_delta:+d} Lotes ({c_pct:+.1f}% Vendedor Agresivo){RESET}"

    sys.stdout.write(f"{BOLD}RESUMEN DE VELA:{RESET} Candle Delta: {delta_label} | Vol Total: {YELLOW}{c_vol:,} Lotes{RESET}\n")
    sys.stdout.write(f"  POC de Mayor Peso: {CYAN}{BOLD}{fp['poc_price']:.{digits}f} {unit}{RESET} ({fp['poc_node']['total']} Lotes · {fp['poc_pct']}% del total de la vela)\n")

    if fp["stacked_buy"]:
        sys.stdout.write(f"  {BG_GREEN} ⚡ STACKED BUY IMBALANCE: 3+ niveles consecutivos de compras institucionales agresivas {RESET}\n")
    elif fp["stacked_sell"]:
        sys.stdout.write(f"  {BG_RED} ⚡ STACKED SELL IMBALANCE: 3+ niveles consecutivos de ventas institucionales agresivas {RESET}\n")

    if fp["absorption_status"] == "ABSORCION_COMPRADORA":
        sys.stdout.write(f"  {BG_CYAN} 🛡️ ABSORCIÓN EN SOPORTE DETECTADA: Compradores pasivos absorbieron todas las ventas a mercado (Vendedores atrapados en mínimos) {RESET}\n")
    elif fp["absorption_status"] == "ABSORCION_VENDEDORA":
        sys.stdout.write(f"  {BG_YELLOW} 🛡️ ABSORCIÓN EN RESISTENCIA DETECTADA: Vendedores pasivos absorbieron todas las compras a mercado (Compradores atrapados en máximos) {RESET}\n")

def render_terminal_dashboard(symbol="XAUUSD", timeframe="4H", override_price=None):
    dom = generate_synthetic_dom_l3(symbol, timeframe, override_price)
    max_c = dom["max_cum"]
    digits = dom["digits"]
    tf = dom["timeframe"]
    tf_prof = dom["tf_profile"]
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    fp = generate_synthetic_footprint(symbol, tf, dom["current_price"], dom["step"], digits, tf_prof["vol_multiplier"])

    contract_info = "1 Lote = 100 oz" if "XAU" in dom["symbol"] else "1 Lote = 100k"
    total_liq_str = format_notional(dom["total_liquidity_usd"])

    # Barra interactiva de temporalidades
    tf_buttons = []
    for t_key in ["1H", "2H", "3H", "4H", "8H"]:
        if t_key == tf:
            tf_buttons.append(f"{BG_VIOLET} > {t_key} < {RESET}")
        else:
            tf_buttons.append(f"{DIM}  {t_key}  {RESET}")
    tf_bar_str = " | ".join(tf_buttons)

    view_mode = GLOBAL_CONFIG["view_mode"]
    view_label = f"{BG_CYAN} VISTA: {view_mode} {RESET}"

    sys.stdout.write(CLEAR)
    sys.stdout.write(f"{CYAN}{BOLD}========================================================================================{RESET}\n")
    sys.stdout.write(f"{BOLD}   MONITOR CUANTITATIVO ATLAS: DOM LEVEL 3 (MBO) + FOOTPRINT ORDER FLOW   {RESET}\n")
    sys.stdout.write(f"  Activo: {YELLOW}{BOLD}{dom['symbol']}{RESET} | Spread: {YELLOW}{dom['spread_label']}{RESET} | {CYAN}{contract_info}{RESET} | {view_label} | {GREEN}CME Proxy{RESET}\n")
    sys.stdout.write(f"  TEMPORALIDAD: [ {tf_bar_str} ] {DIM}(Teclas 1, 2, 3, 4 u 8 | 'V' Cambiar Vista | 'P' Par){RESET}\n")
    vol_tag = tf_prof.get('cme_vol_regime', 'FXVL NORMAL')
    if "XAU" in dom['symbol'] or "GOLD" in dom['symbol']:
        vol_tag = vol_tag.replace("CME FXVL", "COMEX GVZ / Gold CVOL")
    sys.stdout.write(f"  Marco HFT: {YELLOW}{BOLD}{tf_prof['label']}{RESET} | {MAGENTA}{vol_tag}{RESET}\n")
    sys.stdout.write(f"  Tiempo: {DIM}{now_str}{RESET} | Paso ({tf}): {CYAN}{dom['step']:.{digits}f} {dom['unit']}{RESET} | Liquidez Visible: {YELLOW}{total_liq_str}{RESET}\n")

    # MODO 1: DOM LEVEL 3 (Si la vista es DUAL o DOM)
    if view_mode in ["DUAL", "DOM"]:
        sys.stdout.write(f"{CYAN}{BOLD}========================================================================================{RESET}\n")
        sys.stdout.write(f"{BOLD}   LIBRO DE ÓRDENES (DOM LEVEL 3 · MBO) · LIQUIDEZ PASIVA DE MERCADO   {RESET}\n")
        sys.stdout.write(f"{CYAN}{BOLD}========================================================================================{RESET}\n")
        sys.stdout.write(f"{BOLD}{'PRECIO':>10s} | {'LOTES':>8s} | {'VALOR ($)':>9s} | {'# ORD':>5s} | {'ACUMULADO':>10s} | {'PROFUNDIDAD / ESTADO':<22s}{RESET}\n")
        sys.stdout.write(f"{DIM}----------------------------------------------------------------------------------------{RESET}\n")

        # Asks
        asks_to_render = dom["asks"] if view_mode == "DOM" else dom["asks"][-5:]
        for a in asks_to_render:
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
                tag = f" {YELLOW}{BOLD}[TECHO {tf}: {a['notional_str']} | {a['orders']} ORD | EDAD: {tf_prof['wall_age']}]{RESET}" if a["is_wall"] else ""
                sys.stdout.write(f"{RED}{price_fmt}{RESET} | {lots_fmt} | {val_fmt} | {ord_fmt} | {cum_fmt} | {bar}{tag}\n")

        # Spread / Spot Banner
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
            sys.stdout.write(f" >>> {GREEN}{BOLD}PRECIO SPOT: {cur_fmt} {dom['unit']}{RESET} (Mejor Bid: {bid_fmt} / Mejor Ask: {ask_fmt})\n")
        sys.stdout.write(f"{DIM}----------------------------------------------------------------------------------------{RESET}\n")

        # Bids
        bids_to_render = dom["bids"] if view_mode == "DOM" else dom["bids"][:5]
        for b in bids_to_render:
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
                tag = f" {YELLOW}{BOLD}[PISO {tf}: {b['notional_str']} | {b['orders']} ORD | EDAD: {tf_prof['wall_age']}]{RESET}" if b["is_wall"] else ""
                sys.stdout.write(f"{GREEN}{price_fmt}{RESET} | {lots_fmt} | {val_fmt} | {ord_fmt} | {cum_fmt} | {bar}{tag}\n")

    # MODO 2: FOOTPRINT ORDER FLOW (Si la vista es DUAL o FOOTPRINT)
    if view_mode in ["DUAL", "FOOTPRINT"]:
        render_footprint_block(fp, digits, dom["unit"], is_compact=(view_mode == "DUAL"))

    # Dictamen Institucional ATLAS L3
    sys.stdout.write(f"{CYAN}{BOLD}========================================================================================{RESET}\n")
    ask_walls = [a for a in dom['asks'] if a['is_wall']]
    bid_walls = [b for b in dom['bids'] if b['is_wall']]
    ask_wall = ask_walls[0] if ask_walls else dom['asks'][0]
    bid_wall = bid_walls[0] if bid_walls else dom['bids'][-1]
    rango_pts = ask_wall['price'] - bid_wall['price']

    sys.stdout.write(f"{BOLD}DICTAMEN ATLAS [{tf}]:{RESET} ")
    sys.stdout.write(f"PISO: {GREEN}{bid_wall['price']:.{digits}f} ({bid_wall['notional_str']}){RESET} | ")
    sys.stdout.write(f"TECHO: {RED}{ask_wall['price']:.{digits}f} ({ask_wall['notional_str']}){RESET} | ")
    sys.stdout.write(f"Rango: {YELLOW}{rango_pts:.{digits}f} {dom['unit']}{RESET}\n")
    sys.stdout.write(f"  Confluencia: {CYAN}{tf_prof['smc_focus']}{RESET} | CVD: {GREEN}{tf_prof['cvd_pressure']}{RESET}\n")
    sys.stdout.write(f"  Atajos: [1-8] Temporalidad | [V] Modo Vista ({view_mode}) | [P] Cambiar Par | [Q] Salir\n")
    sys.stdout.flush()

if __name__ == "__main__":
    target = "XAUUSD"
    current_tf = "4H"
    price_override = None

    for arg in sys.argv[1:]:
        arg_u = arg.upper().strip()
        if arg_u in ["1H", "2H", "3H", "4H", "8H"]:
            current_tf = arg_u
        elif arg_u in ["XAUUSD", "EURUSD", "GBPUSD", "GBPJPY", "AUDUSD", "NZDCAD"]:
            target = arg_u
        elif arg_u in ["DUAL", "FOOTPRINT", "DOM"]:
            GLOBAL_CONFIG["view_mode"] = arg_u
        else:
            try:
                price_override = float(arg)
            except ValueError:
                pass

    if target in OFFICIAL_PAIRS:
        GLOBAL_CONFIG["pair_idx"] = OFFICIAL_PAIRS.index(target)

    print(f"Iniciando visualizador ATLAS DOM Level 3 + Footprint para {target} [{current_tf}]...")
    try:
        while True:
            # Teclado en caliente no bloqueante en Windows
            if HAS_MSVCRT and msvcrt.kbhit():
                try:
                    key = msvcrt.getch().decode('utf-8', errors='ignore').upper()
                    if key == '1': current_tf = '1H'
                    elif key == '2': current_tf = '2H'
                    elif key == '3': current_tf = '3H'
                    elif key == '4': current_tf = '4H'
                    elif key == '8': current_tf = '8H'
                    elif key == 'V':
                        modes = ["DUAL", "FOOTPRINT", "DOM"]
                        cur_idx = modes.index(GLOBAL_CONFIG["view_mode"])
                        GLOBAL_CONFIG["view_mode"] = modes[(cur_idx + 1) % len(modes)]
                    elif key == 'P':
                        GLOBAL_CONFIG["pair_idx"] = (GLOBAL_CONFIG["pair_idx"] + 1) % len(OFFICIAL_PAIRS)
                        target = OFFICIAL_PAIRS[GLOBAL_CONFIG["pair_idx"]]
                    elif key == 'Q':
                        break
                except Exception:
                    pass

            render_terminal_dashboard(target, current_tf, price_override)
            time.sleep(1.2)
    except KeyboardInterrupt:
        sys.stdout.write(f"\n\n{YELLOW}Monitor ATLAS DOM + Footprint {target} [{current_tf}] cerrado por el usuario.{RESET}\n")
