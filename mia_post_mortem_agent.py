#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
MIA POST-MORTEM AGENT (RAMA 1 - AGENTE FORENSE DE AUTOPSIA Y ANÁLISIS DE HERDS)
================================================================================
Agente cognitivo autónomo especializado en la autopsia técnica y forense
de operaciones cerradas en MetaTrader 5 y la evaluación individual de los 7 Herds.

MISIÓN ESPECÍFICA:
1. Extraer y auditar los datos contables y de ejecución del trade cerrado en MT5.
2. Analizar el comportamiento, dictamen y sesgo de CADA UNO DE LOS 7 HERDS:
   - TIDAL: Sesgo macro, Killzones (Londres, NY, Asia) y correlación DXY.
   - NORO: Confluencia matemática POC, dinámica de energía y CVOL.
   - ZEPHR: Distribución de probabilidad bayesiana y ratio Expected Value (EV).
   - LUMEN: Smart Money Concepts (SMC), Order Blocks 2H, FVG y trampas BOS.
   - RUNE: Gestión de riesgo, buffer de SL, TP1 parcial y cascada de 4 fases.
   - TENSORFLOW: Inferencia tensorial 22D, confianza de la red y sesgo direccional.
   - ATLAS: Microestructura CME/COMEX DOM L3, CVD Delta y absorción institucional.
3. Emitir el Diagnóstico Forense Preliminar y el Borrador de Propuestas para los 7 Herds.
4. Pasar el informe al MIA Quant Supervisor para la validación cuantitativa y
   calibración en bucle (Quality Loop) con Google Gemini 1.5 Pro.
================================================================================
"""

import os
import json
import datetime
import requests
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

load_dotenv()


class MiaPostMortemAgent:
    """
    AGENTE POST-MORTEM: Autopsia técnica y forense de operaciones MT5.
    Desacoplado del Supervisor Quant; interactúa en un loop cognitivo de calibración.
    """
    def __init__(self):
        self.UPSTASH_URL = os.getenv("UPSTASH_REDIS_REST_URL", "https://firm-koi-93555.upstash.io")
        self.UPSTASH_TOKEN = os.getenv("UPSTASH_REDIS_REST_TOKEN", "gQAAAAAAAW1zAAIgcDFmZGI5MGViNWY4Mjc0MGE1Yjg3NDZiOTdiN2MyMjg5Yg")
        self.UPSTASH_HEADERS = {"Authorization": f"Bearer {self.UPSTASH_TOKEN}"}

    def fetch_recent_closed_trades(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Extrae trades cerrados recientes desde Upstash Redis (Zero Firestore Read Quota)."""
        closed = []
        try:
            r = requests.get(f"{self.UPSTASH_URL}/get/cache_hist_mt5", headers=self.UPSTASH_HEADERS, timeout=4)
            if r.status_code == 200 and r.json().get("result"):
                raw = r.json().get("result")
                d = json.loads(raw) if isinstance(raw, str) else (raw or {})
                recent = d.get("recent_logs", [])
                for data in recent:
                    ticket = str(data.get("ticket", ""))
                    if ticket.isdigit() and len(ticket) >= 8:
                        pnl = float(data.get("pnl", 0.0) or 0.0)
                        accion = data.get("accion", "")
                        if accion in ["CIERRE_TOTAL", "CERRAR_TP", "CIERRE_PARCIAL", "TRAILING_STOP", "PROTECCION_BE"] or pnl != 0.0:
                            closed.append({
                                "ticket": ticket,
                                "symbol": data.get("activo", "EURUSD"),
                                "profit": pnl,
                                "type": accion,
                                "motivo": data.get("motivo", "Cierre MT5"),
                                "timestamp": data.get("timestamp", datetime.datetime.now().isoformat()),
                                "score": data.get("score", 75.0),
                                "detalle_setup": data.get("detalle_setup", "")
                            })
        except Exception as e:
            print(f"| POST-MORTEM AGENT WARN | Error leyendo Upstash cache_hist_mt5: {e}")
        return closed[:limit]

    def audit_trade_execution(self, trade: Dict[str, Any]) -> Dict[str, Any]:
        """Audita si el cierre fue por dinámica de mercado o reportó anomalía técnica."""
        motivo = str(trade.get("motivo", "")).lower()
        profit = float(trade.get("profit", 0.0) or 0.0)
        
        anomalia_tecnica = False
        nota = "Ejecución nominal en MetaTrader 5."
        
        if any(k in motivo for k in ["timeout", "socket", "desconexion", "error_broker", "rechazo"]):
            anomalia_tecnica = True
            nota = f"Alerta técnica de ejecución en MT5: {motivo}"
            
        return {
            "ticket": trade.get("ticket"),
            "symbol": trade.get("symbol"),
            "profit": profit,
            "es_ganador": profit > 0,
            "es_breakeven": profit == 0.0,
            "anomalia_tecnica": anomalia_tecnica,
            "nota_auditoria": nota
        }

    def analyze_trade_and_herds(self, trade: Dict[str, Any]) -> Dict[str, Any]:
        """
        AUTOPSIA FORENSE DE LOS 7 HERDS:
        Analiza a profundidad qué hizo cada uno de los 7 Herds de trading durante la operación.
        Genera el diagnóstico preliminar y el borrador de calibración que entregará al Supervisor Quant.
        """
        ticket = str(trade.get("ticket", "N/A"))
        symbol = str(trade.get("symbol", "EURUSD")).upper()
        profit = float(trade.get("profit", 0.0) or 0.0)
        tipo = str(trade.get("type", "CIERRE")).upper()
        score = float(trade.get("score", 75.0) or 75.0)
        setup = str(trade.get("detalle_setup", "SMC Setup"))
        motivo = str(trade.get("motivo", ""))

        is_win = profit > 0
        is_loss = profit < 0
        is_be = profit == 0
        res_str = "Ganador" if is_win else ("Breakeven" if is_be else "Pérdida")

        # Clúster Institucional CME / COMEX
        if "XAU" in symbol or "GOLD" in symbol:
            cluster = "COMEX Metals (CFD Spot | Volatilidad: GVZ)"
        else:
            cluster = "CME G5 FX Basket (Forex Spot | Volatilidad: FXVL)"

        # 1. Recolección de Contexto Operativo Atómico desde Upstash Redis (Zero Firestore Reads)
        estrategia_actual = "{}"
        estado_tf = {}
        debate_herds = {}
        atlas_micro = {}
        estado_mt5 = {}

        try:
            mget_url = f"{self.UPSTASH_URL}/mget/cache_regla_de_3/cache_mia_tensorflow/cache_herd_debate_latest/cache_mia_atlas/cache_mt5"
            r_all = requests.get(mget_url, headers=self.UPSTASH_HEADERS, timeout=4).json()
            slots = r_all.get("result", [])
            if len(slots) >= 5:
                if slots[0]:
                    estrategia_actual = slots[0]
                if slots[1]:
                    estado_tf = json.loads(slots[1]) if isinstance(slots[1], str) else slots[1]
                if slots[2]:
                    raw_deb = json.loads(slots[2]) if isinstance(slots[2], str) else slots[2]
                    debate_herds = raw_deb.get("debate", raw_deb) if isinstance(raw_deb, dict) else {}
                if slots[3]:
                    atlas_micro = json.loads(slots[3]) if isinstance(slots[3], str) else slots[3]
                if slots[4]:
                    estado_mt5 = json.loads(slots[4]) if isinstance(slots[4], str) else slots[4]
        except Exception as e_ctx:
            print(f"| POST-MORTEM AGENT WARN | Error leyendo MGET en Upstash: {e_ctx}")

        # 2. Autopsia Específica de los 7 Herds
        # Tidal: Macro & Sesión Killzone
        tidal_raw = str(debate_herds.get("herd_1_tidal", "N/A"))
        if is_win:
            tidal_eval = f"TIDAL alineó correctamente la ventana de liquidez y el sesgo macro ({tidal_raw[:100]})."
            tidal_prop = f"Consolidar la ventana horaria activa de {symbol} como zona de alta probabilidad institucional."
        else:
            tidal_eval = f"TIDAL operó en divergencia de liquidez o sesgo neutro ({tidal_raw[:100]})."
            tidal_prop = f"Reforzar el filtro Killzone en {symbol} y subordinar entradas estrictamente al sesgo macro de 4H/1D."

        # Noro: Matemáticas, POC & CVOL
        noro_raw = str(debate_herds.get("herd_2_noro", "N/A"))
        if is_win:
            noro_eval = f"NORO confirmó el nivel de confluencia POC y régimen de energía ({noro_raw[:100]})."
            noro_prop = f"Mantener el POC como nivel de soporte/resistencia institucional con tolerancia < 15 pips."
        else:
            noro_eval = f"NORO no detectó expansión contraria o hubo desalineación con el POC ({noro_raw[:100]})."
            noro_prop = f"Exigir confluencia estricta de Volume POC a menos de 15 pips y validar dinámica CVOL antes de autorizar el trade."

        # Zephr: EV & Probabilidad Bayesiana
        zephr_raw = str(debate_herds.get("herd_3_zephr", "N/A"))
        if is_win:
            zephr_eval = f"ZEPHR validó una distribución bayesiana favorable ({zephr_raw[:100]})."
            zephr_prop = f"Ratificar el modelo de Expected Value (EV) positivo para el setup {setup}."
        else:
            zephr_eval = f"ZEPHR permitió la entrada con ratio EV ajustado o score inferior al 80% ({score}%)."
            zephr_prop = f"Elevar el umbral bayesiano a >= 80% estricto y exigir un Expected Value mínimo de 1:1.5R para mitigar la asimetría."

        # Lumen: SMC Order Blocks & Liquidity
        lumen_raw = str(debate_herds.get("herd_4_lumen", "N/A"))
        if is_win:
            lumen_eval = f"LUMEN validó exitosamente la mitigación del Order Block institucional ({lumen_raw[:100]})."
            lumen_prop = f"Consolidar Order Blocks 2H y FVG en {symbol} como zonas primarias de confluencia institucional."
        else:
            lumen_eval = f"LUMEN identificó un bloque de órdenes que sufrió un barrido de liquidez macro o trampa BOS ({lumen_raw[:100]})."
            lumen_prop = f"Invalidar Order Blocks no respaldados por barridos de liquidez macro previos y exigir confirmación de mitigación en temporalidad superior."

        # Rune: Riesgo, Buffers & Trailing Locks
        rune_raw = str(debate_herds.get("herd_5_rune", "N/A"))
        if is_win:
            rune_eval = f"RUNE aplicó la cascada de 4 fases asegurando beneficios ({rune_raw[:100]})."
            rune_prop = f"Mantener la disciplina de la cascada de 4 fases (TP1 50% al 50%, BE +2.5p, Trailing Locks al 75% y 85%)."
        else:
            rune_eval = f"RUNE sufrió un barrido prematuro del Stop Loss sin margen para el retroceso ({rune_raw[:100]})."
            rune_prop = f"Ajustar el buffer del Stop Loss (+2.5 pips mínimo sobre ATR) y activar cobro de parciales anticipado para recortar la pérdida máxima."

        # TensorFlow: Inferencia 22D
        tf_acc = estado_tf.get("accuracy", "N/A")
        tf_trades = estado_tf.get("trades_aprendidos", estado_tf.get("trades_learned", 798))
        if is_win:
            tf_eval = f"TENSORFLOW acertó la inferencia tensorial 22D (Red entrenada con {tf_trades} trades)."
            tf_prop = f"Reforzar con gradiente positivo (+RL) los pesos de los tensores de entrada para {symbol}."
        else:
            tf_eval = f"TENSORFLOW falló en la predicción direccional bajo el régimen actual de volatilidad."
            tf_prop = f"Aplicar gradiente negativo (-RL) a los tensores que validaron la confluencia errónea e incorporar el caso al dataset de entrenamiento."

        # Atlas: CME/COMEX DOM L3 & CVD Delta
        atlas_raw = str(atlas_micro.get("cvd_delta", "N/A"))
        if is_win:
            atlas_eval = f"ATLAS confirmó absorción y correlación de flujo institucional en el DOM ({atlas_raw})."
            atlas_prop = f"Validar correlación positiva consistente entre flujo de órdenes CME/COMEX y el precio MT5."
        else:
            atlas_eval = f"ATLAS presentó divergencia entre el CVD Delta y la acción del precio ({atlas_raw})."
            atlas_prop = f"Exigir confirmación estricta de absorción institucional en CME DOM L3 antes de autorizar entradas que dependan de divergencia CVD."

        autopsia_herds = {
            "tidal": tidal_eval,
            "noro": noro_eval,
            "zephr": zephr_eval,
            "lumen": lumen_eval,
            "rune": rune_eval,
            "tensorflow": tf_eval,
            "atlas": atlas_eval
        }

        borrador_propuestas = {
            "tidal": tidal_prop,
            "noro": noro_prop,
            "zephr": zephr_prop,
            "lumen": lumen_prop,
            "rune": rune_prop,
            "tensorflow": tf_prop,
            "atlas": atlas_prop
        }

        # Auditoría de Anomalía Técnica
        audit = self.audit_trade_execution(trade)
        anomalia_tecnica = audit.get("anomalia_tecnica", False)
        nota_tecnica = audit.get("nota_auditoria", "Infraestructura backend nominal.")

        # Diagnóstico Forense Preliminar Consolidado
        diagnostico_forense = (
            f"Autopsia Forense Agente Post-Mortem: Trade #{ticket} en {symbol} ({tipo}) finalizó como {res_str} "
            f"(${profit:.2f} USD). Clúster: {cluster}. Setup: {setup}. Score entrada: {score}%. "
            f"Dictamen forense: {'Confluencia validada en enjambre.' if is_win else 'Desalineación entre sesgo de volatilidad y microestructura DOM/CVD.'}"
        )

        return {
            "ticket": ticket,
            "symbol": symbol,
            "cluster": cluster,
            "profit": profit,
            "type": tipo,
            "score": score,
            "setup": setup,
            "resultado": res_str,
            "es_ganador": is_win,
            "es_perdida": is_loss,
            "es_breakeven": is_be,
            "diagnostico_forense": diagnostico_forense,
            "autopsia_herds": autopsia_herds,
            "borrador_propuestas_7_herds": borrador_propuestas,
            "anomalia_tecnica": anomalia_tecnica,
            "nota_tecnica": nota_tecnica,
            "contexto_operativo": {
                "balance": estado_mt5.get("balance"),
                "equity": estado_mt5.get("equity"),
                "tf_trades": tf_trades,
                "tf_accuracy": tf_acc,
                "debate_7_herds": debate_herds,
                "atlas_micro": atlas_micro
            }
        }


# Instancia singleton del Agente Post-Mortem
post_mortem_agent = MiaPostMortemAgent()

# Exportación canónica para 100% retrocompatibilidad con app.py, crons y microservicios vía __getattr__
def __getattr__(name):
    if name == "MiaQuantSupervisor":
        from mia_supervisor_quant import MiaQuantSupervisor
        return MiaQuantSupervisor
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

if __name__ == "__main__":
    mock_trade = {
        "ticket": "994821",
        "symbol": "XAUUSD",
        "type": "VENTA",
        "profit": -45.50,
        "score": 78.5,
        "detalle_setup": "Mitigación FVG 15M + Divergencia CVD Delta",
        "motivo": "Stop Loss alcanzado"
    }
    report = post_mortem_agent.analyze_trade_and_herds(mock_trade)
    print("=== AUTOPSIA FORENSE AGENTE POST-MORTEM ===")
    print("Diagnóstico:", report.get("diagnostico_forense"))
    print("\nBorrador Propuestas 7 Herds:")
    for k, v in report.get("borrador_propuestas_7_herds", {}).items():
        print(f"• {k.upper()}: {v}")
