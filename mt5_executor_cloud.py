# ==============================================================================
#           METATRADER 5 CLOUD AUTOMATED EXECUTOR (METAAPI CLOUD)
# ==============================================================================
# Este script se ejecuta en segundo plano en Render/Nube.
# Se encarga de:
# 1. Conectarse a MetaAPI Cloud de forma asíncrona.
# 2. Analizar técnicamente los 8 activos descargando velas vía MetaAPI.
# 3. Detectar Order Blocks, FVG, iFVG y Breaker Blocks.
# 4. Sincronizar las confirmaciones técnicas con el servidor en la nube (FastAPI/Firebase).
# 5. Ejecutar operaciones en la nube usando la API de trading de MetaAPI.
# ==============================================================================

import asyncio
import datetime
import os
import io
import random
import pandas as pd
import numpy as np
import httpx
from typing import Dict, List, Optional
from dotenv import load_dotenv
load_dotenv()

def print(*args, **kwargs):
    import builtins
    msg = " ".join(map(str, args))
    try:
        builtins.print(msg, **kwargs)
    except UnicodeEncodeError:
        # Fallback to ascii representation for emojis/non-ascii chars
        safe_msg = msg.encode('ascii', errors='backslashreplace').decode('ascii')
        builtins.print(safe_msg, **kwargs)


# --- CONFIGURACIÓN ---
FASTAPI_URL = os.getenv("FASTAPI_URL", "http://localhost:8080")

ACCESS_TOKEN = os.getenv("BRIDGE_ACCESS_TOKEN", "tu-token-seguro-de-acceso")

METAAPI_TOKEN = os.getenv("METAAPI_TOKEN")
MT5_LOGIN = os.getenv("MT5_LOGIN", "5051870219")
MT5_PASSWORD = os.getenv("MT5_PASSWORD", "*5FkZuJe")
MT5_SERVER = os.getenv("MT5_SERVER", "MetaQuotes-Demo")

# Diccionario global para trackear posiciones y detectar aperturas, parciales y cierres en bucle
# ticket -> {"volume": float, "symbol": str, "type": int, "price_open": float, "tp": float, "sl": float, "parcial_tomado": bool}
POSICIONES_ACTIVAS = {}

ACTIVOS = ["GBPJPY", "GBPUSD", "EURUSD", "XAUUSD"]


# Mapeo de nombres de activos locales a símbolos del Broker
MAPEO_BROKER = {
    "NASDAQ100": "USTEC",
    "SP500": "US500",
    "US30": "US30",
    "BTC": "BTCUSD",
    "GBPJPY": "GBPJPY",
    "GBPUSD": "GBPUSD",
    "EURUSD": "EURUSD",
    "XAUUSD": "XAUUSD"
}

# ------------------------------------------------------------------------------
# 1. CONEXIÓN CON METAAPI
# ------------------------------------------------------------------------------
async def conectar_metaapi():
    """Inicializa la API, busca la cuenta demo y retorna el objeto de cuenta y conexión RPC."""
    try:
        from metaapi_cloud_sdk import MetaApi
    except ImportError:
        print("❌ Error: Se requiere la librería 'metaapi-cloud-sdk'.")
        return None, None

    if not METAAPI_TOKEN:
        print("❌ Error: Falta METAAPI_TOKEN en el entorno.")
        return None, None

    print("🔌 Conectando a MetaAPI Cloud...")
    api = MetaApi(METAAPI_TOKEN)

    try:
        # Buscar cuenta demo
        accounts_data = await api.metatrader_account_api.get_accounts_with_infinite_scroll_pagination()
        accounts = accounts_data if isinstance(accounts_data, list) else (accounts_data.get('items', []) if hasattr(accounts_data, 'get') else getattr(accounts_data, 'items', []))
        account = next((a for a in accounts if a.login == MT5_LOGIN), None)

        if not account:
            print(f"📝 Registrando cuenta demo {MT5_LOGIN} en MetaAPI...")
            account = await api.metatrader_account_api.create_account({
                'name': 'Mia Demo Account',
                'type': 'cloud',
                'login': MT5_LOGIN,
                'password': MT5_PASSWORD,
                'server': MT5_SERVER,
                'platform': 'mt5',
                'magic': 20260616
            })
            print(f"✅ Cuenta creada en MetaAPI. ID: {account.id}")
        else:
            print(f"✅ Cuenta encontrada en MetaAPI. ID: {account.id}")

        # Desplegar la cuenta si está desconectada
        if account.state != 'DEPLOYED':
            print("🚀 Desplegando cuenta de trading demo en MetaAPI...")
            await account.deploy()
        
        await account.wait_connected()
        print("✅ Cuenta conectada al Broker.")

        # Obtener conexión RPC
        connection = account.get_rpc_connection()
        await connection.connect()
        await connection.wait_synchronized()
        print("✅ Conexión RPC sincronizada.")

        return account, connection

    except Exception as e:
        print(f"❌ Error en la conexión a MetaAPI: {e}")
        return None, None

async def obtener_velas_cloud(account, simbolo: str, temporalidad: str, cantidad: int = 100) -> Optional[pd.DataFrame]:
    """Descarga las últimas velas para un símbolo usando la API de MetaAPI"""
    try:
        # temporalidad en MetaAPI: '1h', '4h', etc.
        candles = await account.get_historical_candles(simbolo, temporalidad, datetime.datetime.now(datetime.timezone.utc), cantidad)
        if not candles or len(candles) == 0:
            return None
            
        df = pd.DataFrame(candles)
        # Asegurar columnas correctas y formato esperado por el escáner
        df['time'] = pd.to_datetime(df['time'])
        df['open'] = df['open'].astype(float)
        df['high'] = df['high'].astype(float)
        df['low'] = df['low'].astype(float)
        df['close'] = df['close'].astype(float)
        return df
    except Exception as e:
        print(f"| METAAPI ERROR | Error al obtener velas para {simbolo}: {e}")
        return None

# ------------------------------------------------------------------------------
# 2. CÁLCULO DE INDICADORES TÉCNICOS
# ------------------------------------------------------------------------------
def calcular_rsi(df: pd.DataFrame, periodo: int = 14) -> pd.Series:
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=periodo).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=periodo).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def detectar_soportes_resistencias(df: pd.DataFrame) -> Dict[str, List[float]]:
    soportes = []
    resistencias = []
    
    for i in range(2, len(df) - 2):
        if df['low'].iloc[i] < df['low'].iloc[i-1] and df['low'].iloc[i] < df['low'].iloc[i-2] and \
           df['low'].iloc[i] < df['low'].iloc[i+1] and df['low'].iloc[i] < df['low'].iloc[i+2]:
            soportes.append(float(df['low'].iloc[i]))
            
        if df['high'].iloc[i] > df['high'].iloc[i-1] and df['high'].iloc[i] > df['high'].iloc[i-2] and \
           df['high'].iloc[i] > df['high'].iloc[i+1] and df['high'].iloc[i] > df['high'].iloc[i+2]:
            resistencias.append(float(df['high'].iloc[i]))
            
    return {"soportes": soportes[-5:], "resistencias": resistencias[-5:]}

# ------------------------------------------------------------------------------
# 3. DETECCIÓN DE PATRONES SMC / ICT
# ------------------------------------------------------------------------------
def analizar_smc_ict(df: pd.DataFrame) -> Dict[str, bool]:
    confirmaciones = {
        "order_block_detectado": False,
        "fvg_detectado": False,
        "breaker_block_detectado": False,
        "sweep_liquidez_detectado": False
    }
    
    if len(df) < 5:
        return confirmaciones

    i = len(df) - 1
    if df['low'].iloc[i] > df['high'].iloc[i-2]:
        confirmaciones["fvg_detectado"] = True
    elif df['high'].iloc[i] < df['low'].iloc[i-2]:
        confirmaciones["fvg_detectado"] = True

    # Detección de Barrido de Liquidez (Sweep Liquidity) real
    # Buscamos si el precio actual o de la vela anterior barrió mínimos/máximos pasados (pools de liquidez) y regresó
    if i >= 15:
        minimo_previo = df['low'].iloc[i-15:i-2].min()
        maximo_previo = df['high'].iloc[i-15:i-2].max()
        
        # Barrido Bajista (Toma liquidez de Sell Stops y rechaza al alza)
        if df['low'].iloc[i] < minimo_previo and df['close'].iloc[i] > minimo_previo:
            confirmaciones["sweep_liquidez_detectado"] = True
            
        # Barrido Alcista (Toma liquidez de Buy Stops y rechaza a la baja)
        if df['high'].iloc[i] > maximo_previo and df['close'].iloc[i] < maximo_previo:
            confirmaciones["sweep_liquidez_detectado"] = True

    if df['close'].iloc[i-1] < df['open'].iloc[i-1] and df['close'].iloc[i] > df['high'].iloc[i-1]:
        confirmaciones["order_block_detectado"] = True

    if df['close'].iloc[i] > df['high'].iloc[i-2] and df['close'].iloc[i-2] < df['open'].iloc[i-2]:
         confirmaciones["breaker_block_detectado"] = True

    return confirmaciones

# ------------------------------------------------------------------------------
# 4. COMUNICACIÓN CON FASTAPI (Nube)
# ------------------------------------------------------------------------------
async def sincronizar_matriz_tecnica(activo: str, confirmaciones: Dict[str, bool], rsi_val: float, ma_alineada: bool, soporte_activo: bool, killzone_activa: bool = True):
    url = f"{FASTAPI_URL}/webhook_technical_update"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    
    smc_codes = []
    if confirmaciones["order_block_detectado"]: smc_codes.append(1)
    if confirmaciones["fvg_detectado"]: smc_codes.append(2)
    if confirmaciones["breaker_block_detectado"]: smc_codes.append(3)
    if confirmaciones["sweep_liquidez_detectado"]: smc_codes.append(4)
    
    payload = {
        "activo": activo,
        "killzone_activa": killzone_activa,
        "confirmaciones_tecnicas": {
            "soporte_resistencia_activo": bool(soporte_activo),
            "medias_moviles_alineadas": bool(ma_alineada),
            "rsi_sobrecompra_sobreventa": bool(rsi_val >= 80 or rsi_val <= 20),
            "smc_codes": smc_codes
        }
    }

    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload, timeout=5)
            if response.status_code == 200:
                print(f"| CLOUD | Confirmaciones para {activo} actualizadas con éxito.")
                return response.json()
            else:
                print(f"| CLOUD ERROR | No se pudo actualizar matriz en la nube: {response.text}")
    except Exception as e:
        print(f"| CLOUD EXCEPTION | Error al conectar con FastAPI en sincronizar: {e}")
        await reportar_error_nube("Sincronización FastAPI", str(e))
    return None

async def reportar_error_nube(componente: str, mensaje: str):
    url = f"{FASTAPI_URL}/webhook_log_error"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {"componente": componente, "mensaje": mensaje}
    try:
        async with httpx.AsyncClient() as client:
            await client.post(url, headers=headers, json=payload, timeout=3)
    except:
        pass

async def solicitar_autorizacion_trade(activo: str, accion: str, precio: float) -> Optional[Dict]:
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
        # Aumentamos el timeout a 45 segundos porque /webhook_mt5_setup 
        # consulta a IAs como Gemini/ChatGPT que tardan en responder
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload, timeout=45.0)
            if response.status_code == 200:
                return response.json()
    except Exception as e:
        print(f"| CLOUD EXCEPTION | Error al solicitar autorización de trade: {e}")
    return None

async def reportar_evento_trade(simbolo: str, ticket: str, tipo_posicion: str, evento: str, precio: float, sl: float, tp: float, pnl: float = 0.0, comentario: str = ""):
    url = f"{FASTAPI_URL}/webhook"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    
    is_buy = (tipo_posicion == "POSITION_TYPE_BUY" or tipo_posicion == "0")
    if evento == "APERTURA":
        accion = "COMPRA" if is_buy else "VENTA"
        estrategia = f"APERTURA (Ticket {ticket})"
    elif evento == "CIERRE_PARCIAL":
        accion = "CIERRE_PARCIAL"
        estrategia = f"PARCIAL (Ticket {ticket}) - {comentario}"
    else:
        accion = "CIERRE_TOTAL"
        estrategia = f"CIERRE (Ticket {ticket}) - {comentario}"
        
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
        "ticket": int(ticket) if ticket.isdigit() else 0
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload, timeout=5)
            if response.status_code == 200:
                print(f"| CLOUD SUCCESS | Evento {evento} registrado con éxito en Notion y Bitacora Excel.")
            else:
                print(f"| CLOUD ERROR | No se pudo registrar el evento: {response.text}")
    except Exception as e:
        print(f"| CLOUD EXCEPTION | Error al reportar evento de trade: {e}")

async def reportar_rechazo(activo: str, motivo: str):
    """Notifica al backend que el trade no pudo ser ejecutado para actualizar el Live Feed"""
    try:
        url = f"{FASTAPI_URL}/webhook_marcar_rechazado"
        headers = {"Authorization": f"Bearer {ACCESS_TOKEN}", "Content-Type": "application/json"}
        payload = {"activo": activo, "motivo": motivo}
        async with httpx.AsyncClient() as client:
            await client.post(url, headers=headers, json=payload, timeout=5)
    except Exception as e:
        print(f"| CLOUD ERROR | No se pudo reportar rechazo al backend: {e}")

async def obtener_matriz_activo(activo: str) -> Optional[Dict]:
    url = f"{FASTAPI_URL}/get_asset_matrix?activo={activo}"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, timeout=5)
            if response.status_code == 200:
                return response.json()
    except Exception as e:
        print(f"| CLOUD ERROR | Error al obtener matriz para {activo}: {e}")
    return None

# ------------------------------------------------------------------------------
# 5. GESTIÓN DE POSICIONES ACTIVAS (MetaAPI)
# ------------------------------------------------------------------------------
async def gestionar_posiciones_activas(connection):
    global POSICIONES_ACTIVAS
    
    try:
        positions = await connection.get_positions()
    except Exception as e:
        print(f"| METAAPI ERROR | No se pudieron obtener posiciones: {e}")
        return

    tickets_actuales = set()
    
    for pos in positions:
        # pos fields: id, symbol, type, openPrice, currentPrice, volume, stopLoss, takeProfit, profit, swap, commission, magic
        # solo monitoreamos las que tengan el magic de Leona
        if getattr(pos, 'magic', 0) != 20260616:
            continue

        ticket = pos.id
        tickets_actuales.add(ticket)
        
        # 1. SI ES UNA NUEVA POSICIÓN: Registrar e informar de APERTURA
        if ticket not in POSICIONES_ACTIVAS:
            POSICIONES_ACTIVAS[ticket] = {
                "volume": pos.volume,
                "symbol": pos.symbol,
                "type": pos.type,
                "price_open": pos.openPrice,
                "tp": pos.takeProfit or 0.0,
                "sl": pos.stopLoss or 0.0,
                "parcial_tomado": False
            }
            print(f"| SEGUIMIENTO | Nueva posición detectada. Ticket: {ticket} | Lote: {pos.volume}")
            await reportar_evento_trade(pos.symbol, ticket, pos.type, "APERTURA", pos.openPrice, pos.stopLoss or 0.0, pos.takeProfit or 0.0)
            
        activo = next((act for act in ACTIVOS if MAPEO_BROKER.get(act) == pos.symbol), None)
        if not activo:
            continue
            
        entry_price = pos.openPrice
        current_price = pos.currentPrice
        tp = pos.takeProfit or 0.0
        sl = pos.stopLoss or 0.0
        volume = pos.volume
        
        if tp == 0.0:
            continue
            
        # Target 1 (TP1) al 50% de la distancia al TP final
        distancia_total = tp - entry_price
        tp1 = entry_price + (distancia_total * 0.5)
        
        es_buy = pos.type == 'POSITION_TYPE_BUY'
        alcanzo_tp1 = (es_buy and current_price >= tp1) or (not es_buy and current_price <= tp1)
        
        # A. Tomar Parciales al 80% si no se ha tomado (lote remanente > 0.02 y alcanzó TP1)
        if alcanzo_tp1 and volume > 0.02 and not POSICIONES_ACTIVAS[ticket]["parcial_tomado"]:
            lote_a_cerrar = volume * 0.8
            lote_a_cerrar = round(lote_a_cerrar, 2)
            if lote_a_cerrar >= 0.01:
                print(f"| GESTOR PARCIALES | Intentando cerrar parcialmente {lote_a_cerrar} lotes de {ticket}...")
                try:
                    close_result = await connection.close_position_partially(ticket, lote_a_cerrar)
                    POSICIONES_ACTIVAS[ticket]["parcial_tomado"] = True
                    POSICIONES_ACTIVAS[ticket]["volume"] = volume - lote_a_cerrar
                    
                    await asyncio.sleep(1)
                    # PnL estimado de esta parcial (MetaAPI no devuelve deals historicos directamente de forma facil en RPC de inmediato, estimamos o enviamos 0.0)
                    pnl_parcial = (current_price - entry_price) * lote_a_cerrar * 100 # Estimado basico
                    if not es_buy:
                        pnl_parcial = -pnl_parcial
                    
                    await reportar_evento_trade(pos.symbol, ticket, pos.type, "CIERRE_PARCIAL", current_price, sl, tp, pnl=pnl_parcial, comentario=f"Cerrado 80% ({lote_a_cerrar:.2f} lotes)")
                except Exception as e:
                    print(f"| GESTOR PARCIALES ERROR | Falló cierre parcial para ticket {ticket}: {e}")
                    
        # B. Gestión de Break-Even dinámico relativo a Liquidez Institucional
        distancia_tp1 = abs(tp1 - entry_price)
        rango_tolerancia = distancia_tp1 * 0.15
        
        esta_en_zona_entrada = False
        if es_buy:
            esta_en_zona_entrada = (current_price <= entry_price + rango_tolerancia) and (sl < entry_price)
        else:
            esta_en_zona_entrada = (current_price >= entry_price - rango_tolerancia) and (sl > entry_price or sl == 0.0)
            
        if esta_en_zona_entrada:
            # Consultar base de datos en la nube para volumen institucional (Firestore)
            matrix = await obtener_matriz_activo(activo)
            liq_institucional = False
            if matrix:
                confirmaciones_inst = matrix.get("confirmaciones_institucionales", {})
                liq_institucional = confirmaciones_inst.get("dark_pools_compra_masiva", False) or \
                                    confirmaciones_inst.get("heatmap_ordenes_limite", False)
                                    
            if liq_institucional:
                print(f"| GESTOR BE | {activo} regresando a entrada. Soporte institucional DETECTADO. Manteniendo SL original.")
            else:
                print(f"| GESTOR BE | {activo} regresando a entrada sin soporte institucional. Colocando Break-Even.")
                try:
                    # Modificar SL a Break-Even
                    await connection.modify_position(ticket, entry_price, tp)
                    print(f"| GESTOR BE SUCCESS | Ticket {ticket} modificado a Break-Even (SL={entry_price}).")
                    POSICIONES_ACTIVAS[ticket]["sl"] = entry_price
                except Exception as e:
                    print(f"| GESTOR BE ERROR | No se pudo modificar ticket {ticket} a BE: {e}")

    # 2. DETECTAR POSICIONES CERRADAS TOTALMENTE
    tickets_cerrados = []
    for ticket, info in POSICIONES_ACTIVAS.items():
        if ticket not in tickets_actuales:
            tickets_cerrados.append(ticket)
            
    for ticket in tickets_cerrados:
        info = POSICIONES_ACTIVAS[ticket]
        print(f"| SEGUIMIENTO | Posición cerrada detectada. Ticket: {ticket}")
        
        # En la nube estimamos PnL final desde los precios o intentamos leer información de la cuenta
        # Para simplificar y mantener la consistencia con Notion/Excel:
        try:
            # Recuperar precio actual del activo para reporte
            price = await connection.get_symbol_price(info["symbol"])
            precio_cierre = price.get('bid' if info["type"] == 'POSITION_TYPE_BUY' else 'ask', info["price_open"])
        except Exception:
            precio_cierre = info["price_open"]
            
        pnl_final = (precio_cierre - info["price_open"]) * info["volume"] * 100
        if info["type"] == 'POSITION_TYPE_SELL':
            pnl_final = -pnl_final
            
        await reportar_evento_trade(info["symbol"], ticket, info["type"], "CIERRE_TOTAL", precio_cierre, info["sl"], info["tp"], pnl=pnl_final, comentario="Cerrado totalmente")
        del POSICIONES_ACTIVAS[ticket]

# ------------------------------------------------------------------------------
# 6. GESTOR DE OPERACIONES (Apertura de Órdenes)
# ------------------------------------------------------------------------------
async def ejecutar_orden_cloud(connection, activo: str, accion: str, precio: float, decision: Dict) -> bool:
    simbolo_broker = MAPEO_BROKER.get(activo, activo)
    
    try:
        tick = await connection.get_symbol_price(simbolo_broker)
        if not tick:
            print(f"| METAAPI ERROR | No se pudo obtener ticks para {simbolo_broker}")
            return False
            
        es_buy = accion.upper() == "COMPRA"
        precio_ejecucion = tick.get('ask' if es_buy else 'bid', precio)
        
        sl = decision.get("stop_loss", precio_ejecucion - 200 if es_buy else precio_ejecucion + 200)
        tp = decision.get("take_profit", precio_ejecucion + 400 if es_buy else precio_ejecucion - 400)
        lote = decision.get("lote", 0.2)

        # Generar un clientId único que siga el patrón requerido y no supere la longitud
        short_sym = simbolo_broker.replace("/", "").replace("-", "")[:6]
        client_id = f"L_{short_sym}_{random.randint(1000, 9999)}"
        options = {
            'comment': 'Mia',
            'clientId': client_id
        }

        print(f"| TRADING | Enviando orden de {accion} en {simbolo_broker} (Lote: {lote})...")
        if es_buy:
            result = await connection.create_market_buy_order(simbolo_broker, lote, sl, tp, options)
        else:
            result = await connection.create_market_sell_order(simbolo_broker, lote, sl, tp, options)

        order_id = result.get("orderId", "N/A")
        print(f"| METAAPI SUCCESS | Orden colocada con éxito en {simbolo_broker}. Ticket ID: {order_id}")
        
        # Avisar al backend que ya se ejecutó para que apague el semáforo y evite doble ejecución
        try:
            url = f"{FASTAPI_URL}/webhook_marcar_ejecutado"
            headers = {"Authorization": f"Bearer {ACCESS_TOKEN}", "Content-Type": "application/json"}
            payload = {
                "ticket": str(order_id),
                "activo": activo,
                "accion": accion,
                "score": 100.0,
                "precio_ejecucion": precio_ejecucion,
                "ejecutada_mt5": True,
                "motivo": "Ejecutada por Escáner Cloud"
            }
            async with httpx.AsyncClient() as client:
                await client.post(url, headers=headers, json=payload, timeout=5)
        except Exception as e:
            print(f"| CLOUD ERROR | No se pudo marcar como ejecutado: {e}")
            
        return True

    except Exception as e:
        error_str = str(e)
        if hasattr(e, 'details'):
            error_str += f" | {e.details}"
        print(f"| METAAPI ERROR | Orden rechazada por broker o API: {error_str}")
        await reportar_rechazo(activo, f"Rechazado por Broker (MetaAPI): {error_str}")
        return False

# ------------------------------------------------------------------------------
# 7. HORARIO DE KILLZONES
# ------------------------------------------------------------------------------
def obtener_nombre_killzone() -> Optional[str]:
    """Verifica si la hora actual local de México (GMT-6) está dentro de una Killzone."""
    LONDRES_INICIO = 2.0
    LONDRES_FIN = 5.0
    NY_INICIO = 7.0
    NY_FIN = 10.0
    ASIA_INICIO = 18.0
    ASIA_FIN = 22.0
    
    # Forzar hora de México (GMT-6) en cualquier servidor (Render corre en UTC)
    gmt_minus_6 = datetime.timezone(datetime.timedelta(hours=-6))
    ahora = datetime.datetime.now(gmt_minus_6)
    hora_decimal = ahora.hour + ahora.minute / 60.0
    
    if LONDRES_INICIO <= hora_decimal < LONDRES_FIN:
        return "LONDRES"
    elif NY_INICIO <= hora_decimal < NY_FIN:
        return "NUEVA_YORK"
    elif ASIA_INICIO <= hora_decimal < ASIA_FIN:
        return "ASIA"
    return None

# ------------------------------------------------------------------------------
# 7.1 VERIFICACIÓN DE MERCADO ABIERTO
# ------------------------------------------------------------------------------
def es_mercado_abierto(activo: str) -> bool:
    """Verifica si el mercado del activo está abierto (Hora de México GMT-6)."""
    # Criptomonedas operan 24/7
    if "BTC" in activo.upper() or "CRYPTO" in activo.upper():
        return True
        
    gmt_minus_6 = datetime.timezone(datetime.timedelta(hours=-6))
    ahora = datetime.datetime.now(gmt_minus_6)
    dia = ahora.weekday() # 0=Mon, 1=Tue, 2=Wed, 3=Thu, 4=Fri, 5=Sat, 6=Sun
    hora = ahora.hour
    
    # Fin de semana (Forex/Metales): Cierra Viernes 15:00, Abre Domingo 15:00
    if dia == 4 and hora >= 15: return False
    if dia == 5: return False
    if dia == 6 and hora < 15: return False
    
    # Receso diario (Forex/Metales): Lunes a Jueves de 15:00 a 16:00
    if dia < 4 and hora == 15: return False
    
    return True

# ------------------------------------------------------------------------------
# 8. BUCLE PRINCIPAL DE ANÁLISIS EN LA NUBE
# ------------------------------------------------------------------------------
async def ejecutar_escaner_cloud(account, connection):
    try:
        await gestionar_posiciones_activas(connection)
    except Exception as e:
        print(f"| GESTOR POSICIONES ERROR | Falló gestión de posiciones en la nube: {e}")
        
    killzone_activa = obtener_nombre_killzone()
    if killzone_activa:
        print(f"| ESCANER CLOUD | Sesión activa: {killzone_activa} | Escaneando {len(ACTIVOS)} activos en H1...")
    else:
        print("| ESCANER CLOUD | Fuera de horario de Killzones. Sincronizando pero entradas desactivadas.")
        
    for activo in ACTIVOS:
        if not es_mercado_abierto(activo):
            print(f"| MERCADO CERRADO | {activo} en receso o fin de semana. Omitiendo escaneo.")
            continue
            
        simbolo = MAPEO_BROKER.get(activo)
        # Análisis Multi-Temporal (MTF): 1H y 4H
        df_1h = await obtener_velas_cloud(account, simbolo, '1h', 100)
        df_4h = await obtener_velas_cloud(account, simbolo, '4h', 300)
        
        if df_1h is None or df_1h.empty or df_4h is None or df_4h.empty:
            continue
            
        # 1. Indicadores Macro (Basados en 4H para mayor fiabilidad)
        rsi_series = calcular_rsi(df_4h)
        rsi_actual = rsi_series.iloc[-1]
        
        ema_50 = df_4h['close'].ewm(span=50, adjust=False).mean().iloc[-1]
        ema_200 = df_4h['close'].ewm(span=200, adjust=False).mean().iloc[-1]
        precio_actual = df_4h['close'].iloc[-1]
        ma_alineada = (precio_actual > ema_50 > ema_200) or (precio_actual < ema_50 < ema_200)
        
        niveles = detectar_soportes_resistencias(df_4h)
        soporte_activo = False
        for sup in niveles["soportes"]:
            if abs(precio_actual - sup) < (precio_actual * 0.001):
                soporte_activo = True
                break
                
        # 2. SMC Institucional Fusión (1H + 4H)
        conf_1h = analizar_smc_ict(df_1h)
        conf_4h = analizar_smc_ict(df_4h)
        
        confirmaciones = {
            "order_block_detectado": conf_1h["order_block_detectado"] or conf_4h["order_block_detectado"],
            "fvg_detectado": conf_1h["fvg_detectado"] or conf_4h["fvg_detectado"],
            "breaker_block_detectado": conf_1h["breaker_block_detectado"] or conf_4h["breaker_block_detectado"],
            "sweep_liquidez_detectado": conf_1h["sweep_liquidez_detectado"] or conf_4h["sweep_liquidez_detectado"]
        }
        
        # 1. Sincronizar confirmaciones con la matriz en Firestore (vía webhook)
        webhook_response = await sincronizar_matriz_tecnica(activo, confirmaciones, rsi_actual, ma_alineada, soporte_activo, bool(killzone_activa))
        
        # 2. Validar si el backend (Firebase) autorizó el gatillo (Score >= 80%)
        gatillo_autorizado = webhook_response and webhook_response.get("gatillo_entrada") is True
        
        if gatillo_autorizado:
            if not killzone_activa:
                print(f"| GATILLO CLOUD OMITIDO | Setup detectado en {activo} pero está fuera de Killzone.")
                continue
                
            accion = "COMPRA" if (precio_actual > ema_50) else "VENTA"
            
            # Solicitar autorización al cerebro (Mia)
            decision = await solicitar_autorizacion_trade(activo, accion, precio_actual)
            
            if decision and decision.get("authorized") is True:
                print(f"| LEONA DE LA LIQUIDEZ CLOUD | ¡Gatillo Cruzado Exitoso! Entrando al mercado...")
                exito = await ejecutar_orden_cloud(connection, activo, accion, precio_actual, decision)
                if not exito:
                    print(f"| GATILLO RECHAZADO | Falló la ejecución en el broker.")
            else:
                reason = decision.get("reason", "Razón desconocida") if decision else "No hubo respuesta del cerebro"
                print(f"| GATILLO RECHAZADO | El cerebro (Mia) denegó la ejecución: {reason}")
                await reportar_rechazo(activo, f"Mia Denegó: {reason}")
                
        await asyncio.sleep(2)

async def run_escaner_loop():
    """Bucle infinito del escáner en segundo plano diseñado para integrarse con FastAPI."""
    print("🤖 Iniciando escáner e ejecutor asíncrono de MetaAPI en la nube...")
    
    # Bucle de conexión hasta tener éxito
    account, connection = None, None
    while not account or not connection:
        account, connection = await conectar_metaapi()
        if not account or not connection:
            print("⏳ Reintentando conexión a MetaAPI en 15 segundos...")
            await asyncio.sleep(15)
            
    print("🚀 Escáner de trading asíncrono iniciado correctamente.")
    while True:
        try:
            await ejecutar_escaner_cloud(account, connection)
        except Exception as e:
            print(f"| RUNNER CLOUD ERROR | Ocurrió un fallo en el escáner: {e}")
            await reportar_error_nube("Escáner Core", str(e))
        await asyncio.sleep(900) # Ejecutar cada 15 minutos (900 seg) para timeframes H1-H8

async def abrir_posicion_test(simbolo: str, lote: float) -> str:
    """Función de prueba para abrir una posición directamente en MetaAPI."""
    try:
        from metaapi_cloud_sdk import MetaApi
    except ImportError:
        return "Error: metaapi-cloud-sdk no instalada"
        
    if not METAAPI_TOKEN:
        return "Error: falta METAAPI_TOKEN"
        
    print(f"| TEST TRADE | Intentando abrir compra de prueba en {simbolo} (Lote: {lote})...")
    api = MetaApi(METAAPI_TOKEN)
    try:
        accounts_data = await api.metatrader_account_api.get_accounts_with_infinite_scroll_pagination()
        accounts = accounts_data if isinstance(accounts_data, list) else (accounts_data.get('items', []) if hasattr(accounts_data, 'get') else getattr(accounts_data, 'items', []))
        account = next((a for a in accounts if a.login == MT5_LOGIN), None)
        
        if not account:
            return f"Error: Cuenta demo {MT5_LOGIN} no encontrada en MetaAPI"
            
        await account.wait_connected()
        connection = account.get_rpc_connection()
        await connection.connect()
        await connection.wait_synchronized()
        
        # Obtener símbolo del broker
        simbolo_broker = MAPEO_BROKER.get(simbolo, simbolo)
        
        # Generar clientId
        import random
        short_sym = simbolo_broker.replace("/", "").replace("-", "")[:6]
        client_id = f"T_{short_sym}_{random.randint(1000, 9999)}"
        options = {
            'comment': 'Test Buy',
            'clientId': client_id
        }
        
        # Obtener precio para TP/SL estimados
        tick = await connection.get_symbol_price(simbolo_broker)
        if not tick:
            return f"Error: No se pudo obtener precio para {simbolo_broker}"
            
        precio_ej = tick.get('ask', 0.0)
        
        # TP/SL amplios
        if simbolo == "XAUUSD":
            sl = precio_ej - 5.0
            tp = precio_ej + 10.0
        else:
            sl = precio_ej * 0.99
            tp = precio_ej * 1.02
            
        print(f"| TEST TRADE | Enviando compra al broker para {simbolo_broker} (Precio: {precio_ej}, SL: {sl}, TP: {tp})")
        result = await connection.create_market_buy_order(simbolo_broker, lote, sl, tp, options)
        order_id = result.get("orderId", "N/A")
        print(f"| TEST TRADE SUCCESS | Posición abierta con éxito. Ticket ID: {order_id}")
        return f"Exito: Orden colocada. Ticket ID: {order_id}"
    except Exception as e:
        print(f"| TEST TRADE ERROR | Fallo la orden de prueba: {e}")
        return f"Error: {e}"
