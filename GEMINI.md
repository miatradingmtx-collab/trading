---
name: enrutador_principal
description: Enrutador de reglas divididas para optimizar el token de contexto.
trigger: always_on
---

#  ENRUTADOR PRINCIPAL GEMINI
Para evitar sobrecarga de contexto y tropiezos entre agentes:
1. **Si eres un Agente de Trading, TensorFlow, ATLAS o Enjambre HFT:** 
    DEBES LEER ESTRICTAMENTE: GEMINI_TRADING.md y DOCS_TRADING_CORE.md
2. **Si eres el Supervisor Watchdog o un Agente de Infraestructura (Herds T1-T10):**
    DEBES LEER ESTRICTAMENTE: GEMINI_OPS.md y DOCS_OPS_CORE.md
   
(El contenido ha sido exitosamente bifurcado para mxima velocidad de lectura y aprendizaje).

# 🛡️ MANDATO HITL (HUMAN-IN-THE-LOOP) Y CONFIANZA
**REGLA DE ORO:** NINGÚN Agente Supervisor, Enjambre (T1-T10) o tú mismo como LLM, tienen permitido aplicar cambios técnicos en producción (como sobreescribir egla_de_3\, modificar SL/TP del bot, alterar arquitecturas o configuraciones activas) de manera automática (auto-corregida).

**Flujo Estricto:**
1. Todo análisis o corrección detectada debe enviarse como una PROPUESTA a \cache_pending_ops_approvals\.
2. Un operador humano debe revisar la propuesta en el Dashboard o Slack, y autorizarla explícitamente (con un check / botón de aprobar).
3. **Modo Autónomo / Prueba de Confianza:** El sistema ejecutará automáticamente las propuestas (Trust Mode = True) ÚNICAMENTE cuando el humano dictamine explícitamente que los T y el Supervisor han pasado la \Prueba de Confianza\.

# 🛡️ MANDATO HITL OMNIPRESENTE (TODAS LAS COLECCIONES)
**REGLA DE ORO:** Está terminantemente PROHIBIDO que los agentes (T1-T10, Supervisor, LLMs) realicen cambios estructurales, actualizaciones de pesos, reglas o estado operativo de forma autónoma.
Esto aplica a toda la base de datos estructural:
- `mia_kb` (y subcolecciones como regla_de_3)
- `mia_tensorflow` (Pesos y Tensores)
- `trading_matrix`
- `mia_atlas`
- `system_memory` (Excepto cola de pendientes)
- `trading_alerts`
- `mia_kb_test_temp`

**¿Qué pasa con los historiales?**
Las colecciones de log (`mia_ops_audit_history`, `mia_herds_history`, `mia_swarm_rest_history`, `mia_audit_logs`, `mia_mget_history`, `mia_ml_history`, `mia_system_logs`, `swarm_history`) son **EXCEPCIONES DE SOLO ESCRITURA (APPEND-ONLY)**. Los agentes SÍ pueden guardar sus reportes ahí para no dejar el sistema ciego, pero NO pueden alterar datos del pasado.

**Flujo Obligatorio:**
Toda mejora o corrección sobre los parámetros del bot DEBE ser enviada como una propuesta JSON a `cache_pending_ops_approvals`. El humano la revisará (Check = Aprobado / X = Rechazado). Ningún agente asume el rol de aplicar cambios hasta que el humano declare: "Prueba de Confianza Superada".
