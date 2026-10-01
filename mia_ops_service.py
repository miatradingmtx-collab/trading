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
from fastapi.responses import JSONResponse, PlainTextResponse
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
    """Retorna el último pulso de salud de los 10 Herds desde Upstash."""
    return system_ops_supervisor.run_swarm_audit(notify_slack=False)

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
        upstash_url = os.getenv("UPSTASH_REDIS_REST_URL", "https://certain-gnat-160816.upstash.io")
        upstash_token = os.getenv("UPSTASH_REDIS_REST_TOKEN", "gQAAAAAAAnQwAAIgcDI2YTA5YjRlZDU2MDM0OWU5ODhlZjBlYTk4ODYyZDg0OA")
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
    upstash_url = os.getenv("UPSTASH_REDIS_REST_URL", "https://certain-gnat-160816.upstash.io")
    upstash_token = os.getenv("UPSTASH_REDIS_REST_TOKEN", "gQAAAAAAAnQwAAIgcDI2YTA5YjRlZDU2MDM0OWU5ODhlZjBlYTk4ODYyZDg0OA")
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
    upstash_url = os.getenv("UPSTASH_REDIS_REST_URL", "https://certain-gnat-160816.upstash.io")
    upstash_token = os.getenv("UPSTASH_REDIS_REST_TOKEN", "gQAAAAAAAnQwAAIgcDI2YTA5YjRlZDU2MDM0OWU5ODhlZjBlYTk4ODYyZDg0OA")
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
    channel_id = event.get("channel", "")

    # Aislamiento de canales: Solo procesar #back-office-y-backend
    if "chat" in str(channel_id).lower() or channel_id == "C0C4QCZPTPH":
        return PlainTextResponse("IGNORED_NON_OPS_CHANNEL", status_code=200)

    if event.get("type") in ["app_mention", "message"] and not event.get("bot_id"):
        text = event.get("text", "")
        if "auditar" in text.lower() or "resync" in text.lower() or "estado" in text.lower():
            background_tasks.add_task(system_ops_supervisor.run_swarm_audit, notify_slack=True)

    return PlainTextResponse("EVENT_RECEIVED", status_code=200)

@app.post("/api/slack/interactions")
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

    if action_id == "approve_triage_action":
        # Aprobar todas las propuestas
        res = system_ops_supervisor.apply_approved_actions(user_name="Padre")
        slack_bridge.send_channel_message(
            text=f"✅ *[AUTORIZADO POR EL PADRE]:* Se han aplicado {len(res.get('ejecutadas', []))} propuestas técnicas en caliente. (+1 Confianza registrada en KB)",
            channel="C0C4ZMFCMJ8"
        )
    elif action_id == "reject_triage_action":
        # Rechazar propuestas
        res = system_ops_supervisor.reject_proposals(user_name="Padre")
        slack_bridge.send_channel_message(
            text=f"⛔ *[RECHAZADO POR EL PADRE]:* Se mantendrá la configuración actual. Precedente registrado en KB para autocalibración.",
            channel="C0C4ZMFCMJ8"
        )
    elif action_id == "resync_action":
        # Forzar resync
        background_tasks.add_task(system_ops_supervisor.run_swarm_audit, notify_slack=True)

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
