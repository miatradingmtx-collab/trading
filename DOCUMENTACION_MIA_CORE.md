---
tags:
  - arquitectura
  - documentacion-core
  - hft
  - webhook
  - multi-agentes
fecha: 2026-08-25
---

# ð§  DOCUMENTACIÃN CORE DE MIA TRADING AI

# ð§  MIA KB: VectorizaciÃ³n del Sweep y Ciclo AMD

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

## ð¬ Anexo Machine Learning: El Escenario 6 (BifurcaciÃ³n)
Para alimentar la base de datos de entrenamiento del ML y poder comparar el rendimiento de estrategias *con* Sweep vs *sin* Sweep, se codificÃ³ el **Escenario 6 (Indicador Puro Lux)**.

**LÃ³gica de Aislamiento:**
- Si el escÃ¡ner (`mt5_executor_cloud.py`) detecta un **Order Block Institucional (Mapa de calor Lux simulado)** sin mezclas de FVGs ni retail:
  1. El backend le inyecta un score forzado de `85.0` (Bypass de validaciÃ³n).
  2. El ejecutor en la nube hace un **Bypass de la Regla de Riesgo (Doble Trade)**, permitiendo abrir la operaciÃ³n en MT5 aunque el activo ya estÃ© operando otra estrategia.
- **Objetivo ML:** Medir estadÃ­sticamente el WinRate de los OBs institucionales de alto volumen en estado puro, separÃ¡ndolos del resto de escenarios que requieren validaciÃ³n de Sweep y Tendencia.

## 4. Arquitectura de OptimizaciÃ³n de Base de Datos (Memoria CachÃ© RAM)
Para evitar cuellos de botella y errores por lÃ­mite de cuota en Firebase (Ej. 429 Quota Exceeded), **absolutamente todas las consultas recurrentes y monitoreos de estado deben hacerse contra la CachÃ© RAM local del bot (POSICIONES_ACTIVAS, diccionarios en memoria o variables globales) y NO directamente contra la base de datos.**
- **SincronizaciÃ³n PeriÃ³dica:** La estructura estÃ¡ diseÃ±ada para volcar y guardar la informaciÃ³n en Firebase cada 30 segundos mediante rutinas asÃ­ncronas de fondo.
- **Lectura:** Cuando se requiera analizar la matriz, calcular scores, generar reportes o validar el estado de un trade en vivo, se debe leer la informaciÃ³n de la memoria cachÃ©, que es la fuente de la verdad en tiempo de ejecuciÃ³n, en lugar de saturar Firestore con peticiones de lectura constantes.

---

# ð§  MIA KB: OptimizaciÃ³n HFT y Blindaje de Cuotas (Firebase Juez)

Este documento actÃºa como puente (MD Bridge) para sincronizar las Ãºltimas actualizaciones de la arquitectura base de MÃ­a hacia la base de conocimiento, con enfoque en la protecciÃ³n de las cuotas de Firebase (Read/Writes).

## 1. Contexto: El Problema (Error 429 - Quota Exceeded)
Con la implementaciÃ³n del ciclo HFT de MetaTrader 5 (escaneos cada 30 y 60 segundos), el trÃ¡fico hacia Firebase se volviÃ³ exponencial.
- **MT5 Scanner (60s):** EscribÃ­a el estado de los indicadores de forma forzada a la base de datos 1,440 veces al dÃ­a por activo.
- **Cache Local (30m):** Descargaba 800 logs histÃ³ricos cada media hora (38,400 lecturas/dÃ­a).
- Esto saturaba la cuota gratuita (50k lecturas, 20k escrituras), tirando el servidor (Error 429) e interrumpiendo el flujo de MÃ­a.

## 2. ImplementaciÃ³n: La SoluciÃ³n (El Escudo RAM)
Se inyectaron 3 murallas de contenciÃ³n en el servidor backend (FastAPI - `app.py`) para aislar a Firebase y dejarlo puramente como un **Juez Supremo** que solo habla cuando es estrictamente necesario:

### A. CachÃ© Global en RAM (Lecturas = 0)
- **`GLOBAL_MATRICES_CACHE_FULL`**: Todas las consultas de MetaApi/MT5 (que se hacen cada 30 segundos preguntando por permisos de lotaje o entrada) chocan ahora contra la memoria RAM de Python. No consumen lecturas de Firebase.
- **Bypass del Dashboard**: El portal web de KPIs `/api/dashboard_data` tiene un *Bypass Total*. Se alimenta exclusivamente de la RAM, independientemente de cuÃ¡ntos usuarios estÃ©n viendo la grÃ¡fica.

### B. Espejo DinÃ¡mico (Filtro de Escrituras)
- El webhook tÃ©cnico recibe los datos del scanner de MT5 cada 60 segundos.
- Antes de ordenar un `doc_ref.set()`, el backend compara si las confirmaciones tÃ©cnicas (Order Blocks, FVGs, Tendencia) **cambiaron** respecto al minuto anterior.
- Si el mercado no ha hecho movimientos clave (todo sigue idÃ©ntico), se aborta la escritura y Firebase permanece intacto. Ahorro masivo del 98% en cuota de escrituras.

### C. Parche de LÃ­mite de Recarga
- El ciclo de recarga de 30 minutos se redujo de `limit(800)` a `limit(150)` sobre la tabla `mia_audit_logs`. Esto bajÃ³ el consumo fijo de 38,400 lecturas a solo **7,200 lecturas diarias**.

## 3. DesconexiÃ³n de Agentes Secundarios
Para aislar el laboratorio de MÃ­a por las prÃ³ximas 3 semanas:
- **n8n y Postgres:** Pasados a modo `Offline` en Railway.
- **El Cerebro:** El Machine Learning ahora es impulsado internamente vÃ­a `APScheduler` (FunciÃ³n `entrenar_pesos_dinamicos`) todos los viernes a las 16:00, leyendo un histÃ³rico de 500 operaciones para ajustar los pesos sin sobrecarga externa.

## 4. Resultado Final
MÃ­a puede procesar y cazar la liquidez de los ciclos *AMD (Accumulation, Manipulation, Distribution)* 24/5 sin ningÃºn temor a que la base de datos se caiga por trÃ¡fico excesivo. La recolecciÃ³n de datos y el ranking de estrategias tienen total libertad de operaciÃ³n.

## 5. REGLA DE ORO PARA EL AGENTE DE IA (LLMs y Scripts)
Al analizar historiales, homologar reportes o validar la 'Regla de 3', **SE PROHÃBE AL AGENTE (IA) CREAR SCRIPTS PYTHON QUE HAGAN BARRIDOS MASIVOS (stream()) CONTRA FIREBASE**. Todo script de reporte debe apuntar a la CachÃ© RAM o limitar drÃ¡sticamente sus consultas. Los barridos directos saturan la cuota gratuita inmediatamente causando el error 429.

---

# ð§  MIA KB: Webhooks (MT5/Firebase) y LÃ­mites de Riesgo (2 Trades)

Este documento sincroniza los cambios arquitectÃ³nicos implementados en `app.py` para corregir la mensajerÃ­a del sistema y proteger el capital controlando el riesgo de mÃºltiples trades en cascada.

## 1. El Mito de TradingView (CorrecciÃ³n de Webhook)
HistÃ³ricamente, los logs del sistema y los mensajes de Telegram indicaban errÃ³neamente: `ALERTA RECIBIDA DE TRADINGVIEW`.
Esto causaba confusiÃ³n arquitectÃ³nica porque **TradingView no se conecta directamente al webhook de ejecuciÃ³n de MIA**. 
- El Ãºnico y verdadero juez es **Firebase**.
- Quien dispara los Webhooks de `EJECUTADO`, `CIERRE_PARCIAL`, y `CIERRE_TOTAL` es **MT5 / MetaApi** a travÃ©s de Botpress.
**SoluciÃ³n:** Se corrigiÃ³ permanentemente el registro en el servidor y en la recuperaciÃ³n de la cachÃ© (memoria RAM), pasando a ser `ALERTA RECIBIDA EN WEBHOOK (MT5/FIREBASE)`. Al usar Firebase como juez supremo (homologado para todos los activos), tambiÃ©n se solucionÃ³ el bug donde los cierres marcaban "Estrategia: MANUAL", logrando recuperar la estrategia institucional original cruzando los tickets o el nombre del activo en la RAM Cache.

## 2. Bloqueo Estricto de Trades Concurrentes (Risk Management)
Cuando el semÃ¡foro tÃ©cnico alcanzaba el 80%, se autorizaba la apertura de un trade. Si el mercado retrocedÃ­a temporalmente bajando el score (volviendo a `INACTIVO`) y luego recibÃ­a una nueva alerta que lo subÃ­a a 80%, MIA abrÃ­a un trade adicional, superando el lÃ­mite analÃ­tico diseÃ±ado para poner a prueba los Order Blocks (SMC vs Lux Algo).

**ImplementaciÃ³n del Candado:**
Se inyectÃ³ una doble validaciÃ³n en `app.py` (webhook MT5 y evaluaciÃ³n de semÃ¡foro):
`if len(operaciones_activas) >= 2:`
A partir de ahora, ningÃºn activo (como el AUD) podrÃ¡ superar los 2 trades activos (ej. 1 SMC y 1 Lux), protegiendo la gestiÃ³n de riesgo.

## 3. LÃ³gica de Trailing Stop y Break Even
El backend en Python ahora extrae el `precio_apertura` del histÃ³rico (si ocurre un `CIERRE_PARCIAL` o `CIERRE_TOTAL`) para calcular de forma milimÃ©trica las distancias a los Take Profits (TP1 25%, TP2 50%, Full TP). 
Si se cierran parciales con ganancia o el trade toca el trailing stop, los mensajes de Telegram dibujan dinÃ¡micamente un checkmark (`â`) indicando que el mercado alcanzÃ³ dicha rentabilidad antes de regresar, honrando la protecciÃ³n del capital (Break Even).
*Nota CrÃ­tica:* El deslizamiento del Stop Loss (Breakà¦«à¦à§à¦¨ a 25% o 50%) **lo ejecuta exclusivamente el Robot (EA) dentro de MetaTrader 5 / Botpress**. Se debe asegurar que las variables de entrada (inputs) del Trailing Step estÃ©n correctamente homologadas y activas en todos los activos operados en la terminal MT5, ya que Python actÃºa como receptor del PNL final, no como el ejecutor tic-a-tic.

---

# ð§  VALIDACIÃN DE ALIMENTACIÃN DE DATOS (STORED PROCEDURE)
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
### ð¨ ACTUALIZACIÃN CRÃTICA: PROHIBICIÃN DE HEDGING (Cobertura Cero)
- Queda **estrictamente prohibido** que el bot mantenga operaciones simultÃ¡neas en direcciones opuestas sobre el mismo activo (ej. Venta y Compra en GBPUSD).
- Si existe 1 operaciÃ³n abierta (ej. Compra), el bot sÃ³lo tiene permitido abrir una segunda operaciÃ³n (para llegar al mÃ¡ximo de 2) **si y sÃ³lo si es en la misma direcciÃ³n** (ej. otra Compra) como mÃ©todo de escalamiento.
- Cualquier seÃ±al en contra generada por el escÃ¡ner serÃ¡ **bloqueada absolutamente** hasta que se cierre la posiciÃ³n actual.
- La detecciÃ³n de LUX OB o SMC OB (siendo totalmente independientes) sirve para validar segundas entradas a favor de la tendencia, pero NO otorgan permisos de Hedging. Toda operaciÃ³n cruzada queda cancelada.


## ð Changelog Reciente

### Septiembre 2026
- **MigraciÃ³n a Upstash Redis:** Se eliminÃ³ la dependencia de Firebase/Railway RAM para el cachÃ©, pasando a Upstash (Serverless Redis) para prevenir bloqueos Error 429.
- **OptimizaciÃ³n de Groq (8000 TPM):** Se redujo el enjambre temporalmente de 8 a 4 agentes CORE (TIDAL, NORO, ZEPHR, RUNE) para cumplir la cuota.
- **Velocidad de ejecuciÃ³n:** Se eliminÃ³ el sleep individual por agente y se configurÃ³ un ciclo de 35 segundos.
- **Modelo Llama 3.3:** MigraciÃ³n forzada al modelo llama-3.3-70b-versatile en Groq tras el retiro del modelo 3.1.

- **Failover Dinï¿½mico de IA (Groq + Gemini):** Implementaciï¿½n de una arquitectura tolerante a fallos para operar 24/7 de forma gratuita. El motor principal (ChatGroq con groq/compound-mini) absorbe las primeras ~25 corridas del dï¿½a usando el lï¿½mite de 500k TPD de Llama. Al recibir el error 429 (RateLimit), LangChain enruta instantï¿½neamente la peticiï¿½n a ChatGoogleGenerativeAI (gemini-1.5-flash), el cual procesa las ~70 corridas restantes del dï¿½a (usando su lï¿½mite de 1500 peticiones diarias). Este diseï¿½o de ciclo infinito cubre perfectamente las 96 corridas diarias necesarias (bucle de 15 minutos).
- **Desacoplamiento de Cuentas MetaApi:** MetaApi bloquea la ediciï¿½n del *Account Login* una vez desplegado. Para migrar la cuenta, se implementï¿½ el protocolo de 'Eliminaciï¿½n y Recreaciï¿½n Automï¿½tica'. El usuario elimina el slot en MetaApi, y el script asï¿½ncrono (mt5_executor_cloud.py) detecta la ausencia del ID, recreando automï¿½ticamente la cuenta mediante la API interna con los parï¿½metros de la nueva cuenta (112472341).
- **MetaApi Localidad (NY vs London):** La ubicaciï¿½n elegida (ackup-new-york o london) solo determina el servidor fï¿½sico de ping hacia el broker, no afecta el Timestamp (UTC) ni la sincronizaciï¿½n de las velas. El UTC siempre lo rige el servidor del Broker (ej. EET en MetaQuotes-Demo).
- **Validaciï¿½n de ï¿½ndices:** Si los ï¿½ndices (US30, US500, USTEC) aparecen 'en gris', significa que el servidor gratuito de prueba (MetaQuotes-Demo) restringe la operativa de ï¿½ndices por horarios cerrados o bloqueos de cuenta; en estos casos, el bot seguirï¿½ operando automï¿½ticamente en el ecosistema Forex (24/5) sin interrupciones.


### Septiembre 2026 (Actualizaciï¿½n de Arquitectura y Machine Learning)
- **Modo Recopilaciï¿½n del Enjambre:** El Enjambre Groktopus se mantiene en fase de anï¿½lisis pasivo (Recabando Data y Veredictos), mientras que la ejecuciï¿½n real en MT5 sigue dictada por el Juez de Firebase.
- **Failover Dinï¿½mico de 5 Capas (Indestructible):** Se migrï¿½ de un modelo dual a una arquitectura de 5 respaldos: Llama 3.3 (70B) -> Llama 3.1 (8B) -> Mixtral -> Gemma2 -> Gemini 2.5 Flash. Esto proporciona +1.6 Millones de tokens diarios gratuitos, permitiendo operaciï¿½n 24/5 ininterrumpida. Tambiï¿½n se incorporï¿½ un 	ime.sleep(20) para evadir los lï¿½mites de 5 RPM (Request Per Minute) estrictos de Gemini en la capa gratuita.
- **Cancelaciï¿½n de Delegaciï¿½n en CrewAI:** Se desactivï¿½ llow_delegation=False en todos los agentes para forzar una lï¿½nea de ensamblaje recta (TIDAL -> NORO -> ZEPHR -> RUNE) y prevenir bucles infinitos de agentes rebotando tareas entre ellos.
- **Variable Morgan (V_M) y ï¿½lgebra Lineal:** Se oficializï¿½ la fï¿½rmula del filtro absoluto: V_M = Fuerza_AUC * Sum(W_i * X_i). La matriz booleana comprobï¿½ que conceptos Retail puros (FVG, Sweep aislados) devuelven Win Rate de 0%. El algoritmo exige la presencia de Lux Algo Order Blocks (X1) para validar un trade. 
- **Desacoplamiento de Memoria de Enjambres a Upstash:** La memoria de los anï¿½lisis de RUNE se desvinculï¿½ de los contenedores efï¿½meros de Railway. Ahora se utiliza obsidian_writer_tool para realizar un POST directo hacia Upstash Redis (mia_swarm_history_[Nombre]), guardando el histï¿½rico perpetuo sin saturar la cachï¿½ viva (cache_mt5).


### [2026-09-14] EstÃ¡ndar de Notificaciones y Reportes (Telegram / Exportaciones)
- **Variable de Estrategia:** NUNCA se debe recortar o simplificar la variable estrategia. Todos los scripts de reportes (gen_post_fix_report.py, etch_api.py) y las notificaciones a Telegram (pp.py) deben inyectar la variable detalle_setup COMPLETA (Ej. EURUSD | 2026-08-20... | SMC Setup | MEDIAS MOVILES...).
- **Telegram (ActivaciÃ³n):** El bot enviarÃ¡ la notificaciÃ³n asÃ­ncrona a Telegram con todo este formato (incluyendo Take Profits y Break Even). Es mandatorio asegurar que las variables de entorno TELEGRAM_CHAT_ID y TELEGRAM_BOT_TOKEN estÃ©n declaradas en la infraestructura (Railway) para que el mÃ³dulo de bypass las pueda usar.


### [2026-09-15] Estandar de Base de Datos y Cache (Swarms y Auditoria)
- **Prohibicion de etiqueta MANUAL:** Queda estrictamente prohibido guardar trades con la estrategia MANUAL en mia_audit_logs si se trata de un trade huerfano o reportado tras un fallo del broker. El sistema (app.py) DEBE hacer un barrido del string detalle_setup, extraer la estrategia original y asignarla correctamente.
- **Fuente de Verdad de los Enjambres:** La cache de los enjambres en Upstash (mia_swarm_history_*) es la fuente primaria. Esta misma data se usa para crear y poblar la coleccion swarm_history en Firebase. Ya se realizo la migracion de los datos existentes.
- **Consultas Aisladas:** Los Enjambres (Groktopus) tienen PROHIBIDO consultar Firebase directamente. Todas sus lecturas se hacen a traves del slot aislado de Upstash Redis (railway_cache_tool) para proteger la cuota de la base de datos.


### [2026-09-15] Psicologia Algoritmica y Optimizacion de Rentabilidad (Cero SL Flotantes)
- **Eliminacion de Riesgo Flotante (BE Acelerado):** Con la implementacion estricta del cobro de Parciales al 25% y 50%, la cuenta entra en un estado de 'Cero Stop Loss Negativos Flotantes'. Al tocar el primer hito, el trade queda asegurado (+1 pip de comision). La cuenta sube constantemente protegiendo el capital desde la primera fraccion de movimiento.
- **Preparacion para Slot 2 (Scalping HFT):** Toda la estructura de metricas (metrics_dump y cache de Upstash) ha sido sanitizada: redondeo a 2 decimales y preparacion de llaves historicas de 'partials' y 'trailing_stops'. Esta estandarizacion asegura que cuando se active el Segundo Slot dedicado a Scalping (1m, 5m, 15m), MIA Cerebro herede la misma base de datos de aprendizaje. Podra ejecutar estrategias de Alta Frecuencia (Lotajes Altos con TPs cortos) basados puramente en la estadistica de Fuerza de Liquidez por Sesion.


### [2026-09-15] Modelado Matematico: Patrones Armonicos Dinamicos (Area Bajo la Curva y Constante Dinamica)
- **Concepto de Resonancia Armonica:** Se abandona el uso de patrones armonicos geometricos estaticos (retail) en favor de un modelo de calculo integral diferencial. El patron armonico se define matematicamente por el cruce y el 'Area Bajo la Curva' (Area Amarilla) entre dos ondas vectoriales del mercado (Fuerza de Oferta vs Fuerza de Demanda).
- **Formula Aplicada:** Area = ? [Fuerza_A(x) - Fuerza_B(x)] dx + C(t)
- **Constante Dinamica C(t):** El Santo Grial de este modelo radica en mutar la constante de integracion estatica (+ C) a una variable dinamica C(t). Esta constante se auto-calibra instantaneamente absorbiendo las anomalias del mercado (shocks de volatilidad, manipulacion institucional, picos de liquidez). Al hacer C(t) dinamica, el patron armonico se vuelve elastico; no espera a que el mercado encaje en una figura rigida, sino que el modelo se deforma y ajusta su Punto Cero en tiempo real para predecir la explosion (cruce) con exactitud milimetrica, sin importar la entropia del entorno.


### [2026-09-15] Optimizacion de Riesgo: Micro-Cortes Dinamicos via Fourier y Transformada Z
- **Filtrado Espectral de Ruido:** Se incorpora conceptualmente el uso de Transformadas de Fourier y Transformadas Z sobre los senos y cosenos dinamicos. Esto elimina el 'ruido blanco' del mercado (falsos rompimientos) y aísla la frecuencia institucional pura.
- **Reaccion de Stop Loss Anticipado (Micro-Cuts):** Al ser un ecosistema 100% dinamico, el sistema ya no es esclavo de un 'Stop Loss fijo' en la grafica. Si las transformadas matematicas detectan una anomalia instantanea (ruptura del patron armonico en tiempo real), el sistema no espera a que el precio golpee el SL rigido original. 
- **Auto-Recalibracion y Reversion (Stop & Reverse):** El algoritmo reacciona de forma anticipada cerrando la posicion inmediatamente asumiendo una perdida microscopica. Acto seguido, recalibra el patron armonico con la nueva data anomalica e ingresa instantaneamente en la direccion correcta con un nuevo TP, transformando una trampa de liquidez en una operacion sniper ganadora.

### [2026-09-16] Arquitectura Multi-Provider y Optimización de Cuotas (Anti-429)
- **Modificación de Arquitectura (Load Balancing):** Debido a la descontinuación de modelos clásicos en Groq (llama3-8b, mixtral) y las severas restricciones en modelos pesados de Gemini (límite de 20 peticiones diarias en Gemini 2.5 Flash), se migró el núcleo analítico de los agentes (TIDAL, NORO, ZEPHR, RUNE) exclusivamente a **Google Gemini Flash Lite Latest**. Esto garantiza una respuesta hiper-rápida y tolerancia masiva en la capa gratuita (evitando Errores 404).
- **Optimizaciones (Latencia y Hard-Throttle):** Para evadir bloqueos por ráfagas de consultas (ResourceExhausted 429) generados por los reintentos de Langchain, se inyectó un 	ime.sleep(15) en el step_callback de los Agentes. Este freno físico asegura un máximo de 4 RPM globales, sacrificando latencia de procesamiento por 100% de estabilidad de cuota. Además, se configuró max_rpm=3 de forma nativa por Agente (compatibilidad crewai<0.50).
- **Minimización Matemática (Payloads):** Se eliminó el array masivo eed (DOM) dentro de la 
ailway_cache_tool. Esta compresión redujo el peso del JSON de 54,000 a ~5,000 caracteres, evitando el desbordamiento prematuro del límite TPM (Tokens por Minuto).


## 🧠 NODO: ARQUITECTURA TENSORFLOW Y UPSTASH (NUEVO ECOSISTEMA)
- **Cerebro Neuronal:** Mia implementa TensorFlow (Keras Sequential) para predicción probabilística de éxito de trades.
- **Topología de Caché (Upstash Redis):**
  1. cache_mt5: Pulso en vivo del broker.
  2. cache_hist_mt5: Historial para Dashboard (evade 429 de Firebase).
  3. cache_mia_tensorflow: Modelo neuronal compilado en Base64 y métricas de Accuracy.
  4. mia_swarm_history_...: Memoria colectiva de los Enjambres (Obsidian).
- **Regla CI/CD:** El entrenamiento neuronal se dispara vía endpoint en Railway (/api/cron/train_tensorflow). JAMÁS ejecutar entrenamiento masivo local.
