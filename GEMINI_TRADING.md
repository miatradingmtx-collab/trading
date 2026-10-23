# REGLAS DE NEGOCIO Y TRADING (FRONT-OFFICE)

---
name: modo_shadow_bloqueo_mt5
description: Regla de operabilidad en Modo Shadow (Paper Trading) con bloqueo estricto de MetaTrader 5 y asignacin de tickets virtuales.
trigger: always_on
---

#  REGLA: MODO SHADOW GLOBAL Y TICKETS VIRTUALES (#SHADOW_XXXXXX)
1. **Bloqueo Estricto de MetaTrader 5:** Durante la ventana de calibracin de 1 a 2 semanas, la ejecucin real en MetaQuotes est BLOQUEADA (`SHADOW_MODE_GLOBAL = True`). Queda estrictamente prohibido enviar rdenes con dinero real.
2. **Asignacin de Tickets Virtuales:** Cada trade analizado o simulado por los Enjambres Herds, TensorFlow o ATLAS debe asignarse a un ticket virtual con formato `#SHADOW_XXXXXX` correlacionado con el ticket real.
3. **Anlisis Contrafactual ("What-If"):** Toda comparacin entre la Rama Champion (Herds tradicionales) y la Rama Challenger (ATLAS con CVD Delta + ATR + DOM) se almacena en los slots `cache_shadow_trades` y `cache_mia_atlas` de Upstash Redis para no contaminar el historial productivo ni generar errores 429 en Firebase.

---
name: malla_7_herds_desacoplada
description: Regla para la arquitectura de 7 Herds desacoplados, Qurum Master y prevencin de 429/404 en OpenRouter.
trigger: always_on
---

#  REGLA: MALLA DE 7 HERDS DESACOPLADOS Y QURUM MASTER
1. **Taxonoma Unvoca de Especializacin (Single Responsibility):** Prohibido fusionar o mezclar roles en un solo Herd. La malla consta de 7 agentes independientes:
   - `HERD 1 (TIDAL)`: Macro Trend & Liquidez de Sesiones.
   - `HERD 2 (NORO)`: Matemticas Cuantitativas, POC y Markov.
   - `HERD 3 (ZEPHR)`: Probabilidad Bayesiana y Expected Value.
   - `HERD 4 (LUMEN)`: Smart Money Concepts (SMC) & Order Blocks.
   - `HERD 5 (RUNE)`: Gestin de Riesgo Defensivo y Sizing.
   - `HERD 6 (TENSORFLOW)`: Inferencia Neuronal Continua (Railway).
   - `HERD 7 (ATLAS)`: Microestructura DOM CME/OANDA, CVD Delta y Servidor MCP.
   - `MASTER ORCHESTRATOR`: Gatekeeper de Qurum Calificado Ponderado ($\sum w_i \cdot v_i \ge 0.70$).
2. **Prevencin Anti-429 y Anti-404:** Toda la deliberacin inter-agente debe ejecutarse en un solo ciclo atmico a OpenRouter con triple failover (`meta-llama/llama-3.3-70b-instruct` -> `deepseek/deepseek-chat` -> `meta-llama/llama-3.1-70b-instruct`). Cero tokens de LLM para cmputo determinista (TF, NORO y ATLAS MCP corren en C++/Python nativo).

---
name: homologacion_estricta_mt5_dashboard
description: Regla de paridad absoluta entre la cuenta real de MetaTrader 5 y el Dashboard Web (Anti-Discrepancia).
trigger: always_on
---

#  REGLA: HOMOLOGACIN ESTRICTA MT5 VS DASHBOARD (CERO DISCREPANCIA)
1. **Paridad Total con Broker:** Las posiciones mostradas en el Dashboard (`Posiciones Activas / Trades en Vivo (MT5)`) y en el slot `cache_mt5` deben coincidir exactamente con las rdenes abiertas reales en MetaTrader 5.
2. **Prohibicin de rdenes Fantasma:** Si una orden cierra o se liquida en MT5 (ej. XAUUSD), queda estrictamente prohibido mantenerla en `operaciones_activas`. Debe ser depurada de inmediato de la memoria viva y archivada en `cache_hist_mt5`.
3. **Precisin Matemtica y Redondeo:** El flotante neto, balance, equidad y mrgenes deben recalcularse dinmicamente y con estricto redondeo a 2 decimales (`round(val, 2)`), homologados con la moneda de la cuenta de trading.

---
name: dinamismo_regla_de_3_y_supervisor
description: Regla para la actualizacin perpetua de la Regla de 3 y el rol del Agente Supervisor Watchdog.
trigger: always_on
---

# ⚖️ REGLA: REGLA DE 3 DINÁMICA CON FILTRO ANTI-SUERTE (>= 50 TRADES) Y AGENTE SUPERVISOR
1. **Regla de 3 Dinámica con Filtro Anti-Suerte:** La colección `mia_kb/regla_de_3` y el slot `cache_regla_de_3` se rigen por la **Ley Institucional de Significancia Estadística (>= 50 Trades)**. Queda ESTRICTAMENTE PROHIBIDO que el Machine Learning, agentes LLM o supervisores alteren o propongan alterar el Top 1, Top 2 o Top 3 basándose en rachas de corto plazo, el 'día de suerte' o la 'semana de suerte' (< 50 trades). Todo candidato DEBE contar con al menos 50 confirmaciones históricas reales cerradas en `indicadores_impacto` o `patrones_ict_smc`, ordenándose por Win Rate real y expectativa matemática positiva ($PnL > 0$).
2. **Top 3 Institucional Validado:**
   - **Top 1:** `rsi_sobrecompra_sobreventa` (67 trades | 83.58% Win Rate | +$466.47 PnL | Peso 35).
   - **Top 2:** `order_block_zona_2h` (158 trades | 80.38% Win Rate | -$39.22 PnL | Peso 30).
   - **Top 3:** `lux_algo_ob_2h` (106 trades | 61.32% Win Rate | +$113.76 PnL | Peso 25).
3. **MIA Supervisor Watchdog (`mia_supervisor_agent.py`):** Monitorea la integridad de los datos, previene ráfagas masivas duplicadas de reportes HFT en Firestore y mantiene sincronizado el Dashboard respetando estrictamente el umbral de 50 trades. Toda propuesta de ajuste requiere autorización HITL explícita.

---
name: arquitectura_dual_swarms_desacoplados
description: Regla de desacoplamiento estricto entre Enjambre de Trading y Enjambre de Infraestructura / Ops.
trigger: always_on
---

#  REGLA: ARQUITECTURA DUAL DE ENJAMBRES (TRADING VS SYSTEM OPS)
1. **Desacoplamiento Front-Office / Back-Office:** Queda estrictamente prohibido mezclar tareas de infraestructura, sanitizacin de base de datos o cmputo de mtricas de UI dentro del Enjambre de Trading de Mercado (`mia_master_swarm_rest.py`).
2. **Enjambre de Trading (`MIA_MARKET_TRADING_SWARM`):** 7 Herds Especializados (TIDAL, NORO, ZEPHR, LUMEN, RUNE, TENSORFLOW, ATLAS) + MASTER Gatekeeper enfocados exclusivamente en la lectura de mercado, SMC, DOM, CVD Delta y deliberacin a OpenRouter.
3. **Enjambre de Operaciones (`MIA_SYSTEM_OPS_SWARM`):** 4 Herds Tcnicos (HERD T1 DB_SYNC, HERD T2 KB_ENGINE, HERD T3 KPI_ANALYTICS, HERD T4 DEVOPS_HEALTH) bajo el mando del `WATCHDOG SUPERVISOR`.
4. **Cero Tokens LLM en Infraestructura:** El Enjambre de Operaciones corre en Python nativo determinista, consumiendo cero tokens de LLM y cero cuota de Firebase mediante Upstash Redis.

---
name: estricta_separacion_shadow_y_filtro_noticias
description: Regla para evitar la contaminacion cruzada de metricas Shadow a Produccion y gobernar el Filtro de Noticias.
trigger: always_on
---

# ?? REGLA: SEPARACIN STRICTA SHADOW MODE Y FILTRO DE NOTICIAS
1. **Contaminacin Cero a Produccin:** Queda ESTRICTAMENTE PROHIBIDO que el Agente Supervisor o cualquier script automtico inyecte pesos, mtricas o indicadores provenientes de TensorFlow, ATLAS o Enjambres HFT (Herds) hacia las tablas de produccin (ej. mia_kb/regla_de_3) mientras se encuentren en periodo de "Shadow Mode" o calibracin.
2. **Tablas Aisladas:** El aprendizaje en la sombra debe escribirse EXCLUSIVAMENTE en sus colecciones y cachs dedicadas (cache_mia_atlas, cache_mia_tensorflow, cache_shadow_trades, cache_herd_debate_latest).
3. **Filtro de Noticias Trampa:** El nodo iltro_trampa_noticias (que rige los 15 minutos previos y 5 posteriores a una noticia) es una regla estructural y esttica de seguridad. **NO debe ser alterada dinmicamente por Machine Learning**. Si los Enjambres desean probar diferentes tiempos de bloqueo pre-noticia, lo harn simulando en sus propias tablas, sin afectar la produccin.
4. **Consulta Anti-429 Integral:** El iltro_trampa_noticias y la 
egla_de_3 deben ser consultados 100% mediante Upstash Redis (cache_regla_de_3). Cero consultas directas a Firebase Firestore al momento de ejecutar un trade.
5. **Protocolo de Migracin (Slack):** Cuando termine la ventana de calibracin (1-2 semanas), la decisin de pasar a TensorFlow/ATLAS a Produccin (hacer el "Switch") es clasificada como [REQUIERE APROBACIN HUMANA ??]. El Supervisor debe solicitar autorizacin obligatoria en Slack antes de tocar la base de datos principal de Firebase.



# 🧠 CBR DE ENJAMBRES DE TRADING (ANÁLISIS POST-MORTEM Y AUTO-AJUSTE)
**DIVISIÓN CANÓNICA DE TAREAS Y MODELOS EN TRADING:**
1. **Agente Post-Mortem y Supervisor Quant (Motor: Google Gemini 1.5 Pro | Canal: #mia-trading-insights):**
   - Son los encargados cognitivos exclusivos de realizar la autopsia de cada trade cerrado (Win, Loss, Breakeven).
   - Recopilan y cruzan: el debate de los 7 Herds (Llama 70B), la inferencia de TensorFlow, la microestructura DOM/CVD de ATLAS, el balance de MT5 y el historial de Firebase.
   - Sintetizan el caso y lo guardan en la memoria CBR:
     * Memoria Viva (Upstash): `cache_trading_learning_kb`
     * Memoria Histórica (Firebase): `mia_trading_learning_history`
   - Formulan propuestas de mejora cuantitativa para los 5 pares oficiales de MT5 con mandato HITL.

2. **Los 7 Herds del Swarm (Motor: Llama 3.3 70B REST / Groq | Upstash Redis):**
   - TIDAL, NORO, ZEPHR, LUMEN, RUNE, TENSORFLOW y ATLAS analizan el mercado segundo a segundo usando Llama 70B.
   - **Consultar el CBR antes de Operar:** Antes de emitir un veredicto de compra/venta, consultan `cache_trading_learning_kb` para identificar si la situación actual coincide con un caso perdedor previo y evitar caer en la misma trampa.
   - Vuelcan su debate inter-agente a `cache_herd_debate_latest` para que el Agente Post-Mortem lo audite.

*(Nota: Debido al mandato HITL Omnipresente, cualquier alteración real a pesos o métricas derivada de estos Casos de Estudio debe enviarse como propuesta a `cache_pending_ops_approvals` para aprobación humana, hasta que se certifique la Prueba de Confianza).*

# REGLA: TERMINOLOGÍA ESTRICTA PARA PARCIALES VS TRAILING STOP
**REGLA DE ORO:** Está terminantemente PROHIBIDO confundir un Cierre Parcial (Take Profit Parcial) con un Trailing Stop. Son dos conceptos operativos matemáticamente distintos y su telemetría no debe cruzarse.
- **PARCIAL (TP40, TP65, TP25, TP50):** Es una toma de liquidez estática programada a un nivel específico de ganancia. Los campos de la base de datos 	otal_hits_tp40 y 	otal_hits_tp65 DEBEN referirse exclusivamente a la ejecución de estos parciales. En el código, deben usarse constantes como TP_PARCIAL_40 o TP_PARCIAL_65.
- **TRAILING STOP (TS):** Es el seguimiento dinámico del SL (Stop Loss) para proteger ganancias conforme el precio avanza. No es un TP estático. Golpear el Trailing Stop significa que el SL dinámico fue alcanzado en retroceso.
Los LLMs y el Agente Quant/Post-Mortem deben aplicar siempre esta distinción ontológica al redactar sus diagnósticos y reglas en el CBR.


---
name: regla_oro_balance_base_5000
description: Prohibición terminante de calificar la cuenta o ganancias como saludables u óptimas mientras el saldo esté por debajo del capital inicial base de $5,000 USD.
trigger: always_on
---

# 🛑 REGLA DE ORO DE VERDAD FINANCIERA (SALDO BASE $5,000 USD)
**MANDATO ESTRICTO PARA TODOS LOS AGENTES LLM, CUANTITATIVOS Y DE INFRAESTRUCTURA:**
1. **Capital Base Inicial Canónico:** La cuenta partió formalmente de un capital inicial de **$5,000.00 USD**.
2. **Prohibición Terminante de Calificación "Saludable" u "Óptima":**
   Queda TERMINANTEMENTE PROHIBIDO que cualquier Agente LLM (Post-Mortem, Supervisor Quant, Watchdog T1-T10, 7 Herds) o reporte califique la cuenta, el balance o las ganancias como "saludables", "óptimas" o "positivas" mientras el balance auditado se encuentre por debajo de **$5,000.00 USD**.
3. **Estado Oficial de la Cuenta:** Mientras `balance < $5,000.00 USD`, el único estado oficial, honesto y auditable es:
   `ESTADO DE LA CUENTA: EN RECUPERACIÓN / BAJO DRAWDOWN SEVERO ACUMULADO (-$X USD / -Y% vs Base $5,000)`.
4. **Criterio Inquebrantable de Restablecimiento:** La cuenta SOLO y EXCLUSIVAMENTE podrá ser declarada como "Restablecida / Saludable" cuando el balance real auditado en MT5 sea **>= $5,000.00 USD** de forma neta y comprobada.
5. **Enfoque de Recuperación de Capital:** Cada propuesta de trading, ajuste de lotaje, trailing stop, sesiones o DOM debe tener como único objetivo prioritario la recuperación asimétrica del capital hacia los $5,000 USD, erradicando micro-ganancias prematuras ($2-$5 USD) en operaciones que arriesgan $30+ USD.

# 🛑 REGLA DE ORO DE ASIMETRÍA MATEMÁTICA DE RECUPERACIÓN Y HIGH-WATER MARK (LEY D / (1 - D))
**MANDATO CUANTITATIVO PARA TODOS LOS AGENTES LLM (POST-MORTEM, QUANT, WATCHDOG T1-T10, 7 HERDS) Y ALGORITMOS:**
1. **Prohibición Terminante de Proyección Simétrica:**
   Queda TERMINANTEMENTE PROHIBIDO que cualquier Agente LLM o algoritmo asuma o reporte que una pérdida porcentual se recupera con el mismo porcentaje de ganancia (e.g. creer que perder 20% se sana ganando 20%).
2. **Fórmula Canónica de Recuperación Asimétrica:**
   Para cualquier drawdown fraccional $d = \frac{\text{Pérdida en USD}}{\text{Cota de Referencia}}$ (donde $0 \le d < 1$), el porcentaje de recuperación real requerido $R$ sobre el balance reducido actual es:
   $$R = \frac{d}{1 - d} \times 100 = \frac{\text{Capital a Recuperar (USD)}}{\text{Balance Actual (USD)}} \times 100$$
   - Pérdida de -10% $\implies$ Requiere ganar **+11.11%**.
   - Pérdida de -20% $\implies$ Requiere ganar **+25.00%** (Déficit residual si solo se gana 20%: $B_{peak} \times d^2 = \$200$ USD).
   - Pérdida de -24.16% (Drawdown actual $3,791.83 vs $5,000) $\implies$ Requiere ganar **+31.86%** ($+$1,208.17 USD).
   - Pérdida de -30% $\implies$ Requiere ganar **+42.86%**.
   - Pérdida de -50% $\implies$ Requiere ganar **+100.00%**.
3. **Doble Cota de Sanación (Base $5,000 USD vs High-Water Mark Dinámico):**
   - **Caso 1: Balance < $5,000.00 USD (Drawdown Estructural vs Base):**
     La meta obligatoria de sanación es $C_{base} = \$5,000.00$. El porcentaje de recuperación es $R_{base} = \frac{5,000 - \text{Balance}}{\text{Balance}} \times 100$. Estado: `ESTADO DE LA CUENTA: EN RECUPERACIÓN / BAJO DRAWDOWN SEVERO ACUMULADO`.
   - **Caso 2: Balance >= $5,000.00 USD pero < High-Water Mark (Retroceso de Pico):**
     Si la cuenta sube a $5,400 y luego retrocede a $5,200 (caída de -3.70%), la recuperación requerida para sanar el retroceso al pico es $R_{HWM} = \frac{5,400 - 5,200}{5,200} \times 100 = +3.85\%$. Estado: `ESTADO DE LA CUENTA: EN RECUPERACIÓN / RETROCESO DE PICO HWM (-$200 USD / -3.70% vs HWM $5,400)`.
   - **Criterio Inquebrantable de Cuenta Sanada:** La cuenta SOLO se considera plenamente "Sanada y en Máximos" cuando el balance real auditado sea $\ge \$5,000.00$ USD Y $\ge B_{HWM}$.

---
name: portafolio_hermetico_oficial_mt5
description: Regla de portafolio hermético canónico (5 Live MT5 + 1 Sandbox NZDCAD) y control estricto anti-429 de inferencia LLM.
trigger: always_on
---

# 🛑 REGLA: PORTAFOLIO HERMÉTICO INSTITUCIONAL MT5 (5 LIVE + 1 SANDBOX)
1. **Composición Canónica Inalterable:**
   - **5 Pares en Vivo MT5:** `EURUSD`, `GBPUSD`, `AUDUSD`, `GBPJPY`, `XAUUSD`.
   - **1 Par en Sandbox (Shadow Mode):** `NZDCAD` (aislado estrictamente para reentrenamiento; prohibido abrir órdenes en broker).
2. **Prohibición de Activos Foráneos o Residuales:**
   Queda terminantemente prohibido que los escáneres, matrices de confirmación (`trading_matrix`), memorias RAM (`FIREBASE VIP`) o deliberaciones de los Herds procesen activos fuera del portafolio (como `BTC`, `UNKNOWN`, `XAUUSD_TEST`, `SP500`, `SPX500`, `NAS100`, `NASDAQ100`, `US30`, `USDJPY`, `USDCAD`, `USDCHF`, `EURGBP`, `GBPCAD`, `CHFJPY`, `EURJPY`).
3. **Optimización de Cuotas LLM (Anti-429 Groq / Gemini / OpenRouter):**
   Para no agotar cuotas innecesariamente, los 7 Herds y LLMs solo evalúan activos que cuenten con liquidez en su Killzone institucional activa:
   - **Londres:** `GBPUSD`, `EURUSD`, `GBPJPY`.
   - **Nueva York:** `EURUSD`, `XAUUSD`.
   - **Asia:** `AUDUSD`, `GBPJPY`.
   Esto reduce el consumo de tokens en un 70% y previene bloqueos por rate limit 429.

---
name: cascada_riesgo_v2_rune
description: Regla de gestión de riesgo institucional v2 con cascada asimétrica de 4 fases y límite de canasta USD.
trigger: always_on
---

# 🛑 REGLA: GESTIÓN DE RIESGO INSTITUCIONAL V2 (CASCADA RUNE 4 FASES)
1. **Cascada Asimétrica de 4 Fases (HERD 5 RUNE):**
   - **Fase 1 (TP1 Parcial al 50% de recorrido):** Cobro obligado del 50% del volumen inicial con un ratio mínimo de +1.0R.
   - **Fase 2 (Break-Even Institucional):** Desplazamiento automático de SL a BE tras consolidar TP1, agregando un buffer de **+2.5 pips** para soportar el spread y volatilidad interbancaria.
   - **Fase 3 (Trailing Locks Asimétricos):**
     * Al 75% del recorrido $\implies$ Trailing Lock 1 asegurando el **+40%** de la ganancia proyectada.
     * Al 85% del recorrido $\implies$ Trailing Lock 2 asegurando el **+65%** de la ganancia proyectada.
   - **Fase 4 (Front-Run TP al 95%):** Cierre del 100% de la posición remanente al 95% de la distancia para evitar que retrocesos de última hora erosionen el beneficio en el último pip.
2. **Filtro de Exposición en Canasta USD:** Máximo 2 posiciones abiertas simultáneas en pares correlacionados al dólar (`EURUSD`, `GBPUSD`, `AUDUSD`, `XAUUSD`).
3. **Filtro Anti-Caza ATH en Oro (XAUUSD):** Prohibido comprar en Oro si la cotización se encuentra a menos del 0.5% del All-Time High sin un retroceso previo consolidado de 30 a 50 pips.
