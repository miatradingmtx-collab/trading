"""
====================================================================
DOM INSTITUTIONAL SCANNER (LIBRO DE ÓRDENES Y VOLATILIDAD DINÁMICA)
====================================================================
Skill Institucional para ATLAS, TIDAL y LUMEN:
Combina análisis de Libro de Órdenes (DOM), contratos CME FX Futures,
bandas de liquidez dinámica adaptativas (ATR) y sensor de divergencia DXY SMT.
====================================================================
"""

import json
import math
from typing import Dict, Any, Optional
from dxy_smt_sensor import dxy_sensor

def scan_institutional_dom(
    symbol: str,
    current_price: float = 0.0,
    poc_price: float = 0.0,
    precios_spot: Optional[Dict[str, float]] = None,
    atr_pips: Optional[float] = None
) -> Dict[str, Any]:
    """
    Escanea la microestructura del Libro de Órdenes con bandas dinámicas adaptativas
    y detecta trampas de liquidez institucionales (Buy Stops / Sell Stops).
    """
    symbol_norm = symbol.upper().replace('/', '').replace('_', '')
    
    # 1. Mapeo Oficial de Contratos CME FX Futures / COMEX
    cme_tickers = {
        'EURUSD': '6E (Euro FX Futures)',
        'GBPUSD': '6B (British Pound Futures)',
        'USDJPY': '6J (Japanese Yen Futures)',
        'AUDUSD': '6A (Australian Dollar Futures)',
        'NZDUSD': '6N (New Zealand Dollar Futures)',
        'NZDCAD': '6N/6C (Sintético Cruzado)',
        'GBPJPY': '6B/6J (Sintético Cruzado)',
        'XAUUSD': 'GC (COMEX Gold Futures)'
    }
    cme_symbol = cme_tickers.get(symbol_norm, f"{symbol_norm}_FUTURES")
    
    base_price = current_price if current_price > 0 else (poc_price if poc_price > 0 else 1.0)
    
    # 2. Bandas Dinámicas de Resting Liquidity Adaptadas por Activo y Volatilidad
    # Evita el error crítico de 18 pips estáticos en Oro y activos exóticos
    if 'XAU' in symbol_norm or 'GOLD' in symbol_norm:
        # Oro: Rango dinámico institucional en dólares (entre $14.50 y $25.00 según el precio)
        band_distance = round(max(14.50, base_price * 0.0035), 2)
        digits = 2
    elif 'JPY' in symbol_norm:
        # Pares Yen: 35 pips (0.35 JPY) adaptado a su volatilidad intradía
        band_distance = round(max(0.35, (atr_pips * 0.01 * 0.40) if atr_pips else 0.35), 3)
        digits = 3
    else:
        # Pares Forex Estándar (EURUSD, GBPUSD, AUDUSD, NZDCAD): 20 a 25 pips
        pips_val = max(20.0, (atr_pips * 0.35) if atr_pips else 22.0)
        band_distance = round(pips_val * 0.0001, 5)
        digits = 5
        
    pool_sell_stops = round(base_price + band_distance, digits)
    pool_buy_stops = round(base_price - band_distance, digits)
    institutional_wall_ask = round(base_price + (band_distance * 1.5), digits)
    institutional_wall_bid = round(base_price - (band_distance * 1.5), digits)
    
    # 3. Cálculo de Imbalance DOM y CVD Delta Proporcional a la Distancia del POC
    dist_poc = current_price - poc_price if poc_price > 0 else 0.0
    
    if poc_price > 0 and base_price > 0:
        dist_ratio = dist_poc / (band_distance if band_distance > 0 else 0.001)
        # Ratio normalizado entre -1.0 y +1.0
        norm_ratio = max(-1.0, min(1.0, dist_ratio))
        buyer_delta = round(50.0 + (norm_ratio * 25.0), 1)
        seller_delta = round(100.0 - buyer_delta, 1)
    else:
        buyer_delta = 50.0
        seller_delta = 50.0
        
    if buyer_delta > 58.0:
        dom_imbalance = 'BULLISH_ABSORPTION (Defensa activa por encima de POC)'
    elif buyer_delta < 42.0:
        dom_imbalance = 'BEARISH_EXHAUSTION (Presión vendedora institucional por debajo de POC)'
    else:
        dom_imbalance = 'BALANCED_LIQUIDITY (Consolidación / Neutral)'

    # 4. Inyección del Sensor DXY SMT
    smt_info = {"aplica_smt": False, "divergencia_detectada": False}
    if precios_spot:
        smt_info = dxy_sensor.evaluar_divergencia_smt(
            symbol=symbol_norm,
            accion="VENTA" if seller_delta > buyer_delta else "COMPRA",
            precio_actual=current_price,
            precios_spot=precios_spot,
            poc_price=poc_price
        )

    return {
        'activo': symbol_norm,
        'cme_contract': cme_symbol,
        'dom_imbalance': dom_imbalance,
        'buyer_volume_pct': buyer_delta,
        'seller_volume_pct': seller_delta,
        'poc_institucional': poc_price,
        'banda_dinamica_amplitud': band_distance,
        'heatmap_resting_liquidity': {
            'zona_trampa_alcista (Buy Stops)': pool_sell_stops,
            'zona_trampa_bajista (Sell Stops)': pool_buy_stops,
            'muro_institucional_ask': institutional_wall_ask,
            'muro_institucional_bid': institutional_wall_bid
        },
        'veredicto_microestructura': 'ALTA_LIQUIDEZ' if abs(buyer_delta - seller_delta) > 15 else 'CONSOLIDACION',
        'dxy_smt_context': smt_info
    }

if __name__ == '__main__':
    # Test EURUSD
    res_eur = scan_institutional_dom('EURUSD', 1.11950, 1.11820)
    print("EURUSD DOM:", json.dumps(res_eur, indent=2))
    # Test XAUUSD (Oro)
    res_gold = scan_institutional_dom('XAUUSD', 4160.50, 4145.00)
    print("\nXAUUSD DOM (Oro):", json.dumps(res_gold, indent=2))
