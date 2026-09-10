import os
import json
import firebase_admin
from firebase_admin import credentials, firestore
from langchain.tools import tool

import requests

# Inicializar Firebase solo si no está inicializado (ya no se usa para lectura, pero lo dejamos por si acaso)
try:
    firebase_admin.get_app()
except ValueError:
    try:
        cred = credentials.Certificate('serviceAccountKey.json')
        firebase_admin.initialize_app(cred)
    except Exception:
        pass

db = None
try:
    db = firestore.client()
except Exception:
    pass

@tool("Leer Railway Cache RAM")
def railway_cache_tool() -> str:
    """Útil para extraer métricas, KPIs y rendimiento por estrategia desde la caché RAM (Ahora en Upstash Redis)."""
    try:
        url = "https://certain-gnat-160816.upstash.io/get/cache_mt5"
        headers = {"Authorization": "Bearer gQAAAAAAAnQwAAIgcDI2YTA5YjRlZDU2MDM0OWU5ODhlZjBlYTk4ODYyZDg0OA"}
        
        session = requests.Session()
        session.trust_env = False
        response = session.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        if data.get("result"):
            # Redis guarda strings, lo convertimos de vuelta a JSON
            try:
                parsed_data = json.loads(data["result"])
                return f"Datos desde Upstash Redis:\n{json.dumps(parsed_data, indent=2)}"
            except:
                return f"Datos (Raw String) desde Upstash Redis:\n{data['result']}"
        else:
            return "El caché de Redis está vacío. Esperando datos del Bot MT5."
            
    except Exception as e:
        return f"Error leyendo Upstash Redis Cache: {str(e)}"

@tool("Leer Mia Core Markdown")
def mia_core_reader_tool() -> str:
    """Útil para que el Master Agent lea las reglas de oro y arquitectura base (Regla de 3, Riesgo) desde DOCUMENTACION_MIA_CORE.md"""
    try:
        with open("DOCUMENTACION_MIA_CORE.md", "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"Error leyendo Mia Core: {str(e)}"

@tool("Escribir Reporte en Obsidian")
def obsidian_writer_tool(titulo_archivo: str, contenido_markdown: str) -> str:
    """Útil para guardar físicamente los análisis de los agentes en formato .md en la bóveda de Obsidian."""
    try:
        import os
        # Reemplazar espacios para nombres de archivo
        safe_title = titulo_archivo.replace(" ", "_").replace("/", "-")
        if not safe_title.endswith(".md"):
            safe_title += ".md"
            
        base_path = r"D:\obsidiana\Proyectos\Mia_Trading"
        os.makedirs(base_path, exist_ok=True)
        full_path = os.path.join(base_path, safe_title)
            
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(contenido_markdown)
        return f"Éxito: Archivo {safe_title} creado correctamente en la bóveda de Obsidian en {full_path}."
    except Exception as e:
        return f"Error escribiendo en disco: {str(e)}"
