#!/bin/bash
# start_groktopus.sh
# ----------------------------------------------------
# 1. Iniciar el Enjambre (REST Puro) en segundo plano
echo "Iniciando Swarm REST en Background..."
python mia_master_swarm_rest.py &

# 2. Iniciar el Servidor Web / WebSockets en primer plano
if [ -z "$PORT" ]; then
  export PORT=8080
fi
echo "Iniciando Servidor WebSocket y UI en el puerto $PORT..."
uvicorn mia_websocket_server:app --host 0.0.0.0 --port $PORT
