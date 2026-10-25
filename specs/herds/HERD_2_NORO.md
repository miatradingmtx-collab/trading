# 📐 HERD 2 (NORO): MATEMÁTICAS CUANTITATIVAS, ÁREA CVOL & CADENAS DE MARKOV

## 1. MISIÓN Y RESPONSABILIDAD TÉCNICA
HERD 2 (NORO) es el motor matemático determinista de MIA Core.
Su misión es calcular la integral del Área de Energía CVOL, modelar la dinámica de fluidos del Point of Control (POC) y evaluar las matrices de transición de Cadenas de Markov para determinar si el mercado se encuentra en régimen de compresión, equilibrio o expansión de volatilidad.

---

## 2. FÓRMULA CANÓNICA DEL ÁREA DE ENERGÍA CVOL
El régimen de energía neta entre compradores y vendedores sobre el rango de precios institucional se define por:

$$\text{Energía}(t) = \int_{p_{min}}^{p_{max}} \left[ Fuerza_{compradora}(x) - Fuerza_{vendedora}(x) \right] \, dx + C(t)$$

Donde:
- $x$ representa el nivel de precio en pips o puntos de cotización.
- $Fuerza_{compradora}(x)$ y $Fuerza_{vendedora}(x)$ son las densidades de volumen ponderadas obtenidas del perfil de volumen institucional y del libro de órdenes.
- $C(t)$ es la **constante de inercia institucional acumulada**, que amortigua fluctuaciones de ruido y captura la aceleración direccional de la sesión.

### Régimen y Normalización de Energía (Eje Z Tensorial):
$$\text{Ratio de Energía Normalizada} = \frac{\text{Área de Energía}}{2 \cdot C(t)}$$
- **Régimen Expansivo ($\text{Ratio} \ge 0.70$):** Fuerte desequilibrio institucional. Fase óptima para entradas en dirección del flujo.
- **Régimen Neutral ($0.35 \le \text{Ratio} < 0.70$):** Consolidación alrededor del POC. Exige validación estricta de extremos.
- **Régimen de Compresión ($\text{Ratio} < 0.35$):** Agotamiento de volatilidad. Prohibido abrir órdenes de ruptura falsa.

---

## 3. DOMINIO MULTI-TEMPORAL OBLIGATORIO (5 TEMPORALIDADES)
NORO evalúa estrictamente las 5 temporalidades institucionales canónicas:
- **8H & 4H (Macro Fluido):** Define la tendencia del vector de energía principal y la ubicación de las grandes bandas de $C(t)$.
- **3H & 2H (Intermedio Institucional):** Zona de cálculo del POC promediado y detección de divergencias en el área bajo la curva.
- **1H (Entrada y Confluencia Local):** Nivel de verificación de la reacción de precio.
- **Veto Terminante a Micro-Ruido:** Prohibido emitir votos o cálculos basados en velas de 1m, 5m o 15m sin confluencia de la integral macro.

---

## 4. CADENAS DE MARKOV (TRANSICIÓN DE REGÍMENES)
La matriz de transición de Markov evalúa la probabilidad de salto entre 4 estados discretos:
1. $S_1$: Tendencia Fuerte Alcista / Bajista.
2. $S_2$: Expansión de Volatilidad (Rompimiento de POC).
3. $S_3$: Rango de Equilibrio Estacionario.
4. $S_4$: Alta Dispersión / Choppy Market.

NORO solo autoriza cuando la probabilidad de transición $P(S_t \rightarrow S_{expansión}) \ge 65\%$.

---

## 5. CONDICIONES DE VETO Y APROBACIÓN
- **VETO ABSOLUTO (⛔):**
  - Área de Energía neta en colisión frontal con la dirección del trade propuesto.
  - Precio ubicado a más de 2 desviaciones estándar del POC dinámico sin retroceso institucional.
- **APROBADO (✅):**
  - Ratio de Energía normalizado $\ge 0.70$ alineado con la dirección del quórum y probabilidad de Markov expansiva.
