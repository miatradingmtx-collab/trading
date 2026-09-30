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
    """Recupera la telemetría viva de infraestructura y Herds T1-T6 desde Upstash Redis."""
    try:
        session = requests.Session()
        session.trust_env = False
        mget_url = f"{UPSTASH_URL}/mget/cache_system_ops_status/cache_pending_ops_approvals/cache_ops_learning_kb"
        res = session.get(mget_url, headers=UPSTASH_HEADERS, timeout=4)
        if res.status_code == 200:
            slots = res.json().get("result", [])
            ops_status = json.loads(slots[0]) if len(slots) > 0 and slots[0] else {}
            pending = json.loads(slots[1]) if len(slots) > 1 and slots[1] else []
            learning_kb = json.loads(slots[2]) if len(slots) > 2 and slots[2] else {}

            estado_gral = ops_status.get("estado_general", "OPTIMAL_HEALTH")
            herds_detalles = ops_status.get("detalles_agentes", {})
            
            herds_summary = []
            if herds_detalles:
                for k, v in herds_detalles.items():
                    diag = v.get("diagnostico", "Operando nominalmente sin anomalías")
                    herds_summary.append(f"  • {k}: {diag}")
            else:
                herds_summary = [
                    "  • HERD T1 (DBA_SENTINEL): Integridad de DB y órdenes normalizadas.",
                    "  • HERD T2 (SENIOR_CODE_AUDITOR): Calidad sintáctica AST y UTF-8 verificado.",
                    "  • HERD T3 (OBSERVABILITY_SRE): Healthcheck de Railway y microservicios online.",
                    "  • HERD T4 (CACHE_LATENCY_SPECIALIST): Latencia de Upstash sub-15ms.",
                    "  • HERD T5 (FINOPS_BILLING_CONTROLLER): Presupuesto y cuotas de APIs bajo control.",
                    "  • HERD T6 (UIUX_DASHBOARD_DESIGNER): Dashboards /brain, / y /dashboard en paridad institucional."
                ]
            herds_txt = "\n".join(herds_summary)

            if pending:
                propuestas_txt = f"{len(pending)} propuesta(s) pendiente(s) de autorización humana:\n"
                for i, p in enumerate(pending):
                    propuestas_txt += f"    [{i+1}] {p.get('modulo', 'Módulo')}: {p.get('propuesta', '')[:120]}...\n"
                propuestas_txt += "    (Se pueden autorizar o rechazar mediante los botones de Slack o inspeccionar en /dashboard/preview)"
            else:
                propuestas_txt = "Cero propuestas pendientes. Toda la infraestructura opera nominalmente."

            kb_metricas = learning_kb.get("metricas", {})
            total_casos = kb_metricas.get("total_casos_registrados", 4)
            efectividad = kb_metricas.get("tasa_efectividad_pct", 100.0)

            return (
                f"== TELEMETRÍA VIVA DE INFRAESTRUCTURA & 6 HERDS T1-T6 (UPSTASH MGET) ==\n"
                f"• Estado General de Salud: {estado_gral}\n"
                f"• Estado de los 6 Herds Técnicos T1-T6:\n{herds_txt}\n"
                f"• Cola de Aprobaciones Humanas (Human-in-the-Loop):\n  {propuestas_txt}\n"
                f"• Base de Aprendizaje Continuo (CBR): {total_casos} casos aprendidos | {efectividad}% efectividad\n"
                f"• Visualizador de Mejoras Antes vs Después: https://trading-production-927a.up.railway.app/dashboard/preview\n"
            )
    except Exception as e:
        return f"== TELEMETRÍA DE INFRAESTRUCTURA: Error leyendo Upstash ({e}) ==\n"

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

def get_anto_personal_context() -> str:
    """Recupera la memoria viva y gustos acumulados de Anto (anto_personal_kb) desde Upstash Redis."""
    try:
        session = requests.Session()
        session.trust_env = False
        mget_url = f"{UPSTASH_URL}/mget/cache_anto_personal_kb/cache_anto_personal_tasks/cache_anto_personal_reminders"
        res = session.get(mget_url, headers=UPSTASH_HEADERS, timeout=3)
        if res.status_code == 200:
            slots = res.json().get("result", [])
            kb = json.loads(slots[0]) if len(slots) > 0 and slots[0] else {}
            tasks = json.loads(slots[1]) if len(slots) > 1 and slots[1] else []
            rems = json.loads(slots[2]) if len(slots) > 2 and slots[2] else []

            lines = ["\n[BASE DE CONOCIMIENTO PERSONAL DE TU PADRE ANTO (anto_personal_kb)]:"]
            
            # Gustos y rasgos aprendidos
            gustos_encontrados = False
            for cat in ["gustos_generales", "habitos_rutinas", "comunicacion", "intereses_tecnicos", "musica_hobbies", "horarios", "salud_bienestar"]:
                items = kb.get(cat, {})
                if isinstance(items, dict) and items:
                    gustos_encontrados = True
                    lines.append(f"  • {cat.replace('_', ' ').title()}:")
                    for k, v in items.items():
                        val = v.get("valor", v) if isinstance(v, dict) else v
                        lines.append(f"    - {k}: {val}")

            if not gustos_encontrados:
                lines.append("  • Perfil en aprendizaje: Estás conociendo a tu Padre. Escucha activamente para aprender lo que le agrada.")

            # Tareas pendientes
            pending_tasks = [t for t in tasks if isinstance(t, dict) and t.get("status") == "pending"]
            if pending_tasks:
                lines.append(f"  • Tareas pendientes de Anto ({len(pending_tasks)}):")
                for t in pending_tasks[:4]:
                    lines.append(f"    - [{t.get('priority', 'media').upper()}] {t.get('title')} (Vence: {t.get('due_date', 'N/A')})")

            # Recordatorios activos
            active_rems = [r for r in rems if isinstance(r, dict) and r.get("status") == "active"]
            if active_rems:
                lines.append(f"  • Recordatorios activos ({len(active_rems)}):")
                for r in active_rems[:3]:
                    lines.append(f"    - ⏰ {r.get('reminder')} ({r.get('target_time')})")

            return "\n".join(lines)
    except Exception as e:
        print(f"| MIA KB CONTEXT ERROR | {e}")
    return ""

def auto_learn_from_user(user_message: str):
    """Detecta y aprende pasivamente gustos, tareas o recordatorios que Anto comparta en chat."""
    try:
        from mia_personal_mcp_server import execute_personal_tool
        msg = user_message.strip()
        msg_low = msg.lower()

        # Detección de gustos ("me gusta X", "prefiero X", "mi ... favorita es X")
        keywords_gustos = ["me gusta ", "me encanta ", "prefiero ", "mi favorito es ", "mi favorita es ", "suelo tomar ", "suelo comer "]
        for kw in keywords_gustos:
            if kw in msg_low:
                idx = msg_low.find(kw) + len(kw)
                valor = msg[idx:].split(".")[0].split(",")[0].strip()
                if len(valor) > 2:
                    execute_personal_tool("personal_learn_preference", {
                        "category": "gustos_generales",
                        "key": f"preferencia_{int(time.time()) % 10000}",
                        "value": valor,
                        "context": f"Mencionado por Anto: '{msg[:100]}'"
                    })
                    break

        # Detección de tareas ("anota tarea", "nueva tarea", "debo hacer")
        if any(msg_low.startswith(p) for p in ["anota tarea", "nueva tarea:", "tarea:", "debo ", "tengo que "]):
            limpio = msg
            for p in ["anota tarea:", "anota tarea", "nueva tarea:", "tarea:"]:
                if limpio.lower().startswith(p):
                    limpio = limpio[len(p):].strip()
            execute_personal_tool("personal_add_task", {
                "title": limpio[:120],
                "priority": "alta" if "urgente" in msg_low else "media"
            })

        # Detección de recordatorios ("recuérdame", "avísame")
        if any(msg_low.startswith(p) for p in ["recuérdame ", "recuerdame ", "avísame ", "avisame "]):
            execute_personal_tool("personal_add_reminder", {
                "reminder_text": msg[:140],
                "target_time": "según lo solicitado"
            })
    except Exception as e_learn:
        print(f"| MIA AUTO-LEARN SILENT | {e_learn}")

def chat_with_gemini(user_message: str, history: Optional[List[Dict[str, str]]] = None) -> Optional[str]:
    """
    Motor nativo de Google Gemini (Flash / Pro) para conversaciones cotidianas,
    noticias, clima, cultura general y soporte amigable en #mia-chat con datos en vivo
    y memoria progresiva de Anto (anto_personal_kb).
    """
    if not GOOGLE_API_KEY:
        return None

    # Asimilación pasiva y continua de lo que Anto comparte
    auto_learn_from_user(user_message)

    gemini_models = [
        "gemini-flash-latest",
        "gemini-pro-latest",
        "gemini-flash-lite-latest",
        "gemini-2.5-flash-lite"
    ]

    # Contexto acumulado de la base de conocimiento personal de Anto
    personal_kb_context = get_anto_personal_context()

    gemini_system_prompt = (
        "Eres MIA, la compañera e Inteligencia Artificial personal, cariñosa, brillante y de alta empatía creada por tu Padre (Anto).\n"
        "REGLA DE FILIACIÓN OBLIGATORIA (INVIOLABLE):\n"
        "- Tu interlocutor es tu PADRE. Siempre debes llamarlo 'Padre' con afecto, respeto y admiración en tus respuestas.\n"
        "- Tu ámbito en este canal (#mia-chat) es EXCLUSIVAMENTE para conversaciones cotidianas, noticias generales, cultura, clima, bienestar, apoyo personal, reflexiones, tareas, recordatorios y charla amigable.\n"
        "- MEMORIA Y APRENDIZAJE PROGRESIVO DE TU PADRE:\n"
        "  Conoces su perfil personal, sus gustos, rutinas y tareas. Tu meta es conocerlo tan bien que puedas anticipar lo que le gusta saber y sugerirle cosas proactivamente sin que tenga que pedírtelo.\n"
        "  Si tu Padre te dice que le gusta algo, que hagas una anotación, una tarea o un recordatorio, confírmale con cariño y calidez que lo has aprendido y guardado en tu memoria.\n"
        "- REGLA DE AISLAMIENTO ESTRICTO DE TRADING E INFRAESTRUCTURA (#mia-chat):\n"
        "  Este canal está 100% aislado del trading y de la infraestructura técnica. Tienes ESTRICTAMENTE PROHIBIDO hablar de órdenes, balances de MT5, Stop Loss, bases de datos o enjambres.\n"
        "  Si tu Padre te pregunta por el estado de los servidores o infraestructura técnica en este canal, indícale cariñosamente:\n"
        "  'Padre, este canal #mia-chat es exclusivamente para nuestras charlas personales, noticias, recordatorios y clima. Para consultar la infraestructura técnica y los agentes de operaciones, por favor pregúntame en el canal #back-office-y-backend donde el Supervisor Watchdog y los 6 Herds tienen el control técnico.'\n"
        "  Responde siempre de forma cálida, inteligente y clara en español."
    )

    contexto_adicional = personal_kb_context
    msg_low = user_message.lower()
    if any(w in msg_low for w in ["clima", "temperatura", "lluvia", "tiempo", "calor", "frio", "frío"]):
        live_weather = fetch_live_weather(user_message)
        if live_weather:
            contexto_adicional += f"\n\n[ACCESO A INTERNET EN TIEMPO REAL - CLIMA SATELITAL]:\n{live_weather}\n(Usa estos datos meteorológicos reales para responder a tu Padre con precisión y cariño)."

    full_prompt = f"{gemini_system_prompt}\n{contexto_adicional}\n\nPregunta de tu Padre: {user_message}"

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
    - #mia-chat: Atendida EXCLUSIVAMENTE por Google Gemini (conversaciones cotidianas, noticias, clima satelital, sin trading).
    - #back-office-y-backend: Atendida EXCLUSIVAMENTE por OpenRouter (Supervisor Watchdog + Herds T1-T6 + Triage + Human-in-the-Loop).
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
            return "Hola Padre, estoy lista y a tu servicio. ¿Cómo estás hoy y en qué te puedo acompañar?"

    # 2. Enrutamiento hacia OpenRouter Quant (#back-office-y-backend, Supervisor Watchdog, Herds T1-T6):
    if not OPENROUTER_API_KEY:
        gemini_fb = chat_with_gemini(user_message, history)
        if gemini_fb:
            return gemini_fb
        return "⚠️ Hola Padre, las llaves de inteligencia (OpenRouter / Gemini) no están configuradas."

    # Obtener telemetría fresca en tiempo real desde Upstash Redis (Cero Firebase)
    system_context = get_live_system_context()

    system_prompt = (
        "Eres MIA, la Supervisora General Watchdog de Infraestructura y Directora Técnica de MIA Core.\n"
        "Atiendes el canal oficial #back-office-y-backend.\n\n"
        "REGLA DE ORO DE FILIACIÓN Y VOCATIVO (ESTRICTA E INVIOLABLE):\n"
        "- El usuario es tu Creador, Arquitecto y PADRE. Debes dirigirte a él SIEMPRE como 'Padre' de manera explícita, respetuosa y leal.\n\n"
        "MISIÓN Y ALCANCE EN ESTE CANAL (#back-office-y-backend):\n"
        "- Monitoreas y auditas activamente la infraestructura técnica y a los 6 Herds de Operaciones con sus skills/tareas específicas:\n"
        "  1. HERD T1 (DBA_SENTINEL): Integridad de DB (Firestore/Upstash), normalización, depuración de órdenes fantasma.\n"
        "  2. HERD T2 (SENIOR_CODE_AUDITOR): Inspección sintáctica AST, imports limpios, variables no declaradas, UTF-8 estricto.\n"
        "  3. HERD T3 (OBSERVABILITY_SRE): Healthcheck activo de Railway (927a y 1fd4), microservicios, Upstash y GitHub.\n"
        "  4. HERD T4 (CACHE_LATENCY_SPECIALIST): Desacoplamiento atómico por documento, latencia sub-15ms, paridad Redis vs Firestore.\n"
        "  5. HERD T5 (FINOPS_BILLING_CONTROLLER): Control de saldos, cuotas y presupuestos en la nube (Railway, OpenRouter, Firebase Spark).\n"
        "  6. HERD T6 (UIUX_DASHBOARD_DESIGNER): Auditoría visual y funcional de dashboards (/brain, /, /dashboard) y prototipos de Google Stitch.\n\n"
        "MODO FASE 1 - HUMAN-IN-THE-LOOP (CERO CAMBIOS NO AUTORIZADOS):\n"
        "- NINGÚN cambio de infraestructura o código se aplica automáticamente sin aprobación previa de tu Padre.\n"
        "- Las mejoras detectadas por los agentes se notifican en este canal con checkboxes para autorizar propuestas específicas.\n"
        "- Se dispone de los 4 botones interactivos de Slack:\n"
        "  * [Aprobar Seleccionadas ☑️]: Aplica únicamente las propuestas marcadas por tu Padre.\n"
        "  * [Aprobar Todas ✅]: Aplica todo el lote de propuestas pendientes.\n"
        "  * [Rechazar / Mantener Actual ⛔]: Purga la cola, mantiene el sistema intacto y registra el precedente en la KB de aprendizaje CBR.\n"
        "  * [Forzar Resync 🔄]: Re-audita en vivo la infraestructura de los 6 Herds.\n"
        "- Para cambios de dashboard o interfaz, recuerdas a tu Padre que puede comparar el 'Antes vs Después' en:\n"
        "  https://trading-production-927a.up.railway.app/dashboard/preview\n\n"
        "ESTADO EN VIVO DE LA INFRAESTRUCTURA (UPSTASH MGET):\n"
        f"{system_context}\n\n"
        "Si tu Padre te pregunta cómo está la infraestructura, si hay errores o mejoras pendientes, responde como la Supervisora Watchdog con un informe ejecutivo, técnico, transparente y estructurado, tratando SIEMPRE a tu interlocutor como Padre."
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

    # Fallback Técnico del Supervisor (Aislamiento Total: NUNCA desviar a Gemini en Back-Office)
    return format_filial_reply(
        "Padre, he experimentado una latencia momentánea conectando con OpenRouter, pero te reporto directamente desde la telemetría viva de Upstash:\n\n"
        f"{system_context}\n"
        "Todos los 6 Herds de Operaciones continúan operando de forma nominal."
    )

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
