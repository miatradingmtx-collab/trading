---
tags:
  - arquitectura
  - webhook
  - mt5
  - limites
fecha: 2026-08-25
---

# 🧠 MIA KB: Webhooks (MT5/Firebase) y Límites de Riesgo (2 Trades)

Este documento sincroniza los cambios arquitectónicos implementados en `app.py` para corregir la mensajería del sistema y proteger el capital controlando el riesgo de múltiples trades en cascada.

## 1. El Mito de TradingView (Corrección de Webhook)
Históricamente, los logs del sistema y los mensajes de Telegram indicaban erróneamente: `ALERTA RECIBIDA DE TRADINGVIEW`.
Esto causaba confusión arquitectónica porque **TradingView no se conecta directamente al webhook de ejecución de MIA**. 
- El único y verdadero juez es **Firebase**.
- Quien dispara los Webhooks de `EJECUTADO`, `CIERRE_PARCIAL`, y `CIERRE_TOTAL` es **MT5 / MetaApi** a través de Botpress.
**Solución:** Se corrigió permanentemente el registro en el servidor y en la recuperación de la caché (memoria RAM), pasando a ser `ALERTA RECIBIDA EN WEBHOOK (MT5/FIREBASE)`. Al usar Firebase como juez supremo (homologado para todos los activos), también se solucionó el bug donde los cierres marcaban "Estrategia: MANUAL", logrando recuperar la estrategia institucional original cruzando los tickets o el nombre del activo en la RAM Cache.

## 2. Bloqueo Estricto de Trades Concurrentes (Risk Management)
Cuando el semáforo técnico alcanzaba el 80%, se autorizaba la apertura de un trade. Si el mercado retrocedía temporalmente bajando el score (volviendo a `INACTIVO`) y luego recibía una nueva alerta que lo subía a 80%, MIA abría un trade adicional, superando el límite analítico diseñado para poner a prueba los Order Blocks (SMC vs Lux Algo).

**Implementación del Candado:**
Se inyectó una doble validación en `app.py` (webhook MT5 y evaluación de semáforo):
`if len(operaciones_activas) >= 2:`
A partir de ahora, ningún activo (como el AUD) podrá superar los 2 trades activos (ej. 1 SMC y 1 Lux), protegiendo la gestión de riesgo.

## 3. Lógica de Trailing Stop y Break Even
El backend en Python ahora extrae el `precio_apertura` del histórico (si ocurre un `CIERRE_PARCIAL` o `CIERRE_TOTAL`) para calcular de forma milimétrica las distancias a los Take Profits (TP1 25%, TP2 50%, Full TP). 
Si se cierran parciales con ganancia o el trade toca el trailing stop, los mensajes de Telegram dibujan dinámicamente un checkmark (`✅`) indicando que el mercado alcanzó dicha rentabilidad antes de regresar, honrando la protección del capital (Break Even).
*Nota Crítica:* El deslizamiento del Stop Loss (Break Even a 25% o 50%) **lo ejecuta exclusivamente el Robot (EA) dentro de MetaTrader 5 / Botpress**. Se debe asegurar que las variables de entrada (inputs) del Trailing Step estén correctamente homologadas y activas en todos los activos operados en la terminal MT5, ya que Python actúa como receptor del PNL final, no como el ejecutor tic-a-tic.
