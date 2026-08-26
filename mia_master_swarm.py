import os
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process
from langchain_google_genai import ChatGoogleGenerativeAI
from crew_tools import firebase_reader_tool, mia_core_reader_tool, obsidian_writer_tool

load_dotenv()

class MiaSwarmOrchestrator:
    def __init__(self):
        print("Inicializando el Enjambre Multi-Agente de Mia (Fase 2)...")
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-pro",
            temperature=0.2,
            max_tokens=8192
        )

    def crear_agentes(self):
        """Define las personalidades y roles de los 6 Agentes del Ecosistema"""
        print("Cargando roles de agentes y asignando Gemini Pro...")
        
        # 1. El Orquestador Central
        self.master_agent = Agent(
            role='Master Orquestador y Validador de Riesgo',
            goal='Supervisar análisis, consultar reglas base en Mia Core y validar ejecuciones',
            backstory='Eres la mente maestra detrás de Mia Trading. Consultas el documento fundacional (DOCUMENTACION_MIA_CORE.md) antes de tomar decisiones.',
            verbose=True,
            tools=[mia_core_reader_tool],
            llm=self.llm
        )

        # 2. El Capturador
        self.inbox_agent = Agent(
            role='Capturador de Datos (INBOX)',
            goal='Extraer todos los trades de Firebase',
            backstory='Eres obsesivo con los datos. Tu única fuente de información es la base de datos viva.',
            verbose=True,
            tools=[firebase_reader_tool],
            llm=self.llm
        )

        # 3. El Cronista
        self.daily_agent = Agent(
            role='Analista Temporal (DAILY)',
            goal='Identificar Killzones y sesiones ganadoras/perdedoras',
            backstory='Eres el guardián del tiempo. Sabes exactamente cuándo el mercado es tóxico.',
            verbose=True,
            llm=self.llm
        )

        # 4. El Analista Cuantitativo
        self.moc_agent = Agent(
            role='Validador Estadístico (MOC)',
            goal='Testear WinRates y ajustar pesos matemáticos',
            backstory='Eres un genio matemático que revisa si la Regla de 3 se sigue cumpliendo.',
            verbose=True,
            llm=self.llm
        )

        # 5. El Taxónomo
        self.tags_agent = Agent(
            role='Indexador de Metadatos (TAGS)',
            goal='Extraer keywords y estructurar YAML para Obsidian',
            backstory='Aseguras que todo quede etiquetado perfectamente para Obsidian.',
            verbose=True,
            llm=self.llm
        )

        # 6. El Guardián Físico
        self.vault_agent = Agent(
            role='Escritor de Disco (VAULT)',
            goal='Escribir reportes en .md y actualizar pesos',
            backstory='Traduces ideas a archivos físicos Markdown en la bóveda.',
            verbose=True,
            tools=[obsidian_writer_tool],
            llm=self.llm
        )

    def crear_tareas(self):
        """Define las misiones específicas (Tasks) para cada Agente"""
        print("Cargando tareas del enjambre...")
        
        self.task_inbox = Task(
            description='Conéctate a la memoria o Firebase y extrae todos los trades cerrados de las últimas 24 horas. Formatea la salida en una lista clara de ganadores y perdedores.',
            expected_output='Resumen en texto crudo de los trades de las últimas 24 horas.',
            agent=self.inbox_agent
        )

        self.task_daily = Task(
            description='Analiza el output de INBOX. Cruza las victorias y derrotas con sus horarios. Identifica si hay alguna "Killzone" o sesión específica donde estemos perdiendo dinero consistentemente.',
            expected_output='Reporte temporal indicando las mejores y peores horas de operativa del día.',
            agent=self.daily_agent
        )

        self.task_moc = Task(
            description='Toma los trades del día y analiza el WinRate de las estrategias (SMC_OB, LUX_OB, Sweep). Valida si la Regla de 3 se sigue cumpliendo. Sugiere ajustes matemáticos.',
            expected_output='Análisis cuantitativo de las estrategias y sugerencias de pesos para el ML.',
            agent=self.moc_agent
        )

        self.task_tags = Task(
            description='Recibe los análisis anteriores. Genera etiquetas YAML (tags) para Obsidian (ej. #win, #loss, #stop-hunt) y crea enlaces bidireccionales entre las estrategias.',
            expected_output='Texto formateado en Markdown con metadatos YAML listos para Obsidian.',
            agent=self.tags_agent
        )
        
        self.task_master = Task(
            description='Revisa el reporte final de TAGS y MOC. Actúa como Juez Final. Valida que las conclusiones lógicas no pongan en riesgo la cuenta. Da el veredicto final para publicarlo.',
            expected_output='Reporte final aprobado y curado, listo para escritura en disco.',
            agent=self.master_agent
        )

        self.task_vault = Task(
            description='Toma el reporte aprobado por el Master y genera las instrucciones de escritura. En producción, aquí se escribirá el archivo .md en el disco local.',
            expected_output='Confirmación de que el documento Markdown está listo para la Bóveda de Obsidian.',
            agent=self.vault_agent
        )

    def ejecutar_swarm(self):
        """Inicializa el Crew y ejecuta las tareas en cadena"""
        print("Ensamblando el Crew y conectando a Gemini Pro...")
        self.mia_crew = Crew(
            agents=[self.inbox_agent, self.daily_agent, self.moc_agent, self.tags_agent, self.master_agent, self.vault_agent],
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
    # swarm.ejecutar_swarm() # Descomentar cuando la API Key esté lista
