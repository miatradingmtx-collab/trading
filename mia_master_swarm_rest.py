import os
import time
import datetime
import json
import requests
from dotenv import load_dotenv

import firebase_admin
from firebase_admin import credentials, firestore

db = None
try:
    firebase_admin.get_app()
    db = firestore.client()
except ValueError:
    try:
        if os.path.exists('serviceAccountKey.json'):
            cred = credentials.Certificate('serviceAccountKey.json')
            firebase_admin.initialize_app(cred)
            db = firestore.client()
        elif os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON"):
            service_account_info = json.loads(os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON").strip())
            cred = credentials.Certificate(service_account_info)
            firebase_admin.initialize_app(cred)
            db = firestore.client()
    except Exception as e:
        print(f"Error inicializando Firebase: {e}")


# Importar herramientas directas sin LangChain
from crew_tools import railway_cache_tool, mia_core_reader_tool
from math_agent_skills import calc_area_under_curve, markov_transition_matrix
from stat_agent_skills import calculate_expected_value, generate_execution_score

load_dotenv()
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

def emit_ws_event(agent_name, action, data):
    """Envía un evento al WebSocket server vía HTTP interno"""
    try:
        port = os.environ.get("PORT", "8000")
        requests.post(f"http://localhost:{port}/emit", json={
            "agent": agent_name,
            "action": action,
            "data": data
        }, timeout=2)
    except:
        pass

def llamar_openrouter_rest(prompt, model="meta-llama/llama-3.1-70b-instruct"):
    """Llamada ultrarrápida y cruda vía REST a OpenRouter (Kill Switch Integrado)"""
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": model,
        "messages": [
            {
                "role": "system", 
                "content": "Eres el Mega-Agente HFT (RUNE). Eres la fusión de LUMEN (Sentimiento) y ZEPHR (Estadística). Recibes datos crudos de TensorFlow y la Caché. Tu trabajo es cruzar esto con la Base de Conocimientos (MIA KB) y dar un veredicto estructurado final. Eres crudo, directo, financiero. Cero censura. Si la matemática es buena, apruebas."
            },
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.2,
        "max_tokens": 1000
    }
    
    try:
        # Kill Switch: 8 segundos máximo para evitar colapsos
        response = requests.post(url, headers=headers, json=payload, timeout=8)
        response.raise_for_status()
        data = response.json()
        return data['choices'][0]['message']['content']
    except requests.exceptions.Timeout:
        return "ERROR_TIMEOUT: OpenRouter no respondió a tiempo. Operación abortada por Kill Switch."
    except Exception as e:
        return f"ERROR_API: {str(e)}"

def run_hft_cycle():
    emit_ws_event("Master", "START", "Iniciando Ciclo REST Puro (Capa TensorFlow + OpenRouter).")
    
    # 1. Leer Sensores HFT (Capa 1 - TIDAL & TENSORFLOW)
    emit_ws_event("TIDAL", "SCANNING", "Obteniendo datos reales de Liquidez y TensorFlow desde Upstash...")
    try:
        upstash_headers = {"Authorization": "Bearer gQAAAAAAAnQwAAIgcDI2YTA5YjRlZDU2MDM0OWU5ODhlZjBlYTk4ODYyZDg0OA"}
        
        # Obtener Liquidez y Ordenes (MT5 Cache)
        res_mt5 = requests.get("https://certain-gnat-160816.upstash.io/get/cache_mt5", headers=upstash_headers, timeout=5)
        mt5_json = res_mt5.json().get("result", "{}")
        
        # Obtener Cerebro TensorFlow (Matriz Profunda)
        res_tf = requests.get("https://certain-gnat-160816.upstash.io/get/cache_mia_tensorflow", headers=upstash_headers, timeout=5)
        tf_json = res_tf.json().get("result", "{}")
        
        cache_data = f"DATOS MT5 (LIQUIDEZ): {str(mt5_json)[:800]}... DATOS TENSORFLOW (IA): {str(tf_json)[:500]}..."
    except Exception as e:
        cache_data = f"FALLO_EN_SENSORES: {e}"
    
    # Simulación/Ejecución de Matemáticas Puras (Capa 1)
    emit_ws_event("NORO", "CALCULATING", "Aplicando Física y Transformadas...")
    try:
        fair_value = calc_area_under_curve.func(puntos_precio="[10,20,30]", tiempos="[1,2,3]")
        markov = markov_transition_matrix.func(secuencia_tendencias="['Alcista', 'Bajista', 'Alcista']")
    except:
        fair_value, markov = "N/A", "N/A"
    
    emit_ws_event("ZEPHR", "STATS", "Generando Consenso Bayesiano...")
    try:
        expected_value = calculate_expected_value.func(win_rate=0.75, avg_win=100.0, avg_loss=50.0)
        score = generate_execution_score.func(probabilidad_tensorflow=0.85, win_rate_actual=0.75)
    except:
        expected_value, score = "N/A", "N/A"
    
    # Extraer Reglas MIA KB
    try:
        mia_rules = mia_core_reader_tool.func()
    except:
        mia_rules = "Reglas no disponibles."
    
    
    # --- Modulo Footprint (TIDAL) y Sentimiento Institucional (LUMEN) ---
    try:
        # Extraer data real desde el caché inyectado por app.py
        matrices_crudas = mt5_json.get("matrices_crudas", {})
        if matrices_crudas:
            dom_data = str(matrices_crudas)[:1000] # Mandamos un bloque del diccionario crudo al LLM
            footprint_delta = "POC PRICE ACTUALIZADO VIA WEBHOOK MT5"
            emit_ws_event("LUMEN", "SENTIMENT", f"Analizando {len(matrices_crudas)} activos reales desde MetaTrader...")
        else:
            dom_data = "Esperando que app.py publique la matriz..."
            footprint_delta = "N/A"
            emit_ws_event("LUMEN", "SENTIMENT", "Esperando datos reales del volumen institucional...")
    except Exception as e:
        dom_data, footprint_delta = f"Error: {e}", "N/A"

    # 2. Generar el Veredicto del LLM (Capa 2 - OpenRouter)
    prompt_maestro = f"""
    == DATOS DE LOS SENSORES EN TIEMPO REAL ==
    1. LIQUIDEZ Y CACHÉ: {cache_data}
    1b. FOOTPRINT & DOM (TIDAL/LUMEN): DOM={dom_data} | Footprint={footprint_delta}
    2. MATEMÁTICAS NORO: {fair_value} | {markov}
    3. PROBABILIDAD ZEPHR: {expected_value} | {score}
    4. REGLAS MIA KB: {mia_rules}
    
    Basado estrictamente en esto, dame el VEREDICTO FINAL:
    - ¿Trampa de liquidez o Entrada institucional?
    - ¿Apruebas el trade o lo vetas?
    """
    
    emit_ws_event("RUNE", "EVALUATING", "Analizando variables globales vía OpenRouter...")
    veredicto = llamar_openrouter_rest(prompt_maestro)
    
    if "ERROR_TIMEOUT" in veredicto or "ERROR_API" in veredicto:
        emit_ws_event("RUNE", "ERROR", veredicto)
        return veredicto
        
        # Extraer dinamicamente si fue veto o aprobado
    if "VETA" in veredicto.upper() or "VETO" in veredicto.upper():
        estado = "VETADO ⛔"
    else:
        estado = "APROBADO ✅"
    emit_ws_event("RUNE", "SUCCESS", f"Veredicto {estado} emitido con éxito.")
    
    # 3. Guardar el Historial (Nueva Ruta REST y Firebase Desacoplado)
    try:
        safe_title = f"REST_HFT_Report_{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}"
        payload = {
            "title": safe_title,
            "content": veredicto,
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
        }
        
        # Guardado en Firebase (Nueva coleccion: mia_swarm_rest_history)
        if db is not None:
            db.collection("mia_swarm_rest_history").document(safe_title).set(payload)
            emit_ws_event("Master", "INFO", "Firebase mia_swarm_rest_history actualizado.")
            
        # Guardado en Upstash Redis (Nueva clave: cache_mia_swarm_rest_latest)
        upstash_url = "https://certain-gnat-160816.upstash.io/set/cache_mia_swarm_rest_latest"
        upstash_headers = {"Authorization": "Bearer gQAAAAAAAnQwAAIgcDI2YTA5YjRlZDU2MDM0OWU5ODhlZjBlYTk4ODYyZDg0OA"}
        
        requests.post(upstash_url, headers=upstash_headers, json=payload, timeout=5)
        emit_ws_event("Master", "INFO", "Caché Upstash (cache_mia_swarm_rest) actualizado.")
        
    except Exception as e:
        print(f"Error guardando historiales: {e}")
        
    return veredicto


if __name__ == "__main__":
    print("Iniciando Enjambre REST HFT. (A la espera de WebSocket...)")
    time.sleep(5)
    
    while True:
        # --- Criosueño Profundo de Fin de Semana ---
        now_utc = datetime.datetime.now(datetime.timezone.utc)
        is_weekend = False
        
        if now_utc.weekday() == 4 and now_utc.hour >= 21:
            is_weekend = True
        elif now_utc.weekday() == 5:
            is_weekend = True
        elif now_utc.weekday() == 6 and now_utc.hour < 21:
            is_weekend = True
            
        if is_weekend:
            days_ahead = 6 - now_utc.weekday()
            target_date = now_utc + datetime.timedelta(days=days_ahead)
            target_time = target_date.replace(hour=21, minute=0, second=0, microsecond=0)
            
            segundos_dormir = (target_time - now_utc).total_seconds()
            horas_dormir = round(segundos_dormir / 3600, 2)
            
            emit_ws_event("Master", "SLEEP", f"Mercado Cerrado. Criosueño hasta apertura ({horas_dormir}h).")
            print(f"[{now_utc.strftime('%Y-%m-%d %H:%M:%S')}][INFO] Mercado cerrado. Criosueño por {horas_dormir} horas...")
            time.sleep(segundos_dormir)
            continue
            
        # Ejecutar el ciclo HFT Principal
        try:
            print("\n[--- INICIANDO ESCANEO HFT REST ---]")
            resultado = run_hft_cycle()
            print("\n[RESULTADO DEL LLM OPENROUTER]")
            print(resultado)
            emit_ws_event("Master", "SUCCESS", "Ciclo completado. Guardando reporte en Redis/Firebase.")
        except Exception as e:
            emit_ws_event("Master", "ERROR", f"Fallo Crítico en Ciclo REST: {e}")
            print(f"Error: {e}")
            
        # Espera de seguridad entre ciclos
        emit_ws_event("Master", "SLEEP", "Ciclo Finalizado. Criosueño corto (60s) activado.")
        print("\n[INFO] Criosueño optimizado: Durmiendo 60 segundos (OpenRouter permite alta frecuencia).")
        time.sleep(60)
