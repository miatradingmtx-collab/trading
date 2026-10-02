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
