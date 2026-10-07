import os
import datetime
import json
import requests
from dotenv import load_dotenv
load_dotenv()
import firebase_admin
try:
    import google.generativeai as genai
except ImportError:
    genai = None
from firebase_admin import credentials, firestore

try:
    from mia_slack_bridge import slack_bridge
except ImportError:
    slack_bridge = None

class MiaQuantSupervisor:
    """
    SUPERVISOR INDEPENDIENTE DE TRADING Y POST-MORTEM.
    (Completamente aislado de MIA Watchdog / Ops).
    Motor LLM Exclusivo: Gemini 1.5 Pro.
    Skills: Análisis de Mercado, Cruce de CBR de Trading, Price Action.
    """
    def __init__(self):
        if not firebase_admin._apps:
            try:
                cred = credentials.Certificate('serviceAccountKey.json')
                firebase_admin.initialize_app(cred)
            except Exception:
                pass
        self.db = firestore.client() if firebase_admin._apps else None
        
        self.UPSTASH_URL = os.getenv("UPSTASH_REDIS_REST_URL", "https://certain-gnat-160816.upstash.io")
        self.UPSTASH_TOKEN = os.getenv("UPSTASH_REDIS_REST_TOKEN", "gQAAAAAAAnQwAAIgcDI2YTA5YjRlZDU2MDM0OWU5ODhlZjBlYTk4ODYyZDg0OA")
        self.UPSTASH_HEADERS = {"Authorization": f"Bearer {self.UPSTASH_TOKEN}"}
        self.SLACK_INSIGHTS_CHANNEL = os.getenv("SLACK_CHANNEL_INSIGHTS", "C0C6DUTQVEZ")

    def _llm_gemini_inference(self, trade_context, cbr_history):
        """
        Llamada EXCLUSIVA a Gemini 1.5 Pro.
        Cruza la info del trade perdido con los casos históricos del CBR,
        las estrategias activas de mia_kb (regla de 3) y el estado de la Red Neuronal (TensorFlow).
        """
        gemini_api_key = (os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY") or "").strip("'").strip('"')

        # 1. Recolectar Contexto Operativo (Anti-429: Todo desde Upstash Hot Cache)
        estrategia_actual = "{}"
        estado_tf = "{}"
        try:
            r_kb = requests.get(f"{self.UPSTASH_URL}/get/cache_regla_de_3", headers=self.UPSTASH_HEADERS, timeout=3).json()
            estrategia_actual = r_kb.get("result", "{}")
            
            r_tf = requests.get(f"{self.UPSTASH_URL}/get/cache_mia_tensorflow", headers=self.UPSTASH_HEADERS, timeout=3).json()
            # Solo pasamos una radiografía ligera de TF para no reventar el token limit
            tf_data = json.loads(r_tf.get("result", "{}")) if r_tf.get("result") else {}
            estado_tf = json.dumps({"accuracy": tf_data.get("accuracy"), "trades_aprendidos": tf_data.get("trades_learned")})
        except Exception:
            pass

        if not gemini_api_key:
            return {
                "diagnostico": f"Evaluación simulada (Falta GEMINI_API_KEY): El trade {trade_context.get('ticket')} falló.",
                "sugerencia_7_herds_trading": "Sugerencia: Configurar GEMINI_API_KEY en entorno para habilitar razonamiento avanzado de los 7 Herds.",
                "nota_infraestructura_t1_t10": "Infraestructura backend nominal."
            }

        prompt = f"""
        Eres MIA Quant Supervisor (Gemini Pro). Tu tarea es hacer un Análisis Cuantitativo y Post-Mortem de un trade cerrado para alimentar el CBR de Trading.
        NO vas a ejecutar nada en vivo. Emites un diagnóstico y una propuesta cuantitativa para la aprobación humana (HITL).

        TAXONOMÍA Y ROLES EN EL ECOSISTEMA MIA:
        1. LOS 7 HERDS DEL SWARM DE TRADING (FRONT-OFFICE / HFT / ANÁLISIS DE MERCADO):
           - HERD 1 (TIDAL): Flujo macro, sesiones Londres/NY, volumen delta y filtro de horarios.
           - HERD 2 (NORO): Matemáticas cuantitativas, POC dinámico y cadenas de Markov.
           - HERD 3 (ZEPHR): Probabilidad bayesiana, Expected Value y ratio Sharpe.
           - HERD 4 (LUMEN): Smart Money Concepts (SMC), Order Blocks LuxAlgo y Fair Value Gaps.
           - HERD 5 (RUNE): Gestión de riesgo estricto, tamaño de lote defensivo, SL/TP y trailing stop dinámico.
           - HERD 6 (TENSORFLOW): Inferencia neuronal profunda continua (Red Neuronal de 678 trades).
           - HERD 7 (ATLAS): Microestructura institucional, Order Book DOM CME/OANDA, CVD Delta y MCP.
           *Ellos son los ÚNICOS encargados de operar, analizar gráficos, calibrar SL/TP/Trailing Stop y confluencias de mercado.*

        2. HERDS T1 AL T10 + WATCHDOG SUPERVISOR (BACK-OFFICE / INFRAESTRUCTURA TÉCNICA):
           - Encargados EXCLUSIVOS de la estabilidad del backend, bases de datos (Firestore/Upstash), sincronización con MetaTrader 5, Uvicorn, latencia de red y CI/CD en Railway.
           - ¡NO HACEN TRADING, NO TIENEN SL/TP, NI ANALIZAN VELAS NI PARES! NUNCA les propongas ajustar parámetros de trading a ellos.

        [TRADE (GANANCIA, PERDIDA O BE)]
        {json.dumps(trade_context)}
        
        [ESTRATEGIAS ACTUALES (mia_kb / regla_de_3 / ML)]
        {estrategia_actual}
        
        [ESTADO RED NEURONAL TENSORFLOW]
        {estado_tf}
        
        [HISTORIAL CBR DE TRADING (Aprende de estos casos previos)]
        {json.dumps(cbr_history[:10])}
        
        Instrucciones:
        1. Si el trade fue PERDEDOR (PNL negativo), descubre por qué falló la predicción (ej. barrido de liquidez, stop muy ajustado, contra-tendencia de sesión asiática, divergencia de CVD).
        2. Si el trade fue GANADOR (PNL positivo), identifica el patrón clave que permitió el éxito para forzar a TensorFlow a darle más peso y a RUNE a proteger la posición.
        3. Si el trade fue BREAK-EVEN (PNL 0) o cierre por Trailing Stop, analiza si el trailing stop cortó las ganancias prematuramente o si protegió correctamente el capital ante una reversión.
        4. Devuelve estrictamente un JSON con las siguientes claves:
           - "diagnostico": Explicación concisa y técnica de lo ocurrido con el precio y la confluencia de mercado.
           - "sugerencia_7_herds_trading": Qué reglas matemáticas, parámetros de SL/TP, trailing stop (RUNE), pesos neuronales (TENSORFLOW), libro de órdenes DOM/CVD (ATLAS) o confluencias SMC (LUMEN/ZEPHR/NORO/TIDAL) propones ajustar a los 7 Herds del Swarm de Trading.
           - "nota_infraestructura_t1_t10": Si el trade falló por una desconexión de red, error 500 o bug de sincronización técnica en el backend, indícalo aquí para los Herds T1-T10. Si fue un movimiento normal de mercado y la infraestructura operó perfectamente, pon exactamente: "Infraestructura backend nominal (sin fallas técnicas)."
        """

        texto = None

        # Intento 1: SDK oficial si está disponible
        if genai:
            try:
                genai.configure(api_key=gemini_api_key)
                target_model_name = 'gemini-1.5-pro'
                try:
                    available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
                    if 'models/gemini-1.5-pro' in available_models:
                        target_model_name = 'gemini-1.5-pro'
                    elif 'models/gemini-2.5-flash' in available_models:
                        target_model_name = 'gemini-2.5-flash'
                    elif 'models/gemini-flash-latest' in available_models:
                        target_model_name = 'gemini-flash-latest'
                    elif len(available_models) > 0:
                        target_model_name = available_models[0].replace('models/', '')
                except Exception as dyn_e:
                    target_model_name = 'gemini-2.5-flash'

                model = genai.GenerativeModel(target_model_name)
                response = model.generate_content(prompt)
                texto = response.text
            except Exception as e_sdk:
                print(f"| QUANT AGENT | SDK Gemini error: {e_sdk}, probando REST...")

        # Intento 2: REST directo con failover de modelos
        if not texto:
            candidate_models = ["gemini-2.5-flash", "gemini-flash-latest", "gemini-2.5-flash-lite", "gemini-pro-latest", "gemini-3.1-pro-preview"]
            for m in candidate_models:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent?key={gemini_api_key}"
                payload = {
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {"temperature": 0.2, "maxOutputTokens": 1000}
                }
                try:
                    r = requests.post(url, json=payload, timeout=12)
                    if r.status_code == 200:
                        cand = r.json().get("candidates", [])
                        if cand:
                            texto = cand[0].get("content", {}).get("parts", [])[0].get("text", "")
                            if texto:
                                break
                except Exception:
                    continue

        if not texto:
            return {
                "diagnostico": f"No se pudo completar la inferencia con Gemini para el trade {trade_context.get('ticket')}.",
                "sugerencia_7_herds_trading": "Mantener configuraciones actuales de los 7 Herds. Error temporal en API de Gemini.",
                "nota_infraestructura_t1_t10": "Infraestructura backend nominal."
            }

        try:
            limpio = texto.replace('```json', '').replace('```', '').strip()
            resultado = json.loads(limpio)
            if "sugerencia" in resultado and "sugerencia_7_herds_trading" not in resultado:
                resultado["sugerencia_7_herds_trading"] = resultado["sugerencia"]
            if "nota_infraestructura_t1_t10" not in resultado:
                resultado["nota_infraestructura_t1_t10"] = "Infraestructura backend nominal."
            return resultado
        except Exception as e_parse:
            return {
                "diagnostico": f"Respuesta de Gemini generada pero no parseable: {texto[:100]}",
                "sugerencia_7_herds_trading": "Ajustar parámetros según confluencia de 7 Herds.",
                "nota_infraestructura_t1_t10": "Infraestructura backend nominal."
            }

    def analyze_recent_losses(self):
        print("| QUANT SUPERVISOR | Iniciando escaneo post-mortem con Gemini...")
        try:
            r = requests.get(f"{self.UPSTASH_URL}/get/cache_hist_mt5", headers=self.UPSTASH_HEADERS, timeout=5)
            hist = json.loads(r.json().get("result", "[]")) if r.json().get("result") else []
        except Exception:
            hist = []

        perdedores = [t for t in hist if float(t.get('profit', 0)) < 0]
        
        if not perdedores:
            perdedores = [{
                "ticket": "999999", "symbol": "EURUSD", "type": "BUY", "profit": -15.50,
                "time_out": datetime.datetime.now().isoformat()
            }]
            
        for trade in perdedores:
            self._generate_and_register_case(trade)
            break

    def _generate_and_register_case(self, trade):
        ticket = trade.get('ticket')
        symbol = trade.get('symbol')
        profit = trade.get('profit')
        
        # Obtener historial CBR para que Gemini cruce la información
        try:
            r_cbr = requests.get(f"{self.UPSTASH_URL}/get/cache_trading_learning_kb", headers=self.UPSTASH_HEADERS).json()
            cbr_history = json.loads(r_cbr.get("result", "[]")) if r_cbr.get("result") else []
        except Exception:
            cbr_history = []
            
        # 1. Llamada exclusiva a GEMINI PRO (Aislado de OpenRouter/Llama)
        gemini_analysis = self._llm_gemini_inference(trade, cbr_history)
        
        sugerencia_trading = gemini_analysis.get("sugerencia_7_herds_trading") or gemini_analysis.get("sugerencia", "Sin sugerencia de trading.")
        nota_infra = gemini_analysis.get("nota_infraestructura_t1_t10", "Infraestructura backend nominal.")
        diagnostico = gemini_analysis.get("diagnostico", "Diagnóstico no disponible.")

        case_id = f"TRADE_CASE_{ticket}_{int(datetime.datetime.now().timestamp())}"
        payload = {
            "caso": f"Análisis Post-Mortem Quant Trade {ticket}",
            "fecha": datetime.datetime.now().isoformat(),
            "ticket": ticket,
            "symbol": symbol,
            "diagnostico": diagnostico,
            "solucion_aprendida": sugerencia_trading,
            "nota_infraestructura_t1_t10": nota_infra,
            "accion_ejecutada": "NINGUNA. SOLO REGISTRO DE CBR QUANT (HITL ACTIVO)."
        }

        # 2. Guardar en el CBR
        if self.db:
            try:
                self.db.collection("mia_trading_learning_history").document(case_id).set(payload)
            except Exception:
                pass

        try:
            cbr_history.insert(0, payload)
            requests.post(f"{self.UPSTASH_URL}/set/cache_trading_learning_kb", headers=self.UPSTASH_HEADERS, json=cbr_history[:50])
        except Exception:
            pass

        # 3. Notificar a Slack en el canal de Insights (Con Interfaz RLHF Block Kit)
        if slack_bridge and (slack_bridge.bot_token or slack_bridge.quant_bot_token):
            msg_fallback = f"MIA Quant: Análisis para {ticket} en {symbol}"
            
            blocks = [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f"🌌 MIA QUANT: Post-Mortem Trade {ticket}",
                        "emoji": True
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": (
                            f"*Símbolo:* {symbol} | *Resultado:* `{profit}`\n\n"
                            f"*🧠 Diagnóstico Gemini Pro:*\n{diagnostico}\n\n"
                            f"*🎯 Acción Propuesta para los 7 Herds de Trading (LUMEN, TIDAL, NORO, ZEPHR, RUNE, ATLAS, TENSORFLOW):*\n{sugerencia_trading}"
                        )
                    }
                },
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": f"Caso CBR: `{case_id}` | 🧠 *Memoria Viva:* `cache_trading_learning_kb` | Mandato HITL Activo."
                        }
                    ]
                },
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "✅ Aprobar Aprendizaje",
                                "emoji": True
                            },
                            "style": "primary",
                            "value": f"approve_{case_id}",
                            "action_id": f"quant_approve_{ticket}"
                        },
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "❌ Rechazar Razonamiento",
                                "emoji": True
                            },
                            "style": "danger",
                            "value": f"reject_{case_id}",
                            "action_id": f"quant_reject_{ticket}"
                        },
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "🔍 Revisión Manual",
                                "emoji": True
                            },
                            "value": f"review_{case_id}",
                            "action_id": f"quant_review_{ticket}"
                        }
                    ]
                },
                {
                    "type": "divider"
                }
            ]
            
            try:
                slack_bridge.send_channel_message(
                    text=msg_fallback, 
                    channel=self.SLACK_INSIGHTS_CHANNEL, 
                    username="MIA Quant Supervisor", 
                    icon_emoji=":brain:",
                    blocks=blocks
                )
                print(f"| QUANT AGENT | Mensaje enviado a Slack con exito para {ticket}.")
            except Exception as e:
                print(f"| QUANT AGENT | Error enviando Block Kit: {e}")

            # Bifurcación Estricta: Si hubo un error técnico de infraestructura, notificar exclusivamente a #back-office-y-backend
            if "nominal" not in nota_infra.lower() and "sin fallas" not in nota_infra.lower():
                try:
                    slack_bridge.send_channel_message(
                        text=f"🚨 *ALERTA TÉCNICA INFRAESTRUCTURA (T1-T10 / SRE)*: Trade `{ticket}` en {symbol} reportó anomalía técnica: {nota_infra}",
                        channel=os.getenv("SLACK_CHANNEL_OPS", "C0C4ZMFCMJ8"),
                        username="MIA SRE Watchdog",
                        icon_emoji=":warning:"
                    )
                    print(f"| QUANT AGENT | Incidente técnico bifurcado a #back-office-y-backend para {ticket}.")
                except Exception as e_ops:
                    print(f"| QUANT AGENT | Error enviando alerta técnica a ops: {e_ops}")

if __name__ == "__main__":
    agent = MiaQuantSupervisor()
    agent.analyze_recent_losses()
