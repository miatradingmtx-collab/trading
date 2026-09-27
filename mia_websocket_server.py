import asyncio
import json
import httpx
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import uvicorn
import os
import datetime

RAILWAY_URL = "https://trading-production-927a.up.railway.app/api/dashboard_data"

app = FastAPI(title="Mia Swarm WebSocket Server")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Montar Interfaz de React (Antopus 3D) ---
build_dir = os.path.join(os.path.dirname(__file__), "mia_3d_ui", "build")
if os.path.exists(build_dir):
    app.mount("/static", StaticFiles(directory=os.path.join(build_dir, "static")), name="static")
    
    @app.get("/")
    async def serve_react_app():
        return FileResponse(os.path.join(build_dir, "index.html"))
    
    # Manejar rutas de React Router o recursos estáticos en la raíz
    @app.get("/brain")
    async def render_brain():
        try:
            return FileResponse(os.path.join(os.path.dirname(__file__), "tensorflow_vision.html"))
        except Exception as e:
            return {"error": str(e)}

    @app.get("/dashboard")
    async def render_dashboard():
        try:
            # En 1fd4, /dashboard sirve el Dashboard de Enjambres (React 3D Multi-Agent Swarm)
            if os.path.exists(build_dir):
                return FileResponse(os.path.join(build_dir, "index.html"))
            return FileResponse(os.path.join(os.path.dirname(__file__), "dashboard_mia.html"))
        except Exception as e:
            return {"error": str(e)}

    @app.get("/diagramas/malla-shadow")
    async def render_diagram_malla_shadow():
        try:
            return FileResponse(os.path.join(os.path.dirname(__file__), "diagrama_malla_shadow_bifurcacion.html"))
        except Exception as e:
            return {"error": str(e)}

    @app.get("/diagramas/atlas-mcp")
    async def render_diagram_atlas_mcp():
        try:
            return FileResponse(os.path.join(os.path.dirname(__file__), "diagrama_atlas_mcp_externo.html"))
        except Exception as e:
            return {"error": str(e)}

    # Las rutas de API y WebSocket se registran primero; el catch-all estático al final

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        disconnected = []
        for connection in list(self.active_connections):
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.append(connection)
        for d in disconnected:
            if d in self.active_connections:
                self.active_connections.remove(d)

manager = ConnectionManager()

@app.on_event("startup")
async def start_heartbeat():
    async def heartbeat_loop():
        while True:
            await asyncio.sleep(25)
            await manager.broadcast({"type": "HEARTBEAT"})
    asyncio.create_task(heartbeat_loop())

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        now_utc = datetime.datetime.now(datetime.timezone.utc)
        is_weekend = False
        if now_utc.weekday() == 4 and now_utc.hour >= 21:
            is_weekend = True
        elif now_utc.weekday() == 5:
            is_weekend = True
        elif now_utc.weekday() == 6 and now_utc.hour < 21:
            is_weekend = True
            
        if is_weekend:
            days_ahead = 6 - now_utc.weekday()
            target_date = now_utc + datetime.timedelta(days=days_ahead)
            target_time = target_date.replace(hour=21, minute=0, second=0, microsecond=0)
            horas = round(max(0, (target_time - now_utc).total_seconds()) / 3600, 1)
            init_msg = f"MERCADO CERRADO (Fin de semana). Criosueño activo ({horas}h restantes para apertura dom 21:00 UTC). Consumo de tokens: 0."
            action_status = "STANDBY"
        else:
            init_msg = "MERCADO EN VIVO. Enjambre HFT activo en OpenRouter (Llama 3.3 70B REST & TensorFlow 97.87%)."
            action_status = "LIVE"

        await websocket.send_json({
            "agent": "Master",
            "action": action_status,
            "data": init_msg
        })
        while True:
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.post("/emit")
async def emit_event(event: dict):
    """
    Endpoint para que mia_master_swarm.py empuje eventos al WebSocket vía HTTP POST.
    """
    await manager.broadcast(event)
    return {"status": "ok"}

@app.get("/api/dashboard_data")
async def get_dashboard_data_proxy():
    """Proxy hacia el endpoint institucional de dashboard en 927a (Anti-429)."""
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(RAILWAY_URL, headers={"User-Agent": "MiaSwarmBot/1.0"})
            response.raise_for_status()
            return response.json()
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/api/cache_mget")
async def get_cache_mget_proxy():
    """Proxy hacia el slot consolidado cache_mget en 927a."""
    try:
        url = "https://trading-production-927a.up.railway.app/api/cache_mget"
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(url, headers={"User-Agent": "MiaSwarmBot/1.0"})
            response.raise_for_status()
            return response.json()
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/api/chart_data/{symbol}")
async def get_chart_data_proxy(symbol: str, timeframe: str = "1h"):
    """Proxy hacia chart_data en 927a para velas Yahoo Finance sin CORS."""
    try:
        url = f"https://trading-production-927a.up.railway.app/api/chart_data/{symbol}?timeframe={timeframe}"
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(url, headers={"User-Agent": "MiaSwarmBot/1.0"})
            response.raise_for_status()
            return response.json()
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/api/export_audit_csv")
async def get_export_csv_proxy():
    """Proxy hacia export_audit_csv en 927a."""
    try:
        url = "https://trading-production-927a.up.railway.app/api/export_audit_csv"
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(url, headers={"User-Agent": "MiaSwarmBot/1.0"})
            response.raise_for_status()
            return response.text
    except Exception as e:
        return {"status": "error", "message": str(e)}

# --- Montar Servidor MCP y Agente Investigador ATLAS ---
try:
    from mia_mcp_server import mcp_router, api_mcp_router
    app.include_router(mcp_router)
    app.include_router(api_mcp_router)
    
    from mia_researcher_agent import atlas_researcher
    
    @app.post("/api/researcher/investigate")
    async def api_trigger_investigation(payload: dict = None):
        """Dispara un ciclo de investigación cuantitativa on-demand de ATLAS"""
        try:
            args = payload or {}
            sym = args.get("symbol", "EURUSD")
            px = float(args.get("current_price", 1.0850))
            poc = float(args.get("poc_price", 1.0842))
            res = atlas_researcher.investigate_symbol_microstructure(sym, px, poc)
            return {"status": "success", "result": res}
        except Exception as e:
            return {"status": "error", "message": str(e)}
            
    @app.get("/api/researcher/brief")
    async def api_get_researcher_brief():
        """Obtiene el último brief de inteligencia de ATLAS directamente desde Upstash Redis"""
        try:
            import requests, json
            up_headers = {"Authorization": "Bearer gQAAAAAAAnQwAAIgcDI2YTA5YjRlZDU2MDM0OWU5ODhlZjBlYTk4ODYyZDg0OA"}
            r = requests.get("https://certain-gnat-160816.upstash.io/get/cache_researcher_insights", headers=up_headers, timeout=4)
            if r.status_code == 200:
                raw = r.json().get("result")
                data = json.loads(raw) if raw and isinstance(raw, str) else (raw or {})
                return {"status": "success", "data": data}
            return {"status": "empty", "data": None}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    @app.get("/api/atlas/backtest_data")
    async def api_get_atlas_backtest_data():
        """Obtiene la matriz comparativa A/B (Champion vs Challenger) directamente desde Upstash Redis"""
        try:
            import requests, json
            up_headers = {"Authorization": "Bearer gQAAAAAAAnQwAAIgcDI2YTA5YjRlZDU2MDM0OWU5ODhlZjBlYTk4ODYyZDg0OA"}
            r = requests.get("https://certain-gnat-160816.upstash.io/get/cache_mia_atlas", headers=up_headers, timeout=4)
            if r.status_code == 200:
                raw = r.json().get("result")
                data = json.loads(raw) if raw and isinstance(raw, str) else (raw or {})
                return {"status": "success", "data": data, "source": "upstash_cache_mia_atlas"}
            return {"status": "empty", "data": None}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    @app.get("/api/shadow/trades")
    async def api_get_shadow_trades():
        """Obtiene el historial de trades reales correlacionados con tickets virtuales #SHADOW_XXXXXX desde Upstash"""
        try:
            import requests, json
            up_headers = {"Authorization": "Bearer gQAAAAAAAnQwAAIgcDI2YTA5YjRlZDU2MDM0OWU5ODhlZjBlYTk4ODYyZDg0OA"}
            r = requests.get("https://certain-gnat-160816.upstash.io/get/cache_shadow_trades", headers=up_headers, timeout=4)
            if r.status_code == 200:
                raw = r.json().get("result")
                data = json.loads(raw) if raw and isinstance(raw, str) else (raw or {})
                return {"status": "success", "data": data, "source": "upstash_cache_shadow_trades"}
            return {"status": "empty", "data": None}
        except Exception as e:
            return {"status": "error", "message": str(e)}
except Exception as e_mcp:
    print(f"Error montando MCP en websocket server: {e_mcp}")


# Catch-all estático para React (SPA fallback)
if os.path.exists(build_dir):
    @app.get("/{file_path:path}")
    async def serve_static_files(file_path: str):
        full_path = os.path.join(build_dir, file_path)
        if os.path.exists(full_path) and os.path.isfile(full_path):
            return FileResponse(full_path)
        return FileResponse(os.path.join(build_dir, "index.html"))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
