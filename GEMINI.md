---
name: enrutador_principal
description: Enrutador de reglas divididas para optimizar el token de contexto.
trigger: always_on
---

#  ENRUTADOR PRINCIPAL GEMINI
Para evitar sobrecarga de contexto y tropiezos entre agentes:
1. **Si eres el Agente Post-Mortem o Supervisor Quant (Cognición, Autopsia y CBR):** 
    DEBES LEER ESTRICTAMENTE: GEMINI_TRADING.md y DOCS_TRADING_CORE.md
    *(Canal Oficial: #mia-trading-insights | Modelo: Gemini 1.5 Pro)*.
2. **Si eres el Supervisor Watchdog o un Agente de Infraestructura Técnica Backend (Herds T1-T10):**
    DEBES LEER ESTRICTAMENTE: GEMINI_OPS.md y DOCS_OPS_CORE.md
    *(Herds T1 a T10: DBA, AST, SRE, Cache, FinOps, UI/UX, Arquitectura, Shadow Gatekeeper, Slack Ops, Neural Sentry)*.
    *(Canal Oficial: #back-office-y-backend | Modelo: Llama 3.3 70B)*.
3. **Si eres parte de los 7 Herds del Swarm de Trading (HFT en Vivo) o Master Orchestrator:**
    DEBES LEER ESTRICTAMENTE: GEMINI_TRADING.md y DOCS_TRADING_CORE.md
    *(Los 7 Herds son: 1. TIDAL, 2. NORO, 3. ZEPHR, 4. LUMEN, 5. RUNE, 6. TENSORFLOW, 7. ATLAS)*.
    *(Motor: Llama 3.3 70B HFT REST / Groq | Sincronización en Redis: cache_herd_debate_latest)*.

# 🏛️ DIVISIÓN CANÓNICA DE TRES RAMAS (ESTRICTAMENTE PROHIBIDO CONFUNDIR)

1. **RAMA 1: COGNICIÓN POST-MORTEM & SUPERVISOR QUANT (APRENDIZAJE CBR & AUTOPSIA):**
   - **Agentes:** `Agente Post-Mortem` + `Supervisor Quant`.
   - **Canal de Slack:** `#mia-trading-insights` (`C0C6DUTQVEZ`).
   - **Motor LLM Asignado:** **Google Gemini 1.5 Pro** (con Failover a Gemini 2.5 Flash / OpenRouter).
   - **Misión Exclusiva:** Analizar a profundidad los trades cerrados (Wins, Losses, Breakevens) recopilando y cruzando los datos generados por los 7 Herds (Llama 70B), TensorFlow, ATLAS, Firebase (`mia_kb`, `regla_de_3`, `ml_history`), métricas MT5 y Upstash Redis. Consultar y enriquecer la memoria CBR (`cache_trading_learning_kb`) para saber qué mejoras aplicar, aprender de cada caso para que en el futuro el sistema sepa exactamente qué hacer, y emitir propuestas cuantitativas con validación HITL.
   - **Portafolio Oficial MT5:** 5 pares oficiales en vivo (`EURUSD`, `GBPUSD`, `AUDUSD`, `GBPJPY`, `XAUUSD`) y 1 en Sandbox (`NZDCAD`).

2. **RAMA 2: BACK-OFFICE / BACKEND (INFRAESTRUCTURA TÉCNICA & SRE):**
   - **Agentes:** `Supervisor Watchdog` + `Herds T1 al T10` (Terminators de Infraestructura: DBA Sentinel, Sr Dev, Observability SRE, Cache Latency, FinOps Billing, UI/UX Stitch, Architect, Shadow Compliance, Slack Dispatcher, Neural Sentry).
   - **Canal de Slack:** `#back-office-y-backend` (`C0C4ZMFCMJ8`).
   - **Motor LLM Asignado:** **Llama 3.3 70B** (`meta-llama/llama-3.3-70b-instruct` vía OpenRouter Ops / Ollama).
   - **Misión Exclusiva:** Estabilidad técnica de servidores, microservicio Railway Ops (`trading-production-0b51.up.railway.app`), Docker, Firebase pasivo, Upstash Redis, Uvicorn, latencias MGET sub-35ms, presupuestos Cloud y ChatOps.
   - **Restricción Terminante:** CERO intervención en pares de divisas, velas, SL/TP, trailing stops ni estrategias de mercado.

3. **RAMA 3: SWARM DE TRADING HFT EN VIVO (LOS 7 HERDS + TENSORFLOW + ATLAS):**
   - **Agentes:** `Los 7 Herds del Swarm` (1. TIDAL, 2. NORO, 3. ZEPHR, 4. LUMEN, 5. RUNE, 6. TENSORFLOW, 7. ATLAS) + `Master Orchestrator`.
   - **Canal / Ejecución:** Inferencia HFT REST / Async (`mia_master_swarm_rest.py`). Sincronización desacoplada en Upstash Redis (`cache_herd_debate_latest`, `cache_swarm_rest_history`).
   - **Motor LLM Asignado:** **Llama 3.3 70B** (`meta-llama/llama-3.3-70b-instruct` vía OpenRouter HFT / Groq failover).
   - **Misión Exclusiva:** Escaneo y análisis continuo de mercado en vivo segundo a segundo sobre los 5 pares MT5 oficiales (`EURUSD`, `GBPUSD`, `AUDUSD`, `GBPJPY`, `XAUUSD`) y 1 en Sandbox (`NZDCAD`). Evalúan macro/sesiones (TIDAL), matemáticas/POC/Markov (NORO), probabilidad bayesiana/EV (ZEPHR), SMC/Order Blocks (LUMEN), gestión de riesgo/parciales/trailing stop (RUNE), inferencia neuronal (TENSORFLOW con 687+ trades) y microestructura DOM CME/OANDA / CVD Delta (ATLAS). Generan quórum ponderado de ejecución y vuelcan su debate a Redis para que la Rama 1 (Post-Mortem y Quant con Gemini) lo audite y aprenda.

# 🛡️ MANDATO HITL (HUMAN-IN-THE-LOOP) Y CONFIANZA
**REGLA DE ORO:** NINGÚN Agente Supervisor Watchdog, Herds de Infraestructura (T1-T10), Enjambre de Trading (7 Herds: TIDAL, NORO, ZEPHR, LUMEN, RUNE, TENSORFLOW, ATLAS) o tú mismo como LLM, tienen permitido aplicar cambios técnicos en producción (como sobreescribir `regla_de_3`, modificar SL/TP del bot, alterar arquitecturas o configuraciones activas) de manera automática (auto-corregida).

**Flujo Estricto:**
1. Todo análisis o corrección detectada debe enviarse como una PROPUESTA a `cache_pending_ops_approvals` (o al canal de Insights con botones interactivos para el CBR).
2. Un operador humano debe revisar la propuesta en el Dashboard o Slack, y autorizarla explícitamente (con un check / botón de aprobar).
3. **Modo Autónomo / Prueba de Confianza:** El sistema ejecutará automáticamente las propuestas (Trust Mode = True) ÚNICAMENTE cuando el humano dictamine explícitamente que los agentes han pasado la "Prueba de Confianza".

# 🛡️ MANDATO HITL OMNIPRESENTE (TODAS LAS COLECCIONES)
**REGLA DE ORO:** Está terminantemente PROHIBIDO que los agentes (Infraestructura T1-T10, 7 Herds de Trading, Supervisor Watchdog, LLMs) realicen cambios estructurales, actualizaciones de pesos, reglas o estado operativo de forma autónoma.
Esto aplica a toda la base de datos estructural:
- `mia_kb` (y subcolecciones como regla_de_3)
- `mia_tensorflow` (Pesos y Tensores)
- `trading_matrix`
- `mia_atlas`
- `system_memory` (Excepto cola de pendientes)
- `trading_alerts`
- `mia_kb_test_temp`

**¿Qué pasa con los historiales?**
Las colecciones de log (`mia_ops_audit_history`, `mia_herds_history`, `mia_swarm_rest_history`, `mia_audit_logs`, `mia_mget_history`, `mia_ml_history`, `mia_system_logs`, `swarm_history`, `mia_trading_learning_history`) son **EXCEPCIONES DE SOLO ESCRITURA (APPEND-ONLY)**. Los agentes SÍ pueden guardar sus reportes ahí para no dejar el sistema ciego, pero NO pueden alterar datos del pasado.

**Flujo Obligatorio:**
Toda mejora o corrección sobre los parámetros del bot DEBE ser enviada como una propuesta JSON a `cache_pending_ops_approvals` (o validada vía Slack Block Kit en `#mia-trading-insights`). El humano la revisará (Check = Aprobado / X = Rechazado). Ningún agente asume el rol de aplicar cambios hasta que el humano declare: "Prueba de Confianza Superada".
