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
        # Frenamos el LLM 20s para no hacer saltar el Error 429 de límite de tokens (5 RPM en Gemini free)
        time.sleep(20) 
        
        # CrewAI >= 0.x envia diferentes tipos de objetos al callback (AgentStep, ToolResult, etc.)
        # Hacemos str(output) para no chocar con atributos deprecados como .raw
        texto = str(output)
        emit_ws_event(agent_name, "OUTPUT", texto[:150] + "...")
    return callback

from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI

# ── FAILOVER DINÁMICO (Tolerancia a fallos 24/7) ──
# Motor Principal: Groq Compound (Mejor calidad)
primary_llm = ChatGroq(
    model_name="groq/compound",
    groq_api_key=os.environ.get("GROQ_API_KEY"),
    temperature=0.2
)

# Respaldo 1: Groq Compound Mini (Rápido, menos pesado)
fallback_1 = ChatGroq(
    model_name="groq/compound-mini",
    groq_api_key=os.environ.get("GROQ_API_KEY"),
    temperature=0.2
)

# Respaldo 2: Qwen 3.6 (Otra cuota separada)
fallback_2 = ChatGroq(
    model_name="qwen/qwen3.6-27b",
    groq_api_key=os.environ.get("GROQ_API_KEY"),
    temperature=0.2
)

# Respaldo 3: Allam (Otra cuota separada)
fallback_3 = ChatGroq(
    model_name="allam-2-7b",
    groq_api_key=os.environ.get("GROQ_API_KEY"),
    temperature=0.2
)

# Respaldo 4: Google Gemini (Emergencia final, 20 peticiones)
fallback_4 = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    google_api_key=os.environ.get("GOOGLE_API_KEY"),
    temperature=0.2
)

# Fusionar todos los motores en un cerebro indestructible
my_llm = primary_llm.with_fallbacks([fallback_1, fallback_2, fallback_3, fallback_4])

# ── 1. TIDAL (Liquidez) ──
tidal = Agent(
    role="TIDAL - Order Book Scanner",
    goal="Leer los volúmenes institucionales y reportar bloqueos.",
    backstory="Analizas los deltas de volumen en milisegundos buscando trampas institucionales.",
    verbose=True,
    memory=False,
    allow_delegation=False,
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
    allow_delegation=False,
    llm=my_llm,
    step_callback=create_callback("NORO")
)

# ── 4. ZEPHR (Estadística y Esperanza) ──
zephr = Agent(
    role='Liquidity Mapper & Stats (ZEPHR)',
    goal='Calcular la esperanza matemática y el score probabilístico.',
    backstory='Usas herramientas bayesianas para sacar un score final (Consenso > 0.70).',
    tools=[calculate_expected_value, generate_execution_score],
    allow_delegation=False,
    llm=my_llm,
    step_callback=create_callback("ZEPHR")
)

# ── 5. OKAPI (Cobertura) (APAGADO TEMPORALMENTE - Límite de Tokens Groq) ──
# okapi = Agent(...)

# ── 6. RUNE (Veto de Riesgo) ──
rune = Agent(
    role='El Oráculo Final (RUNE)',
    goal='Validar todos los puntajes y dar el veredicto final (APROBADO/VETADO).',
    backstory='Eres la última línea de defensa. Recibes la data de los otros agentes. Si ves que el indicador LUX ALGO (order_block_zona) o Liquidez (alineamiento_liquidez) está presente, le das prioridad máxima absoluta por su alta probabilidad. Luego escribes el resultado en Obsidian.',
    tools=[obsidian_writer_tool],
    allow_delegation=False,
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
    import datetime
    while True:
        # --- Criosueño de Fin de Semana (Ahorro de Tokens) ---
        now_utc = datetime.datetime.utcnow()
        is_weekend = False
        # Viernes después de las 21:00 UTC
        if now_utc.weekday() == 4 and now_utc.hour >= 21:
            is_weekend = True
        # Sábado todo el día
        elif now_utc.weekday() == 5:
            is_weekend = True
        # Domingo antes de las 21:00 UTC
        elif now_utc.weekday() == 6 and now_utc.hour < 21:
            is_weekend = True
            
        if is_weekend:
            emit_ws_event("Master", "SLEEP", "Mercado Cerrado. Enjambre en Criosueño (Ahorro de tokens). Revisando en 1 hora...")
            print(f"[{now_utc.strftime('%Y-%m-%d %H:%M:%S')}][INFO] Mercado Forex cerrado. Durmiendo 1 hora para no desperdiciar tokens...")
            time.sleep(3600)
            continue
            
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
