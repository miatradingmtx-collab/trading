#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
MIA POST-MORTEM AGENT (RAMA 1 - WORKER FORENSE DE TRADING)
================================================================================
Worker especializado en la recolección, auditoría y análisis forense de datos
de trades cerrados desde MetaTrader 5 (Upstash cache_hist_mt5 y Firestore mia_audit_logs).

MISIÓN:
- Extraer métricas crudas del trade: Ticket MT5, PnL, Tipo de cierre, Drawdown relativo.
- Auditoría de anomalías técnicas de ejecución (desconexiones, timeouts, slippage).
- Suministrar el contexto forense limpio al MiaQuantSupervisor para su deliberación con Gemini Pro.
================================================================================
"""

import os
import json
import datetime
import requests
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

load_dotenv()

# Exportación Canónica para Retrocompatibilidad 100% con app.py y crons
from mia_supervisor_quant import MiaQuantSupervisor

class MiaPostMortemAgent:
    """
    AGENTE FORENSE POST-MORTEM (WORKER DE TRADING).
    Extrae y normaliza trades cerrados de MT5 para el Supervisor Quant.
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

if __name__ == "__main__":
    agent = MiaPostMortemAgent()
    trades = agent.fetch_recent_closed_trades(limit=5)
    print(f"| POST-MORTEM AGENT | {len(trades)} trades cerrados auditados.")
    if trades:
        audit = agent.audit_trade_execution(trades[0])
        print(json.dumps(audit, indent=2))
