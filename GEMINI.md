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


