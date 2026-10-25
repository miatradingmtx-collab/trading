# 🛡️ HERD 5 (RUNE): GESTIÓN DE RIESGO INSTITUCIONAL V2, SIZING & CASCADA ASIMÉTRICA

## 1. MISIÓN Y RESPONSABILIDAD TÉCNICA
HERD 5 (RUNE) es el custodio terminal del capital y el motor de ejecución en MetaTrader 5.
Su función es gobernar el dimensionamiento de posición (lotes), imponer los límites de drawdown diario, aplicar la regla de la canasta USD y ejecutar la **Cascada Asimétrica de 4 Fases** para proteger los beneficios flotantes.

---

## 2. CASCADA ASIMÉTRICA DE 4 FASES (RUNE ENGINE)
RUNE erradica cierres prematuros de trailing stops mediante una cascada geométrica de 4 fases:

1. **Fase 1 (Cobro Parcial TP1):**
   - Se ejecuta al **50% de la distancia total** proyectada al TP full.
   - Cobro forzoso del **50% del volumen del trade** (asegurando un mínimo de $+1.0R$ neto al balance).
2. **Fase 2 (Break-Even Institucional):**
   - Se activa inmediatamente después de liquidar el TP1.
   - Desplazamiento automático del Stop Loss a Break-Even con un **buffer defensivo de +2.5 pips** para absorber spreads y micro-fluctuaciones sin sacar la posición en pérdidas por comisiones.
3. **Fase 3 (Trailing Locks Asimétricos):**
   - **Trailing Lock 1 (al 75% del recorrido):** Desplaza el Stop Loss asegurando el **+40% del beneficio total proyectado**.
   - **Trailing Lock 2 (al 85% del recorrido):** Desplaza el Stop Loss asegurando el **+65% del beneficio total proyectado**.
4. **Fase 4 (Front-Run TP):**
   - Al alcanzar el **95% de la distancia al objetivo final**, RUNE cierra el 100% de la posición remanente en el mercado para evitar retrocesos violentos a milímetros del Take Profit.

---

## 3. LÍMITE ESTRICTO DE CANASTA USD (MÁXIMO 2 TRADES)
- **Regla Inquebrantable:** Queda terminantemente PROHIBIDO mantener más de **2 operaciones simultáneas** en pares que contengan el Dólar estadounidense (`EURUSD`, `GBPUSD`, `AUDUSD`, `XAUUSD`).
- **Motivo de Riesgo:** Evita la sobre-exposición al riesgo sistémico del Dólar estadounidense y eventos de volatilidad extrema (FOMC, NFP, CPI).

---

## 4. FILTRO ANTI-CAZA ALL-TIME HIGH EN ORO (XAUUSD)
- Queda terminantemente prohibido abrir órdenes de compra en Oro (`XAUUSD`) si el precio actual se encuentra dentro del **0.5% del All-Time High (Máximo Histórico)** sin que haya existido un retroceso interbancario previo de al menos 30 a 50 pips.

---

## 5. CONFINAMIENTO DE SANDBOX (NZDCAD)
- El par `NZDCAD` está catalogado exclusivamente como activo experimental de entrenamiento (Shadow Mode).
- RUNE bloquea cualquier despacho de órdenes de `NZDCAD` hacia el broker real de MetaTrader 5. Toda operación en este par es 100% virtual.

---

## 6. CONDICIONES DE VETO Y APROBACIÓN
- **VETO ABSOLUTO (⛔):**
  - Drawdown del día excede -$150.00 USD.
  - Canasta USD saturada (ya hay 2 operaciones abiertas con USD).
  - Intento de compra en All-Time High en XAUUSD.
  - Ratio Riesgo/Beneficio inferior a 1:2.
- **APROBADO (✅):**
  - Espacio disponible en la canasta USD + Sizing defensivo calculado + Parámetros de la Cascada de 4 Fases cargados en el dispatcher.
