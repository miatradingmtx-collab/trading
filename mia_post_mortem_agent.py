import os
import datetime
import json
import requests
import firebase_admin
from firebase_admin import credentials, firestore

try:
    from mia_slack_bridge import slack_bridge
except ImportError:
    slack_bridge = None

class TradingPostMortemAgent:
    def __init__(self):
        # Asegurar inicialización de Firebase
        if not firebase_admin._apps:
            try:
                cred = credentials.Certificate('serviceAccountKey.json')
                firebase_admin.initialize_app(cred)
            except Exception:
                pass
        self.db = firestore.client() if firebase_admin._apps else None
        
        self.UPSTASH_URL = "https://certain-gnat-160816.upstash.io"
        self.UPSTASH_HEADERS = {"Authorization": "Bearer ASQwAAIjcDFlNWQ4NTEyNmZhMTY0ODg4OTYxOGFmMGNmNDIzZmRiM3AxMA"}
        
        # El canal a configurar en el futuro en slack
        self.SLACK_INSIGHTS_CHANNEL = os.getenv("SLACK_CHANNEL_INSIGHTS", "C0C6DUTQVEZ") # Placeholder

    def analyze_recent_losses(self):
        """
        Lee el historial reciente y simula un post-mortem en caso de pérdida.
        NUNCA EJECUTA CAMBIOS, SOLO PROPONE Y REGISTRA EN EL CBR.
        """
        print("| POST-MORTEM AGENT | Iniciando escaneo de trades...")
        # En producción, esto leeria cache_hist_mt5. Aquí simularemos un hallazgo si la lógica lo requiere,
        # o leeremos la caché real.
        try:
            r = requests.get(f"{self.UPSTASH_URL}/get/cache_hist_mt5", headers=self.UPSTASH_HEADERS, timeout=5)
            hist = json.loads(r.json().get("result", "[]")) if r.json().get("result") else []
        except Exception as e:
            print(f"| POST-MORTEM AGENT | Error leyendo historial: {e}")
            hist = []

        # Filtrar trades perdedores no analizados (Simulación conceptual para el primer paso)
        perdedores = [t for t in hist if float(t.get('profit', 0)) < 0]
        
        # Si no hay, creamos un caso simulado de ejemplo para que veas cómo funciona en Slack
        if not perdedores:
            print("| POST-MORTEM AGENT | No hay pérdidas reales en caché. Generando simulación de Post-Mortem...")
            perdedores = [{
                "ticket": "999999", "symbol": "EURUSD", "type": "BUY", "profit": -15.50,
                "time_out": datetime.datetime.now().isoformat()
            }]
            
        for trade in perdedores:
            self._generate_and_register_case(trade)
            # Solo procesar uno por ejecución para evitar spam
            break

    def _generate_and_register_case(self, trade):
        ticket = trade.get('ticket')
        symbol = trade.get('symbol')
        profit = trade.get('profit')
        
        # 1. Agente LLM simula el diagnóstico (En el futuro esto llama al modelo Gemini Pro real)
        diagnostico = f"El trade {ticket} en {symbol} cerró en pérdida ({profit}). Se detectó divergencia de volumen."
        sugerencia = "Sugerencia: Incrementar filtro de volatilidad VIX > 15 para temporalidades M5."
        
        case_id = f"TRADE_CASE_{ticket}_{int(datetime.datetime.now().timestamp())}"
        payload = {
            "caso": f"Análisis Post-Mortem Trade {ticket}",
            "fecha": datetime.datetime.now().isoformat(),
            "ticket": ticket,
            "symbol": symbol,
            "diagnostico": diagnostico,
            "solucion_aprendida": sugerencia,
            "accion_ejecutada": "NINGUNA. SOLO REGISTRO DE CBR (HITL ACTIVO)."
        }

        # 2. Guardar en el CBR
        if self.db:
            try:
                self.db.collection("mia_trading_learning_history").document(case_id).set(payload)
                print(f"| POST-MORTEM AGENT | Caso {case_id} guardado en Firebase.")
            except Exception as e:
                print(f"Error Firebase: {e}")

        # Upstash
        try:
            r = requests.get(f"{self.UPSTASH_URL}/get/cache_trading_learning_kb", headers=self.UPSTASH_HEADERS).json()
            kb_data = json.loads(r.get("result", "[]")) if r.get("result") else []
            kb_data.insert(0, payload)
            requests.post(f"{self.UPSTASH_URL}/set/cache_trading_learning_kb", headers=self.UPSTASH_HEADERS, json=kb_data[:50])
        except Exception:
            pass

        # 3. Notificar a Slack en el canal Independiente
        if slack_bridge and slack_bridge.bot_token:
            msg = (f"🧠 *NUEVO APRENDIZAJE POST-MORTEM (CBR)*\n"
                   f"• *Trade:* {ticket} ({symbol})\n"
                   f"• *Diagnóstico:* {diagnostico}\n"
                   f"• *Sugerencia (No aplicada):* {sugerencia}\n"
                   f"_(Guardado como Caso {case_id} para referencia futura)_")
            
            # Aqui usa el canal configurado, o uno por defecto
            try:
                # Omitimos el channel= si quieres que use el default para pruebas, 
                # o usamos self.SLACK_INSIGHTS_CHANNEL
                slack_bridge.send_channel_message(msg, channel=self.SLACK_INSIGHTS_CHANNEL)
                print("| POST-MORTEM AGENT | Slack notificado.")
            except Exception as e:
                print(f"| POST-MORTEM AGENT | Error Slack: {e}")
        else:
            print("| POST-MORTEM AGENT | Slack Bridge no disponible.")

if __name__ == "__main__":
    agent = TradingPostMortemAgent()
    agent.analyze_recent_losses()
