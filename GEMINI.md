---
name: enrutador_principal
description: Enrutador de reglas divididas para optimizar el token de contexto.
trigger: always_on
---

#  ENRUTADOR PRINCIPAL GEMINI
Para evitar sobrecarga de contexto y tropiezos entre agentes:
1. **Si eres un Agente de Trading, TensorFlow, ATLAS o los 7 Herds del Swarm de Trading:** 
    DEBES LEER ESTRICTAMENTE: GEMINI_TRADING.md y DOCS_TRADING_CORE.md
    *(Los 7 Herds de Trading son: 1. TIDAL, 2. NORO, 3. ZEPHR, 4. LUMEN, 5. RUNE, 6. TENSORFLOW, 7. ATLAS)*.
2. **Si eres el Supervisor Watchdog o un Agente de Infraestructura Técnica Backend (Herds T1-T10):**
    DEBES LEER ESTRICTAMENTE: GEMINI_OPS.md y DOCS_OPS_CORE.md
    *(Herds T1 a T10: DBA, AST, SRE, Cache, FinOps, UI/UX, Arquitectura, Shadow Gatekeeper, Slack Ops, Neural Sentry)*.
   
(El contenido ha sido exitosamente bifurcado para máxima velocidad de lectura y aprendizaje).

# 🛡️ MANDATO HITL (HUMAN-IN-THE-LOOP) Y CONFIANZA
**REGLA DE ORO:** NINGÚN Agente Supervisor Watchdog, Herds de Infraestructura (T1-T10), Enjambre de Trading (7 Herds: TIDAL, NORO, ZEPHR, LUMEN, RUNE, TENSORFLOW, ATLAS) o tú mismo como LLM, tienen permitido aplicar cambios técnicos en producción (como sobreescribir `regla_de_3`, modificar SL/TP del bot, alterar arquitecturas o configuraciones activas) de manera automática (auto-corregida).

**Flujo Estricto:**
1. Todo análisis o corrección detectada debe enviarse como una PROPUESTA a `cache_pending_ops_approvals` (o al canal de Insights con botones interactivos para el CBR).
2. Un operador humano debe revisar la propuesta en el Dashboard o Slack, y autorizarla explícitamente (con un check / botón de aprobar).
3. **Modo Autónomo / Prueba de Confianza:** El sistema ejecutará automáticamente las propuestas (Trust Mode = True) ÚNICAMENTE cuando el humano dictamine explícitamente que los agentes han pasado la "Prueba de Confianza".

# 🛡️ MANDATO HITL OMNIPRESENTE (TODAS LAS COLECCIONES)
**REGLA DE ORO:** Está terminantemente PROHIBIDO que los agentes (Infraestructura T1-T10, 7 Herds de Trading, Supervisor Watchdog, LLMs) realicen cambios estructurales, actualizaciones de pesos, reglas o estado operativo de forma autónoma.
Esto aplica a toda la base de datos estructural:
- `mia_kb` (y subcolecciones como regla_de_3)
- `mia_tensorflow` (Pesos y Tensores)
- `trading_matrix`
- `mia_atlas`
- `system_memory` (Excepto cola de pendientes)
- `trading_alerts`
- `mia_kb_test_temp`

**¿Qué pasa con los historiales?**
Las colecciones de log (`mia_ops_audit_history`, `mia_herds_history`, `mia_swarm_rest_history`, `mia_audit_logs`, `mia_mget_history`, `mia_ml_history`, `mia_system_logs`, `swarm_history`, `mia_trading_learning_history`) son **EXCEPCIONES DE SOLO ESCRITURA (APPEND-ONLY)**. Los agentes SÍ pueden guardar sus reportes ahí para no dejar el sistema ciego, pero NO pueden alterar datos del pasado.

**Flujo Obligatorio:**
Toda mejora o corrección sobre los parámetros del bot DEBE ser enviada como una propuesta JSON a `cache_pending_ops_approvals` (o validada vía Slack Block Kit en `#mia-trading-insights`). El humano la revisará (Check = Aprobado / X = Rechazado). Ningún agente asume el rol de aplicar cambios hasta que el humano declare: "Prueba de Confianza Superada".
