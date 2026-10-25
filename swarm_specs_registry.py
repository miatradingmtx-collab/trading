#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
SWARM SPECS REGISTRY: CARGADOR DECLARATIVO DE ESPECIFICACIONES MARKDOWN (.MD)
================================================================================
Gestiona la lectura en memoria RAM de las 9 especificaciones canónicas de los Herds.
Implementa @lru_cache para garantizar CERO latencia de disco (0 I/O) durante el
bucle de escaneo HFT en producción (Railway Cloud / Local).
================================================================================
"""

import os
from functools import lru_cache
from typing import Dict, Optional

# Directorio oficial de especificaciones
SPECS_DIR = os.path.join(os.path.dirname(__file__), "specs", "herds")

HERD_SPEC_MAP = {
    "HERD_1_TIDAL": "HERD_1_TIDAL.md",
    "HERD_2_NORO": "HERD_2_NORO.md",
    "HERD_3_ZEPHR": "HERD_3_ZEPHR.md",
    "HERD_4_LUMEN": "HERD_4_LUMEN.md",
    "HERD_5_RUNE": "HERD_5_RUNE.md",
    "HERD_6_TENSORFLOW": "HERD_6_TENSORFLOW.md",
    "HERD_7_ATLAS": "HERD_7_ATLAS.md",
    "MASTER_ORCHESTRATOR": "MASTER_ORCHESTRATOR.md",
    "CBR_POST_MORTEM_QUANT": "CBR_POST_MORTEM_QUANT.md"
}

@lru_cache(maxsize=16)
def get_herd_specification(herd_key: str) -> str:
    """
    Retorna el contenido íntegro de la especificación .md del Herd.
    Almacenado en RAM con lru_cache para desempeño sub-milisegundo.
    """
    filename = HERD_SPEC_MAP.get(herd_key)
    if not filename:
        return ""
    filepath = os.path.join(SPECS_DIR, filename)
    if not os.path.exists(filepath):
        # Fallback a raíz si no está en subdirectorio
        filepath = os.path.join(os.path.dirname(__file__), filename)
        if not os.path.exists(filepath):
            return ""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read().strip()
    except Exception as e:
        print(f"⚠️ [SPECS REGISTRY WARN] Error leyendo {filename}: {e}")
        return ""

@lru_cache(maxsize=1)
def build_swarm_system_grounding() -> str:
    """
    Construye el System Grounding conciso para Llama 3.3 70B REST extrayendo
    las misiones canónicas declaradas en los archivos .md.
    """
    h1 = get_herd_specification("HERD_1_TIDAL")
    h2 = get_herd_specification("HERD_2_NORO")
    h3 = get_herd_specification("HERD_3_ZEPHR")
    h4 = get_herd_specification("HERD_4_LUMEN")
    h5 = get_herd_specification("HERD_5_RUNE")
    h6 = get_herd_specification("HERD_6_TENSORFLOW")
    h7 = get_herd_specification("HERD_7_ATLAS")
    master = get_herd_specification("MASTER_ORCHESTRATOR")

    def _extract_summary(spec_text: str, default: str) -> str:
        if not spec_text:
            return default
        # Tomar las primeras líneas de misión técnica
        lines = [l.strip() for l in spec_text.splitlines() if l.strip() and not l.startswith("#")]
        return lines[0] if lines else default

    return (
        "Eres el Motor de Deliberación Inter-Agente Herds de MIA Core (Malla Desacoplada de 7 Herds Especializados + Master Gatekeeper).\n"
        f"• HERD 1 (TIDAL): {_extract_summary(h1, 'Macro Trend, Killzones y divergencia SMT con DXY.')}\n"
        f"• HERD 2 (NORO): {_extract_summary(h2, 'Matemáticas cuantitativas, POC dinámico, Área CVOL y Cadenas de Markov en 1H-8H.')}\n"
        f"• HERD 3 (ZEPHR): {_extract_summary(h3, 'Probabilidad bayesiana, Expected Value (EV en R) y asimetría de pérdidas.')}\n"
        f"• HERD 4 (LUMEN): {_extract_summary(h4, 'Smart Money Concepts, Order Blocks LuxAlgo y ciclos AMD con barridos macro.')}\n"
        f"• HERD 5 (RUNE): {_extract_summary(h5, 'Gestión de riesgo defensivo institucional v2, cascada de 4 fases y límite canasta USD.')}\n"
        f"• HERD 6 (TENSORFLOW): {_extract_summary(h6, 'Inferencia de red neuronal profunda continua (22D sináptico).')}\n"
        f"• HERD 7 (ATLAS): {_extract_summary(h7, 'Microestructura institucional DOM CME/OANDA, CVD Delta direccional y servidor MCP.')}\n"
        f"• MASTER: {_extract_summary(master, 'Veredicto de Quórum Calificado (Score >= 0.70 APROBADO o VETADO).')}\n"
        "El debate es directo, técnico, sin rodeos y sin repetir texto."
    )

def clear_specs_cache():
    """Limpia la caché de memoria si se modificaron archivos .md en caliente."""
    get_herd_specification.cache_clear()
    build_swarm_system_grounding.cache_clear()
    print("🔄 [SPECS REGISTRY] Memoria caché de especificaciones .md invalidada.")
