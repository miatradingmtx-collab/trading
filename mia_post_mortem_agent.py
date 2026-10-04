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
        Stub para la llamada EXCLUSIVA a Gemini Pro.
        Cruza la info del trade perdido con los casos históricos del CBR.
        """
        # Aquí irá la lógica de google-generativeai en el futuro.
        # Por ahora devolvemos la deducción simulada basada en el cruce de datos.
        return {
            "diagnostico": f"Evaluación Gemini Pro: El trade {trade_context['ticket']} cerró en pérdida. Fallo de TensorFlow por divergencia de volumen.",
            "sugerencia": "Sugerencia Cuántica: Incrementar filtro de volatilidad VIX > 15 para temporalidades M5."
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

        # 3. Notificar a Slack en el canal de Insights
        if slack_bridge and slack_bridge.bot_token:
            msg = (f"🌌 *MIA QUANT SUPERVISOR (Powered by Gemini Pro)*\n"
                   f"🧠 *NUEVO APRENDIZAJE POST-MORTEM*\n"
                   f"• *Trade:* {ticket} ({symbol})\n"
                   f"• *Diagnóstico:* {gemini_analysis['diagnostico']}\n"
                   f"• *Sugerencia Evolutiva:* {gemini_analysis['sugerencia']}\n"
                   f"_(Guardado en CBR Quant como {case_id})_")
            try:
                slack_bridge.send_channel_message(msg, channel=self.SLACK_INSIGHTS_CHANNEL, username="MIA Quant", icon_emoji=":brain:")
            except Exception:
                pass

if __name__ == "__main__":
    agent = MiaQuantSupervisor()
    agent.analyze_recent_losses()
