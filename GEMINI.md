---
name: actualizacion_documentacion_continua
description: Regla para asegurar que todos los cambios se guarden en la base de conocimientos.
trigger: always_on
---

# ?? Regla de Documentación Automotica (MIA Core)

Como Inteligencia Artificial, tienes la directriz estricta de mantener la Base de Conocimientos (Obsidian) siempre sincronizada. 

Cada vez que realices o diseñes:
1. **Modificación de Arquitectura:** (Ej. Enjambres, Failovers, Firebase).
2. **Modelados Matematicos:** (Ej. area Bajo la Curva, Morgan, V_M, Montecarlo).
3. **Optimizaciones:** (Ej. Criosueño, Cache Redis, Latencia).

**Instrucción de Ejecución:**
Debes de manera autonoma editar el archivo DOCUMENTACION_MIA_CORE.md (o el nodo de trading correspondiente) e inyectar un resumen detallado del cambio, la fecha y la formula aplicada. Tras hacerlo, realiza el Commit y Push. **No le preguntes al usuario si debe guardarse, hazlo por defecto y avisale cuando este terminado.**

---
name: reportes_desde_cache
description: Regla para evitar bloqueos 429 en Firebase usando Upstash.
trigger: always_on
---

# =؀� Regla de Extracci�n de Reportes (Anti-429)

Como Inteligencia Artificial, tienes PROHIBIDO realizar consultas iterativas masivas o descargas de colecciones completas en Firebase (ej. mia_audit_logs, 	rading_matrix) para generar reportes estad�sticos, de ML o de rankings.

**Instrucci�n de Ejecuci�n:**
Para obtener datos de reportes, rankings, pesos de Machine Learning (ML) o m�tricas de PNL, DEBES conectarte exclusivamente a la cach� de **Upstash Redis**.
El endpoint o variable que almacena estos reportes pre-procesados est� en Upstash, evitando as� agotar la cuota de lecturas (429 Quota Exceeded) en el plan Spark de Firebase.



---
name: arquitectura_tensorflow_cloud
description: Regla de CI/CD para TensorFlow y Upstash
trigger: always_on
---

# 🧠 ARQUITECTURA TENSORFLOW Y UPSTASH (CI/CD)
1. **CI/CD Cloud-Native:** Toda la IA y el modelo predictivo corre exclusivamente en Railway. Prohibido ejecutar scripts de entrenamiento local.
2. **TensorFlow Deep Learning:** El cerebro de Mia migró a un Modelo Secuencial (Capas Densas, ReLU, Dropout, Sigmoid).
3. **Desacoplamiento (Anti-429):** TensorFlow entrena leyendo de cache_hist_mt5 (Upstash) y guarda el cerebro en cache_mia_tensorflow (Upstash).
4. **Swarm HFT:** Los Enjambres consultan la probabilidad neuronal directamente desde Upstash, consumiendo cero cuota de Firebase.

---
name: deprecacion_crewai_langchain
description: Regla para migrar de CrewAI/Langchain al nuevo framework moderno.
trigger: always_on
---

# 🚫 REGLA ESTRICTA: MIGRACIÓN DE CREWAI / LANGCHAIN
Como Inteligencia Artificial, tienes PROHIBIDO sugerir, instanciar o construir arquitecturas nuevas utilizando crewai o langchain. 
Estas librerías son consideradas LEGACY (Antiguas). A partir de ahora, todo el sistema de agentes, herramientas y orquestación debe construirse exclusivamente utilizando el nuevo framework moderno ("Penriye Reset" / Pydantic AI / PraisonAI). Asegúrate de validar la sintaxis correcta del nuevo framework al refactorizar o crear nuevos agentes.

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
name: desacoplamiento_canonico_slots_atomicos
description: Regla de desacoplamiento por documento canónico atómico (Anti-Split-Brain y MGET sub-35ms).
trigger: always_on
---

# 📦 REGLA: SLOTS CANÓNICOS ATÓMICOS EN UPSTASH (ANTI-SPLIT-BRAIN)
1. **Desacoplamiento Atómico Obligatorio:** Los datos requeridos por los Enjambres Herds deben desacoplarse por **Documento Canónico Específico** (`cache_mt5`, `cache_mia_tensorflow`, `cache_trading_matrix`, `cache_researcher_insights`, `cache_regla_de_3`).
2. **Prohibición de Duplicidad Híbrida:** Queda estrictamente prohibido guardar un documento dentro de una megatabla compuesta en Redis si ya existe como slot individual atómico.
3. **Consumo Atómico vía MGET:** Toda deliberación inter-agente debe recuperar sus insumos en un único viaje de red HTTP (`GET /mget/...`), garantizando latencia $< 35\text{ ms}$, consumo de memoria optimizado y paridad absoluta de información.

---
name: malla_6_herds_ops_y_watchdog
description: Regla de arquitectura para la Malla de 6 Herds de Operaciones (Back-Office) y el Supervisor General Watchdog.
trigger: always_on
---

# 🛠️ REGLA: MALLA DE 6 HERDS TÉCNICOS Y WATCHDOG SUPERVISOR (BACK-OFFICE)
1. **Taxonomía de los 6 Herds Técnicos Especializados:**
   - `HERD T1 (DBA_SENTINEL)`: Integridad de Firestore/Upstash, normalización, sanitización anti-null/NaN y depuración de órdenes fantasma.
   - `HERD T2 (SENIOR_CODE_AUDITOR)`: Auditoría sintáctica profunda con AST, imports limpios (cero CrewAI/LangChain), variables no declaradas y codificación UTF-8 estricta.
   - `HERD T3 (OBSERVABILITY_SRE)`: Monitoreo activo de endpoints de Railway (1fd4 y 927a), OpenRouter, Servidores MCP (`/mcp` y `/mcp/ops`), Upstash y GitHub.
   - `HERD T4 (CACHE_LATENCY_SPECIALIST)`: Desacoplamiento canónico por documento, garantía de latencia MGET $< 35\text{ ms}$ y paridad perpetua de la Regla de 3.
   - `HERD T5 (FINOPS_BILLING_CONTROLLER)`: Control de presupuestos en modo Spark (Railway, OpenRouter, MetaAPI, Firebase Spark limit), con alertas preventivas a 48 horas con montos exactos y enlaces directos de pago.
   - `HERD T6 (UIUX_DASHBOARD_DESIGNER)`: Auditoría visual de `/brain` (Red Neuronal), `/` (Enjambres 3D) y `/dashboard` (KPIs estilo Plotly institucional sin pérdida de datos ni menús existentes).
2. **Supervisor General Watchdog Master:**
   - Ejerce liderazgo senior integral. Ejecuta los 6 Herds en Python determinista (0 tokens de LLM) y realiza el triage clasificando en:
     - `[AUTO-CORREGIDO EN CALIENTE ✅]`: Acciones seguras ejecutadas de forma autónoma.
     - `[REQUIERE APROBACIÓN HUMANA ⚠️]`: Pagos de FinOps, propuestas de rediseño UI/UX o migraciones de base de datos despachadas a Slack (`#back-office-y-backend`) con botones interactivos.

---
name: homologacion_antigravity_cloud_openrouter
description: Regla de homologación entre agentes locales de Antigravity y la ejecución autónoma en Railway con OpenRouter.
trigger: always_on
---

# 🧠 REGLA: HOMOLOGACIÓN ANTIGRAVITY (LOCAL) VS OPENROUTER (RAILWAY CLOUD)
1. **Paridad Cognitiva y de Contexto:** Los prompts ejecutados en local vía Antigravity y los workers autónomos en Railway comparten la misma taxonomía, reglas de negocio y acceso a los slots atómicos de Upstash Redis.
2. **Patrón Híbrido (Deterministic First + Cognition-on-Demand):**
   - El 95% de las auditorías de infraestructura corren en Python nativo a costo cero ($0.00 USD).
   - Ante excepciones de código o fallos complejos en la nube, el sistema invoca quirúrgicamente a OpenRouter (`Claude 3.5 Sonnet`, `DeepSeek V3` o `Llama 3.3 70B`) para generar diagnósticos y parches automáticos con la misma capacidad analítica que Antigravity.
3. **Estándar de Modernización Frontend (HERD T6):** Toda mejora o rediseño para `/dashboard` (`https://trading-production-927a.up.railway.app/dashboard`) debe adoptar la estética financiera de gráficos interactivos estilo Plotly Dark, preservando intactos el menú lateral, balances, márgenes, floating PnL, regla de 3 y tabla de posiciones de MT5.






