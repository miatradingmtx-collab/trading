## Regla de Arquitectura (Ejecución MT5)
El servidor central en la nube de Mia (app.py en Railway) **NO** es el que ejecuta los trades en MetaTrader 5 de forma directa. Su única función es recibir las señales, calcular el Score, y escribir el resultado en Firebase. La ejecución real ocurre en un sistema externo/local que monitorea Firebase y dispara las órdenes en MT5 **ÚNICAMENTE** cuando detecta un nuevo trade con score >= 80.

## Regla de Documentación en Obsidian (Mandato Absoluto)
A partir de este momento, **todo cambio, actualización, modificación de código, o ajuste de arquitectura** que se realice en CUALQUIERA de los 4 proyectos (Trading, Renta Lanchas, Venta Lanchas, Remolques) y su Infraestructura Tecnológica (Python Backend, Firebase, Upstash Redis, Botpress) DEBE ser registrado y documentado **obligatoriamente y automáticamente** en la bóveda de Obsidian (`D:\obsidiana\Proyectos`). 

**Nunca** des por finalizada una tarea ni le reportes al usuario que has terminado sin antes haber:
1. Actualizado el `Historial_Cambios_*.md` del proyecto correspondiente.
2. Actualizado el `Estructura_Codigo_*.md` si hubo cambios arquitectónicos.
Esto es vital para garantizar el crecimiento ininterrumpido de la Red Neuronal y la Base de Conocimiento (KB) de Mia.

## Regla de Hitos y Tareas Pendientes (Bitácora Evolutiva)
Todo agente que trabaje en el proyecto de Trading DEBE mantener la bitácora (Historial_Cambios_Trading.md) actualizada con: 
1. **Checklist de completados [x]**: Hitos con la fecha exacta de lo que se va haciendo.
2. **Checklist de pendientes [ ]**: Cualquier tarea incompleta, idea, o ajuste pendiente que deba retomarse en futuras sesiones. 
Esto garantiza que la KB de Mia crezca como un Cerebro estructurado que sabe exactamente en qué estado dejó la operación y qué falta por hacer.

## Regla de Despliegue en Railway (Pipeline de Actualización)
Todo agente que modifique código fuente de los endpoints, servidores o lógica base de Mia (ej. app.py) DEBE recordar que dichos cambios inicialmente solo ocurren en local. Para que el cambio surta efecto en producción (Railway), es OBLIGATORIO:
1. Ejecutar 'git add .'
2. Ejecutar 'git commit -m "Descripción del cambio"'
3. Ejecutar 'git push'
Railway está conectado a GitHub y solo detectará y compilará la actualización cuando reciba el push en el repositorio.

## Regla de Arquitectura de Microservicios en Railway (Tríada Desacoplada: 0b51, 1fd4, 927a)
La infraestructura en Railway opera desacoplada en 3 microservicios independientes para blindar la ejecución y no competir por recursos:
1. **Instancia `0b51` (`trading-production-0b51.up.railway.app`):** Control Plane & ChatOps Gateway.
   - Gobierna los 2 canales de Slack: `#back-office-y-backend` (`C0C4ZMFCMJ8` para Herds T1-T10) y `#mia-trading-insights` (`C0C6DUTQVEZ` para Post-Mortem y Supervisor Quant).
   - Endpoints de Slack: `/api/slack/interactions`, `/api/slack/events`, `/api/slack/command`.
   - Servidor MCP Back-Office: `/mcp/ops` y `/api/mcp/ops` (`mia_ops_mcp_server.py`) con Llama 3.3 70B (`OPENROUTER_API_KEY_OPS`).
   - Supervisor Quant: Autopsias y CBR con Gemini 1.5 Pro (`GOOGLE_API_KEY`).
2. **Instancia `1fd4` (`trading-production-1fd4.up.railway.app`):** Neural Cluster & 3D Terminal.
   - URLs canónicas: `/` (Terminal Antopus 3D / WebSocket `/ws`), `/brain` (Visualizador Neuronal 3D y CBR), `/mods` (Catálogo de Módulos & Extensiones).
   - Inferencia de red neuronal profunda TensorFlow Keras (22 tensores sinápticos) y consenso de los 7 Herds.
3. **Instancia `927a` (`trading-production-927a.up.railway.app`):** MT5 Data Plane & HFT Execution Core.
   - Ejecución directa hacia MT5 Broker, ingesta de ticks, streaming de precios, `/dashboard`, `/dashboard/preview`, MCP Trading `/mcp`.
   - Trailing stop asimétrico institucional de RUNE sub-50ms.
   - **CERO tráfico de Slack** para garantizar latencia ultra-baja y cero bloqueos.

## Regla de Modo Aprendiz (Arquitectura de Validación)
Mia (Botpress) se encuentra actualmente en **Modo Aprendiz** (recaudando datos durante 1 a 3 meses para la "Regla de 3"). 
Por tanto, Mia NO toma decisiones finales de trading ni ejecuta órdenes de forma autónoma basándose solo en su IA.
- **Firebase es el Juez:** Las ejecuciones en MetaAPI hacia MT5 están bloqueadas/gobernadas por condiciones estadísticas, reglas matemáticas en el código (Lotaje 1%, Drawdown 3%) y el umbral de `score >= 80` validado en la nube.
- **Objetivo de la Base de Conocimiento (KB):** La meta de recopilar y auditar cada trade en Obsidiania/Firebase es enseñarle a Mia cuáles son los "mejores trades" bajo la "Regla de 3" (mínimo 3 confirmaciones institucionales) para que en el futuro logre plena autonomía.

## Regla de Motor Nativo de Machine Learning & Aprendizaje por Refuerzo (RL)
El ecosistema de Mia opera de forma 100% nativa en Python mediante **NumPy, Pandas y TensorFlow Keras** en los microservicios de **Railway**. Queda terminantemente erradicado el uso de flujos externos en N8N para trading o inferencia; el scheduler interno asíncrono en Python (`app.py`) y la red neuronal profunda de 22 tensores sinápticos (`mia_tensorflow` en Instancia `1fd4`) gestionan el cálculo de pesos dinámicos, la vectorización y la sincronización en caliente hacia Upstash Redis (`cache_mia_tensorflow` y `cache_herd_rl_weights`) de manera autónoma.

## Regla de Protección Quota 429 y Caché en RAM (Firebase Bypass)
Si la conexión a Firebase Cloud Firestore agota su límite gratuito de 50,000 lecturas/escrituras diarias, la aplicación (app.py) continuará funcionando mediante el uso de excepciones (try...except) que capturarán el error y permitirán el flujo en RAM. Cualquier agente que programe operaciones de webhooks deberá evitar llamadas bloqueantes o crashings del servidor ante fallos de conexión (bypass silencioso para no sobrecargar los logs en Railway).

## Regla Anti-Spam de Telegram y TPs Explícitos
Telegram solo debe alertar (ya sea de apertura o cierre) sobre trades **ejecutados**, esto es cuando traen un Ticket válido. Nunca enviar señales crudas que no hayan pasado por el filtro de Mia. Adicionalmente, toda Apertura debe especificar la estructura escalonada de Take Profit:
- TP1: Cobro del 50% del volumen al 50% de distancia (+1.0R asegurado en caja).
- Break-Even Institucional: Desplazamiento automático de SL a BE con buffer defensivo de +2.5 pips.
- Trailing Locks Asimétricos: Lock 1 al 75% dist (+40% beneficio asegurado) y Lock 2 al 85% dist (+65% asegurado).
- Front-Run TP: Cierre del 100% remanente al 95% de distancia.

## Regla de Logs (Bypass Notion & Excel)
Dado que Notion y Excel actualmente no están configurados o habilitados, el sistema de Mia genera un log de error 401 para Notion y una advertencia de archivo no encontrado para Excel en Railway. **Estos no son errores críticos que deban ser corregidos**. Forman parte de un bypass intencional, y los agentes no deben enviar alertas de error ni intentar modificar el código para 'arreglarlos', simplemente ignorarlos en los logs de auditoría.

## Regla de Portafolio Canónico (5 Live MT5 + 1 Sandbox NZDCAD) y Control Anti-429
El portafolio de trading de Mia está estrictamente restringido a:
1. **5 Pares Oficiales en Vivo MT5:** `EURUSD`, `GBPUSD`, `AUDUSD`, `GBPJPY`, `XAUUSD`.
2. **1 Par Oficial en Sandbox:** `NZDCAD` (modo shadow/entrenamiento, PROHIBIDA ejecución en broker real).
Está terminantemente prohibido que `trading_matrix`, memorias RAM (`FIREBASE VIP`), escáneres o llamadas a LLMs procesen activos residuales o foráneos (como `BTC`, `UNKNOWN`, `XAUUSD_TEST`, índices o cruces exóticos). Las consultas a LLMs deben limitarse a los activos con liquidez activa en su sesión correspondiente para blindar las cuotas de Groq, Gemini y OpenRouter.

## Regla de Gestión de Riesgo Institucional v2 (Cascada RUNE & Doble Anillo de Autocuración Post-Sleep)
1. **Cascada de 4 Fases (RUNE):** TP1 cobro de 50% al 50% de distancia (+1.0R mínimo), Break-Even automático post-TP1 con buffer institucional de +2.5 pips, Trailing Lock 1 al 75% (+40% de ganancia asegurada), Trailing Lock 2 al 85% (+65% asegurado), y Front-Run TP al 95% (cierre de 100% remanente).
2. **Doble Anillo de Redundancia y Autocuración Post-Sleep (RUNE & Orchestrator):** Al despertar de cada ciclo de reposo de 30s en mia_master_swarm_rest.py, RUNE audita las posiciones activas en MT5. Si detecta desvíos por latencia, timeouts o caídas en la instancia ejecutora (927a) —como parciales omitidos, SL en pérdida tras superar el 50%, o retrocesos que penetran los Trailing Locks—, despacha de inmediato una orden de autocuración a cache_mt5_pending_execution, notifica en #back-office-y-backend (C0C4ZMFCMJ8) y #mia-trading-insights (C0C6DUTQVEZ), y asienta el evento en el CBR.
3. **Límite Canasta USD:** Máximo 2 operaciones simultáneas en pares que contengan USD (EURUSD, GBPUSD, AUDUSD, XAUUSD).
4. **Filtro Anti-Caza ATH en Oro:** Prohibido comprar XAUUSD si se encuentra a menos de 0.5% del All-Time High sin retroceso de 30 a 50 pips.

## Regla de Verdad Financiera Base $5,000 USD y Asimetría Matemática (Ley D / (1 - D))
1. **Capital Base Inicial:** La cuenta partió de $5,000.00 USD. Queda estrictamente prohibido reportar o calificar la cuenta como "saludable" u "óptima" mientras el balance sea < $5,000.00 USD.
2. **Asimetría de Recuperación:** Las pérdidas se recuperan de forma asimétrica ($R = \frac{d}{1-d} \times 100$). Toda propuesta y gestión debe orientarse a sanar el drawdown estructural hacia la base de $5,000 USD y el High-Water Mark.

## Regla de Oro de Actualización, Homologación y Depuración Perpetua de Documentación Core (Anti-Discrepancias y Anti-Alucinación)
1. **Mandato Obligatorio Ante Cada Modificación:**
   Cada vez que se realice cualquier modificación de código, arquitectura, parámetros, fórmulas matemáticas, slots en Upstash Redis, colecciones en Firebase Firestore, o actualización de datos contables MT5, TODO agente LLM, desarrollador o script TIENE LA OBLIGACIÓN ESTRICTA de barrer y homologar todos los documentos centrales:
   - `DOCS_OPS_CORE.md` y `DOCS_TRADING_CORE.md` (Blueprints Maestros)
   - `GEMINI.md`, `GEMINI_OPS.md`, `GEMINI_TRADING.md` y `.agents/AGENTS.md` (Reglas del Sistema)
   - Las 9 micro-especificaciones en `specs/herds/`
   - Bóveda de Obsidian (`D:\obsidiana\Proyectos\Mia_Trading\`)
2. **Depuración Radical Obligatoria (Prohibición de Coexistencia de Datos Obsoletos):**
   Queda **TERMINANTEMENTE PROHIBIDO** dejar datos viejos, métricas históricas desactualizadas, indicadores descartados o saldos superados conviviendo con la información nueva. No basta con poner un aviso o nota de advertencia arriba: **toda cifra obsoleta o sección contradictoria DEBE ser eliminada o sobrescrita de raíz** para garantizar una única fuente de la verdad inquebrantable.
3. **Blindaje Cognitivo Anti-Alucinación ("Lost in the Middle"):**
   Si los agentes LLMs (Gemini Pro, Llama 3.3 70B, DeepSeek) o los 7 Herds del Swarm leen documentos donde coexisten datos en conflicto (ejemplo: un Top 3 antiguo de septiembre con 94% WR junto al Top 3 validado con $\ge 50$ trades, o balances desfasados de $4,325 junto a $3,688), el agente sufre degradación de atención ("Lost in the Middle"), alucina, pierde precisión en el razonamiento probabilístico o revierte a parámetros erróneos ya superados. Mantener la documentación limpia, homologada y unívoca es una **condición crítica de seguridad operativa**.
4. **Protocolo de Cierre Obligatorio (Definition of Done):**
   Ningún agente puede reportar una tarea como completada ni hacer commit/push hacia Railway sin antes haber verificado la ausencia total de discrepancias entre los archivos de documentación y las especificaciones activas, habiendo asentado el hito con fecha exacta en `Historial_Cambios_Trading.md`.


## Regla de Diagramas Institucionales High-Fidelity y Almacenamiento en Diagramas/
1. **Mandato Visual Inquebrantable:** Todo diagrama o flujo de arquitectura, enjambres o conectividad generado en cualquiera de los 7 chats/prompts DEBE diseñarse bajo el estándar de High-Fidelity Cyber-Dashboard (HTML5 semántico, dynamic SVG Bézier anti-colisiones, CSS Grid/Flexbox puro, Vanilla JS, fondo Dark Obsidian `#080a0f`, ticker superior en vivo y cero CDNs pesadas), tal como se evidencia en `flujo_conectividad_figma_mcp.html`.
2. **Ruta Canónica de Almacenamiento:** Todo diagrama o visualizador HTML/SVG generado en el sistema debe guardarse obligatoriamente dentro del directorio canónico:
   `C:\Users\ecybe\OneDrive\Documentos\Trading\Diagramas\`


## 🎨 MANDATO OBLIGATORIO DE ENLACES DE DIAGRAMAS T6 & T7 Y COMPARATIVA ANTES VS DESPUÉS
1. **Visualización Dual de Diagramas:** Todo diagrama o flujo arquitectónico generado o auditado por HERD T6 o T7 DEBE proporcionar de forma obligatoria tanto la ruta local del archivo:
   `file:///C:/Users/ecybe/OneDrive/Documentos/Trading/Diagramas/<nombre_diagrama>.html`
   como su enlace web en vivo para previsualización directa en Slack:
   `https://trading-production-927a.up.railway.app/diagramas/<nombre_diagrama>.html`
   (ejemplo: `file:///C:/Users/ecybe/OneDrive/Documentos/Trading/Diagramas/flujo_conectividad_figma_mcp.html` y `https://trading-production-927a.up.railway.app/flujo/figma-mcp`).
2. **Checkboxes HITL para Selección Quirúrgica:** Toda propuesta de los Herds T1 al T10 debe publicarse en `#back-office-y-backend` con casillas de verificación interactivas (`checkboxes`) para permitir autorización individual o masiva mediante los 4 botones canónicos (`[Aprobar Seleccionadas ☑️]`, `[Aprobar Todas ✅]`, `[Rechazar ⛔]`, `[Forzar Resync 🔄]`).
3. **Comparativa 'Antes vs Después' (Visual Diff):** Toda propuesta de interfaz en dashboards (`/brain`, `/`, `/mods`, `/dashboard`) debe incluir la comparativa 'Antes vs Después' y el enlace interactivo:
   `👉 https://trading-production-927a.up.railway.app/dashboard/preview`
   junto con la barra de enlaces persistente a los 5 dashboards en el pie de mensaje.
