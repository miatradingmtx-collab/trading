import os
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process, LLM
from crew_tools import firebase_reader_tool, mia_core_reader_tool, obsidian_writer_tool
import requests

def emit_ws_event(agent_name, action, data=""):
    try:
        requests.post("http://localhost:8000/emit", json={
            "agent": agent_name,
            "action": action,
            "data": data
        }, timeout=1)
    except:
        pass

load_dotenv()
# LiteLLM (usado por CrewAI) espera GEMINI_API_KEY
if "GOOGLE_API_KEY" in os.environ and "GEMINI_API_KEY" not in os.environ:
    os.environ["GEMINI_API_KEY"] = os.environ["GOOGLE_API_KEY"]

class MiaSwarmOrchestrator:
    def __init__(self):
        print("Inicializando el Enjambre Multi-Agente de Mia (Fase 2)...")
        self.llm = LLM(
            model="gemini/gemini-2.5-flash", 
            api_key=os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
        )

    def crear_agentes(self):
        """Define las personalidades y roles de los 6 Agentes del Ecosistema"""
        print("Cargando roles de agentes y asignando Gemini Pro...")
        
        # 1. Agente Inbox
        self.inbox_agent = Agent(
            role="Data Inbox Router",
            goal="Consumir datos de Firebase y clasificarlos preliminarmente.",
            backstory="Eres el guardián de entrada. Todo dato crudo pasa primero por ti.",
            verbose=True,
            allow_delegation=False,
            tools=[firebase_reader_tool],
            llm=self.llm,
            step_callback=lambda step: emit_ws_event("Inbox", "thinking", "Procesando datos en Firebase...")
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
        """Define las misiones específicas (Tasks) para cada Agente"""
        print("Cargando tareas del enjambre...")
        
        self.task_inbox = Task(
            description='Conéctate a la memoria o Firebase y extrae todos los trades cerrados de las últimas 24 horas. Formatea la salida en una lista clara de ganadores y perdedores.',
            expected_output='Resumen en texto crudo de los trades de las últimas 24 horas.',
            agent=self.inbox_agent
        )

        # 2. Tarea de Daily
        self.task_daily = Task(
            description='Tomar los trades filtrados por INBOX y separarlos por Killzone, calculando qué sesión (London/NY) es más rentable.',
            expected_output='Un diccionario JSON con winrates por killzone.',
            agent=self.daily_bias_agent,
        )

        # 3. Tarea de MOC
        self.task_moc = Task(
            description='Conectar los datos del INBOX y del DAILY para aplicar la Regla de 3 de Mia (3 setups ganadores diarios). Verifica si estadísticamente se cumplió o no.',
            expected_output='Resumen textual del desempeño estadístico del día.',
            agent=self.moc_agent
        )

        # 4. Tarea de TAGS
        self.task_tags = Task(
            description='Leer el análisis estadístico de MOC y generar el frontmatter YAML exacto para Obsidian (tags, aliases, date).',
            expected_output='Bloque YAML válido de Obsidian.',
            agent=self.tags_agent
        )

        # 5. Tarea del MASTER
        self.task_master = Task(
            description='Revisar el YAML y el Análisis. Leer DOCUMENTACION_MIA_CORE.md obligatoriamente para verificar si el desempeño de hoy rompió alguna regla del drawdown. Redactar el Markdown final.',
            expected_output='El contenido completo en formato Markdown listo para guardarse.',
            agent=self.master_agent
        )

        # 6. Tarea del VAULT
        self.task_vault = Task(
            description='Tomar el Markdown final del MASTER y escribirlo en un archivo en C:\\Users\\ecybe\\OneDrive\\Documentos\\Trading\\mia_knowledge_base con la fecha de hoy.',
            expected_output='Confirmación de que el archivo .md fue escrito con éxito.',
            agent=self.vault_agent
        )

    def ejecutar_swarm(self):
        """Inicializa el Crew y ejecuta las tareas en cadena"""
        print("Ensamblando el Crew y conectando a Gemini Pro...")
        self.mia_crew = Crew(
            agents=[self.inbox_agent, self.daily_bias_agent, self.moc_agent, self.tags_agent, self.master_agent, self.vault_agent],
            tasks=[self.task_inbox, self.task_daily, self.task_moc, self.task_tags, self.task_master, self.task_vault],
            verbose=True,
            process=Process.sequential # Los agentes se pasan la información uno tras otro en orden
        )
        
        print("¡Iniciando simulación del Enjambre (Dry Run)!")
        resultado = self.mia_crew.kickoff()
        print("=== RESULTADO FINAL DEL ENJAMBRE ===")
        print(resultado)
        return resultado

if __name__ == "__main__":
    swarm = MiaSwarmOrchestrator()
    swarm.crear_agentes()
    swarm.crear_tareas()
    swarm.ejecutar_swarm()
