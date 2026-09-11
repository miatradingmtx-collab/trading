import os
import json
import time
import requests
import sys
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process

from crew_tools import railway_cache_tool, obsidian_writer_tool
from math_agent_skills import calc_area_under_curve, markov_transition_matrix
from stat_agent_skills import calculate_expected_value, generate_execution_score

load_dotenv()
os.environ["GROQ_API_KEY"] = os.getenv("GROQ_API_KEY")

# Forzar codificación UTF-8 para evitar errores con emojis en Windows CMD (EventBus Error)
if sys.stdout.encoding != 'utf-8':
    os.environ["PYTHONIOENCODING"] = "utf-8"

# Emisor de WebSocket para conectar con React 3D (La Terminal de Cristal)
def emit_ws_event(agent_name, action, data):
    """Envía un evento al WebSocket server vía HTTP interno"""
    try:
        import os
        port = os.environ.get("PORT", "8000")
        requests.post(f"http://localhost:{port}/emit", json={
            "agent": agent_name,
            "action": action,
            "data": data
        })
    except:
        pass

def create_callback(agent_name):
    def callback(output):
        # Frenamos el LLM 15s para no hacer saltar el Error 429 de límite de tokens (8000 TPM)
        time.sleep(15) 
        
        # CrewAI >= 0.x envia diferentes tipos de objetos al callback (AgentStep, ToolResult, etc.)
        # Hacemos str(output) para no chocar con atributos deprecados como .raw
        texto = str(output)
        emit_ws_event(agent_name, "OUTPUT", texto[:150] + "...")
    return callback

from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI

# ── FAILOVER DINÁMICO (Tolerancia a fallos 24/7) ──
# Motor Principal: Groq (Llama-based, cuota diaria de 500k tokens)
primary_llm = ChatGroq(
    model_name="groq/compound-mini",
    groq_api_key=os.environ.get("GROQ_API_KEY")
)

# Motor de Respaldo: Gemini 1.5 Flash (1500 peticiones diarias gratuitas)
# Intercepta automáticamente errores 429 de Groq para operar 24h sin frenar.
fallback_llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-flash",
    google_api_key=os.environ.get("GOOGLE_API_KEY"),
    temperature=0.2
)

my_llm = primary_llm.with_fallbacks([fallback_llm])

# ── 1. TIDAL (Liquidez) ──
tidal = Agent(
    role="TIDAL - Order Book Scanner",
    goal="Leer los volúmenes institucionales y reportar bloqueos.",
    backstory="Analizas los deltas de volumen en milisegundos buscando trampas institucionales.",
    verbose=True,
    memory=False,
    llm=my_llm,
    step_callback=create_callback("TIDAL"),
    tools=[railway_cache_tool]
)

# ── 2. LUMEN (Sentimiento) (APAGADO TEMPORALMENTE - Límite de Tokens Groq) ──
# lumen = Agent(...)

# ── 3. NORO (Matemáticas Duras) ──
noro = Agent(
    role='Fair Value Math (NORO)',
    goal='Calcular integrales y matrices de markov.',
    backstory='Eres un quant matemático. Usas las herramientas de Área Bajo la Curva y Matrices de Markov.',
    tools=[calc_area_under_curve, markov_transition_matrix],
    llm=my_llm,
    step_callback=create_callback("NORO")
)

# ── 4. ZEPHR (Estadística y Esperanza) ──
zephr = Agent(
    role='Liquidity Mapper & Stats (ZEPHR)',
    goal='Calcular la esperanza matemática y el score probabilístico.',
    backstory='Usas herramientas bayesianas para sacar un score final (Consenso > 0.70).',
    tools=[calculate_expected_value, generate_execution_score],
    llm=my_llm,
    step_callback=create_callback("ZEPHR")
)

# ── 5. OKAPI (Cobertura) (APAGADO TEMPORALMENTE - Límite de Tokens Groq) ──
# okapi = Agent(...)

# ── 6. RUNE (Veto de Riesgo) ──
rune = Agent(
    role='Risk Control (RUNE)',
    goal='Aprobar o rechazar (Veto) el trade basado en el Consenso de ZEPHR y guardarlo en Obsidian.',
    backstory='Tu único trabajo es decir NO si el score es menor a 0.70. Eres la muralla de riesgo y anotas el reporte final.',
    tools=[obsidian_writer_tool],
    llm=my_llm,
    step_callback=create_callback("RUNE")
)

# ── 7. VESKA (Ejecución) (APAGADO TEMPORALMENTE - Límite de Tokens Groq) ──
# veska = Agent(...)

# ── 8. MARIN (Liquidación) (APAGADO TEMPORALMENTE - Funciones delegadas a RUNE) ──
# marin = Agent(...)

# ── TAREAS ──
tasks = [
    Task(description='Obtén los KPIs actuales desde railway_cache_tool.', expected_output='Resumen de liquidez.', agent=tidal),
    Task(description='Usa calc_area_under_curve con "[10,20,30]", "[1,2,3]". Y genera una matriz de markov con \'["Alcista", "Bajista", "Alcista"]\'.', expected_output='Fair Value y Matrices.', agent=noro),
    Task(description='Usa calculate_expected_value (wr=0.75, avg_win=100, avg_loss=50). Y genera score de ejecucion (prob=0.68, wr=0.75).', expected_output='Score de consenso.', agent=zephr),
    Task(description='Revisa el output estadístico. Si el Score es mayor a 0.70 aprueba el trade, si no VETADO. Usa obsidian_writer_tool para guardar el dictamen.', expected_output='Confirmación de registro (APROBADO/VETADO guardado).', agent=rune)
]

# ── CREW MASTER ──
groktopus_crew = Crew(
    agents=[tidal, noro, zephr, rune],
    tasks=tasks,
    process=Process.sequential,
    verbose=True
)

if __name__ == "__main__":
    while True:
        emit_ws_event("Master", "START", "Iniciando Groktopus Floor. Despertando a los 4 agentes (Core)...")
        try:
            result = groktopus_crew.kickoff()
            emit_ws_event("Master", "SUCCESS", "Ciclo completado con éxito. Veredicto asimilado.")
            print("\n[RESULTADO FINAL DEL ENJAMBRE]")
            print(result)
        except Exception as e:
            emit_ws_event("Master", "ERROR", f"Error en el enjambre: {str(e)}")
            print(f"Error: {e}")
            
        emit_ws_event("Master", "SLEEP", "Enjambre en Criosueño. Siguiente análisis en 15 minutos (Límite Diario)...")
        print("\n[INFO] Durmiendo por 15 minutos para no quemar el Límite Diario (TPD) de 500,000 tokens...")
        time.sleep(900) # 15 minutos de pausa entre ciclos globales
