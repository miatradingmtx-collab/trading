import numpy as np
import json
from crewai.tools import tool

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
