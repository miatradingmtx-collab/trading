import os
import datetime
import json
import requests
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
        
        self.UPSTASH_URL = "https://certain-gnat-160816.upstash.io"
        self.UPSTASH_HEADERS = {"Authorization": "Bearer ASQwAAIjcDFlNWQ4NTEyNmZhMTY0ODg4OTYxOGFmMGNmNDIzZmRiM3AxMA"}
        self.SLACK_INSIGHTS_CHANNEL = os.getenv("SLACK_CHANNEL_INSIGHTS", "C0C6DUTQVEZ")

    def _llm_gemini_inference(self, trade_context, cbr_history):
        """
        Llamada EXCLUSIVA a Gemini 1.5 Pro.
        Cruza la info del trade perdido con los casos históricos del CBR,
        las estrategias activas de mia_kb (regla de 3) y el estado de la Red Neuronal (TensorFlow).
        """
        gemini_api_key = os.getenv("GOOGLE_API_KEY", os.getenv("GEMINI_API_KEY"))
        
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

        if not genai or not gemini_api_key:
            return {
                "diagnostico": f"Evaluación simulada (Falta GEMINI_API_KEY): El trade {trade_context.get('ticket')} falló.",
                "sugerencia": "Sugerencia: Configurar GEMINI_API_KEY en entorno para habilitar razonamiento avanzado."
            }

        try:
            genai.configure(api_key=gemini_api_key)
            # Usar el modelo pro para mayor ventana de contexto y cruce de datos
            model = genai.GenerativeModel('gemini-1.5-pro-latest')
            
            prompt = f"""
            Eres MIA Quant Supervisor. Tu tarea es hacer un Análisis Post-Mortem de un trade perdedor.
            NO vas a ejecutar nada, solo darás un diagnóstico y una sugerencia para el CBR.
            
            [TRADE PERDIDO]
            {json.dumps(trade_context)}
            
            [ESTRATEGIAS ACTUALES (mia_kb / regla_de_3 / ML)]
            {estrategia_actual}
            
            [ESTADO RED NEURONAL TENSORFLOW]
            {estado_tf}
            
            [HISTORIAL CBR DE TRADING (Aprende de estos casos)]
            {json.dumps(cbr_history[:10])} # Top 10 casos recientes
            
            Instrucciones:
            1. Haz un cruce de información: ¿Por qué la estrategia actual y la red neuronal fallaron en este trade?
            2. Revisa el Historial CBR: ¿Es un error repetido (Ej. Case 10)? Si es así, indícalo.
            3. Devuelve estrictamente un JSON con las claves: "diagnostico" (qué falló) y "sugerencia" (qué hiperparámetros o reglas propones ajustar para el enjambre o TensorFlow).
            """
            
            response = model.generate_content(prompt)
            texto = response.text.replace('```json', '').replace('```', '').strip()
            resultado = json.loads(texto)
            return resultado
        except Exception as e:
            return {
                "diagnostico": f"Error de inferencia Gemini: {e}",
                "sugerencia": "Mantener configuraciones actuales. Fallo en procesamiento Quant."
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
        
        case_id = f"TRADE_CASE_{ticket}_{int(datetime.datetime.now().timestamp())}"
        payload = {
            "caso": f"Análisis Post-Mortem Quant Trade {ticket}",
            "fecha": datetime.datetime.now().isoformat(),
            "ticket": ticket,
            "symbol": symbol,
            "diagnostico": gemini_analysis["diagnostico"],
            "solucion_aprendida": gemini_analysis["sugerencia"],
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
                        "text": f"*Símbolo:* {symbol}\n*Resultado:* {profit}\n\n*🧠 Diagnóstico Gemini Pro:*\n{gemini_analysis['diagnostico']}\n\n*🎯 Acción Propuesta para Enjambres:*\n{gemini_analysis['sugerencia']}"
                    }
                },
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": f"Caso CBR: `{case_id}` | Requiere validación humana (Mandato HITL) para sumar nivel de confianza."
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

if __name__ == "__main__":
    agent = MiaQuantSupervisor()
    agent.analyze_recent_losses()
