import os
import json
import firebase_admin
from firebase_admin import credentials, firestore
from crewai.tools import tool

# Inicializar Firebase solo si no está inicializado
try:
    firebase_admin.get_app()
except ValueError:
    cred = credentials.Certificate('serviceAccountKey.json')
    firebase_admin.initialize_app(cred)

db = firestore.client()

@tool("Leer Historico Firebase")
def firebase_reader_tool() -> str:
    """Útil para extraer los registros (trades) históricos de la base de datos de Firebase."""
    try:
        # Extraer una muestra representativa de los últimos trades para análisis
        docs = db.collection("mia_audit_logs").order_by("fecha_hora", direction=firestore.Query.DESCENDING).limit(100).stream()
        trades = []
        for d in docs:
            data = d.to_dict()
            trades.append({
                "ticket": d.id,
                "activo": data.get("activo"),
                "pnl": data.get("pnl_final", 0),
                "ganador": data.get("pnl_final", 0) > 0,
                "estrategia": data.get("estrategia"),
                "hora": data.get("fecha_hora")
            })
        return json.dumps(trades, indent=2)
    except Exception as e:
        return f"Error leyendo Firebase: {str(e)}"

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
        # Reemplazar espacios para nombres de archivo
        safe_title = titulo_archivo.replace(" ", "_").replace("/", "-")
        if not safe_title.endswith(".md"):
            safe_title += ".md"
            
        with open(safe_title, "w", encoding="utf-8") as f:
            f.write(contenido_markdown)
        return f"Éxito: Archivo {safe_title} creado correctamente en la bóveda de Obsidian."
    except Exception as e:
        return f"Error escribiendo en disco: {str(e)}"
