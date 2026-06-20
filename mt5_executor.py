# ==============================================================================
#                 METATRADER 5 AUTOMATED EXECUTOR (SMC / ICT)
# ==============================================================================
# Este script se ejecuta localmente en tu máquina de Windows o en el VPS de AWS.
# Se encarga de:
# 1. Conectarse de forma nativa a MetaTrader 5.
# 2. Analizar técnicamente los 8 activos seleccionados en temporalidades de 1h-8h.
# 3. Detectar Order Blocks, FVG, iFVG y Breaker Blocks.
# 4. Sincronizar las confirmaciones técnicas con el servidor en la nube (FastAPI).
# 5. Ejecutar operaciones con Stop Loss, Take Profit y cierre parcial del 80%.
# ==============================================================================

import time
import datetime
import requests
import os
import pandas as pd
import numpy as np
from typing import Dict, List, Optional

try:
    import MetaTrader5 as mt5
except ImportError:
    print("Error: Se requiere la librería 'MetaTrader5'. Corre: pip install MetaTrader5")
    exit(1)

# --- CONFIGURACIÓN ---
FASTAPI_URL = os.getenv("FASTAPI_URL", "https://puente-trading.onrender.com")
ACCESS_TOKEN = os.getenv("BRIDGE_ACCESS_TOKEN", "tu-token-seguro-de-acceso")
TIMEFRAMES = {
    "1H": mt5.TIMEFRAME_H1,
    "4H": mt5.TIMEFRAME_H4,
    "8H": mt5.TIMEFRAME_H8
}

# --- CREDENCIALES CUENTA DEMO MT5 ---
MT5_LOGIN = int(os.getenv("MT5_LOGIN", "50123456"))  # Reemplazar con tu número de cuenta demo
MT5_PASSWORD = os.getenv("MT5_PASSWORD", "DemoPassword123")  # Reemplazar con tu contraseña demo
MT5_SERVER = os.getenv("MT5_SERVER", "MetaQuotes-Demo")  # Reemplazar con tu servidor de broker demo

# Diccionario global para trackear posiciones y detectar aperturas, parciales y cierres en bucle
# ticket -> {"volume": float, "symbol": str, "type": int, "price_open": float, "tp": float, "sl": float, "parcial_tomado": bool}
POSICIONES_ACTIVAS = {}

ACTIVOS = ["GBPJPY", "GBPUSD", "EURUSD", "XAUUSD"]

# Mapeo de nombres de activos locales a símbolos del Broker (Ajusta según tu broker, ej: US30 -> WS30)
MAPEO_BROKER = {
    "NASDAQ100": "USTEC", # O NASDAQ100, NQ, NAS100
    "SP500": "US500",     # O SP500, SPY, ES
    "US30": "US30",       # O WS30, DJI, YM
    "BTC": "BTCUSD",
    "GBPJPY": "GBPJPY",
    "GBPUSD": "GBPUSD",
    "EURUSD": "EURUSD",
    "XAUUSD": "XAUUSD"     # O GOLD
}

# ------------------------------------------------------------------------------
# 1. FUNCIONES DE CONEXIÓN CON METATRADER 5
# ------------------------------------------------------------------------------
def conectar_mt5() -> bool:
    if not mt5.initialize():
        print(f"| MT5 ERROR | Falló la inicialización. Código: {mt5.last_error()}")
        return False
        
    # Iniciar sesión con la cuenta demo configurada
    login_result = mt5.login(
        login=MT5_LOGIN,
        password=MT5_PASSWORD,
        server=MT5_SERVER
    )
    
    if not login_result:
        print(f"| MT5 ERROR | Falló el login en la cuenta demo {MT5_LOGIN} (Servidor: {MT5_SERVER}). Código: {mt5.last_error()}")
        return False
        
    print(f"| MT5 SUCCESS | Conectado e identificado con éxito en cuenta demo {MT5_LOGIN} ({MT5_SERVER}).")
    return True

def obtener_velas(simbolo: str, temporalidad: int, cantidad: int = 100) -> Optional[pd.DataFrame]:
    """Descarga las últimas velas para un símbolo desde MT5"""
    # Asegurar que el símbolo esté visible en Market Watch
    if not mt5.symbol_select(simbolo, True):
        print(f"| MT5 ERROR | Símbolo {simbolo} no disponible.")
        return None
        
    rates = mt5.copy_rates_from_pos(simbolo, temporalidad, 0, cantidad)
    if rates is None or len(rates) == 0:
        return None
        
    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    return df

# ------------------------------------------------------------------------------
# 2. CÁLCULO DE INDICADORES TÉCNICOS (Medias Móviles, RSI, Soportes)
# ------------------------------------------------------------------------------
def calcular_rsi(df: pd.DataFrame, periodo: int = 14) -> pd.Series:
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=periodo).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=periodo).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def detectar_soportes_resistencias(df: pd.DataFrame) -> Dict[str, List[float]]:
    """Detecta niveles de soporte y resistencia locales basados en pivotes"""
    soportes = []
    resistencias = []
    
    for i in range(2, len(df) - 2):
        # Mínimo local (Soporte)
        if df['low'].iloc[i] < df['low'].iloc[i-1] and df['low'].iloc[i] < df['low'].iloc[i-2] and \
           df['low'].iloc[i] < df['low'].iloc[i+1] and df['low'].iloc[i] < df['low'].iloc[i+2]:
            soportes.append(float(df['low'].iloc[i]))
            
        # Máximo local (Resistencia)
        if df['high'].iloc[i] > df['high'].iloc[i-1] and df['high'].iloc[i] > df['high'].iloc[i-2] and \
           df['high'].iloc[i] > df['high'].iloc[i+1] and df['high'].iloc[i] > df['high'].iloc[i+2]:
            resistencias.append(float(df['high'].iloc[i]))
            
    return {"soportes": soportes[-5:], "resistencias": resistencias[-5:]}

# ------------------------------------------------------------------------------
# 3. DETECCIÓN DE PATRONES SMC / ICT (Order Blocks, FVG, iFVG, Breakers, Sweeps)
# ------------------------------------------------------------------------------
def analizar_smc_ict(df: pd.DataFrame) -> Dict[str, bool]:
    """
    Analiza el gráfico de velas y detecta patrones de Smart Money.
    Retorna un diccionario de booleanos con los setups activos.
    """
    confirmaciones = {
        "order_block_detectado": False,
        "fvg_detectado": False,
        "breaker_block_detectado": False,
        "sweep_liquidez_detectado": False
    }
    
    if len(df) < 5:
        return confirmaciones

    # A. Detectar Fair Value Gap (FVG) de compra en las últimas 3 velas
    # Condición FVG Alcista: El Low de la vela actual (i) está por encima del High de la vela de hace dos períodos (i-2)
    # Condición FVG Bajista: El High de la vela actual (i) está por debajo del Low de la vela de hace dos períodos (i-2)
    i = len(df) - 1
    if df['low'].iloc[i] > df['high'].iloc[i-2]:
        confirmaciones["fvg_detectado"] = True
    elif df['high'].iloc[i] < df['low'].iloc[i-2]:
        confirmaciones["fvg_detectado"] = True

    # B. Detectar Stop Hunt / Sweep de Liquidez (Mecha larga barriendo un soporte/resistencia reciente)
    # Se evalúa si el cuerpo de la última vela es menor al 30% del rango total de la vela y tiene una mecha larga en el extremo
    rango_total = df['high'].iloc[i] - df['low'].iloc[i]
    rango_cuerpo = abs(df['close'].iloc[i] - df['open'].iloc[i])
    
    if rango_total > 0:
        porcentaje_cuerpo = (rango_cuerpo / rango_total) * 100
        # Mecha inferior larga (cazando compras)
        mecha_inferior = min(df['open'].iloc[i], df['close'].iloc[i]) - df['low'].iloc[i]
        if porcentaje_cuerpo < 30 and mecha_inferior > (rango_total * 0.5):
            confirmaciones["sweep_liquidez_detectado"] = True

    # C. Order Blocks (OB): Última vela contraria antes de un impulso fuerte
    # Si la vela i-1 es bajista y las velas i y posteriores causaron una fuerte subida (Market Structure Shift)
    if df['close'].iloc[i-1] < df['open'].iloc[i-1] and df['close'].iloc[i] > df['high'].iloc[i-1]:
        confirmaciones["order_block_detectado"] = True

    # D. Breaker Blocks (BB): Un Order Block roto que ahora cambia su polaridad
    # Para simplificar, si el precio rompió con fuerza el OB anterior
    if df['close'].iloc[i] > df['high'].iloc[i-2] and df['close'].iloc[i-2] < df['open'].iloc[i-2]:
         confirmaciones["breaker_block_detectado"] = True

    return confirmaciones

# ------------------------------------------------------------------------------
# 4. COMUNICACIÓN CON EL CEREBRO CLOUD (FastAPI Webhooks)
# ------------------------------------------------------------------------------
def sincronizar_matriz_tecnica(activo: str, confirmaciones: Dict[str, bool], rsi_val: float, ma_alineada: bool, soporte_activo: bool):
    """Envía las confirmaciones técnicas al servidor FastAPI en la nube para actualizar Firebase"""
    url = f"{FASTAPI_URL}/webhook_technical_update"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "activo": activo,
        "confirmaciones_tecnicas": {
            "soporte_resistencia_activo": soporte_activo,
            "medias_moviles_alineadas": ma_alineada,
            "rsi_sobrecompra_sobreventa": (rsi_val >= 80 or rsi_val <= 20),
            "order_block_detectado": confirmaciones["order_block_detectado"],
            "fvg_detectado": confirmaciones["fvg_detectado"],
            "breaker_block_detectado": confirmaciones["breaker_block_detectado"],
            "sweep_liquidez_detectado": confirmaciones["sweep_liquidez_detectado"]
        }
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=5)
        if response.status_code == 200:
            print(f"| CLOUD | Confirmaciones para {activo} actualizadas con éxito.")
            return response.json()
        else:
            print(f"| CLOUD ERROR | No se pudo actualizar matriz en la nube: {response.text}")
    except Exception as e:
        print(f"| CLOUD EXCEPTION | Error al conectar con FastAPI: {e}")
    return None

def solicitar_autorizacion_trade(activo: str, accion: str, precio: float) -> Optional[Dict]:
    """Solicita a Mia (IA en Render/Firebase) si se autoriza el trade basado en la validación booleana >= 80%"""
    url = f"{FASTAPI_URL}/webhook_mt5_setup"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "activo": activo,
        "accion": accion,
        "precio": precio,
        "estrategia": "SMC_ICT_Leona"
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=5)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"| CLOUD EXCEPTION | Error al solicitar autorización de trade: {e}")
    return None

def obtener_pnl_reciente(ticket: int) -> float:
    """Busca el último deal asociado a un ticket para obtener su PnL realizado"""
    from_date = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=2)
    to_date = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=5)
    
    deals = mt5.history_deals_get(from_date, to_date, position=ticket)
    if deals is not None and len(deals) > 0:
        for deal in reversed(deals):
            if deal.entry in [mt5.DEAL_ENTRY_OUT, mt5.DEAL_ENTRY_INOUT]:
                return float(deal.profit)
    return 0.0

def obtener_detalles_cierre(ticket: int, position_type: int) -> (float, float):
    """Obtiene el PnL final y el precio de cierre de una posición desde el historial de deals"""
    from_date = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=1)
    to_date = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=5)
    
    deals = mt5.history_deals_get(from_date, to_date, position=ticket)
    pnl_total = 0.0
    precio_cierre = 0.0
    
    if deals is not None and len(deals) > 0:
        for deal in deals:
            pnl_total += deal.profit
            if deal.entry == mt5.DEAL_ENTRY_OUT:
                precio_cierre = deal.price
                
    if precio_cierre == 0.0:
        # Respaldo si no se encuentra deal de salida
        symbol = deals[0].symbol if (deals and len(deals) > 0) else ""
        tick = mt5.symbol_info_tick(symbol) if symbol else None
        if tick:
            precio_cierre = tick.bid if position_type == mt5.POSITION_TYPE_BUY else tick.ask
            
    return float(pnl_total), float(precio_cierre)

def reportar_evento_trade(simbolo: str, ticket: int, tipo_posicion: int, evento: str, precio: float, sl: float, tp: float, pnl: float = 0.0, comentario: str = ""):
    """Envía un reporte de evento de trade al servidor FastAPI para registrar en Notion y Excel"""
    url = f"{FASTAPI_URL}/webhook"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    
    # Mapear tipo de posición y evento a descripciones claras
    if evento == "APERTURA":
        accion = "COMPRA" if tipo_posicion == mt5.POSITION_TYPE_BUY else "VENTA"
        estrategia = f"APERTURA (Ticket {ticket})"
    elif evento == "CIERRE_PARCIAL":
        accion = "CIERRE PARCIAL"
        estrategia = f"PARCIAL (Ticket {ticket}) - {comentario}"
    else: # CIERRE_TOTAL
        accion = "CIERRE TOTAL"
        estrategia = f"CIERRE (Ticket {ticket}) - {comentario}"
        
    # Resolver nombre del activo original (ej: USTEC -> NASDAQ100)
    activo_original = simbolo
    for act, symb in MAPEO_BROKER.items():
        if symb == simbolo:
            activo_original = act
            break
            
    payload = {
        "activo": activo_original,
        "accion": accion,
        "precio": float(precio),
        "stop_loss": float(sl) if sl else 0.0,
        "take_profit": float(tp) if tp else 0.0,
        "estrategia": estrategia,
        "pnl": float(pnl),
        "ticket": int(ticket)
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=5)
        if response.status_code == 200:
            print(f"| CLOUD SUCCESS | Evento {evento} registrado con éxito en Notion y Bitacora Excel.")
        else:
            print(f"| CLOUD ERROR | No se pudo registrar el evento: {response.text}")
    except Exception as e:
        print(f"| CLOUD EXCEPTION | Error al reportar evento de trade: {e}")

def obtener_matriz_activo(activo: str) -> Optional[Dict]:
    """Obtiene la matriz de validación desde el servidor FastAPI"""
    url = f"{FASTAPI_URL}/get_asset_matrix?activo={activo}"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    try:
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"| CLOUD ERROR | Error al obtener matriz para {activo}: {e}")
    return None

def cerrar_parcial_mt5(posicion, lote_a_cerrar: float) -> bool:
    """Cierra parcialmente una posición en MetaTrader 5"""
    simbolo = posicion.symbol
    tick = mt5.symbol_info_tick(simbolo)
    if not tick:
        print(f"| MT5 ERROR | No se pudo obtener tick para cierre parcial de {simbolo}")
        return False
        
    tipo_orden_cierre = mt5.ORDER_TYPE_SELL if posicion.type == mt5.POSITION_TYPE_BUY else mt5.ORDER_TYPE_BUY
    precio_cierre = tick.bid if posicion.type == mt5.POSITION_TYPE_BUY else tick.ask
    
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": simbolo,
        "volume": round(lote_a_cerrar, 2),
        "type": tipo_orden_cierre,
        "position": posicion.ticket,
        "price": precio_cierre,
        "deviation": 20,
        "magic": 20260616,
        "comment": "CP 80% Leona",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }
    
    result = mt5.order_send(request)
    if result.retcode == mt5.TRADE_RETCODE_DONE:
        print(f"| MT5 SUCCESS | Cierre parcial de 80% ejecutado. Ticket: {posicion.ticket}. Lotes cerrados: {round(lote_a_cerrar, 2)}")
        return True
    else:
        print(f"| MT5 ERROR | Falló cierre parcial para ticket {posicion.ticket}. Código: {result.retcode} | {result.comment}")
        return False

def gestionar_posiciones_activas():
    """Monitorea posiciones abiertas para tomar parciales del 80%, aplicar break-even y reportar cierres/aperturas"""
    global POSICIONES_ACTIVAS
    
    positions = mt5.positions_get(magic=20260616)
    tickets_actuales = set()
    
    if positions is not None and len(positions) > 0:
        for pos in positions:
            tickets_actuales.add(pos.ticket)
            
            # 1. SI ES UNA NUEVA POSICIÓN: Registrarla localmente e informar de la APERTURA a Notion y Excel
            if pos.ticket not in POSICIONES_ACTIVAS:
                POSICIONES_ACTIVAS[pos.ticket] = {
                    "volume": pos.volume,
                    "symbol": pos.symbol,
                    "type": pos.type,
                    "price_open": pos.price_open,
                    "tp": pos.tp,
                    "sl": pos.sl,
                    "parcial_tomado": False
                }
                print(f"| SEGUIMIENTO | Nueva posición detectada. Ticket: {pos.ticket} | Lote: {pos.volume}")
                reportar_evento_trade(pos.symbol, pos.ticket, pos.type, "APERTURA", pos.price_open, pos.sl, pos.tp)
                
            # Encontrar el activo original de nuestra lista
            activo = None
            for act in ACTIVOS:
                if MAPEO_BROKER.get(act) == pos.symbol:
                    activo = act
                    break
                    
            if not activo:
                continue
                
            # Parámetros del trade
            entry_price = pos.price_open
            current_price = pos.price_current
            tp = pos.tp
            sl = pos.sl
            volume = pos.volume
            
            if tp == 0.0:
                continue
                
            # Target 1 (TP1) al 50% de la distancia al TP final
            distancia_total = tp - entry_price
            tp1 = entry_price + (distancia_total * 0.5)
            
            es_buy = pos.type == mt5.POSITION_TYPE_BUY
            alcanzo_tp1 = (es_buy and current_price >= tp1) or (not es_buy and current_price <= tp1)
            
            # A. Tomar Parciales al 80% si no se ha tomado (lote remanente > 0.02 y alcanzó TP1)
            if alcanzo_tp1 and volume > 0.02 and not POSICIONES_ACTIVAS[pos.ticket]["parcial_tomado"]:
                lote_a_cerrar = volume * 0.8
                lote_a_cerrar = round(lote_a_cerrar, 2)
                if lote_a_cerrar >= 0.01:
                    if cerrar_parcial_mt5(pos, lote_a_cerrar):
                        POSICIONES_ACTIVAS[pos.ticket]["parcial_tomado"] = True
                        POSICIONES_ACTIVAS[pos.ticket]["volume"] = pos.volume - lote_a_cerrar
                        
                        # Esperar a que el deal se registre e informar a Notion/Excel
                        time.sleep(1)
                        pnl_parcial = obtener_pnl_reciente(pos.ticket)
                        reportar_evento_trade(pos.symbol, pos.ticket, pos.type, "CIERRE_PARCIAL", current_price, sl, tp, pnl=pnl_parcial, comentario=f"Cerrado 80% ({lote_a_cerrar:.2f} lotes)")
                        
            # B. Gestión de Break-Even dinámico relativo a Liquidez Institucional
            distancia_tp1 = abs(tp1 - entry_price)
            rango_tolerancia = distancia_tp1 * 0.15  # Tolerancia del 15% del recorrido
            
            esta_en_zona_entrada = False
            if es_buy:
                esta_en_zona_entrada = (current_price <= entry_price + rango_tolerancia) and (sl < entry_price)
            else:
                esta_en_zona_entrada = (current_price >= entry_price - rango_tolerancia) and (sl > entry_price or sl == 0.0)
                
            if esta_en_zona_entrada:
                # Consultar base de datos en la nube para volumen institucional
                matrix = obtener_matriz_activo(activo)
                liq_institucional = False
                if matrix:
                    confirmaciones_inst = matrix.get("confirmaciones_institucionales", {})
                    liq_institucional = confirmaciones_inst.get("dark_pools_compra_masiva", False) or \
                                        confirmaciones_inst.get("heatmap_ordenes_limite", False)
                                        
                if liq_institucional:
                    print(f"| GESTOR BE | {activo} regresando a entrada. Soporte institucional DETECTADO. Manteniendo SL original.")
                else:
                    print(f"| GESTOR BE | {activo} regresando a entrada sin soporte institucional. Colocando Break-Even.")
                    request = {
                        "action": mt5.TRADE_ACTION_SLTP,
                        "symbol": pos.symbol,
                        "position": pos.ticket,
                        "sl": entry_price,
                        "tp": tp
                    }
                    result = mt5.order_send(request)
                    if result.retcode == mt5.TRADE_RETCODE_DONE:
                        print(f"| GESTOR BE SUCCESS | Ticket {pos.ticket} modificado a Break-Even (SL={entry_price}).")
                        POSICIONES_ACTIVAS[pos.ticket]["sl"] = entry_price
                    else:
                        print(f"| GESTOR BE ERROR | No se pudo modificar ticket {pos.ticket}: {result.comment}")

    # 2. DETECTAR POSICIONES CERRADAS TOTALMENTE (estaban registradas pero ya no están activas)
    tickets_cerrados = []
    for ticket, info in POSICIONES_ACTIVAS.items():
        if ticket not in tickets_actuales:
            tickets_cerrados.append(ticket)
            
    for ticket in tickets_cerrados:
        info = POSICIONES_ACTIVAS[ticket]
        print(f"| SEGUIMIENTO | Posición cerrada detectada. Ticket: {ticket}")
        
        # Esperar un momento para asegurar que los deals se asienten en el historial
        time.sleep(1.5)
        pnl_final, precio_cierre = obtener_detalles_cierre(ticket, info["type"])
        
        reportar_evento_trade(info["symbol"], ticket, info["type"], "CIERRE_TOTAL", precio_cierre, info["sl"], info["tp"], pnl=pnl_final, comentario="Cerrado totalmente")
        
        # Eliminar del registro
        del POSICIONES_ACTIVAS[ticket]

# ------------------------------------------------------------------------------
# 5. GESTOR DE OPERACIONES (Órdenes, SL, TP, Cierre Parcial del 80%)
# ------------------------------------------------------------------------------
def ejecutar_orden_mt5(activo: str, accion: str, precio: float, decision: Dict) -> bool:
    """Ejecuta la orden en MetaTrader 5 y configura Stop Loss y Take Profit"""
    simbolo_broker = MAPEO_BROKER.get(activo, activo)
    
    # Obtener info de ticks
    tick = mt5.symbol_info_tick(simbolo_broker)
    if not tick:
        print(f"| MT5 ERROR | No se pudo obtener información de precio para {simbolo_broker}")
        return False
        
    tipo_orden = mt5.ORDER_TYPE_BUY if accion.upper() == "COMPRA" else mt5.ORDER_TYPE_SELL
    precio_ejecucion = tick.ask if tipo_orden == mt5.ORDER_TYPE_BUY else tick.bid
    
    # Calcular SL y TP estimados (O proporcionados por Mia en el JSON)
    sl = decision.get("stop_loss", precio_ejecucion - 200 if tipo_orden == mt5.ORDER_TYPE_BUY else precio_ejecucion + 200)
    tp = decision.get("take_profit", precio_ejecucion + 400 if tipo_orden == mt5.ORDER_TYPE_BUY else precio_ejecucion - 400)
    
    lote = decision.get("lote", 0.1)
    
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": simbolo_broker,
        "volume": lote,
        "type": tipo_orden,
        "price": precio_ejecucion,
        "sl": sl,
        "tp": tp,
        "deviation": 20,
        "magic": 20260616,
        "comment": "Leona Liquidez Bot",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }
    
    result = mt5.order_send(request)
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        print(f"| MT5 ERROR | Orden rechazada por broker. Código: {result.retcode} | {result.comment}")
        return False
        
    print(f"| MT5 SUCCESS | Orden de {accion} colocada en {simbolo_broker}. ID Ticket: {result.order}")
    return True

def obtener_nombre_killzone() -> Optional[str]:
    """
    Verifica si la hora actual local de México está dentro de una Killzone de trading.
    Retorna el nombre de la Killzone activa ("LONDRES", "NUEVA_YORK", "ASIA") o None.
    """
    LONDRES_INICIO = 2.0  # 2:00 AM
    LONDRES_FIN = 5.0     # 5:00 AM
    NY_INICIO = 7.0       # 7:00 AM
    NY_FIN = 10.0         # 10:00 AM
    ASIA_INICIO = 18.0    # 6:00 PM (18:00)
    ASIA_FIN = 22.0       # 10:00 PM (22:00)
    
    ahora = datetime.datetime.now()
    hora_decimal = ahora.hour + ahora.minute / 60.0
    
    if LONDRES_INICIO <= hora_decimal < LONDRES_FIN:
        return "LONDRES"
    elif NY_INICIO <= hora_decimal < NY_FIN:
        return "NUEVA_YORK"
    elif ASIA_INICIO <= hora_decimal < ASIA_FIN:
        return "ASIA"
    return None

# ------------------------------------------------------------------------------
# 6. BUCLE PRINCIPAL DE ANÁLISIS
# ------------------------------------------------------------------------------
def ejecutar_escaner():
    if not conectar_mt5():
        return
        
    # Gestionar posiciones abiertas antes de buscar nuevos setups
    try:
        gestionar_posiciones_activas()
    except Exception as e:
        print(f"| GESTOR POSICIONES ERROR | Fallo al gestionar posiciones: {e}")
        
    killzone_activa = obtener_nombre_killzone()
    if killzone_activa:
        print(f"| ESCANER | Sesion activa: {killzone_activa} | Iniciando escaneo de los 8 activos clave en 1H...")
    else:
        print("| ESCANER | Fuera de horario de Killzones (Londres, NY, Asia). Sincronizando datos pero las entradas estan bloqueadas.")
    
    for activo in ACTIVOS:
        simbolo = MAPEO_BROKER.get(activo)
        # Descargar velas en temporalidad H1 (1 Hora)
        df = obtener_velas(simbolo, mt5.TIMEFRAME_H1, 100)
        
        if df is None or df.empty:
            continue
            
        # Calcular indicadores
        rsi_series = calcular_rsi(df)
        rsi_actual = rsi_series.iloc[-1]
        
        # Medias móviles (EMA 50 y EMA 200)
        ema_50 = df['close'].ewm(span=50, adjust=False).mean().iloc[-1]
        ema_200 = df['close'].ewm(span=200, adjust=False).mean().iloc[-1]
        ma_alineada = (df['close'].iloc[-1] > ema_50 > ema_200) or (df['close'].iloc[-1] < ema_50 < ema_200)
        
        # Soportes y resistencias
        niveles = detectar_soportes_resistencias(df)
        precio_actual = df['close'].iloc[-1]
        soporte_activo = False
        
        for sup in niveles["soportes"]:
            if abs(precio_actual - sup) < (precio_actual * 0.001): # Si está muy cerca del nivel
                soporte_activo = True
                break
                
        # Analizar metodologías SMC / ICT (FVG, OB, BB, Sweeps)
        confirmaciones = analizar_smc_ict(df)
        
        # 1. Sincronizar todos estos indicadores técnicos en la nube de Firebase
        sincronizacion = sincronizar_matriz_tecnica(activo, confirmaciones, rsi_actual, ma_alineada, soporte_activo)
        
        # 2. Si hay un setup de entrada (ej: precio en soporte con FVG y OB activos)
        # Evaluamos el gatillo en Firebase. Si la nube nos indica que está listo:
        if confirmaciones["fvg_detectado"] or confirmaciones["order_block_detectado"]:
            if not killzone_activa:
                print(f"| GATILLO OMITIDO | Setup detectado en {activo} pero esta fuera de horario de Killzone.")
                continue
                
            accion = "COMPRA" if (precio_actual > ema_50) else "VENTA"
            
            # Solicitar al cerebro (Mia) si autoriza el trade
            decision = solicitar_autorizacion_trade(activo, accion, precio_actual)
            
            if decision and decision.get("authorized") is True:
                print(f"| LEONA DE LA LIQUIDEZ | ¡Gatillo Cruzado Exitoso! Entrando al mercado...")
                ejecutar_orden_mt5(activo, accion, precio_actual, decision)
                
        time.sleep(2) # Pausa de cortesía para no saturar la terminal

if __name__ == "__main__":
    while True:
        try:
            ejecutar_escaner()
        except Exception as e:
            print(f"| RUNNER ERROR | Ocurrió un fallo en el bucle: {e}")
        time.sleep(60) # Ejecutar escaneo cada minuto
