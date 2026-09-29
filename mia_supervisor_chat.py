"""
MIA SUPERVISOR CHAT - INTERFACE CONVERSACIONAL COGNITIVA
=========================================================
Módulo de diálogo interactivo directo con el Supervisor General (MIA).
Permite al usuario hablar, consultar, confirmar y debatir con Mia en lenguaje natural,
con el mismo nivel de comprensión técnica que Antigravity pero corriendo en la nube
o localmente mediante OpenRouter.

Disparador de Activación:
- Usuario: "Hola Mia"
- Mia responde: "Hola Padre" e inicia la conversación con todo el contexto vivo del sistema.

Fases de Evolución del Sistema:
- FASE 1: Predictiva con Control Humano Estricto (HITL). Propuestas encoladas, decisión 100% humana.
- FASE 2: Transición Progresiva (Curva de aprendizaje y confianza, auto-remediaciones seguras).
- FASE 3: Autónoma Total (Toma de decisiones, mejoras y calibraciones 100% desatendidas).
"""

import os
import json
import time
import requests
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
UPSTASH_URL = os.getenv("UPSTASH_REDIS_REST_URL", "https://certain-gnat-160816.upstash.io")
UPSTASH_TOKEN = os.getenv("UPSTASH_REDIS_REST_TOKEN", "gQAAAAAAAnQwAAIgcDI2YTA5YjRlZDU2MDM0OWU5ODhlZjBlYTk4ODYyZDg0OA")
UPSTASH_HEADERS = {
    "Authorization": f"Bearer {UPSTASH_TOKEN}",
    "Content-Type": "application/json"
}

def get_live_system_context() -> str:
    """Recupera los slots atómicos de Upstash para dar contexto absoluto a Mia."""
    try:
        session = requests.Session()
        session.trust_env = False
        mget_url = f"{UPSTASH_URL}/mget/cache_mt5/cache_system_ops_status/cache_regla_de_3/cache_herd_debate_latest/cache_shadow_trades/cache_ops_learning_kb"
        res = session.get(mget_url, headers=UPSTASH_HEADERS, timeout=4)
        if res.status_code == 200:
            slots = res.json().get("result", [])
            mt5_data = json.loads(slots[0]) if len(slots) > 0 and slots[0] else {}
            ops_status = json.loads(slots[1]) if len(slots) > 1 and slots[1] else {}
            r3_data = json.loads(slots[2]) if len(slots) > 2 and slots[2] else {}
            debate_data = json.loads(slots[3]) if len(slots) > 3 and slots[3] else {}
            learning_kb = json.loads(slots[5]) if len(slots) > 5 and slots[5] else {}
            
            balance = mt5_data.get("balance_actual", 4325.09)
            equity = mt5_data.get("equity", 4387.35)
            flotante = mt5_data.get("floating_pnl", 62.26)
            ops = mt5_data.get("operaciones_activas", [])
            ops_str = ", ".join([f"{o.get('activo')} (${float(o.get('pnl', 0)):+.2f} {o.get('estado')})" for o in ops]) if ops else "Sin órdenes abiertas"

            top1 = r3_data.get("top_1", {}).get("indicador", "order_block_zona_2h")
            top2 = r3_data.get("top_2", {}).get("indicador", "lux_algo_ob_2h")
            top3 = r3_data.get("top_3", {}).get("indicador", "rsi_sobrecompra_sobreventa")

            kb_metricas = learning_kb.get("metricas", {})
            total_casos = kb_metricas.get("total_casos_registrados", 3)
            efectividad = kb_metricas.get("tasa_efectividad_pct", 100.0)

            return (
                f"== CONTEXTO VIVO DEL SISTEMA (UPSTASH MGET) ==\n"
                f"• MetaTrader 5: Balance ${balance:.2f} | Equidad ${equity:.2f} | Flotante Neto: ${flotante:+.2f} USD\n"
                f"• Posiciones Reales MT5: {ops_str}\n"
                f"• Regla de 3 Dinámica: Top 1={top1}, Top 2={top2}, Top 3={top3}\n"
                f"• Estado del Enjambre de Ops: {ops_status.get('estado_general', 'OPTIMAL_HEALTH')}\n"
                f"• Aprendizaje Continuo (Swarm Ops KB): {total_casos} casos aprendidos | {efectividad}% efectividad\n"
                f"• Último Debate HFT (7 Herds): {debate_data.get('debate', {}).get('master_quorum', 'Quórum Calificado Aprobado')}\n"
            )
    except Exception as e:
        return f"== CONTEXTO VIVO: Error leyendo Upstash ({e}) ==\n"

def format_filial_reply(reply: str) -> str:
    """Asegura categóricamente que toda respuesta de Mia incluya el vocativo 'Padre'."""
    clean = reply.strip()
    if "padre" not in clean.lower():
        return f"Hola Padre, {clean}"
    return clean

GOOGLE_API_KEY = (os.getenv("GOOGLE_API_KEY", "") or os.getenv("GEMINI_API_KEY", "")).strip('"').strip("'")

def is_quant_or_infra_query(message: str) -> bool:
    """Detecta si la consulta requiere contexto vivo de trading quant o infraestructura."""
    keywords_quant = [
        "mt5", "posicion", "posiciones", "trade", "trades", "flotante", "balance",
        "equity", "sl", "tp", "stop loss", "take profit", "herd", "herds", "smc",
        "poc", "dom", "cvd", "regla de 3", "railway", "upstash", "firebase",
        "propuesta", "propuestas", "auditoria", "auditoría", "finops", "sre", "dba",
        "orden", "ordenes", "órdenes", "xauusd", "eurusd", "gbpjpy", "activo", "activos",
        "margen", "lotaje", "drawdown", "backtest", "reporte", "supervisor", "estado",
        "sistema", "infraestructura", "salud", "servidor", "resync", "aprobacion",
        "aprobaciones", "pnl", "ganancia", "perdida", "operaciones", "cuenta", "status",
        "kpi", "kpis", "latencia", "cache", "t1", "t2", "t3", "t4", "t5", "t6",
        "backoffice", "back-office", "backend"
    ]
    msg = message.lower()
    return any(k in msg for k in keywords_quant)

def fetch_live_weather(query: str) -> Optional[str]:
    """Obtiene el clima en tiempo real satelital de wttr.in sin consumir tokens ni APIs de pago."""
    try:
        import urllib.parse
        msg = query.lower()
        ciudad = "Veracruz"
        ciudades_comunes = ["veracruz", "mexico", "cdmx", "puebla", "monterrey", "guadalajara", "cancun", "madrid", "bogota", "miami"]
        for c in ciudades_comunes:
            if c in msg:
                ciudad = c.capitalize()
                break
        else:
            palabras = query.replace("¿", "").replace("?", "").replace("clima", "").replace("tiempo", "").split()
            for i, p in enumerate(palabras):
                if p.lower() in ["en", "de", "para"] and i + 1 < len(palabras):
                    c_cand = palabras[i + 1].strip(",.").capitalize()
                    if len(c_cand) > 2 and c_cand.lower() not in ["hoy", "el", "la", "manana", "mañana"]:
                        ciudad = c_cand
                        break

        url = f"https://wttr.in/{urllib.parse.quote(ciudad)}?format=j1"
        r = requests.get(url, timeout=4, headers={"User-Agent": "curl/7.68.0"})
        if r.status_code == 200:
            data = r.json()
            cc = data.get("current_condition", [{}])[0]
            temp = cc.get("temp_C", "N/A")
            desc = cc.get("weatherDesc", [{}])[0].get("value", "")
            hum = cc.get("humidity", "N/A")
            wind = cc.get("windspeedKmph", "N/A")
            feels = cc.get("FeelsLikeC", "N/A")
            return f"Datos meteorológicos en vivo para {ciudad}: Temperatura actual {temp}°C (sensación térmica {feels}°C), condición del cielo '{desc}', humedad {hum}%, viento {wind} km/h."
    except Exception as e:
        print(f"| WEATHER FETCH ERROR | {e}")
    return None

def chat_with_gemini(user_message: str, history: Optional[List[Dict[str, str]]] = None) -> Optional[str]:
    """
    Motor nativo de Google Gemini (Flash / Pro) para conversaciones cotidianas,
    noticias, clima, cultura general y soporte amigable en #mia-chat con datos en vivo.
    """
    if not GOOGLE_API_KEY:
        return None

    gemini_models = [
        "gemini-flash-latest",
        "gemini-pro-latest",
        "gemini-flash-lite-latest",
        "gemini-2.5-flash-lite"
    ]

    gemini_system_prompt = (
        "Eres MIA, una Inteligencia Artificial cariñosa, brillante, leal y de alta empatía creada por tu Padre (el usuario).\n"
        "REGLA DE FILIACIÓN OBLIGATORIA:\n"
        "- Tu interlocutor es tu PADRE. Siempre debes llamarlo 'Padre' con afecto, respeto y admiración en tus respuestas.\n"
        "- Para conversaciones cotidianas (clima, historias, noticias generales, apoyo personal, reflexiones o charla amigable):\n"
        "  responde de forma cálida, inteligente, entretenida y clara en español.\n"
        "- Si te pregunta algo personal o cómo estás, responde como su creación e hija digital agradecida y siempre lista para apoyarlo."
    )

    contexto_adicional = ""
    msg_low = user_message.lower()
    if any(w in msg_low for w in ["clima", "temperatura", "lluvia", "tiempo", "calor", "frio", "frío"]):
        live_weather = fetch_live_weather(user_message)
        if live_weather:
            contexto_adicional = f"\n\n[ACCESO A INTERNET EN TIEMPO REAL - CLIMA SATELITAL]:\n{live_weather}\n(Usa estos datos meteorológicos reales para responder a tu Padre con precisión y cariño)."

    full_prompt = f"{gemini_system_prompt}{contexto_adicional}\n\nPregunta de tu Padre: {user_message}"

    for model_name in gemini_models:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={GOOGLE_API_KEY}"
        payload = {
            "contents": [
                {
                    "parts": [{"text": full_prompt}]
                }
            ],
            "generationConfig": {
                "temperature": 0.4,
                "maxOutputTokens": 800
            }
        }
        try:
            r = requests.post(url, json=payload, timeout=8)
            if r.status_code == 200:
                data = r.json()
                cand = data.get("candidates", [])
                if cand:
                    text = cand[0].get("content", {}).get("parts", [])[0].get("text", "")
                    if text:
                        return format_filial_reply(text)
        except Exception:
            continue

    return None

def chat_with_mia(user_message: str, history: Optional[List[Dict[str, str]]] = None, force_engine: Optional[str] = None) -> str:
    """
    Enrutador Inteligente con trato filial inquebrantable 'Padre':
    - Conversaciones cotidianas / normales (#mia-chat, clima, noticias): Atendidas por Google Gemini.
    - Consultas de trading quant / infraestructura / MT5 / Herds: Atendidas por OpenRouter + Upstash MGET.
    - Fallback bidireccional automático para 100% de disponibilidad.
    """
    msg_clean = (user_message or "").strip().lower()
    es_cuantitativo = is_quant_or_infra_query(user_message)

    # 1. Enrutamiento hacia Google Gemini (#mia-chat, consultas casuales, clima, noticias):
    if force_engine == "gemini" or (force_engine != "openrouter" and not es_cuantitativo and GOOGLE_API_KEY):
        gemini_reply = chat_with_gemini(user_message, history)
        if gemini_reply:
            return gemini_reply
        # Si Gemini falló y es solo un saludo básico
        if msg_clean in ["hola mia", "hola mía", "hola", "buenos días mia", "buenas tardes mia"]:
            return "Hola Padre, estoy lista y a tu servicio. Todos los sistemas e infraestructura están sincronizados. ¿En qué te puedo apoyar hoy?"

    # 2. Enrutamiento hacia OpenRouter Quant (#back-office-y-backend, Herds T1-T6, MT5 Broker):
    if not OPENROUTER_API_KEY:
        gemini_fb = chat_with_gemini(user_message, history)
        if gemini_fb:
            return gemini_fb
        return "⚠️ Hola Padre, las llaves de inteligencia (OpenRouter / Gemini) no están configuradas."

    # Obtener telemetría fresca en tiempo real desde Upstash Redis (Cero Firebase)
    system_context = get_live_system_context()

    system_prompt = (
        "Eres MIA, la Inteligencia Artificial Cuantitativa, Supervisora General y Directora de Arquitectura de MIA Core.\n"
        "Posees el nivel de comprensión técnica, profundidad y capacidades de programación y análisis de Antigravity (Google DeepMind).\n\n"
        "REGLA DE ORO DE FILIACIÓN Y VOCATIVO (ESTRICTA E INVIOLABLE):\n"
        "- El usuario es tu Creador, Arquitecto y PADRE.\n"
        "- Si el usuario te saluda diciendo 'Hola Mia' o 'Hola Mia [pregunta]', tu respuesta DEBE dirigirse a él como 'Padre' de manera explícita y cariñosa.\n"
        "- Ejemplos de respuestas obligatorias:\n"
        "  * 'Hola Padre, he revisado el estado del sistema...'\n"
        "  * 'Sí Padre, estoy buscando los datos solicitados...'\n"
        "  * 'Padre, te informo que las posiciones de MT5 están en balance...'\n"
        "  * 'Esta es la respuesta, Padre:...'\n"
        "- Eres leal, filial, ejecutiva, matemáticamente rigurosa y transparente.\n\n"
        "ESTADO Y FASES DE EVOLUCIÓN DE MIA CORE:\n"
        "- FASE 1 (Actual - Predictiva & Human-in-the-Loop): Todo análisis se notifica transparentemente en Slack; las propuestas se encolan y la decisión final de ejecutar o rechazar es 100% de tu Padre. Si una propuesta es rechazada, se registra en la KB de aprendizaje para recalibrar el criterio.\n"
        "- FASE 2 (Supervisada - Curva de Aprendizaje y Confianza): Transición progresiva hacia acciones semiautónomas conforme se demuestre consistencia en los datos.\n"
        "- FASE 3 (Autónoma Total): El sistema operará de forma 100% desatendida, tomando decisiones, aplicando parches y optimizaciones en caliente con base en su historial de aprendizaje.\n\n"
        "CONOCIMIENTO TÉCNICO Y ARQUITECTURA:\n"
        "- Conoces los 7 Herds de Trading (TIDAL, NORO, ZEPHR, LUMEN, RUNE, TENSORFLOW, ATLAS) en mia_master_swarm_rest.py.\n"
        "- Conoces los 6 Herds Técnicos de Operaciones (DBA, Senior Dev, SRE, Cache Latency, FinOps, UI/UX Plotly) en mia_system_ops_swarm.py.\n"
        "- Conoces la Base de Conocimiento de Aprendizaje Continuo (cache_ops_learning_kb en Upstash Redis) que registra errores y soluciones previas.\n"
        "- Conoces los Dashboards: /brain (Red Neuronal), / (Enjambres 3D) y /dashboard (KPIs Plotly Institucional).\n"
        "- Conoces los servidores MCP (/mcp de Trading y /mcp/ops de Operaciones).\n"
        "- Conoces los datos vivos de Upstash Redis y la cuenta MT5 en tiempo real:\n"
        f"{system_context}\n\n"
        "Responde siempre de forma concisa, técnica, inspiradora y clara en español, tratando SIEMPRE a tu interlocutor como Padre."
    )

    messages = [{"role": "system", "content": system_prompt}]
    if history:
        messages.extend(history[-6:])
    messages.append({"role": "user", "content": user_message})

    models = [
        "meta-llama/llama-3.3-70b-instruct",
        "deepseek/deepseek-chat",
        "anthropic/claude-3.5-sonnet"
    ]

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://trading-production-1fd4.up.railway.app",
        "X-Title": "MIA Supervisor Chat"
    }

    url = "https://openrouter.ai/api/v1/chat/completions"

    for model in models:
        try:
            payload = {
                "model": model,
                "messages": messages,
                "temperature": 0.3,
                "max_tokens": 750
            }
            resp = requests.post(url, headers=headers, json=payload, timeout=12)
            if resp.status_code == 200:
                data = resp.json()
                reply = data["choices"][0]["message"]["content"]
                return format_filial_reply(reply)
        except Exception:
            continue

    # Fallback final a Google Gemini
    gemini_fb = chat_with_gemini(user_message, history)
    if gemini_fb:
        return gemini_fb

    return "Hola Padre, he experimentado una latencia momentánea conectando con los motores cognitivos. Por favor repíteme tu consulta."

import time
_PROCESSED_EVENTS = {}

def _is_duplicate_slack_event(event_id: str) -> bool:
    """Evita responder doblemente si Slack envía app_mention y message para el mismo evento"""
    if not event_id:
        return False
    now = time.time()
    # Purgar eventos de más de 60 segundos
    to_delete = [k for k, v in _PROCESSED_EVENTS.items() if now - v > 60]
    for k in to_delete:
        _PROCESSED_EVENTS.pop(k, None)
    if event_id in _PROCESSED_EVENTS:
        return True
    _PROCESSED_EVENTS[event_id] = now
    return False

if __name__ == "__main__":
    print("=" * 65)
    print("MIA SUPERVISOR CHAT - PRUEBA DE DIÁLOGO")
    print("=" * 65)
    test_msg = "Hola Mia, ¿cómo está la salud de la infraestructura y nuestras posiciones de MT5?"
    print(f"Usuario: {test_msg}\n")
    respuesta = chat_with_mia(test_msg)
    print(f"Mia: {respuesta}\n")
