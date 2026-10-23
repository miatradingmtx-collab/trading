## Regla de Arquitectura (Ejecución MT5)
El servidor central en la nube de Mia (app.py en Railway) **NO** es el que ejecuta los trades en MetaTrader 5 de forma directa. Su única función es recibir las señales, calcular el Score, y escribir el resultado en Firebase. La ejecución real ocurre en un sistema externo/local que monitorea Firebase y dispara las órdenes en MT5 **ÚNICAMENTE** cuando detecta un nuevo trade con score >= 80.

## Regla de Documentación en Obsidian (Mandato Absoluto)
A partir de este momento, **todo cambio, actualización, modificación de código, o ajuste de arquitectura** que se realice en CUALQUIERA de los 4 proyectos (Trading, Renta Lanchas, Venta Lanchas, Remolques) y su Infraestructura Tecnológica (N8N, Firebase, Botpress) DEBE ser registrado y documentado **obligatoriamente y automáticamente** en la bóveda de Obsidian (`D:\obsidiana\Proyectos`). 

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

## Regla de Modo Aprendiz (Arquitectura de Validación)
Mia (Botpress) se encuentra actualmente en **Modo Aprendiz** (recaudando datos durante 1 a 3 meses para la "Regla de 3"). 
Por tanto, Mia NO toma decisiones finales de trading ni ejecuta órdenes de forma autónoma basándose solo en su IA.
- **Firebase es el Juez:** Las ejecuciones en MetaAPI hacia MT5 están bloqueadas/gobernadas por condiciones estadísticas, reglas matemáticas en el código (Lotaje 1%, Drawdown 3%) y el umbral de `score >= 80` validado en la nube.
- **Objetivo de la Base de Conocimiento (KB):** La meta de recopilar y auditar cada trade en Obsidiania/Firebase es enseñarle a Mia cuáles son los "mejores trades" bajo la "Regla de 3" (mínimo 3 confirmaciones institucionales) para que en el futuro logre plena autonomía.

## Regla de Integración N8N y Machine Learning (CI/CD Automático)
Todo el ecosistema de Mia (API de Python, base de datos Postgres y flujos de automatización en N8N) se encuentra alojado y orquestado en **Railway**. Esto garantiza una operación CI/CD 100% en la nube que NO depende de que el equipo local del usuario esté encendido. El nodo de N8N 'Mia_Machine_Learning_Loop' se ejecuta en los servidores de Railway todos los viernes a las 16:00, contactando al endpoint `/api/entrenar_pesos` mediante el `BRIDGE_ACCESS_TOKEN`. Agentes futuros no deben intentar ejecutar estas rutinas localmente.

## Regla de Protección Quota 429 y Caché en RAM (Firebase Bypass)
Si la conexión a Firebase Cloud Firestore agota su límite gratuito de 50,000 lecturas/escrituras diarias, la aplicación (app.py) continuará funcionando mediante el uso de excepciones (try...except) que capturarán el error y permitirán el flujo en RAM. Cualquier agente que programe operaciones de webhooks deberá evitar llamadas bloqueantes o crashings del servidor ante fallos de conexión (bypass silencioso para no sobrecargar los logs en Railway).

## Regla Anti-Spam de Telegram y TPs Explícitos
Telegram solo debe alertar (ya sea de apertura o cierre) sobre trades **ejecutados**, esto es cuando traen un Ticket válido. Nunca enviar señales crudas que no hayan pasado por el filtro de Mia. Adicionalmente, toda Apertura debe especificar la estructura escalonada de Take Profit:
- TP1 (25%)
- TP2 (50%)
- Full TP

## Regla de Logs (Bypass Notion & Excel)
Dado que Notion y Excel actualmente no están configurados o habilitados, el sistema de Mia genera un log de error 401 para Notion y una advertencia de archivo no encontrado para Excel en Railway. **Estos no son errores críticos que deban ser corregidos**. Forman parte de un bypass intencional, y los agentes no deben enviar alertas de error ni intentar modificar el código para 'arreglarlos', simplemente ignorarlos en los logs de auditoría.

## Regla de Portafolio Canónico (5 Live MT5 + 1 Sandbox NZDCAD) y Control Anti-429
El portafolio de trading de Mia está estrictamente restringido a:
1. **5 Pares Oficiales en Vivo MT5:** `EURUSD`, `GBPUSD`, `AUDUSD`, `GBPJPY`, `XAUUSD`.
2. **1 Par Oficial en Sandbox:** `NZDCAD` (modo shadow/entrenamiento, PROHIBIDA ejecución en broker real).
Está terminantemente prohibido que `trading_matrix`, memorias RAM (`FIREBASE VIP`), escáneres o llamadas a LLMs procesen activos residuales o foráneos (como `BTC`, `UNKNOWN`, `XAUUSD_TEST`, índices o cruces exóticos). Las consultas a LLMs deben limitarse a los activos con liquidez activa en su sesión correspondiente para blindar las cuotas de Groq, Gemini y OpenRouter.

## Regla de Gestión de Riesgo Institucional v2 (Cascada RUNE & Canasta USD)
1. **Cascada de 4 Fases (RUNE):** TP1 cobro de 50% al 50% de distancia (+1.0R mínimo), Break-Even automático post-TP1 con buffer institucional de +2.5 pips, Trailing Lock 1 al 75% (+40% de ganancia asegurada), Trailing Lock 2 al 85% (+65% asegurado), y Front-Run TP al 95% (cierre de 100% remanente).
2. **Límite Canasta USD:** Máximo 2 operaciones simultáneas en pares que contengan USD (`EURUSD`, `GBPUSD`, `AUDUSD`, `XAUUSD`).
3. **Filtro Anti-Caza ATH en Oro:** Prohibido comprar XAUUSD si se encuentra a menos de 0.5% del All-Time High sin retroceso de 30 a 50 pips.

## Regla de Verdad Financiera Base $5,000 USD y Asimetría Matemática (Ley D / (1 - D))
1. **Capital Base Inicial:** La cuenta partió de $5,000.00 USD. Queda estrictamente prohibido reportar o calificar la cuenta como "saludable" u "óptima" mientras el balance sea < $5,000.00 USD.
2. **Asimetría de Recuperación:** Las pérdidas se recuperan de forma asimétrica ($R = \frac{d}{1-d} \times 100$). Toda propuesta y gestión debe orientarse a sanar el drawdown estructural hacia la base de $5,000 USD y el High-Water Mark.
