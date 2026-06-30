## Regla de Arquitectura (Ejecucion MT5)
El servidor central en la nube de Mia (app.py en Railway) **NO** es el que ejecuta los trades en MetaTrader 5 de forma directa. Su Ãºnica funciÃ³n es recibir las seÃ±ales, calcular el Score, y escribir el resultado en Firebase. La ejecuciÃ³n real ocurre en un sistema externo/local que monitorea Firebase y dispara las Ã³rdenes en MT5 **ÃšNICAMENTE** cuando detecta un nuevo trade con score >= 80.

## Regla de DocumentaciÃ³n en Obsidian (Mandato Absoluto)
A partir de este momento, **todo cambio, actualizaciÃ³n, modificaciÃ³n de cÃ³digo, o ajuste de arquitectura** que se realice en CUALQUIERA de los 4 proyectos (Trading, Renta Lanchas, Venta Lanchas, Remolques) y su Infraestructura TecnolÃ³gica (N8N, Firebase, Botpress) DEBE ser registrado y documentado **obligatoriamente y automÃ¡ticamente** en la bÃ³veda de Obsidian (`D:\obsidiana\Proyectos`). 

**Nunca** des por finalizada una tarea ni le reportes al usuario que has terminado sin antes haber:
1. Actualizado el `Historial_Cambios_*.md` del proyecto correspondiente.
2. Actualizado el `Estructura_Codigo_*.md` si hubo cambios arquitectÃ³nicos.
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
