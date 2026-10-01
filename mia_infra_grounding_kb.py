"""
MIA INFRASTRUCTURE GROUNDING KNOWLEDGE BASE (KB ENGINE)
======================================================
Compendio vivo de la arquitectura de infraestructura, topología cloud,
bases de datos, historial de commits y directrices de Antigravity.

Propósito:
Transferir todo el conocimiento del proyecto a los modelos LLM (Llama 3.3 70B en OpenRouter)
y a los 10 Herds de Operaciones para que evalúen, diagnostiquen y propongan soluciones
conociendo el 100% de la infraestructura real sin alucinar tecnologías ajenas.
"""

import os
import json
import datetime
import requests
from typing import Dict, Any, List

UPSTASH_URL = os.getenv("UPSTASH_REDIS_REST_URL", "https://certain-gnat-160816.upstash.io")
UPSTASH_TOKEN = os.getenv("UPSTASH_REDIS_REST_TOKEN", "gQAAAAAAAnQwAAIgcDI2YTA5YjRlZDU2MDM0OWU5ODhlZjBlYTk4ODYyZDg0OA")
UPSTASH_HEADERS = {
    "Authorization": f"Bearer {UPSTASH_TOKEN}",
    "Content-Type": "application/json"
}

class MiaInfraGroundingKB:
    SLOT_KEY = "cache_mia_architecture_grounding"

    @classmethod
    def get_canonical_architecture_spec(cls) -> Dict[str, Any]:
        """
        Retorna la radiografía completa y canónica de la infraestructura de trading y ops.
        """
        return {
            "proyecto": "MIA Trading AI & Back-Office Infrastructure",
            "repositorio_github": "https://github.com/miatradingmtx-collab/trading.git",
            "rama_oficial": "main",
            "stack_tecnologico_oficial": {
                "lenguaje_backend": "Python 3.12 (FastAPI, WebSockets nativos, Asyncio, Pydantic v2)",
                "ia_trading_cerebro": "TensorFlow 2.15 Deep Learning (Capas 7-10-8-2, ReLU/Sigmoid) + 7 Trading Herds",
                "ia_deliberacion_llm": "OpenRouter REST puro (Llama 3.3 70B, DeepSeek V3, Llama 3.1 70B) - Single-Cycle Turn",
                "frameworks_prohibidos": ["CrewAI", "LangChain"],
                "base_de_datos_viva_hot": "Upstash Redis (Serverless REST API Anti-429, latencia sub-35ms MGET)",
                "base_de_datos_fria_judge": "Google Cloud Firebase Firestore (Plan Spark, persistencia inmutable pasiva)",
                "infraestructura_cloud": "Railway Cloud PaaS (Dual Deploy: 1fd4 y 927a)",
                "broker_gateway": "MetaTrader 5 via MetaAPI Cloud (EET UTC Broker Time)",
                "chatops_interactivo": "Slack Workspace (Canal exclusivo Ops: #back-office-y-backend, Bot: Mia Watchdog)",
                "ui_frontend": "Google Stitch UI + Plotly Dark Theme (#0d1117, #161b22, acentos cian/verde)"
            },
            "radiografia_microservicios_railway": {
                "instancia_1fd4": {
                    "url": "https://trading-production-1fd4.up.railway.app",
                    "rol": "Plano de Datos & Swarm HFT (MIA_MARKET_TRADING_SWARM)",
                    "endpoints_clave": [
                        "/ws (WebSockets en vivo)",
                        "/brain (Red Neuronal Canvas 2D interactiva)",
                        "/ (Antopus 3D Three.js Swarm Orbit)",
                        "/mcp (Servidor MCP Trading JSON-RPC)",
                        "/api/cache_mget (Proxy agregador atómico)"
                    ]
                },
                "instancia_927a": {
                    "url": "https://trading-production-927a.up.railway.app",
                    "rol": "Backend de Ejecución MT5 (Data Plane de Mercado)",
                    "endpoints_clave": [
                        "/api/trade_alert (Webhook ejecutor de MetaTrader 5)",
                        "/dashboard (Dashboard Institucional de KPIs y Trades MT5)",
                        "/api/dashboard_data (Bypass total servido desde Upstash)",
                        "/diagrama (Mapa interactivo de conectividad SVG/HTML)"
                    ]
                },
                "instancia_0b51_ops": {
                    "url": "https://trading-production-0b51.up.railway.app",
                    "rol": "Plano de Control SRE, 10 Terminators, Servidor MCP Ops & ChatOps Slack (Desacoplado)",
                    "estado": "ONLINE_Y_DESACOPLADO_ACTIVO",
                    "endpoints_clave": [
                        "/health (Healthcheck de microservicio y 10 Terminators)",
                        "/api/ops/status (Auditoría continua SRE y evaluación Llama 3.3)",
                        "/mcp/ops (Servidor MCP Ops JSON-RPC)",
                        "/api/slack/events (Receptor de eventos Slack #back-office-y-backend)",
                        "/api/slack/interactions (Botones interactivos y triage Block Kit)",
                        "/api/slack/command (/mia comando interactivo)",
                        "/api/ops/vectorize (Vectorización 20D de Terminator T1)",
                        "/api/antigravity/mirror/push (Receptor de Antigravity Live Mirror)"
                    ]
                },
                "microservicio_ops_status": {
                    "nombre": "mia-ops-service",
                    "estado": "DESPLEGADO_Y_OPERATIVO_EN_PRODUCCION",
                    "url_oficial": "https://trading-production-0b51.up.railway.app",
                    "resultado": "Slack API, MCP Ops y Herds T1-T10 desacoplados al 100% de 927a, 0% de jitter en MT5."
                }
            },
            "radiografia_completa_bases_de_datos": {
                "upstash_redis_slots_canonicos": [
                    {"slot": "cache_mt5", "tipo": "JSON", "proposito": "Órdenes vivas reales del broker, balance, equity, flotante y márgenes"},
                    {"slot": "cache_hist_mt5", "tipo": "JSON", "proposito": "Historial de los últimos 50 trades reales cerrados de MT5 (Anti-429)"},
                    {"slot": "cache_mia_tensorflow", "tipo": "JSON Base64", "proposito": "Pesos compilados de la Red Neuronal, Accuracy (97.87%) y tensores"},
                    {"slot": "cache_trading_matrix", "tipo": "JSON", "proposito": "Matriz cuantitativa de confluencias y ranking de activos"},
                    {"slot": "cache_researcher_insights", "tipo": "JSON", "proposito": "Análisis macroeconómico y sentimiento de mercado"},
                    {"slot": "cache_regla_de_3", "tipo": "JSON", "proposito": "Top 1, 2 y 3 dinámico de confirmaciones institucionales y filtro de noticias"},
                    {"slot": "cache_shadow_trades", "tipo": "JSON", "proposito": "Tickets virtuales simulados (#SHADOW_XXXXXX) durante modo calibración"},
                    {"slot": "cache_mia_atlas", "tipo": "JSON", "proposito": "Análisis contrafactual A/B Champion (Herds) vs Challenger (ATLAS DOM/CVD)"},
                    {"slot": "cache_system_ops_status", "tipo": "JSON", "proposito": "Estado de salud consolidado de los 10 Herds de Operaciones"},
                    {"slot": "cache_ops_learning_kb", "tipo": "JSON", "proposito": "Memoria CBR de errores, parches y decisiones aprobadas por el Padre"},
                    {"slot": "cache_pending_ops_approvals", "tipo": "JSON", "proposito": "Cola de propuestas técnicas pendientes de clic humano en Slack"}
                ],
                "firebase_firestore_colecciones": [
                    {"coleccion": "mia_kb", "documentos_clave": ["regla_de_3", "indicadores_impacto/detalle"], "regla": "Lectura directa prohibida en HFT"},
                    {"coleccion": "mia_audit_logs", "proposito": "Histórico perpetuo inmutable de auditoría de trades"},
                    {"coleccion": "mia_swarm_rest_history", "proposito": "Archivo inmutable de los debates de los Herds de trading"},
                    {"coleccion": "mia_atlas", "proposito": "Auditorías de microestructura CVD Delta y snapshots diarios obligatorios (23:59)"},
                    {"coleccion": "system_memory", "proposito": "Persistencia espejo de los estados de Upstash"},
                    {"coleccion": "mia_ops_audit_history", "proposito": "Trazabilidad perpetua de las auditorías de Herds T1-T10"},
                    {"coleccion": "mia_ops_learning_history", "proposito": "Histórico granular de casos CBR aprobados/rechazados"}
                ]
            },
            "banco_errores_historicos_y_soluciones": [
                {
                    "error": "HTTP 429 Quota Exceeded en Firebase Spark",
                    "causa": "MT5 escaneaba cada 30s e invocaba doc_ref.set() 1440 veces/día; barridos stream() de 800 logs",
                    "solucion_aplicada": "RAM Cache Shield + Upstash Redis. Lecturas de Firestore reducidas a cero en tiempo real; límite reducido de 800 a 150."
                },
                {
                    "error": "Órdenes Fantasma y Discrepancias MT5 vs Dashboard",
                    "causa": "Posición de XAUUSD liquidada en el broker quedaba flotando en operaciones_activas; campos pnl recibían null/NaN",
                    "solucion_aplicada": "Depuración estricta en caliente por HERD T1 (DBA), coalescencia con (val or 0.0) y redondeo matemático round(x, 2)."
                },
                {
                    "error": "Regla de 3 Congelada en Fecha Pasada",
                    "causa": "La función entrenar_pesos_dinamicos intentaba leer 500 docs directos de Firestore fallando silenciosamente",
                    "solucion_aplicada": "HERD T4 recalibra leyendo de memoria Upstash y actualiza timestamp 'ultima_actualizacion' al segundo actual."
                },
                {
                    "error": "Degeneración de Bucles LLM y Caídas de CrewAI/LangChain",
                    "causa": "Frameworks legados reintentaban infinitamente, saturaban TPM y generaban listas repetitivas hasta la línea 77",
                    "solucion_aplicada": "Purga absoluta de CrewAI/LangChain; adopción de OpenRouter REST nativo con Kill Switch de 8s, max_tokens: 250 y repetition_penalty: 1.15."
                },
                {
                    "error": "Corrupción de Código y Documentación por Bytes NUL (\\x00)",
                    "causa": "Sobreescrituras concurrentes o herramientas no seguras inyectaron 1,830 caracteres NUL",
                    "solucion_aplicada": "Auditoría sintáctica estricta con AST (ast.parse) y encoding utf-8-sig por HERD T2."
                },
                {
                    "error": "Desconexiones en Red Móvil Android / Termux CLI",
                    "causa": "NAT carrier cortaba sockets inactivos lanzando NameError: asyncio",
                    "solucion_aplicada": "Heartbeat keepalive de 25s en el servidor WebSocket y cliente CLI con fallback HTTP REST."
                },
                {
                    "error": "Cruce de Identidad y Ruido en Slack (#mia-chat vs #back-office-y-backend)",
                    "causa": "MIA Watchdog respondía a mensajes generales de chat en #mia-chat consumiendo tokens de Gemini",
                    "solucion_aplicada": "Silenciamiento 100% de #mia-chat en Watchdog. #back-office-y-backend opera exclusivamente con OpenRouter Llama 3.3 70B y Herds T1-T10."
                }
            ],
            "protocolo_fase_1_human_in_the_loop": {
                "regla_mandatoria": "CERO mutaciones destructivas en producción sin aprobación humana explícita.",
                "mecanismo_slack": "Checkboxes seleccionables individuales + Botones [Aprobar Seleccionadas], [Aprobar Todas], [Rechazar], [Forzar Resync].",
                "comparativa_obligatoria": "Bloque ANTES vs DESPUÉS para cada propuesta técnica.",
                "modo_confianza": "Cada aprobación suma +1 punto; cada rechazo resta -2 puntos. Umbral de autonomía futura: >= 95% de confianza acumulada."
            }
        }

    @classmethod
    def get_grounding_prompt_for_llama(cls) -> str:
        """
        Genera el bloque de contexto inyectable en OpenRouter para que Llama 3.3 70B
        conozca exactamente la arquitectura de MIA y emita juicios certeros.
        """
        spec = cls.get_canonical_architecture_spec()
        return f"""
=== GROUNDING DE ARQUITECTURA TÉCNICA REAL DE MIA CORE (BASE DE CONOCIMIENTO INMUTABLE) ===
Eres el Auditor Cognitivo del Watchdog Supervisor de MIA Trading & Ops.
TIENES ACCESO A LA RADIOGRAFÍA TOTAL DEL SISTEMA:
1. Repositorio Oficial: {spec['repositorio_github']} (Rama: {spec['rama_oficial']}).
2. Backend y Lenguaje: {spec['stack_tecnologico_oficial']['lenguaje_backend']}.
3. Lógica de Bases de Datos:
   - Upstash Redis REST ({spec['stack_tecnologico_oficial']['base_de_datos_viva_hot']}): Es la fuente viva de la verdad (slots atómicos: cache_mt5, cache_hist_mt5, cache_mia_tensorflow, cache_regla_de_3, etc.).
   - Firebase Firestore ({spec['stack_tecnologico_oficial']['base_de_datos_fria_judge']}): Persistencia pasiva. PROHIBIDO sugerir barridos masivos stream() (Riesgo 429 Spark).
4. Infraestructura Cloud Railway:
   - Instancia 1fd4 ({spec['radiografia_microservicios_railway']['instancia_1fd4']['url']}): Trading Herds, WebSockets (/ws), Red Neuronal (/brain), MCP (/mcp, /mcp/ops).
   - Instancia 927a ({spec['radiografia_microservicios_railway']['instancia_927a']['url']}): MT5 Webhooks, Dashboard Plotly (/dashboard), Slack Webhooks (/api/slack/*).
   - Próximo microservicio: 'mia-ops-service' para aislar Slack y Ops de MT5.
5. Frontend & UI: Google Stitch UI + Plotly Dark Theme. Queda prohibido rediseñar eliminando métricas o menús existentes.
6. Protocolo Human-In-The-Loop: Ningún cambio en producción es automático. Todo se propone con Antes vs Después y checkboxes para autorización del Padre.
7. Historial de Errores: Conoces perfectamente los errores pasados (429 Quota Exceeded, órdenes fantasma XAUUSD, regla de 3 estancada, CrewAI deprecado, bytes NUL).

DIRECTRIZ DE JUICIO:
- Evalúa cada propuesta técnica de los Herds T1 al T10.
- Si una propuesta propone herramientas o arquitecturas ajenas (ej. proponer GitLab en vez de GitHub, o proponer bases sin considerar el escudo de Upstash), DESCÁRTALA o penalízala.
- Asigna un SCORE de 0 a 100 y justifica detalladamente tu dictamen.
"""

    @classmethod
    def sync_grounding_to_upstash(cls) -> bool:
        """Sincroniza la radiografía a Upstash Redis para consulta ultra-rápida."""
        spec = cls.get_canonical_architecture_spec()
        try:
            r = requests.post(f"{UPSTASH_URL}/set/{cls.SLOT_KEY}", headers=UPSTASH_HEADERS, json=spec, timeout=4)
            return r.status_code == 200
        except Exception:
            return False

if __name__ == "__main__":
    ok = MiaInfraGroundingKB.sync_grounding_to_upstash()
    print(f"Grounding KB sincronizada en Upstash: {ok}")
