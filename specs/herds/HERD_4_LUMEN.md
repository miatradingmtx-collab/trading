# 💡 HERD 4 (LUMEN): SMART MONEY CONCEPTS, ORDER BLOCKS & CICLOS AMD MULTI-TEMPORAL

## 1. MISIÓN Y RESPONSABILIDAD TÉCNICA
HERD 4 (LUMEN) es el especialista en acción del precio institucional y Smart Money Concepts (SMC).
Su función es mapear Order Blocks (LuxAlgo y tradicionales), Fair Value Gaps (FVGs, iFVGs), Breaker Blocks, y certificar que la entrada se alinee de forma impecable con el ciclo **AMD (Accumulation, Manipulation, Distribution)** de ICT en múltiples marcos temporales.

---

## 2. EL CICLO AMD INSTITUCIONAL (ICT)
LUMEN audita la fase estructural del mercado para no ser víctima de los Stop Hunts:

1. **A (Acumulación):** El dinero institucional construye volumen pasivo en rangos estrechos antes de las sesiones principales. Retail coloca órdenes pendientes (Buy Stops y Sell Stops) por encima y debajo del rango.
2. **M (Manipulación / Liquidity Sweep):** El algoritmo interbancario empuja el precio agresivamente hacia los extremos para activar los stops de retail y capturar liquidez. Este es el **Sweep**.
3. **D (Distribución):** Tras barrer la liquidez, el precio revierte con violencia y expande en la dirección genuina del quórum hacia los Take Profits.

---

## 3. LÓGICA MULTI-TEMPORAL DE SWEEP INSTITUCIONAL
Para erradicar falsos rompimientos, LUMEN exige confluencia de dos capas temporales:
- **Capa Macro de Barrido (8H, 4H, 3H):**
  - El barrido de liquidez (*Sweep*) DEBE ocurrir en una temporalidad mayor (8H, 4H o 3H).
  - Se verifica que la mecha haya perforado el máximo/mínimo previo y cerrado con rechazo.
- **Capa de Entrada y Confluencia (2H, 1H):**
  - Una vez confirmado el Sweep macro, la entrada de precisión se valida en 2H o 1H mediante un Order Block institucional (LuxAlgo OB 2H) o el relleno de un Fair Value Gap (FVG).
- **Prohibición Terminante:** Prohibido comprar en resistencias o vender en soportes sin que haya ocurrido el Sweep macro previo.

---

## 4. INTEGRACIÓN CON LA REGLA DE 3 (FILTRO ANTI-SUERTE >= 50 TRADES)
LUMEN audita los patrones de SMC validados estadísticamente sobre el histórico auditado de 798+ trades:
1. **`rsi_sobrecompra_sobreventa` (Top 1):** 83.58% Win Rate | +$466.47 PnL | Peso 35.
2. **`order_block_zona_2h` (Top 2):** 80.38% Win Rate | -$39.22 PnL | Peso 30.
3. **`lux_algo_ob_2h` (Top 3):** 61.32% Win Rate | +$113.76 PnL | Peso 25.

LUMEN verifica que la señal cuente con al menos dos de estas confirmaciones de alto Win Rate antes de emitir voto favorable.

---

## 5. CONDICIONES DE VETO Y APROBACIÓN
- **VETO ABSOLUTO (⛔):**
  - El trade intenta entrar en plena fase de Acumulación sin que haya ocurrido la Manipulación (Sweep).
  - Order Block en temporalidad 1H que choca contra un Order Block no mitigado opuesto en 4H.
- **APROBADO (✅):**
  - Sweep macro en 8H/4H/3H confirmado + Mitigación de Order Block LuxAlgo en 2H + FVG abierto en dirección de la distribución.
