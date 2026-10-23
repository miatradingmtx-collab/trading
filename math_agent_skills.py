import numpy as np
import json
def tool(name=None):
    def decorator(func):
        func.tool_name = name or func.__name__
        func.func = func
        return func
    if callable(name):
        f = name
        name = f.__name__
        return decorator(f)
    return decorator


# 5 Temporalidades Oficiales Institucionales de Mia (Homologadas a la Arquitectura Central)
TEMPORALIDADES_OFICIALES = {
    "1H": {"c_factor": 1.0, "peso_inercia": 1.00, "descripcion": "1H (Intradía Rápido · Microestructura & Sweeps)"},
    "2H": {"c_factor": 1.8, "peso_inercia": 1.25, "descripcion": "2H (Swing Intradía · POC Dinámico - Regla de 3 Top 2)"},
    "3H": {"c_factor": 2.6, "peso_inercia": 1.50, "descripcion": "3H (Overlap Londres-NY · Flujo AMD Institucional)"},
    "4H": {"c_factor": 3.8, "peso_inercia": 1.85, "descripcion": "4H (Macro Intradía · Absorción Interbancaria CME)"},
    "8H": {"c_factor": 6.5, "peso_inercia": 2.40, "descripcion": "8H (Sesión Completa · Campana Institucional Consenso Fondos)"}
}

@tool("Calcular Area de Energia CVOL")
def calc_area_energia_cvol(fuerza_a_json, fuerza_b_json, precios_json, timeframe: str = "2H", activo: str = "EURUSD") -> str:
    """
    Calcula el Área de Energía como CVOL mediante el cálculo integral:
    Área de Energía = ∫ [FuerzaA(x) - FuerzaB(x)] dx + C(t)
    donde C(t) es la constante institucional de inercia indexada estrictamente por las 5 temporalidades
    oficiales que opera Mia: 1H, 2H, 3H, 4H, 8H.
    Cualquier temporalidad ciega (ej. 1m, 15m) es rechazada y homologada al núcleo 2H (Top 2 Regla de 3).
    """
    try:
        tf_input = str(timeframe).upper().strip()
        filtro_bloqueo = None
        if tf_input not in TEMPORALIDADES_OFICIALES:
            filtro_bloqueo = f"Temporalidad '{tf_input}' rechazada (fuera de portafolio/ruido ciego 1m/15m). Homologada forzosamente a 2H (Top 2 R3)."
            tf = "2H"
        else:
            tf = tf_input
            
        cfg = TEMPORALIDADES_OFICIALES[tf]
        c_t = round(float(cfg["c_factor"] * cfg["peso_inercia"]), 4)
        
        fa = np.array(json.loads(fuerza_a_json) if isinstance(fuerza_a_json, str) else fuerza_a_json, dtype=float)
        fb = np.array(json.loads(fuerza_b_json) if isinstance(fuerza_b_json, str) else fuerza_b_json, dtype=float)
        px = np.array(json.loads(precios_json) if isinstance(precios_json, str) else precios_json, dtype=float)
        
        if len(fa) != len(fb) or len(fa) != len(px):
            return json.dumps({"error": "Dimensiones incompatibles entre FuerzaA, FuerzaB y Precios."})
            
        fuerza_neta = fa - fb
        
        trap_func = getattr(np, 'trapezoid', getattr(np, 'trapz', None))
        integral_fuerza = float(trap_func(fuerza_neta, px))
        
        area_energia = float(integral_fuerza + c_t)
        
        delta_p = abs(float(px[-1] - px[0])) if len(px) > 1 and abs(float(px[-1] - px[0])) > 0 else 0.0010
        escala_cvol = 100.0 if "XAU" in activo.upper() else 10000.0
        cvol_equivalente = round(abs(area_energia) / (delta_p * escala_cvol + 1e-6), 2)
        
        regimen = "EXPANSION_ALTA_ENERGIA" if cvol_equivalente >= 1.5 else ("ABSORCION_EQUILIBRADA" if cvol_equivalente >= 0.8 else "COMPRESION_BAJA_ENERGIA")
        
        res = {
            "activo": activo,
            "timeframe": tf,
            "descripcion_timeframe": cfg["descripcion"],
            "constante_C_t": c_t,
            "integral_fuerza_neta": round(integral_fuerza, 4),
            "area_energia": round(area_energia, 4),
            "cvol_equivalente": cvol_equivalente,
            "regimen_cvol": regimen
        }
        if filtro_bloqueo:
            res["filtro_homologacion"] = filtro_bloqueo
        return json.dumps(res)
    except Exception as e:
        return json.dumps({"error": str(e)})

@tool("Calcular Area Bajo Curva")
def calc_area_under_curve(volume_data: str, time_intervals: str) -> str:
    """
    Calcula el área bajo la curva (integral) del volumen inyectado usando NumPy.
    Útil para medir la fuerza real del movimiento institucional.
    Recibe listas en formato string, ej: volume_data="[100, 200, 500]", time_intervals="[1, 2, 3]".
    """
    try:
        y = np.array(json.loads(volume_data))
        x = np.array(json.loads(time_intervals))
        
        if len(x) != len(y):
            return "Error: Las matrices de volumen y tiempo deben tener la misma longitud."
            
        area = np.trapz(y, x)
        return json.dumps({"area_bajo_curva": float(area), "interpretacion": "Fuerza institucional acumulada calculada con éxito."})
    except Exception as e:
        return f"Error matemático: {str(e)}"

@tool("Generar Matriz de Markov")
def markov_transition_matrix(price_states_json: str) -> str:
    """
    Genera una Matriz de Transición Vectorial (Cadenas de Markov) usando NumPy.
    Calcula la probabilidad pura de que el precio pase de un estado a otro (Alcista, Bajista, Consolidación).
    Recibe lista de estados en string, ej: '["Alcista", "Alcista", "Bajista", "Alcista"]'.
    """
    try:
        states = json.loads(price_states_json)
        if not states:
            return "Error: Array de estados vacío."
            
        unique_states = list(set(states))
        state_index = {state: i for i, state in enumerate(unique_states)}
        n = len(unique_states)
        
        # Inicializar matriz de ceros
        transition_matrix = np.zeros((n, n))
        
        # Contar transiciones
        for i in range(len(states) - 1):
            current_state = states[i]
            next_state = states[i + 1]
            transition_matrix[state_index[current_state]][state_index[next_state]] += 1
            
        # Normalizar probabilidades
        row_sums = transition_matrix.sum(axis=1)
        # Evitar división por cero
        with np.errstate(divide='ignore', invalid='ignore'):
            transition_matrix = np.nan_to_num(transition_matrix / row_sums[:, np.newaxis])
            
        result = {
            "estados": unique_states,
            "matriz_transicion": transition_matrix.tolist()
        }
        return json.dumps(result)
    except Exception as e:
        return f"Error en álgebra lineal: {str(e)}"
