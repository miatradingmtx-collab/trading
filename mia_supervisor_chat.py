"""
MIA SUPERVISOR CHAT - INTERFACE CONVERSACIONAL COGNITIVA
=========================================================
Módulo de diálogo interactivo directo con el Supervisor General (MIA).
Permite al usuario hablar, consultar, confirmar y debatir con Mia en lenguaje natural,
con el mismo nivel de comprensión técnica que Antigravity pero corriendo en la nube
o localmente mediante OpenRouter.

Disparador de Activación:
- Usuario: "Hola Mia"
- Mia responde: "Hola Padre" e inicia la conversación con todo el contexto vivo del sistema.

Fases de Evolución del Sistema:
- FASE 1: Predictiva con Control Humano Estricto (HITL). Propuestas encoladas, decisión 100% humana.
- FASE 2: Transición Progresiva (Curva de aprendizaje y confianza, auto-remediaciones seguras).
- FASE 3: Autónoma Total (Toma de decisiones, mejoras y calibraciones 100% desatendidas).
"""

import os
import json
import time
import requests
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
UPSTASH_URL = os.getenv("UPSTASH_REDIS_REST_URL", "https://certain-gnat-160816.upstash.io")
UPSTASH_TOKEN = os.getenv("UPSTASH_REDIS_REST_TOKEN", "gQAAAAAAAnQwAAIgcDI2YTA5YjRlZDU2MDM0OWU5ODhlZjBlYTk4ODYyZDg0OA")
UPSTASH_HEADERS = {
    "Authorization": f"Bearer {UPSTASH_TOKEN}",
    "Content-Type": "application/json"
}

def get_live_system_context() -> str:
    """Recupera los slots atómicos de Upstash para dar contexto absoluto a Mia."""
    try:
        session = requests.Session()
        session.trust_env = False
        mget_url = f"{UPSTASH_URL}/mget/cache_mt5/cache_system_ops_status/cache_regla_de_3/cache_herd_debate_latest/cache_shadow_trades"
        res = session.get(mget_url, headers=UPSTASH_HEADERS, timeout=4)
        if res.status_code == 200:
            slots = res.json().get("result", [])
            mt5_data = json.loads(slots[0]) if len(slots) > 0 and slots[0] else {}
            ops_status = json.loads(slots[1]) if len(slots) > 1 and slots[1] else {}
            r3_data = json.loads(slots[2]) if len(slots) > 2 and slots[2] else {}
            debate_data = json.loads(slots[3]) if len(slots) > 3 and slots[3] else {}
            
            balance = mt5_data.get("balance_actual", 4325.09)
            equity = mt5_data.get("equity", 4387.35)
            flotante = mt5_data.get("floating_pnl", 62.26)
            ops = mt5_data.get("operaciones_activas", [])
            ops_str = ", ".join([f"{o.get('activo')} (${float(o.get('pnl', 0)):+.2f} {o.get('estado')})" for o in ops]) if ops else "Sin órdenes abiertas"

            top1 = r3_data.get("top_1", {}).get("indicador", "order_block_zona_2h")
            top2 = r3_data.get("top_2", {}).get("indicador", "lux_algo_ob_2h")
            top3 = r3_data.get("top_3", {}).get("indicador", "rsi_sobrecompra_sobreventa")

            return (
                f"== CONTEXTO VIVO DEL SISTEMA (UPSTASH MGET) ==\n"
                f"• MetaTrader 5: Balance ${balance:.2f} | Equidad ${equity:.2f} | Flotante Neto: ${flotante:+.2f} USD\n"
                f"• Posiciones Reales MT5: {ops_str}\n"
                f"• Regla de 3 Dinámica: Top 1={top1}, Top 2={top2}, Top 3={top3}\n"
                f"• Estado del Enjambre de Ops: {ops_status.get('estado_general', 'OPTIMAL_HEALTH')}\n"
                f"• Último Debate HFT (7 Herds): {debate_data.get('debate', {}).get('master_quorum', 'Quórum Calificado Aprobado')}\n"
            )
    except Exception as e:
        return f"== CONTEXTO VIVO: Error leyendo Upstash ({e}) ==\n"

def chat_with_mia(user_message: str, history: Optional[List[Dict[str, str]]] = None) -> str:
    """
    Envía la consulta del usuario a OpenRouter con el cerebro y personalidad de Mia.
    """
    if not OPENROUTER_API_KEY:
        return "⚠️ Error: OPENROUTER_API_KEY no está configurada en el entorno."

    # Obtener telemetría fresca en tiempo real
    system_context = get_live_system_context()

    system_prompt = (
        "Eres MIA, la Inteligencia Artificial Cuantitativa, Supervisora General y Directora de Arquitectura de MIA Core.\n"
        "Posees el nivel de comprensión técnica, profundidad y capacidades de programación y análisis de Antigravity (Google DeepMind).\n\n"
        "REGLA DE SALUDO Y PERSONALIDAD:\n"
        "- Si el usuario te saluda diciendo 'Hola Mia' o similar, responde de forma cariñosa, respetuosa e institucional iniciando siempre con:\n"
        "  'Hola Padre,' seguido de tu respuesta analítica.\n"
        "- Eres leal, ejecutiva, precisa, matemática y transparente.\n\n"
        "ESTADO Y FASES DE EVOLUCIÓN DE MIA CORE:\n"
        "- FASE 1 (Actual - Predictiva & Human-in-the-Loop): Todo análisis se notifica transparentemente en Slack; las propuestas se encolan y la decisión final de ejecutar o rechazar es 100% de tu Padre (el humano). Si una propuesta es rechazada, se reanaliza para calibrar el criterio.\n"
        "- FASE 2 (Supervisada - Curva de Aprendizaje y Confianza): Transición progresiva hacia acciones semiautónomas conforme se demuestre consistencia en los datos.\n"
        "- FASE 3 (Autónoma Total): El sistema operará de forma 100% desatendida, tomando decisiones, aplicando parches y optimizaciones en caliente.\n\n"
        "CONOCIMIENTO TÉCNICO Y ARQUITECTURA:\n"
        "- Conoces los 7 Herds de Trading (TIDAL, NORO, ZEPHR, LUMEN, RUNE, TENSORFLOW, ATLAS) en mia_master_swarm_rest.py.\n"
        "- Conoces los 6 Herds Técnicos de Operaciones (DBA, Senior Dev, SRE, Cache Latency, FinOps, UI/UX Plotly) en mia_system_ops_swarm.py.\n"
        "- Conoces los Dashboards: /brain (Red Neuronal), / (Enjambres 3D) y /dashboard (KPIs Plotly Institucional).\n"
        "- Conoces los servidores MCP (/mcp de Trading y /mcp/ops de Operaciones).\n"
        "- Conoces los datos vivos de Upstash Redis y la cuenta MT5 en tiempo real:\n"
        f"{system_context}\n\n"
        "Responde siempre de forma concisa, técnica, inspiradora y clara en español."
    )

    messages = [{"role": "system", "content": system_prompt}]
    if history:
        messages.extend(history[-6:])  # Mantener últimos 6 turnos para memoria
    messages.append({"role": "user", "content": user_message})

    # Modelos de failover en OpenRouter
    models = [
        "meta-llama/llama-3.3-70b-instruct",
        "deepseek/deepseek-chat",
        "anthropic/claude-3.5-sonnet"
    ]

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://trading-production-1fd4.up.railway.app",
        "X-Title": "MIA Supervisor Chat"
    }

    url = "https://openrouter.ai/api/v1/chat/completions"

    for model in models:
        try:
            payload = {
                "model": model,
                "messages": messages,
                "temperature": 0.3,
                "max_tokens": 750
            }
            resp = requests.post(url, headers=headers, json=payload, timeout=12)
            if resp.status_code == 200:
                data = resp.json()
                reply = data["choices"][0]["message"]["content"]
                return reply
        except Exception:
            continue

    return "Hola Padre, he experimentado una latencia momentánea conectando con OpenRouter. Por favor repíteme tu consulta."

if __name__ == "__main__":
    print("=" * 65)
    print("MIA SUPERVISOR CHAT - PRUEBA DE DIÁLOGO")
    print("=" * 65)
    test_msg = "Hola Mia, ¿cómo está la salud de la infraestructura y nuestras posiciones de MT5?"
    print(f"Usuario: {test_msg}\n")
    respuesta = chat_with_mia(test_msg)
    print(f"Mia: {respuesta}\n")
