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
    try:
        requests.post("http://localhost:8000/emit", json={
            "agent": agent_name,
            "action": action,
            "data": data
        }, timeout=2)
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

# Nuevo formato requerido por litellm en CrewAI >= 0.x
llm_model = "groq/openai/gpt-oss-120b"

# ── 1. TIDAL (Liquidez) ──
tidal = Agent(
    role='Order Book Scanner (TIDAL)',
    goal='Extraer datos de liquidez desde la Caché de Railway RAM.',
    backstory='Lees la liquidez profunda. NUNCA tocas Firebase, solo usas railway_cache_tool.',
    tools=[railway_cache_tool],
    llm=llm_model,
    step_callback=create_callback("TIDAL")
)

# ── 2. LUMEN (Sentimiento) ──
lumen = Agent(
    role='Sentiment Engine (LUMEN)',
    goal='Leer el contexto macro y sentimiento fundamental.',
    backstory='Analizas si el miedo institucional es alto basado en los datos de la cache.',
    tools=[railway_cache_tool],
    llm=llm_model,
    step_callback=create_callback("LUMEN")
)

# ── 3. NORO (Matemáticas Duras) ──
noro = Agent(
    role='Fair Value Math (NORO)',
    goal='Calcular integrales y matrices de markov.',
    backstory='Eres un quant matemático. Usas las herramientas de Área Bajo la Curva y Matrices de Markov.',
    tools=[calc_area_under_curve, markov_transition_matrix],
    llm=llm_model,
    step_callback=create_callback("NORO")
)

# ── 4. ZEPHR (Estadística y Esperanza) ──
zephr = Agent(
    role='Liquidity Mapper & Stats (ZEPHR)',
    goal='Calcular la esperanza matemática y el score probabilístico.',
    backstory='Usas herramientas bayesianas para sacar un score final (Consenso > 0.70).',
    tools=[calculate_expected_value, generate_execution_score],
    llm=llm_model,
    step_callback=create_callback("ZEPHR")
)

# ── 5. OKAPI (Cobertura) ──
okapi = Agent(
    role='Hedge Exposure (OKAPI)',
    goal='Evaluar el riesgo de exposición beta.',
    backstory='Decides si la cuenta tiene demasiada exposición direccional.',
    tools=[],
    llm=llm_model,
    step_callback=create_callback("OKAPI")
)

# ── 6. RUNE (Veto de Riesgo) ──
rune = Agent(
    role='Risk Control (RUNE)',
    goal='Aprobar o rechazar (Veto) el trade basado en el Consenso de ZEPHR.',
    backstory='Tu único trabajo es decir NO si el score es menor a 0.70. Eres la muralla de riesgo.',
    tools=[],
    llm=llm_model,
    step_callback=create_callback("RUNE")
)

# ── 7. VESKA (Ejecución) ──
veska = Agent(
    role='Execution Specialist (VESKA)',
    goal='Dar la orden final al mercado.',
    backstory='Eres el francotirador. Solo ejecutas si RUNE y Master aprueban. Nunca promedias.',
    tools=[],
    llm=llm_model,
    step_callback=create_callback("VESKA")
)

# ── 8. MARIN (Liquidación) ──
marin = Agent(
    role='Settlement Desk (MARIN)',
    goal='Guardar el resultado en la bitácora.',
    backstory='Una vez ejecutado, cierras el ticket con obsidian_writer_tool.',
    tools=[obsidian_writer_tool],
    llm=llm_model,
    step_callback=create_callback("MARIN")
)

# ── TAREAS ──
tasks = [
    Task(description='Obtén los KPIs actuales desde railway_cache_tool.', expected_output='Resumen de liquidez.', agent=tidal),
    Task(description='Revisa si hay volatilidad macro.', expected_output='Sentimiento del mercado.', agent=lumen),
    Task(description='Usa calc_area_under_curve con "[10,20,30]", "[1,2,3]". Y genera una matriz de markov con \'["Alcista", "Bajista", "Alcista"]\'.', expected_output='Fair Value y Matrices.', agent=noro),
    Task(description='Usa calculate_expected_value (wr=0.75, avg_win=100, avg_loss=50). Y genera score de ejecucion (prob=0.68, wr=0.75).', expected_output='Score de consenso.', agent=zephr),
    Task(description='Analiza el score y decide si el riesgo de exposición cruzada es aceptable.', expected_output='Aprobación de cobertura.', agent=okapi),
    Task(description='Revisa el output estadístico. Si el Score es mayor a 0.70, aprueba el trade.', expected_output='Dictamen de Riesgo (APROBADO/VETADO).', agent=rune),
    Task(description='Redacta el ticket de ejecución del trade.', expected_output='Detalle de fill de mercado.', agent=veska),
    Task(description='Escribe el reporte final en Obsidian.', expected_output='Confirmación de registro.', agent=marin)
]

# ── CREW MASTER ──
groktopus_crew = Crew(
    agents=[tidal, lumen, noro, zephr, okapi, rune, veska, marin],
    tasks=tasks,
    process=Process.sequential,
    verbose=True
)

if __name__ == "__main__":
    while True:
        emit_ws_event("Master", "START", "Iniciando Groktopus Floor. Despertando a los 8 agentes...")
        try:
            result = groktopus_crew.kickoff()
            emit_ws_event("Master", "SUCCESS", "Ciclo completado con éxito. Veredicto asimilado.")
            print("\n[RESULTADO FINAL DEL ENJAMBRE]")
            print(result)
        except Exception as e:
            emit_ws_event("Master", "ERROR", f"Error en el enjambre: {str(e)}")
            print(f"Error: {e}")
            
        emit_ws_event("Master", "SLEEP", "Enjambre en Criosueño. Siguiente análisis en 15 minutos...")
        print("\n[INFO] Durmiendo por 15 minutos para respetar el Rate Limit de Groq y esperar velas de mercado...")
        time.sleep(900) # 15 minutos de pausa entre ciclos globales
