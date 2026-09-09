import json
import numpy as np
from crewai.tools import tool

@tool("Calcular Esperanza Matematica")
def calculate_expected_value(win_rate: float, avg_win: float, avg_loss: float) -> str:
    """
    Calcula la Esperanza Matemática de un setup basado en WinRate, Ganancia Promedio y Pérdida Promedio.
    Fórmula: (WinRate * AvgWin) - ((1 - WinRate) * AvgLoss)
    """
    try:
        wr = float(win_rate)
        aw = float(avg_win)
        al = float(avg_loss)
        
        esperanza = (wr * aw) - ((1 - wr) * al)
        return json.dumps({
            "esperanza_matematica": round(esperanza, 4),
            "ventaja_estadistica": "POSITIVA" if esperanza > 0 else "NEGATIVA"
        })
    except Exception as e:
        return f"Error estadístico: {str(e)}"

@tool("Generar Score de Ejecucion Bayesiana")
def generate_execution_score(markov_prob: float, historical_wr: float, sentiment_modifier: float = 1.0) -> str:
    """
    Combina la probabilidad matemática actual (Markov) con el peso histórico (WinRate de Mia_kb)
    para generar un SCORE DE CONSENSO FINAL del 0 al 1.
    Si el score > 0.70, el trade es aprobado.
    """
    try:
        p = float(markov_prob)
        h = float(historical_wr)
        s = float(sentiment_modifier)
        
        # Ponderación Bayesiana simple adaptada
        score = (p * 0.4) + (h * 0.5) + ((s - 1) * 0.1)
        
        # Limitar entre 0 y 1
        score = max(0.0, min(1.0, score))
        
        return json.dumps({
            "consenso_final_score": round(score, 4),
            "aprobado": score >= 0.70,
            "umbral_requerido": 0.70
        })
    except Exception as e:
        return f"Error en inferencia: {str(e)}"
