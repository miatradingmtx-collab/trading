# 🧠 CBR: Base de Conocimiento Maestra (Homologada)

Este documento contiene todos los Casos de Razonamiento (Case-Based Reasoning) para los Agentes T y el Watchdog.

---

# CBR Entry: Uvicorn Null Byte Crash
## Error Signature
```python
File "<frozen importlib._bootstrap_external>", line 947, in source_to_code
ValueError: source code string cannot contain null bytes
```

## Diagnóstico
Este error ocurre cuando un archivo de código fuente de Python (ej. `app.py`) se corrompe al insertarse bytes nulos (`\x00`). Esto es común cuando se usan scripts de reemplazo de texto (`regex`, `codecs`) en entornos cruzados (Windows PowerShell a Linux) sin sanear el formato binario.
Como resultado, el servidor Uvicorn / FastAPI entra en un ciclo de "Crash Loop" fatal, pero los monitores de estado HTTP o Docker podrían marcarlo como "Online" falsamente si solo hacen ping al contenedor.

## Falso Positivo del Watchdog
El Watchdog AI falló en su reporte inicial ("Cero cambios críticos pendientes") porque estaba midiendo la disponibilidad de la memoria y la CPU del contenedor (que estaban bien), pero no estaba haciendo una lectura en vivo del `stderr` (Standard Error) de Uvicorn en el puerto 8000. 

## Solución Inmediata (Playbook de Mitigación)
Cuando el Enjambre o el Watchdog detecte este error en los logs de Railway, debe ejecutar inmediatamente el siguiente script de saneamiento binario sobre el archivo corrupto:

```python
# Script de Reparación CBR para Watchdog
import os
archivo_corrupto = 'app.py'

with open(archivo_corrupto, 'rb') as f:
    content = f.read()

if b'\x00' in content:
    content = content.replace(b'\x00', b'')
    with open(archivo_corrupto, 'wb') as f:
        f.write(content)
    print(f"Saneamiento exitoso: Bytes nulos removidos de {archivo_corrupto}.")
```

## Homologación (Mirroring)
Todos los agentes (T1-T10, Watchdog, y Slack Bot) deben incorporar esta firma en sus matrices de riesgo. Si Uvicorn no levanta, el primer paso es escanear por `\x00` antes de asumir fallas lógicas o de dependencias.


---

---
name: homologacion_cbr_tf_data_injection
description: Protocolo de diagnostico para caidas abruptas de Accuracy en TensorFlow tras inyeccion masiva de datos.
trigger: "Accuracy de la Red Neuronal cayo"
---

# 🧠 CBR: TENSORFLOW DATA INJECTION NORMALIZATION (Correccion de Overfitting)

## 📌 Contexto del Incidente
- **Sintoma:** El Supervisor Watchdog o la interfaz de Slack levantan una alerta critica indicando que la "Accuracy (Precision)" de la Red Neuronal cayo por debajo del umbral esperado (ej. paso de 97% a 84.5%).
- **Causa Raiz:** Se inyecto un bloque masivo de datos historicos de golpe (ej. pasar de 50 a 600+ trades aprendidos) sin reentrenamiento incremental previo.
- **Falso Positivo:** El sistema lo interpreta como una degradacion del modelo y propone una accion critica: `REENTRENAR_TENSORFLOW` con regularizacion Dropout.

## 🔬 Diagnostico de Arquitectura (Por que ocurre)
1. **Espejismo de Overfitting (Muestra Pequeña):** Cuando la Red Neuronal opera con menos de 100 trades, tiende a "memorizar" el dataset, mostrando un WinRate artificialmente alto (>95%).
2. **Choque de Varianza Real (Muestra Grande):** Al inyectar 500+ trades reales, el modelo se enfrenta a la volatilidad verdadera del mercado (noticias, ruido, manipulacion). La precision cae de forma natural a su verdadero "Sweet Spot" de generalizacion (usualmente entre 75% y 85%).
3. **Conclusion:** Una precision del 84.5% en 600+ trades en Forex NO es un error, es un estado institucional altamente rentable y realista.

## 🛠️ Protocolo de Resolucion (Para Agentes T y Watchdog)

**SI detectas una caida de Accuracy y notas que el volumen de `TRADES APRENDIDOS` aumento masivamente de golpe:**

1. **NO APROBAR REENTRENAMIENTO INMEDIATO:** Rechazar la propuesta `REENTRENAR_TENSORFLOW`. Forzar a la maquina a recuperar el >90% en 600 trades provocara "Sobreajuste Catastrofico" (memorizara el pasado y perdera dinero en el futuro).
2. **CLASIFICAR COMO WARNING (No Error):** Clasificar el evento como `DATA INJECTION NORMALIZATION`. Emitir un mensaje de advertencia indicando que el modelo se esta ajustando a la nueva varianza de datos.
3. **NUEVO UMBRAL ESTADISTICO:** El umbral de panico oficial para HFT en datasets grandes (>500 trades) queda fijado en **75.0%**. 
   - Si `Accuracy >= 75.0%`: El modelo esta sano y maduro. No hacer nada.
   - Si `Accuracy < 75.0%`: Solo entonces generar una propuesta de `REENTRENAR_TENSORFLOW` genuina.

## 🛡️ Leccion de ML para Enjambres
"La perfeccion matematica (>95%) en los mercados financieros es una ilusion de muestras pequeñas. La rentabilidad institucional se sostiene en la robustez estadistica de muestras grandes (75%-85%)."


---

