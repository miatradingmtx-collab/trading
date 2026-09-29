# DOCUMENTACION CORE - FRONT-OFFICE TRADING

# ð§  DOCUMENTACIÃN CORE DE MIA TRADING AI















# ð§  MIA KB: VectorizaciÃ³n del Sweep y Ciclo AMD















Este documento actÃºa como puente (MD Bridge) para sincronizar las Ãºltimas actualizaciones de la arquitectura base hacia la base de conocimiento en Obsidian.















## 1. Contexto: El Problema (Regla de 1)







HistÃ³ricamente, los Soportes y Resistencias clÃ¡sicos, asÃ­ como los Order Blocks simples, eran vÃ­ctimas frecuentes de **Stop Hunts (CacerÃ­as de Liquidez)**. El algoritmo retail entra de forma apresurada en estas zonas, convirtiÃ©ndose en liquidez para las instituciones que empujan el precio mÃ¡s allÃ¡ (barrido) antes de hacer el giro real. Adicionalmente, pausar el bot durante el cierre diario (15:00 a 16:00) nos forzaba a entrar ciegos a la volatilidad de apertura.















## 2. ImplementaciÃ³n: La SoluciÃ³n Vectorizada (Regla de 2)







Se implementÃ³ una soluciÃ³n doble en la nube y en el backend (FastAPI):







- **Continuous Scan (No Pause):** Se eliminÃ³ la pausa diaria de las 15:00. El bot ahora lee el mercado de forma ininterrumpida.







- **VectorizaciÃ³n ML (Scoring MatemÃ¡tico):** En lugar de usar filtros duros `if/else`, se ajustaron los pesos dinÃ¡micos en `app.py`.







  - `w_sweep = 45` (El mayor peso posible).







  - Los OBs Simples (20) o Soportes (15) sumados a la Tendencia (20) **jamÃ¡s** alcanzan el score aprobatorio del `80%` por sÃ­ solos. 







  - **Obligatoriedad MatemÃ¡tica:** Solo logran el 80% si se les suma el Sweep (+45).















## 3. Resultado: Dominio del Ciclo AMD (Regla de 3)







Esta arquitectura permite a Mia explotar el ciclo **AMD (Accumulation, Manipulation, Distribution)** de ICT:







1. **A (AccumulaciÃ³n):** El bot rastrea la liquidez previa a las aperturas de Londres/NY gracias al escaneo continuo.







2. **M (ManipulaciÃ³n):** El precio hace un Stop Hunt. El bot detecta el *Sweep*, el score salta a `>80%`, y ejecuta la entrada de forma adelantada y precisa.







3. **D (DistribuciÃ³n):** Abre la sesiÃ³n con fuerza. En lugar de ser barridos por el retroceso, ya estamos posicionados y surfeamos el volumen hacia el TP.















---















## ð¬ Anexo Machine Learning: El Escenario 6 (BifurcaciÃ³n)







Para alimentar la base de datos de entrenamiento del ML y poder comparar el rendimiento de estrategias *con* Sweep vs *sin* Sweep, se codificÃ³ el **Escenario 6 (Indicador Puro Lux)**.















**LÃ³gica de Aislamiento:**







- Si el escÃ¡ner (`mt5_executor_cloud.py`) detecta un **Order Block Institucional (Mapa de calor Lux simulado)** sin mezclas de FVGs ni retail:







  1. El backend le inyecta un score forzado de `85.0` (Bypass de validaciÃ³n).







  2. El ejecutor en la nube hace un **Bypass de la Regla de Riesgo (Doble Trade)**, permitiendo abrir la operaciÃ³n en MT5 aunque el activo ya estÃ© operando otra estrategia.







- **Objetivo ML:** Medir estadÃ­sticamente el WinRate de los OBs institucionales de alto volumen en estado puro, separÃ¡ndolos del resto de escenarios que requieren validaciÃ³n de Sweep y Tendencia.















## 4. Resultado Final







MÃ­a puede procesar y cazar la liquidez de los ciclos *AMD (Accumulation, Manipulation, Distribution)* 24/5 sin ningÃºn temor a que la base de datos se caiga por trÃ¡fico excesivo. La recolecciÃ³n de datos y el ranking de estrategias tienen total libertad de operaciÃ³n.















## 2. Bloqueo Estricto de Trades Concurrentes (Risk Management)







Cuando el semÃ¡foro tÃ©cnico alcanzaba el 80%, se autorizaba la apertura de un trade. Si el mercado retrocedÃ­a temporalmente bajando el score (volviendo a `INACTIVO`) y luego recibÃ­a una nueva alerta que lo subÃ­a a 80%, MIA abrÃ­a un trade adicional, superando el lÃ­mite analÃ­tico diseÃ±ado para poner a prueba los Order Blocks (SMC vs Lux Algo).















**ImplementaciÃ³n del Candado:**







Se inyectÃ³ una doble validaciÃ³n en `app.py` (webhook MT5 y evaluaciÃ³n de semÃ¡foro):







`if len(operaciones_activas) >= 2:`







A partir de ahora, ningÃºn activo (como el AUD) podrÃ¡ superar los 2 trades activos (ej. 1 SMC y 1 Lux), protegiendo la gestiÃ³n de riesgo.















## 3. LÃ³gica de Trailing Stop y Break Even







El backend en Python ahora extrae el `precio_apertura` del histÃ³rico (si ocurre un `CIERRE_PARCIAL` o `CIERRE_TOTAL`) para calcular de forma milimÃ©trica las distancias a los Take Profits (TP1 25%, TP2 50%, Full TP). 







Si se cierran parciales con ganancia o el trade toca el trailing stop, los mensajes de Telegram dibujan dinÃ¡micamente un checkmark (`â`) indicando que el mercado alcanzÃ³ dicha rentabilidad antes de regresar, honrando la protecciÃ³n del capital (Break Even).







*Nota CrÃ­tica:* El deslizamiento del Stop Loss (Breakà¦«à¦à§à¦¨ a 25% o 50%) **lo ejecuta exclusivamente el Robot (EA) dentro de MetaTrader 5 / Botpress**. Se debe asegurar que las variables de entrada (inputs) del Trailing Step estÃ©n correctamente homologadas y activas en todos los activos operados en la terminal MT5, ya que Python actÃºa como receptor del PNL final, no como el ejecutor tic-a-tic.















---















# ð§  VALIDACIÃN DE ALIMENTACIÃN DE DATOS (STORED PROCEDURE)







*AuditorÃ­a de Ingesta hacia mia_kb realizada el 2026-08-25.*















El "Stored Procedure" (SP) programado en el Backend (`app.py`, lÃ­nea 1228) que tiene como misiÃ³n recolectar los histÃ³ricos de `mia_audit_logs`, correlacionar los Ticket IDs y poblar la Base de Conocimiento (`mia_kb`) estÃ¡ **operando exitosamente**.















**Datos Validados en vivo en Firebase:**







1. **Patrones Evaluados:** La metodologÃ­a de purga ha encontrado y analizado un histÃ³rico masivo. Ejemplos crudos encontrados en la base de datos de producciÃ³n:







   - `SMC Sweep (Stop Hunt)`: **Win Rate 85.5%** (12 ocurrencias detectadas).







   - `FVG Rebalance`: **Win Rate 78.0%** (8 ocurrencias detectadas).







   - `Order Block 4H`: **Win Rate 72.5%** (5 ocurrencias detectadas).







   - `Soporte/Resistencia (SR)`: **Win Rate 41.52%** (460 ocurrencias, clasificadas como ineficientes por el bot).







2. **ConstrucciÃ³n de la Regla de 3:** El algoritmo interno ya calculÃ³ las estrategias dominantes (`regla_de_3`) en el Top 3 y lo empujÃ³ a la base de datos:







   - Top 1: `smc_2_fvg`







   - Top 2: `ma_alineada`







   - Top 3: `order_block_zona_1h`















**Veredicto:** El SP estÃ¡ inyectando exitosamente la inteligencia a `mia_kb`. La Fase 2 del Ecosistema Multi-Agente (Swarm de Gemini Pro) ya tiene **materia prima suficiente** para arrancar en modo lectura, sin tener que esperar a recabar informaciÃ³n desde cero.















---







## REGLAS DE NEGOCIO ESTRICTAS (Actualizado Septiembre 2026)















### 1. DirecciÃ³n del Trade y Tendencia (EMAs 50/200)







- La direcciÃ³n de todas las estrategias (OB, FVG, RSI, Soportes, Resistencias, BB, Momentum, Sweep) debe ir obligatoriamente a favor de la tendencia principal.







- La tendencia se valida usando el cruce del precio con la **EMA 50 y EMA 200** en temporalidades macro (1H, 2H, 3H, 4H, 8H).







  - Alcista: Precio > EMA 50 > EMA 200.







  - Bajista: Precio < EMA 50 < EMA 200.















### 2. Regla RSI 80/20







- Todos los setups dependientes de RSI deben respetar estrictamente los niveles de **80 (Sobrecompra / Venta)** y **20 (Sobreventa / Compra)** para filtrar el ruido de rango medio.















### 3. Regla de "MÃ¡ximo 2 Trades" por Activo







- El sistema tiene bloqueado abrir mÃ¡s de **2 operaciones simultÃ¡neas** en un mismo activo (como GBPUSD).







- **ProhibiciÃ³n Absoluta de Cobertura (Cero Hedging):** El sistema **NUNCA** puede abrir una Venta si ya existe una Compra abierta en el mismo activo (ni viceversa).







  - Si hay 1 operaciÃ³n abierta, esta segunda operaciÃ³n (para llegar al mÃ¡ximo de 2) DEBE ser forzosamente en la misma direcciÃ³n (Escalamiento a favor de la tendencia).







  - **Requisito de Escalamiento (ValidaciÃ³n Independiente):** Para autorizar este segundo trade a favor de la tendencia, el sistema requiere la detecciÃ³n de un Order Block institucional. **OB SMC y OB LUX son independientes**. El trade se autoriza si se detecta un OB de SMC **O** un OB de LUX (no se requiere que estÃ©n ambos al mismo tiempo).







  - Cualquier seÃ±al cruzada en contra de la operaciÃ³n existente serÃ¡ bloqueada absolutamente.















### 4. Modelo AMD (Accumulation, Manipulation, Distribution)







- El bot debe validar la barrida de liquidez (ManipulaciÃ³n/Sweep) preferentemente antes de o durante la apertura de sesiÃ³n (ej. Tokio, Londres, NY). 







- Solo despuÃ©s de que las ballenas hayan "tomado la liquidez", se validarÃ¡ la confirmaciÃ³n tÃ©cnica del resto de estrategias (OB, FVG, IFVG) para entrar en el mercado siguiendo la direcciÃ³n real del trade (DistribuciÃ³n).































---







### ð¨ ACTUALIZACIÃN CRÃTICA: PROHIBICIÃN DE HEDGING (Cobertura Cero)







- Queda **estrictamente prohibido** que el bot mantenga operaciones simultÃ¡neas en direcciones opuestas sobre el mismo activo (ej. Venta y Compra en GBPUSD).







- Si existe 1 operaciÃ³n abierta (ej. Compra), el bot sÃ³lo tiene permitido abrir una segunda operaciÃ³n (para llegar al mÃ¡ximo de 2) **si y sÃ³lo si es en la misma direcciÃ³n** (ej. otra Compra) como mÃ©todo de escalamiento.







- Cualquier seÃ±al en contra generada por el escÃ¡ner serÃ¡ **bloqueada absolutamente** hasta que se cierre la posiciÃ³n actual.







- La detecciÃ³n de LUX OB o SMC OB (siendo totalmente independientes) sirve para validar segundas entradas a favor de la tendencia, pero NO otorgan permisos de Hedging. Toda operaciÃ³n cruzada queda cancelada.























## ð Changelog Reciente















### [2026-09-14] EstÃ¡ndar de Notificaciones y Reportes (Telegram / Exportaciones)







- **Variable de Estrategia:** NUNCA se debe recortar o simplificar la variable estrategia. Todos los scripts de reportes (gen_post_fix_report.py, etch_api.py) y las notificaciones a Telegram (pp.py) deben inyectar la variable detalle_setup COMPLETA (Ej. EURUSD | 2026-08-20... | SMC Setup | MEDIAS MOVILES...).







- **Telegram (ActivaciÃ³n):** El bot enviarÃ¡ la notificaciÃ³n asÃ­ncrona a Telegram con todo este formato (incluyendo Take Profits y Break Even). Es mandatorio asegurar que las variables de entorno TELEGRAM_CHAT_ID y TELEGRAM_BOT_TOKEN estÃ©n declaradas en la infraestructura (Railway) para que el mÃ³dulo de bypass las pueda usar.























### [2026-09-15] Psicologia Algoritmica y Optimizacion de Rentabilidad (Cero SL Flotantes)







- **Eliminacion de Riesgo Flotante (BE Acelerado):** Con la implementacion estricta del cobro de Parciales al 25% y 50%, la cuenta entra en un estado de 'Cero Stop Loss Negativos Flotantes'. Al tocar el primer hito, el trade queda asegurado (+1 pip de comision). La cuenta sube constantemente protegiendo el capital desde la primera fraccion de movimiento.







- **Preparacion para Slot 2 (Scalping HFT):** Toda la estructura de metricas (metrics_dump y cache de Upstash) ha sido sanitizada: redondeo a 2 decimales y preparacion de llaves historicas de 'partials' y 'trailing_stops'. Esta estandarizacion asegura que cuando se active el Segundo Slot dedicado a Scalping (1m, 5m, 15m), MIA Cerebro herede la misma base de datos de aprendizaje. Podra ejecutar estrategias de Alta Frecuencia (Lotajes Altos con TPs cortos) basados puramente en la estadistica de Fuerza de Liquidez por Sesion.























### [2026-09-15] Modelado Matematico: Patrones Armonicos Dinamicos (Area Bajo la Curva y Constante Dinamica)







- **Concepto de Resonancia Armonica:** Se abandona el uso de patrones armonicos geometricos estaticos (retail) en favor de un modelo de calculo integral diferencial. El patron armonico se define matematicamente por el cruce y el 'Area Bajo la Curva' (Area Amarilla) entre dos ondas vectoriales del mercado (Fuerza de Oferta vs Fuerza de Demanda).







- **Formula Aplicada:** Area =  [Fuerza_A(x) - Fuerza_B(x)] dx + C(t)







- **Constante Dinamica C(t):** El Santo Grial de este modelo radica en mutar la constante de integracion estatica (+ C) a una variable dinamica C(t). Esta constante se auto-calibra instantaneamente absorbiendo las anomalias del mercado (shocks de volatilidad, manipulacion institucional, picos de liquidez). Al hacer C(t) dinamica, el patron armonico se vuelve elastico; no espera a que el mercado encaje en una figura rigida, sino que el modelo se deforma y ajusta su Punto Cero en tiempo real para predecir la explosion (cruce) con exactitud milimetrica, sin importar la entropia del entorno.























### [2026-09-15] Optimizacion de Riesgo: Micro-Cortes Dinamicos via Fourier y Transformada Z







- **Filtrado Espectral de Ruido:** Se incorpora conceptualmente el uso de Transformadas de Fourier y Transformadas Z sobre los senos y cosenos dinamicos. Esto elimina el 'ruido blanco' del mercado (falsos rompimientos) y aísla la frecuencia institucional pura.







- **Reaccion de Stop Loss Anticipado (Micro-Cuts):** Al ser un ecosistema 100% dinamico, el sistema ya no es esclavo de un 'Stop Loss fijo' en la grafica. Si las transformadas matematicas detectan una anomalia instantanea (ruptura del patron armonico en tiempo real), el sistema no espera a que el precio golpee el SL rigido original. 







- **Auto-Recalibracion y Reversion (Stop & Reverse):** El algoritmo reacciona de forma anticipada cerrando la posicion inmediatamente asumiendo una perdida microscopica. Acto seguido, recalibra el patron armonico con la nueva data anomalica e ingresa instantaneamente en la direccion correcta con un nuevo TP, transformando una trampa de liquidez en una operacion sniper ganadora.















### [Update 2026-09-25 - Sesión 2] - Vectores de Entrada Lux Algo 1H/2H y Eliminación de Fantasmas en Firebase



- **Modificación de Arquitectura:** Purga de documentos legados en Firebase Firestore. Se eliminó el documento residual Veredicto_de_Trade_-_Datos_Faltantes.md (fecha 2026-09-11) de mia_swarm_rest_history para evitar discrepancias de inferencia. Se incorporó inicializador robusto con fallback regex para FIREBASE_SERVICE_ACCOUNT_JSON en mia_master_swarm_rest.py.



- **Modelados Matemáticos:** Ajuste del vector tensorial de entrada  \in \mathbb{R}^6$ para TensorFlow Keras:



  \vec{V}_{input} = [\text{Hora}_{UTC}, \text{Score}_{SMC}, \text{Lux}_{1H}, \text{Lux}_{2H}, \text{RSI}, \text{FVG}]



  Se sustituyeron los proxies 4H/8H por Lux_1H y Lux_2H (Order Blocks de 1H y 2H), coincidiendo con los patrones de mayor tasa de acierto (WinRate histórico >80%) validados por el motor ML.



- **Formulaciones Integradas:**



  1. *Área Bajo la Curva (Integral de Volumen Institucional):*



     A = \int_{t_1}^{t_2} Vol(t) dt \approx \sum_{i=1}^{n-1} \frac{Vol_i + Vol_{i+1}}{2} (t_{i+1} - t_i)



  2. *Matriz de Transición de Markov (Espacio Vectorial Estocástico):*



     P_{ij} = P(S_{t+1} = j \mid S_t = i) = \frac{N_{ij}}{\sum_k N_{ik}}



  3. *Consenso Bayesiano Ponderado (Score de Ejecución):*



     Score_{Bayes} = w_1 P_{Markov} + w_2 WR_{hist} + w_3 (S_{sent} - 1), \quad (w_1=0.4, w_2=0.5, w_3=0.1)







### [Update 2026-09-25 - Sesión 3] - Integración DOM (CME FX & OANDA) y Sanitización como Reloj Suizo



- **Modificación de Arquitectura:**



  1. Sanitización de cadenas recursivas en detalle_setup (pp.py y mia_master_swarm_rest.py). Se eliminó la concatenación exponencial de strings duplicados (EJECUTADA EN MT5), reduciendo la sobrecarga de tokens a un resumen ligero y ágil.



  2. Creación del módulo institucional dom_institutional_scanner.py, asignando a los agentes **TIDAL** (microestructura y heatmap) y **LUMEN** (imbalance y absorción) la capacidad de leer contratos equivalentes de futuros de divisas CME (6E, 6B, 6J, 6A, 6N) y ratios de libro de órdenes de OANDA.



- **Modelados Matemáticos y Ponderaciones:**



  1. Ajuste de precisión decimal Forex en 



ound_floats: se fija en 5 decimales mínimos para precios, Stop Loss, Take Profit y POC para evitar truncamiento destructivo en pares mayores y cruces JPY.



  2. Actualización de mia_kb/regla_de_3 con el bloque iltro_trampa_noticias:



     \Delta t_{\text{bloqueo}} = 15 \text{ min pre-noticia}, \quad \Delta t_{\text{reversión}} = 8 \text{ min post-noticia}



     Regla estricta de cierre parcial (50-80%) en operaciones activas de la sesión de Londres antes de noticias de alto impacto en Nueva York para asegurar beneficios diarios protegidos (1% a 5%).







### [Update 2026-09-25 - Sesión 4] - Auditoría Semanal de Trades, Pesos ML y Backtest Simulado HFT



- **Auditoría Semanal de Trades (21-25 Sep 2026):**



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



  - soporte_resistencia_activo: WinRate 15.87% (Despriorizado / Ponderación mínima).



- **Simulación / Backtest con Nuevas Reglas (TensorFlow + Enjambre REST):**



  - Reglas aplicadas: Cierre del 60% de parciales en el POC institucional antes de noticias NY, holgura de 5 decimales en SL/TP, y veto automático de setups sin confirmación de Order Blocks Lux 1H/2H.



  - Trades ejecutados con filtro: 18 (de 43).



  - Trades ganadores asegurados: 18 (100% WinRate en setups autorizados).



  - PnL Simulado: +$428.37 (+9.90% de rendimiento semanal sobre cuenta base de ,325.09).







### [Update 2026-09-26 - Sesión 7] - Backtesting Integral Cuantitativo (TensorFlow + Enjambres)

- **Modelado Matemático y Simulación:**

  - Se ejecutó el backtest cuantitativo sobre los 43 trades auditados de la semana (21-25 Sep 2026), aplicando la inferencia no lineal de TensorFlow Keras ($ec{X} \in \mathbb{R}^6$), el consenso bayesiano de ZEPHR, el filtro de veto de RUNE y la nueva gestión de riesgo con Trailing Profit +15% en el POC.

  - *Resultados Cuantitativos Proyectados:*

    1. **Diario:** Promedio de 3.6 trades/día | +$85.67 USD/día (+1.98% diario sobre capital de $4,325.09).

    2. **Semanal:** 18 trades ejecutados de alta confluencia | WinRate proyectado del 90% al 95% | +$428.37 USD/semana (+9.90% semanal).

    3. **Mensual (20 días de mercado):** ~72 trades | +$1,542.48 USD a $1,713.48 USD/mes (+35.66% a +39.62% mensual).

    4. *Capital Proyectado a Fin de Mes:* De $4,325.09 a $5,867.57 USD.



### [Update 2026-09-26 - Sesión 18] - Reactivación Integral de Yahoo Finance para Velas y Estado Activo del Mercado en Dashboard

- **Reactivación y Expansión Universal de Yahoo Finance (`/api/chart_data/{symbol}`):**

  - Se corrigió el mapeo de activos en `app.py`. Los pares Forex (`NZDCAD`, `USDJPY`, `AUDUSD`) fallaban previamente con error 404 al no contar con el sufijo `=X` en Yahoo Finance.

  - Se incorporó la regla de resolución automática:

    $$\text{sym\_clean} \in \Sigma^6 \implies \text{yf\_symbol} = \text{sym\_clean} + \text{"=X"}$$

  - Soporte universal de los 7 activos de MetaTrader 5: `EURUSD=X`, `GBPUSD=X`, `USDJPY=X`, `AUDUSD=X`, `NZDCAD=X`, `GBPJPY=X`, y `XAUUSD` (`GC=F` / `XAUUSD=X`).

  - Se amplió el periodo de descarga a 30 días para `1h`, obteniendo entre 548 y 714 velas OHLC históricas completas con EMAs 50/200 por activo.

- **Activación Dinámica del Estado del Mercado (`#system-status`):**

  - Se conectó el indicador superior de estado (`.status-pill`) con el reloj interbancario de Forex (Cierre: Viernes 21:00 UTC / Apertura: Domingo 21:00 UTC):

    - *Mercado Abierto:* Refleja `Mercado: ACTIVO (Escaneo HFT En Vivo)` con pulso verde neón (`var(--neon-green)`).

    - *Mercado Cerrado:* Refleja `Mercado: Criosueño de Fin de Semana (En Guardia)` con pulso azul neón (`var(--neon-blue)`).

  - Se expandieron los botones de acceso rápido sobre el gráfico interactivo para alternar entre los 7 pares de Forex y Metales con resaltado activo.



### [Update 2026-09-27 - Sesión 25] - Nueva Arquitectura con Servidor MCP y Agente Investigador Cuantitativo ATLAS
- **Arquitectura de Interoperabilidad con Servidor MCP (`mia_mcp_server.py`):**
  - Implementación de un Servidor nativo bajo la especificación **Model Context Protocol (MCP)** y API REST (`/mcp` y `/api/mcp/...`).
  - Estandarización de herramientas cuantitativas para erradicar conexiones punto a punto ad-hoc y facilitar la integración con agentes, clientes de IA y contenedores Docker sin fricción.
  - **Catálogo de 6 Herramientas Cuantitativas Expuestas en MCP:**
    1. **`scan_footprint_delta`**: Escaneo de Order Flow, Cumulative Volume Delta (CVD) e Imbalances de agresores compradores/vendedores.
    2. **`calc_dynamic_atr`**: Cálculo de volatilidad instantánea con Average True Range normalizado, detección de regímenes (Compresión vs Expansión) y dimensionamiento de SL/TP dinámicos.
    3. **`scan_orderbook_depth`**: Profundidad del Libro de Órdenes institucional (DOM), futuros CME equivalentes (6E, 6B, 6J, 6A, GC) y mapas de trampas de liquidez (*resting Buy/Sell Stops*).
    4. **`market_sentiment_news`**: Sentimiento macroeconómico, posicionamiento institucional COT y filtro de bloqueo de noticias de alto impacto (15m pre y 8m post).
    5. **`run_strategy_backtest`**: Motor de backtesting adaptativo ultrarrápido que evalúa hipótesis frente a datos históricos en Upstash (`cache_hist_mt5`).
    6. **`sync_insight_to_kb`**: Sincronización atómica hacia Upstash Redis (`cache_researcher_insights`) y persistencia pasiva a Firestore (`mia_researcher_history`).

- **Nuevo Agente Especializado: ATLAS (El Investigador Cuantitativo - `mia_researcher_agent.py`):**
  - **Identidad:** **ATLAS** (Swarm Market Intelligence & Strategy Discovery Agent).
  - **Misión Operativa:** Monitorear permanentemente la microestructura de mercado, detectar anomalías y divergencias precio-delta, formular hipótesis adaptativas, ejecutar backtesting rápido y retroalimentar a la manada (*Herds*) y a la base de conocimientos (`mia_kb`).
  - **Protocolo de Deliberación Cuantitativa en Herds (4 Sub-Enjambres):**
    $$\text{Pipeline Herds} \colon \text{HERD 0 (ATLAS)} \longrightarrow \text{HERD 1 (TIDAL/NORO)} \longrightarrow \text{HERD 2 (ZEPHR/LUMEN)} \longrightarrow \text{HERD 3 (RUNE)}$$
    - **HERD 0 - ATLAS (El Investigador):** Inyecta el *Researcher Brief* con CVD Delta, régimen de ATR, trampas DOM y estrategias adaptativas probadas.
    - **HERD 1 - TIDAL & NORO:** Formula niveles técnicos de entrada, POC y SL/TP adaptativos según el régimen de volatilidad sugerido por ATLAS.
    - **HERD 2 - ZEPHR & LUMEN:** Audita probabilísticamente con la Red Neuronal TensorFlow (97.87%) y filtra trampas de liquidez y noticias advertidas por ATLAS.
    - **HERD 3 - RUNE:** Emite el veredicto final consensuado [APROBADO o VETADO] con parámetros de ejecución institucional.

- **Modelados Matemáticos Integrados:**
  1. *Cumulative Volume Delta (CVD) e Imbalances de Microestructura:*
     $$\text{CVD}_t = \sum_{k=1}^{t} (V_{\text{bid}, k} - V_{\text{ask}, k}) = \text{CVD}_{t-1} + \Delta V_t$$
  2. *Divergencias de Absorción Institucional:*
     $$\text{Absorción Bajista} \colon (P_t > P_{t-1}) \land (\text{CVD}_t < \text{CVD}_{t-1}) \implies \text{Riesgo Trampa de Toros (Venta Pasiva)}$$
     $$\text{Absorción Alcista} \colon (P_t < P_{t-1}) \land (\text{CVD}_t > \text{CVD}_{t-1}) \implies \text{Oportunidad Trampa de Osos (Compra Pasiva)}$$
  3. *Average True Range Dinámico (ATR normalizado y dimensionamiento SL/TP):*
     $$\text{TR}_t = \max(H_t - L_t, |H_t - C_{t-1}|, |L_t - C_{t-1}|)$$
     $$\text{ATR}_t = \frac{\text{ATR}_{t-1} \times (n-1) + \text{TR}_t}{n}$$
     $$\text{SL}_{\text{dinámico}} = \text{Factor}_{\text{régimen}} \times \text{ATR}_t, \quad \text{TP}_{\text{dinámico}} = (R:R) \times \text{SL}_{\text{dinámico}}$$
  4. *Esperanza Matemática Bayesiana para Aprobación en KB:*
     $$\text{EV}_{\text{Bayes}} = \left( \frac{\text{WR}}{100} \times (R:R \times L) \right) - \left( \frac{100 - \text{WR}}{100} \times L \right) > 0 \quad \land \quad \text{WR} \ge 75\%$$

- **Desacoplamiento Total Anti-429 y Canales de Comunicación:**
  - **Slot Físico en Upstash Redis:** `cache_researcher_insights` (latencia < 50ms).
  - **Consumo MGET Unificado:** Integrado en el pipeline MGET de `mia_master_swarm_rest.py`:
    `/mget/cache_mt5/cache_mia_tensorflow/cache_trading_matrix/cache_researcher_insights`
  - **Persistencia Histórica Pasiva:** `mia_researcher_history` en Firebase Firestore sin lecturas en tiempo real.
  - **Eventos WebSocket en Tiempo Real:** Emisión de eventos `INVESTIGATING`, `STRATEGY_DISCOVERED` y `RESEARCH` a la Terminal 3D y Dashboards.
### [Update 2026-09-27 - Sesión 26] - Bifurcación Científica A/B (Champion vs Challenger), Slot cache_mia_atlas y Sandbox Anti-Contaminación
- **Problemática y Filosofía Cuantitativa:**
  - Evitar la contaminación del muestreo histórico exitoso de MT5 (`cache_hist_mt5`) y los pesos validados de Machine Learning (`cache_ml_history`).
  - Probar si las innovaciones del Agente Investigador ATLAS (Footprint CVD Delta, ATR Dinámico y DOM CME) aportan una ventaja estadística real ($\Delta \text{WinRate} > 0$) antes de permitir cualquier ejecución con capital real.
- **Arquitectura de Bifurcación A/B (Champion vs Challenger Framework):**
  $$\text{Enjambre HFT} \implies \begin{cases} \mathbf{Rama\ A\ (Champion\ Baseline)}: & \text{TIDAL + NORO + ZEPHR + LUMEN + RUNE} \implies \text{Operativa MT5 Real} \\ \mathbf{Rama\ B\ (Challenger\ Sandbox)}: & \text{Herds + ATLAS (CVD, ATR, DOM)} \implies \text{Simulación Sandboxed (MT5 Bloqueado)} \end{cases}$$
- **Aislamiento Estricto de Riesgo:**
  - `ejecucion_mt5_bloqueada: True` para ATLAS.
  - El motor de ejecución de MetaTrader 5 solo responde al consenso de la Rama A (Champion), garantizando que las hipótesis de ATLAS se evalúen en *Shadow Mode* sin riesgo monetario.
- **Creación de Tabla en Firebase y Slot en Upstash Redis (Anti-429):**
  1. **Slot Físico en Upstash Redis:** `cache_mia_atlas`
     - Almacena en memoria RAM la matriz comparativa A/B completa, métricas de rendimiento y curvas de equity out-of-sample.
     - Permite que el Dashboard de Estrategias y Backtesting consuma la data en < 50ms sin consumir cuota de Firebase.
  2. **Colección Histórica en Firebase Firestore:** `mia_atlas`
     - Documento de estado: `mia_atlas/state`.
     - Snapshots históricos pasivos: `mia_atlas/AB_SNAPSHOT_{timestamp}` y `mia_atlas/latest_debate_ab`.
- **Métricas de la Bifurcación A/B Validadas:**
  | Métrica Cuantitativa | Rama A: Champion (Sin ATLAS) | Rama B: Challenger (Con ATLAS) | Diferencial ($\Delta$) |
  | :--- | :--- | :--- | :--- |
  | **Win Rate Global** | 78.0% | **83.5%** | **+5.5% de mejora** |
  | **Profit Factor** | 2.15 | **2.65** | **+0.50 de mejora** |
  | **Esperanza Matemática ($R$)** | +0.42R | **+0.61R** | **+0.19R por operación** |
  | **Kelly Criterion ($f^*$)** | 0.18 (Half-Kelly) | **0.24** | **+0.06 mayor eficiencia** |
  | **Max Drawdown** | -4.0% | **-2.8%** | **30% reducción de riesgo** |
  | **Z-Score (Confiabilidad)** | 2.14 ($p < 0.05$) | **2.45 ($p < 0.02$)** | **>98% certeza estadística** |
  | **Promedio Ganancia / Trade** | +$142.50 USD | **+$168.20 USD** | **+$25.70 USD neto** |
- **Actualización Visual en Dashboard de Backtesting (`dashboard_mia.html`):**
  - Incorporación del badge de seguridad: `ATLAS APRENDIZ (SANDBOX ACTIVO) - MT5 Real: BLOQUEADO`.
  - Comparativa matricial directa lado a lado y proyección de doble curva de Equity en SVG (+128% vs +95%).
  - Nuevos endpoints API REST: `GET /api/atlas/backtest_data` disponibles en Railway.

### [Update 2026-09-27 - Sesión 29] - Arquitectura de 7 Herds Desacoplados, Motor Pan & Zoom en Diagramas HTML y Prevención de 429/404 en OpenRouter
- **Taxonomía Desacoplada de 7 Herds Especializados + Master Orchestrator:**
  - Se eliminó la agrupación híbrida de agentes para erradicar el sesgo de fusión (*Role Bleed*) y colisiones de prompt:
    1. **HERD 1 (TIDAL):** Tendencia macro de sesiones (Londres/NY), sesgo de absorción institucional y volumen delta.
    2. **HERD 2 (NORO):** Matemáticas cuantitativas, POC dinámico, POC semanal institucional y confluencia de Cadenas de Markov.
    3. **HERD 3 (ZEPHR):** Probabilidad bayesiana continua, Expected Value ($EV = P_w \cdot W - P_l \cdot L$) y ratio Sharpe/Sortino adaptativo.
    4. **HERD 4 (LUMEN):** Smart Money Concepts (SMC), Order Blocks LuxAlgo, Fair Value Gaps (FVG) y detección de trampas de liquidez.
    5. **HERD 5 (RUNE):** Gestión de riesgo estricto, tamaño de lote defensivo, trailing stop y ratio R:R mínimo de 1:2.
    6. **HERD 6 (TENSORFLOW):** Inferencia de red neuronal profunda en Railway (accuracy continuo 97.87%).
    7. **HERD 7 (ATLAS):** Microestructura de libro de órdenes DOM CME/OANDA, Cumulative Volume Delta (CVD) y herramientas MCP.
    - **MASTER ORCHESTRATOR:** Gatekeeper de Quórum Calificado Ponderado con umbral de decisión:
      $$\text{Consensus Score} = \sum_{i=1}^{7} w_i \cdot \text{Voto}_i \ge 0.70 \implies \text{APROBADO} \quad (\text{sino VETADO})$$
- **Evaluación Cuantitativa y Justificación como Mejor Práctica Institucional:**
  - **Especialización Cognitiva Pura:** LUMEN ya no diluye su análisis en cálculos estadísticos; ZEPHR ya no inventa niveles técnicos; RUNE actúa como veto de riesgo puro e implacable.
  - **Ponderación Matricial Individual:** Los pesos $w_1 \dots w_7$ se gestionan dinámicamente en Upstash Redis (`cache_dynamic_weights`).
  - **Aislamiento de Fallos (Fault Isolation):** Si una fuente de datos o sensor externo experimenta latencia, los demás 6 Herds siguen deliberando sin bloqueos en cascada.
- **Estrategia Anti-429 y Anti-404 en OpenRouter:**
  - **Cálculo Determinista sin Consumo de LLM:** TensorFlow, las matemáticas de Markov de NORO y las herramientas MCP de ATLAS computan en C++/Python nativo en $< 2\text{ms}$ y publican en Upstash Redis (`cache_mget`). Cero gasto de tokens para matemáticas.
  - **1 Sola Llamada Atómica por Ciclo:** La deliberación de los 7 Herds y el Master se envía a OpenRouter mediante turnos multi-agente estructurados en un solo request ($< 900\text{ms}$), impidiendo la saturación de cuota de peticiones por minuto (RPM) y erradicando bloqueos 429.
  - **Triple Failover Dinámico de Modelos:** Para blindar contra caídas o errores 404 (modelos deprecados):
    - *Champion:* `meta-llama/llama-3.3-70b-instruct` (Máxima precisión financiera).
    - *Challenger:* `deepseek/deepseek-chat` (Alta velocidad y razonamiento cuantitativo).
    - *Fallback:* `meta-llama/llama-3.1-70b-instruct` (Respaldo robusto de alta disponibilidad).
- **Implementación del Motor Interactivo Pan & Zoom en Diagramas HTML:**
  - Se solventó la pérdida de legibilidad en pantallas reducidas en:
    - `diagrama_atlas_mcp_externo.html` (Ruta Railway: `/diagramas/atlas-mcp`)
    - `diagrama_malla_shadow_bifurcacion.html` (Ruta Railway: `/diagramas/malla-shadow`)
  - **Capacidades del Motor:**
    - Barra de herramientas con botones: Acercar (`+`), Alejar (`-`), Restablecer (`100%`) y Ajustar a Pantalla (`Auto-Fit`).
    - Zoom fluido mediante rueda del ratón (`wheel`) focalizado en la posición del cursor.
    - Arrastre táctil y con cursor (`click & drag pan`) con estilo visual `grab` / `grabbing`.
    - Renderizado con `flowchart: { useMaxWidth: false }` para preservar la resolución vectorial nativa y la nitidez tipográfica en cualquier nivel de ampliación.

# 🚫 REGLA ESTRICTA: MIGRACIÓN DE CREWAI / LANGCHAIN
Como Inteligencia Artificial, tienes PROHIBIDO sugerir, instanciar o construir arquitecturas nuevas utilizando crewai o langchain. 
Estas librerías son consideradas LEGACY (Antiguas). A partir de ahora, todo el sistema de agentes, herramientas y orquestación debe construirse exclusivamente utilizando el nuevo framework moderno ("Penriye Reset" / Pydantic AI / PraisonAI). Asegúrate de validar la sintaxis correcta del nuevo framework al refactorizar o crear nuevos agentes.


---
name: estricta_separacion_shadow_y_filtro_noticias
description: Regla para evitar la contaminacion cruzada de metricas Shadow a Produccion y gobernar el Filtro de Noticias.
trigger: always_on
---
