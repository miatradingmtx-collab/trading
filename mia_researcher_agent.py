"""
====================================================================
AGENTE INVESTIGADOR CUANTITATIVO: ATLAS (MIA RESEARCHER AGENT)
====================================================================
Rol: Swarm Market Intelligence & Adaptive Strategy Discovery Agent
Especialidad:
  - Escaneo de Microestructura Avanzada: Footprint, CVD Delta, Imbalances
  - Volatilidad Dinámica: Régimen de Mercado y ATR Normalizado
  - Profundidad de Libro (DOM): CME FX Futures y Trampas de Liquidez
  - Minería y Backtesting Adaptativo de Nuevas Hipótesis
  - Retroalimentación a MIA KB, TensorFlow y Enjambres Herds

Reglas de Operación:
  - Cero CrewAI, Cero LangChain (Protocolo MCP + REST Nativo)
  - Desacoplamiento Anti-429: Lee y escribe exclusivamente en Upstash Redis
====================================================================
"""

import os
import json
import time
import datetime
import requests
from typing import Dict, Any, Optional

from mia_mcp_server import (
    tool_scan_footprint_delta,
    tool_calc_dynamic_atr,
    tool_scan_orderbook_depth,
    tool_market_sentiment_news,
    tool_run_strategy_backtest,
    tool_sync_insight_to_kb,
    UPSTASH_URL,
    UPSTASH_HEADERS
)

def emit_ws_event(agent_name: str, action: str, data: Any):
    """Emite eventos al WebSocket Server para la Terminal 3D y Dashboards"""
    try:
        port = os.environ.get("PORT", "8000")
        requests.post(f"http://127.0.0.1:{port}/emit", json={
            "agent": agent_name,
            "action": action,
            "data": data
        }, timeout=0.3)
    except Exception:
        pass


class AtlasResearcherAgent:
    """
    Agente Investigador Autónomo de MIA Core (ATLAS).
    Se encarga de la recolección continua de microestructura, evaluación
    de volatilidad, backtesting rápido y comunicación inter-enjambre.
    """

    def __init__(self, name: str = "ATLAS"):
        self.name = name
        self.role = "Swarm Market Intelligence & Strategy Discovery"
        self.version = "1.0.0"

    def investigate_symbol_microstructure(
        self,
        symbol: str = "EURUSD",
        current_price: float = 1.0850,
        poc_price: float = 1.0842
    ) -> Dict[str, Any]:
        """
        Ejecuta el protocolo completo de investigación cuantitativa sobre un activo.
        Utiliza el catálogo de herramientas del Servidor MCP.
        """
        emit_ws_event(self.name, "INVESTIGATING", f"Iniciando escaneo MCP para {symbol} (Footprint, Delta, ATR y DOM)...")
        
        # 1. Footprint & CVD Delta
        footprint = tool_scan_footprint_delta(symbol=symbol, current_price=current_price)
        
        # 2. ATR Dinámico y Régimen de Volatilidad
        atr_data = tool_calc_dynamic_atr(symbol=symbol, current_price=current_price)
        
        # 3. Profundidad del Libro DOM (CME Futures)
        orderbook = tool_scan_orderbook_depth(symbol=symbol, current_price=current_price, poc_price=poc_price)
        
        # 4. Macro Sentimiento y Trampas de Noticias
        sentiment = tool_market_sentiment_news(symbol=symbol)
        
        # 5. Detección de Hipótesis y Backtesting Adaptativo
        # Si hay absorción de delta o compresión de ATR, formulamos una estrategia adaptativa
        tested_strategy = None
        if footprint.get("delta_divergence") or "COMPRESSION" in atr_data.get("volatility_regime", ""):
            strat_name = f"Abs_CVD_{symbol}_ATR_{atr_data.get('atr_pips')}p"
            rules = {
                "min_score": 0.75,
                "requires_delta_divergence": True,
                "use_dynamic_atr_sl": True,
                "risk_reward": atr_data.get("recommended_risk_reward", 2.0)
            }
            tested_strategy = tool_run_strategy_backtest(
                strategy_name=strat_name,
                rules=rules,
                symbol=symbol,
                test_days=14
            )
            
            # Si supera el umbral de aprobación, se sincroniza con la base de conocimientos
            if tested_strategy.get("status") == "APPROVED_FOR_KB":
                tool_sync_insight_to_kb(
                    insight_type="VALIDATED_STRATEGY",
                    title=f"Estrategia Validada: {strat_name}",
                    payload=tested_strategy
                )
                emit_ws_event(self.name, "STRATEGY_DISCOVERED", f"Nueva estrategia validada: {strat_name} (WR: {tested_strategy['win_rate_pct']}%, EV: +${tested_strategy['expected_value_bayes']})")

        # 6. Síntesis Ejecutiva para los Compañeros de Enjambre (Herds Brief)
        brief = self._build_herd_intelligence_brief(
            symbol=symbol,
            footprint=footprint,
            atr_data=atr_data,
            orderbook=orderbook,
            sentiment=sentiment,
            tested_strategy=tested_strategy
        )
        
        # Guardar en Upstash Redis para acceso sub-100ms de todos los subsistemas
        research_payload = {
            "symbol": symbol,
            "brief": brief,
            "footprint": footprint,
            "atr_data": atr_data,
            "orderbook": orderbook,
            "sentiment": sentiment,
            "tested_strategy": tested_strategy,
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
        }
        
        try:
            url = f"{UPSTASH_URL}/set/cache_researcher_insights"
            requests.post(url, headers=UPSTASH_HEADERS, data=json.dumps(research_payload), timeout=4)
        except Exception as e:
            print(f"Error cacheando researcher insights: {e}")
            
        emit_ws_event(self.name, "REPORT_READY", brief)
        return research_payload

    def _build_herd_intelligence_brief(
        self,
        symbol: str,
        footprint: Dict[str, Any],
        atr_data: Dict[str, Any],
        orderbook: Dict[str, Any],
        sentiment: Dict[str, Any],
        tested_strategy: Optional[Dict[str, Any]]
    ) -> str:
        """Construye un brief conciso y de alta densidad para la deliberación inter-agente"""
        cvd_txt = f"CVD: {footprint['cvd_delta']} ({footprint['delta_sentiment']})"
        if footprint.get("delta_divergence"):
            cvd_txt += f" ⚠️ ALERTA: {footprint['divergence_type']}"
            
        atr_txt = f"ATR: {atr_data['atr_pips']} pips [{atr_data['volatility_regime']}]. SL Sugerido: {atr_data['suggested_sl_pips']}p | TP: {atr_data['suggested_tp_pips']}p (R:R {atr_data['recommended_risk_reward']})"
        dom_txt = f"DOM {orderbook['cme_contract']}: {orderbook['dom_imbalance']} (Bid {orderbook['bid_depth_pct']}% / Ask {orderbook['ask_depth_pct']}%). Trampa BuyStops: {orderbook['resting_liquidity_pools']['buy_stops_liquidity_trap']} | Trampa SellStops: {orderbook['resting_liquidity_pools']['sell_stops_liquidity_trap']}"
        
        strat_txt = "Sin nueva estrategia requerida (Parámetros estándar vigentes)"
        if tested_strategy:
            strat_txt = f"Nueva Estrategia Evaluada '{tested_strategy['strategy_name']}': {tested_strategy['status']} (WR {tested_strategy['win_rate_pct']}%, EV +${tested_strategy['expected_value_bayes']})"
            
        brief = (
            f"[INTELIGENCIA CUANTITATIVA ATLAS - {symbol}]: "
            f"1. {cvd_txt} | "
            f"2. {atr_txt} | "
            f"3. {dom_txt} | "
            f"4. Macro: {sentiment['institutional_cot_bias']} (Noticias: {sentiment['news_status']}) | "
            f"5. Backtest Adaptativo: {strat_txt}"
        )
        return brief


# Instancia singleton del Investigador
atlas_researcher = AtlasResearcherAgent()

if __name__ == "__main__":
    print("Probando ciclo de investigación del Agente ATLAS...")
    resultado = atlas_researcher.investigate_symbol_microstructure("EURUSD", 1.0850, 1.0842)
    print("\nBRIEF GENERADO PARA LOS ENJAMBRES:")
    print(resultado["brief"])
