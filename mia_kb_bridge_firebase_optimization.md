---
tags:
  - arquitectura
  - firebase
  - optimizacion
  - machine-learning
  - hft
fecha: 2026-08-11
---

# 🧠 MIA KB: Optimización HFT y Blindaje de Cuotas (Firebase Juez)

Este documento actúa como puente (MD Bridge) para sincronizar las últimas actualizaciones de la arquitectura base de Mía hacia la base de conocimiento, con enfoque en la protección de las cuotas de Firebase (Read/Writes).

## 1. Contexto: El Problema (Error 429 - Quota Exceeded)
Con la implementación del ciclo HFT de MetaTrader 5 (escaneos cada 30 y 60 segundos), el tráfico hacia Firebase se volvió exponencial.
- **MT5 Scanner (60s):** Escribía el estado de los indicadores de forma forzada a la base de datos 1,440 veces al día por activo.
- **Cache Local (30m):** Descargaba 800 logs históricos cada media hora (38,400 lecturas/día).
- Esto saturaba la cuota gratuita (50k lecturas, 20k escrituras), tirando el servidor (Error 429) e interrumpiendo el flujo de Mía.

## 2. Implementación: La Solución (El Escudo RAM)
Se inyectaron 3 murallas de contención en el servidor backend (FastAPI - `app.py`) para aislar a Firebase y dejarlo puramente como un **Juez Supremo** que solo habla cuando es estrictamente necesario:

### A. Caché Global en RAM (Lecturas = 0)
- **`GLOBAL_MATRICES_CACHE_FULL`**: Todas las consultas de MetaApi/MT5 (que se hacen cada 30 segundos preguntando por permisos de lotaje o entrada) chocan ahora contra la memoria RAM de Python. No consumen lecturas de Firebase.
- **Bypass del Dashboard**: El portal web de KPIs `/api/dashboard_data` tiene un *Bypass Total*. Se alimenta exclusivamente de la RAM, independientemente de cuántos usuarios estén viendo la gráfica.

### B. Espejo Dinámico (Filtro de Escrituras)
- El webhook técnico recibe los datos del scanner de MT5 cada 60 segundos.
- Antes de ordenar un `doc_ref.set()`, el backend compara si las confirmaciones técnicas (Order Blocks, FVGs, Tendencia) **cambiaron** respecto al minuto anterior.
- Si el mercado no ha hecho movimientos clave (todo sigue idéntico), se aborta la escritura y Firebase permanece intacto. Ahorro masivo del 98% en cuota de escrituras.

### C. Parche de Límite de Recarga
- El ciclo de recarga de 30 minutos se redujo de `limit(800)` a `limit(150)` sobre la tabla `mia_audit_logs`. Esto bajó el consumo fijo de 38,400 lecturas a solo **7,200 lecturas diarias**.

## 3. Desconexión de Agentes Secundarios
Para aislar el laboratorio de Mía por las próximas 3 semanas:
- **n8n y Postgres:** Pasados a modo `Offline` en Railway.
- **El Cerebro:** El Machine Learning ahora es impulsado internamente vía `APScheduler` (Función `entrenar_pesos_dinamicos`) todos los viernes a las 16:00, leyendo un histórico de 500 operaciones para ajustar los pesos sin sobrecarga externa.

## 4. Resultado Final
Mía puede procesar y cazar la liquidez de los ciclos *AMD (Accumulation, Manipulation, Distribution)* 24/5 sin ningún temor a que la base de datos se caiga por tráfico excesivo. La recolección de datos y el ranking de estrategias tienen total libertad de operación.
