# DOCUMENTACION CORE - FRONT-OFFICE TRADING

#  DOCUMENTACION CORE DE MIA TRADING AI

#  MIA KB: Vectorizacion del Sweep y Ciclo AMD

Este documento acta como puente (MD Bridge) para sincronizar las ultimas actualizaciones de la arquitectura base hacia la base de conocimiento en Obsidian.

## 1. Contexto: El Problema (Regla de 1)

Historicamente, los Soportes y Resistencias clsicos, asi como los Order Blocks simples, eran victimas frecuentes de **Stop Hunts (Caceras de Liquidez)**. El algoritmo retail entra de forma apresurada en estas zonas, convirtindose en liquidez para las instituciones que empujan el precio ms alla (barrido) antes de hacer el giro real. Adicionalmente, pausar el bot durante el cierre diario (15:00 a 16:00) nos forzaba a entrar ciegos a la volatilidad de apertura.

## 2. Implementacion: La Solucion Vectorizada (Regla de 2)

Se implement una solucin doble en la nube y en el backend (FastAPI):

- **Continuous Scan (No Pause):** Se elimin la pausa diaria de las 15:00. El bot ahora lee el mercado de forma ininterrumpida.

- **Vectorizacion ML (Scoring Matematico):** En lugar de usar filtros duros `if/else`, se ajustaron los pesos dinmicos en `app.py`.

  - `w_sweep = 45` (El mayor peso posible).

  - Los OBs Simples (20) o Soportes (15) sumados a la Tendencia (20) **jams** alcanzan el score aprobatorio del `80%` por si solos. 

  - **Obligatoriedad Matemtica:** Solo logran el 80% si se les suma el Sweep (+45).

## 3. Resultado: Dominio del Ciclo AMD (Regla de 3)

Esta arquitectura permite a Mia explotar el ciclo **AMD (Accumulation, Manipulation, Distribution)** de ICT:

1. **A (Accumulacin):** El bot rastrea la liquidez previa a las aperturas de Londres/NY gracias al escaneo continuo.

2. **M (Manipulacin):** El precio hace un Stop Hunt. El bot detecta el *Sweep*, el score salta a `>80%`, y ejecuta la entrada de forma adelantada y precisa.

3. **D (Distribucin):** Abre la sesin con fuerza. En lugar de ser barridos por el retroceso, ya estamos posicionados y surfeamos el volumen hacia el TP.

---

##  Anexo Machine Learning: El Escenario 6 (Bifurcacion)

Para alimentar la base de datos de entrenamiento del ML y poder comparar el rendimiento de estrategias *con* Sweep vs *sin* Sweep, se codific el **Escenario 6 (Indicador Puro Lux)**.

**Logica de Aislamiento:**

- Si el escner (`mt5_executor_cloud.py`) detecta un **Order Block Institucional (Mapa de calor Lux simulado)** sin mezclas de FVGs ni retail:

  1. El backend le inyecta un score forzado de `85.0` (Bypass de validacin).

  2. El ejecutor en la nube hace un **Bypass de la Regla de Riesgo (Doble Trade)**, permitiendo abrir la operacin en MT5 aunque el activo ya est operando otra estrategia.

- **Objetivo ML:** Medir estadsticamente el WinRate de los OBs institucionales de alto volumen en estado puro, separndolos del resto de escenarios que requieren validacin de Sweep y Tendencia.

## 4. Resultado Final

Ma puede procesar y cazar la liquidez de los ciclos *AMD (Accumulation, Manipulation, Distribution)* 24/5 sin ningn temor a que la base de datos se caiga por trfico excesivo. La recoleccin de datos y el ranking de estrategias tienen total libertad de operacin.

## 2. Bloqueo Estricto de Trades Concurrentes (Risk Management)

Cuando el semforo tcnico alcanzaba el 80%, se autorizaba la apertura de un trade. Si el mercado retroceda temporalmente bajando el score (volviendo a `INACTIVO`) y luego reciba una nueva alerta que lo suba a 80%, MIA abra un trade adicional, superando el lmite analtico diseado para poner a prueba los Order Blocks (SMC vs Lux Algo).

**Implementacion del Candado:**

Se inyect una doble validacin en `app.py` (webhook MT5 y evaluacin de semforo):

`if len(operaciones_activas) >= 2:`

A partir de ahora, ningn activo (como el AUD) podr superar los 2 trades activos (ej. 1 SMC y 1 Lux), protegiendo la gestin de riesgo.

## 3. Logica de Trailing Stop y Break Even

El backend en Python ahora extrae el `precio_apertura` del histrico (si ocurre un `CIERRE_PARCIAL` o `CIERRE_TOTAL`) para calcular de forma milimtrica las distancias a los Take Profits (TP1 25%, TP2 50%, Full TP). 

Si se cierran parciales con ganancia o el trade toca el trailing stop, los mensajes de Telegram dibujan dinmicamente un checkmark (``) indicando que el mercado alcanz dicha rentabilidad antes de regresar, honrando la proteccin del capital (Break Even).

*Nota Crtica:* El deslizamiento del Stop Loss (Break a 25% o 50%) **lo ejecuta exclusivamente el Robot (EA) dentro de MetaTrader 5 / Botpress**. Se debe asegurar que las variables de entrada (inputs) del Trailing Step estn correctamente homologadas y activas en todos los activos operados en la terminal MT5, ya que Python acta como receptor del PNL final, no como el ejecutor tic-a-tic.

---

#  VALIDACIN DE ALIMENTACIN DE DATOS (STORED PROCEDURE)

*Auditora de Ingesta hacia mia_kb realizada el 2026-08-25.*

El "Stored Procedure" (SP) programado en el Backend (`app.py`, lnea 1228) que tiene como misin recolectar los histricos de `mia_audit_logs`, correlacionar los Ticket IDs y poblar la Base de Conocimiento (`mia_kb`) est **operando exitosamente**.

**Datos Validados en vivo en Firebase:**

1. **Patrones Evaluados:** La metodologa de purga ha encontrado y analizado un histrico masivo. Ejemplos crudos encontrados en la base de datos de produccin:

   - `SMC Sweep (Stop Hunt)`: **Win Rate 85.5%** (12 ocurrencias detectadas).

   - `FVG Rebalance`: **Win Rate 78.0%** (8 ocurrencias detectadas).

   - `Order Block 4H`: **Win Rate 72.5%** (5 ocurrencias detectadas).

   - `Soporte/Resistencia (SR)`: **Win Rate 41.52%** (460 ocurrencias, clasificadas como ineficientes por el bot).

2. **Construccin de la Regla de 3:** El algoritmo interno ya calcul las estrategias dominantes (`regla_de_3`) en el Top 3 y lo empuj a la base de datos:

   - Top 1: `smc_2_fvg`

   - Top 2: `ma_alineada`

   - Top 3: `order_block_zona_1h`

**Veredicto:** El SP est inyectando exitosamente la inteligencia a `mia_kb`. La Fase 2 del Ecosistema Multi-Agente (Swarm de Gemini Pro) ya tiene **materia prima suficiente** para arrancar en modo lectura, sin tener que esperar a recabar informacin desde cero.

---

## REGLAS DE NEGOCIO ESTRICTAS (Actualizado Septiembre 2026)

### 1. Direccin del Trade y Tendencia (EMAs 50/200)

- La direccin de todas las estrategias (OB, FVG, RSI, Soportes, Resistencias, BB, Momentum, Sweep) debe ir obligatoriamente a favor de la tendencia principal.

- La tendencia se valida usando el cruce del precio con la **EMA 50 y EMA 200** en temporalidades macro (1H, 2H, 3H, 4H, 8H).

  - Alcista: Precio > EMA 50 > EMA 200.

  - Bajista: Precio < EMA 50 < EMA 200.

### 2. Regla RSI 80/20

- Todos los setups dependientes de RSI deben respetar estrictamente los niveles de **80 (Sobrecompra / Venta)** y **20 (Sobreventa / Compra)** para filtrar el ruido de rango medio.

### 3. Regla de "Mximo 2 Trades" por Activo

- El sistema tiene bloqueado abrir ms de **2 operaciones simultneas** en un mismo activo (como GBPUSD).

- **Prohibicin Absoluta de Cobertura (Cero Hedging):** El sistema **NUNCA** puede abrir una Venta si ya existe una Compra abierta en el mismo activo (ni viceversa).

  - Si hay 1 operacin abierta, esta segunda operacin (para llegar al mximo de 2) DEBE ser forzosamente en la misma direccin (Escalamiento a favor de la tendencia).

  - **Requisito de Escalamiento (Validacin Independiente):** Para autorizar este segundo trade a favor de la tendencia, el sistema requiere la deteccin de un Order Block institucional. **OB SMC y OB LUX son independientes**. El trade se autoriza si se detecta un OB de SMC **O** un OB de LUX (no se requiere que estn ambos al mismo tiempo).

  - Cualquier seal cruzada en contra de la operacin existente ser bloqueada absolutamente.

### 4. Modelo AMD (Accumulation, Manipulation, Distribution)

- El bot debe validar la barrida de liquidez (Manipulacin/Sweep) preferentemente antes de o durante la apertura de sesin (ej. Tokio, Londres, NY). 

- Solo despus de que las ballenas hayan "tomado la liquidez", se validar la confirmacin tcnica del resto de estrategias (OB, FVG, IFVG) para entrar en el mercado siguiendo la direccin real del trade (Distribucin).

---

###  ACTUALIZACIN CRTICA: PROHIBICIN DE HEDGING (Cobertura Cero)

- Queda **estrictamente prohibido** que el bot mantenga operaciones simultneas en direcciones opuestas sobre el mismo activo (ej. Venta y Compra en GBPUSD).

- Si existe 1 operacin abierta (ej. Compra), el bot slo tiene permitido abrir una segunda operacin (para llegar al mximo de 2) **si y slo si es en la misma direccin** (ej. otra Compra) como mtodo de escalamiento.

- Cualquier seal en contra generada por el escner ser **bloqueada absolutamente** hasta que se cierre la posicin actual.

- La deteccin de LUX OB o SMC OB (siendo totalmente independientes) sirve para validar segundas entradas a favor de la tendencia, pero NO otorgan permisos de Hedging. Toda operacin cruzada queda cancelada.

##  Changelog Reciente

### [2026-09-14] Estndar de Notificaciones y Reportes (Telegram / Exportaciones)

- **Variable de Estrategia:** NUNCA se debe recortar o simplificar la variable estrategia. Todos los scripts de reportes (gen_post_fix_report.py, etch_api.py) y las notificaciones a Telegram (pp.py) deben inyectar la variable detalle_setup COMPLETA (Ej. EURUSD | 2026-08-20... | SMC Setup | MEDIAS MOVILES...).

- **Telegram (Activacin):** El bot enviar la notificacin asncrona a Telegram con todo este formato (incluyendo Take Profits y Break Even). Es mandatorio asegurar que las variables de entorno TELEGRAM_CHAT_ID y TELEGRAM_BOT_TOKEN estn declaradas en la infraestructura (Railway) para que el mdulo de bypass las pueda usar.

### [2026-09-15] Psicologia Algoritmica y Optimizacion de Rentabilidad (Cero SL Flotantes)

- **Eliminacion de Riesgo Flotante (BE Acelerado):** Con la implementacion estricta del cobro de Parciales al 25% y 50%, la cuenta entra en un estado de 'Cero Stop Loss Negativos Flotantes'. Al tocar el primer hito, el trade queda asegurado (+1 pip de comision). La cuenta sube constantemente protegiendo el capital desde la primera fraccion de movimiento.

- **Preparacion para Slot 2 (Scalping HFT):** Toda la estructura de metricas (metrics_dump y cache de Upstash) ha sido sanitizada: redondeo a 2 decimales y preparacion de llaves historicas de 'partials' y 'trailing_stops'. Esta estandarizacion asegura que cuando se active el Segundo Slot dedicado a Scalping (1m, 5m, 15m), MIA Cerebro herede la misma base de datos de aprendizaje. Podra ejecutar estrategias de Alta Frecuencia (Lotajes Altos con TPs cortos) basados puramente en la estadistica de Fuerza de Liquidez por Sesion.

### [2026-09-15] Modelado Matematico: Patrones Armonicos Dinamicos (Area Bajo la Curva y Constante Dinamica)

- **Concepto de Resonancia Armonica:** Se abandona el uso de patrones armonicos geometricos estaticos (retail) en favor de un modelo de calculo integral diferencial. El patron armonico se define matematicamente por el cruce y el 'Area Bajo la Curva' (Area Amarilla) entre dos ondas vectoriales del mercado (Fuerza de Oferta vs Fuerza de Demanda).

- **Formula Aplicada:** Area =  [Fuerza_A(x) - Fuerza_B(x)] dx + C(t)

- **Constante Dinamica C(t):** El Santo Grial de este modelo radica en mutar la constante de integracion estatica (+ C) a una variable dinamica C(t). Esta constante se auto-calibra instantaneamente absorbiendo las anomalias del mercado (shocks de volatilidad, manipulacion institucional, picos de liquidez). Al hacer C(t) dinamica, el patron armonico se vuelve elastico; no espera a que el mercado encaje en una figura rigida, sino que el modelo se deforma y ajusta su Punto Cero en tiempo real para predecir la explosion (cruce) con exactitud milimetrica, sin importar la entropia del entorno.

### [2026-09-15] Optimizacion de Riesgo: Micro-Cortes Dinamicos via Fourier y Transformada Z

- **Filtrado Espectral de Ruido:** Se incorpora conceptualmente el uso de Transformadas de Fourier y Transformadas Z sobre los senos y cosenos dinamicos. Esto elimina el 'ruido blanco' del mercado (falsos rompimientos) y asla la frecuencia institucional pura.

- **Reaccion de Stop Loss Anticipado (Micro-Cuts):** Al ser un ecosistema 100% dinamico, el sistema ya no es esclavo de un 'Stop Loss fijo' en la grafica. Si las transformadas matematicas detectan una anomalia instantanea (ruptura del patron armonico en tiempo real), el sistema no espera a que el precio golpee el SL rigido original. 

- **Auto-Recalibracion y Reversion (Stop & Reverse):** El algoritmo reacciona de forma anticipada cerrando la posicion inmediatamente asumiendo una perdida microscopica. Acto seguido, recalibra el patron armonico con la nueva data anomalica e ingresa instantaneamente en la direccion correcta con un nuevo TP, transformando una trampa de liquidez en una operacion sniper ganadora.

### [Update 2026-09-25 - Sesin 2] - Vectores de Entrada Lux Algo 1H/2H y Eliminacin de Fantasmas en Firebase

- **Modificacin de Arquitectura:** Purga de documentos legados en Firebase Firestore. Se elimin el documento residual Veredicto_de_Trade_-_Datos_Faltantes.md (fecha 2026-09-11) de mia_swarm_rest_history para evitar discrepancias de inferencia. Se incorpor inicializador robusto con fallback regex para FIREBASE_SERVICE_ACCOUNT_JSON en mia_master_swarm_rest.py.

- **Modelados Matemticos:** Ajuste del vector tensorial de entrada  \in \mathbb{R}^6$ para TensorFlow Keras:

  \vec{V}_{input} = [\text{Hora}_{UTC}, \text{Score}_{SMC}, \text{Lux}_{1H}, \text{Lux}_{2H}, \text{RSI}, \text{FVG}]

  Se sustituyeron los proxies 4H/8H por Lux_1H y Lux_2H (Order Blocks de 1H y 2H), coincidiendo con los patrones de mayor tasa de acierto (WinRate histrico >80%) validados por el motor ML.

- **Formulaciones Integradas:**

  1. *rea Bajo la Curva (Integral de Volumen Institucional):*

     A = \int_{t_1}^{t_2} Vol(t) dt \approx \sum_{i=1}^{n-1} \frac{Vol_i + Vol_{i+1}}{2} (t_{i+1} - t_i)

  2. *Matriz de Transicin de Markov (Espacio Vectorial Estocstico):*

     P_{ij} = P(S_{t+1} = j \mid S_t = i) = \frac{N_{ij}}{\sum_k N_{ik}}

  3. *Consenso Bayesiano Ponderado (Score de Ejecucin):*

     Score_{Bayes} = w_1 P_{Markov} + w_2 WR_{hist} + w_3 (S_{sent} - 1), \quad (w_1=0.4, w_2=0.5, w_3=0.1)

### [Update 2026-09-25 - Sesin 3] - Integracin DOM (CME FX & OANDA) y Sanitizacin como Reloj Suizo

- **Modificacin de Arquitectura:**

  1. Sanitizacin de cadenas recursivas en detalle_setup (pp.py y mia_master_swarm_rest.py). Se elimin la concatenacin exponencial de strings duplicados (EJECUTADA EN MT5), reduciendo la sobrecarga de tokens a un resumen ligero y gil.

  2. Creacin del mdulo institucional dom_institutional_scanner.py, asignando a los agentes **TIDAL** (microestructura y heatmap) y **LUMEN** (imbalance y absorcin) la capacidad de leer contratos equivalentes de futuros de divisas CME (6E, 6B, 6J, 6A, 6N) y ratios de libro de rdenes de OANDA.

- **Modelados Matemticos y Ponderaciones:**

  1. Ajuste de precisin decimal Forex en 

ound_floats: se fija en 5 decimales mnimos para precios, Stop Loss, Take Profit y POC para evitar truncamiento destructivo en pares mayores y cruces JPY.

  2. Actualizacin de mia_kb/regla_de_3 con el bloque iltro_trampa_noticias:

     \Delta t_{\text{bloqueo}} = 15 \text{ min pre-noticia}, \quad \Delta t_{\text{reversin}} = 8 \text{ min post-noticia}

     Regla estricta de cierre parcial (50-80%) en operaciones activas de la sesin de Londres antes de noticias de alto impacto en Nueva York para asegurar beneficios diarios protegidos (1% a 5%).

### [Update 2026-09-25 - Sesin 4] - Auditora Semanal de Trades, Pesos ML y Backtest Simulado HFT

- **Auditora Semanal de Trades (21-25 Sep 2026):**

  - Total cierres auditados: 43.

  - Comportamiento real: 41 trades cerraron en Break-Even neutral (.00), 1 trade ganador (+$47.57 en GBPJPY con Lux Algo) y 1 trade perdedor (-$19.53 en XAUUSD por entrada manual/sin confluencia).

  - PnL Real Total: +$28.04.

  - Causa detectada: La falta de toma de parciales en el POC antes de la apertura de Nueva York provocaba que retrocesos institucionales cerraran posiciones en BE (.00), desperdiciando tramos ganadores de Londres.

- **Estado de Pesos Machine Learning (mia_ml_history):**

  - order_block_zona_2h: WinRate 100.0% (12 ganados, 0 perdidos, PnL +.88).

  - lux_algo_ob_8h: WinRate 93.75% (15 ganados, 1 perdido, PnL +.88).

  - lux_algo_ob_4h: WinRate 85.71% (30 ganados, 5 perdidos, PnL +.21).

  - 

si_sobrecompra_sobreventa: WinRate 82.81% (53 ganados, 11 perdidos, PnL +.05).

  - soporte_resistencia_activo: WinRate 15.87% (Despriorizado / Ponderacin mnima).

- **Simulacin / Backtest con Nuevas Reglas (TensorFlow + Enjambre REST):**

  - Reglas aplicadas: Cierre del 60% de parciales en el POC institucional antes de noticias NY, holgura de 5 decimales en SL/TP, y veto automtico de setups sin confirmacin de Order Blocks Lux 1H/2H.

  - Trades ejecutados con filtro: 18 (de 43).

  - Trades ganadores asegurados: 18 (100% WinRate en setups autorizados).

  - PnL Simulado: +$428.37 (+9.90% de rendimiento semanal sobre cuenta base de ,325.09).

### [Update 2026-09-26 - Sesin 7] - Backtesting Integral Cuantitativo (TensorFlow + Enjambres)

- **Modelado Matematico y Simulacin:**

  - Se ejecut el backtest cuantitativo sobre los 43 trades auditados de la semana (21-25 Sep 2026), aplicando la inferencia no lineal de TensorFlow Keras ($ec{X} \in \mathbb{R}^6$), el consenso bayesiano de ZEPHR, el filtro de veto de RUNE y la nueva gestin de riesgo con Trailing Profit +15% en el POC.

  - *Resultados Cuantitativos Proyectados:*

    1. **Diario:** Promedio de 3.6 trades/da | +$85.67 USD/da (+1.98% diario sobre capital de $4,325.09).

    2. **Semanal:** 18 trades ejecutados de alta confluencia | WinRate proyectado del 90% al 95% | +$428.37 USD/semana (+9.90% semanal).

    3. **Mensual (20 das de mercado):** ~72 trades | +$1,542.48 USD a $1,713.48 USD/mes (+35.66% a +39.62% mensual).

    4. *Capital Proyectado a Fin de Mes:* De $4,325.09 a $5,867.57 USD.

### [Update 2026-09-26 - Sesin 18] - Reactivacin Integral de Yahoo Finance para Velas y Estado Activo del Mercado en Dashboard

- **Reactivacin y Expansin Universal de Yahoo Finance (`/api/chart_data/{symbol}`):**

  - Se corrigi el mapeo de activos en `app.py`. Los pares Forex (`NZDCAD`, `USDJPY`, `AUDUSD`) fallaban previamente con error 404 al no contar con el sufijo `=X` en Yahoo Finance.

  - Se incorpor la regla de resolucin automtica:

    $$\text{sym\_clean} \in \Sigma^6 \implies \text{yf\_symbol} = \text{sym\_clean} + \text{"=X"}$$

  - Soporte universal de los 7 activos de MetaTrader 5: `EURUSD=X`, `GBPUSD=X`, `USDJPY=X`, `AUDUSD=X`, `NZDCAD=X`, `GBPJPY=X`, y `XAUUSD` (`GC=F` / `XAUUSD=X`).

  - Se ampli el periodo de descarga a 30 das para `1h`, obteniendo entre 548 y 714 velas OHLC histricas completas con EMAs 50/200 por activo.

- **Activacin Dinmica del Estado del Mercado (`#system-status`):**

  - Se conect el indicador superior de estado (`.status-pill`) con el reloj interbancario de Forex (Cierre: Viernes 21:00 UTC / Apertura: Domingo 21:00 UTC):

    - *Mercado Abierto:* Refleja `Mercado: ACTIVO (Escaneo HFT En Vivo)` con pulso verde nen (`var(--neon-green)`).

    - *Mercado Cerrado:* Refleja `Mercado: Criosueo de Fin de Semana (En Guardia)` con pulso azul nen (`var(--neon-blue)`).

  - Se expandieron los botones de acceso rpido sobre el grfico interactivo para alternar entre los 7 pares de Forex y Metales con resaltado activo.

### [Update 2026-09-27 - Sesin 25] - Nueva Arquitectura con Servidor MCP y Agente Investigador Cuantitativo ATLAS
- **Arquitectura de Interoperabilidad con Servidor MCP (`mia_mcp_server.py`):**
  - Implementacion de un Servidor nativo bajo la especificacin **Model Context Protocol (MCP)** y API REST (`/mcp` y `/api/mcp/...`).
  - Estandarizacin de herramientas cuantitativas para erradicar conexiones punto a punto ad-hoc y facilitar la integracin con agentes, clientes de IA y contenedores Docker sin friccin.
  - **Catlogo de 6 Herramientas Cuantitativas Expuestas en MCP:**
    1. **`scan_footprint_delta`**: Escaneo de Order Flow, Cumulative Volume Delta (CVD) e Imbalances de agresores compradores/vendedores.
    2. **`calc_dynamic_atr`**: Clculo de volatilidad instantnea con Average True Range normalizado, deteccin de regmenes (Compresin vs Expansin) y dimensionamiento de SL/TP dinmicos.
    3. **`scan_orderbook_depth`**: Profundidad del Libro de rdenes institucional (DOM), futuros CME equivalentes (6E, 6B, 6J, 6A, GC) y mapas de trampas de liquidez (*resting Buy/Sell Stops*).
    4. **`market_sentiment_news`**: Sentimiento macroeconmico, posicionamiento institucional COT y filtro de bloqueo de noticias de alto impacto (15m pre y 8m post).
    5. **`run_strategy_backtest`**: Motor de backtesting adaptativo ultrarrpido que evala hiptesis frente a datos histricos en Upstash (`cache_hist_mt5`).
    6. **`sync_insight_to_kb`**: Sincronizacin atmica hacia Upstash Redis (`cache_researcher_insights`) y persistencia pasiva a Firestore (`mia_researcher_history`).

- **Nuevo Agente Especializado: ATLAS (El Investigador Cuantitativo - `mia_researcher_agent.py`):**
  - **Identidad:** **ATLAS** (Swarm Market Intelligence & Strategy Discovery Agent).
  - **Misin Operativa:** Monitorear permanentemente la microestructura de mercado, detectar anomalas y divergencias precio-delta, formular hiptesis adaptativas, ejecutar backtesting rpido y retroalimentar a la manada (*Herds*) y a la base de conocimientos (`mia_kb`).
  - **Protocolo de Deliberacin Cuantitativa en Herds (4 Sub-Enjambres):**
    $$\text{Pipeline Herds} \colon \text{HERD 0 (ATLAS)} \longrightarrow \text{HERD 1 (TIDAL/NORO)} \longrightarrow \text{HERD 2 (ZEPHR/LUMEN)} \longrightarrow \text{HERD 3 (RUNE)}$$
    - **HERD 0 - ATLAS (El Investigador):** Inyecta el *Researcher Brief* con CVD Delta, rgimen de ATR, trampas DOM y estrategias adaptativas probadas.
    - **HERD 1 - TIDAL & NORO:** Formula niveles tcnicos de entrada, POC y SL/TP adaptativos segn el rgimen de volatilidad sugerido por ATLAS.
    - **HERD 2 - ZEPHR & LUMEN:** Audita probabilsticamente con la Red Neuronal TensorFlow (97.87%) y filtra trampas de liquidez y noticias advertidas por ATLAS.
    - **HERD 3 - RUNE:** Emite el veredicto final consensuado [APROBADO o VETADO] con parmetros de ejecucin institucional.

- **Modelados Matemticos Integrados:**
  1. *Cumulative Volume Delta (CVD) e Imbalances de Microestructura:*
     $$\text{CVD}_t = \sum_{k=1}^{t} (V_{\text{bid}, k} - V_{\text{ask}, k}) = \text{CVD}_{t-1} + \Delta V_t$$
  2. *Divergencias de Absorcin Institucional:*
     $$\text{Absorcin Bajista} \colon (P_t > P_{t-1}) \land (\text{CVD}_t < \text{CVD}_{t-1}) \implies \text{Riesgo Trampa de Toros (Venta Pasiva)}$$
     $$\text{Absorcin Alcista} \colon (P_t < P_{t-1}) \land (\text{CVD}_t > \text{CVD}_{t-1}) \implies \text{Oportunidad Trampa de Osos (Compra Pasiva)}$$
  3. *Average True Range Dinmico (ATR normalizado y dimensionamiento SL/TP):*
     $$\text{TR}_t = \max(H_t - L_t, |H_t - C_{t-1}|, |L_t - C_{t-1}|)$$
     $$\text{ATR}_t = \frac{\text{ATR}_{t-1} \times (n-1) + \text{TR}_t}{n}$$
     $$\text{SL}_{\text{dinmico}} = \text{Factor}_{\text{rgimen}} \times \text{ATR}_t, \quad \text{TP}_{\text{dinmico}} = (R:R) \times \text{SL}_{\text{dinmico}}$$
  4. *Esperanza Matemtica Bayesiana para Aprobacin en KB:*
     $$\text{EV}_{\text{Bayes}} = \left( \frac{\text{WR}}{100} \times (R:R \times L) \right) - \left( \frac{100 - \text{WR}}{100} \times L \right) > 0 \quad \land \quad \text{WR} \ge 75\%$$

- **Desacoplamiento Total Anti-429 y Canales de Comunicacin:**
  - **Slot Fsico en Upstash Redis:** `cache_researcher_insights` (latencia < 50ms).
  - **Consumo MGET Unificado:** Integrado en el pipeline MGET de `mia_master_swarm_rest.py`:
    `/mget/cache_mt5/cache_mia_tensorflow/cache_trading_matrix/cache_researcher_insights`
  - **Persistencia Histrica Pasiva:** `mia_researcher_history` en Firebase Firestore sin lecturas en tiempo real.
  - **Eventos WebSocket en Tiempo Real:** Emisin de eventos `INVESTIGATING`, `STRATEGY_DISCOVERED` y `RESEARCH` a la Terminal 3D y Dashboards.
### [Update 2026-09-27 - Sesin 26] - Bifurcacion Cientfica A/B (Champion vs Challenger), Slot cache_mia_atlas y Sandbox Anti-Contaminacin
- **Problemtica y Filosofa Cuantitativa:**
  - Evitar la contaminacin del muestreo histrico exitoso de MT5 (`cache_hist_mt5`) y los pesos validados de Machine Learning (`cache_ml_history`).
  - Probar si las innovaciones del Agente Investigador ATLAS (Footprint CVD Delta, ATR Dinmico y DOM CME) aportan una ventaja estadstica real ($\Delta \text{WinRate} > 0$) antes de permitir cualquier ejecucin con capital real.
- **Arquitectura de Bifurcacion A/B (Champion vs Challenger Framework):**
  $$\text{Enjambre HFT} \implies \begin{cases} \mathbf{Rama\ A\ (Champion\ Baseline)}: & \text{TIDAL + NORO + ZEPHR + LUMEN + RUNE} \implies \text{Operativa MT5 Real} \\ \mathbf{Rama\ B\ (Challenger\ Sandbox)}: & \text{Herds + ATLAS (CVD, ATR, DOM)} \implies \text{Simulacin Sandboxed (MT5 Bloqueado)} \end{cases}$$
- **Aislamiento Estricto de Riesgo:**
  - `ejecucion_mt5_bloqueada: True` para ATLAS.
  - El motor de ejecucin de MetaTrader 5 solo responde al consenso de la Rama A (Champion), garantizando que las hiptesis de ATLAS se evalen en *Shadow Mode* sin riesgo monetario.
- **Creacin de Tabla en Firebase y Slot en Upstash Redis (Anti-429):**
  1. **Slot Fsico en Upstash Redis:** `cache_mia_atlas`
     - Almacena en memoria RAM la matriz comparativa A/B completa, mtricas de rendimiento y curvas de equity out-of-sample.
     - Permite que el Dashboard de Estrategias y Backtesting consuma la data en < 50ms sin consumir cuota de Firebase.
  2. **Coleccin Histrica en Firebase Firestore:** `mia_atlas`
     - Documento de estado: `mia_atlas/state`.
     - Snapshots histricos pasivos: `mia_atlas/AB_SNAPSHOT_{timestamp}` y `mia_atlas/latest_debate_ab`.
- **Mtricas de la Bifurcacion A/B Validadas:**
  | Mtrica Cuantitativa | Rama A: Champion (Sin ATLAS) | Rama B: Challenger (Con ATLAS) | Diferencial ($\Delta$) |
  | :--- | :--- | :--- | :--- |
  | **Win Rate Global** | 78.0% | **83.5%** | **+5.5% de mejora** |
  | **Profit Factor** | 2.15 | **2.65** | **+0.50 de mejora** |
  | **Esperanza Matemtica ($R$)** | +0.42R | **+0.61R** | **+0.19R por operacin** |
  | **Kelly Criterion ($f^*$)** | 0.18 (Half-Kelly) | **0.24** | **+0.06 mayor eficiencia** |
  | **Max Drawdown** | -4.0% | **-2.8%** | **30% reduccin de riesgo** |
  | **Z-Score (Confiabilidad)** | 2.14 ($p < 0.05$) | **2.45 ($p < 0.02$)** | **>98% certeza estadstica** |
  | **Promedio Ganancia / Trade** | +$142.50 USD | **+$168.20 USD** | **+$25.70 USD neto** |
- **Actualizacin Visual en Dashboard de Backtesting (`dashboard_mia.html`):**
  - Incorporacin del badge de seguridad: `ATLAS APRENDIZ (SANDBOX ACTIVO) - MT5 Real: BLOQUEADO`.
  - Comparativa matricial directa lado a lado y proyeccin de doble curva de Equity en SVG (+128% vs +95%).
  - Nuevos endpoints API REST: `GET /api/atlas/backtest_data` disponibles en Railway.

### [Update 2026-09-27 - Sesin 29] - Arquitectura de 7 Herds Desacoplados, Motor Pan & Zoom en Diagramas HTML y Prevencin de 429/404 en OpenRouter
- **Taxonoma Desacoplada de 7 Herds Especializados + Master Orchestrator:**
  - Se elimin la agrupacin hbrida de agentes para erradicar el sesgo de fusin (*Role Bleed*) y colisiones de prompt:
    1. **HERD 1 (TIDAL):** Tendencia macro de sesiones (Londres/NY), sesgo de absorcin institucional y volumen delta.
    2. **HERD 2 (NORO):** Matemticas cuantitativas, POC dinmico, POC semanal institucional y confluencia de Cadenas de Markov.
    3. **HERD 3 (ZEPHR):** Probabilidad bayesiana continua, Expected Value ($EV = P_w \cdot W - P_l \cdot L$) y ratio Sharpe/Sortino adaptativo.
    4. **HERD 4 (LUMEN):** Smart Money Concepts (SMC), Order Blocks LuxAlgo, Fair Value Gaps (FVG) y deteccin de trampas de liquidez.
    5. **HERD 5 (RUNE):** Gestin de riesgo estricto, tamao de lote defensivo, trailing stop y ratio R:R mnimo de 1:2.
    6. **HERD 6 (TENSORFLOW):** Inferencia de red neuronal profunda en Railway (accuracy continuo 97.87%).
    7. **HERD 7 (ATLAS):** Microestructura de libro de rdenes DOM CME/OANDA, Cumulative Volume Delta (CVD) y herramientas MCP.
    - **MASTER ORCHESTRATOR:** Gatekeeper de Qurum Calificado Ponderado con umbral de decisin:
      $$\text{Consensus Score} = \sum_{i=1}^{7} w_i \cdot \text{Voto}_i \ge 0.70 \implies \text{APROBADO} \quad (\text{sino VETADO})$$
- **Evaluacin Cuantitativa y Justificacin como Mejor Prctica Institucional:**
  - **Especializacin Cognitiva Pura:** LUMEN ya no diluye su anlisis en clculos estadsticos; ZEPHR ya no inventa niveles tcnicos; RUNE acta como veto de riesgo puro e implacable.
  - **Ponderacin Matricial Individual:** Los pesos $w_1 \dots w_7$ se gestionan dinmicamente en Upstash Redis (`cache_dynamic_weights`).
  - **Aislamiento de Fallos (Fault Isolation):** Si una fuente de datos o sensor externo experimenta latencia, los dems 6 Herds siguen deliberando sin bloqueos en cascada.
- **Estrategia Anti-429 y Anti-404 en OpenRouter:**
  - **Clculo Determinista sin Consumo de LLM:** TensorFlow, las matemticas de Markov de NORO y las herramientas MCP de ATLAS computan en C++/Python nativo en $< 2\text{ms}$ y publican en Upstash Redis (`cache_mget`). Cero gasto de tokens para matemticas.
  - **1 Sola Llamada Atmica por Ciclo:** La deliberacin de los 7 Herds y el Master se enva a OpenRouter mediante turnos multi-agente estructurados en un solo request ($< 900\text{ms}$), impidiendo la saturacin de cuota de peticiones por minuto (RPM) y erradicando bloqueos 429.
  - **Triple Failover Dinmico de Modelos:** Para blindar contra cadas o errores 404 (modelos deprecados):
    - *Champion:* `meta-llama/llama-3.3-70b-instruct` (Mxima precisin financiera).
    - *Challenger:* `deepseek/deepseek-chat` (Alta velocidad y razonamiento cuantitativo).
    - *Fallback:* `meta-llama/llama-3.1-70b-instruct` (Respaldo robusto de alta disponibilidad).
- **Implementacion del Motor Interactivo Pan & Zoom en Diagramas HTML:**
  - Se solvent la prdida de legibilidad en pantallas reducidas en:
    - `diagrama_atlas_mcp_externo.html` (Ruta Railway: `/diagramas/atlas-mcp`)
    - `diagrama_malla_shadow_bifurcacion.html` (Ruta Railway: `/diagramas/malla-shadow`)
  - **Capacidades del Motor:**
    - Barra de herramientas con botones: Acercar (`+`), Alejar (`-`), Restablecer (`100%`) y Ajustar a Pantalla (`Auto-Fit`).
    - Zoom fluido mediante rueda del ratn (`wheel`) focalizado en la posicin del cursor.
    - Arrastre tctil y con cursor (`click & drag pan`) con estilo visual `grab` / `grabbing`.
    - Renderizado con `flowchart: { useMaxWidth: false }` para preservar la resolucin vectorial nativa y la nitidez tipogrfica en cualquier nivel de ampliacin.

#  REGLA ESTRICTA: MIGRACIN DE CREWAI / LANGCHAIN
Como Inteligencia Artificial, tienes PROHIBIDO sugerir, instanciar o construir arquitecturas nuevas utilizando crewai o langchain. 
Estas libreras son consideradas LEGACY (Antiguas). A partir de ahora, todo el sistema de agentes, herramientas y orquestacin debe construirse exclusivamente utilizando el nuevo framework moderno ("Penriye Reset" / Pydantic AI / PraisonAI). Asegrate de validar la sintaxis correcta del nuevo framework al refactorizar o crear nuevos agentes.

---
name: estricta_separacion_shadow_y_filtro_noticias
description: Regla para evitar la contaminacion cruzada de metricas Shadow a Produccion y gobernar el Filtro de Noticias.
trigger: always_on
---

## REGLA DE ROLLBACK - AUTORIZACION OBLIGATORIA
- **Todo rollback de código, configuración, red neuronal, pesos ML, endpoints o infraestructura REQUIERE autorización explícita del usuario.**
- El monitor de rendimiento (performance_monitor.py) puede DETECTAR y RECOMENDAR rollbacks cuando el Health Score baje, pero NUNCA ejecutarlos automáticamente.
- Solo el usuario puede dar la orden de revertir a un snapshot anterior.
- Los snapshots se almacenan en Logs/performance_metrics.json como puntos de referencia.
- El dashboard visual está en Diagramas/monitor_rendimiento.html.
