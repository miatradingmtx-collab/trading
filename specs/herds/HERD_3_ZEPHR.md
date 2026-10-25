# 🎲 HERD 3 (ZEPHR): PROBABILIDAD BAYESIANA, EXPECTED VALUE & ASIMETRÍA DE DRAWDOWN

## 1. MISIÓN Y RESPONSABILIDAD TÉCNICA
HERD 3 (ZEPHR) es el auditor probabilístico y estadístico de MIA Core.
Su misión es calcular la expectativa matemática neta ($Expected \, Value$), auditar las probabilidades condicionales bayesianas con base en el historial auditado y garantizar que la rentabilidad potencial compense estrictamente la ley de asimetría de pérdidas de la cuenta.

---

## 2. FÓRMULA CANÓNICA DE EXPECTED VALUE (EV EN R)
Para cada oportunidad evaluada, ZEPHR computa la expectativa matemática:

$$EV = (P_{win} \cdot W) - (P_{loss} \cdot L)$$

Donde:
- $P_{win}$ es la probabilidad condicional bayesiana de éxito, alimentada por el accuracy de la Red Neuronal (TensorFlow) y la tasa de acierto del setup en la Regla de 3.
- $P_{loss} = 1 - P_{win}$ es la probabilidad de tocar el Stop Loss inicial.
- $W$ es la ganancia proyectada en múltiplos de riesgo ($R$), descontando comisiones y slippage.
- $L = 1.0R$ es la pérdida máxima permitida en caso de Stop Loss.

### Umbrales de Aprobación de EV:
- **Operación Normal (Balance $\ge \$5,000$ USD):** Se exige un $EV \ge +1.20R$.
- **Operación en Recuperación (Balance $< \$5,000$ USD):** Se exige un $EV \ge +1.80R$.

---

## 3. LEY DE ASIMETRÍA MATEMÁTICA Y HIGH-WATER MARK (LEY D / (1 - D))
ZEPHR vigila que ningún trade genere proyecciones simétricas engañosas:
Para cualquier drawdown fraccional $d = \frac{\text{Pérdida en USD}}{\text{Cota de Referencia}}$ (con base inicial de $5,000.00 USD o High-Water Mark):

$$R_{requerido} = \frac{d}{1 - d} \times 100 = \frac{\text{Capital a Recuperar (USD)}}{\text{Balance Actual (USD)}} \times 100$$

- Pérdida de -10% $\implies$ Requiere ganar **+11.11%**.
- Pérdida de -20% $\implies$ Requiere ganar **+25.00%**.
- Pérdida de -24.16% (Drawdown actual $3,791.83 vs $5,000) $\implies$ Requiere ganar **+31.86%** ($+$1,208.17 USD).
- Pérdida de -30% $\implies$ Requiere ganar **+42.86%**.

**Mandato de Convexidad:** Queda terminantemente prohibido autorizar trades que arriesguen capital para capturar micro-ganancias (< 0.8R) que no aporten a la recuperación asimétrica estructural.

---

## 4. FILTRO ANTI-CORRELACIÓN DE PORTAFOLIO
ZEPHR evalúa la covarianza de la canasta activa:
- Si ya existe una posición abierta en `EURUSD` en compra, ZEPHR penaliza severamente una compra simultánea en `GBPUSD` si la correlación de 30 días supera $0.85$, exigiendo que el $EV$ del segundo trade supere $+2.2R$ para justificar la doble exposición al Dólar.

---

## 5. CONDICIONES DE VETO Y APROBACIÓN
- **VETO ABSOLUTO (⛔):**
  - Expected Value negativo o marginal ($EV < +1.0R$).
  - Probabilidad Bayesiana $P_{win} < 55\%$ según el clasificador neuronal de TensorFlow.
- **APROBADO (✅):**
  - $EV \ge +1.8R$ en cuenta bajo recuperación con ratio convexidad positivo y asimetría favorable.
