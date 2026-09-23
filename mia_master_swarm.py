import os
import json
import time
import requests
import sys
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process

from crew_tools import railway_cache_tool, obsidian_writer_tool, mia_core_reader_tool
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
        texto = str(output)
        emit_ws_event(agent_name, "OUTPUT", texto[:150] + "...")
        
        import time
        print(f"[{agent_name}] Pausa anti-429 (20s)...")
        time.sleep(20)
    return callback

from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI

# 🚀 MULTI-PROVIDER LOAD BALANCING (Bypass de TPM Groq) 🚀
# El TPM de Groq 70B Free es muy bajo (6,000 TPM). NORO y RUNE lo devoran.
# Solución: Distribuimos la carga pesada hacia Google Gemini (1 Millón TPM gratis) y Groq 8B (30k TPM gratis).
from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI
import os

# 1. Groq Principal (Llama 3.3 70B - Inteligencia alta)
llm_70b = ChatGroq(
    model_name="llama-3.3-70b-versatile",
    groq_api_key=os.environ.get("GROQ_API_KEY"),
    temperature=0.2,
    max_tokens=600
)

# 2. Groq Secundario (Llama 3.1 8B - Intermedio con alto rate limit)
llm_8b = ChatGroq(
    model_name="llama3-8b-8192",
    groq_api_key=os.environ.get("GROQ_API_KEY"),
    temperature=0.2,
    max_tokens=600
)

# 3. Google Gemini (Respaldo absoluto contra 429 - 1 Millón TPM gratis)
llm_gemini = ChatGoogleGenerativeAI(
    model="gemini-1.5-flash",
    google_api_key=os.environ.get("GOOGLE_API_KEY"),
    temperature=0.2
)

# ASIGNACIÓN INTELIGENTE (ANTI-429) CON FALLBACKS AUTOMÁTICOS
# TIDAL: Escanea mucha data. Usamos 8B, si falla pasa a Gemini.
llm_para_tidal = llm_8b.with_fallbacks([llm_gemini])

# NORO: Matemática. Usamos 70B, si falla pasa a Gemini.
llm_para_noro = llm_70b.with_fallbacks([llm_gemini])

# ZEPHR: Análisis técnico. Lo mandamos a Gemini directo para balancear la carga.
llm_para_zephr = llm_gemini

# RUNE: Juez Maestro. Usamos 70B, si falla pasa a Gemini.
llm_para_rune = llm_70b.with_fallbacks([llm_gemini])
# ── 1. TIDAL (Liquidez) ──
tidal = Agent(
    role="TIDAL - Order Book Scanner",
    goal="Leer los volúmenes institucionales y reportar bloqueos.",
    backstory="Analizas los deltas de volumen en milisegundos buscando trampas institucionales.",
    verbose=True,
    memory=False,
    allow_delegation=False,
    max_rpm=3,
    llm=llm_para_tidal,
    step_callback=create_callback("TIDAL"),
    tools=[railway_cache_tool]
)

llm_para_lumen = llm_8b
# 🟢 2. LUMEN (Sentimiento Institucional) 🟢
lumen = Agent(
    role='LUMEN - Sentimiento y Liquidez',
    goal='Evaluar las órdenes abiertas y liquidez.',
    backstory='Especialista en sentimiento institucional.',
    verbose=True,
    memory=False,
    allow_delegation=False,
    max_rpm=3,
    llm=llm_para_lumen,
    step_callback=create_callback('LUMEN'),
    tools=[railway_cache_tool]
)

# ── 3. NORO (Matemáticas Duras) ──
noro = Agent(
    role='Fair Value Math (NORO)',
    goal='Calcular integrales y matrices de markov.',
    backstory='Eres un quant matemático. Usas las herramientas de Área Bajo la Curva y Matrices de Markov.',
    tools=[calc_area_under_curve, markov_transition_matrix],
    allow_delegation=False,
    max_rpm=3,
    llm=llm_para_noro,
    step_callback=create_callback("NORO")
)

# ── 4. ZEPHR (Estadística y Esperanza) ──
zephr = Agent(
    role='Liquidity Mapper & Stats (ZEPHR)',
    goal='Calcular la esperanza matemática y el score probabilístico.',
    backstory='Usas herramientas bayesianas para sacar un score final (Consenso > 0.70).',
    tools=[calculate_expected_value, generate_execution_score],
    allow_delegation=False,
    max_rpm=3,
    llm=llm_para_zephr,
    step_callback=create_callback("ZEPHR")
)

# ── 5. OKAPI (Cobertura) (APAGADO TEMPORALMENTE - Límite de Tokens Groq) ──
# okapi = Agent(...)

# ── 6. RUNE (Veto de Riesgo) ──
rune = Agent(
    role='El Oráculo Final (RUNE)',
    goal='Validar todos los puntajes y dar el veredicto final (APROBADO/VETADO).',
    backstory='Eres la última línea de defensa. Recibes la data de los otros agentes. Si ves que el indicador LUX ALGO (order_block_zona) o Liquidez (alineamiento_liquidez) está presente, le das prioridad máxima absoluta por su alta probabilidad. Luego escribes el resultado en Obsidian.',
    tools=[mia_core_reader_tool, obsidian_writer_tool],
    allow_delegation=False,
    max_rpm=3,
    llm=llm_para_rune,
    step_callback=create_callback("RUNE")
)

# ── 7. VESKA (Ejecución) (APAGADO TEMPORALMENTE - Límite de Tokens Groq) ──
# veska = Agent(...)

# ── 8. MARIN (Liquidación) (APAGADO TEMPORALMENTE - Funciones delegadas a RUNE) ──
# marin = Agent(...)

# ── TAREAS ──
tasks = [
    Task(description='Obtén los KPIs actuales desde railway_cache_tool.', expected_output='Resumen de liquidez.', agent=tidal),
    Task(description='Analiza liquidez y sentimiento de mercado.', expected_output='Diagnóstico de sentimiento direccional institucional.', agent=lumen),
    Task(description='Usa calc_area_under_curve con "[10,20,30]", "[1,2,3]". Y genera una matriz de markov con \'["Alcista", "Bajista", "Alcista"]\'.', expected_output='Fair Value y Matrices.', agent=noro),
    Task(description='Usa calculate_expected_value (wr=0.75, avg_win=100, avg_loss=50). Y genera score de ejecucion (prob=0.68, wr=0.75).', expected_output='Score de consenso.', agent=zephr),
    Task(description='1. Usa mia_core_reader_tool para leer la Base de Conocimiento (Reglas de Riesgo y ML).\n2. Revisa el output estadístico. Si el Score es mayor a 0.70 aprueba el trade, si no VETADO.\n3. Usa obsidian_writer_tool para guardar el dictamen.', expected_output='Confirmación de registro (APROBADO/VETADO guardado).', agent=rune)
]

# ── CREW MASTER ──
antopus_crew = Crew(
    agents=[tidal, lumen, noro, zephr, rune],
    tasks=tasks,
    process=Process.sequential,
    verbose=True
)

if __name__ == "__main__":
    import time
    print("Esperando 10s para que inicie el WebSocket...")
    time.sleep(10)
    import datetime
    while True:
        # --- Criosueño Profundo de Fin de Semana (Cierre a Apertura) ---
        now_utc = datetime.datetime.now(datetime.timezone.utc)
        is_weekend = False
        
        # Viernes después de las 21:00 UTC (17:00 NY - Cierre)
        if now_utc.weekday() == 4 and now_utc.hour >= 21:
            is_weekend = True
        # Sábado todo el día
        elif now_utc.weekday() == 5:
            is_weekend = True
        # Domingo antes de las 21:00 UTC (17:00 NY - Apertura)
        elif now_utc.weekday() == 6 and now_utc.hour < 21:
            is_weekend = True
            
        if is_weekend:
            # Calcular exactamente los segundos hasta el domingo a las 21:00 UTC
            days_ahead = 6 - now_utc.weekday()
            target_date = now_utc + datetime.timedelta(days=days_ahead)
            target_time = target_date.replace(hour=21, minute=0, second=0, microsecond=0)
            
            segundos_dormir = (target_time - now_utc).total_seconds()
            horas_dormir = round(segundos_dormir / 3600, 2)
            
            emit_ws_event("Master", "SLEEP", f"Mercado Forex Cerrado. Criosueño profundo hasta apertura. ({horas_dormir} hrs restantes)")
            print(f"[{now_utc.strftime('%Y-%m-%d %H:%M:%S')}][INFO] Mercado Forex cerrado. Entrando en Criosueño profundo por {horas_dormir} horas hasta la apertura asiática...")
            time.sleep(segundos_dormir)
            continue
            
        emit_ws_event("Master", "START", "Iniciando Antopus Floor. Despertando a los 4 agentes (Core)...")
        try:
            result = antopus_crew.kickoff()
            emit_ws_event("Master", "SUCCESS", "Ciclo completado con éxito. Veredicto asimilado.")
            print("\n[RESULTADO FINAL DEL ENJAMBRE]")
            print(result)
        except Exception as e:
            emit_ws_event("Master", "ERROR", f"Error en el enjambre: {str(e)}")
            print(f"Error: {e}")
            
        emit_ws_event("Master", "SLEEP", "Enjambre en Criosueño. Siguiente analisis en 30 minutos (Límite Diario)...")
        print("\n[INFO] Durmiendo por 30 minutos para no quemar el Límite Diario (TPD) de 500,000 tokens...")
        time.sleep(1800) # 30 minutos de pausa entre ciclos globales
