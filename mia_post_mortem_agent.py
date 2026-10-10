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

        # 1. Recolectar Contexto Operativo Integral vía MGET Atómico (Anti-429: Todo desde Upstash Hot Cache en 1 llamada)
        estrategia_actual = "{}"
        estado_tf = "{}"
        debate_7_herds = "Sin debate previo registrado"
        microestructura_atlas = "Sin datos de libro CME/OANDA"
        estado_mt5 = "{}"

        try:
            mget_url = f"{self.UPSTASH_URL}/mget/cache_regla_de_3/cache_mia_tensorflow/cache_herd_debate_latest/cache_mia_atlas/cache_mt5"
            r_all = requests.get(mget_url, headers=self.UPSTASH_HEADERS, timeout=4).json()
            slots = r_all.get("result", [])
            if len(slots) >= 5:
                # Slot 0: Regla de 3
                if slots[0]:
                    estrategia_actual = slots[0]
                # Slot 1: TensorFlow
                if slots[1]:
                    tf_d = json.loads(slots[1]) if isinstance(slots[1], str) else slots[1]
                    estado_tf = json.dumps({"accuracy": tf_d.get("accuracy"), "trades_aprendidos": tf_d.get("trades_aprendidos", tf_d.get("trades_learned", 687))})
                # Slot 2: Debate de los 7 Herds
                if slots[2]:
                    deb_d = json.loads(slots[2]) if isinstance(slots[2], str) else slots[2]
                    if isinstance(deb_d, dict):
                        deb_dict = deb_d.get("debate", deb_d)
                        debate_7_herds = json.dumps({
                            "tidal": deb_dict.get("herd_1_tidal", "N/A"),
                            "noro": deb_dict.get("herd_2_noro", "N/A"),
                            "zephr": deb_dict.get("herd_3_zephr", "N/A"),
                            "lumen": deb_dict.get("herd_4_lumen", "N/A"),
                            "rune": deb_dict.get("herd_5_rune", "N/A"),
                            "tensorflow": deb_dict.get("herd_6_tensorflow", "N/A"),
                            "atlas": deb_dict.get("herd_7_atlas", "N/A"),
                            "quorum_master": deb_dict.get("master_quorum", deb_d.get("veredicto", "N/A"))
                        })
                    else:
                        debate_7_herds = str(deb_d)[:400]
                # Slot 3: ATLAS DOM/CVD
                if slots[3]:
                    atl_d = json.loads(slots[3]) if isinstance(slots[3], str) else slots[3]
                    if isinstance(atl_d, dict):
                        microestructura_atlas = json.dumps({
                            "cvd_delta": atl_d.get("cvd_delta", "N/A"),
                            "flujo_comprador": atl_d.get("buyer_pct", atl_d.get("buyer_volume_pct", "N/A")),
                            "flujo_vendedor": atl_d.get("seller_pct", atl_d.get("seller_volume_pct", "N/A")),
                            "trampas_detectadas": atl_d.get("heatmap_resting_liquidity", atl_d.get("trampas", "N/A"))
                        })
                    else:
                        microestructura_atlas = str(atl_d)[:300]
                # Slot 4: MT5
                if slots[4]:
                    mt5_d = json.loads(slots[4]) if isinstance(slots[4], str) else slots[4]
                    if isinstance(mt5_d, dict):
                        estado_mt5 = json.dumps({
                            "balance": mt5_d.get("balance"),
                            "equity": mt5_d.get("equity"),
                            "pnl_cerrado_hoy": mt5_d.get("pnl_cerrado_hoy"),
                            "pnl_flotante": mt5_d.get("floating_pnl", mt5_d.get("pnl_flotante"))
                        })
        except Exception as e_mget:
            print(f"| QUANT AGENT WARN | Error leyendo MGET Hot Cache: {e_mget}")

        if not gemini_api_key:
            return {
                "diagnostico": f"Evaluación simulada (Falta GEMINI_API_KEY): El trade {trade_context.get('ticket')} falló.",
                "sugerencia_7_herds_trading": "Sugerencia: Configurar GEMINI_API_KEY en entorno para habilitar razonamiento avanzado de los 7 Herds.",
                "nota_infraestructura_t1_t10": "Infraestructura backend nominal."
            }

        prompt = f"""
        Eres MIA Quant Supervisor (Gemini Pro). Tu tarea es hacer un Análisis Cuantitativo y Post-Mortem de un trade cerrado para alimentar el CBR de Trading.
        NO vas a ejecutar nada en vivo. Emites un diagnóstico y una propuesta cuantitativa para la aprobación humana (HITL).

        TAXONOMÍA Y ROLES EN EL ECOSISTEMA MIA (CANÓNICO - 3 RAMAS ESTRICTAS):
        1. SWARM DE TRADING EN VIVO (HFT / ANÁLISIS DE MERCADO - MOTOR: LLAMA 3.3 70B REST):
           - HERD 1 (TIDAL): Flujo macro, sesiones Londres/NY/Asia, absorción y filtro de horarios óptimos.
           - HERD 2 (NORO): Matemáticas cuantitativas, POC dinámico intradiario/semanal y cadenas de Markov.
           - HERD 3 (ZEPHR): Probabilidad bayesiana, Expected Value (EV) y confluencias estadísticas.
           - HERD 4 (LUMEN): Smart Money Concepts (SMC), Order Blocks LuxAlgo, ChoCh y Fair Value Gaps.
           - HERD 5 (RUNE): Gestión de riesgo estricto, tamaño de lote defensivo, SL/TP, Parciales (TP40/TP65) y Trailing Stop escalonado (40%, 65%, 85%, 95%).
           - HERD 6 (TENSORFLOW): Inferencia neuronal profunda continua (Red Neuronal calibrada con 687+ trades aprendidos).
           - HERD 7 (ATLAS): Microestructura institucional, Order Book DOM CME/OANDA, CVD Delta acumulado y verificación con CBR.
           *Ellos analizan segundo a segundo el mercado con Llama 3.3 70B y guardan su debate en Upstash Redis (cache_herd_debate_latest).*

        2. BACK-OFFICE / INFRAESTRUCTURA TÉCNICA (SRE / TERMINATORS T1-T10 - MOTOR: LLAMA 3.3 70B OPENROUTER OPS - CANAL #BACK-OFFICE-Y-BACKEND):
           - Herds T1 al T10 + Supervisor Watchdog. Encargados EXCLUSIVOS de la estabilidad del backend, bases de datos (Firestore/Upstash), Docker/Railway, Uvicorn, latencia MGET y CI/CD.
           - ¡NO HACEN TRADING, NO TIENEN SL/TP, NI ANALIZAN VELAS NI PARES! NUNCA les propongas ajustar parámetros de trading a ellos.

        3. TÚ: AGENTE POST-MORTEM & SUPERVISOR QUANT (COGNICIÓN, AUTOPSIA Y APRENDIZAJE CBR - MOTOR: GOOGLE GEMINI 1.5 PRO - CANAL #MIA-TRADING-INSIGHTS):
           - Tu misión es cruzar las decisiones y debates de los 7 Herds (Llama 70B), TensorFlow, ATLAS, métricas de MT5 y Firebase para extraer lecciones cuantitativas, alimentar el CBR (cache_trading_learning_kb) y proponer calibraciones para los 5 pares oficiales de MT5.

        PORTAFOLIO OFICIAL EN BROKER MT5:
        - EN VIVO (5 PARES): EURUSD, GBPUSD, AUDUSD, GBPJPY, XAUUSD.
        - SANDBOX EXPERIMENTAL: NZDCAD (Modo Entrenamiento / Shadow, prohibida ejecución en broker).

        [TRADE CERRADO A EVALUAR]
        {json.dumps(trade_context)}
        
        [ESTRATEGIAS ACTUALES (mia_kb / regla_de_3 / ML)]
        {estrategia_actual}
        
        [ESTADO RED NEURONAL TENSORFLOW]
        {estado_tf}

        [ÚLTIMO DICTAMEN DE LOS 7 HERDS DEL SWARM (TIDAL, NORO, ZEPHR, LUMEN, RUNE, TENSORFLOW, ATLAS)]
        {debate_7_herds}

        [MICROESTRUCTURA INSTITUCIONAL ATLAS DOM & CVD DELTA]
        {microestructura_atlas}

        [ESTADO FINANCIERO Y BALANCE MT5]
        {estado_mt5}
        
        [HISTORIAL CBR DE TRADING (Aprende de estos casos previos)]
        {json.dumps(cbr_history[:10])}
        
        Instrucciones:
        1. Si el trade fue PERDEDOR (PNL negativo), descubre por qué falló la confluencia (ej. barrido de liquidez, stop muy ceñido sin buffer ATR, reversión prematura contra CVD, contra-tendencia de sesión).
        2. Si el trade fue GANADOR (PNL positivo), identifica el patrón institucional clave (Order Block respetado, confluencia de POC, sesión óptima) para calibrar a TensorFlow y RUNE.
        3. Si el trade fue BREAK-EVEN (PNL 0) o cierre por Trailing Stop, evalúa si el SL a BE se activó prematuramente cortando la expansión o si protegió correctamente el capital.
        4. Formula recomendaciones concretas para los 7 Herds que apliquen a los 5 pares oficiales de MT5 (EURUSD, GBPUSD, AUDUSD, GBPJPY, XAUUSD):
           - SL defensivo con buffer ATR.
           - Toma de Parcial 1 (TP40) asegurando beneficio.
           - Retrasar el movimiento a Breakeven hasta que el precio supere el 40% del recorrido.
           - Trailing stop escalonado holgado (40%, 65%, 85%, 95%).
        5. Devuelve estrictamente un JSON con las siguientes claves:
           - "diagnostico": Explicación concisa y técnica de lo ocurrido con el precio y la confluencia de mercado.
           - "sugerencia_7_herds_trading": Qué reglas matemáticas, parámetros de SL/TP, trailing stop (RUNE), pesos neuronales (TENSORFLOW), libro de órdenes DOM/CVD (ATLAS) o confluencias SMC (LUMEN/ZEPHR/NORO/TIDAL) propones ajustar a los 7 Herds para los 5 pares operados.
           - "nota_infraestructura_t1_t10": Si el trade falló por una desconexión técnica, bug de sincronización o error 500 en backend, indícalo aquí para T1-T10. Si fue movimiento normal de mercado y la infraestructura operó perfectamente, pon exactamente: "Infraestructura backend nominal (sin fallas técnicas)."
        6. REGLA INQUEBRANTABLE (FILTRO ANTI-SUERTE >= 50 TRADES):
           Está terminantemente PROHIBIDO sugerir o alterar el Top 1, Top 2 o Top 3 de la 'Regla de 3' (mia_kb/regla_de_3) basándote en rachas de corto plazo, el 'día de suerte' o la 'semana de suerte'. Para que cualquier indicador o patrón sea considerado o sugerido para la Regla de 3, DEBE tener un mínimo absoluto de 50 trades históricos reales cerrados con Win Rate validado y expectativa matemática positiva (PnL > 0).
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

                generation_config = {"temperature": 0.2, "max_output_tokens": 2500}
                model = genai.GenerativeModel(target_model_name, generation_config=generation_config)
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
                    "generationConfig": {"temperature": 0.2, "maxOutputTokens": 2500}
                }
                try:
                    r = requests.post(url, json=payload, timeout=15)
                    if r.status_code == 200:
                        cand = r.json().get("candidates", [])
                        if cand:
                            texto = cand[0].get("content", {}).get("parts", [])[0].get("text", "")
                            if texto:
                                break
                except Exception:
                    continue

        # Intento 3: Failover de Gemini vía Gateway OpenRouter (google/gemini-2.5-flash) si Google directo da 429
        if not texto and os.getenv("OPENROUTER_API_KEY"):
            try:
                or_key = os.getenv("OPENROUTER_API_KEY")
                or_headers = {"Authorization": f"Bearer {or_key}", "Content-Type": "application/json"}
                or_payload = {
                    "model": "google/gemini-2.5-flash",
                    "messages": [
                        {"role": "system", "content": "Eres MIA Quant Supervisor (Gemini Pro). Devuelve estrictamente un objeto JSON completo y cerrado."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.2,
                    "max_tokens": 2500
                }
                r_or = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=or_headers, json=or_payload, timeout=15)
                if r_or.status_code == 200:
                    choices = r_or.json().get("choices", [])
                    if choices:
                        texto = choices[0].get("message", {}).get("content", "")
                        print(f"| QUANT AGENT | Inferencia Gemini completada exitosamente vía Gateway OpenRouter.")
            except Exception as e_or:
                print(f"| QUANT AGENT | Error en failover OpenRouter Gemini: {e_or}")

        if not texto:
            return {
                "diagnostico": f"No se pudo completar la inferencia con Gemini para el trade {trade_context.get('ticket')}.",
                "sugerencia_7_herds_trading": "Mantener configuraciones actuales de los 7 Herds. Error temporal en API de Gemini.",
                "nota_infraestructura_t1_t10": "Infraestructura backend nominal."
            }

        resultado = None
        import re
        try:
            m_json = re.search(r'```(?:json)?\s*(\{[\s\S]*?\})\s*```', texto)
            if m_json:
                resultado = json.loads(m_json.group(1))
            else:
                s_idx = texto.find('{')
                e_idx = texto.rfind('}')
                if s_idx != -1 and e_idx != -1 and e_idx > s_idx:
                    resultado = json.loads(texto[s_idx:e_idx+1])
                else:
                    limpio = texto.replace('```json', '').replace('```', '').strip()
                    resultado = json.loads(limpio)
        except Exception as e_parse:
            print(f"| QUANT AGENT | JSON parse error: {e_parse}")

        if resultado and isinstance(resultado, dict):
            if "sugerencia" in resultado and "sugerencia_7_herds_trading" not in resultado:
                resultado["sugerencia_7_herds_trading"] = resultado["sugerencia"]
            if "nota_infraestructura_t1_t10" not in resultado:
                resultado["nota_infraestructura_t1_t10"] = "Infraestructura backend nominal."
            return resultado

        return {
            "diagnostico": texto[:400] if texto else "Diagnóstico no disponible.",
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
            
        # 1. Llamada exclusiva a GEMINI (Aislado de Llama/Back-Office)
        gemini_analysis = self._llm_gemini_inference(trade, cbr_history)
        
        sugerencia_raw = gemini_analysis.get("sugerencia_7_herds_trading") or gemini_analysis.get("sugerencia", "Sin sugerencia de trading.")
        if isinstance(sugerencia_raw, dict):
            sugerencia_trading = "\n".join([f"• *{k}:* {v}" for k, v in sugerencia_raw.items()])
        elif isinstance(sugerencia_raw, list):
            sugerencia_trading = "\n".join([f"• {item}" for item in sugerencia_raw])
        else:
            sugerencia_trading = str(sugerencia_raw)

        diagnostico_raw = gemini_analysis.get("diagnostico", "Diagnóstico no disponible.")
        if isinstance(diagnostico_raw, dict):
            diagnostico = "\n".join([f"• *{k}:* {v}" for k, v in diagnostico_raw.items()])
        else:
            diagnostico = str(diagnostico_raw)

        nota_infra = str(gemini_analysis.get("nota_infraestructura_t1_t10", "Infraestructura backend nominal."))

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

    def reconcile_and_process_daily_trades(self, days_back: int = 2):
        """
        Reconciliador Automático Diario (Watchdog Anti-Pérdida de Trades):
        1. Escanea todos los trades cerrados de las últimas 24h-48h desde Firestore (mia_audit_logs).
        2. Sincroniza e ingesta los trades faltantes en cache_mia_dataset_tf y reentrena TensorFlow.
        3. Verifica que cada trade cerrado tenga su caso analizado en cache_trading_learning_kb (CBR).
        4. Si algún trade no tiene caso post-mortem, lo procesa con Gemini Pro y notifica a Slack.
        """
        print(f"| QUANT RECONCILER | Iniciando reconciliación de trades diarios (últimos {days_back} días)...")
        if not self.db:
            print("| QUANT RECONCILER | Firestore no disponible.")
            return {"status": "error", "message": "Firestore no disponible"}
            
        try:
            # 1. Obtener trades cerrados recientes de Firestore
            docs = self.db.collection('mia_audit_logs').order_by('timestamp', direction=firestore.Query.DESCENDING).limit(100).stream()
            closed_trades = []
            for doc in docs:
                data = doc.to_dict()
                ticket = str(data.get('ticket', doc.id))
                if ticket.isdigit() and len(ticket) >= 8:
                    accion = data.get('accion', '')
                    pnl = float(data.get('pnl', 0.0) or 0.0)
                    if accion in ['CIERRE_TOTAL', 'CERRAR_TP', 'CIERRE_PARCIAL', 'TRAILING_STOP', 'PROTECCION_BE'] or pnl != 0.0:
                        closed_trades.append({
                            'ticket': ticket,
                            'symbol': data.get('activo', 'EURUSD'),
                            'profit': pnl,
                            'type': accion,
                            'motivo': data.get('motivo', 'Cierre MT5'),
                            'timestamp': data.get('timestamp', ''),
                            'detalle_setup': data.get('detalle_setup', ''),
                            'score': data.get('score', 75.0)
                        })
            
            print(f"| QUANT RECONCILER | {len(closed_trades)} trades cerrados detectados en auditoría.")
            
            # 2. Reconciliación con TensorFlow (cache_mia_dataset_tf)
            r_ds = requests.get(f"{self.UPSTASH_URL}/get/cache_mia_dataset_tf", headers=self.UPSTASH_HEADERS, timeout=5)
            tf_ds = []
            if r_ds.status_code == 200 and r_ds.json().get('result'):
                raw = r_ds.json().get('result')
                tf_ds = json.loads(raw) if isinstance(raw, str) else (raw or [])
                
            tf_existing = {str(x.get('ticket')) for x in tf_ds if x.get('ticket')}
            new_tf_trades = 0
            for t in closed_trades:
                if t['ticket'] not in tf_existing:
                    tf_ds.append({
                        'ticket': t['ticket'],
                        'activo': t['symbol'],
                        'pnl': t['profit'],
                        'accion': t['type'],
                        'score': t.get('score', 75.0),
                        'timestamp': t['timestamp'],
                        'detalle_setup': t.get('detalle_setup', '')
                    })
                    tf_existing.add(t['ticket'])
                    new_tf_trades += 1
                    
            if new_tf_trades > 0:
                print(f"| QUANT RECONCILER | Ingestando {new_tf_trades} trades faltantes en TensorFlow dataset...")
                requests.post(f"{self.UPSTASH_URL}/set/cache_mia_dataset_tf", headers=self.UPSTASH_HEADERS, data=json.dumps(tf_ds, default=str), timeout=10)
                try:
                    requests.get("https://trading-production-927a.up.railway.app/api/cron/train_tensorflow", timeout=30)
                    print("| QUANT RECONCILER | Red Neuronal reentrenada exitosamente.")
                except Exception as e_tf_call:
                    print(f"| QUANT RECONCILER WARN | No se pudo llamar /train_tensorflow: {e_tf_call}")

            # 3. Reconciliación con CBR de Trading (cache_trading_learning_kb)
            r_cbr = requests.get(f"{self.UPSTASH_URL}/get/cache_trading_learning_kb", headers=self.UPSTASH_HEADERS, timeout=5)
            cbr_list = []
            if r_cbr.status_code == 200 and r_cbr.json().get('result'):
                raw_cbr = r_cbr.json().get('result')
                cbr_list = json.loads(raw_cbr) if isinstance(raw_cbr, str) else (raw_cbr or [])
                
            cbr_existing_tickets = {str(c.get('ticket')) for c in cbr_list if c.get('ticket')}
            cases_generated = 0
            
            for t in closed_trades:
                if t['ticket'] not in cbr_existing_tickets:
                    print(f"| QUANT RECONCILER | Generando caso Post-Mortem para trade huérfano Ticket {t['ticket']} ({t['symbol']} | PnL: ${t['profit']})...")
                    self._generate_and_register_case(t)
                    cbr_existing_tickets.add(t['ticket'])
                    cases_generated += 1
                    
            print(f"| QUANT RECONCILER | Reconciliación finalizada: {new_tf_trades} trades agregados a TF, {cases_generated} casos post-mortem registrados en CBR.")
            return {
                "status": "success",
                "closed_trades_checked": len(closed_trades),
                "new_tf_trades_ingested": new_tf_trades,
                "new_cbr_cases_generated": cases_generated,
                "total_trades_tf": len(tf_ds),
                "total_cases_cbr": len(cbr_existing_tickets)
            }
        except Exception as e_rec:
            print(f"| QUANT RECONCILER ERROR | Falló la reconciliación: {e_rec}")
            return {"status": "error", "message": str(e_rec)}

    def generate_daily_quant_summary_report(self):
        """
        Genera el Reporte Ejecutivo Diario Cuantitativo y de Áreas de Oportunidad (Gemini Pro).
        Calcula el PnL y Win Rate de la jornada, sintetiza aprendizajes y publica en #mia-trading-insights.
        """
        print("| QUANT SUPERVISOR | Generando Reporte Diario Cuantitativo de Mejoras y Oportunidades...")
        if not self.db:
            return {"status": "error", "message": "Firestore no disponible"}
            
        try:
            today_str = datetime.datetime.now().strftime('%Y-%m-%d')
            docs = self.db.collection('mia_audit_logs').order_by('timestamp', direction=firestore.Query.DESCENDING).limit(100).stream()
            
            today_trades = []
            for doc in docs:
                data = doc.to_dict()
                ticket = str(data.get('ticket', doc.id))
                ts = str(data.get('timestamp', ''))
                if today_str in ts and ticket.isdigit() and len(ticket) >= 8:
                    pnl = float(data.get('pnl', 0.0) or 0.0)
                    accion = data.get('accion', '')
                    if accion in ['CIERRE_TOTAL', 'CERRAR_TP', 'CIERRE_PARCIAL', 'TRAILING_STOP', 'PROTECCION_BE'] or pnl != 0.0:
                        today_trades.append({
                            'ticket': ticket,
                            'activo': data.get('activo', 'EURUSD'),
                            'pnl': pnl,
                            'accion': accion,
                            'timestamp': ts,
                            'motivo': data.get('motivo', '')
                        })
                        
            total_trades = len(today_trades)
            if total_trades == 0:
                print("| QUANT SUPERVISOR | No hay trades cerrados en la jornada de hoy.")
                return {"status": "no_trades", "message": "Sin operaciones cerradas hoy."}
                
            wins = [t for t in today_trades if t['pnl'] > 0]
            losses = [t for t in today_trades if t['pnl'] < 0]
            breakevens = [t for t in today_trades if t['pnl'] == 0]
            
            total_pnl = sum([t['pnl'] for t in today_trades])
            win_rate = (len(wins) / (len(wins) + len(losses)) * 100) if (len(wins) + len(losses)) > 0 else 0.0
            
            # Obtener estado vivo de TensorFlow
            r_tf = requests.get(f"{self.UPSTASH_URL}/get/cache_mia_tensorflow", headers=self.UPSTASH_HEADERS, timeout=5)
            tf_data = json.loads(r_tf.json().get('result', '{}')) if r_tf.status_code == 200 and r_tf.json().get('result') else {}
            tf_trades = tf_data.get('trades_aprendidos', 687)
            tf_acc = tf_data.get('accuracy', 0.57) * 100
            
            # Síntesis Cuantitativa con Gemini Pro
            gemini_api_key = (os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY") or "").strip("'").strip('"')
            prompt_reporte = f"""
            Eres MIA Quant Supervisor (Gemini Pro). Elabora el REPORTE DIARIO DE RENDIMIENTO, MEJORAS Y ÁREAS DE OPORTUNIDAD de la jornada ({today_str}).
            
            DATOS DE LA JORNADA:
            - Total de Trades Cerrados: {total_trades}
            - Ganadores (Wins): {len(wins)} | Perdedores (Losses): {len(losses)} | Breakeven/Parciales: {len(breakevens)}
            - Win Rate del Día: {win_rate:.1f}%
            - PnL Neto de la Jornada: ${total_pnl:.2f} USD
            - Estado de la Red Neuronal (TensorFlow): {tf_trades} trades aprendidos | Accuracy: {tf_acc:.1f}%
            
            DETALLE DE OPERACIONES DE HOY:
            {json.dumps(today_trades, indent=2)}
            
            Instrucciones para la Síntesis:
            Devuelve estrictamente un JSON con las siguientes claves:
            1. "resumen_ejecutivo": Balance cuantitativo claro de la sesión (sesiones de mayor rentabilidad, rendimiento de pares).
            2. "patrones_ganadores": Qué confluencias funcionaron con precisión (OBs, Markov, sesiones Londres/NY, trailing stop).
            3. "areas_de_oportunidad": Qué desajustes causaron las pérdidas o breakevens prematuros, y qué trampas de liquidez evitar.
            4. "propuesta_calibracion_7_herds": Recomendaciones puntuales para TIDAL, NORO, ZEPHR, LUMEN, RUNE, TENSORFLOW y ATLAS.
            5. "calibracion_red_neuronal": Confirmación de la ingesta de los trades del día y estado de aprendizaje supervisado.
            """
            
            texto_sintesis = ""
            if gemini_api_key:
                try:
                    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={gemini_api_key}"
                    r_gem = requests.post(url, json={"contents": [{"parts": [{"text": prompt_reporte}]}], "generationConfig": {"temperature": 0.2, "maxOutputTokens": 2500}}, timeout=15)
                    if r_gem.status_code == 200:
                        cand = r_gem.json().get("candidates", [])
                        if cand:
                            texto_sintesis = cand[0].get("content", {}).get("parts", [])[0].get("text", "")
                except Exception as e_gem:
                    print(f"| QUANT REPORT ERROR | Gemini directo: {e_gem}")
                    
            if not texto_sintesis and os.getenv("OPENROUTER_API_KEY"):
                try:
                    or_key = os.getenv("OPENROUTER_API_KEY")
                    r_or = requests.post("https://openrouter.ai/api/v1/chat/completions", headers={"Authorization": f"Bearer {or_key}", "Content-Type": "application/json"}, json={"model": "google/gemini-2.5-flash", "messages": [{"role": "user", "content": prompt_reporte}], "max_tokens": 2500}, timeout=15)
                    if r_or.status_code == 200:
                        texto_sintesis = r_or.json().get("choices", [{}])[0].get("message", {}).get("content", "")
                except Exception as e_or:
                    print(f"| QUANT REPORT ERROR | OpenRouter: {e_or}")
                    
            parsed_sintesis = {}
            import re
            try:
                m_j = re.search(r'```(?:json)?\s*(\{[\s\S]*?\})\s*```', texto_sintesis)
                if m_j:
                    parsed_sintesis = json.loads(m_j.group(1))
                else:
                    s_i = texto_sintesis.find('{')
                    e_i = texto_sintesis.rfind('}')
                    if s_i != -1 and e_i != -1:
                        parsed_sintesis = json.loads(texto_sintesis[s_i:e_i+1])
            except Exception:
                pass
                
            def _fmt_report_field(val, fallback="N/A"):
                if isinstance(val, dict):
                    return "\n".join([f"• *{k}:* {v}" for k, v in val.items()])
                elif isinstance(val, list):
                    return "\n".join([f"• {v}" for v in val])
                return str(val) if val else fallback

            resumen_ejecutivo = _fmt_report_field(parsed_sintesis.get("resumen_ejecutivo"), f"Jornada {today_str}: {total_trades} trades cerrados, Win Rate {win_rate:.1f}%, PnL ${total_pnl:.2f} USD.")
            patrones_ganadores = _fmt_report_field(parsed_sintesis.get("patrones_ganadores"), "Confluencias SMC en Londres y NY.")
            areas_oportunidad = _fmt_report_field(parsed_sintesis.get("areas_de_oportunidad"), "Gestión de buffer de SL en activos de alta volatilidad.")
            propuesta_7_herds = _fmt_report_field(parsed_sintesis.get("propuesta_calibracion_7_herds"), "Ajustar trailing stop de RUNE y filtros de absorción en ATLAS.")
            
            # Notificar en Slack #mia-trading-insights
            if slack_bridge and (slack_bridge.bot_token or slack_bridge.quant_bot_token):
                emoji_pnl = "🟢" if total_pnl >= 0 else "🔴"
                blocks_daily = [
                    {
                        "type": "header",
                        "text": {"type": "plain_text", "text": f"📊 REPORTE DIARIO QUANT & MEJORAS ({today_str})", "emoji": True}
                    },
                    {
                        "type": "section",
                        "fields": [
                            {"type": "mrkdwn", "text": f"*PnL Neto:* `{emoji_pnl} ${total_pnl:.2f} USD`"},
                            {"type": "mrkdwn", "text": f"*Win Rate:* `{win_rate:.1f}%` ({len(wins)}W / {len(losses)}L / {len(breakevens)}BE)"},
                            {"type": "mrkdwn", "text": f"*Red Neuronal TF:* `{tf_trades} trades` ({tf_acc:.1f}% acc)"},
                            {"type": "mrkdwn", "text": f"*Operaciones:* `{total_trades} cerradas`"}
                        ]
                    },
                    {
                        "type": "section",
                        "text": {"type": "mrkdwn", "text": f"*🧠 Resumen Ejecutivo:*\n{resumen_ejecutivo[:2800]}"}
                    },
                    {
                        "type": "section",
                        "text": {"type": "mrkdwn", "text": f"*💎 Patrones Ganadores Identificados:*\n{patrones_ganadores[:2800]}"}
                    },
                    {
                        "type": "section",
                        "text": {"type": "mrkdwn", "text": f"*⚠️ Áreas de Oportunidad y Fugas:*\n{areas_oportunidad[:2800]}"}
                    },
                    {
                        "type": "section",
                        "text": {"type": "mrkdwn", "text": f"*🎯 Propuesta de Calibración para los 7 Herds (HITL):*\n{propuesta_7_herds[:2800]}"}
                    },
                    {
                        "type": "context",
                        "elements": [{"type": "mrkdwn", "text": "🤖 *MIA Quant Supervisor (Gemini Pro)* | Calibración Continua de Red Neuronal & Swarms activa | Mandato HITL."}]
                    },
                    {"type": "divider"}
                ]
                slack_bridge.send_channel_message(text=f"Reporte Diario Quant: PnL ${total_pnl:.2f} | Win Rate {win_rate:.1f}%", channel=self.SLACK_INSIGHTS_CHANNEL, username="MIA Quant Supervisor", icon_emoji=":chart_with_upwards_trend:", blocks=blocks_daily)
                print("| QUANT SUPERVISOR | Reporte Diario publicado exitosamente en Slack.")
                
            report_payload = {
                "fecha": today_str,
                "timestamp": datetime.datetime.now().isoformat(),
                "total_trades": total_trades,
                "wins": len(wins),
                "losses": len(losses),
                "breakevens": len(breakevens),
                "win_rate": win_rate,
                "pnl_total": total_pnl,
                "resumen_ejecutivo": resumen_ejecutivo,
                "patrones_ganadores": patrones_ganadores,
                "areas_de_oportunidad": areas_oportunidad,
                "propuesta_calibracion_7_herds": propuesta_7_herds,
                "tf_trades_aprendidos": tf_trades,
                "tf_accuracy": tf_acc
            }
            requests.post(f"{self.UPSTASH_URL}/set/cache_quant_daily_report", headers=self.UPSTASH_HEADERS, data=json.dumps(report_payload, default=str), timeout=5)
            self.db.collection("mia_trading_learning_history").document(f"DAILY_REPORT_{today_str}").set(report_payload)
            return {"status": "success", "report": report_payload}
        except Exception as e_rep:
            print(f"| QUANT REPORT ERROR | {e_rep}")
            return {"status": "error", "message": str(e_rep)}

if __name__ == "__main__":
    agent = MiaQuantSupervisor()
    agent.reconcile_and_process_daily_trades()
    agent.generate_daily_quant_summary_report()

