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

    @app.get("/{file_path:path}")
    async def serve_static_files(file_path: str):
        full_path = os.path.join(build_dir, file_path)
        if os.path.exists(full_path) and os.path.isfile(full_path):
            return FileResponse(full_path)
        return FileResponse(os.path.join(build_dir, "index.html"))

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
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                print(f"Error sending message: {e}")

manager = ConnectionManager()

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

@app.get("/api/cache")
async def get_railway_cache():
    """
    Proxy hacia Railway cache RAM.
    El browser llama a localhost:8000/api/cache (sin CORS issues)
    y este endpoint hace el fetch server-side a Railway.
    """
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(
                RAILWAY_URL,
                headers={"User-Agent": "MiaSwarmBot/1.0"}
            )
            response.raise_for_status()
            return response.json()
    except Exception as e:
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
