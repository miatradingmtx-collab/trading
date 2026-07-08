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

# Parámetros de la Matriz de Riesgo Residual (Inteligencia de Negocio)
BASE_BALANCE_MENSUAL = 5000.0
OBJETIVO_MENSUAL_PCT = 10.0
RIESGO_RESIDUAL_MAX_PCT = 25.0  # Porcentaje máximo del colchón residual a arriesgar por trade

# Diccionario global para trackear posiciones y detectar aperturas, parciales y cierres en bucle
# ticket -> {"volume": float, "symbol": str, "type": int, "price_open": float, "tp": float, "sl": float, "parcial_tomado": bool}
POSICIONES_ACTIVAS = {}

ACTIVOS = ["GBPJPY", "GBPUSD", "EURUSD", "XAUUSD", "AUDUSD", "NZDCAD"]

# Mapeo de nombres de activos locales a símbolos del Broker
MAPEO_BROKER = {
    "NASDAQ100": "USTEC",
    "SP500": "US500",
    "US30": "US30",
    "BTC": "BTCUSD",
    "GBPJPY": "GBPJPY",
    "GBPUSD": "GBPUSD",
    "EURUSD": "EURUSD",
    "XAUUSD": "XAUUSD",
    "AUDUSD": "AUDUSD",
    "NZDCAD": "NZDCAD"
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

async def obtener_balance(connection) -> tuple:
    """Obtiene el balance y la equidad actual de la cuenta conectada."""
    try:
        info = await connection.get_account_information()
        return float(info.get('balance', 0.0)), float(info.get('equity', 0.0))
    except Exception as e:
        print(f"| GESTOR RIESGO | Error al obtener balance: {e}")
        return 0.0, 0.0

def calcular_lotaje_dinamico(balance: float, riesgo_pct: float, entry_price: float, sl_price: float, simbolo: str) -> float:
    """Calcula el lote basado en un riesgo % del balance y la distancia del SL."""
    if balance <= 0 or sl_price == 0 or entry_price == 0 or entry_price == sl_price:
        return 0.02 # Fallback
        
    # 1. Calcular objetivo del mes
    objetivo_dinero = BASE_BALANCE_MENSUAL * (1.0 + OBJETIVO_MENSUAL_PCT / 100.0)
    
    # 2. Lógica de Riesgo Residual (Cushion)
    es_colchon_activo = False
    if balance > objetivo_dinero:
        es_colchon_activo = True
        colchon_residual = balance - objetivo_dinero
        # Arriesgamos un porcentaje del colchón acumulado
        riesgo_dinero = colchon_residual * (RIESGO_RESIDUAL_MAX_PCT / 100.0)
        print(f"| GESTOR RIESGO | Colchón Residual Activo (Meta del {OBJETIVO_MENSUAL_PCT}% superada). Colchón: ${colchon_residual:.2f}. Riesgo asignado: ${riesgo_dinero:.2f}")
    else:
        # 3. Lógica Normal / Escudo de Drawdown
        if balance <= 4200.0:
            riesgo_pct = riesgo_pct * 0.5
            print(f"| GESTOR RIESGO | Escudo de Drawdown activado (Balance <= $4200). Reduciendo riesgo al 50%: {riesgo_pct:.2f}%")
        
        riesgo_dinero = balance * (riesgo_pct / 100.0)

    # 4. Calcular distancia de pips y valor del lote
    distancia_precio = abs(entry_price - sl_price)
    
    # 1 Lote estandar (1.00) = $10 por pip (Forex) o $10 por $1 move (Oro)
    if "JPY" in simbolo:
        distancia_pips = distancia_precio * 100
        valor_pip_lote_estandar = 6.5 # Approx para GBPJPY
    elif "XAU" in simbolo or "GOLD" in simbolo:
        distancia_pips = distancia_precio * 10
        valor_pip_lote_estandar = 10.0
    else:
        distancia_pips = distancia_precio * 10000
        valor_pip_lote_estandar = 10.0
        
    if distancia_pips <= 0:
        return 0.02
        
    lotes = riesgo_dinero / (distancia_pips * valor_pip_lote_estandar)
    lotes = round(lotes, 2)
    
    # Validar restricción estricta de pérdida máxima si estamos sobre el objetivo
    if es_colchon_activo:
        max_perdida_posible = lotes * distancia_pips * valor_pip_lote_estandar
        # Si la pérdida esperada supera el colchón residual total, reducimos el lote al mínimo seguro
        if max_perdida_posible > colchon_residual:
            lotes = colchon_residual / (distancia_pips * valor_pip_lote_estandar)
            lotes = round(lotes, 2)
            
        # Si el colchón no alcanza ni para el lote mínimo de 0.01, cancelamos la entrada para proteger el ancla
        if lotes < 0.01:
            print(f"| GESTOR RIESGO CANCEL | Trade cancelado para proteger el ancla de ganancias (${objetivo_dinero}). Colchón insuficiente.")
            return 0.0
            
    # Limites operativos normales
    if lotes < 0.01: lotes = 0.01
    if lotes > 10.0: lotes = 10.0
    
    return lotes

async def verificar_drawdown_diario(balance: float, limite_pct: float = 3.0) -> bool:
    """Consulta el backend para ver si el PNL de hoy supera la pérdida máxima permitida."""
    url = f"{FASTAPI_URL}/api/pnl_hoy"
    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, timeout=5)
            if response.status_code == 200:
                data = response.json()
                pnl_hoy = float(data.get("pnl_hoy", 0.0))
                limite_dinero = -(balance * (limite_pct / 100.0))
                
                # Si la pérdida actual superó el límite (ej. pnl -150 <= -100)
                if pnl_hoy <= limite_dinero:
                    print(f"| GESTOR RIESGO ALERTA | ⛔ DRAWDOWN DIARIO ALCANZADO: PNL Hoy ${pnl_hoy:.2f} <= Límite ${limite_dinero:.2f} (-{limite_pct}%). Modo Pausa Activo.")
                    return True
                return False
    except Exception as e:
        print(f"| GESTOR RIESGO EXCEPTION | No se pudo verificar PNL diario: {e}")
    return False

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
def calcular_volume_profile_poc(df: pd.DataFrame, num_bins: int = 50) -> float:
    """
    Calcula el Point of Control (POC) basado en el Perfil de Volumen de las velas proporcionadas.
    Retorna el nivel de precio (centro del bin) con mayor volumen operado.
    """
    if df is None or df.empty or 'tickVolume' not in df.columns:
        return 0.0
        
    try:
        # Calcular el precio representativo de la vela
        df['typical_price'] = (df['high'] + df['low'] + df['close']) / 3
        min_price = df['low'].min()
        max_price = df['high'].max()
        
        # Crear los rangos de precio (bins)
        bins = np.linspace(min_price, max_price, num_bins)
        
        # Asignar cada vela a un bin
        indices = np.digitize(df['typical_price'], bins)
        
        vol_profile = {}
        for i in range(len(df)):
            bin_idx = indices[i]
            vol = df['tickVolume'].iloc[i]
            if pd.isna(vol): vol = 0
            
            if bin_idx not in vol_profile:
                vol_profile[bin_idx] = 0
            vol_profile[bin_idx] += vol
            
        # Encontrar el bin con maximo volumen
        max_bin_idx = max(vol_profile, key=vol_profile.get)
        
        # El POC es el centro aproximado de ese bin
        if max_bin_idx < len(bins):
            poc_price = bins[max_bin_idx - 1] if max_bin_idx > 0 else bins[0]
        else:
            poc_price = bins[-1]
            
        return float(poc_price)
    except Exception as e:
        print(f"| POC ERROR | Error calculando Volume Profile: {e}")
        return 0.0

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
async def sincronizar_matriz_tecnica(activo: str, confirmaciones: Dict[str, bool], rsi_val: float, ma_alineada: bool, soporte_activo: bool, killzone_activa: bool = True, poc_price: float = 0.0):
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
            "smc_codes": smc_codes,
            "poc_price": poc_price
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
        "ticket": str(ticket)
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
async def gestionar_posiciones_activas(connection, balance: float):
    global POSICIONES_ACTIVAS
    
    # 0. Obtener tickets abiertos en Firebase para validación cruzada y autocuración
    fb_open = []
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.get(f"{FASTAPI_URL}/api/open_trades")
            if r.status_code == 200:
                fb_open = [str(t) for t in r.json().get("open_tickets", [])]
    except Exception as api_err:
        print(f"| GESTOR RIESGO WARN | No se pudo sincronizar tickets de Firebase: {api_err}")

    try:
        positions = await connection.get_positions()
    except Exception as e:
        print(f"| METAAPI ERROR | No se pudieron obtener posiciones: {e}")
        return

    tickets_actuales = set()
    
    for p in positions:
        pos = p if isinstance(p, dict) else getattr(p, '__dict__', {})
        ticket = str(pos.get('id', ''))
        
        # pos fields: id, symbol, type, openPrice, currentPrice, volume, stopLoss, takeProfit, profit, swap, commission, magic
        client_id = pos.get('clientId', '')
        magic = pos.get('magic', 0)
        
        # Validar si es una operación de Mia (por Magic Number, Client ID o si está activa en Firebase)
        is_mia = (magic == 20260616) or (isinstance(client_id, str) and client_id.startswith('L_')) or (ticket in fb_open)
        if not is_mia:
            continue

        tickets_actuales.add(ticket)
        
        # 1. SI ES UNA NUEVA POSICIÓN: Registrar e informar de APERTURA
        if ticket not in POSICIONES_ACTIVAS:
            tp_original = pos.get('takeProfit', 0.0)
            parcial_ya_tomado = False
            
            # Autocuración: Si no tiene TP, intentar recuperarlo de Firebase
            if tp_original == 0.0:
                try:
                    async with httpx.AsyncClient() as client:
                        r = await client.get(f"{FASTAPI_URL}/api/get_trade_tp/{ticket}", timeout=5)
                        if r.status_code == 200:
                            res_data = r.json()
                            if res_data.get("status") == "success":
                                if res_data.get("tp", 0.0) > 0.0:
                                    tp_original = res_data["tp"]
                                    print(f"| AUTOCURACIÓN | Ticket {ticket} sin TP detectado. Restaurando TP original: {tp_original}")
                                    try:
                                        await connection.modify_position(ticket, stop_loss=pos.get('stopLoss', 0.0), take_profit=tp_original)
                                    except Exception as modify_err:
                                        print(f"| AUTOCURACIÓN ERROR | No se pudo inyectar TP en MT5: {modify_err}")
                                parcial_ya_tomado = res_data.get("parcial_tomado", False)
                except Exception as auto_e:
                    print(f"| AUTOCURACIÓN WARN | Fallo al buscar TP en Firebase: {auto_e}")
            
            POSICIONES_ACTIVAS[ticket] = {
                "volume": pos.get('volume', 0.0),
                "symbol": pos.get('symbol', ''),
                "type": pos.get('type', ''),
                "price_open": pos.get('openPrice', 0.0),
                "tp": tp_original,
                "sl": pos.get('stopLoss', 0.0),
                "parcial_tomado": parcial_ya_tomado
            }
            print(f"| SEGUIMIENTO | Nueva posición detectada. Ticket: {ticket} | Lote: {pos.get('volume')}")
            await reportar_evento_trade(pos.get('symbol'), ticket, pos.get('type'), "APERTURA", pos.get('openPrice', 0.0), pos.get('stopLoss', 0.0), tp_original)
            
        activo = next((act for act in ACTIVOS if MAPEO_BROKER.get(act) == pos.get('symbol')), None)
        if not activo:
            continue
            
        entry_price = pos.get('openPrice', 0.0)
        current_price = pos.get('currentPrice', 0.0)
        tp = pos.get('takeProfit', 0.0)
        sl = pos.get('stopLoss', 0.0)
        volume = pos.get('volume', 0.0)
        
        profit_flotante = float(pos.get('profit', pos.get('unrealizedProfit', 0.0)))
            
        es_buy = str(pos.get('type')) in ['POSITION_TYPE_BUY', '0']
        
        # A. Tomar Parciales al 50% de la distancia al Take Profit
        alcanzo_mitad_tp = False
        if tp > 0.0 and entry_price > 0.0:
            distancia_total = abs(tp - entry_price)
            distancia_recorrida = abs(current_price - entry_price)
            # Aseguramos que vamos en direccion a favor
            en_ganancia = (es_buy and current_price > entry_price) or (not es_buy and current_price < entry_price)
            if en_ganancia and distancia_total > 0 and distancia_recorrida >= (distancia_total * 0.5):
                alcanzo_mitad_tp = True
        
        if alcanzo_mitad_tp and volume >= 0.02 and not POSICIONES_ACTIVAS[ticket]["parcial_tomado"]:
            lote_a_cerrar = round(volume * 0.5, 2)
            # Asegurar que siempre quede al menos 0.01 para el runner
            if volume - lote_a_cerrar < 0.01:
                lote_a_cerrar = round(volume - 0.01, 2)
                
            if lote_a_cerrar >= 0.01:
                print(f"| GESTOR PARCIALES | 50% del TP alcanzado. Cerrando {lote_a_cerrar} lotes de {ticket}...")
                try:
                    close_result = await connection.close_position_partially(ticket, lote_a_cerrar)
                    POSICIONES_ACTIVAS[ticket]["parcial_tomado"] = True
                    POSICIONES_ACTIVAS[ticket]["volume"] = volume - lote_a_cerrar
                    
                    await asyncio.sleep(1)
                    # Mover Stop Loss a Break Even + pequeño buffer
                    buffer_be = 0.0001 if not pos.get('symbol', '').endswith("JPY") and "XAU" not in pos.get('symbol', '') else 0.01
                    nuevo_sl = entry_price + buffer_be if es_buy else entry_price - buffer_be
                    try:
                        tp_original = POSICIONES_ACTIVAS[ticket]["tp"]
                        await connection.modify_position(ticket, stop_loss=nuevo_sl, take_profit=tp_original)
                        print(f"| GESTOR RIESGO | SL movido a Break Even para {ticket} (TP mantenido: {tp_original})")
                    except Exception as sl_e:
                        print(f"| GESTOR RIESGO WARNING | No se pudo mover SL a BE: {sl_e}")

                    # PnL estimado de esta parcial
                    distancia_parcial = (current_price - entry_price)
                    if not es_buy:
                        distancia_parcial = -distancia_parcial
                        
                    sym = pos.get('symbol', '').upper()
                    if "JPY" in sym:
                        pnl_parcial = distancia_parcial * lote_a_cerrar * 100000 / current_price
                    elif "XAU" in sym or "GOLD" in sym:
                        pnl_parcial = distancia_parcial * lote_a_cerrar * 100
                    else:
                        pnl_parcial = distancia_parcial * lote_a_cerrar * 100000
                    
                    await reportar_evento_trade(pos.get('symbol', ''), ticket, pos.get('type', ''), "CIERRE_PARCIAL", current_price, sl, tp, pnl=pnl_parcial, comentario=f"Cerrado 50% al alcanzar mitad del TP")
                except Exception as e:
                    print(f"| GESTOR PARCIALES ERROR | Falló cierre parcial para ticket {ticket}: {e}")
                    
        # B. Gestión de SL en ganancias para Runners (Trades que ya tomaron parcial del 50% y están en BE)
        # Si el precio regresa a la zona de entrada pero las condiciones institucionales de H1 siguen siendo favorables,
        # movemos el SL a zona de ganancia asegurada en vez de salir en BE plano.
        if POSICIONES_ACTIVAS[ticket]["parcial_tomado"]:
            distancia_tp1 = abs(tp - entry_price) * 0.4
            rango_tolerancia = distancia_tp1 * 0.25  # Zona amplia de re-test
            
            es_jpy = pos.get('symbol', '').endswith("JPY")
            es_xau = "XAU" in pos.get('symbol', '')
            buffer_ganancia = 0.0003 if not es_jpy and not es_xau else 0.03
            
            # Verificar si el SL ya está en ganancias
            sl_en_ganancia = (es_buy and sl > entry_price + buffer_ganancia) or (not es_buy and sl < entry_price - buffer_ganancia)
            
            if not sl_en_ganancia:
                esta_retornando = False
                if es_buy:
                    esta_retornando = (current_price <= entry_price + rango_tolerancia) and (current_price > entry_price)
                else:
                    esta_retornando = (current_price >= entry_price - rango_tolerancia) and (current_price < entry_price)
                
                if esta_retornando:
                    # Obtener velas 1H para validar Acción del Precio, RSI y EMAs
                    df_1h = await obtener_velas_cloud(account, pos.get('symbol'), '1h', 100)
                    if df_1h is not None and not df_1h.empty:
                        try:
                            # Calcular RSI 14
                            rsi_series = calcular_rsi(df_1h)
                            rsi_1h = rsi_series.iloc[-1]
                            
                            # Calcular EMAs (50 y 200)
                            ema_50 = df_1h['close'].ewm(span=50, adjust=False).mean().iloc[-1]
                            ema_200 = df_1h['close'].ewm(span=200, adjust=False).mean().iloc[-1]
                            
                            # Evaluar confluencias
                            soporte_activo = False
                            resistencia_activa = False
                            sr_levels = detectar_soportes_resistencias(df_1h)
                            
                            # Condición de compra: Estructura alcista, RSI saludable y soporte
                            criterio_buy_valido = False
                            if es_buy:
                                # Soporte o EMA actuando como soporte dinámico
                                cerca_ema = abs(current_price - ema_50) / current_price < 0.001 or abs(current_price - ema_200) / current_price < 0.001
                                soporte_cercano = any(abs(current_price - s) / current_price < 0.0015 for s in sr_levels.get('soportes', []))
                                # RSI no sobrecomprado (espacio para subir) y mayor a 40
                                rsi_valido = 40 < rsi_1h < 68
                                criterio_buy_valido = rsi_valido and (cerca_ema or soporte_cercano or current_price > ema_50)
                            
                            # Condición de venta: Estructura bajista, RSI en zona de ventas y resistencia
                            criterio_sell_valido = False
                            if not es_buy:
                                cerca_ema = abs(current_price - ema_50) / current_price < 0.001 or abs(current_price - ema_200) / current_price < 0.001
                                resistencia_cercana = any(abs(current_price - r) / current_price < 0.0015 for r in sr_levels.get('resistencias', []))
                                rsi_valido = 32 < rsi_1h < 60
                                criterio_sell_valido = rsi_valido and (cerca_ema or resistencia_cercana or current_price < ema_50)
                                
                            if criterio_buy_valido or criterio_sell_valido:
                                # Mover SL a ganancias (asegurar buffer de ganancia adicional en vez de BE simple)
                                nuevo_sl = entry_price + buffer_ganancia if es_buy else entry_price - buffer_ganancia
                                print(f"| GESTOR TRAILING SL | Confluencias H1 válidas (RSI: {rsi_1h:.1f}). Protegiendo runner en ganancias para {ticket}.")
                                try:
                                    await connection.modify_position(ticket, stop_loss=nuevo_sl, take_profit=tp)
                                    print(f"| GESTOR TRAILING SL SUCCESS | Ticket {ticket} SL movido a zona de ganancias: SL={nuevo_sl}")
                                    POSICIONES_ACTIVAS[ticket]["sl"] = nuevo_sl
                                except Exception as e:
                                    print(f"| GESTOR TRAILING SL ERROR | No se pudo mover SL a ganancias para ticket {ticket}: {e}")
                        except Exception as eval_err:
                            print(f"| GESTOR TRAILING SL | Error evaluando indicadores: {eval_err}")
                            
        # C. Gestión de Break-Even dinámico relativo a Liquidez Institucional (Para órdenes que aún no toman parciales)
        if not POSICIONES_ACTIVAS[ticket]["parcial_tomado"]:
            distancia_tp1 = abs(tp - entry_price) * 0.4
            rango_tolerancia = distancia_tp1 * 0.15
            
            esta_en_zona_entrada = False
            if tp > 0.0:
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
                        await connection.modify_position(ticket, stop_loss=entry_price, take_profit=tp)
                        print(f"| GESTOR BE SUCCESS | Ticket {ticket} modificado a Break-Even (SL={entry_price}, TP={tp}).")
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
        
        # Intentamos obtener la ganancia real del deal desde el historial del broker vía MetaAPI
        pnl_final = 0.0
        precio_cierre = info["price_open"]
        try:
            # Traer deals de las últimas 24 horas para encontrar el deal de cierre de este ticket
            desde = datetime.datetime.now() - datetime.timedelta(days=1)
            deals = await connection.get_deals_by_ticket(ticket)
            if deals:
                # Filtrar el deal de salida o acumular PnL de los deals asociados al ticket
                pnl_final = sum(float(d.get('profit', 0.0)) + float(d.get('commission', 0.0)) + float(d.get('swap', 0.0)) for d in deals)
                # Tomar el precio de ejecución del último deal
                precio_cierre = float(deals[-1].get('price', info["price_open"]))
                print(f"| GESTOR COBROS | PnL real obtenido del Broker para Ticket {ticket}: ${pnl_final:.2f} (Precio salida: {precio_cierre})")
            else:
                raise ValueError("No deals found")
        except Exception:
            # Fallback a estimación manual exacta
            try:
                price = await connection.get_symbol_price(info["symbol"])
                precio_cierre = price.get('bid' if info["type"] == 'POSITION_TYPE_BUY' else 'ask', info["price_open"])
            except Exception:
                precio_cierre = info["price_open"]
                
            distancia = (precio_cierre - info["price_open"])
            if info["type"] == 'POSITION_TYPE_SELL' or info["type"] == '1':
                distancia = -distancia
                
            # Forex convencional = 100,000 unidades por lote, JPY = 100,000 unidades (pero cotización en centenas /100), Oro = 100 oz.
            sym = info["symbol"].upper()
            if "JPY" in sym:
                pnl_final = distancia * info["volume"] * 100000 / precio_cierre  # Ajuste de divisa JPY a USD aprox
            elif "XAU" in sym or "GOLD" in sym:
                pnl_final = distancia * info["volume"] * 100 # $100 por dólar de movimiento por lote
            else:
                pnl_final = distancia * info["volume"] * 100000  # $10 por pip en Forex estándar
                
            print(f"| GESTOR COBROS WARNING | Usando PnL estimado para Ticket {ticket}: ${pnl_final:.2f}")
            
        await reportar_evento_trade(info["symbol"], ticket, info["type"], "CIERRE_TOTAL", precio_cierre, info["sl"], info["tp"], pnl=pnl_final, comentario="Cerrado totalmente")
        del POSICIONES_ACTIVAS[ticket]

    # Sincronizar cierres perdidos (manuales o de sesiones anteriores) usando fb_open pre-recuperado
    for t in fb_open:
        if str(t) not in POSICIONES_ACTIVAS and str(t) not in tickets_actuales:
            print(f"| GESTOR RIESGO | Sincronizando cierre faltante para ticket {t}")
            # Intentamos recuperar el PnL del deal histórico antes de poner 0.0
            pnl_sinc = 0.0
            try:
                deals = await connection.get_deals_by_ticket(t)
                if deals:
                    pnl_sinc = sum(float(d.get('profit', 0.0)) + float(d.get('commission', 0.0)) + float(d.get('swap', 0.0)) for d in deals)
            except:
                pass
            await reportar_evento_trade("UNKNOWN", str(t), "UNKNOWN", "CIERRE_TOTAL", 0.0, 0.0, 0.0, pnl=pnl_sinc, comentario="Sincronizado por desaparición en MT5")

# ------------------------------------------------------------------------------
# 6. GESTOR DE OPERACIONES (Apertura de Órdenes)
# ------------------------------------------------------------------------------
async def ejecutar_orden_cloud(connection, activo: str, accion: str, precio: float, decision: Dict, balance: float) -> bool:
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
        
        # LOTAJE DINAMICO (Riesgo configurado sobre el balance diario real, 2% recomendado)
        riesgo_pct = 2.0 
        lote = calcular_lotaje_dinamico(balance, riesgo_pct, precio_ejecucion, sl, simbolo_broker)
        decision["lote"] = lote

        # Generar un clientId único que siga el patrón requerido y no supere la longitud
        short_sym = simbolo_broker.replace("/", "").replace("-", "")[:6]
        client_id = f"L_{short_sym}_{random.randint(1000, 9999)}"
        options = {
            'comment': 'Mia',
            'clientId': client_id,
            'magic': 20260616
        }

        print(f"| TRADING RIESGO | Enviando {accion} en {simbolo_broker} (Balance: ${balance:.2f} | Riesgo {riesgo_pct}% | SL: {sl:.4f} | LOTE: {lote})")
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
                "accion": accion.upper(),
                "score": 100.0,
                "precio_ejecucion": precio_ejecucion,
                "stop_loss": float(sl),
                "take_profit": float(tp),
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
async def ejecutar_escaner_cloud(account, connection, skip_risk=False):
    # 1. Obtener balance y validar Drawdown Diario
    balance, equity = await obtener_balance(connection)
    en_drawdown = await verificar_drawdown_diario(balance, limite_pct=3.0)
    
    if not skip_risk:
        try:
            if FASTAPI_URL and balance > 0:
                import httpx
                async with httpx.AsyncClient() as client:
                    await client.post(f"{FASTAPI_URL}/webhook_update_balance", json={"balance": balance, "equity": equity, "floating_pnl": equity - balance}, headers={"Authorization": f"Bearer {ACCESS_TOKEN}"})
        except Exception as e:
            print(f"| GESTOR BALANCE | Error al enviar webhook_update_balance: {e}")
        
        try:
            await gestionar_posiciones_activas(connection, balance)
        except Exception as e:
            print(f"| GESTOR POSICIONES ERROR | Falló gestión de posiciones en la nube: {e}")
        
    if en_drawdown:
        print("| ESCANER CLOUD | ⛔ Deteniendo escaneo de nuevas entradas por Drawdown Diario (-3%).")
        return # Skip scanning
        
    killzone_activa = obtener_nombre_killzone()
    if killzone_activa:
        print(f"| ESCANER CLOUD | Sesión activa: {killzone_activa} | Escaneando {len(ACTIVOS)} activos en H1...")
    else:
        print("| ESCANER CLOUD | Fuera de horario de Killzones. Sincronizando pero entradas desactivadas.")
        
    try:
        posiciones_activas = await connection.get_positions()
        simbolos_abiertos = [pos.get('symbol') for pos in posiciones_activas]
    except Exception as e:
        print(f"| ESCANER ERROR | No se pudieron obtener las posiciones activas: {e}")
        simbolos_abiertos = []
        
    for activo in ACTIVOS:
        if not es_mercado_abierto(activo):
            print(f"| MERCADO CERRADO | {activo} en receso o fin de semana. Omitiendo escaneo.")
            continue
            
        simbolo = MAPEO_BROKER.get(activo)
        
        if simbolo in simbolos_abiertos:
            print(f"| PROTECCIÓN DOBLE TRADE | Ya existe una posición abierta para {activo} ({simbolo}). Omitiendo escáner para evitar sobreexposición.")
            continue
            
        # Análisis Multi-Temporal (MTF): 1H y 4H
        df_1h = await obtener_velas_cloud(account, simbolo, '1h', 100)
        df_4h = await obtener_velas_cloud(account, simbolo, '4h', 300)
        
        if df_1h is None or df_1h.empty or df_4h is None or df_4h.empty:
            continue
            
        # 1. Indicadores Macro (Basados en 4H para mayor fiabilidad y MTF para RSI)
        df_2h = await obtener_velas_cloud(account, simbolo, '2h', 100)
        df_3h = await obtener_velas_cloud(account, simbolo, '3h', 100)
        
        rsi_1h = calcular_rsi(df_1h).iloc[-1] if df_1h is not None and not df_1h.empty else 50
        rsi_2h = calcular_rsi(df_2h).iloc[-1] if df_2h is not None and not df_2h.empty else 50
        rsi_3h = calcular_rsi(df_3h).iloc[-1] if df_3h is not None and not df_3h.empty else 50
        rsi_4h = calcular_rsi(df_4h).iloc[-1] if df_4h is not None and not df_4h.empty else 50
        
        rsi_avg = (rsi_1h + rsi_2h + rsi_3h + rsi_4h) / 4.0
        rsi_actual = rsi_avg # Reemplazamos rsi_actual por el promedio MTF
        
        poc_price = calcular_volume_profile_poc(df_4h)
        print(f"| POC {activo} | POC Price: {poc_price:.5f} | RSI AVG: {rsi_avg:.2f}")
        
        ema_50 = df_4h['close'].ewm(span=50, adjust=False).mean().iloc[-1]
        ema_200 = df_4h['close'].ewm(span=200, adjust=False).mean().iloc[-1]
        precio_actual = df_4h['close'].iloc[-1]
        ma_alineada = (precio_actual > ema_50 > ema_200) or (precio_actual < ema_50 < ema_200)
        
        niveles = detectar_soportes_resistencias(df_4h)
        soporte_activo = False
        
        # Agregar POC como un nivel fuerte de soporte/resistencia
        niveles_totales = niveles["soportes"] + niveles["resistencias"]
        if poc_price > 0: niveles_totales.append(poc_price)
        
        for nivel in niveles_totales:
            if abs(precio_actual - nivel) < (precio_actual * 0.001):
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
        webhook_response = await sincronizar_matriz_tecnica(activo, confirmaciones, rsi_actual, ma_alineada, soporte_activo, bool(killzone_activa), poc_price)
        
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
                exito = await ejecutar_orden_cloud(connection, activo, accion, precio_actual, decision, balance)
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
    
    # Temporizador para el escáner pesado (cada 15 min)
    ultima_ejecucion_escaner = 0
    
    while True:
        try:
            from time import time
            ahora = time()
            
            # Ejecutar SIEMPRE el Gestor de Posiciones y Balance (Cada 30s)
            balance, equity = await obtener_balance(connection)
            if FASTAPI_URL and balance > 0:
                try:
                    import httpx
                    async with httpx.AsyncClient() as client:
                        await client.post(f"{FASTAPI_URL}/webhook_update_balance", json={"balance": balance, "equity": equity, "floating_pnl": equity - balance}, headers={"Authorization": f"Bearer {ACCESS_TOKEN}"})
                except Exception as e:
                    pass
                    
            try:
                await gestionar_posiciones_activas(connection, balance)
            except Exception as e:
                print(f"| GESTOR POSICIONES ERROR | {e}")
            
            # Ejecutar Escáner de Mercado cada 15 Minutos (900s)
            if ahora - ultima_ejecucion_escaner >= 900:
                await ejecutar_escaner_cloud(account, connection, skip_risk=True)
                ultima_ejecucion_escaner = ahora
                
        except Exception as e:
            print(f"| RUNNER CLOUD ERROR | Ocurrió un fallo en el escáner: {e}")
            await reportar_error_nube("Escáner Core", str(e))
            
        await asyncio.sleep(30) # Loop base cada 30 segundos

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
