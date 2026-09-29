# REGLAS DE NEGOCIO Y TRADING (FRONT-OFFICE)

---
name: modo_shadow_bloqueo_mt5
description: Regla de operabilidad en Modo Shadow (Paper Trading) con bloqueo estricto de MetaTrader 5 y asignación de tickets virtuales.
trigger: always_on
---

# 🛡️ REGLA: MODO SHADOW GLOBAL Y TICKETS VIRTUALES (#SHADOW_XXXXXX)
1. **Bloqueo Estricto de MetaTrader 5:** Durante la ventana de calibración de 1 a 2 semanas, la ejecución real en MetaQuotes está BLOQUEADA (`SHADOW_MODE_GLOBAL = True`). Queda estrictamente prohibido enviar órdenes con dinero real.
2. **Asignación de Tickets Virtuales:** Cada trade analizado o simulado por los Enjambres Herds, TensorFlow o ATLAS debe asignarse a un ticket virtual con formato `#SHADOW_XXXXXX` correlacionado con el ticket real.
3. **Análisis Contrafactual ("What-If"):** Toda comparación entre la Rama Champion (Herds tradicionales) y la Rama Challenger (ATLAS con CVD Delta + ATR + DOM) se almacena en los slots `cache_shadow_trades` y `cache_mia_atlas` de Upstash Redis para no contaminar el historial productivo ni generar errores 429 en Firebase.

---
name: malla_7_herds_desacoplada
description: Regla para la arquitectura de 7 Herds desacoplados, Quórum Master y prevención de 429/404 en OpenRouter.
trigger: always_on
---

# 🐝 REGLA: MALLA DE 7 HERDS DESACOPLADOS Y QUÓRUM MASTER
1. **Taxonomía Unívoca de Especialización (Single Responsibility):** Prohibido fusionar o mezclar roles en un solo Herd. La malla consta de 7 agentes independientes:
   - `HERD 1 (TIDAL)`: Macro Trend & Liquidez de Sesiones.
   - `HERD 2 (NORO)`: Matemáticas Cuantitativas, POC y Markov.
   - `HERD 3 (ZEPHR)`: Probabilidad Bayesiana y Expected Value.
   - `HERD 4 (LUMEN)`: Smart Money Concepts (SMC) & Order Blocks.
   - `HERD 5 (RUNE)`: Gestión de Riesgo Defensivo y Sizing.
   - `HERD 6 (TENSORFLOW)`: Inferencia Neuronal Continua (Railway).
   - `HERD 7 (ATLAS)`: Microestructura DOM CME/OANDA, CVD Delta y Servidor MCP.
   - `MASTER ORCHESTRATOR`: Gatekeeper de Quórum Calificado Ponderado ($\sum w_i \cdot v_i \ge 0.70$).
2. **Prevención Anti-429 y Anti-404:** Toda la deliberación inter-agente debe ejecutarse en un solo ciclo atómico a OpenRouter con triple failover (`meta-llama/llama-3.3-70b-instruct` -> `deepseek/deepseek-chat` -> `meta-llama/llama-3.1-70b-instruct`). Cero tokens de LLM para cómputo determinista (TF, NORO y ATLAS MCP corren en C++/Python nativo).

---
name: homologacion_estricta_mt5_dashboard
description: Regla de paridad absoluta entre la cuenta real de MetaTrader 5 y el Dashboard Web (Anti-Discrepancia).
trigger: always_on
---

# 🎯 REGLA: HOMOLOGACIÓN ESTRICTA MT5 VS DASHBOARD (CERO DISCREPANCIA)
1. **Paridad Total con Broker:** Las posiciones mostradas en el Dashboard (`Posiciones Activas / Trades en Vivo (MT5)`) y en el slot `cache_mt5` deben coincidir exactamente con las órdenes abiertas reales en MetaTrader 5.
2. **Prohibición de Órdenes Fantasma:** Si una orden cierra o se liquida en MT5 (ej. XAUUSD), queda estrictamente prohibido mantenerla en `operaciones_activas`. Debe ser depurada de inmediato de la memoria viva y archivada en `cache_hist_mt5`.
3. **Precisión Matemática y Redondeo:** El flotante neto, balance, equidad y márgenes deben recalcularse dinámicamente y con estricto redondeo a 2 decimales (`round(val, 2)`), homologados con la moneda de la cuenta de trading.

---
name: dinamismo_regla_de_3_y_supervisor
description: Regla para la actualización perpetua de la Regla de 3 y el rol del Agente Supervisor Watchdog.
trigger: always_on
---

# 👁️ REGLA: REGLA DE 3 DINÁMICA Y AGENTE SUPERVISOR WATCHDOG
1. **Regla de 3 Dinámica:** La colección `mia_kb/regla_de_3` y el slot `cache_regla_de_3` no pueden permanecer con fechas estáticas. El Top 1, Top 2 y Top 3 deben recalibrarse automáticamente según el WinRate real de `indicadores_impacto`, actualizando el timestamp `ultima_actualizacion` en tiempo real.
2. **MIA Supervisor Watchdog (`mia_supervisor_agent.py`):** Un agente autónomo en segundo plano monitorea la integridad de los datos, previene ráfagas masivas duplicadas de reportes HFT en Firestore y mantiene sincronizado el Dashboard sin necesidad de intervención manual o nuevos prompts.

---
name: arquitectura_dual_swarms_desacoplados
description: Regla de desacoplamiento estricto entre Enjambre de Trading y Enjambre de Infraestructura / Ops.
trigger: always_on
---

# ⚡ REGLA: ARQUITECTURA DUAL DE ENJAMBRES (TRADING VS SYSTEM OPS)
1. **Desacoplamiento Front-Office / Back-Office:** Queda estrictamente prohibido mezclar tareas de infraestructura, sanitización de base de datos o cómputo de métricas de UI dentro del Enjambre de Trading de Mercado (`mia_master_swarm_rest.py`).
2. **Enjambre de Trading (`MIA_MARKET_TRADING_SWARM`):** 7 Herds Especializados (TIDAL, NORO, ZEPHR, LUMEN, RUNE, TENSORFLOW, ATLAS) + MASTER Gatekeeper enfocados exclusivamente en la lectura de mercado, SMC, DOM, CVD Delta y deliberación a OpenRouter.
3. **Enjambre de Operaciones (`MIA_SYSTEM_OPS_SWARM`):** 4 Herds Técnicos (HERD T1 DB_SYNC, HERD T2 KB_ENGINE, HERD T3 KPI_ANALYTICS, HERD T4 DEVOPS_HEALTH) bajo el mando del `WATCHDOG SUPERVISOR`.
4. **Cero Tokens LLM en Infraestructura:** El Enjambre de Operaciones corre en Python nativo determinista, consumiendo cero tokens de LLM y cero cuota de Firebase mediante Upstash Redis.

---
name: estricta_separacion_shadow_y_filtro_noticias
description: Regla para evitar la contaminacion cruzada de metricas Shadow a Produccion y gobernar el Filtro de Noticias.
trigger: always_on
---

# ?? REGLA: SEPARACI�N STRICTA SHADOW MODE Y FILTRO DE NOTICIAS
1. **Contaminaci�n Cero a Producci�n:** Queda ESTRICTAMENTE PROHIBIDO que el Agente Supervisor o cualquier script autom�tico inyecte pesos, m�tricas o indicadores provenientes de TensorFlow, ATLAS o Enjambres HFT (Herds) hacia las tablas de producci�n (ej. mia_kb/regla_de_3) mientras se encuentren en periodo de "Shadow Mode" o calibraci�n.
2. **Tablas Aisladas:** El aprendizaje en la sombra debe escribirse EXCLUSIVAMENTE en sus colecciones y cach�s dedicadas (cache_mia_atlas, cache_mia_tensorflow, cache_shadow_trades, cache_herd_debate_latest).
3. **Filtro de Noticias Trampa:** El nodo iltro_trampa_noticias (que rige los 15 minutos previos y 5 posteriores a una noticia) es una regla estructural y est�tica de seguridad. **NO debe ser alterada din�micamente por Machine Learning**. Si los Enjambres desean probar diferentes tiempos de bloqueo pre-noticia, lo har�n simulando en sus propias tablas, sin afectar la producci�n.
4. **Consulta Anti-429 Integral:** El iltro_trampa_noticias y la 
egla_de_3 deben ser consultados 100% mediante Upstash Redis (cache_regla_de_3). Cero consultas directas a Firebase Firestore al momento de ejecutar un trade.
5. **Protocolo de Migraci�n (Slack):** Cuando termine la ventana de calibraci�n (1-2 semanas), la decisi�n de pasar a TensorFlow/ATLAS a Producci�n (hacer el "Switch") es clasificada como [REQUIERE APROBACI�N HUMANA ??]. El Supervisor debe solicitar autorizaci�n obligatoria en Slack antes de tocar la base de datos principal de Firebase.

