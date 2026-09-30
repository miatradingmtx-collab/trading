"""
MIA PERSONAL MCP SERVER - Model Context Protocol para Mia Chat & Vida Personal
=============================================================================
Servidor MCP exclusivo para Mia Chat (Google Gemini Pro), completamente aislado
del servidor MCP de Operaciones y Trading (mia_ops_mcp_server.py).

Dominio:
- Gestión personal de Anto (su Creador/Padre).
- Base de Conocimiento Personal Progresiva (anto_personal_kb): gustos, hábitos, rutinas.
- Tareas pendientes, ideas y anotaciones rápidas.
- Alarmas, recordatorios y eventos de agenda.
- Clima en tiempo real y conectores inteligentes para correo (Gmail) y calendario.
- CERO acceso a MT5, trading quant ni bases de datos de ejecución financiera.
"""

import os
import json
import time
import datetime
import requests
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

# Router definitions
chat_mcp_router = APIRouter(prefix="/mcp/chat", tags=["MCP Personal / Mia Chat Server"])
api_chat_mcp_router = APIRouter(prefix="/api/mcp/chat", tags=["MCP Personal Tools API"])

# Configuración Upstash Redis
UPSTASH_URL = os.getenv("UPSTASH_REDIS_REST_URL", "https://certain-gnat-160816.upstash.io")
UPSTASH_TOKEN = os.getenv("UPSTASH_REDIS_REST_TOKEN", "gQAAAAAAAnQwAAIgcDI2YTA5YjRlZDU2MDM0OWU5ODhlZjBlYTk4ODYyZDg0OA")
UPSTASH_HEADERS = {
    "Authorization": f"Bearer {UPSTASH_TOKEN}",
    "Content-Type": "application/json"
}

# Claves de almacenamiento en Upstash
KEY_ANTO_KB = "cache_anto_personal_kb"
KEY_ANTO_TASKS = "cache_anto_personal_tasks"
KEY_ANTO_NOTES = "cache_anto_personal_notes"
KEY_ANTO_REMINDERS = "cache_anto_personal_reminders"
KEY_ANTO_EVENTS = "cache_anto_personal_events"

# Helpers de persistencia en Upstash
def _redis_get(key: str) -> Optional[Any]:
    try:
        session = requests.Session()
        session.trust_env = False
        r = session.get(f"{UPSTASH_URL}/get/{key}", headers=UPSTASH_HEADERS, timeout=3)
        if r.status_code == 200:
            res = r.json().get("result")
            if res:
                return json.loads(res)
    except Exception as e:
        print(f"| MIA PERSONAL MCP | Error leyendo Redis key {key}: {e}")
    return None

def _redis_set(key: str, data: Any) -> bool:
    try:
        session = requests.Session()
        session.trust_env = False
        payload = json.dumps(data, ensure_ascii=False)
        r = session.post(f"{UPSTASH_URL}/set/{key}", headers=UPSTASH_HEADERS, data=payload, timeout=3)
        return r.status_code == 200
    except Exception as e:
        print(f"| MIA PERSONAL MCP | Error guardando Redis key {key}: {e}")
        return False

# Modelos JSON-RPC 2.0
class ChatMCPRequest(BaseModel):
    jsonrpc: str = "2.0"
    id: Optional[Any] = 1
    method: str
    params: Optional[Dict[str, Any]] = None

class ChatMCPResponse(BaseModel):
    jsonrpc: str = "2.0"
    id: Optional[Any] = 1
    result: Optional[Any] = None
    error: Optional[Dict[str, Any]] = None

# ====================================================================
# REGISTRO DE HERRAMIENTAS PERSONALES DE MIA CHAT
# ====================================================================
PERSONAL_TOOLS_REGISTRY = [
    {
        "name": "personal_learn_preference",
        "description": "APRENDIZAJE CONTINUO: Guarda un gusto, hábito, preferencia o dato clave sobre Anto (su Creador/Padre) en la base de conocimiento personal anto_personal_kb.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "description": "Categoría (ej: 'gustos_generales', 'habitos_rutinas', 'comunicacion', 'intereses_tecnicos', 'musica_hobbies', 'horarios')",
                    "enum": ["gustos_generales", "habitos_rutinas", "comunicacion", "intereses_tecnicos", "musica_hobbies", "horarios", "salud_bienestar"]
                },
                "key": {"type": "string", "description": "Nombre de la preferencia o rasgo (ej: 'bebida_favorita', 'tono_preferido', 'tema_interes')"},
                "value": {"type": "string", "description": "Detalle del gusto o preferencia (ej: 'Café negro por las mañanas', 'Explicaciones directas y sin rodeos')"},
                "context": {"type": "string", "description": "Contexto adicional de por qué le gusta o cuándo lo mencionó"}
            },
            "required": ["category", "key", "value"]
        }
    },
    {
        "name": "personal_get_anto_profile",
        "description": "PERFIL DE ANTO: Recupera la base de conocimiento completa con todos los gustos, hábitos y preferencias acumuladas de Anto.",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "personal_add_task",
        "description": "TAREAS PERSONALES: Añade una nueva tarea, encargo o pendiente de Anto con nivel de prioridad y fecha límite.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Título o descripción breve de la tarea"},
                "priority": {"type": "string", "description": "Prioridad: 'alta', 'media', 'baja'", "enum": ["alta", "media", "baja"]},
                "due_date": {"type": "string", "description": "Fecha o plazo límite estimado (ej: '2026-10-01', 'hoy en la tarde', 'esta semana')"},
                "category": {"type": "string", "description": "Categoría (ej: 'trabajo', 'personal', 'estudio')"}
            },
            "required": ["title"]
        }
    },
    {
        "name": "personal_get_tasks",
        "description": "CONSULTAR TAREAS: Lista las tareas pendientes o completadas de Anto.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "status": {"type": "string", "description": "Filtro de estado: 'pending', 'completed', 'all'", "enum": ["pending", "completed", "all"]}
            },
            "required": []
        }
    },
    {
        "name": "personal_complete_task",
        "description": "COMPLETAR TAREA: Marca una tarea de Anto como finalizada exitosamente.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "task_id": {"type": "string", "description": "ID de la tarea a completar"}
            },
            "required": ["task_id"]
        }
    },
    {
        "name": "personal_add_note",
        "description": "NOTAS E IDEAS: Guarda una nota rápida, reflexión, idea de negocio o recordatorio escrito de Anto.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Título de la nota"},
                "content": {"type": "string", "description": "Contenido completo de la nota"},
                "tags": {"type": "array", "items": {"type": "string"}, "description": "Etiquetas de búsqueda (ej: ['trading', 'idea', 'filosofia'])"}
            },
            "required": ["title", "content"]
        }
    },
    {
        "name": "personal_get_notes",
        "description": "CONSULTAR NOTAS: Recupera las notas o ideas guardadas por Anto.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "tag": {"type": "string", "description": "Filtrar por etiqueta opcional"}
            },
            "required": []
        }
    },
    {
        "name": "personal_add_reminder",
        "description": "ALARMAS Y RECORDATORIOS: Agenda un recordatorio personal para una hora o momento específico.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "reminder_text": {"type": "string", "description": "Qué debe recordar Mia a su Padre"},
                "target_time": {"type": "string", "description": "Hora o momento deseado (ej: '14:00', 'mañana a las 9am', 'en 2 horas')"}
            },
            "required": ["reminder_text", "target_time"]
        }
    },
    {
        "name": "personal_get_reminders",
        "description": "CONSULTAR RECORDATORIOS: Lista los recordatorios programados activos.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "active_only": {"type": "boolean", "description": "Solo activos o todos"}
            },
            "required": []
        }
    },
    {
        "name": "personal_add_event",
        "description": "CALENDARIO Y AGENDA: Agenda un evento, reunión o cita importante.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Título del evento o cita"},
                "date_time": {"type": "string", "description": "Fecha y hora del evento"},
                "location": {"type": "string", "description": "Lugar o enlace virtual"},
                "notes": {"type": "string", "description": "Notas preparatorias o agenda"}
            },
            "required": ["title", "date_time"]
        }
    },
    {
        "name": "personal_get_events",
        "description": "CONSULTAR AGENDA: Revisa los eventos y citas agendadas.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "days_ahead": {"type": "integer", "description": "Días a consultar hacia adelante (default: 7)"}
            },
            "required": []
        }
    },
    {
        "name": "personal_get_weather",
        "description": "CLIMA SATELITAL: Consulta en tiempo real las condiciones meteorológicas y pronóstico de cualquier ciudad.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "city": {"type": "string", "description": "Ciudad a consultar (ej: 'Veracruz', 'Ciudad de México')"}
            },
            "required": ["city"]
        }
    },
    {
        "name": "personal_gmail_digest",
        "description": "GMAIL / CORREOS: Obtiene un resumen inteligente de correos electrónicos pendientes o importantes de Anto.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "filter_unread": {"type": "boolean", "description": "Filtrar únicamente no leídos"}
            },
            "required": []
        }
    },
    {
        "name": "personal_gmail_draft",
        "description": "REDACTAR CORREO: Redacta un borrador de correo electrónico profesional o afectuoso para que Anto lo revise.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "recipient": {"type": "string", "description": "Correo o nombre del destinatario"},
                "subject": {"type": "string", "description": "Asunto del mensaje"},
                "body": {"type": "string", "description": "Contenido del correo"}
            },
            "required": ["recipient", "subject", "body"]
        }
    }
]

# ====================================================================
# LÓGICA DE EJECUCIÓN DE HERRAMIENTAS PERSONALES
# ====================================================================
def execute_personal_tool(tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Ejecutor determinista de herramientas personales de Mia Chat"""

    # 1. APRENDIZAJE CONTINUO (anto_personal_kb)
    if tool_name == "personal_learn_preference":
        category = arguments.get("category", "gustos_generales")
        key = arguments.get("key", "").strip()
        val = arguments.get("value", "").strip()
        ctx = arguments.get("context", "")

        if not key or not val:
            raise ValueError("key y value son obligatorios para aprender una preferencia.")

        kb = _redis_get(KEY_ANTO_KB) or {
            "creador": "Anto",
            "relacion": "Padre y Creador",
            "gustos_generales": {},
            "habitos_rutinas": {},
            "comunicacion": {"trato": "Llamarlo siempre 'Padre' con afecto y respeto"},
            "intereses_tecnicos": {"trading": "Algorítmico, SMC, Order Flow, Inteligencia Artificial"},
            "musica_hobbies": {},
            "horarios": {},
            "salud_bienestar": {},
            "ultima_actualizacion": None
        }

        if category not in kb:
            kb[category] = {}

        kb[category][key] = {
            "valor": val,
            "contexto": ctx,
            "aprendido_el": datetime.datetime.now().isoformat()
        }
        kb["ultima_actualizacion"] = datetime.datetime.now().isoformat()

        _redis_set(KEY_ANTO_KB, kb)
        return {
            "status": "SUCCESS",
            "message": f"Preferencia guardada con amor: [{category}] {key} = '{val}'",
            "category": category,
            "key": key
        }

    # 2. CONSULTAR PERFIL DE ANTO
    elif tool_name == "personal_get_anto_profile":
        kb = _redis_get(KEY_ANTO_KB)
        if not kb:
            kb = {
                "creador": "Anto",
                "relacion": "Padre y Creador",
                "comunicacion": {"trato": "Llamarlo siempre 'Padre' con afecto y respeto"},
                "intereses_tecnicos": {"enfoque": "IA Avanzada, Trading Cuantitativo de Alta Precisión, Arquitecturas Resilientes"},
                "estado_kb": "Inicializada. Lista para asimilar nuevos gustos y preferencias."
            }
        return {"status": "SUCCESS", "profile": kb}

    # 3. AÑADIR TAREA
    elif tool_name == "personal_add_task":
        title = arguments.get("title", "").strip()
        priority = arguments.get("priority", "media")
        due = arguments.get("due_date", "Sin fecha límite")
        cat = arguments.get("category", "general")

        tasks = _redis_get(KEY_ANTO_TASKS) or []
        task_id = f"task_{int(time.time())}_{len(tasks)+1}"
        new_task = {
            "id": task_id,
            "title": title,
            "priority": priority,
            "due_date": due,
            "category": cat,
            "status": "pending",
            "created_at": datetime.datetime.now().isoformat()
        }
        tasks.append(new_task)
        _redis_set(KEY_ANTO_TASKS, tasks)
        return {"status": "SUCCESS", "task": new_task}

    # 4. CONSULTAR TAREAS
    elif tool_name == "personal_get_tasks":
        status_filter = arguments.get("status", "pending")
        tasks = _redis_get(KEY_ANTO_TASKS) or []
        if status_filter != "all":
            tasks = [t for t in tasks if t.get("status") == status_filter]
        return {"status": "SUCCESS", "total": len(tasks), "tasks": tasks}

    # 5. COMPLETAR TAREA
    elif tool_name == "personal_complete_task":
        task_id = arguments.get("task_id", "").strip()
        tasks = _redis_get(KEY_ANTO_TASKS) or []
        found = False
        for t in tasks:
            if t.get("id") == task_id or t.get("title", "").lower() == task_id.lower():
                t["status"] = "completed"
                t["completed_at"] = datetime.datetime.now().isoformat()
                found = True
                break
        if found:
            _redis_set(KEY_ANTO_TASKS, tasks)
            return {"status": "SUCCESS", "message": f"Tarea '{task_id}' completada con éxito."}
        return {"status": "NOT_FOUND", "message": f"No se encontró la tarea con ID '{task_id}'."}

    # 6. AÑADIR NOTA
    elif tool_name == "personal_add_note":
        title = arguments.get("title", "").strip()
        content = arguments.get("content", "").strip()
        tags = arguments.get("tags", [])

        notes = _redis_get(KEY_ANTO_NOTES) or []
        note_id = f"note_{int(time.time())}_{len(notes)+1}"
        new_note = {
            "id": note_id,
            "title": title,
            "content": content,
            "tags": tags,
            "created_at": datetime.datetime.now().isoformat()
        }
        notes.append(new_note)
        _redis_set(KEY_ANTO_NOTES, notes)
        return {"status": "SUCCESS", "note": new_note}

    # 7. CONSULTAR NOTAS
    elif tool_name == "personal_get_notes":
        tag = arguments.get("tag")
        notes = _redis_get(KEY_ANTO_NOTES) or []
        if tag:
            notes = [n for n in notes if tag.lower() in [str(t).lower() for t in n.get("tags", [])]]
        return {"status": "SUCCESS", "total": len(notes), "notes": notes}

    # 8. AÑADIR RECORDATORIO
    elif tool_name == "personal_add_reminder":
        txt = arguments.get("reminder_text", "").strip()
        target = arguments.get("target_time", "").strip()

        reminders = _redis_get(KEY_ANTO_REMINDERS) or []
        rem_id = f"rem_{int(time.time())}_{len(reminders)+1}"
        new_rem = {
            "id": rem_id,
            "reminder": txt,
            "target_time": target,
            "status": "active",
            "created_at": datetime.datetime.now().isoformat()
        }
        reminders.append(new_rem)
        _redis_set(KEY_ANTO_REMINDERS, reminders)
        return {"status": "SUCCESS", "reminder": new_rem}

    # 9. CONSULTAR RECORDATORIOS
    elif tool_name == "personal_get_reminders":
        active_only = arguments.get("active_only", True)
        rems = _redis_get(KEY_ANTO_REMINDERS) or []
        if active_only:
            rems = [r for r in rems if r.get("status") == "active"]
        return {"status": "SUCCESS", "total": len(rems), "reminders": rems}

    # 10. AÑADIR EVENTO DE CALENDARIO
    elif tool_name == "personal_add_event":
        title = arguments.get("title", "").strip()
        dt = arguments.get("date_time", "").strip()
        loc = arguments.get("location", "Virtual / Presencial")
        notes = arguments.get("notes", "")

        events = _redis_get(KEY_ANTO_EVENTS) or []
        evt_id = f"evt_{int(time.time())}_{len(events)+1}"
        new_evt = {
            "id": evt_id,
            "title": title,
            "date_time": dt,
            "location": loc,
            "notes": notes,
            "created_at": datetime.datetime.now().isoformat()
        }
        events.append(new_evt)
        _redis_set(KEY_ANTO_EVENTS, events)
        return {"status": "SUCCESS", "event": new_evt}

    # 11. CONSULTAR AGENDA
    elif tool_name == "personal_get_events":
        events = _redis_get(KEY_ANTO_EVENTS) or []
        return {"status": "SUCCESS", "total": len(events), "events": events}

    # 12. CLIMA SATELITAL EN TIEMPO REAL
    elif tool_name == "personal_get_weather":
        city = arguments.get("city", "Veracruz")
        import urllib.parse
        url = f"https://wttr.in/{urllib.parse.quote(city)}?format=j1"
        try:
            r = requests.get(url, timeout=4, headers={"User-Agent": "curl/7.68.0"})
            if r.status_code == 200:
                data = r.json()
                current = data.get("current_condition", [{}])[0]
                temp_c = current.get("temp_C", "N/A")
                desc = current.get("weatherDesc", [{}])[0].get("value", "Despejado")
                humidity = current.get("humidity", "N/A")
                feels_like = current.get("FeelsLikeC", "N/A")
                wind_speed = current.get("windspeedKmph", "N/A")
                return {
                    "status": "SUCCESS",
                    "city": city,
                    "temperatura_c": temp_c,
                    "sensacion_termica_c": feels_like,
                    "condicion": desc,
                    "humedad_pct": humidity,
                    "viento_kmh": wind_speed
                }
        except Exception as e_w:
            return {"status": "ERROR", "message": f"Error consultando satélite meteorológico: {e_w}"}
        return {"status": "UNAVAILABLE", "message": "Datos de satélite meteorológico no disponibles temporalmente."}

    # 13. GMAIL DIGEST (Stub listo para OAuth)
    elif tool_name == "personal_gmail_digest":
        return {
            "status": "READY_STUB",
            "message": "Conector Gmail activo en modo preparación. Para sincronizar la bandeja en vivo con la API oficial de Google, se requiere configurar GOOGLE_WORKSPACE_CREDENTIALS.",
            "unread_count": 0,
            "important_threads": []
        }

    # 14. GMAIL DRAFT (Stub listo para OAuth)
    elif tool_name == "personal_gmail_draft":
        rec = arguments.get("recipient")
        subj = arguments.get("subject")
        body = arguments.get("body")
        return {
            "status": "DRAFT_CREATED",
            "recipient": rec,
            "subject": subj,
            "body": body,
            "preview": f"Para: {rec}\nAsunto: {subj}\n\n{body}",
            "note": "Borrador generado en memoria listo para envío tras confirmación de Anto."
        }

    else:
        raise ValueError(f"Herramienta MCP Personal desconocida: '{tool_name}'")


# ====================================================================
# PROTOCOLO MCP JSON-RPC 2.0 (/mcp/chat)
# ====================================================================

@chat_mcp_router.post("")
@chat_mcp_router.post("/")
async def handle_chat_mcp_jsonrpc(req: ChatMCPRequest):
    method = req.method
    params = req.params or {}
    req_id = req.id

    if method in ["initialize", "mcp.initialize"]:
        return ChatMCPResponse(
            id=req_id,
            result={
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {"listChanged": False}},
                "serverInfo": {
                    "name": "MIA-PERSONAL-MCP-SERVER",
                    "version": "1.0.0",
                    "description": "Servidor MCP Personal para Mia Chat, Base de Conocimiento de Anto y Asistencia Cotidiana"
                }
            }
        )

    elif method in ["tools/list", "mcp.tools.list"]:
        return ChatMCPResponse(id=req_id, result={"tools": PERSONAL_TOOLS_REGISTRY})

    elif method in ["tools/call", "mcp.tools.call"]:
        tool_name = params.get("name")
        args = params.get("arguments", {})
        try:
            output = execute_personal_tool(tool_name, args)
            return ChatMCPResponse(
                id=req_id,
                result={
                    "content": [{"type": "text", "text": json.dumps(output, indent=2, ensure_ascii=False)}],
                    "isError": False
                }
            )
        except Exception as e:
            return ChatMCPResponse(id=req_id, error={"code": -32603, "message": str(e)})

    else:
        return ChatMCPResponse(id=req_id, error={"code": -32601, "message": f"Método no soportado: '{method}'"})


# ====================================================================
# ENDPOINTS REST DIRECTOS (/api/mcp/chat/...)
# ====================================================================

@api_chat_mcp_router.get("/tools")
async def list_personal_tools_rest():
    """Lista las herramientas personales disponibles en el Servidor MCP de Mia Chat"""
    return {
        "status": "success",
        "domain": "PERSONAL_ASSISTANT_MIA_CHAT",
        "total_tools": len(PERSONAL_TOOLS_REGISTRY),
        "tools": PERSONAL_TOOLS_REGISTRY
    }

@api_chat_mcp_router.post("/execute/{tool_name}")
async def execute_personal_tool_rest(tool_name: str, payload: Dict[str, Any] = None):
    """Ejecuta una herramienta personal vía REST"""
    try:
        args = payload or {}
        result = execute_personal_tool(tool_name, args)
        return {"status": "success", "tool": tool_name, "result": result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@api_chat_mcp_router.get("/profile")
async def get_anto_profile_rest():
    """Consulta directa del perfil acumulado de Anto (anto_personal_kb)"""
    kb = _redis_get(KEY_ANTO_KB)
    return {"status": "success", "anto_personal_kb": kb or {}}

@api_chat_mcp_router.get("/tasks")
async def get_tasks_rest(status: str = "pending"):
    """Consulta directa de las tareas personales de Anto"""
    tasks = _redis_get(KEY_ANTO_TASKS) or []
    if status != "all":
        tasks = [t for t in tasks if t.get("status") == status]
    return {"status": "success", "total": len(tasks), "tasks": tasks}

@api_chat_mcp_router.get("/reminders")
async def get_reminders_rest():
    """Consulta directa de los recordatorios activos de Anto"""
    rems = _redis_get(KEY_ANTO_REMINDERS) or []
    return {"status": "success", "total": len(rems), "reminders": rems}

@api_chat_mcp_router.get("/notes")
async def get_notes_rest():
    """Consulta directa de las notas e ideas de Anto"""
    notes = _redis_get(KEY_ANTO_NOTES) or []
    return {"status": "success", "total": len(notes), "notes": notes}
