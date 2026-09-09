import asyncio
import json
import httpx
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import uvicorn
import os

RAILWAY_URL = "https://trading-production-927a.up.railway.app/api/dashboard_data"

app = FastAPI(title="Mia Swarm WebSocket Server")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Montar Interfaz de React (Groktopus 3D) ---
build_dir = os.path.join(os.path.dirname(__file__), "mia_3d_ui", "build")
if os.path.exists(build_dir):
    app.mount("/static", StaticFiles(directory=os.path.join(build_dir, "static")), name="static")
    
    @app.get("/")
    async def serve_react_app():
        return FileResponse(os.path.join(build_dir, "index.html"))
    
    # Manejar rutas de React Router o recursos estáticos en la raíz
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
