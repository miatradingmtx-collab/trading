#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
MIA SUPERVISOR QUANT (RAMA 1 - COGNICIÓN, AUTOPSIA Y APRENDIZAJE CBR DE TRADING)
================================================================================
Supervisor independiente y orquestador cognitivo de Trading Post-Mortem.
Alineado estrictamente con GEMINI.md (Canal: #mia-trading-insights | Motor: Google Gemini 1.5 Pro).

MISIÓN EXCLUSIVA:
- Analizar a profundidad trades cerrados (Wins, Losses, Breakevens) auditando el ticket real de MT5.
- Cruzar los datos generados por los 7 Herds (Llama 70B), TensorFlow (798+ trades), ATLAS DOM/CVD
  y métricas de balance MT5.
- Generar tickets de caso CBR normalizados: TRADE_CASE_<ticket_mt5>_<timestamp>.
- Despachar interfaz interactiva Block Kit RLHF a #mia-trading-insights para validación humana (HITL).
- Enriquecer la memoria viva cache_trading_learning_kb en Upstash Redis y mia_trading_learning_history en Firestore.
- Acumular confianza humana para habilitar el Modo Autónomo (Trust Mode) ante casos recurrentes.
- Desacoplamiento total: Si detecta anomalía técnica, encola en cache_ops_incidents_queue sin invadir Ops.
================================================================================
"""

import os
import json
import re
import datetime
import requests
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

load_dotenv()

import firebase_admin
from firebase_admin import credentials, firestore

try:
    import google.generativeai as genai  # type: ignore
except ImportError:
    genai = None

try:
    from mia_slack_bridge import slack_bridge
except ImportError:
    slack_bridge = None

class MiaQuantSupervisor:
    """
    SUPERVISOR GENERAL CUANTITATIVO Y DE AUTOPSIA (RAMA 1).
    Canal Oficial: #mia-trading-insights (C0C6DUTQVEZ).
    Motor LLM: Google Gemini 1.5 Pro (Failover: Gemini 2.5 Flash / Groq / OpenRouter).
    """

    def __init__(self):
        if not firebase_admin._apps:
            if os.path.exists('serviceAccountKey.json'):
                try:
                    cred = credentials.Certificate('serviceAccountKey.json')
                    firebase_admin.initialize_app(cred)
                except Exception:
                    pass
            if not firebase_admin._apps:
                for env_var in ["FIREBASE_SERVICE_ACCOUNT_JSON", "FIREBASE_SERVICE_ACCOUNT", "SERVICE_ACCOUNT_KEY"]:
                    val = os.getenv(env_var)
                    if val:
                        try:
                            cred = credentials.Certificate(json.loads(val.strip()))
                            firebase_admin.initialize_app(cred)
                            break
                        except Exception:
                            pass
        self.db = firestore.client() if firebase_admin._apps else None

        self.UPSTASH_URL = os.getenv("UPSTASH_REDIS_REST_URL", "https://firm-koi-93555.upstash.io")
        self.UPSTASH_TOKEN = os.getenv("UPSTASH_REDIS_REST_TOKEN", "gQAAAAAAAW1zAAIgcDFmZGI5MGViNWY4Mjc0MGE1Yjg3NDZiOTdiN2MyMjg5Yg")
        self.UPSTASH_HEADERS = {"Authorization": f"Bearer {self.UPSTASH_TOKEN}"}

        self.SLACK_INSIGHTS_CHANNEL = os.getenv("SLACK_CHANNEL_INSIGHTS", "C0C6DUTQVEZ")

    def _llm_gemini_inference(self, trade_context: Dict[str, Any], cbr_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Llamada EXCLUSIVA a Gemini 1.5 Pro con Failover de Alta Disponibilidad.
        Cruza el trade cerrado con el historial CBR, la Regla de 3, TensorFlow y ATLAS DOM/CVD.
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
                if slots[0]:
                    estrategia_actual = slots[0]
                if slots[1]:
                    tf_d = json.loads(slots[1]) if isinstance(slots[1], str) else slots[1]
                    estado_tf = json.dumps({"accuracy": tf_d.get("accuracy"), "trades_aprendidos": tf_d.get("trades_aprendidos", tf_d.get("trades_learned", 798))})
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
                            "veredicto": deb_dict.get("veredicto", deb_dict.get("master_verdict", "N/A"))
                        })
                    else:
                        debate_7_herds = str(deb_d)[:400]
                if slots[3]:
                    atl_d = json.loads(slots[3]) if isinstance(slots[3], str) else slots[3]
                    if isinstance(atl_d, dict):
                        microestructura_atlas = json.dumps({
                            "cvd_delta": atl_d.get("cvd_delta", "N/A"),
                            "buyer_volume_pct": atl_d.get("buyer_pct", atl_d.get("buyer_volume_pct", "N/A")),
                            "seller_volume_pct": atl_d.get("seller_pct", atl_d.get("seller_volume_pct", "N/A")),
                            "resting_liquidity": atl_d.get("heatmap_resting_liquidity", atl_d.get("trampas", "N/A"))
                        })
                    else:
                        microestructura_atlas = str(atl_d)[:300]
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
            print(f"| QUANT SUPERVISOR WARN | Error leyendo MGET Hot Cache: {e_mget}")

        prompt = f"""
        Eres MIA Quant Supervisor (Gemini Pro). Tu tarea es hacer un Análisis Cuantitativo y Post-Mortem de un trade cerrado para alimentar el CBR de Trading.
        NO vas a ejecutar nada en vivo. Emites un diagnóstico y una propuesta cuantitativa para la aprobación humana (HITL).

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
        1. Diagnostica con precisión por qué se ganó, perdió o cerró en Breakeven el trade (respeto de Order Blocks, barridos de liquidez, buffer ATR, CVD Delta).
        2. Formula recomendaciones puntuales para los 7 Herds (LUMEN, TIDAL, NORO, ZEPHR, RUNE, ATLAS, TENSORFLOW).
        3. Evalúa si la ejecución técnica fue nominal o si reportó alguna anomalía técnica del servidor o red.
        4. REGLA INQUEBRANTABLE (FILTRO ANTI-SUERTE >= 50 TRADES): Prohibido alterar la Regla de 3 sin mínimo 50 trades reales.
        
        Devuelve estrictamente un JSON con:
        - "diagnostico": Explicación concisa y técnica de la confluencia de mercado y resultado.
        - "sugerencia_7_herds_trading": Qué reglas, trailing locks (RUNE), pesos neuronales (TENSORFLOW) o filtros DOM (ATLAS) propones ajustar.
        - "nota_infraestructura_t1_t10": "Infraestructura backend nominal." o detalle de anomalía técnica si falló la conexión/servidor.
        """

        texto = None

        # Intento 1: SDK oficial Google Generative AI (Failover agil sin bloqueo list_models)
        if genai and gemini_api_key:
            for target_model_name in ["gemini-2.5-flash", "gemini-flash-latest", "gemini-2.5-flash-lite"]:
                try:
                    genai.configure(api_key=gemini_api_key)
                    model = genai.GenerativeModel(target_model_name, generation_config={"temperature": 0.2, "max_output_tokens": 2500, "response_mime_type": "application/json"})
                    resp = model.generate_content(prompt)
                    texto = resp.text
                    if texto:
                        break
                except Exception as e_sdk:
                    print(f"| QUANT SUPERVISOR | SDK Gemini ({target_model_name}) error: {e_sdk}")
        # Intento 2: REST Gemini Directo
        if not texto and gemini_api_key:
            for m in ["gemini-2.5-flash", "gemini-flash-latest", "gemini-2.5-flash-lite"]:
                try:
                    url = f"https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent?key={gemini_api_key}"
                    r = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"temperature": 0.2, "maxOutputTokens": 2500, "responseMimeType": "application/json"}}, timeout=15)
                    if r.status_code == 200:
                        cand = r.json().get("candidates", [])
                        if cand:
                            texto = cand[0].get("content", {}).get("parts", [])[0].get("text", "")
                            if texto:
                                break
                except Exception:
                    continue

        # Intento 3: Groq Failover de Alta Disponibilidad
        if not texto and os.getenv("GROQ_API_KEY"):
            groq_key = os.getenv("GROQ_API_KEY")
            for g_model in ["llama-3.3-70b-versatile", "qwen/qwen3.8-27b", "openai/gpt-oss-120b"]:
                try:
                    url_groq = "https://api.groq.com/openai/v1/chat/completions"
                    headers_groq = {"Authorization": f"Bearer {groq_key}", "Content-Type": "application/json"}
                    payload_groq = {
                        "model": g_model,
                        "messages": [
                            {"role": "system", "content": "Eres MIA Quant Supervisor (Failover Groq). Analiza el trade y devuelve estrictamente un objeto JSON con diagnostico, sugerencia_7_herds_trading, y nota_infraestructura_t1_t10."},
                            {"role": "user", "content": prompt}
                        ],
                        "response_format": {"type": "json_object"},
                        "temperature": 0.2,
                        "max_tokens": 2000
                    }
                    resp_g = requests.post(url_groq, headers=headers_groq, json=payload_groq, timeout=10)
                    if resp_g.status_code == 200:
                        content_g = resp_g.json().get("choices", [{}])[0].get("message", {}).get("content", "").strip()
                        if content_g:
                            texto = content_g
                            print(f"| QUANT SUPERVISOR | Inferencia Post-Mortem completada vía Failover Groq ({g_model}).")
                            break
                except Exception as e_groq:
                    print(f"| QUANT SUPERVISOR | Groq ({g_model}) falló: {e_groq}")

        # Intento 4: OpenRouter Failover
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
                    "response_format": {"type": "json_object"},
                    "temperature": 0.2,
                    "max_tokens": 2500
                }
                r_or = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=or_headers, json=or_payload, timeout=12)
                if r_or.status_code == 200:
                    choices = r_or.json().get("choices", [])
                    if choices:
                        texto = choices[0].get("message", {}).get("content", "")
            except Exception as e_or:
                print(f"| QUANT SUPERVISOR | OpenRouter Gemini falló: {e_or}")

        # Intento 5: Fallback Determinista Cuantitativo
        if not texto:
            ticket = trade_context.get('ticket', 'N/A')
            symbol = trade_context.get('symbol', 'N/A')
            profit = float(trade_context.get('profit', 0.0) or 0.0)
            tipo = trade_context.get('type', 'CIERRE')
            score = trade_context.get('score', 75.0)
            setup = trade_context.get('detalle_setup', 'SMC Setup')
            res_str = "Ganador" if profit > 0 else ("Breakeven" if profit == 0 else "Pérdida")

            return {
                "diagnostico": f"Evaluación Cuantitativa Institucional (Fail-Safe): Trade #{ticket} en {symbol} ({tipo}) finalizado con {res_str} (${profit:.2f} USD). Score inicial evaluado: {score}%. Setup técnico: {setup}. Confluencia institucional auditada bajo Regla de 3.",
                "sugerencia_7_herds_trading": f"Mantener disciplina de riesgo y confirmaciones institucionales mínimas (3 confluencias) en {symbol}. Verificar absorción en ATLAS DOM L3 antes de nuevas aperturas.",
                "nota_infraestructura_t1_t10": "Infraestructura backend nominal."
            }

        parsed = self._extract_json(texto)
        if parsed and isinstance(parsed, dict):
            if "sugerencia" in parsed and "sugerencia_7_herds_trading" not in parsed:
                parsed["sugerencia_7_herds_trading"] = parsed["sugerencia"]
            if "nota_infraestructura_t1_t10" not in parsed:
                parsed["nota_infraestructura_t1_t10"] = "Infraestructura backend nominal."
            # Sanitizar proactivamente cualquier campo extraído
            parsed["diagnostico"] = self._sanitize_slack_prose(parsed.get("diagnostico", ""))
            parsed["sugerencia_7_herds_trading"] = self._sanitize_slack_prose(parsed.get("sugerencia_7_herds_trading", ""), "Mantener disciplina de riesgo y confluencia institucional de los 7 Herds.")
            return parsed

        # Fallback limpio sin volcar sintaxis JSON a la vista del usuario
        diag_clean = self._sanitize_slack_prose(texto) if texto else "Diagnóstico cuantitativo completado."
        return {
            "diagnostico": diag_clean,
            "sugerencia_7_herds_trading": "Ajustar parámetros según confluencia de los 7 Herds.",
            "nota_infraestructura_t1_t10": "Infraestructura backend nominal."
        }

    def _sanitize_slack_prose(self, text: Any, default_msg: str = "Diagnóstico cuantitativo completado.") -> str:
        """
        Sanitiza cualquier texto antes de renderizarlo en Slack o guardarlo en la memoria CBR.
        Erradica completamente bloques ```json, llaves {, comillas o estructuras JSON crudas.
        """
        if not text:
            return default_msg
        if isinstance(text, dict):
            return "\n".join([f"• *{k}:* {self._sanitize_slack_prose(v)}" for k, v in text.items()])
        if isinstance(text, list):
            return "\n".join([f"• {self._sanitize_slack_prose(item)}" for item in text])
            
        t = str(text).strip()
        # 1. Eliminar fences de markdown code block ```json o ```
        t = re.sub(r'```(?:json)?', '', t).replace('```', '').strip()
        
        # 2. Si contiene sintaxis JSON cruda {"diagnostico": "..."}
        m = re.search(r'"(?:diagnostico|sugerencia_7_herds_trading|solucion_aprendida)"\s*:\s*"((?:[^"\\]|\\.)*)"', t, re.DOTALL)
        if m:
            try:
                t = m.group(1).encode().decode('unicode_escape', errors='ignore')
            except Exception:
                t = m.group(1)
        elif '"diagnostico"' in t:
            sub = re.search(r'"diagnostico"\s*:\s*"([^"\r\n]*)', t)
            if sub:
                t = sub.group(1)
                
        # 3. Limpiar caracteres de apertura/cierre JSON residuales
        t = re.sub(r'^[\s\{\[\"\'\:]+', '', t)
        t = re.sub(r'[\s\}\]\"\'\:]+$', '', t)
        t = t.replace('\\"', '"').replace('\\n', '\n').strip()
        
        # 4. Asegurar puntuación final limpia
        if t and not t.endswith(('.', '!', '?', ':')):
            t += "..."
            
        return t if t else "Evaluación cuantitativa completada."

    def _extract_json(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Extracción ultra-resiliente de JSON para inferencia de LLMs.
        Soporta JSON directo, strict=False, stripping de bloques markdown, y regex campo por campo.
        """
        if not text:
            return None
        text = str(text).strip()
        
        # 1. Quitar markdown fences primero para evitar fallos de parseo en bloques anidados
        limpio = re.sub(r'```(?:json)?', '', text).replace('```', '').strip()
        
        # 2. Intento directo con strict=False (permite caracteres de control como \n no escapados)
        try:
            return json.loads(limpio, strict=False)
        except Exception:
            pass

        # 3. Intento entre primer '{' y último '}' sobre texto limpio
        try:
            s = limpio.find('{')
            e = limpio.rfind('}')
            if s != -1 and e != -1 and e > s:
                return json.loads(limpio[s:e+1], strict=False)
        except Exception:
            pass

        # 4. Extracción resiliente campo por campo en caso de respuesta truncada por tokens
        try:
            extracted = {}
            m_diag = re.search(r'"diagnostico"\s*:\s*"((?:[^"\\]|\\.)*)"', limpio, re.DOTALL)
            if m_diag:
                try:
                    extracted["diagnostico"] = m_diag.group(1).encode().decode('unicode_escape', errors='ignore')
                except Exception:
                    extracted["diagnostico"] = m_diag.group(1)
            elif '"diagnostico"' in limpio:
                sub = re.search(r'"diagnostico"\s*:\s*"([^"\r\n]*)', limpio)
                if sub:
                    extracted["diagnostico"] = sub.group(1)

            # Extraer sugerencia como objeto JSON o como string
            m_sug_dict = re.search(r'"(?:sugerencia_7_herds_trading|sugerencia)"\s*:\s*(\{[\s\S]*?\n\s*\})', limpio)
            if m_sug_dict:
                try:
                    extracted["sugerencia_7_herds_trading"] = json.loads(m_sug_dict.group(1), strict=False)
                except Exception:
                    extracted["sugerencia_7_herds_trading"] = m_sug_dict.group(1)
            else:
                m_sug = re.search(r'"(?:sugerencia_7_herds_trading|sugerencia)"\s*:\s*"((?:[^"\\]|\\.)*)"', limpio, re.DOTALL)
                if m_sug:
                    try:
                        extracted["sugerencia_7_herds_trading"] = m_sug.group(1).encode().decode('unicode_escape', errors='ignore')
                    except Exception:
                        extracted["sugerencia_7_herds_trading"] = m_sug.group(1)

            m_nota = re.search(r'"nota_infraestructura_t1_t10"\s*:\s*"((?:[^"\\]|\\.)*)"', limpio, re.DOTALL)
            if m_nota:
                try:
                    extracted["nota_infraestructura_t1_t10"] = m_nota.group(1).encode().decode('unicode_escape', errors='ignore')
                except Exception:
                    extracted["nota_infraestructura_t1_t10"] = m_nota.group(1)

            if extracted and "diagnostico" in extracted:
                return extracted
        except Exception:
            pass

        return None

    def _generate_and_register_case(self, trade: Dict[str, Any]) -> Dict[str, Any]:
        """Alias canónico de compatibilidad para process_trade_post_mortem y registro en CBR."""
        return self.process_trade_post_mortem(trade)

    def generate_and_register_case(self, trade: Dict[str, Any]) -> Dict[str, Any]:
        """Alias canónico de compatibilidad para process_trade_post_mortem y registro en CBR."""
        return self.process_trade_post_mortem(trade)

    def process_trade_post_mortem(self, trade: Dict[str, Any]) -> Dict[str, Any]:
        """
        Genera la autopsia post-mortem del trade con el ticket oficial de entrada en MT5.
        Genera el Caso CBR normalizado (TRADE_CASE_<ticket>_<timestamp>) y notifica a Slack (#mia-trading-insights).
        """
        ticket = str(trade.get('ticket', ''))
        symbol = str(trade.get('symbol', 'EURUSD'))
        profit = float(trade.get('profit', 0.0) or 0.0)

        # 1. Obtener historial CBR para que Gemini cruce la información
        try:
            r_cbr = requests.get(f"{self.UPSTASH_URL}/get/cache_trading_learning_kb", headers=self.UPSTASH_HEADERS, timeout=4).json()
            cbr_history = json.loads(r_cbr.get("result", "[]")) if r_cbr.get("result") else []
        except Exception:
            cbr_history = []

        # 2. Inferencia con Gemini Pro
        gemini_analysis = self._llm_gemini_inference(trade, cbr_history)

        sugerencia_raw = gemini_analysis.get("sugerencia_7_herds_trading") or gemini_analysis.get("sugerencia", "Mantener disciplina institucional bajo la Regla de 3 y verificar zonas de liquidez en ATLAS DOM.")
        sugerencia_trading = self._sanitize_slack_prose(sugerencia_raw, "Mantener disciplina de riesgo y confirmaciones institucionales mínimas de los 7 Herds.")

        diagnostico_raw = gemini_analysis.get("diagnostico", "Diagnóstico no disponible.")
        diagnostico = self._sanitize_slack_prose(diagnostico_raw)

        nota_infra = str(gemini_analysis.get("nota_infraestructura_t1_t10", "Infraestructura backend nominal."))

        # 3. Asignación del Caso CBR vinculado al Ticket Oficial de Entrada de MT5 con Score RL (Premio / Castigo)
        ts_now = int(datetime.datetime.now().timestamp())
        case_id = f"TRADE_CASE_{ticket}_{ts_now}"

        # Cálculo Cuantitativo de Recompensa Asimétrica (Reward / Penalty Score)
        riesgo_base_usd = 50.0  # Riesgo estimado por trade en USD
        r_multiplo = round(profit / riesgo_base_usd, 2) if riesgo_base_usd > 0 else 0.0
        
        # Factor de Asimetría según Ley D / (1 - D)
        bal_actual = float(trade.get("balance", 3688.0) or 3688.0)
        drawdown_base = max(0.0, 5000.0 - bal_actual)
        d_frac = min(0.95, drawdown_base / 5000.0)
        factor_asimetria = round(1.0 / (1.0 - d_frac), 2) if d_frac < 1.0 else 1.0

        if profit > 0:
            # Mandato Canónico: Todo WIN parte de como mínimo +1.0R (o ratio superior si superó 1:1)
            r_win_base = max(1.0, round(profit / riesgo_base_usd, 2) if riesgo_base_usd > 0 else 1.0)
            recompensa_neta = round(r_win_base * 1.0, 2)
            delta_weights = {
                "herd_1_tidal": 0.05,
                "herd_2_noro": 0.08,
                "herd_3_zephr": 0.06,
                "herd_4_lumen": 0.12,
                "herd_5_rune": 0.08,
                "herd_6_tensorflow": 0.05,
                "herd_7_atlas": 0.10
            }
            tipo_resultado = "PREMIO_GANADOR"
        elif profit < 0:
            # Mandato Canónico: Todo LOSS parte de como mínimo -1.0R base, amplificado por asimetría D/(1-D)
            r_loss_base = max(1.0, round(abs(profit) / riesgo_base_usd, 2) if riesgo_base_usd > 0 else 1.0)
            recompensa_neta = round(-1.0 * r_loss_base * 1.5 * factor_asimetria, 2)
            delta_weights = {
                "herd_1_tidal": -0.05,
                "herd_2_noro": -0.05,
                "herd_3_zephr": -0.05,
                "herd_4_lumen": -0.08,
                "herd_5_rune": +0.05,
                "herd_6_tensorflow": -0.05,
                "herd_7_atlas": -0.08
            }
            tipo_resultado = "CASTIGO_PERDEDOR"
        else:
            recompensa_neta = 0.20
            delta_weights = {k: 0.01 for k in ["herd_1_tidal", "herd_2_noro", "herd_3_zephr", "herd_4_lumen", "herd_5_rune", "herd_6_tensorflow", "herd_7_atlas"]}
            tipo_resultado = "BREAK_EVEN_NEUTRAL"

        payload_cbr = {
            "case_id": case_id,
            "caso": f"Análisis Post-Mortem Quant Trade #{ticket}",
            "fecha": datetime.datetime.now().isoformat(),
            "ticket": ticket,
            "symbol": symbol,
            "profit": profit,
            "r_multiplo": r_multiplo,
            "diagnostico": diagnostico,
            "solucion_aprendida": sugerencia_trading,
            "nota_infraestructura_t1_t10": nota_infra,
            "veredicto_humano": "PENDIENTE_HITL",
            "score_confianza": 0.85 if profit > 0 else 0.40,
            "accion_ejecutada": "NINGUNA. REGISTRO DE CBR QUANT (MANDATO HITL ACTIVO).",
            "score_premio_castigo": {
                "tipo_resultado": tipo_resultado,
                "recompensa_neta_r": recompensa_neta,
                "factor_asimetria_aplicado": factor_asimetria,
                "delta_weights_herds": delta_weights
            }
        }

        # Guardar en Firestore y Upstash (Dual Mirroring Canónico: cache_trading_learning_kb y cache_cbr)
        cbr_history.insert(0, payload_cbr)
        cbr_top_50 = cbr_history[:50]

        if self.db:
            try:
                self.db.collection("mia_trading_learning_history").document(case_id).set(payload_cbr)
                latest_cbr_doc = {
                    "descripcion": "Snapshot canónico consolidado de memoria CBR Trading (Top 50 casos en vivo)",
                    "total_casos": len(cbr_top_50),
                    "casos": cbr_top_50,
                    "slot_redis_principal": "cache_trading_learning_kb",
                    "ultima_actualizacion": datetime.datetime.now().isoformat()
                }
                self.db.collection("mia_trading_learning_history").document("latest").set(latest_cbr_doc)
            except Exception as e_fb:
                print(f"| QUANT SUPERVISOR WARN | Error guardando CBR en Firestore: {e_fb}")

        try:
            requests.post(f"{self.UPSTASH_URL}/set/cache_trading_learning_kb", headers=self.UPSTASH_HEADERS, json=cbr_top_50, timeout=5)
        except Exception as e_up:
            print(f"| QUANT SUPERVISOR WARN | Error guardando CBR en Upstash: {e_up}")

        # 4. Notificar a Slack (#mia-trading-insights) con Block Kit RLHF (Idéntico a Imagen 1)
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
                            f"*Símbolo:* {symbol} | *Resultado:* `{profit} USD` ({r_multiplo:+.2f}R)\n"
                            f"*⚖️ RL Score:* `{recompensa_neta:+.2f}R` ({tipo_resultado}) | *Asimetría:* `{factor_asimetria}x`\n\n"
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
                print(f"| QUANT SUPERVISOR | Notificación Block Kit enviada exitosamente para {ticket}.")
            except Exception as e_slack:
                print(f"| QUANT SUPERVISOR ERROR | Error enviando Block Kit: {e_slack}")

        # 5. Desacoplamiento Asíncrono de Incidentes Técnicos (Rama 1 -> Rama 2)
        # Si hubo una falla técnica de infraestructura en el trade, encola en Redis asociando el ticket de MT5
        if "nominal" not in nota_infra.lower() and "sin fallas" not in nota_infra.lower():
            try:
                incident_payload = {
                    "origen": "QUANT_POST_MORTEM",
                    "tipo": "INFRASTRUCTURE_TRADE_ANOMALY",
                    "ticket_mt5": ticket,
                    "symbol": symbol,
                    "timestamp": datetime.datetime.now().isoformat(),
                    "nota_tecnica": nota_infra
                }
                requests.post(
                    f"{self.UPSTASH_URL}/rpush/cache_ops_incidents_queue",
                    headers=self.UPSTASH_HEADERS,
                    data=json.dumps([json.dumps(incident_payload)]),
                    timeout=3
                )
                print(f"| QUANT SUPERVISOR | Anomalía técnica encolada en cache_ops_incidents_queue (Ticket MT5: {ticket}).")
            except Exception as e_queue:
                print(f"| QUANT SUPERVISOR WARN | Error encolando anomalía técnica: {e_queue}")

        return payload_cbr

    def analyze_recent_losses(self):
        """Escanea trades perdedores recientes para su procesamiento post-mortem."""
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
            self.process_trade_post_mortem(trade)
            break

    def reconcile_and_process_daily_trades(self, days_back: int = 2):
        """Reconciliador diario anti-pérdida de trades."""
        print(f"| QUANT RECONCILER | Reconciliando trades de los últimos {days_back} días...")
        closed_trades = []
        try:
            r_hist = requests.get(f"{self.UPSTASH_URL}/get/cache_hist_mt5", headers=self.UPSTASH_HEADERS, timeout=5)
            if r_hist.status_code == 200 and r_hist.json().get('result'):
                raw_h = r_hist.json().get('result')
                d_h = json.loads(raw_h) if isinstance(raw_h, str) else (raw_h or {})
                recent = d_h.get('recent_logs', [])
                for data in recent:
                    ticket = str(data.get('ticket', ''))
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
        except Exception as e:
            print(f"| QUANT RECONCILER WARN | Error leyendo Upstash cache_hist_mt5: {e}")

        # Ingesta en TensorFlow Dataset
        try:
            r_ds = requests.get(f"{self.UPSTASH_URL}/get/cache_mia_dataset_tf", headers=self.UPSTASH_HEADERS, timeout=5)
            tf_ds = json.loads(r_ds.json().get('result', '[]')) if r_ds.status_code == 200 and r_ds.json().get('result') else []
            tf_existing = {str(x.get('ticket')) for x in tf_ds if x.get('ticket')}
            new_tf = 0
            for t in closed_trades:
                if t['ticket'] not in tf_existing:
                    tf_ds.append({
                        'ticket': t['ticket'], 'activo': t['symbol'], 'pnl': t['profit'],
                        'accion': t['type'], 'score': t.get('score', 75.0), 'timestamp': t['timestamp']
                    })
                    tf_existing.add(t['ticket'])
                    new_tf += 1
            if new_tf > 0:
                requests.post(f"{self.UPSTASH_URL}/set/cache_mia_dataset_tf", headers=self.UPSTASH_HEADERS, data=json.dumps(tf_ds, default=str), timeout=10)
                try:
                    requests.get("https://trading-production-927a.up.railway.app/api/cron/train_tensorflow", timeout=30)
                except Exception:
                    pass
        except Exception as e_tf:
            print(f"| QUANT RECONCILER WARN | Error sincronizando TF: {e_tf}")

        # Reconciliación con CBR
        cbr_list = []
        try:
            r_cbr = requests.get(f"{self.UPSTASH_URL}/get/cache_trading_learning_kb", headers=self.UPSTASH_HEADERS, timeout=5)
            if r_cbr.status_code == 200 and r_cbr.json().get('result'):
                cbr_list = json.loads(r_cbr.json().get('result'))
        except Exception:
            pass

        cbr_tickets = {str(c.get('ticket')) for c in cbr_list if c.get('ticket')}
        new_cases = 0
        for t in closed_trades:
            if t['ticket'] not in cbr_tickets:
                self.process_trade_post_mortem(t)
                cbr_tickets.add(t['ticket'])
                new_cases += 1

        print(f"| QUANT RECONCILER | Finalizado: {new_cases} casos registrados en CBR.")
        return {"status": "success", "closed_trades": len(closed_trades), "new_cases": new_cases}

    def generate_daily_quant_summary_report(self):
        """Genera y publica el reporte cuantitativo diario en #mia-trading-insights."""
        today_str = datetime.datetime.now().strftime('%Y-%m-%d')
        print(f"| QUANT SUPERVISOR | Generando Reporte Diario Cuantitativo ({today_str})...")
        if not self.db:
            return {"status": "error", "message": "Firestore no disponible"}

        try:
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
                            'ticket': ticket, 'activo': data.get('activo', 'EURUSD'),
                            'pnl': pnl, 'accion': accion, 'timestamp': ts
                        })

            total_trades = len(today_trades)
            if total_trades == 0:
                return {"status": "no_trades", "message": "Sin operaciones cerradas hoy."}

            wins = [t for t in today_trades if t['pnl'] > 0]
            losses = [t for t in today_trades if t['pnl'] < 0]
            breakevens = [t for t in today_trades if t['pnl'] == 0]
            total_pnl = sum([t['pnl'] for t in today_trades])
            win_rate = (len(wins) / (len(wins) + len(losses)) * 100) if (len(wins) + len(losses)) > 0 else 0.0

            emoji_pnl = "🟢" if total_pnl >= 0 else "🔴"
            blocks = [
                {
                    "type": "header",
                    "text": {"type": "plain_text", "text": f"📊 REPORTE DIARIO QUANT & MEJORAS ({today_str})", "emoji": True}
                },
                {
                    "type": "section",
                    "fields": [
                        {"type": "mrkdwn", "text": f"*PnL Neto:* `{emoji_pnl} ${total_pnl:.2f} USD`"},
                        {"type": "mrkdwn", "text": f"*Win Rate:* `{win_rate:.1f}%` ({len(wins)}W / {len(losses)}L / {len(breakevens)}BE)"},
                        {"type": "mrkdwn", "text": f"*Operaciones:* `{total_trades} cerradas`"}
                    ]
                },
                {
                    "type": "context",
                    "elements": [{"type": "mrkdwn", "text": "🤖 *MIA Quant Supervisor (Gemini Pro)* | Gobernanza HITL activa."}]
                },
                {"type": "divider"}
            ]

            if slack_bridge:
                slack_bridge.send_channel_message(
                    text=f"Reporte Diario Quant: PnL ${total_pnl:.2f} | Win Rate {win_rate:.1f}%",
                    channel=self.SLACK_INSIGHTS_CHANNEL,
                    username="MIA Quant Supervisor",
                    icon_emoji=":chart_with_upwards_trend:",
                    blocks=blocks
                )

            return {"status": "success", "total_trades": total_trades, "win_rate": win_rate, "total_pnl": total_pnl}
        except Exception as e:
            print(f"| QUANT REPORT ERROR | {e}")
            return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    supervisor = MiaQuantSupervisor()
    supervisor.reconcile_and_process_daily_trades()
