"""
====================================================================
MÓDULO SENSOR DXY & DETECTOR DE DIVERGENCIAS INSTITUCIONALES SMT
====================================================================
Misión Cuantitativa:
1. Calcular y rastrear la cotización real y sintética del Dollar Index (DXY).
2. Detectar anomalías de Divergencia SMT (Smart Money Technique) entre
   el DXY y las divisas del portafolio (EURUSD, GBPUSD, AUDUSD, XAUUSD).
3. Emitir vetos institucionales automáticos para evitar trampas de liquidez
   y sobre-correlación direccional en el dólar estadounidense.
====================================================================
"""

import math
import time
import datetime
from typing import Dict, Any, Optional, List

# Constantes oficiales de la fórmula geométrica del DXY (US Dollar Index)
# DXY = 50.14348112 * (EURUSD^-0.576) * (USDJPY^0.136) * (GBPUSD^-0.119) * (USDCAD^0.091) * (USDSEK^0.042) * (USDCHF^0.036)
PESOS_DXY = {
    "EURUSD": -0.576,
    "USDJPY": 0.136,
    "GBPUSD": -0.119,
    "USDCAD": 0.091,
    "USDSEK": 0.042,
    "USDCHF": 0.036
}
CONSTANTE_DXY = 50.14348112

class DxySmtSensor:
    def __init__(self):
        self.ultimo_dxy: float = 104.25
        self.ultimo_timestamp: float = 0.0
        self.historial_dxy: List[Dict[str, Any]] = []
        self.historial_pares: Dict[str, List[Dict[str, Any]]] = {
            "EURUSD": [],
            "GBPUSD": [],
            "AUDUSD": [],
            "XAUUSD": []
        }

    def calcular_dxy_sintetico(self, precios_spot: Dict[str, float]) -> float:
        """
        Calcula el DXY con precisión matemática a partir de los precios spot del mercado.
        Si faltan pares secundarios (CAD, SEK, CHF), utiliza valores de equilibrio neutral.
        """
        eurusd = precios_spot.get("EURUSD", 1.1195)
        gbpusd = precios_spot.get("GBPUSD", 1.3235)
        usdjpy = precios_spot.get("USDJPY", precios_spot.get("GBPJPY", 209.5) / gbpusd if gbpusd > 0 else 158.0)
        usdcad = precios_spot.get("USDCAD", 1.3750)
        usdsek = precios_spot.get("USDSEK", 10.450)
        usdchf = precios_spot.get("USDCHF", 0.8650)

        try:
            val = CONSTANTE_DXY * (
                (eurusd ** PESOS_DXY["EURUSD"]) *
                (usdjpy ** PESOS_DXY["USDJPY"]) *
                (gbpusd ** PESOS_DXY["GBPUSD"]) *
                (usdcad ** PESOS_DXY["USDCAD"]) *
                (usdsek ** PESOS_DXY["USDSEK"]) *
                (usdchf ** PESOS_DXY["USDCHF"])
            )
            dxy_calculado = round(val, 3)
            self.ultimo_dxy = dxy_calculado
            self.ultimo_timestamp = time.time()
            
            # Registrar en memoria histórica (máximo 60 registros)
            self.historial_dxy.append({
                "timestamp": self.ultimo_timestamp,
                "dxy": dxy_calculado
            })
            if len(self.historial_dxy) > 60:
                self.historial_dxy.pop(0)
                
            return dxy_calculado
        except Exception:
            return self.ultimo_dxy

    def registrar_precio_par(self, symbol: str, precio: float):
        """Registra el precio de un par para correlación temporal"""
        sym = symbol.upper().replace("/", "").replace("_", "")
        if sym in self.historial_pares:
            self.historial_pares[sym].append({
                "timestamp": time.time(),
                "precio": precio
            })
            if len(self.historial_pares[sym]) > 60:
                self.historial_pares[sym].pop(0)

    def evaluar_divergencia_smt(
        self,
        symbol: str,
        accion: str,
        precio_actual: float,
        precios_spot: Dict[str, float],
        poc_price: float = 0.0
    ) -> Dict[str, Any]:
        """
        Evalúa si existe una anomalía de Divergencia SMT (Smart Money Technique)
        entre el DXY y el activo evaluado.
        
        Reglas Institucionales:
        1. VENTA en Par USD (ej. EURUSD SELL):
           - Si DXY está haciendo nuevos máximos, pero EURUSD no rompe mínimos -> DIVERGENCIA SMT ALCISTA EN EUR.
             Las instituciones están comprando EUR en secreto. -> VETO DE VENTA.
        2. COMPRA en Par USD (ej. EURUSD BUY):
           - Si DXY está haciendo nuevos mínimos, pero EURUSD no rompe máximos -> DIVERGENCIA SMT BAJISTA EN EUR.
             Las instituciones no apoyan la subida. -> VETO DE COMPRA.
        """
        sym = symbol.upper().replace("/", "").replace("_", "")
        accion_norm = accion.upper()
        dxy_actual = self.calcular_dxy_sintetico(precios_spot)
        self.registrar_precio_par(sym, precio_actual)

        # Si el activo no es un par directo con USD, no aplica veto estricto SMT
        if sym not in ["EURUSD", "GBPUSD", "AUDUSD", "XAUUSD"]:
            return {
                "aplica_smt": False,
                "dxy_spot": dxy_actual,
                "divergencia_detectada": False,
                "veto_entrada": False,
                "motivo": f"{sym} no tiene dependencia directa con el dólar estadounidense."
            }

        # Analizar tendencia reciente del DXY
        dxy_delta = 0.0
        if len(self.historial_dxy) >= 2:
            dxy_delta = self.historial_dxy[-1]["dxy"] - self.historial_dxy[0]["dxy"]

        # Analizar tendencia reciente del Par
        par_hist = self.historial_pares.get(sym, [])
        par_delta = 0.0
        if len(par_hist) >= 2:
            par_delta = par_hist[-1]["precio"] - par_hist[0]["precio"]

        divergencia_detectada = False
        tipo_divergencia = "NEUTRAL"
        veto_entrada = False
        motivo = "Flujo institucional DXY alineado."

        # CASO 1: Queremos VENDER el par (apuesta a favor de USD)
        if accion_norm in ["VENTA", "SELL"]:
            # Si el DXY está subiendo fuertemente pero el par se niega a caer (par_delta >= 0 o por encima de POC)
            if dxy_delta > 0.08 and par_delta >= 0.0:
                divergencia_detectada = True
                tipo_divergencia = "SMT_BULLISH_ABSORPTION_IN_PAIR"
                veto_entrada = True
                motivo = (
                    f"⚠️ ALERTA SMT DXY: El Dollar Index sube (+{dxy_delta:.2f}) pero {sym} no rompe mínimos. "
                    "Absorción pasiva institucional detectada en el par. Riesgo alto de trampa para osos."
                )
            # O si el DXY está cayendo fuertemente (dxy_delta < -0.05), vender el par es ir contra el flujo macro del dólar
            elif dxy_delta < -0.06:
                divergencia_detectada = True
                tipo_divergencia = "MACRO_DXY_WEAKNESS"
                veto_entrada = True
                motivo = (
                    f"⚠️ VETO DXY: El Dollar Index muestra debilidad macro ({dxy_delta:.2f}). "
                    f"Prohibido abrir VENTAS en {sym} contra el retroceso del dólar."
                )

        # CASO 2: Queremos COMPRAR el par (apuesta en contra de USD)
        elif accion_norm in ["COMPRA", "BUY"]:
            # Si el DXY está cayendo pero el par se niega a subir
            if dxy_delta < -0.08 and par_delta <= 0.0:
                divergencia_detectada = True
                tipo_divergencia = "SMT_BEARISH_EXHAUSTION_IN_PAIR"
                veto_entrada = True
                motivo = (
                    f"⚠️ ALERTA SMT DXY: El Dollar Index cae ({dxy_delta:.2f}) pero {sym} no logra romper al alza. "
                    "Falta de demanda institucional en el par. Riesgo alto de trampa para toros."
                )
            # O si el DXY está subiendo fuertemente, comprar el par es ir contra el flujo macro
            elif dxy_delta > 0.06:
                divergencia_detectada = True
                tipo_divergencia = "MACRO_DXY_STRENGTH"
                veto_entrada = True
                motivo = (
                    f"⚠️ VETO DXY: El Dollar Index muestra fuerte presión compradora (+{dxy_delta:.2f}). "
                    f"Prohibido abrir COMPRAS en {sym} contra el impulso del dólar."
                )

        return {
            "aplica_smt": True,
            "dxy_spot": dxy_actual,
            "dxy_delta": round(dxy_delta, 3),
            "par_delta": round(par_delta, 5),
            "divergencia_detectada": divergencia_detectada,
            "tipo_divergencia": tipo_divergencia,
            "veto_entrada": veto_entrada,
            "motivo": motivo,
            "timestamp": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        }

# Instancia singleton del sensor
dxy_sensor = DxySmtSensor()
