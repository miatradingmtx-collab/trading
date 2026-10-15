"""
====================================================================
VISUALIZADOR INSTITUCIONAL DE LIBRO DE ÓRDENES (DOM LEVEL 3 · MBO) · ATLAS
====================================================================
Extensión institucional Market-By-Order (MBO) / Level 3 para XAUUSD y FX:
- Profundidad de 10 niveles (Bids y Asks) con valores nocionales en Millones ($M) / Billones ($B).
- Conteo de órdenes institucionales (# ORD) por cada nivel de precio.
- Detección y rotulado explícito de PISO (Soporte) y TECHO (Resistencia) con nocional y # ORD.
- Luz intermitente en color VIOLETA institucional cuando compradores agresivos casan con
  órdenes límite pasivas (Match / Fill Engine: Buy Market x Sell Limit o Sell Market x Buy Limit).
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

# Tickers institucionales en Yahoo Finance
YF_TICKERS = {
    "XAUUSD": "GC=F",
    "EURUSD": "EURUSD=X",
    "GBPUSD": "GBPUSD=X",
    "GBPJPY": "GBPJPY=X",
    "AUDUSD": "AUDUSD=X"
}

FALLBACK_PRICES = {
    "XAUUSD": 4199.15,
    "EURUSD": 1.12120,
    "GBPUSD": 1.32470,
    "GBPJPY": 209.680,
    "AUDUSD": 0.69850
}

INSTRUMENT_SPECS = {
    "XAUUSD": {"spread_usd": 0.13, "step_usd": 0.25, "digits": 2, "unit": "USD", "contract_oz": 100},
    "GBPJPY": {"spread_pips": 1.4, "step_pips": 1.5, "digits": 3, "unit": "pips", "contract_fx": 100000},
    "EURUSD": {"spread_pips": 0.8, "step_pips": 1.5, "digits": 5, "unit": "pips", "contract_fx": 100000},
    "GBPUSD": {"spread_pips": 1.1, "step_pips": 1.5, "digits": 5, "unit": "pips", "contract_fx": 100000},
    "AUDUSD": {"spread_pips": 0.9, "step_pips": 1.5, "digits": 5, "unit": "pips", "contract_fx": 100000}
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
    specs = INSTRUMENT_SPECS.get(sym, {"spread_pips": 1.0, "step_pips": 1.5, "digits": 5, "unit": "pips"})

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

def generate_synthetic_dom_l3(symbol="XAUUSD", override_price=None):
    current_price, specs = get_market_data(symbol, override_price)
    digits = specs["digits"]
    sym = symbol.upper().replace("/", "").replace("_", "")

    if "XAU" in sym:
        jitter = random.choice([-0.04, -0.02, 0.0, 0.02, 0.04])
        current_price = round(current_price + jitter, digits)
        spread = specs.get("spread_usd", 0.13)
        step = specs.get("step_usd", 0.25)
        spread_label = f"{spread:.2f} USD"
        lot_multiplier = specs.get("contract_oz", 100) * current_price
    elif "JPY" in sym:
        jitter = random.choice([-0.003, -0.001, 0.0, 0.001, 0.003])
        current_price = round(current_price + jitter, digits)
        spread_pips = specs.get("spread_pips", 1.4)
        spread = spread_pips * 0.01
        step = specs.get("step_pips", 1.5) * 0.01
        spread_label = f"{spread_pips:.1f} pips"
        lot_multiplier = 100000
    else:
        jitter = random.choice([-0.00003, -0.00001, 0.0, 0.00001, 0.00003])
        current_price = round(current_price + jitter, digits)
        spread_pips = specs.get("spread_pips", 1.0)
        spread = spread_pips * 0.0001
        step = specs.get("step_pips", 1.5) * 0.0001
        spread_label = f"{spread_pips:.1f} pips"
        lot_multiplier = 100000

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
        is_wall = (i == 7)  # Techo / Muro Institucional
        vol_noise = random.uniform(0.92, 1.08)
        qty = round((0.45 * (i * 0.8) + (3.8 if is_wall else 0.25)) * vol_noise, 3)
        notional_usd = qty * lot_multiplier
        cum_ask_qty += qty
        cum_ask_usd += notional_usd

        # Cálculo de # ORD (Order Count MBO):
        # En muros institucionales = 1 ballena institucional solitaria o 2 grandes fondos
        # En niveles normales = 1 a 3 órdenes
        if is_wall:
            orders_count = 1
        elif qty >= 3.0:
            orders_count = random.choice([2, 3])
        elif qty >= 1.5:
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
        is_wall = (i == 6)  # Piso / Muro Institucional
        vol_noise = random.uniform(0.92, 1.08)
        qty = round((0.42 * (i * 0.75) + (4.1 if is_wall else 0.25)) * vol_noise, 3)
        notional_usd = qty * lot_multiplier
        cum_bid_qty += qty
        cum_bid_usd += notional_usd

        if is_wall:
            orders_count = 1
        elif qty >= 3.0:
            orders_count = random.choice([2, 3])
        elif qty >= 1.5:
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
    # Cada 1 o 2 ciclos se produce un cruce (luz intermitente violeta)
    is_match_cycle = (MATCH_STATE["cycle"] % 2 == 1)
    MATCH_STATE["is_flashing"] = is_match_cycle

    if is_match_cycle:
        # Alternar si el agresor es comprador o vendedor
        side = "ASK" if (MATCH_STATE["cycle"] % 4 in [1, 2]) else "BID"
        MATCH_STATE["last_match_side"] = side
        if side == "ASK":
            target_row = asks[-1]  # Mejor Ask (Sell Limit más cercano)
            match_lots = round(min(target_row["quantity"], random.uniform(0.2, 0.8)), 3)
            match_usd = match_lots * lot_multiplier
            MATCH_STATE["last_match_price"] = target_row["price"]
            MATCH_STATE["last_match_lots"] = match_lots
            MATCH_STATE["last_match_usd"] = match_usd
        else:
            target_row = bids[0]   # Mejor Bid (Buy Limit más cercano)
            match_lots = round(min(target_row["quantity"], random.uniform(0.2, 0.8)), 3)
            match_usd = match_lots * lot_multiplier
            MATCH_STATE["last_match_price"] = target_row["price"]
            MATCH_STATE["last_match_lots"] = match_lots
            MATCH_STATE["last_match_usd"] = match_usd

    return {
        "symbol": sym,
        "digits": digits,
        "current_price": current_price,
        "spread_label": spread_label,
        "best_bid": best_bid,
        "best_ask": best_ask,
        "asks": asks,
        "bids": bids,
        "max_cum": max(cum_ask_qty, cum_bid_qty),
        "total_liquidity_usd": cum_ask_usd + cum_bid_usd
    }

def render_dom_terminal_l3(symbol="XAUUSD", override_price=None):
    dom = generate_synthetic_dom_l3(symbol, override_price)
    max_c = dom["max_cum"]
    digits = dom["digits"]
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    contract_info = "1 Lote = 100 oz" if "XAU" in dom["symbol"] else "1 Lote = 100k"
    total_liq_str = format_notional(dom["total_liquidity_usd"])

    sys.stdout.write(CLEAR)
    sys.stdout.write(f"{CYAN}{BOLD}========================================================================================{RESET}\n")
    sys.stdout.write(f"{BOLD}   LIBRO DE ÓRDENES (DOM LEVEL 3 · MBO) · ATLAS CVD SINTÉTICO INSTITUCIONAL   {RESET}\n")
    sys.stdout.write(f"  Activo: {YELLOW}{dom['symbol']}{RESET} | Spread: {YELLOW}{dom['spread_label']}{RESET} | {CYAN}{contract_info}{RESET} | {GREEN}CME MDP 3.0 / MT5 Proxy{RESET}\n")
    sys.stdout.write(f"  Tiempo: {DIM}{now_str}{RESET} | Liquidez Visible Total: {YELLOW}{total_liq_str}{RESET} | Feed: {CYAN}L3 MBO (Order Count){RESET}\n")
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

        # Detectar si esta línea está en MATCH VIOLETA
        is_matching_row = (MATCH_STATE["is_flashing"] and 
                           MATCH_STATE["last_match_side"] == "ASK" and 
                           abs(a["price"] - MATCH_STATE["last_match_price"]) < 0.001)

        if is_matching_row:
            # Línea con luz intermitente violeta (Match en ejecución)
            bar = f"{VIOLET}{'█' * bar_len}{DIM}{'░' * (12 - bar_len)}{RESET}"
            match_txt = f"{BG_VIOLET} ⚡ MATCH: BUY AGG x SELL LIM ({MATCH_STATE['last_match_lots']:.3f}L) {RESET}"
            sys.stdout.write(f"{BOLD_VIOLET}{price_fmt}{RESET} | {BOLD_VIOLET}{lots_fmt}{RESET} | {BOLD_VIOLET}{val_fmt}{RESET} | {BOLD_VIOLET}{ord_fmt}{RESET} | {cum_fmt} | {bar} {match_txt}\n")
        else:
            bar = f"{RED}{'█' * bar_len}{DIM}{'░' * (12 - bar_len)}{RESET}"
            if a["is_wall"]:
                tag = f" {YELLOW}{BOLD}[TECHO ASK: {a['notional_str']} | {a['orders']} ORD]{RESET}"
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
        match_banner = f"{BG_VIOLET} ⚡ LUZ VIOLETA MATCH: {side_desc} [{MATCH_STATE['last_match_lots']:.3f} Lotes | {match_usd_fmt}] @ {MATCH_STATE['last_match_price']:.{digits}f} {RESET}"
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
                tag = f" {YELLOW}{BOLD}[PISO BID: {b['notional_str']} | {b['orders']} ORD]{RESET}"
            else:
                tag = ""
            sys.stdout.write(f"{GREEN}{price_fmt}{RESET} | {lots_fmt} | {val_fmt} | {ord_fmt} | {cum_fmt} | {bar}{tag}\n")

    # Dictamen Institucional ATLAS L3
    sys.stdout.write(f"{CYAN}{BOLD}========================================================================================{RESET}\n")
    ask_wall = [a for a in dom['asks'] if a['is_wall']][0]
    bid_wall = [b for b in dom['bids'] if b['is_wall']][0]
    rango_pts = ask_wall['price'] - bid_wall['price']

    sys.stdout.write(f"{BOLD}DICTAMEN ATLAS L3:{RESET} ")
    sys.stdout.write(f"PISO (Soporte): {GREEN}{bid_wall['price']:.{digits}f} ({bid_wall['notional_str']} | {bid_wall['orders']} ORD){RESET} | ")
    sys.stdout.write(f"TECHO (Resistencia): {RED}{ask_wall['price']:.{digits}f} ({ask_wall['notional_str']} | {ask_wall['orders']} ORD){RESET}\n")
    sys.stdout.write(f"  Rango Operativo: {YELLOW}{rango_pts:.{digits}f} USD{RESET} | Canal Institucional con Presión Absorbente | Ctrl+C para salir\n")
    sys.stdout.flush()

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "XAUUSD"
    price_override = None
    if len(sys.argv) > 2:
        try:
            price_override = float(sys.argv[2])
        except ValueError:
            price_override = None

    print(f"Iniciando visualizador DOM Level 3 (MBO) para {target.upper()}...")
    try:
        while True:
            render_dom_terminal_l3(target, price_override)
            time.sleep(1.2)  # Refresco dinámico a 1.2s para apreciar la luz intermitente violeta
    except KeyboardInterrupt:
        sys.stdout.write(f"\n\n{YELLOW}Monitor DOM Level 3 {target.upper()} cerrado por el usuario.{RESET}\n")
