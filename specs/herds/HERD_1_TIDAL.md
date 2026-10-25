# 🌊 HERD 1 (TIDAL): MACRO TREND, KILLZONES & SMT DXY DIVERGENCE

## 1. MISIÓN Y RESPONSABILIDAD TÉCNICA
HERD 1 (TIDAL) es el guardián de la marea macroeconómica y el flujo institucional global.
Su responsabilidad exclusiva es auditar las ventanas horarias de liquidez bancaria (Killzones), la fortaleza del Índice Dólar (DXY), y las divergencias de Smart Money Tool (SMT) entre pares correlacionados antes de autorizar cualquier operación.

---

## 2. PARÁMETROS INSTITUCIONALES DE SESIÓN (KILLZONES)
- **Sesión de Londres (London Open Killzone):** 07:00 a 10:30 UTC (02:00 a 05:30 EST).
  - *Activos con Liquidez Alta:* GBPUSD, EURUSD, GBPJPY.
- **Sesión de Nueva York (New York Open Killzone):** 12:00 a 15:30 UTC (07:00 a 10:30 EST).
  - *Activos con Liquidez Alta:* EURUSD, GBPUSD, XAUUSD (Oro COMEX).
- **Sesión de Asia / Tokio (Asian Killzone):** 23:00 a 05:00 UTC (18:00 a 00:00 EST).
  - *Activos con Liquidez Alta:* AUDUSD, GBPJPY.
- **Ventana Muerta / Rollover Bancario (Bloqueo Estricto):** 21:00 a 22:30 UTC. Prohibida apertura por ensanchamiento de spreads.

---

## 3. SENSOR DXY & DIVERGENCIA SMT (SMART MONEY TOOL)
1. **Correlación Inversa Estricta en Pares USD:**
   - DXY al alza $\implies$ Presión bajista en EURUSD, GBPUSD, AUDUSD, XAUUSD.
   - DXY a la baja $\implies$ Presión alcista en EURUSD, GBPUSD, AUDUSD, XAUUSD.
2. **Divergencia SMT Alcista (Bullish SMT):**
   - Ocurre cuando el DXY hace un nuevo máximo más alto (*Higher High*), pero EURUSD o GBPUSD falla en hacer un nuevo mínimo más bajo (*Higher Low*). Indica acumulación institucional oculta y giro alcista inminente.
3. **Divergencia SMT Bajista (Bearish SMT):**
   - Ocurre cuando el DXY hace un nuevo mínimo más bajo (*Lower Low*), pero EURUSD o GBPUSD falla en hacer un nuevo máximo más alto (*Lower High*). Indica distribución institucional oculta y giro bajista inminente.

---

## 4. PORTAFOLIO DE COBERTURA OFICIAL
- **5 Pares Oficiales Live MT5:**
  - `EURUSD`: Par ancla USD frente a DXY.
  - `GBPUSD`: Par de alta volatilidad en Killzone Londres.
  - `AUDUSD`: Par sensible a commodities y sesión asiática.
  - `GBPJPY`: Cruce de alta beta, correlación con aversión al riesgo (JPY) y libra.
  - `XAUUSD`: Oro spot. Sensible a yields reales de bonos del tesoro y DXY.
- **1 Par Oficial Sandbox (Shadow Mode):**
  - `NZDCAD`: Modo simulación y reentrenamiento. 0 órdenes reales a broker.

---

## 5. REGLAS DE DECISIÓN Y CONDICIONES DE VETO
- **VETO ABSOLUTO (⛔):**
  - Si el trade propuesto va a favor de una compra en par USD mientras existe una divergencia SMT hostil sin mitigar.
  - Si el activo se encuentra fuera de su Killzone natural y el spread supera el 1.5x de su promedio.
- **APROBADO (✅):**
  - Confluencia de sesión activa + flujo macro alineado con la tendencia del DXY + ausencia de trampas SMT.
