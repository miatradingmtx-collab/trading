#!/bin/bash
# start_groktopus.sh
# ----------------------------------------------------
# 1. Iniciar el Enjambre (CrewAI) en segundo plano
echo "Iniciando Groktopus Swarm en Background..."
python mia_master_swarm.py &

# 2. Iniciar el Servidor Web / WebSockets en primer plano
# Railway inyecta la variable $PORT automáticamente (suele ser 8080 u 8000)
PORT=${PORT:-8000}
echo "Iniciando Servidor WebSocket y UI en el puerto $PORT..."
uvicorn mia_websocket_server:app --host 0.0.0.0 --port $PORT
