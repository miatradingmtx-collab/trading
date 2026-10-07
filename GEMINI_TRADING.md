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

#  REGLA: REGLA DE 3 DINMICA Y AGENTE SUPERVISOR WATCHDOG
1. **Regla de 3 Dinmica:** La coleccin `mia_kb/regla_de_3` y el slot `cache_regla_de_3` no pueden permanecer con fechas estticas. El Top 1, Top 2 y Top 3 deben recalibrarse automticamente segn el WinRate real de `indicadores_impacto`, actualizando el timestamp `ultima_actualizacion` en tiempo real.
2. **MIA Supervisor Watchdog (`mia_supervisor_agent.py`):** Un agente autnomo en segundo plano monitorea la integridad de los datos, previene rfagas masivas duplicadas de reportes HFT en Firestore y mantiene sincronizado el Dashboard sin necesidad de intervencin manual o nuevos prompts.

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
