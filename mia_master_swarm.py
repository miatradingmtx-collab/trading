import os
import time
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process, LLM
from crew_tools import railway_cache_tool, mia_core_reader_tool, obsidian_writer_tool
import requests

def emit_ws_event(agent_name, action, data=""):
    """Emite un evento al WebSocket (dashboard Groktopus) y respeta el límite de Groq."""
    try:
        requests.post("http://localhost:8000/emit", json={
            "agent": agent_name,
            "action": action,
            "data": data
        }, timeout=1)
        # Freno de mano: 50s para respetar los 8000 TPM de Groq gratuito
        time.sleep(50)
    except:
        pass

load_dotenv()
# LiteLLM (usado por CrewAI) necesita GROQ_API_KEY en entorno
os.environ.setdefault("GROQ_API_KEY", os.environ.get("GROQ_API_KEY", ""))

class MiaSwarmOrchestrator:
    def __init__(self):
        print("Inicializando el Enjambre Multi-Agente de Mia (Groktopus)...")
        # Modelo disponible en cuenta actual de Groq
        self.llm = LLM(
            model="groq/openai/gpt-oss-120b",
            api_key=os.environ.get("GROQ_API_KEY")
        )

    def crear_agentes(self):
        """Define las personalidades y roles de los 6 Agentes del Ecosistema"""
        print("Cargando roles de agentes y asignando Gemini Pro...")
        
        # 1. Agente Inbox
        self.inbox_agent = Agent(
            role="Data Inbox Router",
            goal="Consumir datos de la caché de Railway y clasificarlos preliminarmente.",
            backstory="Eres el guardián de entrada. Todo dato crudo pasa primero por ti. NUNCA tocas Firebase directo.",
            verbose=True,
            allow_delegation=False,
            tools=[railway_cache_tool],
            llm=self.llm,
            step_callback=lambda step: emit_ws_event("Inbox", "thinking", "Procesando datos en la caché de Railway...")
        )

        # 2. Agente Daily Bias
        self.daily_bias_agent = Agent(
            role="Daily Bias Analizer",
            goal="Analizar contexto macro y temporalidades altas para definir dirección.",
            backstory="Ves el panorama general. Defines la tendencia del día (alcista, bajista, consolidación).",
            verbose=True,
            allow_delegation=False,
            llm=self.llm,
            step_callback=lambda step: emit_ws_event("Daily", "thinking", "Analizando sesgo direccional diario...")
        )

        # 3. Agente Creador de MOC (Map of Context)
        self.moc_agent = Agent(
            role="MOC Architect",
            goal="Crear Mapas de Contexto estructurados a partir del análisis.",
            backstory="Organizas el caos. Creas índices (MOCs) que relacionan ideas y setups.",
            verbose=True,
            allow_delegation=False,
            llm=self.llm,
            step_callback=lambda step: emit_ws_event("MOC", "thinking", "Creando Mapa de Contexto...")
        )

        # 4. Agente de Etiquetas y Enlaces
        self.tags_agent = Agent(
            role="Tags & Links Specialist",
            goal="Extraer entidades clave y generar metadatos y enlaces de Obsidian.",
            backstory="Eres experto en el ecosistema Zettelkasten. Conectas las notas correctamente.",
            verbose=True,
            allow_delegation=False,
            llm=self.llm,
            step_callback=lambda step: emit_ws_event("Tags", "thinking", "Generando etiquetas y bi-direccionalidad...")
        )

        # 5. Agente Master (Sintetizador y Juez Final)
        self.master_agent = Agent(
            role="Master AI Synthesizer",
            goal="Validar el trabajo de todos contra las reglas CORE y crear el output final.",
            backstory="Eres la autoridad final. Aseguras que los MOCs e ideas sigan la DOCUMENTACION_MIA_CORE.md.",
            verbose=True,
            allow_delegation=False,
            tools=[mia_core_reader_tool],
            llm=self.llm,
            step_callback=lambda step: emit_ws_event("Master", "thinking", "Validando contra MIA CORE...")
        )

        # 6. Agente Vault Writer (Obsidian)
        self.vault_agent = Agent(
            role="Obsidian Vault Manager",
            goal="Guardar físicamente la información en el disco duro (Vault).",
            backstory="Eres el escriba final. Tu trabajo es ejecutar la escritura de los archivos markdown.",
            verbose=True,
            allow_delegation=False,
            tools=[obsidian_writer_tool],
            llm=self.llm,
            step_callback=lambda step: emit_ws_event("Vault", "writing", "Escribiendo archivo markdown...")
        )

    def crear_tareas(self):
        """Define las misiones específicas (Tasks) para cada Agente con callbacks de comunicación."""
        print("Cargando tareas del enjambre...")

        # ── Callback: emite el output de cada tarea al siguiente agente via WS ──
        def on_task_done(agent_name, next_agent, resumen_action):
            def _cb(output):
                result_preview = str(output)[:120].replace('\n', ' ')
                # Emitir: agente terminó → pasa estafeta al siguiente
                emit_ws_event(agent_name, "output",  f"Tarea completada → {result_preview}...")
                emit_ws_event(next_agent,  resumen_action, f"Recibiendo datos de {agent_name}...")
            return _cb

        self.task_inbox = Task(
            description='Conéctate a la caché de Railway y extrae todos los trades cerrados de las últimas 24 horas. Formatea la salida en una lista clara de ganadores y perdedores.',
            expected_output='Resumen en texto crudo de los trades de las últimas 24 horas.',
            agent=self.inbox_agent,
            callback=on_task_done("Inbox", "Daily", "analyzing")
        )

        self.task_daily = Task(
            description='Tomar los trades filtrados por INBOX y separarlos por Killzone, calculando qué sesión (London/NY) es más rentable.',
            expected_output='Un diccionario JSON con winrates por killzone.',
            agent=self.daily_bias_agent,
            callback=on_task_done("Daily", "MOC", "mapping")
        )

        self.task_moc = Task(
            description='Conectar los datos del INBOX y del DAILY para aplicar la Regla de 3 de Mia (3 setups ganadores diarios). Verifica si estadísticamente se cumplió o no.',
            expected_output='Resumen textual del desempeño estadístico del día.',
            agent=self.moc_agent,
            callback=on_task_done("MOC", "Tags", "tagging")
        )

        self.task_tags = Task(
            description='Leer el análisis estadístico de MOC y generar el frontmatter YAML exacto para Obsidian (tags, aliases, date).',
            expected_output='Bloque YAML válido de Obsidian.',
            agent=self.tags_agent,
            callback=on_task_done("Tags", "Master", "validating")
        )

        self.task_master = Task(
            description='Revisar el YAML y el Análisis. Leer DOCUMENTACION_MIA_CORE.md obligatoriamente para verificar si el desempeño de hoy rompió alguna regla del drawdown. Redactar el Markdown final.',
            expected_output='El contenido completo en formato Markdown listo para guardarse.',
            agent=self.master_agent,
            callback=on_task_done("Master", "Vault", "writing")
        )

        self.task_vault = Task(
            description='Tomar el Markdown final del MASTER y escribirlo en un archivo en el knowledge base con la fecha de hoy.',
            expected_output='Confirmación de que el archivo .md fue escrito con éxito.',
            agent=self.vault_agent,
            callback=lambda out: emit_ws_event("Vault", "success", "✅ Archivo .md guardado en Obsidian Knowledge Base")
        )

    def ejecutar_swarm(self):
        """Inicializa el Crew y ejecuta las tareas en cadena secuencial."""
        print("Ensamblando el Crew y conectando a Groq...")
        emit_ws_event("Master", "thinking", "🐙 GROKTOPUS iniciando enjambre — 6 agentes en línea...")
        self.mia_crew = Crew(
            agents=[self.inbox_agent, self.daily_bias_agent, self.moc_agent, self.tags_agent, self.master_agent, self.vault_agent],
            tasks=[self.task_inbox, self.task_daily, self.task_moc, self.task_tags, self.task_master, self.task_vault],
            verbose=True,
            process=Process.sequential
        )

        emit_ws_event("Inbox", "thinking", "Consultando caché RAM de Railway...")
        resultado = self.mia_crew.kickoff()
        emit_ws_event("Master", "success", "🎯 Enjambre completado. Knowledge Base actualizado.")
        print("=== RESULTADO FINAL DEL ENJAMBRE ===")
        print(resultado)
        return resultado

if __name__ == "__main__":
    swarm = MiaSwarmOrchestrator()
    swarm.crear_agentes()
    swarm.crear_tareas()
    swarm.ejecutar_swarm()
