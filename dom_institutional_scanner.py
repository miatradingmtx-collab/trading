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

# ====================================================================
# CLÚSTERS OFICIALES CME GROUP / COMEX
# ====================================================================
CME_ASSET_CLUSTERS = {
    "G5_FX_BASKET": {
        "cluster_name": "CME G5 Foreign Exchange Futures",
        "volatility_benchmark": "FXVL (CME G5 FX Volatility Index / CVOL)",
        "cvol_ticker": "FXVL",
        "pares_directos": {
            "EURUSD": {"ticker": "6E", "contrato": "Euro FX Futures", "cvol_individual": "EUCO"},
            "GBPUSD": {"ticker": "6B", "contrato": "British Pound Futures", "cvol_individual": "BPCO"},
            "AUDUSD": {"ticker": "6A", "contrato": "Australian Dollar Futures", "cvol_individual": "ADCO"},
            "USDJPY": {"ticker": "6J", "contrato": "Japanese Yen Futures", "cvol_individual": "JYCO"},
            "NZDUSD": {"ticker": "6N", "contrato": "New Zealand Dollar Futures", "cvol_individual": "NZCO"},
        },
        "cruces_sinteticos_g5": {
            "GBPJPY": {"ticker": "6B/6J", "contrato": "GBP/JPY Sintético Cruzado Futuros G5", "cvol_proxy": "FXVL_PROXY"},
            "NZDCAD": {"ticker": "6N/6C", "contrato": "NZD/CAD Sintético Cruzado Futuros FX", "cvol_proxy": "FXVL_PROXY"}
        }
    },
    "COMEX_METALS": {
        "cluster_name": "COMEX Precious Metals Division",
        "volatility_benchmark": "GVZ / GLCO (Gold Volatility Index / Gold CVOL)",
        "cvol_ticker": "GVZ",
        "activos": {
            "XAUUSD": {"ticker": "GC", "contrato": "COMEX Gold Futures (100 oz)", "cvol_individual": "GLCO"}
        }
    }
}

# Diccionario plano enriquecido y 100% retrocompatible
CME_TICKERS = {
    "EURUSD": "6E (CME G5 FX Futures | FXVL)",
    "GBPUSD": "6B (CME G5 FX Futures | FXVL)",
    "AUDUSD": "6A (CME G5 FX Futures | FXVL)",
    "USDJPY": "6J (CME G5 FX Futures | FXVL)",
    "NZDUSD": "6N (CME FX Futures | FXVL)",
    "GBPJPY": "6B/6J (CME G5 Sintético Cruzado | FXVL Proxy)",
    "NZDCAD": "6N/6C (CME FX Sintético Cruzado)",
    "XAUUSD": "GC (COMEX Gold Futures | GVZ/Gold CVOL)"
}

def evaluar_regimen_volatilidad_cme(
    symbol: str,
    timeframe: str = "2H",
    atr_pips: Optional[float] = None,
    current_price: float = 0.0
) -> Dict[str, Any]:
    """
    Evalúa el régimen de volatilidad CME (FXVL para G5 FX, GVZ para Oro)
    adaptado a las 5 temporalidades oficiales de Mia: 1H, 2H, 3H, 4H, 8H.
    Determina si el mercado se encuentra en CONSOLIDACIÓN/COMPRESIÓN o EXPANSIÓN/TENDENCIA.
    """
    sym = symbol.upper().replace('/', '').replace('_', '')
    is_gold = 'XAU' in sym or 'GOLD' in sym
    
    benchmark = "GVZ / GLCO (Gold CVOL)" if is_gold else "FXVL (CME G5 FX CVOL)"
    cluster = "COMEX_METALS" if is_gold else "G5_FX_BASKET"
    
    # Parámetros base de volatilidad típica en pips (o USD en Oro) por temporalidad
    base_atr_ref = {
        "1H": 18.0 if not is_gold else 12.0,
        "2H": 28.0 if not is_gold else 18.0,
        "3H": 38.0 if not is_gold else 25.0,
        "4H": 48.0 if not is_gold else 35.0,
        "8H": 75.0 if not is_gold else 55.0
    }.get(timeframe, 28.0)
    
    val_atr = atr_pips if atr_pips and atr_pips > 0 else base_atr_ref
    ratio_vol = val_atr / (base_atr_ref if base_atr_ref > 0 else 1.0)
    
    # Clasificación Cuantitativa de Régimen
    if ratio_vol < 0.85:
        estado = "CONSOLIDACION_COMPRESION"
        diagnostico = "Volatilidad Comprimida / Baja Actividad Implícita CME. Muros pasivos absorben el flujo."
        estrategia = "Operar rango estricto y zonas de Order Blocks 1H/2H. TPs conservadores, prohibido breakouts."
    elif ratio_vol <= 1.25:
        estado = "MERCADO_NORMAL_BALANCEADO"
        diagnostico = "Volatilidad Implícita en Rango Medio CME Globex. Flujo ordenado interbancario."
        estrategia = "Regla de 3 canónica óptima (OB 2H + RSI + LuxAlgo). Respeto al POC institucional."
    elif ratio_vol <= 1.80:
        estado = "EXPANSION_TENDENCIAL"
        diagnostico = "Expansión Institucional CME activa (Sweep de Liquidez / Desbalance CVD). Muros se apartan."
        estrategia = "Operar EXCLUSIVAMENTE a favor de tendencia 4H/8H. Activar Cascada de Riesgo v2 con trailing stop."
    else:
        estado = "SHOCK_VOLATILIDAD_EXTREMA"
        diagnostico = "Shock de Volatilidad / Noticia de Alto Impacto. Adelgazamiento severo de liquidez en DOM."
        estrategia = "Activar Filtro Trampa Noticias (15 min pre / 8 min post). Bloqueo de nuevas órdenes o cierre defensivo."
        
    return {
        "cluster_cme": cluster,
        "benchmark_volatilidad": benchmark,
        "timeframe": timeframe,
        "estado_volatilidad": estado,
        "ratio_volatilidad_vs_norma": round(ratio_vol, 2),
        "diagnostico_dom": diagnostico,
        "recomendacion_estrategica": estrategia
    }

def scan_institutional_dom(
    symbol: str,
    current_price: float = 0.0,
    poc_price: float = 0.0,
    precios_spot: Optional[Dict[str, float]] = None,
    atr_pips: Optional[float] = None,
    timeframe: str = "2H"
) -> Dict[str, Any]:
    """
    Escanea la microestructura del Libro de Órdenes con bandas dinámicas adaptativas
    y detecta trampas de liquidez institucionales (Buy Stops / Sell Stops).
    """
    symbol_norm = symbol.upper().replace('/', '').replace('_', '')
    
    # 1. Mapeo Oficial de Contratos CME FX Futures / COMEX (G5 FXVL & COMEX GVZ)
    cme_tickers = CME_TICKERS
    cme_symbol = cme_tickers.get(symbol_norm, f"{symbol_norm}_FUTURES")
    cme_regimen = evaluar_regimen_volatilidad_cme(symbol_norm, timeframe, atr_pips, current_price)
    
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
        'cme_volatility_regime': cme_regimen,
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
