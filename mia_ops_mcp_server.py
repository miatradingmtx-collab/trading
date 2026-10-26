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
import httpx
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

# ====================================================================
# MOTOR ASÍNCRONO NATIVO YAHOO FINANCE (CERO PANDAS / SUB-150MS)
# ====================================================================
MAPA_YAHOO_CANONICO = {
    "EURUSD": "EURUSD=X",
    "GBPUSD": "GBPUSD=X",
    "GBPJPY": "GBPJPY=X",
    "USDJPY": "USDJPY=X",
    "AUDUSD": "AUDUSD=X",
    "NZDCAD": "NZDCAD=X",
    "USDCAD": "USDCAD=X",
    "USDCHF": "USDCHF=X",
    "EURJPY": "EURJPY=X",
    "EURGBP": "EURGBP=X",
    "XAUUSD": "GC=F",
    "GOLD": "GC=F",
    "NASDAQ100": "NQ=F",
    "NAS100": "NQ=F",
    "US100": "NQ=F",
    "BTCUSD": "BTC-USD",
    "BTCUSDT": "BTC-USD",
    "ETHUSD": "ETH-USD",
    "ETHUSDT": "ETH-USD",
    "US30": "YM=F",
    "SP500": "ES=F"
}

def fetch_market_spot_native(symbol: str) -> Optional[float]:
    """
    Obtiene la cotización spot en tiempo real directamente desde la API JSON de Yahoo Finance
    vía HTTPX nativo (sub-100ms, 0% yfinance, 0% BeautifulSoup).
    """
    try:
        sym_clean = symbol.upper().replace("/", "").replace("_", "").replace("-", "").strip()
        yf_symbol = MAPA_YAHOO_CANONICO.get(sym_clean)
        if not yf_symbol:
            if len(sym_clean) == 6 and sym_clean.isalpha():
                yf_symbol = f"{sym_clean}=X"
            else:
                yf_symbol = sym_clean

        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{yf_symbol}?interval=1m&range=1d"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        with httpx.Client(timeout=4.0, follow_redirects=True) as client:
            resp = client.get(url, headers=headers)
            if resp.status_code == 200:
                res = resp.json().get("chart", {}).get("result", [])
                if res:
                    digits = 2 if any(k in sym_clean for k in ["JPY", "XAU", "GOLD", "US30", "SP500", "NAS"]) else 5
                    meta_p = res[0].get("meta", {}).get("regularMarketPrice")
                    if meta_p and float(meta_p) > 0:
                        return round(float(meta_p), digits)
                    quote = res[0].get("indicators", {}).get("quote", [{}])[0]
                    closes = [c for c in quote.get("close", []) if c is not None]
                    if closes:
                        return round(float(closes[-1]), digits)
        return None
    except Exception:
        return None

def fetch_market_chart_native(symbol: str, timeframe: str = "1h") -> Dict[str, Any]:
    """
    Descarga velas de mercado OHLCV, EMA50 y EMA200 directamente desde la API JSON de Yahoo Finance
    vía HTTPX nativo. Sub-150ms de latencia, 0% Pandas y 0% librerías externas pesadas.
    """
    try:
        sym_clean = symbol.upper().replace("/", "").replace("_", "").replace("-", "").strip()
        yf_symbol = MAPA_YAHOO_CANONICO.get(sym_clean)
        if not yf_symbol:
            if len(sym_clean) == 6 and sym_clean.isalpha():
                yf_symbol = f"{sym_clean}=X"
            else:
                yf_symbol = sym_clean

        tf_lower = timeframe.lower()
        interval = "1h"
        period = "30d"
        bucket_seconds = 0

        if tf_lower in ["1m", "5m"]:
            interval = "5m"
            period = "5d"
        elif tf_lower == "15m":
            interval = "15m"
            period = "14d"
        elif tf_lower == "30m":
            interval = "30m"
            period = "30d"
        elif tf_lower == "1h":
            interval = "1h"
            period = "30d"
        elif tf_lower == "2h":
            interval = "1h"
            period = "60d"
            bucket_seconds = 7200
        elif tf_lower in ["3h", "4h", "8h"]:
            interval = "1h"
            period = "60d"
            bucket_map = {"3h": 10800, "4h": 14400, "8h": 28800}
            bucket_seconds = bucket_map[tf_lower]
        elif tf_lower in ["1d", "d"]:
            interval = "1d"
            period = "1y"

        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{yf_symbol}?interval={interval}&range={period}"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

        with httpx.Client(timeout=10.0, follow_redirects=True) as client:
            resp = client.get(url, headers=headers)
            if resp.status_code != 200:
                if yf_symbol == "GC=F":
                    resp = client.get(f"https://query1.finance.yahoo.com/v8/finance/chart/XAUUSD=X?interval={interval}&range={period}", headers=headers)
                elif yf_symbol.endswith("=X"):
                    resp = client.get(f"https://query1.finance.yahoo.com/v8/finance/chart/{yf_symbol.replace('=X', '')}?interval={interval}&range={period}", headers=headers)

        if resp.status_code != 200:
            return {"status": "error", "message": f"Yahoo Finance HTTP {resp.status_code} para {yf_symbol}"}

        json_data = resp.json()
        result_list = json_data.get("chart", {}).get("result", [])
        if not result_list:
            return {"status": "error", "message": f"No se encontraron datos para {yf_symbol}"}

        result = result_list[0]
        timestamps = result.get("timestamp", [])
        quote = result.get("indicators", {}).get("quote", [{}])[0]
        opens = quote.get("open", [])
        highs = quote.get("high", [])
        lows = quote.get("low", [])
        closes = quote.get("close", [])

        candles = []
        for i in range(len(timestamps)):
            ts = timestamps[i]
            o = opens[i] if i < len(opens) else None
            h = highs[i] if i < len(highs) else None
            l = lows[i] if i < len(lows) else None
            c = closes[i] if i < len(closes) else None

            if None in (ts, o, h, l, c):
                continue

            candles.append({
                "time": int(ts),
                "open": round(float(o), 5),
                "high": round(float(h), 5),
                "low": round(float(l), 5),
                "close": round(float(c), 5)
            })

        if not candles:
            return {"status": "error", "message": f"Velas vacías tras saneamiento para {yf_symbol}"}

        # Resample si es necesario (2h, 3h, 4h, 8h)
        if bucket_seconds > 0 and len(candles) > 1:
            resampled = []
            curr_b = (candles[0]["time"] // bucket_seconds) * bucket_seconds
            bucket = []
            for c in candles:
                b_time = (c["time"] // bucket_seconds) * bucket_seconds
                if b_time == curr_b:
                    bucket.append(c)
                else:
                    if bucket:
                        resampled.append({
                            "time": curr_b,
                            "open": bucket[0]["open"],
                            "high": max(x["high"] for x in bucket),
                            "low": min(x["low"] for x in bucket),
                            "close": bucket[-1]["close"]
                        })
                    curr_b = b_time
                    bucket = [c]
            if bucket:
                resampled.append({
                    "time": curr_b,
                    "open": bucket[0]["open"],
                    "high": max(x["high"] for x in bucket),
                    "low": min(x["low"] for x in bucket),
                    "close": bucket[-1]["close"]
                })
            candles = resampled

        def _calc_ema(candles_list: list, span: int) -> list:
            if not candles_list:
                return []
            alpha = 2.0 / (span + 1.0)
            ema_out = []
            cur = candles_list[0]["close"]
            for candle in candles_list:
                cur = alpha * candle["close"] + (1.0 - alpha) * cur
                ema_out.append({"time": candle["time"], "value": round(float(cur), 5)})
            return ema_out

        return {
            "status": "success",
            "symbol": sym_clean,
            "yf_symbol": yf_symbol,
            "timeframe": timeframe,
            "data": candles,
            "ema50": _calc_ema(candles, 50),
            "ema200": _calc_ema(candles, 200),
            "total_bars": len(candles)
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

# ====================================================================
# REGISTRO DE HERRAMIENTAS DE BACK-OFFICE / OPS
# ====================================================================
OPS_TOOLS_REGISTRY = [
    {
        "name": "mcp_ops_get_spot_price",
        "description": "INFRAESTRUCTURA & FEED: Obtiene la cotización spot en tiempo real de un activo vía HTTPX nativo (sub-100ms, cero yfinance).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "symbol": {"type": "string", "description": "Símbolo del activo (ej: 'EURUSD', 'XAUUSD', 'GBPUSD')"}
            },
            "required": ["symbol"]
        }
    },

    {
        "name": "mcp_ops_get_market_chart",
        "description": "INFRAESTRUCTURA & FEED: Descarga velas de mercado OHLCV, EMA50 y EMA200 directamente desde la API JSON de Yahoo Finance vía HTTPX nativo (sub-150ms, cero Pandas).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "symbol": {"type": "string", "description": "Símbolo del activo (ej: 'EURUSD', 'XAUUSD', 'GBPUSD')"},
                "timeframe": {"type": "string", "description": "Temporalidad (ej: '1m', '5m', '15m', '30m', '1h', '2h', '3h', '4h', '8h', '1d')", "default": "1h"}
            },
            "required": ["symbol"]
        }
    },
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
    },
    {
        "name": "mcp_quant_run_post_mortem",
        "description": "QUANT SUPERVISOR: Ejecuta un Análisis Post-Mortem de los trades cerrados usando Gemini 1.5 Pro.",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    }
]

def execute_ops_tool(tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Ejecutor determinista de herramientas de Back-Office"""
    if tool_name == "mcp_ops_get_market_chart":
        sym = arguments.get("symbol", "EURUSD")
        tf = arguments.get("timeframe", "1h")
        return fetch_market_chart_native(sym, tf)

    elif tool_name == "mcp_ops_get_spot_price":
        sym = arguments.get("symbol", "EURUSD")
        p = fetch_market_spot_native(sym)
        return {"status": "SUCCESS" if p else "ERROR", "symbol": sym, "price": p}

    elif tool_name == "mcp_ops_sync_mt5_cache":
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

    elif tool_name == "mcp_quant_run_post_mortem":
        from mia_post_mortem_agent import MiaQuantSupervisor
        agent = MiaQuantSupervisor()
        agent.analyze_recent_losses()
        return {"status": "SUCCESS", "message": "Análisis Post-Mortem ejecutado por Quant Supervisor"}

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
