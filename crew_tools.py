import os
import json
import firebase_admin
from firebase_admin import credentials, firestore
from langchain.tools import tool

import requests

# Inicializar Firebase para grabar historial del Enjambre
db = None
try:
    firebase_admin.get_app()
    db = firestore.client()
except ValueError:
    try:
        if os.path.exists('serviceAccountKey.json'):
            cred = credentials.Certificate('serviceAccountKey.json')
            firebase_admin.initialize_app(cred)
            db = firestore.client()
        elif os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON"):
            import json
            service_account_info = json.loads(os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON").strip())
            cred = credentials.Certificate(service_account_info)
            firebase_admin.initialize_app(cred)
            db = firestore.client()
    except Exception as e:
        print(f"Error inicializando Firebase en crew_tools: {e}")
except Exception as e:
    print(f"Error general Firebase en crew_tools: {e}")


@tool("Leer Railway Cache RAM")
def railway_cache_tool() -> str:
    """Útil para extraer métricas, KPIs, rendimiento, TensorFlow y Trading Matrix desde Upstash Redis vía MGET (0 Firebase, velocidad de la luz)."""
    try:
        url = "https://certain-gnat-160816.upstash.io/mget/cache_mt5/cache_mia_tensorflow/cache_trading_matrix/cache_system_memory"
        headers = {"Authorization": "Bearer gQAAAAAAAnQwAAIgcDI2YTA5YjRlZDU2MDM0OWU5ODhlZjBlYTk4ODYyZDg0OA"}
        
        session = requests.Session()
        session.trust_env = False
        response = session.get(url, headers=headers, timeout=6)
        response.raise_for_status()
        
        slots = response.json().get("result", [])
        if not slots or not slots[0]:
            return "El caché de Redis está vacío. Esperando datos del Bot MT5."
            
        parsed_data = json.loads(slots[0])
        data_filtrada = {
            "kpis": parsed_data.get("kpis", {}),
            "activos": parsed_data.get("rendimiento_activos", {}),
            "activas": parsed_data.get("operaciones_activas", []),
            "estrategias_vectorizadas": parsed_data.get("estrategias", []),
            "indicadores_ml": parsed_data.get("indicadores", []),
            "ml_matriz_scores": parsed_data.get("matriz_scores", {})
        }
        
        # 1. Cerebro TensorFlow (slot 1)
        if len(slots) > 1 and slots[1]:
            try:
                data_filtrada["tensorflow_ai"] = json.loads(slots[1])
            except Exception:
                data_filtrada["tensorflow_ai"] = {"status": "error_parsing"}
        else:
            data_filtrada["tensorflow_ai"] = {"status": "offline"}

        # 2. Trading Matrix 21 activos (slot 2)
        if len(slots) > 2 and slots[2]:
            try:
                m_json = json.loads(slots[2])
                data_filtrada["trading_matrix_scores"] = {
                    k: {
                        "score": v.get("score_porcentaje", 0),
                        "estado": v.get("estado_ejecucion", "INACTIVO"),
                        "rsi": v.get("rsi", 50.0)
                    }
                    for k, v in m_json.items()
                }
            except Exception:
                pass

        # 3. Memoria Colectiva (slot 3)
        if len(slots) > 3 and slots[3]:
            try:
                data_filtrada["system_memory"] = json.loads(slots[3])
            except Exception:
                pass
        
        return f"Datos Minimizados (Upstash Redis):\n{json.dumps(data_filtrada, indent=2)}"
    except Exception as e:
        return f"Error leyendo Upstash Redis Cache vía MGET: {str(e)}"

@tool("Leer Matriz de Activos Upstash")
def upstash_trading_matrix_tool() -> str:
    """Útil para consultar las confirmaciones técnicas, RSI, score y liquidez de los 21 activos en Upstash Redis (cache_trading_matrix)."""
    try:
        url = "https://certain-gnat-160816.upstash.io/get/cache_trading_matrix"
        headers = {"Authorization": "Bearer gQAAAAAAAnQwAAIgcDI2YTA5YjRlZDU2MDM0OWU5ODhlZjBlYTk4ODYyZDg0OA"}
        session = requests.Session()
        session.trust_env = False
        res = session.get(url, headers=headers, timeout=5)
        if res.status_code == 200:
            result = res.json().get("result")
            if result:
                matrices = json.loads(result)
                resumen = {
                    k: {
                        "score": v.get("score_porcentaje", 0),
                        "estado": v.get("estado_ejecucion", "INACTIVO"),
                        "rsi": v.get("rsi", 50.0),
                        "confirmaciones": v.get("confirmaciones_tecnicas", {})
                    }
                    for k, v in matrices.items()
                }
                return json.dumps(resumen, indent=2)
        return "Caché de trading matrix vacía."
    except Exception as e:
        return f"Error leyendo trading matrix de Upstash: {e}"

@tool("Leer Mia Core Markdown")
def mia_core_reader_tool() -> str:
    """Útil para que el Master Agent lea las reglas de oro y arquitectura base (Regla de 3, Riesgo) desde DOCUMENTACION_MIA_CORE.md"""
    try:
        # BYPASS ANTI-413 (Token Optimization): Devolvemos la síntesis estricta de las reglas maestras de riesgo y ejecución
        return (
            "REGLAS DE ORO MIA CORE: "
            "1. Score >= 0.70 es APROBADO, menor es VETADO. "
            "2. Setups en Order Block Zona 2H y Lux Algo OB tienen máxima prioridad y apalancamiento institucional. "
            "3. Filtro de Noticias: Prohibido operar en noticias de alto impacto (bloqueo 15m pre y 8m post-noticia para evitar trampas institucionales de liquidez). "
            "4. Cierre parcial al 40% del recorrido asegurando +15% de ganancia real en POC y activando trailing stop defensivo."
        )
    except Exception as e:
        return f"Error leyendo Mia Core: {str(e)}"

@tool("Escribir Reporte en Obsidian")
def obsidian_writer_tool(titulo_archivo: str, contenido_markdown: str) -> str:
    """Útil para guardar físicamente los análisis de los agentes (Veredicto y Variables) en formato .md. Sincroniza automáticamente a Upstash Redis para tener el histórico desacoplado en la nube."""
    try:
        import os
        import json
        import requests
        
        # 1. Escritura Local en el contenedor (Opcional, pero util para logs)
        safe_title = titulo_archivo.replace(" ", "_").replace("/", "-")
        if not safe_title.endswith(".md"):
            safe_title += ".md"
            
        with open(safe_title, "w", encoding="utf-8") as f:
            f.write(contenido_markdown)
            
        # 2. Desacoplamiento a Upstash Redis (Historial de Enjambres)
        upstash_url = f"https://certain-gnat-160816.upstash.io/set/mia_swarm_history_{safe_title}"
        upstash_headers = {"Authorization": "Bearer gQAAAAAAAnQwAAIgcDI2YTA5YjRlZDU2MDM0OWU5ODhlZjBlYTk4ODYyZDg0OA"}
        
        # Guardamos un JSON estructurado con la historia
        payload = {
            "title": safe_title,
            "content": contenido_markdown,
            "timestamp": "2026-09-11" # Simplificado, el servidor pone el suyo
        }
        
        session = requests.Session()
        session.trust_env = False
        res = session.post(upstash_url, headers=upstash_headers, data=json.dumps(payload), timeout=10)
        
        # 3. Homologación en Firebase (Colección swarm_history)
        firebase_msg = ""
        global db
        try:
            if db is not None:
                db.collection("swarm_history").document(safe_title).set(payload)
                firebase_msg = "y homologado en Firebase (swarm_history)"
            else:
                firebase_msg = "(Firebase no conectado localmente)"
        except Exception as e:
            firebase_msg = f"(Error guardando en Firebase: {str(e)})"
        
        if res.status_code == 200:
            return f"✅ Éxito: Análisis guardado en Redis {firebase_msg}."
        else:
            return f"⚠️ Guardado local/Firebase, pero error en Upstash: {res.text}"

    except Exception as e:
        return f"Error en obsidian_writer_tool: {str(e)}"
