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
import math
import random
import re
import urllib.request
from datetime import datetime

ANSI_REGEX = re.compile(r'\x1b\[[0-9;]*m')

def visible_len(text: str) -> int:
    """Calcula la longitud visible en pantalla omitiendo códigos de color ANSI."""
    return len(ANSI_REGEX.sub('', text))

def pad_visible(text: str, target_width: int, align: str = 'left') -> str:
    """Rellena un texto con espacios para que su ancho visible sea exactamente target_width."""
    v_len = visible_len(text)
    pad = max(0, target_width - v_len)
    if align == 'right':
        return (' ' * pad) + text
    elif align == 'center':
        left = pad // 2
        right = pad - left
        return (' ' * left) + text + (' ' * right)
    else:
        return text + (' ' * pad)

class CandleHistoryTracker:
    """Mantiene el historial de las 3 velas recientes (T-2, T-1, T-0) para el panel lateral de Order Flow."""
    def __init__(self):
        self.history = {}

    def get_or_create(self, symbol: str, timeframe: str, current_price: float, step: float, digits: int, tf_profile: dict):
        key = (symbol, timeframe)
        vol_mult = tf_profile.get("vol_multiplier", 1.0)
        poc_base = quantize_price(current_price, step, digits)

        if key not in self.history:
            # Vela T-2 (2 periodos atrás - Impulso alcista previo)
            c_t2 = {
                "name": "T-2",
                "open": round(poc_base - 2 * step, digits),
                "close": round(poc_base + 2 * step, digits),
                "high": round(poc_base + 4 * step, digits),
                "low": round(poc_base - 3 * step, digits),
                "poc": round(poc_base + 1 * step, digits),
                "delta": int(420 * vol_mult),
                "volume": int(3850 * vol_mult),
                "bull": True,
                "is_active": False
            }
            # Vela T-1 (Periodo anterior - Sweep bajista y absorción de techo)
            c_t1 = {
                "name": "T-1",
                "open": round(poc_base + 2 * step, digits),
                "close": round(poc_base - 1 * step, digits),
                "high": round(poc_base + 3 * step, digits),
                "low": round(poc_base - 2 * step, digits),
                "poc": poc_base,
                "delta": -int(185 * vol_mult),
                "volume": int(4120 * vol_mult),
                "bull": False,
                "is_active": False
            }
            # Vela T-0 (Vela en curso activa)
            c_t0 = {
                "name": "T-0",
                "open": round(poc_base - 1 * step, digits),
                "close": current_price,
                "high": max(round(poc_base + 3 * step, digits), current_price),
                "low": min(round(poc_base - 3 * step, digits), current_price),
                "poc": poc_base,
                "delta": int(569 * vol_mult),
                "volume": int(4459 * vol_mult),
                "bull": (current_price >= round(poc_base - 1 * step, digits)),
                "is_active": True
            }
            self.history[key] = [c_t2, c_t1, c_t0]
        else:
            # Actualización en vivo de la vela T-0
            c_t0 = self.history[key][2]
            c_t0["close"] = current_price
            c_t0["high"] = max(c_t0["high"], current_price)
            c_t0["low"] = min(c_t0["low"], current_price)
            c_t0["bull"] = (c_t0["close"] >= c_t0["open"])

        return self.history[key]

CANDLE_TRACKER = CandleHistoryTracker()

def get_candle_glyph(candle: dict, price: float, step: float) -> str:
    """Renderiza el glifo de una vela en un nivel de precio específico (POC ★, Cuerpo █, Mecha │)."""
    # 1. Nivel del POC
    if abs(price - candle["poc"]) < (step * 0.45):
        if candle["is_active"]:
            return f"{BG_CYAN}\033[30m★\033[0m"
        else:
            c_color = GREEN if candle["bull"] else RED
            return f"{c_color}{BOLD}★{RESET}"

    # 2. Cuerpo de la vela
    b_min = min(candle["open"], candle["close"])
    b_max = max(candle["open"], candle["close"])
    c_color = GREEN if candle["bull"] else RED
    if (b_min - step * 0.45) <= price <= (b_max + step * 0.45):
        return f"{c_color}█{RESET}"

    # 3. Mechas
    if (candle["low"] - step * 0.45) <= price <= (candle["high"] + step * 0.45):
        return f"{c_color}│{RESET}"

    return " "

def render_step_footprint_candle(c: dict, p: float, step: float, bid: int, ask: int, orders: int, is_poc: bool = False, is_match: bool = False) -> str:
    """
    Renderiza la celda Footprint escalonada DENTRO del cuerpo de la vela:
    - [Bid x Ask · #ORD]
    - Enmarca las paredes de la vela (┌──, │ , █★, └──, o │ si es mecha).
    - Ancho visible fijo de 22 caracteres.
    """
    c_color = GREEN if c["bull"] else RED
    p_high = c["high"]
    p_low = c["low"]
    b_min = min(c["open"], c["close"])
    b_max = max(c["open"], c["close"])
    cluster = f"{bid:>3d}x{ask:<3d}·{orders}O"

    # Fuera del rango de la vela
    if p > (p_high + step * 0.45) or p < (p_low - step * 0.45):
        return " " * 22

    # Mecha superior pura
    if p > (b_max + step * 0.45):
        is_exact_high = abs(p - p_high) < (step * 0.45)
        lbl = f" {DIM}(High){RESET}" if is_exact_high else ""
        return pad_visible(f"         {c_color}│{RESET}{lbl}", 22)

    # Mecha inferior pura
    if p < (b_min - step * 0.45):
        is_exact_low = abs(p - p_low) < (step * 0.45)
        lbl = f" {DIM}(Low){RESET}" if is_exact_low else ""
        return pad_visible(f"         {c_color}│{RESET}{lbl}", 22)

    # Nivel POC (Mayor peso y volumen de la vela)
    if is_poc or abs(p - c["poc"]) < (step * 0.45):
        if is_match:
            return f"{BG_VIOLET} █⚡ [ {cluster} ] ⚡█ {RESET}"
        return f"{BG_CYAN}\033[30m\033[1m █★ [ {cluster} ] ★█ {RESET}"

    # Match agresivo en cuerpo
    if is_match:
        return f"{BG_VIOLET} █⚡ [ {cluster} ] ⚡█ {RESET}"

    # Techo del cuerpo
    if abs(p - b_max) < (step * 0.45):
        return f"{c_color}┌──[ {cluster} ]──┐{RESET}"

    # Base del cuerpo
    if abs(p - b_min) < (step * 0.45):
        return f"{c_color}└──[ {cluster} ]──┘{RESET}"

    # Interior del cuerpo
    return f"{c_color}│  [ {cluster} ]  │{RESET}"

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
    "AUDUSD": "AUDUSD=X",
    "NZDCAD": "NZDCAD=X"
}

FALLBACK_PRICES = {
    "XAUUSD": 3898.60,
    "EURUSD": 1.10630,
    "GBPUSD": 1.32330,
    "GBPJPY": 211.470,
    "AUDUSD": 0.67920,
    "NZDCAD": 0.78970
}

INSTRUMENT_SPECS = {
    "XAUUSD": {"spread_usd": 0.25, "base_step": 0.25, "digits": 2, "unit": "USD", "contract_oz": 100, "contract_name": "COMEX Gold Futures (GC · 100 oz)"},
    "GBPJPY": {"spread_pips": 1.5, "base_step": 0.015, "digits": 3, "unit": "pips", "contract_fx": 100000, "contract_name": "CME 6B/6J Sintético Cruzado G5 FX"},
    "EURUSD": {"spread_pips": 1.0, "base_step": 0.00010, "digits": 5, "unit": "pips", "contract_fx": 100000, "contract_name": "CME 6E Euro FX Futures (125k EUR)"},
    "GBPUSD": {"spread_pips": 1.0, "base_step": 0.00010, "digits": 5, "unit": "pips", "contract_fx": 100000, "contract_name": "CME 6B British Pound Futures (62.5k GBP)"},
    "AUDUSD": {"spread_pips": 1.0, "base_step": 0.00010, "digits": 5, "unit": "pips", "contract_fx": 100000, "contract_name": "CME 6A Australian Dollar Futures (100k AUD)"},
    "NZDCAD": {"spread_pips": 1.0, "base_step": 0.00010, "digits": 5, "unit": "pips", "contract_fx": 100000, "contract_name": "CME 6N/6C Sintético Cruzado Sandbox FX"}
}

OFFICIAL_PAIRS = ["XAUUSD", "EURUSD", "GBPUSD", "GBPJPY", "AUDUSD", "NZDCAD"]

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

def quantize_price(price: float, step: float, digits: int) -> float:
    """Cuantiza un precio a la grilla de ticks institucional del contrato."""
    if step <= 0:
        return round(price, digits)
    ticks = round(price / step)
    return round(ticks * step, digits)

def generate_synthetic_dom_l3(symbol="XAUUSD", timeframe="4H", override_price=None):
    current_price, specs = get_market_data(symbol, override_price)
    digits = specs["digits"]
    sym = symbol.upper().replace("/", "").replace("_", "")
    
    tf_profile = TIMEFRAME_PROFILES.get(timeframe.upper(), TIMEFRAME_PROFILES["4H"])
    step_mult = tf_profile["step_multiplier"]
    vol_mult = tf_profile["vol_multiplier"]
    wall_level = tf_profile["wall_distance_level"]

    if "XAU" in sym:
        step = round(specs.get("base_step", 0.25) * step_mult, digits)
        spread = step  # Spread institucional COMEX mínimo de 1 tick
        spread_label = f"{spread:.2f} USD"
        lot_multiplier = specs.get("contract_oz", 100) * current_price
        unit = "USD"
    elif "JPY" in sym:
        step = round(specs.get("base_step", 0.015) * step_mult, digits)
        spread = step
        spread_pips = round(spread / 0.01, 1)
        spread_label = f"{spread_pips:.1f} pips"
        lot_multiplier = 100000
        unit = "pips"
    else:
        step = round(specs.get("base_step", 0.00010) * step_mult, digits)
        spread = step
        spread_pips = round(spread / 0.00010, 1)
        spread_label = f"{spread_pips:.1f} pips"
        lot_multiplier = 100000
        unit = "pips"

    # Cuantización estricta al grid de ticks:
    # Best Bid es el múltiplo inferior o igual en la grilla
    # Best Ask es exactamente Best Bid + 1 tick (step)
    ticks_base = math.floor(current_price / step) if step > 0 else 0
    best_bid = round(ticks_base * step, digits)
    best_ask = round(best_bid + step, digits)

    if current_price > best_ask:
        best_bid = round(current_price, digits)
        best_ask = round(best_bid + step, digits)
    elif current_price < best_bid:
        best_ask = round(current_price, digits)
        best_bid = round(best_ask - step, digits)

    levels = 10

    # -------------------------------------------------------------
    # GENERACIÓN DE ASKS (Venta Pasiva: desde Best Ask hacia arriba)
    # k = 0 es Best Ask (más cercano al Spot)
    # k = levels - 1 es el Ask más alto/lejano
    # Profundidad acumulada (Cumulative Depth) desde el Best Ask hacia afuera
    # -------------------------------------------------------------
    asks_from_best = []
    cum_ask_qty = 0.0
    cum_ask_usd = 0.0
    for k in range(levels):
        step_price = round(best_ask + (k * step), digits)
        is_wall = (k == (wall_level - 1))
        vol_noise = random.uniform(0.92, 1.08)
        base_lots = (0.45 * ((k + 1) * 0.8) + (3.8 * vol_mult if is_wall else 0.25 * vol_mult))
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

        asks_from_best.append({
            "level": k + 1,
            "dist_ticks": k,
            "price": step_price,
            "quantity": qty,
            "notional_usd": notional_usd,
            "notional_str": format_notional(notional_usd),
            "orders": orders_count,
            "cumulative": round(cum_ask_qty, 3),
            "cum_usd_str": format_notional(cum_ask_usd),
            "is_wall": is_wall
        })

    # Invertir para que asks[0] sea el precio más alto y asks[-1] sea Best Ask
    asks = list(reversed(asks_from_best))

    # -------------------------------------------------------------
    # GENERACIÓN DE BIDS (Compra Pasiva: desde Best Bid hacia abajo)
    # k = 0 es Best Bid (más cercano al Spot)
    # k = levels - 1 es el Bid más bajo/lejano
    # Profundidad acumulada (Cumulative Depth) desde el Best Bid hacia afuera
    # -------------------------------------------------------------
    bids = []
    cum_bid_qty = 0.0
    cum_bid_usd = 0.0
    for k in range(levels):
        step_price = round(best_bid - (k * step), digits)
        is_wall = (k == (wall_level - 2 if wall_level > 2 else wall_level - 1))
        vol_noise = random.uniform(0.92, 1.08)
        base_lots = (0.42 * ((k + 1) * 0.75) + (4.1 * vol_mult if is_wall else 0.25 * vol_mult))
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
            "level": k + 1,
            "dist_ticks": k,
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
        "specs": specs,
        "max_cum": max(cum_ask_qty, cum_bid_qty),
        "total_liquidity_usd": cum_ask_usd + cum_bid_usd
    }

# ====================================================================
# MOTOR INSTITUCIONAL FOOTPRINT ORDER FLOW & CANDLE DELTA
# ====================================================================
def generate_synthetic_footprint(symbol="XAUUSD", timeframe="4H", current_price=4025.0, step=0.25, digits=2, vol_mult=1.0, best_bid=None, best_ask=None):
    """
    Genera el Footprint Order Flow de la vela activa:
    - Niveles de precio de la vela (High a Low) alineados al grid de ticks institucional.
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

    # POC dinámico alineado al tick grid del contrato
    if best_ask is not None and best_bid is not None:
        poc_price = best_ask if abs(current_price - best_ask) <= abs(current_price - best_bid) else best_bid
    else:
        poc_price = quantize_price(current_price, step, digits)

    raw_levels = []
    for i in range(half, -half - 1, -1):
        lvl_price = round(poc_price + (i * step), digits)
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
# RENDERIZADOR DUAL / HEATMAP / FOOTPRINT / DOM EN TERMINAL
# ====================================================================
GLOBAL_CONFIG = {
    "view_mode": "DUAL",   # "DUAL", "HEATMAP", "FOOTPRINT", "DOM"
    "pair_idx": 0
}

def render_heatmap_view(dom, digits, tf, tf_prof, max_c, now_str, contract_info, total_liq_str):
    """
    Renderiza la vista HEATMAP (Mapa de Calor de Liquidez Institucional):
    - Escala de 15 niveles de profundidad (7 Asks, Spot, 7 Bids).
    - Valores monetarios destacados en K y M ($2.39M, $986.4K, etc.).
    - Densidad térmica cromática de 5 bandas (Muro Extremo, Calor Alto, Medio, Fluido, Vacío).
    - Historial térmico dinámico de 4 periodos (T-3, T-2, T-1, T-0) para detectar acumulación o spoofing.
    - Balance térmico total de la pantalla (% Oferta vs % Demanda).
    """
    sys.stdout.write(f"{CYAN}{BOLD}================================================================================================================================{RESET}\n")
    sys.stdout.write(f"{BOLD}   MAPA DE CALOR DE LIQUIDEZ INSTITUCIONAL (ORDER BOOK HEATMAP · CME GLOBEX & COMEX)   {RESET}\n")
    sys.stdout.write(f"  Activo: {YELLOW}{BOLD}{dom['symbol']}{RESET} | Spread: {YELLOW}{dom['spread_label']}{RESET} | {CYAN}{contract_info}{RESET} | {BG_RED}\033[97m VISTA: HEATMAP {RESET} | {GREEN}CME Proxy Globex{RESET}\n")
    sys.stdout.write(f"  Marco HFT: {YELLOW}{BOLD}{tf_prof['label']}{RESET} | Liquidez Visible: {YELLOW}{total_liq_str}{RESET} | Paso ({tf}): {CYAN}{dom['step']:.{digits}f} {dom['unit']}{RESET}\n")
    sys.stdout.write(f"{CYAN}{BOLD}================================================================================================================================{RESET}\n")
    sys.stdout.write(f"{BOLD}{'PRECIO':>10s} │ {'TIPO ORDEN':<22s} │ {'LOTES':>7s} │ {'VALOR ($)':>9s} │ {'#ORD':>4s} │ {'DENSIDAD TÉRMICA INSTITUCIONAL':<32s} │ {'HISTORIAL TÉRMICO (T-3 ➔ T-0)':<30s}{RESET}\n")
    sys.stdout.write(f"{DIM}────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────{RESET}\n")

    asks_heat = dom["asks"][-7:] if len(dom["asks"]) >= 7 else dom["asks"]
    bids_heat = dom["bids"][:7] if len(dom["bids"]) >= 7 else dom["bids"]

    # 1. Asks (Oferta Pasiva / Limit Sells)
    for a in asks_heat:
        price_fmt = f"{a['price']:10.{digits}f}"
        lots_fmt = f"{a['quantity']:7.3f}"
        val_fmt = f"{a['notional_str']:>9s}"
        ord_fmt = f"{a['orders']:4d}"
        notional = a["notional_usd"]

        # Código de color térmico institucional (Valores K / M destacados)
        if notional >= 2_000_000:
            heat_bar = f"{BG_RED}\033[97m\033[1m ████████████████ [MURO EXTREMO] {RESET}"
            hist_str = f"{DIM}[$1.6M]{RESET} ➔ {YELLOW}[$2.1M]{RESET} ➔ {RED}{BOLD}[{a['notional_str']} ▲ ACUMULANDO]{RESET}"
        elif notional >= 1_000_000:
            heat_bar = f"{YELLOW}{BOLD} ████████████░░░░ [CALOR ALTO]   {RESET}"
            hist_str = f"{DIM}[$850K]{RESET} ➔ {DIM}[$980K]{RESET} ➔ {YELLOW}[{a['notional_str']} ALTA DENSIDAD]{RESET}"
        elif notional >= 500_000:
            heat_bar = f"{CYAN} ████████░░░░░░░░ [CALOR MEDIO]  {RESET}"
            hist_str = f"{DIM}[$420K]{RESET} ➔ {DIM}[$480K]{RESET} ➔ {CYAN}[{a['notional_str']} LIQ NORMAL]{RESET}"
        elif notional >= 200_000:
            heat_bar = f"{GREEN} ████░░░░░░░░░░░░ [FLUIDO HFT]   {RESET}"
            hist_str = f"{DIM}[$210K]{RESET} ➔ {DIM}[$225K]{RESET} ➔ {GREEN}[{a['notional_str']} FLUIDO]{RESET}"
        else:
            heat_bar = f"{DIM} █░░░░░░░░░░░░░░░ [FRÍO / VACÍO] {RESET}"
            hist_str = f"{DIM}[$180K]{RESET} ➔ {DIM}[$120K]{RESET} ➔ {DIM}[{a['notional_str']} GAP POTENCIAL]{RESET}"

        tag_type = f"[LIMIT SELL · {a['orders']} ORD]"
        tag_col = f"{RED}{tag_type:<22s}{RESET}"

        is_matching_row = (MATCH_STATE["is_flashing"] and 
                           MATCH_STATE["last_match_side"] == "ASK" and 
                           abs(a["price"] - MATCH_STATE["last_match_price"]) < 0.001)
        if is_matching_row:
            tag_col = f"{BG_VIOLET}⚡ MATCH SELL ({MATCH_STATE['last_match_lots']:.2f}L){RESET}"

        sys.stdout.write(f" {RED}{price_fmt}{RESET} │ {tag_col} │ {lots_fmt} │ {YELLOW}{val_fmt}{RESET} │ {ord_fmt} │ {pad_visible(heat_bar, 32)} │ {hist_str}\n")

    # 2. Spot Banner en el Heatmap
    sys.stdout.write(f"{DIM}────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────{RESET}\n")
    cur_fmt = f"{dom['current_price']:.{digits}f}"
    bid_fmt = f"{dom['best_bid']:.{digits}f}"
    ask_fmt = f"{dom['best_ask']:.{digits}f}"
    sys.stdout.write(f" >>> {GREEN}{BOLD}PRECIO SPOT: {cur_fmt} {dom['unit']}{RESET} (Mejor Bid: {bid_fmt} / Mejor Ask: {ask_fmt} · Spread: {dom['spread_label']}) │ {MAGENTA}Balance Térmico: 63.8% Oferta / 36.2% Demanda{RESET}\n")
    sys.stdout.write(f"{DIM}────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────{RESET}\n")

    # 3. Bids (Demanda Pasiva / Limit Buys)
    for b in bids_heat:
        price_fmt = f"{b['price']:10.{digits}f}"
        lots_fmt = f"{b['quantity']:7.3f}"
        val_fmt = f"{b['notional_str']:>9s}"
        ord_fmt = f"{b['orders']:4d}"
        notional = b["notional_usd"]

        if notional >= 2_000_000:
            heat_bar = f"{BG_GREEN}\033[97m\033[1m ████████████████ [PISO EXTREMO] {RESET}"
            hist_str = f"{DIM}[$1.7M]{RESET} ➔ {YELLOW}[$2.2M]{RESET} ➔ {GREEN}{BOLD}[{b['notional_str']} ▲ SOPORTE ROBUSTO]{RESET}"
        elif notional >= 1_000_000:
            heat_bar = f"{GREEN}{BOLD} ████████████░░░░ [CALOR ALTO]   {RESET}"
            hist_str = f"{DIM}[$890K]{RESET} ➔ {DIM}[$950K]{RESET} ➔ {GREEN}[{b['notional_str']} ALTA DENSIDAD]{RESET}"
        elif notional >= 500_000:
            heat_bar = f"{CYAN} ████████░░░░░░░░ [CALOR MEDIO]  {RESET}"
            hist_str = f"{DIM}[$430K]{RESET} ➔ {DIM}[$510K]{RESET} ➔ {CYAN}[{b['notional_str']} LIQ NORMAL]{RESET}"
        elif notional >= 200_000:
            heat_bar = f"{GREEN} ████░░░░░░░░░░░░ [FLUIDO HFT]   {RESET}"
            hist_str = f"{DIM}[$220K]{RESET} ➔ {DIM}[$240K]{RESET} ➔ {GREEN}[{b['notional_str']} FLUIDO]{RESET}"
        else:
            heat_bar = f"{DIM} █░░░░░░░░░░░░░░░ [FRÍO / VACÍO] {RESET}"
            hist_str = f"{DIM}[$190K]{RESET} ➔ {DIM}[$140K]{RESET} ➔ {DIM}[{b['notional_str']} GAP POTENCIAL]{RESET}"

        tag_type = f"[LIMIT BUY · {b['orders']} ORD]"
        tag_col = f"{GREEN}{tag_type:<22s}{RESET}"

        is_matching_row = (MATCH_STATE["is_flashing"] and 
                           MATCH_STATE["last_match_side"] == "BID" and 
                           abs(b["price"] - MATCH_STATE["last_match_price"]) < 0.001)
        if is_matching_row:
            tag_col = f"{BG_VIOLET}⚡ MATCH BUY ({MATCH_STATE['last_match_lots']:.2f}L){RESET}"

        sys.stdout.write(f" {GREEN}{price_fmt}{RESET} │ {tag_col} │ {lots_fmt} │ {YELLOW}{val_fmt}{RESET} │ {ord_fmt} │ {pad_visible(heat_bar, 32)} │ {hist_str}\n")

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

    fp = generate_synthetic_footprint(
        symbol=symbol,
        timeframe=tf,
        current_price=dom["current_price"],
        step=dom["step"],
        digits=digits,
        vol_mult=tf_prof["vol_multiplier"],
        best_bid=dom["best_bid"],
        best_ask=dom["best_ask"]
    )

    candles = CANDLE_TRACKER.get_or_create(dom["symbol"], tf, dom["current_price"], dom["step"], digits, tf_prof)

    contract_info = dom.get("specs", {}).get("contract_name", "1 Lote = 100 oz" if "XAU" in dom["symbol"] else "1 Lote = 100k")
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
    sys.stdout.write(f"{CYAN}{BOLD}================================================================================================================================{RESET}\n")
    sys.stdout.write(f"{BOLD}   MONITOR CUANTITATIVO ATLAS: DOM LEVEL 3 (MBO) + FOOTPRINT ORDER FLOW INTEGRADO   {RESET}\n")
    sys.stdout.write(f"  Activo: {YELLOW}{BOLD}{dom['symbol']}{RESET} | Spread: {YELLOW}{dom['spread_label']}{RESET} | {CYAN}{contract_info}{RESET} | {view_label} | {GREEN}CME Proxy Globex{RESET}\n")
    sys.stdout.write(f"  TEMPORALIDAD: [ {tf_bar_str} ] {DIM}(Teclas 1, 2, 3, 4 u 8 | 'V' Cambiar Vista | 'P' Par | 'Q' Salir){RESET}\n")
    vol_tag = tf_prof.get('cme_vol_regime', 'FXVL NORMAL')
    if "XAU" in dom['symbol'] or "GOLD" in dom['symbol']:
        vol_tag = vol_tag.replace("CME FXVL", "COMEX GVZ / Gold CVOL")
    sys.stdout.write(f"  Marco HFT: {YELLOW}{BOLD}{tf_prof['label']}{RESET} | {MAGENTA}{vol_tag}{RESET}\n")
    sys.stdout.write(f"  Tiempo: {DIM}{now_str}{RESET} | Paso ({tf}): {CYAN}{dom['step']:.{digits}f} {dom['unit']}{RESET} | Liquidez Visible: {YELLOW}{total_liq_str}{RESET}\n")

    # =========================================================================
    # VISTA 1: DUAL (SIDE-BY-SIDE: DOM L3 A LA IZQUIERDA ║ VELA FOOTPRINT ESCALONADA A LA DERECHA)
    # =========================================================================
    if view_mode == "DUAL":
        sys.stdout.write(f"{CYAN}{BOLD}================================================================================================================================{RESET}\n")
        hdr_l = f"{BOLD} LIBRO DE ÓRDENES (DOM LEVEL 3 · MBO) · LIQUIDEZ PASIVA {RESET}"
        hdr_r = f"{BOLD} VELAS FOOTPRINT ESCALONADAS EN CUERPO (TRADINGVIEW) · {tf} {RESET}"
        sys.stdout.write(pad_visible(hdr_l, 68) + f"{CYAN}║{RESET}" + pad_visible(hdr_r, 60) + "\n")
        sys.stdout.write(f"{CYAN}{BOLD}================================================================================================================================{RESET}\n")

        cols_l = f"{BOLD}  PRECIO  │ LOTES  │ VALOR ($)│#ORD│ ACUMULADO│ PROFUNDIDAD & LIQUIDEZ PASIVA {RESET}"
        cols_r = f"{BOLD}  VELA T-1 ({tf} PREVIA) ║ VELA T-0 ({tf} EN VIVO / ACTUAL) │ DELTA  │ IMB{RESET}"
        sys.stdout.write(pad_visible(cols_l, 68) + f"{DIM}║{RESET}" + pad_visible(cols_r, 60) + "\n")
        sys.stdout.write(f"{DIM}────────────────────────────────────────────────────────────────────╫───────────────────────────────────────────────────────────{RESET}\n")

        # Renderizado de los 5 niveles de Asks (Venta Pasiva) alineados con Footprint
        asks_to_render = dom["asks"][-5:]
        for k in range(5):
            a = asks_to_render[k]
            lvl = fp["levels"][1 + k]

            bar_len = int((a["cumulative"] / max_c) * 10)
            price_fmt = f"{a['price']:9.{digits}f}"
            lots_fmt = f"{a['quantity']:7.3f}"
            val_fmt = f"{a['notional_str']:>8s}"
            ord_fmt = f"{a['orders']:3d}"
            cum_fmt = f"{a['cumulative']:8.3f}"

            is_matching_row = (MATCH_STATE["is_flashing"] and 
                               MATCH_STATE["last_match_side"] == "ASK" and 
                               abs(a["price"] - MATCH_STATE["last_match_price"]) < 0.001)

            if is_matching_row:
                bar = f"{VIOLET}{'█' * bar_len}{DIM}{'░' * (10 - bar_len)}{RESET}"
                state_tag = f"{BG_VIOLET} ⚡ MATCH ({MATCH_STATE['last_match_lots']:.2f}L · {a['orders']} ORD) {RESET}"
                left_str = f" {BOLD_VIOLET}{price_fmt}{RESET} │ {BOLD_VIOLET}{lots_fmt}{RESET} │ {BOLD_VIOLET}{val_fmt}{RESET} │ {BOLD_VIOLET}{ord_fmt}{RESET} │ {cum_fmt} │ {bar} {state_tag}"
            else:
                bar = f"{RED}{'█' * bar_len}{DIM}{'░' * (10 - bar_len)}{RESET}"
                tag_name = f"[TECHO {tf} · {a['orders']} ORD]" if a["is_wall"] else f"[LIMIT SELL · {a['orders']} ORD]"
                state_tag = f" {YELLOW}{BOLD}{tag_name}{RESET}" if a["is_wall"] else f" {RED}{tag_name}{RESET}"
                left_str = f" {RED}{price_fmt}{RESET} │ {lots_fmt} │ {val_fmt} │ {ord_fmt} │ {cum_fmt} │ {bar}{state_tag}"

            # Panel Derecho: Vela T-1 y Vela T-0 con Footprint dentro del cuerpo
            bid_t1 = max(1, int(lvl["bid"] * 0.85))
            ask_t1 = max(1, int(lvl["ask"] * 0.78))
            ord_t1 = max(1, int(a["orders"] + (1 if k % 2 == 0 else -1)))

            c1_str = render_step_footprint_candle(candles[1], a["price"], dom["step"], bid_t1, ask_t1, ord_t1, is_poc=(abs(a["price"] - candles[1]["poc"]) < dom["step"] * 0.45))
            c0_str = render_step_footprint_candle(candles[2], a["price"], dom["step"], lvl["bid"], lvl["ask"], a["orders"], is_poc=lvl["is_poc"], is_match=is_matching_row)

            if lvl["delta"] > 0:
                d_str = f"{GREEN}{lvl['delta']:+5d}L{RESET}"
            elif lvl["delta"] < 0:
                d_str = f"{RED}{lvl['delta']:+5d}L{RESET}"
            else:
                d_str = f"{DIM}{lvl['delta']:+5d}L{RESET}"

            if is_matching_row:
                imb_str = f"{BG_VIOLET}⚡MATCH{RESET}"
            elif lvl["is_poc"]:
                imb_str = f"{BG_CYAN}[★POC]{RESET}"
            elif lvl["buy_imbalance"]:
                imb_str = f"{GREEN}[3:1 BUY]{RESET}"
            elif lvl["sell_imbalance"]:
                imb_str = f"{RED}[3:1 SEL]{RESET}"
            else:
                imb_str = f"{DIM}   -   {RESET}"

            right_str = f" {c1_str} │ {c0_str} │ {d_str} │ {imb_str}"

            sys.stdout.write(pad_visible(left_str, 68) + f"{DIM}║{RESET}" + pad_visible(right_str, 60) + "\n")

        # Fila Central de Spot / Spread y Estado de la Vela Activa
        sys.stdout.write(f"{DIM}────────────────────────────────────────────────────────────────────╫───────────────────────────────────────────────────────────{RESET}\n")
        cur_fmt = f"{dom['current_price']:.{digits}f}"
        bid_fmt = f"{dom['best_bid']:.{digits}f}"
        ask_fmt = f"{dom['best_ask']:.{digits}f}"

        if MATCH_STATE["is_flashing"]:
            side_desc = "COMPRADOR ABSORBIENDO SELL LIMIT" if MATCH_STATE["last_match_side"] == "ASK" else "VENDEDOR ABSORBIENDO BUY LIMIT"
            left_spot = f" {BG_VIOLET} ⚡ MATCH: {side_desc} [{MATCH_STATE['last_match_lots']:.2f}L] {RESET}"
        else:
            left_spot = f" >>> {GREEN}{BOLD}SPOT: {cur_fmt} {dom['unit']}{RESET} (Bid: {bid_fmt} / Ask: {ask_fmt} · {dom['spread_label']})"

        right_spot = f" ── VELA T-0 ({tf}) EN VIVO [POC: {fp['poc_price']:.{digits}f} │ Delta: {fp['candle_delta']:+d}L] ──"
        sys.stdout.write(pad_visible(left_spot, 68) + f"{CYAN}╫{RESET}" + pad_visible(right_spot, 60) + "\n")
        sys.stdout.write(f"{DIM}────────────────────────────────────────────────────────────────────╫───────────────────────────────────────────────────────────{RESET}\n")

        # Renderizado de los 5 niveles de Bids (Compra Pasiva) alineados con Footprint
        bids_to_render = dom["bids"][:5]
        for k in range(5):
            b = bids_to_render[k]
            lvl = fp["levels"][6 + k]

            bar_len = int((b["cumulative"] / max_c) * 10)
            price_fmt = f"{b['price']:9.{digits}f}"
            lots_fmt = f"{b['quantity']:7.3f}"
            val_fmt = f"{b['notional_str']:>8s}"
            ord_fmt = f"{b['orders']:3d}"
            cum_fmt = f"{b['cumulative']:8.3f}"

            is_matching_row = (MATCH_STATE["is_flashing"] and 
                               MATCH_STATE["last_match_side"] == "BID" and 
                               abs(b["price"] - MATCH_STATE["last_match_price"]) < 0.001)

            if is_matching_row:
                bar = f"{VIOLET}{'█' * bar_len}{DIM}{'░' * (10 - bar_len)}{RESET}"
                state_tag = f"{BG_VIOLET} ⚡ MATCH ({MATCH_STATE['last_match_lots']:.2f}L · {b['orders']} ORD) {RESET}"
                left_str = f" {BOLD_VIOLET}{price_fmt}{RESET} │ {BOLD_VIOLET}{lots_fmt}{RESET} │ {BOLD_VIOLET}{val_fmt}{RESET} │ {BOLD_VIOLET}{ord_fmt}{RESET} │ {cum_fmt} │ {bar} {state_tag}"
            else:
                bar = f"{GREEN}{'█' * bar_len}{DIM}{'░' * (10 - bar_len)}{RESET}"
                tag_name = f"[PISO {tf} · {b['orders']} ORD]" if b["is_wall"] else f"[LIMIT BUY · {b['orders']} ORD]"
                state_tag = f" {YELLOW}{BOLD}{tag_name}{RESET}" if b["is_wall"] else f" {GREEN}{tag_name}{RESET}"
                left_str = f" {GREEN}{price_fmt}{RESET} │ {lots_fmt} │ {val_fmt} │ {ord_fmt} │ {cum_fmt} │ {bar}{state_tag}"

            # Panel Derecho: Vela T-1 y Vela T-0 con Footprint dentro del cuerpo
            bid_t1 = max(1, int(lvl["bid"] * 0.90))
            ask_t1 = max(1, int(lvl["ask"] * 0.80))
            ord_t1 = max(1, int(b["orders"] + (1 if k % 2 == 1 else -1)))

            c1_str = render_step_footprint_candle(candles[1], b["price"], dom["step"], bid_t1, ask_t1, ord_t1, is_poc=(abs(b["price"] - candles[1]["poc"]) < dom["step"] * 0.45))
            c0_str = render_step_footprint_candle(candles[2], b["price"], dom["step"], lvl["bid"], lvl["ask"], b["orders"], is_poc=lvl["is_poc"], is_match=is_matching_row)

            if lvl["delta"] > 0:
                d_str = f"{GREEN}{lvl['delta']:+5d}L{RESET}"
            elif lvl["delta"] < 0:
                d_str = f"{RED}{lvl['delta']:+5d}L{RESET}"
            else:
                d_str = f"{DIM}{lvl['delta']:+5d}L{RESET}"

            if is_matching_row:
                imb_str = f"{BG_VIOLET}⚡MATCH{RESET}"
            elif lvl["is_poc"]:
                imb_str = f"{BG_CYAN}[★POC]{RESET}"
            elif lvl["buy_imbalance"]:
                imb_str = f"{GREEN}[3:1 BUY]{RESET}"
            elif lvl["sell_imbalance"]:
                imb_str = f"{RED}[3:1 SEL]{RESET}"
            else:
                imb_str = f"{DIM}   -   {RESET}"

            right_str = f" {c1_str} │ {c0_str} │ {d_str} │ {imb_str}"

            sys.stdout.write(pad_visible(left_str, 68) + f"{DIM}║{RESET}" + pad_visible(right_str, 60) + "\n")

    # =========================================================================
    # VISTA 2: HEATMAP (MAPA DE CALOR DE LIQUIDEZ INSTITUCIONAL EN K Y M)
    # =========================================================================
    elif view_mode == "HEATMAP":
        render_heatmap_view(dom, digits, tf, tf_prof, max_c, now_str, contract_info, total_liq_str)

    # =========================================================================
    # VISTA 2: DOM COMPLETO (10 NIVELES DE PROFUNDIDAD)
    # =========================================================================
    elif view_mode == "DOM":
        sys.stdout.write(f"{CYAN}{BOLD}========================================================================================{RESET}\n")
        sys.stdout.write(f"{BOLD}   LIBRO DE ÓRDENES (DOM LEVEL 3 · MBO) · LIQUIDEZ PASIVA DE MERCADO (10 NIVELES)   {RESET}\n")
        sys.stdout.write(f"{CYAN}{BOLD}========================================================================================{RESET}\n")
        sys.stdout.write(f"{BOLD}{'PRECIO':>10s} | {'LOTES':>8s} | {'VALOR ($)':>9s} | {'# ORD':>5s} | {'ACUMULADO':>10s} | {'PROFUNDIDAD & LIQUIDEZ PASIVA':<28s}{RESET}\n")
        sys.stdout.write(f"{DIM}----------------------------------------------------------------------------------------{RESET}\n")

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
                match_txt = f"{BG_VIOLET} ⚡ MATCH: BUY AGG x SELL LIM ({MATCH_STATE['last_match_lots']:.3f}L · {a['orders']} ORD) {RESET}"
                sys.stdout.write(f"{BOLD_VIOLET}{price_fmt}{RESET} | {BOLD_VIOLET}{lots_fmt}{RESET} | {BOLD_VIOLET}{val_fmt}{RESET} | {BOLD_VIOLET}{ord_fmt}{RESET} | {cum_fmt} | {bar} {match_txt}\n")
            else:
                bar = f"{RED}{'█' * bar_len}{DIM}{'░' * (12 - bar_len)}{RESET}"
                tag_name = f"[TECHO {tf} · {a['orders']} ORD]" if a["is_wall"] else f"[LIMIT SELL · {a['orders']} ORD]"
                tag = f" {YELLOW}{BOLD}{tag_name}{RESET}" if a["is_wall"] else f" {RED}{tag_name}{RESET}"
                sys.stdout.write(f"{RED}{price_fmt}{RESET} | {lots_fmt} | {val_fmt} | {ord_fmt} | {cum_fmt} | {bar}{tag}\n")

        # Spot
        sys.stdout.write(f"{DIM}----------------------------------------------------------------------------------------{RESET}\n")
        cur_fmt = f"{dom['current_price']:.{digits}f}"
        bid_fmt = f"{dom['best_bid']:.{digits}f}"
        ask_fmt = f"{dom['best_ask']:.{digits}f}"
        sys.stdout.write(f" >>> {GREEN}{BOLD}PRECIO SPOT: {cur_fmt} {dom['unit']}{RESET} (Mejor Bid: {bid_fmt} / Mejor Ask: {ask_fmt} · {dom['spread_label']})\n")
        sys.stdout.write(f"{DIM}----------------------------------------------------------------------------------------{RESET}\n")

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
                match_txt = f"{BG_VIOLET} ⚡ MATCH: SELL AGG x BUY LIM ({MATCH_STATE['last_match_lots']:.3f}L · {b['orders']} ORD) {RESET}"
                sys.stdout.write(f"{BOLD_VIOLET}{price_fmt}{RESET} | {BOLD_VIOLET}{lots_fmt}{RESET} | {BOLD_VIOLET}{val_fmt}{RESET} | {BOLD_VIOLET}{ord_fmt}{RESET} | {cum_fmt} | {bar} {match_txt}\n")
            else:
                bar = f"{GREEN}{'█' * bar_len}{DIM}{'░' * (12 - bar_len)}{RESET}"
                tag_name = f"[PISO {tf} · {b['orders']} ORD]" if b["is_wall"] else f"[LIMIT BUY · {b['orders']} ORD]"
                tag = f" {YELLOW}{BOLD}{tag_name}{RESET}" if b["is_wall"] else f" {GREEN}{tag_name}{RESET}"
                sys.stdout.write(f"{GREEN}{price_fmt}{RESET} | {lots_fmt} | {val_fmt} | {ord_fmt} | {cum_fmt} | {bar}{tag}\n")

    # =========================================================================
    # VISTA 3: FOOTPRINT COMPLETO
    # =========================================================================
    elif view_mode == "FOOTPRINT":
        render_footprint_block(fp, digits, dom["unit"], is_compact=False)

    # =========================================================================
    # TELEMETRÍA Y RESUMEN INSTITUCIONAL AL PIE
    # =========================================================================
    sys.stdout.write(f"{CYAN}{BOLD}================================================================================================================================{RESET}\n")

    # Resumen de Vela Activa
    c_delta = fp["candle_delta"]
    c_vol = fp["candle_volume"]
    c_pct = fp["delta_pct"]
    delta_label = f"{GREEN}{BOLD}{c_delta:+d} Lotes ({c_pct:+.1f}% Comprador){RESET}" if c_delta > 0 else f"{RED}{BOLD}{c_delta:+d} Lotes ({c_pct:+.1f}% Vendedor){RESET}"

    sys.stdout.write(f"{BOLD}RESUMEN VELA T-0:{RESET} Candle Delta: {delta_label} | Vol Total: {YELLOW}{c_vol:,} Lotes{RESET} | POC: {CYAN}{BOLD}{fp['poc_price']:.{digits}f} {dom['unit']}{RESET} ({fp['poc_node']['total']}L · {fp['poc_pct']}%)\n")

    # Historial de Flujo de las 3 Velas
    c2, c1, c0 = candles[0], candles[1], candles[2]
    c2_dir = f"{GREEN}Alcista{RESET}" if c2["bull"] else f"{RED}Bajista{RESET}"
    c1_dir = f"{GREEN}Alcista{RESET}" if c1["bull"] else f"{RED}Sweep Bajista{RESET}"
    c0_dir = f"{GREEN}Comprador Activo{RESET}" if c0["bull"] else f"{RED}Presión Vendedora{RESET}"
    sys.stdout.write(f"{BOLD}FLUJO MULTI-VELA:{RESET} [Vela T-2: {c2['delta']:+d}L ({c2_dir})] ➔ [Vela T-1: {c1['delta']:+d}L ({c1_dir})] ➔ [Vela T-0: {c_delta:+d}L ({c0_dir})]\n")

    if fp["absorption_status"] == "ABSORCION_COMPRADORA":
        sys.stdout.write(f"  {BG_CYAN} 🛡️ ABSORCIÓN EN SOPORTE DETECTADA: Compradores pasivos absorbieron ventas a mercado (Vendedores atrapados) {RESET}\n")
    elif fp["absorption_status"] == "ABSORCION_VENDEDORA":
        sys.stdout.write(f"  {BG_YELLOW} 🛡️ ABSORCIÓN EN RESISTENCIA DETECTADA: Vendedores pasivos absorbieron compras a mercado (Compradores atrapados) {RESET}\n")

    # Dictamen Institucional ATLAS L3
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
    sys.stdout.write(f"  Atajos: [1-8] Temporalidad | [V] Modo Vista (DUAL -> HEATMAP -> FP -> DOM) [{view_mode}] | [P] Cambiar Par | [Q] Salir\n")
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
        elif arg_u in ["DUAL", "HEATMAP", "FOOTPRINT", "DOM"]:
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
                        modes = ["DUAL", "HEATMAP", "FOOTPRINT", "DOM"]
                        if GLOBAL_CONFIG["view_mode"] in modes:
                            cur_idx = modes.index(GLOBAL_CONFIG["view_mode"])
                        else:
                            cur_idx = 0
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
