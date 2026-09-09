import os
import json
import firebase_admin
from firebase_admin import credentials, firestore
from crewai.tools import tool

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
    """Útil para extraer métricas, KPIs y rendimiento por estrategia desde la caché RAM de Railway."""
    try:
        headers = {'User-Agent': 'MiaSwarmBot/1.0'}
        response = requests.get(
            'https://trading-production-927a.up.railway.app/api/dashboard_data',
            headers=headers, timeout=20
        )
        response.raise_for_status()
        data = response.json().get("data", {})

        # Extraer métricas clave disponibles en el endpoint
        resumen = {
            "fuente": "Railway Cache RAM (NO Firebase directo)",
            "balance_actual": data.get("balance_actual"),
            "equity": data.get("equity"),
            "floating_pnl": data.get("floating_pnl"),
            "kpis": data.get("kpis", {}),
            "estrategias": data.get("estrategias", []),
            "rendimiento_activos": data.get("rendimiento_activos", {}),
            "operaciones_activas": data.get("operaciones_activas", []),
        }
        return json.dumps(resumen, indent=2, ensure_ascii=False)
    except Exception as e:
        return f"Error leyendo Railway Cache: {str(e)}"

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
