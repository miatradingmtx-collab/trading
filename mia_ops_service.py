"""
MIA OPS SERVICE - MICROSERVICIO DEDICADO DE INFRAESTRUCTURA & CHATOPS
=====================================================================
Microservicio autónomo e independiente del backend de ejecución de MT5 (app.py).

Arquitectura de Separación de Planos:
- Plano de Datos (MT5 Data Plane en 927a): Exclusivo para órdenes de trading, webhooks de ticks y trailing stop. Latencia sub-50ms, cero jitter.
- Plano de Control (Ops Control Plane en este microservicio):
  1. Servidor MCP de Back-Office (/mcp/ops).
  2. Webhooks de Slack (/api/slack/events, /api/slack/interactions, /api/slack/command).
  3. Bucle continuo de la Malla de 10 Herds (T1 a T10).
  4. Watchdog Supervisor con evaluación cognitiva Llama 3.3 70B (OpenRouter).
  5. Sincronización en caliente del Antigravity Live Mirror y Grounding de Arquitectura.
"""

import os
import json
import time
import asyncio
import datetime
import requests
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, Request, HTTPException, BackgroundTasks, Form
from fastapi.responses import JSONResponse, PlainTextResponse, RedirectResponse
from pydantic import BaseModel
import uvicorn
from dotenv import load_dotenv

from mia_system_ops_swarm import system_ops_supervisor
from mia_slack_bridge import slack_bridge
from mia_ops_mcp_server import ops_mcp_router, api_ops_mcp_router
from mia_infra_grounding_kb import MiaInfraGroundingKB
from mia_antigravity_mirror import AntigravityLiveMirror

load_dotenv()

app = FastAPI(
    title="MIA Ops Control Plane Microservice",
    description="Microservicio dedicado de Infraestructura, 10 Herds SRE, MCP Ops y ChatOps Slack",
    version="1.0.0"
)

# Montar routers MCP de Back-Office
app.include_router(ops_mcp_router)
app.include_router(api_ops_mcp_router)

# ====================================================================
# CLIENTE FIREBASE FIRESTORE (PERSISTENCIA HISTÓRICA HOMOLOGADA)
# ====================================================================
_firestore_db = None

def get_firestore_db():
    global _firestore_db
    if _firestore_db is not None:
        return _firestore_db
    try:
        import firebase_admin
        from firebase_admin import credentials, firestore
        if not firebase_admin._apps:
            key_path = "serviceAccountKey.json"
            if os.path.exists(key_path):
                cred = credentials.Certificate(key_path)
                firebase_admin.initialize_app(cred)
            else:
                for env_var in ["FIREBASE_SERVICE_ACCOUNT_JSON", "FIREBASE_SERVICE_ACCOUNT", "SERVICE_ACCOUNT_KEY"]:
                    raw_val = os.getenv(env_var)
                    if raw_val:
                        try:
                            info = json.loads(raw_val.strip())
                            cred = credentials.Certificate(info)
                            firebase_admin.initialize_app(cred)
                            break
                        except Exception:
                            keys = ["type", "project_id", "private_key_id", "private_key", "client_email", "client_id", "auth_uri", "token_uri", "auth_provider_x509_cert_url", "client_x509_cert_url"]
                            info = {}
                            for k in keys:
                                pat = re.compile(r'[\'"]' + re.escape(k) + r'[\'"]\s*:\s*[\'"](.*?)[\'"]', re.DOTALL)
                                m = pat.search(raw_val)
                                if m:
                                    info[k] = m.group(1).replace(r'\\n', '\n')
                            if "private_key" in info and "client_email" in info:
                                cred = credentials.Certificate(info)
                                firebase_admin.initialize_app(cred)
                                break
        if firebase_admin._apps:
            _firestore_db = firestore.client()
        return _firestore_db
    except Exception as e_fb:
        print(f"| FIREBASE CLIENT INIT ERROR | {e_fb}")
        return None


# ====================================================================
# HEALTHCHECK & TELEMETRÍA
# ====================================================================
@app.get("/health")
def healthcheck():
    return {
        "microservicio": "mia-ops-service",
        "estado": "ONLINE",
        "rol": "Ops Control Plane & 10 Herds SRE",
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "herds_activos": 10,
        "evaluador_llm": "OpenRouter (Llama 3.3 70B Grounded)"
    }

@app.get("/api/ops/status")
def get_ops_status():
    """Retorna el último pulso de salud de los 10 Herds desde Upstash en sub-25ms."""
    try:
        upstash_url = os.getenv("UPSTASH_REDIS_REST_URL", "https://firm-koi-93555.upstash.io")
        upstash_token = os.getenv("UPSTASH_REDIS_REST_TOKEN", "gQAAAAAAAW1zAAIgcDFmZGI5MGViNWY4Mjc0MGE1Yjg3NDZiOTdiN2MyMjg5Yg")
        headers = {"Authorization": f"Bearer {upstash_token}"}
        r = requests.get(f"{upstash_url}/get/cache_system_ops_status", headers=headers, timeout=3)
        if r.status_code == 200 and r.json().get("result"):
            raw = r.json().get("result")
            return json.loads(raw) if isinstance(raw, str) else raw
    except Exception:
        pass
    return system_ops_supervisor.run_swarm_audit(notify_slack=False)

@app.get("/dashboard/preview")
def redirect_to_dashboard_preview():
    """Redirige al visualizador comparativo Antes vs Después en el microservicio 927a."""
    return RedirectResponse(url="https://trading-production-927a.up.railway.app/dashboard/preview", status_code=307)

@app.get("/dashboard")
def redirect_to_dashboard():
    """Redirige al Dashboard Central Gold Standard en el microservicio 927a."""
    return RedirectResponse(url="https://trading-production-927a.up.railway.app/dashboard", status_code=307)

@app.post("/api/ops/audit")
async def trigger_ops_audit(background_tasks: BackgroundTasks):
    """Dispara un ciclo de auditoría completo y notifica a Slack."""
    background_tasks.add_task(system_ops_supervisor.run_swarm_audit, notify_slack=True)
    return {"status": "AUDIT_QUEUED", "mensaje": "Ciclo de auditoría de 10 Herds iniciado en segundo plano."}

@app.post("/api/ops/sync_mirror")
def sync_antigravity_mirror():
    """Sincroniza en caliente el Antigravity Live Mirror y Grounding de Arquitectura."""
    ok_g = MiaInfraGroundingKB.sync_grounding_to_upstash()
    ok_m = AntigravityLiveMirror.sync_to_upstash()
    return {
        "status": "SYNCED",
        "grounding_synced": ok_g,
        "antigravity_mirror_synced": ok_m,
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
    }

@app.post("/api/antigravity/mirror/push")
async def push_antigravity_mirror_delta(request: Request):
    """
    Endpoint receptor del Live Mirror desde sesiones de Google Antigravity.
    Recibe el payload con commits, decisiones, prompts y lo inyecta a Upstash en caliente.
    """
    try:
        body = await request.json()
        upstash_url = os.getenv("UPSTASH_REDIS_REST_URL", "https://firm-koi-93555.upstash.io")
        upstash_token = os.getenv("UPSTASH_REDIS_REST_TOKEN", "gQAAAAAAAW1zAAIgcDFmZGI5MGViNWY4Mjc0MGE1Yjg3NDZiOTdiN2MyMjg5Yg")
        headers = {"Authorization": f"Bearer {upstash_token}", "Content-Type": "application/json"}
        
        # Persistir en slot Upstash
        r = requests.post(f"{upstash_url}/set/cache_mia_live_antigravity_delta", headers=headers, json=body, timeout=4)
        return {
            "status": "MIRROR_RECEIVED",
            "upstash_status": r.status_code,
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving mirror delta: {e}")

@app.get("/api/antigravity/mirror")
def get_antigravity_mirror():
    """Retorna el estado actual del espejo de Antigravity inyectado en Upstash."""
    upstash_url = os.getenv("UPSTASH_REDIS_REST_URL", "https://firm-koi-93555.upstash.io")
    upstash_token = os.getenv("UPSTASH_REDIS_REST_TOKEN", "gQAAAAAAAW1zAAIgcDFmZGI5MGViNWY4Mjc0MGE1Yjg3NDZiOTdiN2MyMjg5Yg")
    headers = {"Authorization": f"Bearer {upstash_token}"}
    r = requests.get(f"{upstash_url}/get/cache_mia_live_antigravity_delta", headers=headers, timeout=4)
    if r.status_code == 200 and r.json().get("result"):
        raw = r.json().get("result")
        return json.loads(raw) if isinstance(raw, str) else raw
    return {"status": "NO_MIRROR_DATA", "detalle": "Slot cache_mia_live_antigravity_delta vacío o no inicializado."}

class HomologateApprovalRequest(BaseModel):
    tarea_id: str
    detalle: Optional[str] = ""
    solucion: Optional[str] = ""

@app.post("/api/antigravity/homologate_approval")
def homologate_antigravity_approval_endpoint(payload: HomologateApprovalRequest):
    """
    Homologa en caliente una aprobación o solución ejecutada directamente en Google Antigravity.
    Remueve la tarea de 'cache_pending_ops_approvals', actualiza el espejo en vivo
    y registra el precedente en 'mia_ops_learning_history' con score de confianza 0.98.
    """
    res = AntigravityLiveMirror.homologate_antigravity_approval(
        tarea_id_o_accion=payload.tarea_id,
        detalle=payload.detalle or "",
        solucion=payload.solucion or ""
    )
    return res

@app.post("/api/ops/vectorize")
def trigger_vectorization(payload: Optional[Dict[str, Any]] = None):
    """
    HERD T1 (DBA_SENTINEL): Vectoriza campos de catálogos y arrays a un tensor numérico 20D.
    Guarda en cache_vector_indicadores para ingesta sub-5ms de TensorFlow.
    """
    from mia_system_ops_swarm import HerdDBAExpert
    sample_doc = payload or {
        "sesion": "NEW_YORK",
        "regimen": "EXPANSION_ALCISTA",
        "confirmaciones": ["OB_4H", "SMC_SWEEP", "CVD_DIVERGENCE"],
        "top_1": {"peso": 35},
        "top_2": {"peso": 30},
        "top_3": {"peso": 25},
        "spread": 1.15
    }
    vector_result = HerdDBAExpert.vectorize_features(sample_doc)
    upstash_url = os.getenv("UPSTASH_REDIS_REST_URL", "https://firm-koi-93555.upstash.io")
    upstash_token = os.getenv("UPSTASH_REDIS_REST_TOKEN", "gQAAAAAAAW1zAAIgcDFmZGI5MGViNWY4Mjc0MGE1Yjg3NDZiOTdiN2MyMjg5Yg")
    headers = {"Authorization": f"Bearer {upstash_token}", "Content-Type": "application/json"}
    requests.post(f"{upstash_url}/set/cache_vector_indicadores", headers=headers, json=vector_result, timeout=4)
    return {"status": "VECTORIZED", "vector": vector_result}

# ====================================================================
# CHATOPS SLACK WEBHOOKS (DESACOPLADOS DE MT5)
# ====================================================================
@app.post("/api/slack/events")
async def slack_events_endpoint(request: Request, background_tasks: BackgroundTasks):
    """
    Webhook receptor de eventos de Slack.
    Soporta verificación de URL (challenge) y procesamiento asíncrono de menciones/mensajes.
    Aislamiento estricto: Ignora cualquier evento proveniente de #mia-chat.
    """
    try:
        body_bytes = await request.body()
        payload = json.loads(body_bytes.decode("utf-8"))
    except Exception:
        return PlainTextResponse("Invalid JSON", status_code=400)

    # 1. Challenge Handshake de Slack API
    if payload.get("type") == "url_verification":
        return PlainTextResponse(payload.get("challenge", ""))

    event = payload.get("event", {})
    event_type = event.get("type")
    channel_id = event.get("channel") or "C0C4ZMFCMJ8"
    bot_id = event.get("bot_id")
    subtype = event.get("subtype")
    text = (event.get("text") or "").strip()

    # Ignorar mensajes emitidos por bots, cambios de mensajes o texto vacío
    if bot_id or subtype in ["bot_message", "message_changed", "message_deleted"] or not text:
        return PlainTextResponse("IGNORED_BOT_OR_EMPTY", status_code=200)

    # Aislamiento de canales: Solo procesar #back-office-y-backend (silenciar #mia-chat)
    if "chat" in str(channel_id).lower() or channel_id == "C0C4QCZPTPH":
        return PlainTextResponse("IGNORED_NON_OPS_CHANNEL", status_code=200)

    if event_type in ["app_mention", "message"]:
        event_id = payload.get("event_id") or event.get("client_msg_id") or f"{channel_id}_{event.get('ts')}"
        from mia_supervisor_chat import _is_duplicate_slack_event, chat_with_mia
        if _is_duplicate_slack_event(event_id):
            return PlainTextResponse("DUPLICATE_IGNORED", status_code=200)

        # Si el usuario pide forzar resync explícitamente
        text_lower = text.lower()
        if any(k in text_lower for k in ["forzar resync", "re-auditar en vivo"]):
            background_tasks.add_task(system_ops_supervisor.run_swarm_audit, notify_slack=True)
            return PlainTextResponse("AUDIT_TRIGGERED", status_code=200)

        # Responder conversacionalmente con OpenRouter y telemetría de 10 Herds
        def process_chat_response():
            try:
                reply = chat_with_mia(text, force_engine="openrouter")
                msg_formatted = f"🛡️ *MIA Watchdog (Supervisor / 10 Herds T1-T10)*:\n{reply}"
                chat_blocks = [
                    {
                        "type": "section",
                        "text": {"type": "mrkdwn", "text": msg_formatted}
                    },
                    {
                        "type": "actions",
                        "block_id": "watchdog_chat_actions",
                        "elements": [
                            {
                                "type": "button",
                                "text": {"type": "plain_text", "text": "Aprobar Todas ✅", "emoji": True},
                                "style": "primary",
                                "value": "approve_all_pending",
                                "action_id": "approve_triage_action"
                            },
                            {
                                "type": "button",
                                "text": {"type": "plain_text", "text": "Rechazar / Mantener Actual ⛔", "emoji": True},
                                "style": "danger",
                                "value": "reject_all_pending",
                                "action_id": "reject_triage_action"
                            },
                            {
                                "type": "button",
                                "text": {"type": "plain_text", "text": "Forzar Resync 🔄", "emoji": True},
                                "value": "force_resync",
                                "action_id": "resync_action"
                            }
                        ]
                    }
                ]
                slack_bridge.send_channel_message(
                    msg_formatted,
                    channel=channel_id,
                    username="MIA Watchdog",
                    icon_emoji=":shield:",
                    blocks=chat_blocks
                )
            except Exception as e_chat:
                print(f"| SLACK OPS CHAT ERROR | Error procesando respuesta: {e_chat}")

        background_tasks.add_task(process_chat_response)

    return PlainTextResponse("EVENT_RECEIVED", status_code=200)

@app.post("/api/slack/interactions")
@app.post("/slack/interactions")
async def slack_interactions_endpoint(request: Request, background_tasks: BackgroundTasks):
    """
    Maneja las interacciones de botones y checkboxes en Slack.
    Procesa [Aprobar Seleccionadas], [Aprobar Todas], [Rechazar] y [Forzar Resync].
    """
    try:
        form_data = await request.form()
        payload_raw = form_data.get("payload")
        if not payload_raw:
            return PlainTextResponse("Payload missing", status_code=400)
        payload = json.loads(payload_raw)
    except Exception as e:
        return PlainTextResponse(f"Error parsing interaction: {e}", status_code=400)

    actions = payload.get("actions", [])
    if not actions:
        return PlainTextResponse("No actions", status_code=200)

    action = actions[0]
    action_id = action.get("action_id", "")
    val = action.get("value", "")
    user_name = payload.get("user", {}).get("name") or "Padre"
    channel_id = payload.get("channel", {}).get("id") or "C0C4ZMFCMJ8"
    response_url = payload.get("response_url", "")
    
    # Telemetría forense en Upstash Redis para auditoría de clics en tiempo real
    try:
        up_h = {"Authorization": "Bearer gQAAAAAAAW1zAAIgcDFmZGI5MGViNWY4Mjc0MGE1Yjg3NDZiOTdiN2MyMjg5Yg"}
        audit_entry = {
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "server": "0b51",
            "path": request.url.path,
            "action_id": action_id,
            "val": val,
            "user": user_name
        }
        requests.post("https://firm-koi-93555.upstash.io/lpush/cache_slack_interactions_audit", headers=up_h, data=json.dumps(audit_entry), timeout=1)
    except Exception:
        pass

    # 1. Ignorar clics en los checkboxes directamente (solo guardan estado en el cliente)
    if "selected_proposals_checkbox" in action_id or "checkboxes" in action_id:
        return PlainTextResponse("OK", status_code=200)

    # 2. Botones de MIA Quant Supervisor (RLHF Post-Mortem y CBR Trading)
    if action_id.startswith("quant_approve_") or action_id.startswith("quant_reject_") or action_id.startswith("quant_review_"):
        def do_quant_interaction():
            try:
                ticket_id = action_id.replace("quant_approve_", "").replace("quant_reject_", "").replace("quant_review_", "")
                action_type = "APROBADO" if "quant_approve_" in action_id else ("RECHAZADO" if "quant_reject_" in action_id else "REVISION")
                target_case_id = val.replace("approve_", "").replace("reject_", "").replace("review_", "") if val else ""
                
                # 1. Actualizar Upstash CBR Trading
                up_headers = {"Authorization": "Bearer gQAAAAAAAW1zAAIgcDFmZGI5MGViNWY4Mjc0MGE1Yjg3NDZiOTdiN2MyMjg5Yg"}
                r_cbr = requests.get("https://firm-koi-93555.upstash.io/get/cache_trading_learning_kb", headers=up_headers, timeout=6).json()
                cbr_data = json.loads(r_cbr.get("result", "[]")) if r_cbr.get("result") else []
                updated_case = None
                for caso in cbr_data:
                    match = False
                    if target_case_id and str(caso.get("case_id")) == target_case_id:
                        match = True
                    elif not target_case_id and str(caso.get("ticket")) == str(ticket_id):
                        match = True
                    
                    if match:
                        caso["veredicto_humano"] = action_type
                        caso["aprobado_por"] = user_name
                        caso["score_confianza"] = 1.0 if action_type == "APROBADO" else 0.0
                        caso["timestamp_aprobacion"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
                        updated_case = caso
                
                # Recalcular métricas de la Prueba de Confianza (Trust Mode)
                aprobados = sum(1 for c in cbr_data if c.get("veredicto_humano") == "APROBADO")
                rechazados = sum(1 for c in cbr_data if c.get("veredicto_humano") == "RECHAZADO")
                resueltos = aprobados + rechazados
                tasa_confianza = round((aprobados / resueltos * 100), 1) if resueltos > 0 else 0.0

                racha = 0
                for c in cbr_data:
                    if c.get("veredicto_humano") == "APROBADO":
                        racha += 1
                    elif c.get("veredicto_humano") == "RECHAZADO":
                        break

                trust_mode_activo = (racha >= 20 and tasa_confianza >= 90.0)
                trust_stats = {
                    "aprobados_hitl": aprobados,
                    "rechazados_hitl": rechazados,
                    "racha_consecutiva": racha,
                    "tasa_confianza_pct": tasa_confianza,
                    "trust_mode_activo": trust_mode_activo,
                    "ultima_actualizacion": datetime.datetime.now(datetime.timezone.utc).isoformat()
                }
                requests.post("https://firm-koi-93555.upstash.io/set/cache_cbr_trust_mode", headers=up_headers, json=trust_stats)
                requests.post("https://firm-koi-93555.upstash.io/set/cache_trading_learning_kb", headers=up_headers, json=cbr_data[:50])

                # 2. Homologación Dual en Firebase Firestore (mia_trading_learning_history)
                db_fb = get_firestore_db()
                if db_fb:
                    try:
                        update_payload = {
                            "veredicto_humano": action_type,
                            "aprobado_por": user_name,
                            "score_confianza": 1.0 if action_type == "APROBADO" else 0.0,
                            "timestamp_aprobacion": datetime.datetime.now(datetime.timezone.utc).isoformat()
                        }
                        found_in_fb = False
                        today_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
                        
                        # A. Buscar en subcolección jerárquica del día
                        if target_case_id:
                            doc_hier = db_fb.collection("mia_trading_learning_history").document(today_str).collection("casos").document(target_case_id)
                            if doc_hier.get().exists:
                                doc_hier.update(update_payload)
                                found_in_fb = True
                        
                        # B. Buscar en todas las subcolecciones 'casos' por case_id o ticket
                        if not found_in_fb and target_case_id:
                            docs_cg = db_fb.collection_group("casos").where("case_id", "==", target_case_id).stream()
                            for dc in docs_cg:
                                dc.reference.update(update_payload)
                                found_in_fb = True
                                
                        if not found_in_fb and ticket_id:
                            docs_cg_t = db_fb.collection_group("casos").where("ticket", "==", str(ticket_id)).stream()
                            for dc in docs_cg_t:
                                dc.reference.update(update_payload)
                                found_in_fb = True
                        
                        # C. Compatibilidad con raíz legacy
                        if target_case_id:
                            doc_legacy = db_fb.collection("mia_trading_learning_history").document(target_case_id)
                            if doc_legacy.get().exists:
                                doc_legacy.update(update_payload)
                                found_in_fb = True
                        
                        # D. Si no existía, persistir en la jerarquía del día actual
                        if not found_in_fb and updated_case:
                            cid = target_case_id or f"TRADE_CASE_{ticket_id}_{int(time.time())}"
                            db_fb.collection("mia_trading_learning_history").document(today_str).set({
                                "fecha": today_str,
                                "has_subcollections": True,
                                "ultima_actualizacion": datetime.datetime.now(datetime.timezone.utc).isoformat()
                            }, merge=True)
                            db_fb.collection("mia_trading_learning_history").document(today_str).collection("casos").document(cid).set(updated_case)

                        # Actualizar documento latest
                        try:
                            db_fb.collection("mia_trading_learning_history").document("latest").set({
                                "ultimo_caso_evaluado": target_case_id or ticket_id,
                                "veredicto_humano": action_type,
                                "aprobado_por": user_name,
                                "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                                "prueba_de_confianza": trust_stats
                            }, merge=True)
                        except Exception:
                            pass
                        print(f"| FIREBASE CBR SYNC | Caso {target_case_id or ticket_id} homologado exitosamente en Firestore mia_trading_learning_history.")
                    except Exception as e_fb:
                        print(f"| FIREBASE CBR SYNC ERROR | {e_fb}")

                emoji_status = "✅" if action_type == "APROBADO" else ("❌" if action_type == "RECHAZADO" else "🔍")
                estado_auto = "🚀 MODO_AUTÓNOMO (CONFIANZA SUPERADA)" if trust_mode_activo else f"🔒 ASISTIDO_HITL (Progreso: {racha}/20 racha | Tasa: {tasa_confianza}%)"
                msg_quant = (
                    f"{emoji_status} *MIA COGNICIÓN CBR:* Aprendizaje del trade `{ticket_id}` registrado como *{action_type}* por @{user_name}.\n"
                    f"• *Confianza Sello Humano:* `{'100% (Verificado)' if action_type == 'APROBADO' else 'Descartado'}`.\n"
                    f"• *🛡️ Prueba de Confianza (Hacia la Autonomía):* `{estado_auto}` ({aprobados} aprobados / {rechazados} rechazados).\n"
                    f"• *Destino:* `cache_trading_learning_kb` y `mia_trading_learning_history` (Firebase) sincronizados con Gemini Pro y ATLAS."
                )
                
                # Despacho dual: response_url + canal de insights
                if response_url:
                    try:
                        requests.post(response_url, json={"text": msg_quant, "replace_original": False, "response_type": "in_channel"}, timeout=3)
                    except Exception:
                        pass
                slack_bridge.send_channel_message(msg_quant, channel=os.getenv("SLACK_CHANNEL_INSIGHTS", "C0C6DUTQVEZ"))
            except Exception as e_quant:
                print(f"| QUANT CBR ERROR (OPS SERVICE) | {e_quant}")
        
        background_tasks.add_task(do_quant_interaction)
        return PlainTextResponse("OK", status_code=200)

    # 2.5 Botón: Aprobar Seleccionadas
    elif "approve_selected" in val or "approve_selected" in action_id:
        state_values = payload.get("state", {}).get("values", {})
        indices = []
        for b_id, b_val in state_values.items():
            for k, v in b_val.items():
                if isinstance(v, dict) and "selected_options" in v:
                    for opt in v.get("selected_options", []):
                        v_opt = opt.get("value", "")
                        if "propuesta_" in v_opt:
                            try:
                                indices.append(int(v_opt.replace("propuesta_", "")))
                            except:
                                pass

        if not indices:
            warning_msg = (
                f"⚠️ *Atención Padre*: No marcaste ninguna casilla antes de presionar *Aprobar Seleccionadas*.\n"
                f"• Por favor marca con el check (☑️) una o más propuestas pendientes y vuelve a presionar el botón.\n"
                f"• O presiona *[Aprobar Todas ✅]* para autorizar todas las tareas pendientes en un solo clic."
            )
            slack_bridge.send_channel_message(warning_msg, channel=channel_id)
            if response_url:
                try:
                    requests.post(response_url, json={"text": warning_msg, "replace_original": False, "response_type": "in_channel"}, timeout=3)
                except Exception:
                    pass
            return PlainTextResponse("OK", status_code=200)

        def do_apply_selected():
            try:
                exec_res = system_ops_supervisor.apply_approved_actions(selected_indices=indices, user_name=user_name)
                res = system_ops_supervisor.run_swarm_audit(notify_slack=False)
                ejecutadas_str = ", ".join(exec_res.get("ejecutadas", [])) if exec_res.get("ejecutadas") else "Propuestas seleccionadas aplicadas"
                msg = (
                    f"☑️ *Propuestas Seleccionadas Aprobadas por el Padre*:\n"
                    f"• *Acciones aplicadas ({len(indices)}):* `{ejecutadas_str}`\n"
                    f"• *Pendientes restantes:* `{exec_res.get('pendientes_restantes', 0)}`\n"
                    f"• *Salud Global:* `{res.get('estado_general')}`\n"
                    f"• *Aprendizaje CBR:* Precedente grabado en `cache_ops_learning_kb` y `mia_ops_learning_history` (+1 Confianza)."
                )
                slack_bridge.send_channel_message(msg, channel=channel_id)
                if response_url:
                    try:
                        requests.post(response_url, json={"text": msg, "replace_original": False, "response_type": "in_channel"}, timeout=3)
                    except Exception:
                        pass
            except Exception as e_sel:
                print(f"| APPLY SELECTED ERROR | {e_sel}")
                slack_bridge.send_channel_message(f"❌ *Error al aplicar propuestas*: {e_sel}", channel=channel_id)

        background_tasks.add_task(do_apply_selected)
        return PlainTextResponse("OK", status_code=200)

    # 3. Botón: Aprobar Todas
    elif "approve" in val or "approve" in action_id:
        def do_apply_all():
            try:
                res_exec = system_ops_supervisor.apply_approved_actions(user_name="Padre")
                res_audit = system_ops_supervisor.run_swarm_audit(notify_slack=False)
                ejecutadas_str = ", ".join(res_exec.get("ejecutadas", [])) if res_exec.get("ejecutadas") else "Todas las tareas aplicadas"
                msg = (
                    f"✅ *Todas las Propuestas Aprobadas por el Padre*:\n"
                    f"• *Acciones ejecutadas:* `{ejecutadas_str}`\n"
                    f"• *Salud Global:* `{res_audit.get('estado_general')}`\n"
                    f"• *Aprendizaje CBR:* Registrado en memoria viva (+1 Confianza)."
                )
                slack_bridge.send_channel_message(msg, channel=channel_id)
                if response_url:
                    try:
                        requests.post(response_url, json={"text": msg, "replace_original": False, "response_type": "in_channel"}, timeout=3)
                    except Exception:
                        pass
            except Exception as e_all:
                print(f"| APPLY ALL ERROR | {e_all}")
                slack_bridge.send_channel_message(f"❌ *Error al aprobar propuestas*: {e_all}", channel=channel_id)

        background_tasks.add_task(do_apply_all)
        return PlainTextResponse("OK", status_code=200)

    # 4. Botón: Rechazar / Mantener Actual
    elif "reject" in val or "reject" in action_id:
        def do_reject():
            try:
                res_rej = system_ops_supervisor.reject_proposals(user_name="Padre")
                msg = (
                    f"⛔ *Propuestas Rechazadas por el Padre*:\n"
                    f"• Se mantiene la configuración intacta sin modificaciones.\n"
                    f"• *Aprendizaje CBR:* Precedente registrado para autocalibración preventiva."
                )
                slack_bridge.send_channel_message(msg, channel=channel_id)
                if response_url:
                    try:
                        requests.post(response_url, json={"text": msg, "replace_original": False, "response_type": "in_channel"}, timeout=3)
                    except Exception:
                        pass
            except Exception as e_rej:
                print(f"| REJECT ERROR | {e_rej}")
                slack_bridge.send_channel_message(f"❌ *Error al rechazar propuestas*: {e_rej}", channel=channel_id)

        background_tasks.add_task(do_reject)
        return PlainTextResponse("OK", status_code=200)

    # 5. Botón: Forzar Resync
    elif "resync" in val or "resync" in action_id:
        background_tasks.add_task(system_ops_supervisor.run_swarm_audit, notify_slack=True)
        return PlainTextResponse("OK", status_code=200)

    return PlainTextResponse("OK", status_code=200)

@app.post("/api/slack/command")
async def slack_command_endpoint(
    command: str = Form(...),
    text: str = Form(""),
    channel_id: str = Form(""),
    user_name: str = Form("Padre")
):
    """Slash command /mia en Slack. Retorna el pulso inmediato de los 10 Herds."""
    if command == "/mia":
        if "chat" in str(channel_id).lower() or channel_id == "C0C4QCZPTPH":
            return {
                "response_type": "ephemeral",
                "text": "Padre, el comando /mia de infraestructura opera exclusivamente en #back-office-y-backend."
            }
        report = system_ops_supervisor.run_swarm_audit(notify_slack=False)
        return {
            "response_type": "in_channel",
            "text": f"🛡️ *MIA WATCHDOG SUPERVISOR (10 Herds SRE):*\nEstado General: `{report.get('estado_general')}`\nAccuracy TensorFlow: `{report.get('herds_results', {}).get('herd_t10_swarm_neural_sentry', {}).get('tensorflow_accuracy')}%`"
        }
    return {"text": "Comando no reconocido."}

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    print(f"Iniciando MIA Ops Control Plane Microservice en puerto {port}...")
    uvicorn.run(app, host="0.0.0.0", port=port)
