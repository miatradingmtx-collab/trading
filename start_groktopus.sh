#!/bin/bash
# start_groktopus.sh
# ----------------------------------------------------
# 1. Iniciar el Enjambre (REST Puro) en segundo plano
echo "Iniciando Swarm REST en Background..."
python mia_master_swarm_rest.py &

# 2. Iniciar el Servidor Web / WebSockets en primer plano
# Default to 8080 if PORT is not set
if [ -z "" ]; then
  PORT=8080
fi
echo "Iniciando Servidor WebSocket y UI en el puerto ..."
uvicorn app:app --host 0.0.0.0 --port 
