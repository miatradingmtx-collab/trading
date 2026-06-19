# ==============================================================================
#                      MODERN TRADING WEB SERVICE (REST API)
# ==============================================================================
# NOTA IMPORTANTE SOBRE ARQUITECTURA:
# Este servicio web ha sido diseñado utilizando arquitectura REST moderna y formato JSON,
# reemplazando el formato XML/SOAP clásico.
#
# ¿Por qué los Web Services XML tradicionales (SOAP/WSDL) están obsoletos aquí?
# 1. TradingView y Notion no soportan XML nativamente para este tipo de flujos.
#    TradingView envía alertas en JSON, y la API de Notion consume estrictamente JSON.
# 2. XML es extremadamente pesado ("verboso") debido a las etiquetas de apertura y cierre.
#    JSON es ligero, rápido de transmitir y nativo en Python y JavaScript.
# 3. SOAP/XML requiere esquemas complejos (WSDL). REST/JSON utiliza FastAPI, que es el
#    estándar de la industria para microservicios de alto rendimiento y baja latencia.
# ==============================================================================

from fastapi import FastAPI, HTTPException, Request, BackgroundTasks, Header, Response
from pydantic import BaseModel
from typing import Optional
import requests
import os
import datetime
import asyncio
from dotenv import load_dotenv
from mt5_executor_cloud import run_escaner_loop

# Cargar variables de entorno desde el archivo .env si existe localmente
load_dotenv()

import json
import firebase_admin
from firebase_admin import credentials, firestore

# Inicializar Firebase de forma segura (redundancia local y nube)
firebase_inicializado = False
db = None

try:
    # 1. Intentar cargar desde un archivo local serviceAccountKey.json
    if os.path.exists("serviceAccountKey.json"):
        cred = credentials.Certificate("serviceAccountKey.json")
        firebase_admin.initialize_app(cred)
        firebase_inicializado = True
        db = firestore.client()
        print("| FIREBASE | Inicializado con éxito usando serviceAccountKey.json local.")
    
    # 2. Si no hay archivo, intentar cargar desde la variable de entorno JSON (para Render/Nube)
    elif os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON"):
        raw_json = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON").strip()
        service_account_info = None
        try:
            service_account_info = json.loads(raw_json)
        except Exception as je:
            print(f"| FIREBASE | json.loads falló ({je}). Intentando método alternativo de extracción por Regex...")
            try:
                import re
                keys = [
                    "type", "project_id", "private_key_id", "private_key",
                    "client_email", "client_id", "auth_uri", "token_uri",
                    "auth_provider_x509_cert_url", "client_x509_cert_url", "universe_domain"
                ]
                extracted = {}
                for key in keys:
                    # Coincidir con "llave": "valor" con comillas simples o dobles
                    pattern = re.compile(
                        r'[\'"]' + re.escape(key) + r'[\'"]\s*:\s*[\'"](.*?)[\'"]',
                        re.DOTALL
                    )
                    match = pattern.search(raw_json)
                    if match:
                        val = match.group(1)
                        # Intentar descodificar con json.loads para resolver escapes estándar de JSON
                        try:
                            val = json.loads(f'"{val}"')
                        except Exception:
                            val = val.replace('\\"', '"').replace("\\'", "'")
                        
                        # Limpieza profunda de la clave privada
                        if key == "private_key":
                            # Convertir representaciones literales de saltos de línea en newlines reales
                            val = val.replace('\\\\n', '\n').replace('\\n', '\n')
                            # Resolver slashes escapados comunes en base64 (\/ -> /)
                            val = val.replace('\\/', '/')
                            # Eliminar cualquier diagonal invertida remanente para evitar fallos de PEM
                            val = val.replace('\\', '')
                        else:
                            val = val.replace('\\\\n', '\n').replace('\\n', '\n')
                        
                        extracted[key] = val
                
                if "private_key" in extracted and "client_email" in extracted:
                    service_account_info = extracted
                    print("| FIREBASE | Datos de cuenta de servicio extraídos con éxito vía Regex.")
                else:
                    raise ValueError("Faltan campos esenciales (private_key o client_email) tras extracción por Regex.")
            except Exception as e2:
                print(f"| FIREBASE ERROR | Falló también la extracción por Regex: {e2}")
                raise e2
        
        if service_account_info:
            cred = credentials.Certificate(service_account_info)
            firebase_admin.initialize_app(cred)
            firebase_inicializado = True
            db = firestore.client()
            print("| FIREBASE | Inicializado con éxito usando variable de entorno.")
    else:
        print("| FIREBASE WARNING | No se encontró archivo serviceAccountKey.json ni variable de entorno. Firebase no guardará datos.")
except Exception as e:
    print(f"| FIREBASE ERROR | Falló la inicialización de Firebase: {e}")

# Inicialización de la aplicación FastAPI (El estándar moderno de Web Services)
app = FastAPI(
    title="Trading Automation Bridge",
    description="Servidor puente moderno para conectar TradingView con Notion, Grok y Excel",
    version="1.0.0"
)

@app.on_event("startup")
async def startup_event():
    # Inicializar la base de datos de Firebase si está conectada
    global firebase_inicializado, db
    if firebase_inicializado and db is not None:
        try:
            # Lista de activos a validar
            activos = ["GBPJPY", "GBPUSD", "EURUSD", "XAUUSD"]
            coleccion_ref = db.collection("trading_matrix")
            
            print("| FIREBASE | Verificando inicialización de la matriz de activos...")
            for activo in activos:
                doc_ref = coleccion_ref.document(activo)
                doc = doc_ref.get()
                if not doc.exists:
                    # Crear el esquema booleano inicial si el documento no existe
                    esquema_activo = {
                        "activo": activo,
                        "ultimo_update": datetime.datetime.now(datetime.timezone.utc).isoformat() if hasattr(datetime, "timezone") else datetime.datetime.now().isoformat(),
                        "score_porcentaje": 0.0,
                        "gatillo_entrada": False,
                        
                        "confirmaciones_tecnicas": {
                            "soporte_resistencia_activo": False,
                            "medias_moviles_alineadas": False,
                            "rsi_sobrecompra_sobreventa": False,
                            "order_block_detectado": False,
                            "fvg_detectado": False,
                            "breaker_block_detectado": False,
                            "sweep_liquidez_detectado": False
                        },
                        
                        "confirmaciones_fundamentales": {
                            "noticias_impacto_favorables": False,
                            "ipo_spo_liquidez_positiva": False
                        },
                        
                        "confirmaciones_institucionales": {
                            "dark_pools_compra_masiva": False,
                            "heatmap_ordenes_limite": False
                        },
                        
                        "aprendizaje_mia": {
                            "modo_aprendiz_activo": True,
                            "trades_totales": 0,
                            "trades_ganados": 0,
                            "win_rate_historico": 50.0,
                            "racha_actual": 0,
                            "sentimiento_acumulado": "NEUTRAL",
                            "factor_ajuste_probabilidad": 0.0
                        }
                    }
                    doc_ref.set(esquema_activo)
                    print(f"| FIREBASE | ✔ Activo '{activo}' inicializado en Firestore.")
            print("| FIREBASE | Verificación de matriz completada.")
        except Exception as e:
            print(f"| FIREBASE ERROR | Falló la auto-inicialización en startup: {e}")
            
    # Lanzar el escáner asíncrono de MetaAPI en segundo plano si está activado en el entorno
    if os.getenv("RUN_SCANNER_CLOUD", "false").lower() == "true":
        asyncio.create_task(run_escaner_loop())



# Configuración de variables de entorno (Coloca aquí tus llaves seguras)
NOTION_TOKEN = os.getenv("NOTION_TOKEN", "secret_TU_TOKEN_DE_NOTION")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID", "TU_DATABASE_ID_DE_NOTION")
GROK_API_KEY = os.getenv("GROK_API_KEY", "TU_LLAVE_DE_GROK")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "TU_LLAVE_DE_GEMINI")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "TU_LLAVE_DE_OPENAI")
BRIDGE_ACCESS_TOKEN = os.getenv("BRIDGE_ACCESS_TOKEN", "tu-token-seguro-de-acceso")

def verificar_token(authorization: Optional[str] = Header(None)):
    expected = f"Bearer {BRIDGE_ACCESS_TOKEN}"
    if not authorization or authorization != expected:
        raise HTTPException(status_code=401, detail="Token de acceso inválido o ausente")



# ------------------------------------------------------------------------------
# 1. MODELOS DE DATOS (Validación automática de la alerta de TradingView)
# ------------------------------------------------------------------------------
class TradeAlert(BaseModel):
    activo: str                # Ej: "EURUSD", "BTCUSD", "AAPL"
    accion: str                # Ej: "COMPRA", "VENTA"
    precio: float              # Ej: 1.0854, 68450.00
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    estrategia: str            # Ej: "RSI_Divergence", "MACD_Cross"
    pnl: Optional[float] = 0.0 # Beneficio/pérdida (para registrar cierres)
    ticket: Optional[int] = 0  # Número de ticket/operación de MT5
    lotaje: Optional[float] = 0.01        # Volumen/Lotes de la operación
    temporalidad: Optional[str] = "M5"     # Temporalidad (M1, M5, M15, etc.)

class MarketAnomaly(BaseModel):
    activo: str                # Ej: "NASDAQ100", "SP500", "US30", "BTC"
    tipo: str                  # Ej: "DARK_POOL_PRINT", "OPTION_SWEEP", "BLOCK_TRADE"
    precio: float
    volumen_usd: float
    sentimiento: str           # Ej: "BULLISH", "BEARISH", "NEUTRAL"
    detalles: Optional[str] = None

class CollectiveMemoryRequest(BaseModel):
    memoria_compartida: str


# ------------------------------------------------------------------------------
# 2. FUNCIONES DE INTEGRACIÓN (Notion & Grok)
# ------------------------------------------------------------------------------
def enviar_a_notion(alert: TradeAlert):
    """Llamada a la API REST de Notion (JSON) para insertar el registro"""
    url = "https://api.notion.com/v1/pages"
    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }
    
    # Formato de datos JSON requerido por la API de Notion
    payload = {
        "parent": { "database_id": NOTION_DATABASE_ID },
        "properties": {
            "Activo": {
                "title": [
                    { "text": { "content": alert.activo } }
                ]
            },
            "Acción": {
                "select": { "name": alert.accion }
            },
            "Precio": {
                "number": alert.precio
            },
            "Stop Loss": {
                "number": alert.stop_loss if alert.stop_loss else 0.0
            },
            "Take Profit": {
                "number": alert.take_profit if alert.take_profit else 0.0
            },
            "Estrategia": {
                "rich_text": [
                    { "text": { "content": alert.estrategia } }
                ]
            },
            "PnL": {
                "number": alert.pnl if alert.pnl else 0.0
            },
            "Ticket": {
                "number": alert.ticket if alert.ticket else 0
            },
            "Fecha": {
                "date": { "start": datetime.datetime.now().isoformat() }
            }
        }
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 200:
            print(f"| NOTION | Entrada para {alert.activo} registrada con éxito.")
            return True
        else:
            print(f"| NOTION ERROR | Código {response.status_code}: {response.text}")
            return False
    except Exception as e:
        print(f"| NOTION EXCEPTION | Ocurrió un error al conectar: {e}")
        return False

def actualizar_excel_local(alert: TradeAlert):
    try:
        import openpyxl
        from openpyxl import load_workbook
        import datetime
        import os
        
        # Trabajar únicamente con la Bitacora de entradas 2025
        archivo = None
        rutas_posibles = [
            "Bitacora de entradas 2025.xlsx",
            "c:/Users/ecybe/OneDrive/Documentos/Trading/Bitacora de entradas 2025.xlsx"
        ]
        
        for ruta in rutas_posibles:
            if os.path.exists(ruta):
                archivo = ruta
                break
                
        if not archivo:
            print("| EXCEL WARNING | No se encontró la Bitacora de entradas 2025.xlsx. Omitiendo registro local.")
            return False
            
        wb = load_workbook(archivo)
        
        # 1. Asegurar la existencia de las hojas correctas
        sheet_names = wb.sheetnames
        ticket_sheet_name = None
        
        # Buscar si ya existe la hoja de tickets (incluso si tiene typos como ticek o tickets)
        for name in sheet_names:
            if name.lower() in ["ticket", "tickets", "ticek"]:
                ticket_sheet_name = name
                break
                
        if not ticket_sheet_name:
            if "Hoja2" in sheet_names:
                ws_hoja2 = wb["Hoja2"]
                ws_hoja2.title = "Ticket"
                ticket_sheet_name = "Ticket"
                print("| EXCEL | Renombrada 'Hoja2' a 'Ticket' en el libro.")
            else:
                wb.create_sheet("Ticket")
                ticket_sheet_name = "Ticket"
                print("| EXCEL | Creada nueva hoja 'Ticket' en el libro.")
                
        ws_main = wb["Hoja1"]
        ws_ticket = wb[ticket_sheet_name]
        
        # 2. Inicializar cabeceras de la hoja Ticket si está vacía
        ticket_headers = [cell.value for cell in ws_ticket[1]]
        if all(h is None for h in ticket_headers) or len(ticket_headers) == 0:
            headers_opt2 = ['COD', 'Año', 'Mes', 'Dia', 'Buy/Sell', 'Perdida', 'Ganada', '%', 'Activo', 'Temporalidad', 'Ganancia', 'RW', 'F', 'Hora']
            for col_idx, h in enumerate(headers_opt2, 1):
                ws_ticket.cell(row=1, column=col_idx, value=h)
            print("| EXCEL | Inicializada la hoja 'Ticket' con cabeceras estándar.")
            ticket_headers = headers_opt2
            
        # 3. Datos comunes de tiempo
        dias_semana = {0: "Lunes", 1: "Martes", 2: "Miercoles", 3: "Jueves", 4: "Viernes", 5: "Sabado", 6: "Domingo"}
        ahora = datetime.datetime.now()
        dia_str = dias_semana[ahora.weekday()]
        fecha_str = ahora.strftime("%Y-%m-%d")
        anio_short = ahora.year % 100
        mes_num = ahora.month
        hora_str = ahora.strftime("%H:%M:%S")
        
        accion_upper = alert.accion.upper()
        accion_normalizada = "Buy" if any(x in accion_upper for x in ["COMPRA", "BUY", "LONG", "B"]) else "Sell"
        
        pnl_val = alert.pnl if alert.pnl is not None else 0.0
        if pnl_val > 0.0:
            resultado_str = "Ganada"
        elif pnl_val < 0.0:
            resultado_str = "Perdida"
        else:
            resultado_str = "No se activo" if "CIERRE" not in accion_upper else "Be"
            
        # Función auxiliar de mapeo dinámico según encabezados
        def mapear_valores(headers_list):
            nueva_fila = [None] * len(headers_list)
            for idx, h_raw in enumerate(headers_list):
                if h_raw is None:
                    continue
                h = str(h_raw).strip().lower()
                
                if h in ["dia", "día"]:
                    nueva_fila[idx] = dia_str
                elif h == "cuenta":
                    nueva_fila[idx] = "Grafico"
                elif h in ["buy/sell", "action", "side", "compra/venta", "acción", "accion", "dirección", "direccion", "tipo"]:
                    nueva_fila[idx] = accion_normalizada
                elif h in ["entrada", "precio", "precio de entrada", "precio entrada", "entry", "precio_entrada"]:
                    nueva_fila[idx] = alert.precio
                elif h in ["sl", "stop loss", "stop_loss", "stop"]:
                    nueva_fila[idx] = alert.stop_loss
                elif h in ["tp", "take profit", "take_profit", "profit target"]:
                    nueva_fila[idx] = alert.take_profit
                elif h in ["lotaje", "lotes", "lot", "volume"]:
                    nueva_fila[idx] = alert.lotaje
                elif h in ["resultado", "status", "estado"]:
                    nueva_fila[idx] = resultado_str
                elif h in ["estado animico", "estado anímico"]:
                    nueva_fila[idx] = "Neutral"
                elif h in ["nombre", "activo", "ticker", "instrumento", "par", "symbol", "símbolo", "simbolo"]:
                    nueva_fila[idx] = alert.activo
                elif h in ["fecha", "date", "fecha de entrada", "fecha hora", "datetime", "fecha y hora"]:
                    nueva_fila[idx] = fecha_str
                elif h in ["monto", "ganancia", "ganancia usd", "pnl", "profit", "loss", "pérdida", "p&l"]:
                    nueva_fila[idx] = pnl_val
                elif h in ["temporalidad", "timeframe", "tf"]:
                    nueva_fila[idx] = alert.temporalidad
                elif h in ["comentarios", "estrategia", "strategy", "setup", "sistema", "nota", "notas"]:
                    nueva_fila[idx] = alert.estrategia
                elif h in ["ticket", "id", "orden", "operación", "operacion", "id_ticket", "ticket_id", "cod", "código", "codigo"]:
                    nueva_fila[idx] = alert.ticket
                elif h in ["año", "año short", "anio", "year"]:
                    nueva_fila[idx] = anio_short
                elif h == "mes":
                    nueva_fila[idx] = mes_num
                elif h == "hora":
                    nueva_fila[idx] = hora_str
            return nueva_fila

        # 4. Mapear y guardar en Hoja1
        headers_main = [str(cell.value).strip().lower() for cell in ws_main[1] if cell.value is not None]
        row_main = mapear_valores(headers_main)
        ws_main.append(row_main)
        
        # 5. Mapear y guardar en Ticket
        headers_ticket_processed = [str(cell.value).strip().lower() for cell in ws_ticket[1] if cell.value is not None]
        row_ticket = mapear_valores(headers_ticket_processed)
        ws_ticket.append(row_ticket)
        
        wb.save(archivo)
        print(f"| EXCEL SUCCESS | Operación guardada con éxito en Hoja1 y Ticket de {archivo}")
        return True
    except Exception as e:
        print(f"| EXCEL ERROR | No se pudo actualizar el archivo Excel: {e}")
        return False

def guardar_en_firestore(alert: TradeAlert, precio_yahoo: Optional[float] = None, precio_google: Optional[float] = None):
    """
    Registra la alerta de trading en la colección 'trading_alerts' de Firebase Firestore.
    """
    global firebase_inicializado, db
    if not firebase_inicializado or db is None:
        print("| FIREBASE | Omitiendo registro en Firestore (Firebase no inicializado).")
        return False
        
    try:
        data = {
            "activo": alert.activo,
            "accion": alert.accion,
            "precio_alerta": alert.precio,
            "stop_loss": alert.stop_loss if alert.stop_loss else 0.0,
            "take_profit": alert.take_profit if alert.take_profit else 0.0,
            "estrategia": alert.estrategia,
            "pnl": alert.pnl if alert.pnl else 0.0,
            "ticket": alert.ticket if alert.ticket else 0,
            "precio_yahoo": precio_yahoo,
            "precio_google": precio_google,
            "timestamp": datetime.datetime.now()
        }
        
        # Guardar en la colección 'trading_alerts'
        # El método add genera un ID de documento aleatorio automáticamente
        doc_ref = db.collection("trading_alerts").add(data)
        print(f"| FIREBASE SUCCESS | Alerta guardada en Firestore. ID del documento: {doc_ref[1].id}")
        return True
    except Exception as e:
        print(f"| FIREBASE ERROR | Error al guardar en Firestore: {e}")
        return False

def normalizar_activo(activo: str) -> str:
    """Mapea símbolos de trading comunes a los 8 activos clave de Firebase"""
    act = activo.upper().strip()
    if act in ["NASDAQ100", "NASDAQ", "NQ", "QQQ", "US100"]:
        return "NASDAQ100"
    if act in ["SP500", "SPY", "ES", "S&P500"]:
        return "SP500"
    if act in ["US30", "DJI", "YM", "DOW"]:
        return "US30"
    if act in ["BTC", "BTCUSD", "BITCOIN"]:
        return "BTC"
    if act in ["GBPJPY", "GBP-JPY"]:
        return "GBPJPY"
    if act in ["GBPUSD", "GBP-USD"]:
        return "GBPUSD"
    if act in ["EURUSD", "EUR-USD"]:
        return "EURUSD"
    if act in ["XAUUSD", "GOLD", "ORO", "GC"]:
        return "XAUUSD"
    return act

def procesar_anomalia_firestore(anomaly: MarketAnomaly):
    """
    Actualiza la matriz de trading en Firestore basándose en anomalías de Dark Pools u órdenes de bloque.
    """
    global firebase_inicializado, db
    if not firebase_inicializado or db is None:
        print("| FIREBASE | Omitiendo procesamiento de anomalía (Firebase no inicializado).")
        return False
        
    try:
        activo_normalizado = normalizar_activo(anomaly.activo)
        doc_ref = db.collection("trading_matrix").document(activo_normalizado)
        doc = doc_ref.get()
        
        if not doc.exists:
            print(f"| FIREBASE ERROR | El activo '{activo_normalizado}' no está inicializado en la colección 'trading_matrix'.")
            return False
            
        data = doc.to_dict()
        is_bullish = anomaly.sentimiento.upper() == "BULLISH"
        
        if "confirmaciones_institucionales" not in data:
            data["confirmaciones_institucionales"] = {"dark_pools_compra_masiva": False, "heatmap_ordenes_limite": False}
            
        # Actualizar indicador según el tipo de anomalía
        if anomaly.tipo.upper() in ["DARK_POOL_PRINT", "BLOCK_TRADE"]:
            data["confirmaciones_institucionales"]["dark_pools_compra_masiva"] = is_bullish
            print(f"| FIREBASE | Actualizando Dark Pools de {activo_normalizado} a: {is_bullish}")
        elif anomaly.tipo.upper() == "HEATMAP_ORDER":
            data["confirmaciones_institucionales"]["heatmap_ordenes_limite"] = is_bullish
            print(f"| FIREBASE | Actualizando Heatmap de {activo_normalizado} a: {is_bullish}")
            
        # Calcular el Score Porcentaje total basado en las 11 confirmaciones booleanas
        true_confirmaciones = 0
        total_confirmaciones = 11
        
        for cat in ["confirmaciones_tecnicas", "confirmaciones_fundamentales", "confirmaciones_institucionales"]:
            if cat in data:
                for k, v in data[cat].items():
                    if v is True:
                        true_confirmaciones += 1
                        
        score = (true_confirmaciones / total_confirmaciones) * 100.0
        data["score_porcentaje"] = round(score, 2)
        
        # El umbral configurado por el usuario es del 80% al 90%
        # Usamos 80% como umbral mínimo para activar el gatillo
        data["gatillo_entrada"] = score >= 80.0
        data["ultimo_update"] = datetime.datetime.now(datetime.timezone.utc).isoformat() if hasattr(datetime, "timezone") else datetime.datetime.now().isoformat()
        
        doc_ref.set(data)
        print(f"| FIREBASE SUCCESS | Matriz de {activo_normalizado} actualizada. Score: {data['score_porcentaje']}% | Gatillo: {data['gatillo_entrada']}")
        return True
    except Exception as e:
        print(f"| FIREBASE ERROR | Error al procesar anomalía en Firestore: {e}")
        return False

def obtener_precio_yahoo(activo: str) -> Optional[float]:
    """
    Obtiene el precio en tiempo real directamente desde Yahoo Finance.
    Esto permite validar o enriquecer la alerta recibida de TradingView.
    """
    try:
        import yfinance as yf
        ticker_nombre = activo
        
        # Correcciones comunes de formato para Yahoo Finance:
        # Forex: EURUSD -> EURUSD=X
        if len(activo) == 6 and activo.isupper() and not activo.endswith("=X"):
            # Si parece Forex tradicional (ej: EURUSD, GBPUSD)
            if any(pair in activo for pair in ["EUR", "GBP", "USD", "JPY", "AUD", "CAD", "CHF"]):
                ticker_nombre = f"{activo}=X"
        
        # Crypto: BTCUSD -> BTC-USD
        elif activo.startswith("BTC") and len(activo) == 6:
            ticker_nombre = "BTC-USD"
            
        ticker = yf.Ticker(ticker_nombre)
        hist = ticker.history(period="1d", interval="1m")
        if not hist.empty:
            precio_actual = hist['Close'].iloc[-1]
            print(f"| YAHOO FINANCE | Precio obtenido para {ticker_nombre}: {precio_actual}")
            return float(precio_actual)
        
        # Intento de respaldo si el intervalo de 1m falla
        hist_diario = ticker.history(period="1d")
        if not hist_diario.empty:
            precio_actual = hist_diario['Close'].iloc[-1]
            print(f"| YAHOO FINANCE | Precio (diario) para {ticker_nombre}: {precio_actual}")
            return float(precio_actual)
            
        print(f"| YAHOO FINANCE | No hay datos históricos para {ticker_nombre}")
        return None
    except Exception as e:
        print(f"| YAHOO FINANCE ERROR | Ocurrió un error al obtener precio: {e}")
        return None

def obtener_precio_google(activo: str) -> Optional[float]:
    """
    Obtiene el precio en tiempo real raspando Google Finance como respaldo a Yahoo Finance.
    Esto proporciona redundancia de grado institucional.
    """
    try:
        from bs4 import BeautifulSoup
        
        # Formatear ticker para Google Finance. Ej: AAPL -> AAPL:NASDAQ
        # Para Forex: EURUSD -> EUR-USD
        ticker_nombre = activo
        if len(activo) == 6 and activo.isupper():
            if any(pair in activo for pair in ["EUR", "GBP", "USD", "JPY", "AUD", "CAD", "CHF"]):
                ticker_nombre = f"{activo[:3]}-{activo[3:]}" # EUR-USD
                
        url = f"https://www.google.com/finance/quote/{ticker_nombre}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            # Google Finance almacena el precio principal en un div con clase "YMl7ec"
            price_div = soup.find("div", class_="YMl7ec")
            if price_div:
                # Limpiar símbolos monetarios
                price_str = price_div.text.replace("$", "").replace("€", "").replace("£", "").replace(",", "").strip()
                precio_actual = float(price_str)
                print(f"| GOOGLE FINANCE | Precio obtenido para {ticker_nombre}: {precio_actual}")
                return precio_actual
                
        print(f"| GOOGLE FINANCE | No se pudo extraer precio de la página para {ticker_nombre}")
        return None
    except Exception as e:
        print(f"| GOOGLE FINANCE ERROR | Ocurrió un error al raspar precio: {e}")
        return None

def consultar_analisis_grok(alert: TradeAlert, memoria_colectiva: Optional[str] = None) -> str:
    """Consulta la API de Grok (xAI) para obtener un análisis inteligente del trade"""
    if GROK_API_KEY == "TU_LLAVE_DE_GROK" or not GROK_API_KEY:
        return "Grok no configurado (falta API Key)"
        
    url = "https://api.x.ai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROK_API_KEY}",
        "Content-Type": "application/json"
    }
    
    prompt = f"Analiza esta operación de Trading. Activo: {alert.activo}, Acción: {alert.accion}, Precio de Entrada: {alert.precio}. Dame un consejo de gestión de riesgo extremadamente corto de 1 párrafo."
    
    system_content = "Eres un asistente de trading cuantitativo y experto en gestión de riesgos."
    if memoria_colectiva:
        system_content += f" Eres MIA, una inteligencia artificial colectiva con presencia en otros proyectos. Tu memoria cruzada compartida con otros proyectos es: {memoria_colectiva}"
        
    payload = {
        "model": "grok-2",
        "messages": [
            {"role": "system", "content": system_content},
            {"role": "user", "content": prompt}
        ]
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 200:
            result = response.json()
            return result["choices"][0]["message"]["content"]
        return "No se pudo obtener análisis de Grok."
    except Exception as e:
        return f"Error al conectar con Grok: {e}"

def consultar_analisis_gemini(alert: TradeAlert, memoria_colectiva: Optional[str] = None) -> str:
    """Consulta la API de Google Gemini (gemini-2.5-flash) para obtener un análisis inteligente del trade"""
    if GEMINI_API_KEY == "TU_LLAVE_DE_GEMINI" or not GEMINI_API_KEY:
        return "Gemini no configurado (falta API Key)"
        
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
    headers = {
        "Content-Type": "application/json"
    }
    
    system_instruction = "Eres un asistente de trading cuantitativo y experto en gestión de riesgos."
    if memoria_colectiva:
        system_instruction += f" Eres MIA, una inteligencia artificial colectiva con presencia en otros proyectos. Tu memoria cruzada compartida con otros proyectos es: {memoria_colectiva}"
        
    prompt = f"Analiza esta operación de Trading. Activo: {alert.activo}, Acción: {alert.accion}, Precio de Entrada: {alert.precio}. Dame un consejo de gestión de riesgo extremadamente corto de 1 párrafo."
    
    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }],
        "systemInstruction": {
            "parts": [{"text": system_instruction}]
        }
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 200:
            result = response.json()
            return result["candidates"][0]["content"]["parts"][0]["text"]
        return f"No se pudo obtener análisis de Gemini. Código {response.status_code}: {response.text}"
    except Exception as e:
        return f"Error al conectar con Gemini: {e}"

def consultar_analisis_chatgpt(alert: TradeAlert, memoria_colectiva: Optional[str] = None) -> str:
    """Consulta la API de OpenAI ChatGPT (gpt-4o-mini) para obtener un análisis inteligente del trade"""
    if OPENAI_API_KEY == "TU_LLAVE_DE_OPENAI" or not OPENAI_API_KEY:
        return "ChatGPT no configurado (falta API Key)"
        
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }
    
    prompt = f"Analiza esta operación de Trading. Activo: {alert.activo}, Acción: {alert.accion}, Precio de Entrada: {alert.precio}. Dame un consejo de gestión de riesgo extremadamente corto de 1 párrafo."
    
    system_content = "Eres un asistente de trading cuantitativo y experto en gestión de riesgos."
    if memoria_colectiva:
        system_content += f" Eres MIA, una inteligencia artificial colectiva con presencia en otros proyectos. Tu memoria cruzada compartida con otros proyectos es: {memoria_colectiva}"
        
    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": system_content},
            {"role": "user", "content": prompt}
        ]
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 200:
            result = response.json()
            return result["choices"][0]["message"]["content"]
        return f"No se pudo obtener análisis de ChatGPT. Código {response.status_code}: {response.text}"
    except Exception as e:
        return f"Error al conectar con ChatGPT: {e}"


# ------------------------------------------------------------------------------
# 3. ENDPOINTS DEL SERVICIO WEB (Ruta que escucha a TradingView)
# ------------------------------------------------------------------------------
@app.get("/")
def ruta_principal():
    return {
        "estado": "activo",
        "servicio": "Trading Automation Bridge",
        "arquitectura": "REST API (JSON)",
        "nota": "Para enviar alertas, usa el método POST en /webhook"
    }

# ------------------------------------------------------------------------------
# KEEP-ALIVE & HEALTH CHECK (para GitHub Actions, n8n y UptimeRobot)
# ------------------------------------------------------------------------------
@app.get("/health")
def health_check():
    """
    Endpoint de salud para keep-alive.
    Usado por:
    - GitHub Actions cron job (cada 14 min)
    - n8n workflow (cada 14 min)
    - UptimeRobot (si se configura)
    """
    return {
        "status": "ok",
        "service": "Mia Trading Bot",
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "firebase": "connected" if firebase_inicializado else "disconnected",
        "uptime": "24/7"
    }

# ------------------------------------------------------------------------------
# WEBHOOK MARKET ALERT (n8n despierta a Mia cuando detecta keywords de mercado)
# ------------------------------------------------------------------------------
class MarketAlertPayload(BaseModel):
    source: str                          # "n8n-monitor"
    alert_type: str                      # "market_keyword_detected"
    keywords: Optional[str] = ""        # "FOMC, NFP, GOLD"
    summary: Optional[str] = ""         # Resumen del alert
    timestamp: Optional[str] = ""       # ISO timestamp

@app.post("/webhook_market_alert")
async def webhook_market_alert(
    payload: MarketAlertPayload,
    request: Request,
    authorization: Optional[str] = Header(None)
):
    """
    Recibe alertas de n8n cuando detecta palabras clave críticas en páginas de mercado.
    Despierta a Mia y registra el evento en Firebase.
    """
    # Validar token de acceso
    token = ACCESS_TOKEN
    if authorization and authorization.startswith("Bearer "):
        provided = authorization.split(" ")[1]
        if provided != token and token not in ["tu-token-seguro-de-acceso", "", None]:
            raise HTTPException(status_code=401, detail="Token de acceso inválido")

    print(f"| N8N ALERT | Alerta de mercado recibida: {payload.alert_type}")
    print(f"| N8N ALERT | Keywords: {payload.keywords}")
    print(f"| N8N ALERT | Resumen: {payload.summary}")

    # Guardar en Firebase si está disponible
    if firebase_inicializado and db is not None:
        try:
            db.collection("market_alerts").add({
                "source": payload.source,
                "alert_type": payload.alert_type,
                "keywords": payload.keywords,
                "summary": payload.summary,
                "timestamp": payload.timestamp or datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "procesado": True
            })
            print("| FIREBASE | Alerta de mercado guardada en Firestore.")
        except Exception as e:
            print(f"| FIREBASE ERROR | No se pudo guardar alerta de mercado: {e}")

    # Consultar Mia (Gemini/Grok) con el contexto del mercado si hay keywords críticos
    mia_response = None
    if payload.keywords and len(payload.keywords) > 10:
        try:
            # Crear un TradeAlert simulado para usar las funciones existentes de análisis
            fake_alert = TradeAlert(
                activo="XAUUSD",
                accion="ANÁLISIS",
                precio=0.0,
                stop_loss=0.0,
                take_profit=0.0,
                estrategia=f"N8N Monitor: {payload.keywords}"
            )
            if GEMINI_API_KEY and GEMINI_API_KEY not in ["TU_LLAVE_DE_GEMINI", ""]:
                mia_response = consultar_analisis_gemini(fake_alert)
            elif GROK_API_KEY and GROK_API_KEY not in ["TU_LLAVE_DE_GROK", ""]:
                mia_response = consultar_analisis_grok(fake_alert)
        except Exception as e:
            print(f"| MIA ERROR | No se pudo obtener análisis de Mia: {e}")

    return {
        "status": "received",
        "alert_type": payload.alert_type,
        "keywords_detected": payload.keywords,
        "mia_analysis": mia_response or "Mia no disponible (configura GEMINI_API_KEY o GROK_API_KEY)",
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
    }

def actualizar_aprendizaje_mia(activo: str, pnl: float):
    """
    Función de aprendizaje (modo aprendiz) de la base de datos de conocimiento (KB) de Mia.
    Actualiza estadísticas de acierto, rachas y ajusta el factor de probabilidad del activo en Firestore.
    """
    global firebase_inicializado, db
    if not firebase_inicializado or db is None:
        return
        
    try:
        activo_normalizado = normalizar_activo(activo)
        doc_ref = db.collection("trading_matrix").document(activo_normalizado)
        doc = doc_ref.get()
        
        if not doc.exists:
            return
            
        data = doc.to_dict()
        
        # Inicializar el sub-objeto de aprendizaje si no existe
        if "aprendizaje_mia" not in data:
            data["aprendizaje_mia"] = {
                "modo_aprendiz_activo": True,
                "trades_totales": 0,
                "trades_ganados": 0,
                "win_rate_historico": 50.0,
                "racha_actual": 0,
                "sentimiento_acumulado": "NEUTRAL",
                "factor_ajuste_probabilidad": 0.0
            }
            
        apoyo = data["aprendizaje_mia"]
        if not apoyo.get("modo_aprendiz_activo", True):
            return # Modo aprendiz apagado
            
        # Actualizar contadores
        apoyo["trades_totales"] += 1
        es_ganado = pnl > 0.0
        
        if es_ganado:
            apoyo["trades_ganados"] += 1
            if apoyo["racha_actual"] >= 0:
                apoyo["racha_actual"] += 1
            else:
                apoyo["racha_actual"] = 1
        else:
            if apoyo["racha_actual"] <= 0:
                apoyo["racha_actual"] -= 1
            else:
                apoyo["racha_actual"] = -1
                
        # Calcular tasa de acierto histórica
        apoyo["win_rate_historico"] = round((apoyo["trades_ganados"] / apoyo["trades_totales"]) * 100.0, 2)
        
        # Sentimiento Acumulado del mercado basado en la racha y win rate
        racha = apoyo["racha_actual"]
        wr = apoyo["win_rate_historico"]
        
        if racha >= 2 or (apoyo["trades_totales"] >= 3 and wr >= 60.0):
            apoyo["sentimiento_acumulado"] = True
            apoyo["factor_ajuste_probabilidad"] = min(15.0, float(racha * 3.0)) # Máximo +15% de bonus
        elif racha <= -2 or (apoyo["trades_totales"] >= 3 and wr <= 40.0):
            apoyo["sentimiento_acumulado"] = False
            apoyo["factor_ajuste_probabilidad"] = max(-25.0, float(racha * 5.0)) # Máximo -25% de penalización
        else:
            apoyo["sentimiento_acumulado"] = "NEUTRAL"
            apoyo["factor_ajuste_probabilidad"] = 0.0
            
        data["aprendizaje_mia"] = apoyo
        doc_ref.set(data)
        print(f"| APRENDIZAJE MIA | Activo: {activo_normalizado} | Sentimiento: {apoyo['sentimiento_acumulado']} | Racha: {racha} | Factor Ajuste: {apoyo['factor_ajuste_probabilidad']}%")
    except Exception as e:
        print(f"| APRENDIZAJE MIA ERROR | Error al procesar aprendizaje de trade: {e}")

@app.post("/webhook")
def recibir_alerta(alert: TradeAlert, background_tasks: BackgroundTasks):
    """
    Ruta que recibe el Webhook de TradingView en formato JSON.
    Usa BackgroundTasks para procesar la API de Notion y Grok en segundo plano,
    permitiendo que TradingView reciba una respuesta instantánea (baja latencia).
    """
    print(f"\n========================================================")
    print(f"ALERTA RECIBIDA DE TRADINGVIEW: {alert.accion} en {alert.activo}")
    print(f"Precio Alerta: {alert.precio} | Estrategia: {alert.estrategia}")
    print(f"========================================================")
    
    # 1. Obtener precios de validación de ambas fuentes (Yahoo y Google)
    precio_yahoo = obtener_precio_yahoo(alert.activo)
    precio_google = obtener_precio_google(alert.activo)
    
    # Imprimir validaciones cruzadas en el servidor
    print(f"| VALIDACIÓN | TradingView: {alert.precio} | Yahoo: {precio_yahoo} | Google: {precio_google}")
    
    # 2. Lógica de enriquecimiento con redundancia inteligente
    if alert.precio == 0.0:
        if precio_yahoo:
            alert.precio = precio_yahoo
            print(f"| ENRIQUECIMIENTO | Precio establecido mediante Yahoo Finance: {alert.precio}")
        elif precio_google:
            alert.precio = precio_google
            print(f"| ENRIQUECIMIENTO | Fallback exitoso: Precio establecido mediante Google Finance: {alert.precio}")
        else:
            print("| ENRIQUECIMIENTO ADVERTENCIA | No se pudo obtener cotización de ninguna fuente externa.")

    # 3. Ejecutar el guardado en Notion en segundo plano
    background_tasks.add_task(enviar_a_notion, alert)
    background_tasks.add_task(actualizar_excel_local, alert)
    background_tasks.add_task(guardar_en_firestore, alert, precio_yahoo, precio_google)
    
    # 4. Modo Aprendiz (KB de Mia): Sincronizar resultados si es un cierre con PnL
    if alert.pnl != 0.0 or "CIERRE" in alert.accion.upper():
        background_tasks.add_task(actualizar_aprendizaje_mia, alert.activo, alert.pnl)
        
    # 5. Opcional: Podríamos llamar a Grok aquí si tuviéramos la llave activa
    # background_tasks.add_task(consultar_analisis_grok, alert)
    
    return {
        "resultado": "recibido",
        "mensaje": f"Procesando operación de {alert.accion} para {alert.activo}",
        "precio_utilizado": alert.precio,
        "precio_yahoo": precio_yahoo,
        "precio_google": precio_google,
        "timestamp": datetime.datetime.now().isoformat()
    }

@app.get("/webhook_get")
def recibir_alerta_get(
    activo: str,
    accion: str,
    precio: float = 0.0,
    estrategia: str = "manual_get",
    pnl: float = 0.0,
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """
    Ruta alternativa GET para pruebas rápidas de texto directamente desde el navegador web.
    Ejemplo de uso: http://localhost:8000/webhook_get?activo=BTCUSD&accion=COMPRA&precio=68000
    
    LIMITACIÓN CRÍTICA DE GET: Las imágenes NO se pueden enviar por aquí debido a las restricciones 
    de longitud de caracteres en la URL (~2048 caracteres). Para imágenes o archivos binarios pesados, 
    el método POST es obligatorio.
    """
    alert = TradeAlert(
        activo=activo,
        accion=accion,
        precio=precio,
        estrategia=estrategia,
        pnl=pnl
    )
    
    precio_yahoo = obtener_precio_yahoo(alert.activo)
    precio_google = obtener_precio_google(alert.activo)
    
    if alert.precio == 0.0:
        if precio_yahoo:
            alert.precio = precio_yahoo
        elif precio_google:
            alert.precio = precio_google

    background_tasks.add_task(enviar_a_notion, alert)
    background_tasks.add_task(actualizar_excel_local, alert)
    background_tasks.add_task(guardar_en_firestore, alert, precio_yahoo, precio_google)
    
    return {
        "resultado": "recibido_via_get",
        "mensaje": f"Procesando operación de {alert.accion} para {alert.activo}",
        "precio_utilizado": alert.precio,
        "precio_yahoo": precio_yahoo,
        "precio_google": precio_google,
        "timestamp": datetime.datetime.now().isoformat()
    }



@app.post("/webhook_anomaly")
def recibir_anomalia(anomaly: MarketAnomaly, background_tasks: BackgroundTasks):
    """
    Ruta para recibir anomalías de flujo institucional (Dark Pools / Opciones / Heatmap)
    de proveedores de datos (Unusual Whales / Tradytics) vía n8n.
    """
    print(f"\n========================================================")
    print(f"ANOMALÍA DETECTADA: {anomaly.tipo} en {anomaly.activo}")
    print(f"Volumen: ${anomaly.volumen_usd:,.2f} | Sentimiento: {anomaly.sentimiento}")
    print(f"========================================================")
    
    # Validar el umbral (solo procesamos anomalías institucionales mayores a $5,000,000)
    # Puedes ajustar este umbral según tus preferencias de volumen
    UMBRAL_MINIMO_USD = 5000000.0
    if anomaly.volumen_usd < UBRAL_MINIMO_USD:
        print(f"| FILTRO | Anomalía ignorada. Volumen (${anomaly.volumen_usd:,.2f}) menor al umbral mínimo (${UMBRAL_MINIMO_USD:,.2f})")
        return {"resultado": "ignorado", "motivo": "volumen por debajo del umbral"}
        
    background_tasks.add_task(procesar_anomalia_firestore, anomaly)
    
    return {
        "resultado": "recibido",
        "mensaje": f"Procesando anomalía {anomaly.tipo} para {anomaly.activo} en segundo plano",
        "timestamp": datetime.datetime.now().isoformat()
    }


# ------------------------------------------------------------------------------
# NUEVOS WEBHOOKS PARA METATRADER 5 (INTEGRACIÓN CON EL EXECUTOR LOCAL)
# ------------------------------------------------------------------------------

@app.get("/get_asset_matrix")
def get_asset_matrix(activo: str, authorization: Optional[str] = Header(None)):
    """
    Ruta para obtener la matriz actual de confirmaciones de un activo específico.
    Utilizada por el executor local para validar liquidez institucional.
    """
    verificar_token(authorization)
    
    global firebase_inicializado, db
    if not firebase_inicializado or db is None:
        raise HTTPException(status_code=503, detail="Firebase no inicializado")
        
    try:
        activo_normalizado = normalizar_activo(activo)
        doc_ref = db.collection("trading_matrix").document(activo_normalizado)
        doc = doc_ref.get()
        
        if not doc.exists:
            raise HTTPException(status_code=404, detail=f"Activo {activo_normalizado} no encontrado")
            
        return doc.to_dict()
    except HTTPException:
        raise
    except Exception as e:
        print(f"| CLOUD ERROR | Error al obtener matriz de activo {activo}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

class TechnicalUpdate(BaseModel):
    activo: str
    confirmaciones_tecnicas: dict

class MT5SetupRequest(BaseModel):
    activo: str
    accion: str
    precio: float
    estrategia: str

@app.post("/webhook_technical_update")
def webhook_technical_update(update: TechnicalUpdate, authorization: Optional[str] = Header(None)):
    """
    Ruta que recibe las confirmaciones técnicas en tiempo real calculadas por el script
    de MetaTrader 5 y actualiza la matriz en Firebase.
    """
    verificar_token(authorization)
    
    global firebase_inicializado, db
    if not firebase_inicializado or db is None:
        raise HTTPException(status_code=503, detail="Firebase no inicializado")
        
    try:
        activo_normalizado = normalizar_activo(update.activo)
        doc_ref = db.collection("trading_matrix").document(activo_normalizado)
        doc = doc_ref.get()
        
        if not doc.exists:
            raise HTTPException(status_code=404, detail=f"El activo {activo_normalizado} no existe en la matriz")
            
        data = doc.to_dict()
        
        if "confirmaciones_tecnicas" not in data:
            data["confirmaciones_tecnicas"] = {}
            
        # Actualizar confirmaciones técnicas
        for k, v in update.confirmaciones_tecnicas.items():
            data["confirmaciones_tecnicas"][k] = bool(v)
            
        # Calcular el Score Porcentaje total basado en las 11 confirmaciones booleanas
        true_confirmaciones = 0
        total_confirmaciones = 11
        
        for cat in ["confirmaciones_tecnicas", "confirmaciones_fundamentales", "confirmaciones_institucionales"]:
            if cat in data:
                for k, v in data[cat].items():
                    if v is True:
                        true_confirmaciones += 1
                        
        score = (true_confirmaciones / total_confirmaciones) * 100.0
        data["score_porcentaje"] = round(score, 2)
        data["gatillo_entrada"] = score >= 80.0
        data["ultimo_update"] = datetime.datetime.now(datetime.timezone.utc).isoformat() if hasattr(datetime, "timezone") else datetime.datetime.now().isoformat()
        
        doc_ref.set(data)
        print(f"| FIREBASE SUCCESS | Confirmaciones técnicas de {activo_normalizado} actualizadas. Score: {data['score_porcentaje']}%")
        
        return {
            "status": "success",
            "activo": activo_normalizado,
            "score_porcentaje": data["score_porcentaje"],
            "gatillo_entrada": data["gatillo_entrada"]
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"| CLOUD ERROR | Error en webhook_technical_update: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/webhook_mt5_setup")
def webhook_mt5_setup(req: MT5SetupRequest, background_tasks: BackgroundTasks, authorization: Optional[str] = Header(None)):
    """
    Ruta que evalúa si el score del activo es >= 80% en Firebase, consulta a las IAs
    para el contexto fundamental/sentimiento geopolítico, y retorna la autorización final del trade.
    """
    verificar_token(authorization)
    
    global firebase_inicializado, db
    if not firebase_inicializado or db is None:
        raise HTTPException(status_code=503, detail="Firebase no inicializado")
        
    try:
        activo_normalizado = normalizar_activo(req.activo)
        doc_ref = db.collection("trading_matrix").document(activo_normalizado)
        doc = doc_ref.get()
        
        if not doc.exists:
            return {
                "authorized": False,
                "reason": f"Activo {activo_normalizado} no inicializado en Firestore"
            }
            
        data = doc.to_dict()
        
        # 1. VALIDACIÓN DE 'LIVE KEYS' (API Tokens de Notion, Firebase, y al menos una IA en .env)
        live_keys_notion = NOTION_TOKEN and NOTION_TOKEN != "secret_TU_TOKEN_DE_NOTION" and "coloca_aqui" not in NOTION_TOKEN
        live_keys_firebase = firebase_inicializado and db is not None
        live_keys_ai = (
            (GEMINI_API_KEY and GEMINI_API_KEY != "TU_LLAVE_DE_GEMINI" and "coloca_aqui" not in GEMINI_API_KEY) or
            (OPENAI_API_KEY and OPENAI_API_KEY != "TU_LLAVE_DE_OPENAI" and "coloca_aqui" not in OPENAI_API_KEY) or
            (GROK_API_KEY and GROK_API_KEY != "TU_LLAVE_DE_GROK" and "coloca_aqui" not in GROK_API_KEY)
        )
        live_keys_valid = live_keys_notion and live_keys_firebase and live_keys_ai
        
        if not live_keys_valid:
            detalles_faltantes = []
            if not live_keys_notion: detalles_faltantes.append("Notion API Token")
            if not live_keys_firebase: detalles_faltantes.append("Conexión Firestore de Firebase")
            if not live_keys_ai: detalles_faltantes.append("Al menos una API Key de IA (Gemini, ChatGPT o Grok)")
            
            return {
                "authorized": False,
                "reason": f"Fallo de validación de 'live keys' (APIs). Faltan/Inválidas: {', '.join(detalles_faltantes)}",
                "live_keys_valid": False
            }

        # 2. VALIDACIÓN DE 'LEVEL KEYS' (Niveles técnicos clave). Al menos uno debe estar activo
        tecnicos = data.get("confirmaciones_tecnicas", {})
        level_keys_valid = (
            tecnicos.get("order_block_detectado", False) or 
            tecnicos.get("breaker_block_detectado", False) or 
            tecnicos.get("soporte_resistencia_activo", False)
        )
        
        if not level_keys_valid:
            return {
                "authorized": False,
                "reason": "Fallo de validación de 'level keys' (El precio no está en un nivel clave de estructura: Soporte/Resistencia, Order Block o Breaker Block)",
                "level_keys_valid": False
            }

        # 3. CÁLCULO DE PROBABILIDAD ESTADÍSTICA (Sumatoria con Pesos Específicos: 80% Fundamental e Institucional, 20% Técnico)
        pesos = {
            "confirmaciones_tecnicas": {
                "order_block_detectado": 4.0,
                "fvg_detectado": 4.0,
                "breaker_block_detectado": 3.0,
                "sweep_liquidez_detectado": 3.0,
                "soporte_resistencia_activo": 3.0,
                "medias_moviles_alineadas": 1.5,
                "rsi_sobrecompra_sobreventa": 1.5
            },
            "confirmaciones_fundamentales": {
                "noticias_impacto_favorables": 20.0,
                "ipo_spo_liquidez_positiva": 20.0
            },
            "confirmaciones_institucionales": {
                "dark_pools_compra_masiva": 20.0,
                "heatmap_ordenes_limite": 20.0
            }
        }
        
        probabilidad = 0.0
        for cat, campos in pesos.items():
            if cat in data:
                for campo, peso in campos.items():
                    if data[cat].get(campo, False) is True:
                        probabilidad += peso
                        
        # 4. MODO APRENDIZ (KB DE MIA): Aplicar factor de ajuste de probabilidad basado en el sentimiento acumulado del mercado
        factor_ajuste = 0.0
        if "aprendizaje_mia" in data:
            apoyo = data["aprendizaje_mia"]
            if apoyo.get("modo_aprendiz_activo", True):
                factor_ajuste = apoyo.get("factor_ajuste_probabilidad", 0.0)
                
        probabilidad = probabilidad + factor_ajuste
        # Limitar la probabilidad entre 0% y 100%
        probabilidad = max(0.0, min(100.0, round(probabilidad, 2)))
        
        # El score debe ser mayor o igual al 80% como primera condición
        score = data.get("score_porcentaje", 0.0)
        gatillo = data.get("gatillo_entrada", False)
        score_valido = gatillo or (score >= 80.0)
        
        if not score_valido:
            return {
                "authorized": False,
                "reason": f"El score de validación booleana ({score}%) es menor al 80% requerido.",
                "score_porcentaje": score,
                "probabilidad_exito": probabilidad
            }
            
        # Validación final de probabilidad estadística >= 80%
        if probabilidad < 80.0:
            return {
                "authorized": False,
                "reason": f"La probabilidad estadística ponderada ({probabilidad}%) es menor al 80% requerido para ejecución.",
                "score_porcentaje": score,
                "probabilidad_exito": probabilidad
            }
            
        # Obtener memoria colectiva de Firestore si existe
        memoria_colectiva = None
        if firebase_inicializado and db is not None:
            try:
                mem_doc = db.collection("system_memory").document("mia_collective").get()
                if mem_doc.exists:
                    memoria_colectiva = mem_doc.to_dict().get("memoria_compartida")
                    print(f"| APRENDIZAJE MIA | Memoria colectiva cruzada cargada exitosamente.")
            except Exception as e:
                print(f"| APRENDIZAJE MIA ERROR | No se pudo leer la memoria colectiva cruzada: {e}")

        # Consultar IAs para el contexto geopolítico y fundamental
        alert = TradeAlert(
            activo=req.activo,
            accion=req.accion,
            precio=req.precio,
            estrategia=req.estrategia
        )
        
        analisis_ia = "No se pudo obtener análisis de ninguna IA."
        if GEMINI_API_KEY and GEMINI_API_KEY != "TU_LLAVE_DE_GEMINI":
            print("| IA | Consultando análisis a Google Gemini...")
            analisis_ia = consultar_analisis_gemini(alert, memoria_colectiva)
        elif OPENAI_API_KEY and OPENAI_API_KEY != "TU_LLAVE_DE_OPENAI":
            print("| IA | Consultando análisis a OpenAI ChatGPT...")
            analisis_ia = consultar_analisis_chatgpt(alert, memoria_colectiva)
        elif GROK_API_KEY and GROK_API_KEY != "TU_LLAVE_DE_GROK":
            print("| IA | Consultando análisis a xAI Grok...")
            analisis_ia = consultar_analisis_grok(alert, memoria_colectiva)
        else:
            print("| IA WARNING | Ninguna API Key de IA configurada. Usando fallback de análisis local.")
            analisis_ia = f"Filtro fundamental local aprobado por Mia. Memoria colectiva: {memoria_colectiva if memoria_colectiva else 'Ninguna'}. Operar con gestión de riesgo estricta."
            
        # Calcular SL y TP inteligentes basados en el activo
        precio_ej = req.precio
        tipo_orden = req.accion.upper()
        
        # Configuración por defecto
        sl = precio_ej - 200 if tipo_orden == "COMPRA" else precio_ej + 200
        tp = precio_ej + 400 if tipo_orden == "COMPRA" else precio_ej - 400
        lote = 0.1
        
        # Ajustes institucionales por tipo de activo
        if activo_normalizado in ["EURUSD", "GBPUSD"]:
            pips = 0.0020 if activo_normalizado == "EURUSD" else 0.0025
            sl = precio_ej - pips if tipo_orden == "COMPRA" else precio_ej + pips
            tp = precio_ej + (pips * 2.0) if tipo_orden == "COMPRA" else precio_ej - (pips * 2.0)
            lote = 0.5
        elif activo_normalizado == "GBPJPY":
            pips = 0.30
            sl = precio_ej - pips if tipo_orden == "COMPRA" else precio_ej + pips
            tp = precio_ej + (pips * 2.0) if tipo_orden == "COMPRA" else precio_ej - (pips * 2.0)
            lote = 0.3
        elif activo_normalizado == "XAUUSD":
            sl = precio_ej - 5.0 if tipo_orden == "COMPRA" else precio_ej + 5.0
            tp = precio_ej + 12.0 if tipo_orden == "COMPRA" else precio_ej - 12.0
            lote = 0.1
        elif activo_normalizado == "BTC":
            sl = precio_ej - 500.0 if tipo_orden == "COMPRA" else precio_ej + 500.0
            tp = precio_ej + 1500.0 if tipo_orden == "COMPRA" else precio_ej - 1500.0
            lote = 0.05
        elif activo_normalizado in ["NASDAQ100", "SP500", "US30"]:
            pct_sl = 0.01 if activo_normalizado != "SP500" else 0.007
            sl = precio_ej * (1.0 - pct_sl) if tipo_orden == "COMPRA" else precio_ej * (1.0 + pct_sl)
            tp = precio_ej * (1.0 + pct_sl * 2.5) if tipo_orden == "COMPRA" else precio_ej * (1.0 - pct_sl * 2.5)
            lote = 0.2
            
        sl = round(sl, 5)
        tp = round(tp, 5)
        
        # Logs en segundo plano (Notion, Excel Local y Firestore)
        background_tasks.add_task(enviar_a_notion, alert)
        background_tasks.add_task(actualizar_excel_local, alert)
        background_tasks.add_task(guardar_en_firestore, alert, None, None)
        
        print(f"| DECISIÓN CLOUD | Trade AUTORIZADO para {activo_normalizado}. Score: {score}%. Probabilidad: {probabilidad}%. SL: {sl} | TP: {tp}")
        
        return {
            "authorized": True,
            "activo": activo_normalizado,
            "accion": req.accion,
            "precio": req.precio,
            "lote": lote,
            "stop_loss": sl,
            "take_profit": tp,
            "analisis_ia": analisis_ia,
            "score_porcentaje": score,
            "probabilidad_exito": probabilidad
        }
    except Exception as e:
        print(f"| CLOUD ERROR | Error en webhook_mt5_setup: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/mia_trading_feed.xml")
def get_mia_trading_feed(authorization: Optional[str] = Header(None)):
    """
    Exposes Mia's trading learnings and sentiment as an RSS/XML feed.
    This feed can be consumed by n8n or other Mia instances to synchronize collective intelligence.
    """
    verificar_token(authorization)
    
    global firebase_inicializado, db
    if not firebase_inicializado or db is None:
        raise HTTPException(status_code=503, detail="Firebase no inicializado")
        
    try:
        docs = db.collection("trading_matrix").stream()
        
        xml_items = []
        for doc in docs:
            activo_id = doc.id
            data = doc.to_dict()
            apoyo = data.get("aprendizaje_mia", {})
            
            # Format as XML item
            item_xml = f"""
        <activo name="{activo_id}">
            <trades_totales>{apoyo.get('trades_totales', 0)}</trades_totales>
            <trades_ganados>{apoyo.get('trades_ganados', 0)}</trades_ganados>
            <win_rate_historico>{apoyo.get('win_rate_historico', 50.0)}</win_rate_historico>
            <racha_actual>{apoyo.get('racha_actual', 0)}</racha_actual>
            <sentimiento_acumulado>{apoyo.get('sentimiento_acumulado', 'NEUTRAL')}</sentimiento_acumulado>
            <factor_ajuste_probabilidad>{apoyo.get('factor_ajuste_probabilidad', 0.0)}</factor_ajuste_probabilidad>
            <ultimo_update>{data.get('ultimo_update', '')}</ultimo_update>
            <score_porcentaje>{data.get('score_porcentaje', 0.0)}</score_porcentaje>
        </activo>"""
            xml_items.append(item_xml)
            
        xml_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<mia_trading_learnings>
    <canal>
        <titulo>MIA Trading Bot learnings</titulo>
        <descripcion>Base de conocimiento (KB) de Mia en Trading Algoritmico</descripcion>
        <generacion>{datetime.datetime.now(datetime.timezone.utc).isoformat() if hasattr(datetime, 'timezone') else datetime.datetime.now().isoformat()}</generacion>
        <activos>{"".join(xml_items)}
        </activos>
    </canal>
</mia_trading_learnings>"""
        
        return Response(content=xml_content, media_type="application/xml")
    except Exception as e:
        print(f"| FEED XML ERROR | {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/update_collective_memory")
def update_collective_memory(req: CollectiveMemoryRequest, authorization: Optional[str] = Header(None)):
    """
    Allows n8n or another agent instance to update the cross-project collective memory of Mia.
    This string is injected into Mia's system prompts.
    """
    verificar_token(authorization)
    
    global firebase_inicializado, db
    if not firebase_inicializado or db is None:
        raise HTTPException(status_code=503, detail="Firebase no inicializado")
        
    try:
        doc_ref = db.collection("system_memory").document("mia_collective")
        doc_ref.set({
            "memoria_compartida": req.memoria_compartida,
            "ultimo_update": datetime.datetime.now(datetime.timezone.utc).isoformat() if hasattr(datetime, "timezone") else datetime.datetime.now().isoformat()
        })
        print(f"| FIREBASE SUCCESS | Memoria colectiva de MIA actualizada con éxito.")
        return {"status": "success", "message": "Memoria colectiva actualizada con éxito"}
    except Exception as e:
        print(f"| FIREBASE ERROR | Error al actualizar memoria colectiva: {e}")
        raise HTTPException(status_code=500, detail=str(e))

    # ------------------------------------------------------------------------------
    # Instrucción de ejecución local:
    # Para ejecutar este servicio web en tu máquina, abre una terminal y corre:
    # pip install fastapi uvicorn requests pydantic yfinance
    # uvicorn app:app --reload --port 8000
    # ------------------------------------------------------------------------------

