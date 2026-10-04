# REGLAS DE INFRAESTRUCTURA Y BACK-OFFICE (OPS)
---

name: actualizacion_documentacion_continua

description: Regla para asegurar que todos los cambios se guarden en la base de conocimientos.

trigger: always_on

---

# ?? Regla de Documentacin Automtica (MIA Core)

Como Inteligencia Artificial, tienes la directriz estricta de mantener la Base de Conocimientos (Obsidian) siempre sincronizada. 

Cada vez que realices o disees:

1. **Modificacin de Arquitectura:** (Ej. Enjambres, Failovers, Firebase).

2. **Modelados Matematicos:** (Ej. area Bajo la Curva, Morgan, V_M, Montecarlo).

3. **Optimizaciones:** (Ej. Criosueo, Cache Redis, Latencia).

**Instruccin de Ejecucin:**

Debes de manera autonoma editar el archivo DOCUMENTACION_MIA_CORE.md (o el nodo de trading correspondiente) e inyectar un resumen detallado del cambio, la fecha y la formula aplicada. Tras hacerlo, realiza el Commit y Push. **No le preguntes al usuario si debe guardarse, hazlo por defecto y avisale cuando este terminado.**

---

name: reportes_desde_cache

description: Regla para evitar bloqueos 429 en Firebase usando Upstash.

trigger: always_on

---

# = Regla de Extraccin de Reportes (Anti-429)

Como Inteligencia Artificial, tienes PROHIBIDO realizar consultas iterativas masivas o descargas de colecciones completas en Firebase (ej. mia_audit_logs, 	rading_matrix) para generar reportes estadsticos, de ML o de rankings.

**Instruccin de Ejecucin:**

Para obtener datos de reportes, rankings, pesos de Machine Learning (ML) o mtricas de PNL, DEBES conectarte exclusivamente a la cach de **Upstash Redis**.

El endpoint o variable que almacena estos reportes pre-procesados est en Upstash, evitando asi agotar la cuota de lecturas (429 Quota Exceeded) en el plan Spark de Firebase.

---

name: arquitectura_tensorflow_cloud

description: Regla de CI/CD para TensorFlow y Upstash

trigger: always_on

---

#  ARQUITECTURA TENSORFLOW Y UPSTASH (CI/CD)

1. **CI/CD Cloud-Native:** Toda la IA y el modelo predictivo corre exclusivamente en Railway. Prohibido ejecutar scripts de entrenamiento local.

2. **TensorFlow Deep Learning:** El cerebro de Mia migr a un Modelo Secuencial (Capas Densas, ReLU, Dropout, Sigmoid).

3. **Desacoplamiento (Anti-429):** TensorFlow entrena leyendo de cache_hist_mt5 (Upstash) y guarda el cerebro en cache_mia_tensorflow (Upstash).

4. **Swarm HFT:** Los Enjambres consultan la probabilidad neuronal directamente desde Upstash, consumiendo cero cuota de Firebase.

---

name: actualizacion_documentacion_continua

description: Regla para asegurar que todos los cambios se guarden en la base de conocimientos.

trigger: always_on

---

# ?? Regla de Documentacin Automtica (MIA Core)

Como Inteligencia Artificial, tienes la directriz estricta de mantener la Base de Conocimientos (Obsidian) siempre sincronizada. 

Cada vez que realices o disees:

1. **Modificacin de Arquitectura:** (Ej. Enjambres, Failovers, Firebase).

2. **Modelados Matematicos:** (Ej. area Bajo la Curva, Morgan, V_M, Montecarlo).

3. **Optimizaciones:** (Ej. Criosueo, Cache Redis, Latencia).

**Instruccin de Ejecucin:**

Debes de manera autonoma editar el archivo DOCUMENTACION_MIA_CORE.md (o el nodo de trading correspondiente) e inyectar un resumen detallado del cambio, la fecha y la formula aplicada. Tras hacerlo, realiza el Commit y Push. **No le preguntes al usuario si debe guardarse, hazlo por defecto y avisale cuando este terminado.**

---

name: reportes_desde_cache

description: Regla para evitar bloqueos 429 en Firebase usando Upstash.

trigger: always_on

---

# = Regla de Extraccin de Reportes (Anti-429)

Como Inteligencia Artificial, tienes PROHIBIDO realizar consultas iterativas masivas o descargas de colecciones completas en Firebase (ej. mia_audit_logs, 	rading_matrix) para generar reportes estadsticos, de ML o de rankings.

**Instruccin de Ejecucin:**

Para obtener datos de reportes, rankings, pesos de Machine Learning (ML) o mtricas de PNL, DEBES conectarte exclusivamente a la cach de **Upstash Redis**.

El endpoint o variable que almacena estos reportes pre-procesados est en Upstash, evitando asi agotar la cuota de lecturas (429 Quota Exceeded) en el plan Spark de Firebase.

---

name: arquitectura_tensorflow_cloud

description: Regla de CI/CD para TensorFlow y Upstash

trigger: always_on

---

#  ARQUITECTURA TENSORFLOW Y UPSTASH (CI/CD)

1. **CI/CD Cloud-Native:** Toda la IA y el modelo predictivo corre exclusivamente en Railway. Prohibido ejecutar scripts de entrenamiento local.

2. **TensorFlow Deep Learning:** El cerebro de Mia migr a un Modelo Secuencial (Capas Densas, ReLU, Dropout, Sigmoid).

3. **Desacoplamiento (Anti-429):** TensorFlow entrena leyendo de cache_hist_mt5 (Upstash) y guarda el cerebro en cache_mia_tensorflow (Upstash).

4. **Swarm HFT:** Los Enjambres consultan la probabilidad neuronal directamente desde Upstash, consumiendo cero cuota de Firebase.

---
name: deprecacion_crewai_langchain
description: Regla para migrar de CrewAI/Langchain al nuevo framework moderno.
trigger: always_on
---

#  REGLA ESTRICTA: MIGRACIN DE CREWAI / LANGCHAIN
Como Inteligencia Artificial, tienes PROHIBIDO sugerir, instanciar o construir arquitecturas nuevas utilizando crewai o langchain. 
Estas libreras son consideradas LEGACY (Antiguas). A partir de ahora, todo el sistema de agentes, herramientas y orquestacin debe construirse exclusivamente utilizando el nuevo framework moderno ("Penriye Reset" / Pydantic AI / PraisonAI). Asegrate de validar la sintaxis correcta del nuevo framework al refactorizar o crear nuevos agentes.

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
name: desacoplamiento_canonico_slots_atomicos
description: Regla de desacoplamiento por documento cannico atmico (Anti-Split-Brain y MGET sub-35ms).
trigger: always_on
---

#  REGLA: SLOTS CANNICOS ATMICOS EN UPSTASH (ANTI-SPLIT-BRAIN)
1. **Desacoplamiento Atmico Obligatorio:** Los datos requeridos por los Enjambres Herds deben desacoplarse por **Documento Cannico Especfico** (`cache_mt5`, `cache_mia_tensorflow`, `cache_trading_matrix`, `cache_researcher_insights`, `cache_regla_de_3`).
2. **Prohibicin de Duplicidad Hbrida:** Queda estrictamente prohibido guardar un documento dentro de una megatabla compuesta en Redis si ya existe como slot individual atmico.
3. **Consumo Atmico va MGET:** Toda deliberacin inter-agente debe recuperar sus insumos en un nico viaje de red HTTP (`GET /mget/...`), garantizando latencia $< 35\text{ ms}$, consumo de memoria optimizado y paridad absoluta de informacin.

---
name: desacoplamiento_canonico_slots_atomicos
description: Regla de desacoplamiento por documento cannico atmico (Anti-Split-Brain y MGET sub-35ms).
trigger: always_on
---

#  REGLA: SLOTS CANNICOS ATMICOS EN UPSTASH (ANTI-SPLIT-BRAIN)
1. **Desacoplamiento Atmico Obligatorio:** Los datos requeridos por los Enjambres Herds deben desacoplarse por **Documento Cannico Especfico** (`cache_mt5`, `cache_mia_tensorflow`, `cache_trading_matrix`, `cache_researcher_insights`, `cache_regla_de_3`).
2. **Prohibicin de Duplicidad Hbrida:** Queda estrictamente prohibido guardar un documento dentro de una megatabla compuesta en Redis si ya existe como slot individual atmico.
3. **Consumo Atmico va MGET:** Toda deliberacin inter-agente debe recuperar sus insumos en un nico viaje de red HTTP (`GET /mget/...`), garantizando latencia $< 35\text{ ms}$, consumo de memoria optimizado y paridad absoluta de informacin.

---
name: malla_10_herds_ops_y_watchdog
description: Regla de arquitectura para la Malla de 10 Herds de Operaciones (Back-Office) y el Supervisor General Watchdog.
trigger: always_on
---

# 🛡️ REGLA: MALLA DE 10 HERDS TÉCNICOS Y WATCHDOG SUPERVISOR (BACK-OFFICE)
1. **Taxonomía de los 10 Herds Técnicos Especializados:**
   - `HERD T1 (DBA_SENTINEL)`: Integridad de Firestore/Upstash, normalización, sanitización anti-null/NaN, depuración de órdenes fantasma y vectorización 20D para TensorFlow.
   - `HERD T2 (SENIOR_CODE_AUDITOR)`: Auditoría sintáctica profunda con AST, imports limpios (cero librerías legadas), variables no declaradas, UTF-8 estricto y acoplamiento frontend/backend.
   - `HERD T3 (OBSERVABILITY_SRE)`: Monitoreo activo de los 3 microservicios Railway (927a MT5, 1fd4 Brain, 0b51 Ops), OpenRouter, Servidores MCP (`/mcp` y `/mcp/ops`), Upstash y GitHub.
   - `HERD T4 (CACHE_LATENCY_SPECIALIST)`: Desacoplamiento canónico por documento, garantía de latencia MGET $< 35\text{ ms}$ y paridad perpetua de la Regla de 3.
   - `HERD T5 (FINOPS_BILLING_CONTROLLER)`: Control de presupuestos en modo Spark (Railway, OpenRouter, MetaAPI, Firebase Spark limit), con alertas preventivas a 48 horas con montos exactos y enlaces directos de pago.
   - `HERD T6 (UIUX_STITCH_DESIGNER)`: Diseño frontend con Google Stitch y Plotly Dark Theme; extracción de CSS/HTML modular. Auditoría visual de `/brain`, `/` y `/dashboard`.
   - `HERD T7 (ARCHITECT_DIAGRAMMER_INNOVATOR)`: Arquitectura del sistema, topología de 3 microservicios desacoplados y diagramas Mermaid/SVG vivos en tiempo real.
   - `HERD T8 (SHADOW_COMPLIANCE_GATEKEEPER)`: Candado institucional de ejecución (SHADOW_MODE_GLOBAL = True) y custodia estricta del filtro de noticias (15m Pre / 5m Post).
   - `HERD T9 (SLACK_OPS_DISPATCHER)`: Aislamiento total de canal (#back-office-y-backend exclusivo; #mia-chat silenciado) y despacho interactivo con Block Kit y checkboxes.
   - `HERD T10 (SWARM_NEURAL_SENTRY)`: Vigilancia de salud, precisión y latencia de TensorFlow Deep Learning ($> 85\%$) y de los 7 Herds de Trading HFT.
2. **Supervisor General Watchdog Master:**
   - Ejerce liderazgo senior integral. Ejecuta los 10 Herds en Python determinista (0 tokens de LLM), evalúa propuestas cognitivamente con Llama 3.3 70B Grounded y realiza el triage clasificando en:
     - `[AUTO-CORREGIDO EN CALIENTE ⚡]`: Acciones seguras ejecutadas de forma autónoma o ratificadas en Google Antigravity.
     - `[REQUIERE APROBACIÓN HUMANA ⭐]`: Propuestas de Score >= 85 despachadas a Slack (`#back-office-y-backend`) con checkboxes y botones interactivos.
     - `[OBSERVADAS / DESCARTADAS ⚠️]`: Propuestas con Score < 85 con justificación técnica de descarte.

---
name: homologacion_antigravity_cloud_openrouter
description: Regla de homologacin entre agentes locales de Antigravity y la ejecucin autnoma en Railway con OpenRouter.
trigger: always_on
---

#  REGLA: HOMOLOGACIN ANTIGRAVITY (LOCAL) VS OPENROUTER (RAILWAY CLOUD)
1. **Paridad Cognitiva y de Contexto:** Los prompts ejecutados en local va Antigravity y los workers autnomos en Railway comparten la misma taxonoma, reglas de negocio y acceso a los slots atmicos de Upstash Redis.
2. **Patrn Hbrido (Deterministic First + Cognition-on-Demand):**
   - El 95% de las auditoras de infraestructura corren en Python nativo a costo cero ($0.00 USD).
   - Ante excepciones de cdigo o fallos complejos en la nube, el sistema invoca quirrgicamente a OpenRouter (`Claude 3.5 Sonnet`, `DeepSeek V3` o `Llama 3.3 70B`) para generar diagnsticos y parches automticos con la misma capacidad analtica que Antigravity.
3. **Estndar de Modernizacin Frontend (HERD T6):** Toda mejora o rediseo para `/dashboard` (`https://trading-production-927a.up.railway.app/dashboard`) debe adoptar la esttica financiera de grficos interactivos estilo Plotly Dark, preservando intactos el men lateral, balances, mrgenes, floating PnL, regla de 3 y tabla de posiciones de MT5.

---
name: homologacion_antigravity_cloud_openrouter
description: Regla de homologacin entre agentes locales de Antigravity y la ejecucin autnoma en Railway con OpenRouter.
trigger: always_on
---

#  REGLA: HOMOLOGACIN ANTIGRAVITY (LOCAL) VS OPENROUTER (RAILWAY CLOUD)
1. **Paridad Cognitiva y de Contexto:** Los prompts ejecutados en local va Antigravity y los workers autnomos en Railway comparten la misma taxonoma, reglas de negocio y acceso a los slots atmicos de Upstash Redis.
2. **Patrn Hbrido (Deterministic First + Cognition-on-Demand):**
   - El 95% de las auditoras de infraestructura corren en Python nativo a costo cero ($0.00 USD).
   - Ante excepciones de cdigo o fallos complejos en la nube, el sistema invoca quirrgicamente a OpenRouter (`Claude 3.5 Sonnet`, `DeepSeek V3` o `Llama 3.3 70B`) para generar diagnsticos y parches automticos con la misma capacidad analtica que Antigravity.
3. **Estndar de Modernizacin Frontend (HERD T6):** Toda mejora o rediseo para `/dashboard` (`https://trading-production-927a.up.railway.app/dashboard`) debe adoptar la esttica financiera de grficos interactivos estilo Plotly Dark, preservando intactos el men lateral, balances, mrgenes, floating PnL, regla de 3 y tabla de posiciones de MT5.

---
name: strict_human_in_the_loop_fase1
description: Regla mandatoria de Fase 1 para requerir notificacin transparente de cada agente y aprobacin humana obligatoria en Slack antes de cualquier cambio.
trigger: always_on
---

# 🛡️ REGLA: PROTOCOLO ESTRICTO HUMAN-IN-THE-LOOP (FASE 1 - ENTRENAMIENTO)
1. **Prohibición Total de Auto-Ejecución (Modo Entrenamiento):** En esta Fase 1, TODOS los agentes técnicos (HERD T1 a T10) y el Supervisor Watchdog están en modo de entrenamiento y aprendizaje progresivo. Queda TERMINANTEMENTE PROHIBIDO que cualquier agente ejecute cambios, reentrenamientos, mutaciones de base de datos o parches por sí mismo.
2. **Obligatoriedad de Checkboxes en Slack:** Antes de aplicar cualquier cambio o issue detectado, es OBLIGATORIO preguntarle al Padre en Slack (#back-office-y-backend) mediante CHECKBOXES individuales ([ ]) para que él revise, evalúe y seleccione cuáles son correctos y seguros de aplicar.
3. **Verificación Previa de Homologación de Caché:** Ningún cambio puede aplicarse a ciegas sin verificar que la caché (Upstash) y las fuentes canónicas estén 100% homologadas (evitando errores como reentrenar sobre buffers recientes en lugar del dataset histórico).
4. **Control por Botones Interactivos en Slack:**
   - [Aprobar Seleccionadas ☑️]: Aplica única y exclusivamente las propuestas que el Padre haya marcado en los checkboxes.
   - [Aprobar Todas ✅]: Aplica el lote solo bajo expresa confirmación.
   - [Rechazar / Mantener Actual ⛔]: Purga la cola, mantiene el sistema intacto y registra el precedente en la KB de aprendizaje CBR.
   - [Forzar Resync 🔄]: Re-ejecuta la auditoría en vivo para verificar el estado de los 10 Herds.
5. **Evolución Progresiva a Fase 2 (Confianza Acumulada):** Los agentes solo podrán auto-ejecutar remediaciones cuando hayan superado la prueba de confianza estadística (+1 por aprobación humana verificada, -2 por descarte). Mientras tanto, la regla de selección humana por checkbox aplica sin excepción para TODOS los issues.

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


---
name: homologacion_cbr_knowledge_base
description: Protocolo de diagnostico clinico del Watchdog mediante la consulta del Case-Based Reasoning (CBR).
trigger: always_on
---

# 🧠 REGLA: CONSULTA OBLIGATORIA DEL CBR (CASE-BASED REASONING)
1. **El CBR es la Enciclopedia Medica:** Todos los errores fatales, crash loops y anomalias que el ecosistema ha resuelto en el pasado se documentan en archivos .md dentro del directorio Docuementos/ (ej. CBR_MASTER_KNOWLEDGE_BASE.md).
2. **Protocolo del Watchdog y Herds T:** 
   - Antes de proponer una solucion o emitir un reporte de 'Cero cambios criticos' tras una caida de sistema, el Watchdog y los agentes de infraestructura (Herds T1-T10) DEBEN leer el directorio Docuementos/ y buscar cualquier documento que empiece con CBR_.
   - Si la firma del error actual (logs de Railway, Uvicorn, Docker, Upstash) coincide con un registro CBR, el Watchdog extraera la 'Solucion Inmediata' (Playbook) del CBR.
3. **Delegacion Asignada:** Una vez leido el CBR, el Watchdog asignara el script de mitigacion al agente T correspondiente (ej. T3 Observability o T1) para que ejecute la cura con precision milimetrica sin inventar codigo nuevo.


# 🛡️ MANDATO HITL (HUMAN-IN-THE-LOOP) Y CONFIANZA
**REGLA DE ORO:** NINGÚN Agente Supervisor, Enjambre (T1-T10) o tú mismo como LLM, tienen permitido aplicar cambios técnicos en producción (como sobreescribir `regla_de_3`, modificar SL/TP del bot, alterar arquitecturas o configuraciones activas) de manera automática (auto-corregida).

**Flujo Estricto:**
1. Todo análisis o corrección detectada debe enviarse como una PROPUESTA a `cache_pending_ops_approvals`.
2. Un operador humano debe revisar la propuesta en el Dashboard o Slack, y autorizarla explícitamente (con un check / botón de aprobar).
3. **Modo Autónomo / Prueba de Confianza:** El sistema ejecutará automáticamente las propuestas (Trust Mode = True) ÚNICAMENTE cuando el humano dictamine explícitamente que los T y el Supervisor han pasado la `Prueba de Confianza`.
4. Mientras la Prueba de Confianza no sea certificada, debes forzar `TRUST_MODE_ENABLED = False` en el código (ya implementado en mia_supervisor_agent.py y mia_system_ops_swarm.py).
