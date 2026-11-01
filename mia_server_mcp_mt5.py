"""
====================================================================
MIA SERVER MCP MT5 - Model Context Protocol para MetaTrader 5
====================================================================
Microservicio independiente y desacoplado para la ejecución, monitoreo
de telemetría, gestión de órdenes y Cascada RUNE en MetaTrader 5.

Diseñado bajo el principio de Menor Privilegio y Separación de Dominios:
- Este servidor gestiona EXCLUSIVAMENTE la comunicación con el broker MT5.
- Expone herramientas estándar JSON-RPC 2.0 (MCP Specification) y REST.
- Cero dependencia de servicios de suscripción de terceros (MetaAPI).
- Interfaz nativa para agentes autónomos (RUNE, LUMEN, Watchdog, Quant).

Herramientas Expuestas:
  1. mcp_mt5_account_summary: Balance, equidad, margen libre, apalancamiento.
  2. mcp_mt5_get_open_positions: Posiciones vivas con tickets, SL, TP y PnL.
  3. mcp_mt5_open_order: Apertura Market Buy/Sell con sizing y SL/TP.
  4. mcp_mt5_close_partial_order: Cobro parcial de volumen (Fase 1 Cascada RUNE).
  5. mcp_mt5_modify_sl_tp: Ajuste de SL para Break-Even (+2.5 pips) y Trailing Locks.
  6. mcp_mt5_close_position: Cierre total de posición en mercado (Fase 4 Front-Run).
  7. mcp_mt5_get_rates: Descarga de velas recientes (OHLCV) del broker.
====================================================================
"""

import os
import sys
import json
import time
import datetime
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

# Intento de importación defensiva de la librería oficial MetaTrader5
try:
    import MetaTrader5 as mt5
    MT5_AVAILABLE = True
except ImportError:
    mt5 = None
    MT5_AVAILABLE = False

# Variables de Configuración desde Entorno
MT5_LOGIN = int(os.getenv("MT5_LOGIN", "112472341"))
MT5_PASSWORD = os.getenv("MT5_PASSWORD", "*uR8HmJh")
MT5_SERVER = os.getenv("MT5_SERVER", "MetaQuotes-Demo")
MT5_PATH = os.getenv("MT5_PATH", None)
FASTAPI_URL = os.getenv("FASTAPI_URL", "https://trading-production-927a.up.railway.app")

PORTAFOLIO_CANONICO = ["EURUSD", "GBPUSD", "AUDUSD", "GBPJPY", "XAUUSD", "NZDCAD"]
PORTAFOLIO_SANDBOX = ["NZDCAD"]  # Confinado a entrenamiento (0 órdenes reales)

BASE_BALANCE_USD = 5000.0

app = FastAPI(
    title="Mia MT5 MCP Server",
    description="Servidor MCP de Ejecución y Telemetría Nativa MetaTrader 5",
    version="1.0.0"
)

mt5_mcp_router = APIRouter(prefix="/mcp/mt5", tags=["MCP MT5 Server"])
api_mt5_router = APIRouter(prefix="/api/mcp/mt5", tags=["MCP MT5 Tools REST"])

# ====================================================================
# MODELOS PYDANTIC MCP JSON-RPC 2.0
# ====================================================================

class MCPRequest(BaseModel):
    jsonrpc: str = "2.0"
    id: Optional[Any] = 1
    method: str
    params: Optional[Dict[str, Any]] = None

class MCPResponse(BaseModel):
    jsonrpc: str = "2.0"
    id: Optional[Any] = 1
    result: Optional[Any] = None
    error: Optional[Dict[str, Any]] = None


# ====================================================================
# GESTOR DE CONEXIÓN CON EL TERMINAL METATRADER 5
# ====================================================================

_mt5_connected = False

def ensure_mt5_connected() -> bool:
    """Verifica y asegura la conexión con el terminal MetaTrader 5"""
    global _mt5_connected
    if not MT5_AVAILABLE:
        return False
    
    # Comprobar si ya está inicializado y conectado
    try:
        terminal_info = mt5.terminal_info()
        if terminal_info is not None and terminal_info.connected:
            _mt5_connected = True
            return True
    except Exception:
        pass

    # 1. Intento de conexión nativa al terminal en ejecución
    ok = False
    try:
        if MT5_PATH:
            ok = mt5.initialize(path=MT5_PATH)
        else:
            ok = mt5.initialize()
    except Exception as e:
        print(f"[MT5 MCP] Error en initialize() base: {e}")

    # 2. Si falló la conexión base y hay credenciales explícitas, intentar con login
    if not ok and MT5_LOGIN and MT5_PASSWORD and MT5_SERVER:
        try:
            init_kwargs = {"login": MT5_LOGIN, "password": MT5_PASSWORD, "server": MT5_SERVER}
            if MT5_PATH:
                init_kwargs["path"] = MT5_PATH
            ok = mt5.initialize(**init_kwargs)
        except Exception as e:
            print(f"[MT5 MCP] Error en initialize() con credenciales: {e}")

    if ok:
        # Verificar cuenta activa
        acc = mt5.account_info()
        if acc and acc.login == MT5_LOGIN:
            _mt5_connected = True
            print(f"[MT5 MCP] Conectado exitosamente a la cuenta oficial {acc.server} (Login: {acc.login} | Balance: ${acc.balance:.2f})")
            return True

        # Si el terminal está en otra cuenta o no autenticado, forzar login en la cuenta oficial 112472341
        if MT5_LOGIN and MT5_PASSWORD and MT5_SERVER:
            auth = mt5.login(login=MT5_LOGIN, password=MT5_PASSWORD, server=MT5_SERVER)
            if auth:
                _mt5_connected = True
                print(f"[MT5 MCP] Login oficial exitoso en {MT5_SERVER} (Login: {MT5_LOGIN})")
                return True
            else:
                print(f"[MT5 MCP] Falló autenticación en cuenta oficial {MT5_LOGIN} ({MT5_SERVER}): {mt5.last_error()}")
                _mt5_connected = False
                return False
        _mt5_connected = True
        return True
    else:
        print(f"[MT5 MCP] No se pudo inicializar terminal MT5: {mt5.last_error()}")
        _mt5_connected = False
        return False


# ====================================================================
# IMPLEMENTACIÓN DE HERRAMIENTAS MCP DE METATRADER 5
# ====================================================================

def resolve_broker_symbol(sym: str) -> str:
    """Resuelve automáticamente el símbolo con sufijos del broker (ej: EURUSD -> EURUSD...)"""
    sym_clean = sym.upper().replace("/", "").replace("_", "")
    if not MT5_AVAILABLE:
        return sym_clean
    try:
        if mt5.symbol_info(sym_clean) is not None:
            return sym_clean
        symbols = mt5.symbols_get()
        if symbols:
            for s in symbols:
                if s.name == sym_clean or s.name.startswith(sym_clean):
                    mt5.symbol_select(s.name, True)
                    return s.name
    except Exception:
        pass
    return sym_clean


def tool_account_summary() -> Dict[str, Any]:
    """Retorna el estado auditado de la cuenta, balance, equidad y drawdown vs Base $5,000 USD"""
    if not ensure_mt5_connected():
        return {
            "status": "DISCONNECTED",
            "error": "Terminal MT5 no disponible o sin conexión",
            "login": MT5_LOGIN,
            "server": MT5_SERVER,
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
        }
    
    acc = mt5.account_info()
    if not acc:
        return {"status": "ERROR", "error": str(mt5.last_error())}
    
    ad = acc._asdict()
    balance = float(ad.get("balance", 0.0))
    equity = float(ad.get("equity", 0.0))
    profit = float(ad.get("profit", 0.0))
    margin = float(ad.get("margin", 0.0))
    margin_free = float(ad.get("margin_free", 0.0))
    
    # Ley de Asimetría Matemática D / (1 - D) vs Base $5,000 USD
    drawdown_base_usd = round(balance - BASE_BALANCE_USD, 2)
    drawdown_base_pct = round((drawdown_base_usd / BASE_BALANCE_USD) * 100, 2)
    if balance < BASE_BALANCE_USD and balance > 0:
        recup_pct = round(((BASE_BALANCE_USD - balance) / balance) * 100, 2)
        estado_cuenta = f"EN RECUPERACION / BAJO DRAWDOWN SEVERO ACUMULADO (${drawdown_base_usd} USD / {drawdown_base_pct}% vs Base $5,000)"
    else:
        recup_pct = 0.0
        estado_cuenta = "RESTABLECIDA / EN MAXIMOS HISTORICOS (>= $5,000 USD)"

    return {
        "status": "CONNECTED",
        "login": ad.get("login"),
        "name": ad.get("name"),
        "server": ad.get("server"),
        "currency": ad.get("currency", "USD"),
        "balance": balance,
        "equity": equity,
        "profit": profit,
        "margin": margin,
        "margin_free": margin_free,
        "margin_level": float(ad.get("margin_level", 0.0)),
        "leverage": ad.get("leverage", 100),
        "trade_allowed": ad.get("trade_allowed", False),
        "trade_expert": ad.get("trade_expert", False),
        "drawdown_base_usd": drawdown_base_usd,
        "drawdown_base_pct": drawdown_base_pct,
        "recuperacion_requerida_base_pct": recup_pct,
        "estado_cuenta": estado_cuenta,
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
    }


def tool_get_open_positions(symbol: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retorna las posiciones activas en el broker con telemetría de Cascada RUNE"""
    if not ensure_mt5_connected():
        return []
    
    if symbol:
        positions = mt5.positions_get(symbol=symbol)
    else:
        positions = mt5.positions_get()
    
    if positions is None:
        return []
    
    resultado = []
    for p in positions:
        pd = p._asdict()
        tipo_str = "BUY" if pd.get("type") == 0 else "SELL"
        resultado.append({
            "ticket": str(pd.get("ticket")),
            "symbol": pd.get("symbol"),
            "type": tipo_str,
            "volume": float(pd.get("volume", 0.0)),
            "open_price": float(pd.get("price_open", 0.0)),
            "current_price": float(pd.get("price_current", 0.0)),
            "sl": float(pd.get("sl", 0.0)),
            "tp": float(pd.get("tp", 0.0)),
            "pnl": float(pd.get("profit", 0.0)),
            "magic": pd.get("magic", 0),
            "comment": pd.get("comment", ""),
            "time_setup": datetime.datetime.fromtimestamp(pd.get("time", time.time()), datetime.timezone.utc).isoformat()
        })
    return resultado


def tool_open_order(
    symbol: str,
    action: str,
    volume: float,
    sl: float = 0.0,
    tp: float = 0.0,
    comment: str = "MIA_RUNE_MCP",
    magic: int = 234000
) -> Dict[str, Any]:
    """Ejecuta una orden de compra o venta a mercado con Stop Loss y Take Profit inicial"""
    sym_raw = symbol.upper().replace("/", "").replace("_", "")
    
    # Blindaje de Sandbox: Confinamiento estricto de NZDCAD
    if sym_raw in PORTAFOLIO_SANDBOX:
        return {
            "status": "BLOCKED_SANDBOX",
            "message": f"El par {sym_raw} pertenece estrictamente al Sandbox de entrenamiento. Órdenes a mercado bloqueadas por Constitución RUNE."
        }
    
    if not ensure_mt5_connected():
        return {"status": "ERROR", "error": "Terminal MT5 sin conexión"}
    
    sym = resolve_broker_symbol(sym_raw)
    sym_info = mt5.symbol_info(sym)
    if not sym_info:
        # Intentar selección de símbolo
        if not mt5.symbol_select(sym, True):
            return {"status": "ERROR", "error": f"Símbolo '{sym}' no disponible en el broker"}
        sym_info = mt5.symbol_info(sym)
        if not sym_info:
            return {"status": "ERROR", "error": f"No se pudo obtener información de '{sym}'"}

    is_buy = action.upper() in ["BUY", "COMPRA"]
    order_type = mt5.ORDER_TYPE_BUY if is_buy else mt5.ORDER_TYPE_SELL
    price = sym_info.ask if is_buy else sym_info.bid
    digits = sym_info.digits
    
    order_request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": sym,
        "volume": round(float(volume), 2),
        "type": order_type,
        "price": round(float(price), digits),
        "sl": round(float(sl), digits) if sl else 0.0,
        "tp": round(float(tp), digits) if tp else 0.0,
        "deviation": 20,
        "magic": int(magic),
        "comment": comment[:31],
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }
    
    result = mt5.order_send(order_request)
    if not result:
        return {"status": "ERROR", "error": str(mt5.last_error())}
    
    rd = result._asdict()
    if rd.get("retcode") == mt5.TRADE_RETCODE_DONE:
        return {
            "status": "SUCCESS",
            "ticket": str(rd.get("order")),
            "deal": str(rd.get("deal")),
            "symbol": sym,
            "action": "BUY" if is_buy else "SELL",
            "volume": float(volume),
            "price": float(rd.get("price", price)),
            "sl": float(sl),
            "tp": float(tp),
            "comment": comment,
            "retcode": rd.get("retcode")
        }
    else:
        return {
            "status": "REJECTED",
            "retcode": rd.get("retcode"),
            "comment": rd.get("comment"),
            "error": f"Broker rechazó orden: retcode {rd.get('retcode')} - {rd.get('comment')}"
        }


def tool_close_partial_order(ticket: int, volume_to_close: float) -> Dict[str, Any]:
    """Cierra parcialmente una posición existente (Fase 1 de la Cascada RUNE: cobro del 50%)"""
    if not ensure_mt5_connected():
        return {"status": "ERROR", "error": "Terminal MT5 sin conexión"}
    
    t_int = int(ticket)
    positions = mt5.positions_get(ticket=t_int)
    if not positions or len(positions) == 0:
        return {"status": "NOT_FOUND", "error": f"Posición con ticket {t_int} no encontrada"}
    
    pos = positions[0]._asdict()
    sym = pos.get("symbol")
    pos_type = pos.get("type")
    current_volume = float(pos.get("volume", 0.0))
    vol_close = round(float(volume_to_close), 2)
    
    if vol_close > current_volume:
        vol_close = current_volume
        
    sym_info = mt5.symbol_info(sym)
    if not sym_info:
        return {"status": "ERROR", "error": f"Símbolo '{sym}' no disponible"}
    
    # Para cerrar compra enviamos SELL; para cerrar venta enviamos BUY
    close_type = mt5.ORDER_TYPE_SELL if pos_type == 0 else mt5.ORDER_TYPE_BUY
    price = sym_info.bid if pos_type == 0 else sym_info.ask
    
    close_request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "position": t_int,
        "symbol": sym,
        "volume": vol_close,
        "type": close_type,
        "price": price,
        "deviation": 20,
        "magic": pos.get("magic", 234000),
        "comment": f"RUNE_TP1_PARTIAL_{t_int}"[:31],
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }
    
    result = mt5.order_send(close_request)
    if not result:
        return {"status": "ERROR", "error": str(mt5.last_error())}
    
    rd = result._asdict()
    if rd.get("retcode") == mt5.TRADE_RETCODE_DONE:
        rem_vol = round(current_volume - vol_close, 2)
        return {
            "status": "SUCCESS",
            "ticket": str(t_int),
            "deal": str(rd.get("deal")),
            "volume_closed": vol_close,
            "volume_remaining": rem_vol,
            "close_price": float(rd.get("price", price)),
            "retcode": rd.get("retcode")
        }
    else:
        return {
            "status": "REJECTED",
            "retcode": rd.get("retcode"),
            "comment": rd.get("comment"),
            "error": f"Fallo al cerrar parcial: {rd.get('comment')}"
        }


def tool_modify_sl_tp(ticket: int, sl: Optional[float] = None, tp: Optional[float] = None) -> Dict[str, Any]:
    """Modifica el Stop Loss o Take Profit de una posición (Fase 2 BE +2.5 pips y Fase 3 Trailing Locks)"""
    if not ensure_mt5_connected():
        return {"status": "ERROR", "error": "Terminal MT5 sin conexión"}
    
    t_int = int(ticket)
    positions = mt5.positions_get(ticket=t_int)
    if not positions or len(positions) == 0:
        return {"status": "NOT_FOUND", "error": f"Posición con ticket {t_int} no encontrada"}
    
    pos = positions[0]._asdict()
    sym = pos.get("symbol")
    sym_info = mt5.symbol_info(sym)
    digits = sym_info.digits if sym_info else 5
    
    new_sl = round(float(sl), digits) if sl is not None else float(pos.get("sl", 0.0))
    new_tp = round(float(tp), digits) if tp is not None else float(pos.get("tp", 0.0))
    
    request = {
        "action": mt5.TRADE_ACTION_SLTP,
        "position": t_int,
        "symbol": sym,
        "sl": new_sl,
        "tp": new_tp,
    }
    
    result = mt5.order_send(request)
    if not result:
        return {"status": "ERROR", "error": str(mt5.last_error())}
    
    rd = result._asdict()
    if rd.get("retcode") == mt5.TRADE_RETCODE_DONE:
        return {
            "status": "SUCCESS",
            "ticket": str(t_int),
            "symbol": sym,
            "new_sl": new_sl,
            "new_tp": new_tp,
            "retcode": rd.get("retcode")
        }
    else:
        return {
            "status": "REJECTED",
            "retcode": rd.get("retcode"),
            "comment": rd.get("comment"),
            "error": f"Error al modificar SL/TP: {rd.get('comment')}"
        }


def tool_close_position(ticket: int) -> Dict[str, Any]:
    """Cierra el 100% de la posición en mercado (Fase 4 Front-Run TP o Cierre Total Defensivo)"""
    if not ensure_mt5_connected():
        return {"status": "ERROR", "error": "Terminal MT5 sin conexión"}
    
    t_int = int(ticket)
    positions = mt5.positions_get(ticket=t_int)
    if not positions or len(positions) == 0:
        return {"status": "NOT_FOUND", "error": f"Posición con ticket {t_int} no encontrada"}
    
    pos = positions[0]._asdict()
    return tool_close_partial_order(ticket=t_int, volume_to_close=float(pos.get("volume", 0.0)))


def tool_get_rates(symbol: str, timeframe: str = "1h", count: int = 100) -> Dict[str, Any]:
    """Descarga velas OHLCV recientes directas del broker sin intermediarios"""
    if not ensure_mt5_connected():
        return {"status": "ERROR", "error": "Terminal MT5 sin conexión"}
    
    sym_raw = symbol.upper().replace("/", "").replace("_", "")
    sym = resolve_broker_symbol(sym_raw)
    tf_map = {
        "1m": mt5.TIMEFRAME_M1,
        "5m": mt5.TIMEFRAME_M5,
        "15m": mt5.TIMEFRAME_M15,
        "30m": mt5.TIMEFRAME_M30,
        "1h": mt5.TIMEFRAME_H1,
        "4h": mt5.TIMEFRAME_H4,
        "1d": mt5.TIMEFRAME_D1,
    }
    tf = tf_map.get(timeframe.lower(), mt5.TIMEFRAME_H1)
    rates = mt5.copy_rates_from_pos(sym, tf, 0, min(int(count), 500))
    if rates is None or len(rates) == 0:
        return {"status": "ERROR", "error": f"No se pudieron descargar velas de '{sym}'"}
    
    candles = []
    for r in rates[-min(len(rates), 100):]:
        candles.append({
            "time": datetime.datetime.fromtimestamp(r['time'], datetime.timezone.utc).isoformat(),
            "open": float(r['open']),
            "high": float(r['high']),
            "low": float(r['low']),
            "close": float(r['close']),
            "tick_volume": int(r['tick_volume'])
        })
    
    return {
        "status": "SUCCESS",
        "symbol": sym,
        "timeframe": timeframe,
        "count": len(candles),
        "candles": candles
    }


# ====================================================================
# CATÁLOGO DE HERRAMIENTAS MCP (JSON-RPC SCHEMA)
# ====================================================================

MCP_TOOLS_REGISTRY = [
    {
        "name": "mcp_mt5_account_summary",
        "description": "Retorna balance, equidad, margen libre, apalancamiento y estado de la cuenta vs Base $5,000 USD.",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "mcp_mt5_get_open_positions",
        "description": "Retorna la lista de posiciones vivas en el broker con telemetría de Cascada RUNE y PnL flotante.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "symbol": {"type": "string", "description": "Filtro opcional por símbolo (ej. EURUSD)"}
            },
            "required": []
        }
    },
    {
        "name": "mcp_mt5_open_order",
        "description": "Ejecuta una orden a mercado (Market BUY o SELL) con Stop Loss y Take Profit.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "symbol": {"type": "string", "description": "Símbolo oficial del portafolio (ej: EURUSD, GBPUSD, AUDUSD, GBPJPY, XAUUSD)"},
                "action": {"type": "string", "enum": ["BUY", "SELL"], "description": "Acción a ejecutar"},
                "volume": {"type": "number", "description": "Volumen en lotes (ej: 0.10, 0.21)"},
                "sl": {"type": "number", "description": "Precio de Stop Loss"},
                "tp": {"type": "number", "description": "Precio de Take Profit"},
                "comment": {"type": "string", "description": "Comentario identificador del trade"},
                "magic": {"type": "integer", "description": "Número mágico (default 234000)"}
            },
            "required": ["symbol", "action", "volume"]
        }
    },
    {
        "name": "mcp_mt5_close_partial_order",
        "description": "Cierra parcialmente una posición activa (Fase 1 Cascada RUNE: cobro del 50% de volumen).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "ticket": {"type": "integer", "description": "Número de ticket de la posición"},
                "volume_to_close": {"type": "number", "description": "Volumen en lotes a liquidar"}
            },
            "required": ["ticket", "volume_to_close"]
        }
    },
    {
        "name": "mcp_mt5_modify_sl_tp",
        "description": "Modifica el Stop Loss (Fase 2 Break-Even +2.5 pips y Fase 3 Trailing Locks) de una posición activa.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "ticket": {"type": "integer", "description": "Número de ticket de la posición"},
                "sl": {"type": "number", "description": "Nuevo precio de Stop Loss"},
                "tp": {"type": "number", "description": "Nuevo precio de Take Profit"}
            },
            "required": ["ticket"]
        }
    },
    {
        "name": "mcp_mt5_close_position",
        "description": "Cierra el 100% de una posición en mercado (Fase 4 Front-Run TP o Cierre Total).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "ticket": {"type": "integer", "description": "Número de ticket de la posición a liquidar"}
            },
            "required": ["ticket"]
        }
    },
    {
        "name": "mcp_mt5_get_rates",
        "description": "Descarga velas OHLCV recientes directamente del broker sin intermediarios.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "symbol": {"type": "string", "description": "Símbolo (ej. EURUSD)"},
                "timeframe": {"type": "string", "enum": ["1m", "5m", "15m", "30m", "1h", "4h", "1d"], "description": "Temporalidad"},
                "count": {"type": "integer", "description": "Número de velas (máx 100)"}
            },
            "required": ["symbol"]
        }
    }
]


def execute_mt5_tool(tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Despachador determinista de herramientas MCP MT5"""
    if tool_name == "mcp_mt5_account_summary":
        return tool_account_summary()
    elif tool_name == "mcp_mt5_get_open_positions":
        sym = arguments.get("symbol")
        return {"positions": tool_get_open_positions(sym)}
    elif tool_name == "mcp_mt5_open_order":
        return tool_open_order(
            symbol=arguments.get("symbol", "EURUSD"),
            action=arguments.get("action", "BUY"),
            volume=float(arguments.get("volume", 0.01)),
            sl=float(arguments.get("sl", 0.0)),
            tp=float(arguments.get("tp", 0.0)),
            comment=str(arguments.get("comment", "MIA_RUNE_MCP")),
            magic=int(arguments.get("magic", 234000))
        )
    elif tool_name == "mcp_mt5_close_partial_order":
        return tool_close_partial_order(
            ticket=int(arguments.get("ticket", 0)),
            volume_to_close=float(arguments.get("volume_to_close", 0.01))
        )
    elif tool_name == "mcp_mt5_modify_sl_tp":
        return tool_modify_sl_tp(
            ticket=int(arguments.get("ticket", 0)),
            sl=float(arguments["sl"]) if "sl" in arguments and arguments["sl"] is not None else None,
            tp=float(arguments["tp"]) if "tp" in arguments and arguments["tp"] is not None else None
        )
    elif tool_name == "mcp_mt5_close_position":
        return tool_close_position(ticket=int(arguments.get("ticket", 0)))
    elif tool_name == "mcp_mt5_get_rates":
        return tool_get_rates(
            symbol=arguments.get("symbol", "EURUSD"),
            timeframe=arguments.get("timeframe", "1h"),
            count=int(arguments.get("count", 100))
        )
    else:
        raise ValueError(f"Herramienta MCP MT5 desconocida: '{tool_name}'")


# ====================================================================
# ENDPOINTS PROTOCOLO MCP JSON-RPC 2.0
# ====================================================================

@mt5_mcp_router.post("")
@mt5_mcp_router.post("/")
async def handle_mcp_request(req: MCPRequest):
    """Punto de entrada estándar JSON-RPC 2.0 para Clientes MCP"""
    method = req.method
    params = req.params or {}
    req_id = req.id

    if method == "initialize":
        return MCPResponse(
            id=req_id,
            result={
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {"listChanged": False}},
                "serverInfo": {
                    "name": "mia-server-mcp-mt5",
                    "version": "1.0.0",
                    "broker_server": MT5_SERVER,
                    "account_login": MT5_LOGIN
                }
            }
        )

    elif method in ["tools/list", "tools_list"]:
        return MCPResponse(
            id=req_id,
            result={"tools": MCP_TOOLS_REGISTRY}
        )

    elif method in ["tools/call", "tools_call"]:
        tool_name = params.get("name")
        args = params.get("arguments", {})
        try:
            output = execute_mt5_tool(tool_name, args)
            return MCPResponse(
                id=req_id,
                result={
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(output, indent=2, ensure_ascii=False)
                        }
                    ],
                    "isError": False
                }
            )
        except Exception as e:
            return MCPResponse(
                id=req_id,
                error={"code": -32603, "message": str(e)}
            )

    else:
        return MCPResponse(
            id=req_id,
            error={"code": -32601, "message": f"Método MCP no soportado: '{method}'"}
        )


# ====================================================================
# ENDPOINTS REST DIRECTOS (/api/mcp/mt5/...)
# ====================================================================

@api_mt5_router.get("/tools")
async def list_tools_rest():
    """Lista las herramientas disponibles en el Servidor MCP MT5"""
    return {
        "status": "success",
        "total_tools": len(MCP_TOOLS_REGISTRY),
        "tools": MCP_TOOLS_REGISTRY
    }

@api_mt5_router.post("/execute/{tool_name}")
async def execute_tool_rest(tool_name: str, payload: Dict[str, Any] = None):
    """Ejecuta directamente una herramienta del Servidor MCP MT5 vía REST"""
    try:
        args = payload or {}
        res = execute_mt5_tool(tool_name, args)
        return {"status": "success", "tool": tool_name, "result": res}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@api_mt5_router.get("/telemetry")
async def get_mt5_telemetry_quick():
    """Retorna un snapshot rápido de telemetría de cuenta y posiciones abiertas"""
    acc = tool_account_summary()
    pos = tool_get_open_positions()
    return {
        "status": "success",
        "account": acc,
        "open_positions_count": len(pos),
        "positions": pos,
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
    }


# ====================================================================
# RUTAS DE SALUD Y MONTAJE FASTAPI
# ====================================================================

@app.get("/health")
def health():
    connected = ensure_mt5_connected()
    return {
        "service": "mia-server-mcp-mt5",
        "status": "ONLINE" if connected else "DISCONNECTED",
        "broker_server": MT5_SERVER,
        "account_login": MT5_LOGIN,
        "fastapi_url": FASTAPI_URL,
        "env_configured": {
            "mt5_login": bool(MT5_LOGIN),
            "mt5_password": bool(MT5_PASSWORD),
            "mt5_server": bool(MT5_SERVER),
            "fastapi_url": bool(FASTAPI_URL)
        },
        "tools_count": len(MCP_TOOLS_REGISTRY),
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
    }

app.include_router(mt5_mcp_router)
app.include_router(api_mt5_router)

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8085))
    print(f"🚀 Iniciando Mia MT5 MCP Server en puerto {port}...")
    uvicorn.run("mia_server_mcp_mt5:app", host="0.0.0.0", port=port, reload=False)
