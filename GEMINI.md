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

# 🛡️ REGLA DE ORO: FILTRO ANTI-SUERTE INSTITUCIONAL PARA LA REGLA DE 3 (>= 50 TRADES)
**REGLA INQUEBRANTABLE:** Queda terminantemente PROHIBIDO que cualquier Agente LLM, Supervisor Quant, Agente Post-Mortem, Watchdog de Infraestructura (T1-T10) o algoritmo de Machine Learning altere o proponga alterar la 'Regla de 3' (`mia_kb/regla_de_3` o `cache_regla_de_3`) basándose en rachas de corto plazo, el 'día de suerte' o la 'semana de suerte'.
- **Umbral Obligatorio de Significancia Estadística:** Para que cualquier confirmación técnica o patrón SMC/ICT sea elegible como candidato al Top 1, Top 2 o Top 3, DEBE contar con un MÍNIMO de **50 trades históricos reales cerrados** en la base de datos auditada (`indicadores_impacto` o `patrones_ict_smc`). Muestras menores a 50 trades son descartadas automáticamente por falta de significancia estadística.
- **Criterio de Ranking:** Los candidatos maduros (>= 50 trades) se ordenan por su Win Rate real comprobado (`trades_ganados / trades_totales * 100`) y expectativa matemática positiva ($PnL > 0$).
- **Top 3 Validado Canónico:**
  1. **Top 1:** `rsi_sobrecompra_sobreventa` (67 trades | 83.58% Win Rate | +$466.47 PnL | Peso 35)
  2. **Top 2:** `order_block_zona_2h` (158 trades | 80.38% Win Rate | -$39.22 PnL | Peso 30)
  3. **Top 3:** `lux_algo_ob_2h` (106 trades | 61.32% Win Rate | +$113.76 PnL | Peso 25)
- **Mandato HITL:** Ningún agente puede sobreescribir la Regla de 3 automáticamente; cualquier recalibración debe cumplir el umbral de >= 50 trades y presentarse para autorización HITL explícita.

# 🛑 REGLA DE ORO DE VERDAD FINANCIERA Y VOCABULARIO CANÓNICO (SALDO BASE $5,000 USD)
**MANDATO ESTRICTO PARA TODOS LOS AGENTES LLM, CUANTITATIVOS Y SRE:**
1. **Saldo Base Inicial Original:** La cuenta partió formalmente de un capital inicial de **$5,000.00 USD**.
2. **Prohibición Terminante de Calificación "Saludable" u "Óptima":**
   Queda TERMINANTEMENTE PROHIBIDO que cualquier Agente LLM (Post-Mortem, Supervisor Quant, Watchdog T1-T10, 7 Herds) o reporte califique la cuenta, el balance o las ganancias como "saludables", "óptimas" o "positivas" mientras el balance auditado se encuentre por debajo de **$5,000.00 USD**.
3. **Estado Oficial de la Cuenta:** Mientras el saldo sea < $5,000.00 USD, el único estado oficial, honesto y auditable es:
   `ESTADO DE LA CUENTA: EN RECUPERACIÓN / BAJO DRAWDOWN SEVERO ACUMULADO (-$X USD / -Y% vs Base $5,000)`.
4. **Criterio Inquebrantable de Restablecimiento:** La cuenta SOLO y EXCLUSIVAMENTE podrá ser declarada como "Restablecida / Saludable" cuando el balance real auditado en MT5 sea **>= $5,000.00 USD** de forma neta y comprobada.
5. **Enfoque de Recuperación de Capital:** Cada propuesta de trading, ajuste de lotaje o trailing stop debe tener como único objetivo prioritario la recuperación asimétrica del capital hacia los $5,000 USD, erradicando micro-ganancias que se coman los retrocesos normales de mercado.


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

# 🛑 REGLA DE ORO DE PORTAFOLIO HERMÉTICO Y CONTROL ESTRICTO DE CUOTAS LLM (5 LIVE MT5 + 1 SANDBOX NZDCAD)
**MANDATO ESTRICTO PARA TODOS LOS AGENTES (FRONT-OFFICE, BACK-OFFICE, HERDS Y SRE):**
1. **Composición Inquebrantable del Portafolio:**
   - **5 Pares Oficiales en Vivo MT5:** `EURUSD`, `GBPUSD`, `AUDUSD`, `GBPJPY`, `XAUUSD`.
   - **1 Par Oficial en Sandbox (Shadow Mode):** `NZDCAD` (estrictamente experimental / entrenamiento continuo, 0 órdenes reales a MetaTrader 5).
2. **Prohibición Terminante de Activos Residuales o Ficticios:**
   Queda TERMINANTEMENTE PROHIBIDO que `trading_matrix`, `app.py` (`ACTIVOS_INICIALIZADOS` / `FIREBASE VIP`), `mt5_executor_cloud.py`, `mia_master_swarm_rest.py`, escáneres o llamadas a APIs de LLMs (Groq, Gemini, OpenRouter) carguen, matriculen, procesen, evalúen o escaneen activos fuera del portafolio oficial (como `BTC`, `UNKNOWN`, `XAUUSD_TEST`, `SP500`, `SPX500`, `NAS100`, `NASDAQ100`, `US30`, `USDJPY`, `USDCAD`, `USDCHF`, `EURGBP`, `GBPCAD`, `CHFJPY`, `EURJPY`).
3. **Eficiencia y Blindaje Anti-429 en Inferencia LLM:**
   El escaneo y deliberación de los 7 Herds y LLMs solo procesa activos con liquidez activa en su Killzone correspondiente (Londres: `GBPUSD`, `EURUSD`, `GBPJPY` | NY: `EURUSD`, `XAUUSD` | Asia: `AUDUSD`, `GBPJPY`). No se queman tokens ni llamadas en pares cerrados o fuera de sesión.
4. **Protección de la Colección `trading_matrix`:**
   La colección `trading_matrix` en Firebase Firestore y el slot `cache_trading_matrix` en Upstash Redis deben albergar ÚNICAMENTE los 6 activos oficiales (`AUDUSD`, `EURUSD`, `GBPJPY`, `GBPUSD`, `NZDCAD`, `XAUUSD`). Cualquier documento ajeno o residual es purgado de raíz.

# 🛑 REGLA DE ORO DE GESTIÓN DE RIESGO INSTITUCIONAL V2 (CASCADA RUNE 4 FASES & CANASTA USD)
**MANDATO CUANTITATIVO PARA EJECUCIÓN MT5 Y HERD 5 (RUNE):**
1. **Cascada Asimétrica de 4 Fases (RUNE):**
   - **Fase 1 (TP1 Parcial):** Cobro obligado del 50% del volumen al 50% de la distancia total (+1.0R mínimo).
   - **Fase 2 (Break-Even Institucional):** Desplazamiento automático del Stop Loss a Break-Even post-TP1 con buffer defensivo de **+2.5 pips** para amortiguar spreads y micro-ruido.
   - **Fase 3 (Trailing Locks Asimétricos):**
     * Al 75% del recorrido $\implies$ Trailing Lock 1 asegurando el **+40%** del beneficio total.
     * Al 85% del recorrido $\implies$ Trailing Lock 2 asegurando el **+65%** del beneficio total.
   - **Fase 4 (Front-Run TP):** Cierre del 100% de la posición remanente al **95%** de la distancia proyectada para erradicar pérdidas por retrocesos violentos a milímetros del objetivo.
2. **Límite Canasta USD:** Máximo 2 operaciones simultáneas en pares que contengan USD (`EURUSD`, `GBPUSD`, `AUDUSD`, `XAUUSD`) para prevenir sobreexposición al dólar estadounidense.
3. **Filtro Anti-Caza All-Time High en Oro (XAUUSD):** Prohibido abrir compras en Oro si el precio se ubica dentro del 0.5% del All-Time High sin un retroceso interbancario previo de al menos 30 a 50 pips.
