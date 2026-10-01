"""
MIA OPS MCP SERVER - Model Context Protocol para Back-Office y DevOps
=====================================================================
Servidor MCP independiente y desacoplado del MCP de Trading (mia_mcp_server.py).
Diseñado bajo el principio de Menor Privilegio (Least Privilege) y Separación de Dominios:
- Este servidor expone ÚNICAMENTE herramientas de infraestructura, base de datos,
  salud del sistema, redondeo numérico y ChatOps/Slack.
- Los agentes de trading (ATLAS, TIDAL, etc.) NO tienen acceso a este servidor,
  evitando que agentes de mercado ejecuten accidentalmente acciones destructivas en la BD.
- Compatible con JSON-RPC 2.0 (MCP Protocol) y endpoints REST (/api/mcp/ops/...).
"""

import os
import json
import time
import datetime
import requests
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from mia_system_ops_swarm import system_ops_supervisor
from mia_slack_bridge import slack_bridge

ops_mcp_router = APIRouter(prefix="/mcp/ops", tags=["MCP Ops Server"])
api_ops_mcp_router = APIRouter(prefix="/api/mcp/ops", tags=["MCP Ops Tools API"])

# Modelos JSON-RPC 2.0
class OpsMCPRequest(BaseModel):
    jsonrpc: str = "2.0"
    id: Optional[Any] = 1
    method: str
    params: Optional[Dict[str, Any]] = None

class OpsMCPResponse(BaseModel):
    jsonrpc: str = "2.0"
    id: Optional[Any] = 1
    result: Optional[Any] = None
    error: Optional[Dict[str, Any]] = None

# ====================================================================
# REGISTRO DE HERRAMIENTAS DE BACK-OFFICE / OPS
# ====================================================================
OPS_TOOLS_REGISTRY = [
    {
        "name": "mcp_ops_sync_mt5_cache",
        "description": "HERD T1: Sincroniza cache_mt5 con el broker, elimina órdenes fantasma cerradas y recalcula equidad y márgenes.",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "mcp_ops_recalibrate_regla_de_3",
        "description": "HERD T2: Recalibra dinámicamente el Top 1-3 de confirmaciones en mia_kb/regla_de_3 y renueva el timestamp a la fecha actual.",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "mcp_ops_sanitize_pnl_decimals",
        "description": "HERD T3: Sanitiza colas flotantes IEEE 754 en PnL simulados de shadow_trades_audit a 2 decimales exactos.",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "mcp_ops_get_system_health",
        "description": "HERD T4: Monitorea latencia de red en Upstash Redis, contenedores Railway y estado de los streams.",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "mcp_ops_dispatch_slack_approval",
        "description": "CHATOPS: Despacha una solicitud con botones interactivos [APROBAR] / [RECHAZAR] a Slack para decisiones humanas.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "action_id": {"type": "string", "description": "Identificador único de la acción"},
                "title": {"type": "string", "description": "Título de la solicitud"},
                "details": {"type": "string", "description": "Detalles técnicos de la acción a ejecutar"}
            },
            "required": ["action_id", "title", "details"]
        }
    },
    {
        "name": "mcp_ops_run_full_audit",
        "description": "WATCHDOG MASTER: Ejecuta la auditoría integral y sincronización de los 4 Herds de infraestructura.",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "mcp_ops_chat_with_mia",
        "description": "SUPERVISOR CHAT: Diálogo interactivo con Mia Supervisor (análisis quant, trading, infraestructura, o consultas generales con Gemini/OpenRouter).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "message": {"type": "string", "description": "Mensaje o consulta del usuario"},
                "channel": {"type": "string", "description": "Canal de origen opcional (ej: 'mia-chat' o 'back-office-y-backend')"}
            },
            "required": ["message"]
        }
    },
    {
        "name": "mcp_ops_send_slack_message",
        "description": "CHATOPS SLACK: Envía un mensaje formateado a cualquier canal de Slack (#mia-chat, #back-office-y-backend) usando SLACK_BOT_TOKEN o Webhook.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "message": {"type": "string", "description": "Texto formateado en Markdown para Slack"},
                "channel": {"type": "string", "description": "Nombre o ID del canal destino (ej: '#mia-chat', '#back-office-y-backend')"}
            },
            "required": ["message"]
        }
    },
    {
        "name": "mcp_ops_get_slack_status",
        "description": "CHATOPS SLACK: Verifica la conectividad, credenciales (Bot Token xoxb, Webhook) y canales activos de Slack.",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    }
]

def execute_ops_tool(tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Ejecutor determinista de herramientas de Back-Office"""
    if tool_name == "mcp_ops_sync_mt5_cache":
        return system_ops_supervisor.herd_db.execute(system_ops_supervisor.db)

    elif tool_name == "mcp_ops_recalibrate_regla_de_3":
        return system_ops_supervisor.herd_kb.execute(system_ops_supervisor.db)

    elif tool_name == "mcp_ops_sanitize_pnl_decimals":
        return system_ops_supervisor.herd_kpi.execute(system_ops_supervisor.db)

    elif tool_name == "mcp_ops_get_system_health":
        return system_ops_supervisor.herd_devops.execute(system_ops_supervisor.db)

    elif tool_name == "mcp_ops_dispatch_slack_approval":
        action_id = arguments.get("action_id", f"act_{int(time.time())}")
        title = arguments.get("title", "Confirmación de Operación")
        details = arguments.get("details", "Acción requerida por el Watchdog.")
        sent = slack_bridge.send_approval_request(action_id, title, details)
        return {"status": "sent" if sent else "skipped_no_webhook", "action_id": action_id}

    elif tool_name == "mcp_ops_run_full_audit":
        return system_ops_supervisor.run_swarm_audit()

    elif tool_name == "mcp_ops_chat_with_mia":
        from mia_supervisor_chat import chat_with_mia
        msg = arguments.get("message", "Hola Mia")
        ch = arguments.get("channel")
        engine = "gemini" if ch and "chat" in str(ch).lower() else None
        reply = chat_with_mia(msg, force_engine=engine)
        return {"status": "SUCCESS", "reply": reply, "engine": engine or "auto_detected"}

    elif tool_name == "mcp_ops_send_slack_message":
        msg = arguments.get("message", "")
        ch = arguments.get("channel")
        sent = slack_bridge.send_channel_message(msg, channel=ch)
        return {"status": "SUCCESS" if sent else "ERROR", "delivered": sent, "channel": ch or "default_webhook"}

    elif tool_name == "mcp_ops_get_slack_status":
        has_token = bool(slack_bridge.bot_token)
        has_webhook = bool(slack_bridge.webhook_url)
        token_prefix = slack_bridge.bot_token[:9] + "..." if has_token else "NOT_SET"
        return {
            "status": "OPERATIONAL" if (has_token or has_webhook) else "DISCONNECTED",
            "bot_user_oauth_token_active": has_token,
            "bot_token_prefix": token_prefix,
            "incoming_webhook_active": has_webhook,
            "supported_channels": ["#back-office-y-backend", "#mia-chat"],
            "direct_api_enabled": has_token
        }

    else:
        raise ValueError(f"Herramienta MCP Ops desconocida: '{tool_name}'")


# ====================================================================
# PROTOCOLO MCP JSON-RPC 2.0 (/mcp/ops)
# ====================================================================

@ops_mcp_router.post("")
@ops_mcp_router.post("/")
async def handle_ops_mcp_jsonrpc(req: OpsMCPRequest):
    method = req.method
    params = req.params or {}
    req_id = req.id

    if method in ["initialize", "mcp.initialize"]:
        return OpsMCPResponse(
            id=req_id,
            result={
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {"listChanged": False}},
                "serverInfo": {
                    "name": "MIA-OPS-MCP-SERVER",
                    "version": "1.0.0",
                    "description": "Servidor MCP para Back-Office, Salud de Infraestructura y ChatOps"
                }
            }
        )

    elif method in ["tools/list", "mcp.tools.list"]:
        return OpsMCPResponse(id=req_id, result={"tools": OPS_TOOLS_REGISTRY})

    elif method in ["tools/call", "mcp.tools.call"]:
        tool_name = params.get("name")
        args = params.get("arguments", {})
        try:
            output = execute_ops_tool(tool_name, args)
            return OpsMCPResponse(
                id=req_id,
                result={
                    "content": [{"type": "text", "text": json.dumps(output, indent=2, ensure_ascii=False)}],
                    "isError": False
                }
            )
        except Exception as e:
            return OpsMCPResponse(id=req_id, error={"code": -32603, "message": str(e)})

    else:
        return OpsMCPResponse(id=req_id, error={"code": -32601, "message": f"Método no soportado: '{method}'"})


# ====================================================================
# ENDPOINTS REST DIRECTOS (/api/mcp/ops/...)
# ====================================================================

@api_ops_mcp_router.get("/health")
async def mcp_ops_health_rest():
    """Healthcheck REST para el servidor MCP Ops"""
    return {
        "status": "HEALTHY",
        "domain": "BACK_OFFICE_DEVOPS",
        "total_tools": len(OPS_TOOLS_REGISTRY)
    }

@api_ops_mcp_router.get("/tools")
async def list_ops_tools_rest():
    """Lista las herramientas de infraestructura disponibles en el Servidor MCP Ops"""
    return {
        "status": "success",
        "domain": "BACK_OFFICE_DEVOPS",
        "total_tools": len(OPS_TOOLS_REGISTRY),
        "tools": OPS_TOOLS_REGISTRY
    }

@api_ops_mcp_router.post("/execute/{tool_name}")
async def execute_ops_tool_rest(tool_name: str, payload: Dict[str, Any] = None):
    """Ejecuta una herramienta de infraestructura vía REST"""
    try:
        args = payload or {}
        result = execute_ops_tool(tool_name, args)
        return {"status": "success", "tool": tool_name, "result": result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
