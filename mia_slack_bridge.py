"""
MIA SLACK BRIDGE (HUMAN-IN-THE-LOOP & CHATOPS INTEGRATION)
===========================================================
Conector de comunicación entre el Watchdog Supervisor (Back-Office)
y el usuario a través de Slack.
Permite:
1. Transparencia total: cada uno de los 6 Herds reporta qué está haciendo y qué detectó.
2. Veredicto Senior del Supervisor Watchdog.
3. Modo FASE 1 STRICT HUMAN-IN-THE-LOOP: Cero cambios automáticos sin aprobación previa.
4. Botones interactivos de acción directa:
   - [Aprobar Propuestas ✅]
   - [Rechazar / Mantener Actual ⛔]
   - [Forzar Resync 🔄]
5. Enlaces directos a Dashboards:
   - Red Neuronal: https://trading-production-1fd4.up.railway.app/brain
   - Enjambres 3D: https://trading-production-1fd4.up.railway.app/
   - Dashboard Plotly: https://trading-production-927a.up.railway.app/dashboard
"""

import os
import json
import requests
from typing import Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()

SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL", "")
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN", "")

class MiaSlackBridge:
    def __init__(self, webhook_url: Optional[str] = None):
        self.webhook_url = webhook_url or os.getenv("SLACK_WEBHOOK_URL", "")

    def send_raw_message(self, text: str) -> bool:
        if not self.webhook_url:
            print("| SLACK BRIDGE | Webhook no configurado (SLACK_WEBHOOK_URL). Mensaje omitido.")
            return False
        try:
            r = requests.post(self.webhook_url, json={"text": text}, timeout=4)
            return r.status_code == 200
        except Exception as e:
            print(f"| SLACK ERROR | Error enviando mensaje crudo: {e}")
            return False

    def send_senior_ops_report(self, summary: Dict[str, Any]) -> bool:
        """
        Envía un reporte Senior consolidado con transparencia de los 6 Herds,
        Veredicto del Supervisor y Botones para Aprobación Humana estricta.
        """
        if not self.webhook_url:
            return False

        herds = summary.get("herds_results", {})
        t1 = herds.get("herd_t1_dba", {})
        t2 = herds.get("herd_t2_senior_dev", {})
        t3 = herds.get("herd_t3_observability_sre", {})
        t4 = herds.get("herd_t4_cache_latency", {})
        t5 = herds.get("herd_t5_finops_billing", {})
        t6 = herds.get("herd_t6_ui_ux_designer", {})

        triage = summary.get("triage", {})
        por_aprobar = triage.get("requiere_aprobacion_humana", [])
        ms = summary.get("total_execution_ms", 0.0)
        estado = summary.get("estado_general", "OPTIMAL_HEALTH")

        # 1. Desglose detallado de qué está haciendo cada uno de los 6 agentes
        txt_agentes = (
            f"• *🗄️ HERD T1 (DBA Sentinel):* {t1.get('resumen', 'Auditoría de base de datos activa.')}\n"
            f"• *💻 HERD T2 (Senior Dev):* {t2.get('resumen', 'Auditoría de sintaxis y código activa.')}\n"
            f"• *📡 HERD T3 (Observability SRE):* {t3.get('resumen', 'Monitoreo de endpoints activo.')}\n"
            f"• *⚡ HERD T4 (Cache Latency):* {t4.get('resumen', 'Medición de latencia sub-35ms activa.')}\n"
            f"• *💳 HERD T5 (FinOps Billing):* {t5.get('resumen', 'Control de presupuesto y pagos activo.')}\n"
            f"• *🎨 HERD T6 (UI/UX Plotly):* {t6.get('resumen', 'Auditoría visual de dashboards activa.')}"
        )

        # 2. Veredicto del Supervisor
        txt_supervisor = (
            f"*Veredicto Global:* `{estado}` (Auditado en {ms} ms)\n"
            f"*Modo Operativo:* `FASE 1: STRICT HUMAN-IN-THE-LOOP` 🔒\n"
            f"*Directriz:* Ningún agente modifica producción sin tu confirmación previa."
        )

        # 3. Propuestas que requieren aprobación humana
        if por_aprobar:
            txt_aprobar = "\n".join([
                f"{i+1}. ⚠️ *{pa.get('accion', 'PROPUESTA')}*: {pa.get('detalle', pa.get('propuesta', ''))}"
                for i, pa in enumerate(por_aprobar[:5])
            ])
        else:
            txt_aprobar = "• ✅ Cero cambios pendientes de autorización. Todo opera en óptimas condiciones."

        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "🛡️ MIA WATCHDOG SUPERVISOR - Auditoría & Triage de Infraestructura",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*👑 VEREDICTO DEL SUPERVISOR GENERAL:*\n{txt_supervisor}"
                }
            },
            {
                "type": "divider"
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*🔍 ¿QUÉ ESTÁ HACIENDO CADA UNO DE LOS 6 AGENTES?*\n{txt_agentes}"
                }
            },
            {
                "type": "divider"
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*📋 [PROPUESTAS PENDIENTES DE APROBACIÓN HUMANA]:*\n{txt_aprobar}"
                }
            },
            {
                "type": "actions",
                "block_id": "watchdog_triage_actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "Aprobar Propuestas ✅", "emoji": True},
                        "style": "primary",
                        "value": "approve_all_pending",
                        "action_id": "approve_triage_action"
                    },
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "Rechazar / Mantener Actual ⛔", "emoji": True},
                        "style": "danger",
                        "value": "reject_all_pending",
                        "action_id": "reject_triage_action"
                    },
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "Forzar Resync 🔄", "emoji": True},
                        "value": "force_resync",
                        "action_id": "resync_action"
                    }
                ]
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": (
                            "🔗 *Dashboards:* "
                            "<https://trading-production-1fd4.up.railway.app/brain|🧠 Red Neuronal> | "
                            "<https://trading-production-1fd4.up.railway.app/|🌐 Enjambres 3D> | "
                            "<https://trading-production-927a.up.railway.app/dashboard|📊 Dashboard Plotly>"
                        )
                    }
                ]
            }
        ]

        try:
            r = requests.post(self.webhook_url, json={"blocks": blocks}, timeout=4)
            return r.status_code == 200
        except Exception as e:
            print(f"| SLACK ERROR | Error enviando reporte senior: {e}")
            return False

    def send_ops_report(self, audit_summary: Dict[str, Any]) -> bool:
        """Fallback compatible con versiones previas"""
        return self.send_senior_ops_report(audit_summary)

    def send_approval_request(self, action_id: str, title: str, details: str) -> bool:
        """
        Envía una solicitud interactiva a Slack con botones de APROBACIÓN HUMANA.
        """
        if not self.webhook_url:
            return False

        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"⚠️ SOLICITUD DE APROBACIÓN: {title}",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Detalle de la Acción Propuesta:*\n{details}\n\n*¿Autorizas al Supervisor Watchdog a ejecutar esta acción?*"
                }
            },
            {
                "type": "actions",
                "block_id": f"approval_block_{action_id}",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "Aprobar Acción ✅", "emoji": True},
                        "style": "primary",
                        "value": f"approve_{action_id}",
                        "action_id": "approve_action"
                    },
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "Rechazar / Cancelar ⛔", "emoji": True},
                        "style": "danger",
                        "value": f"reject_{action_id}",
                        "action_id": "reject_action"
                    }
                ]
            }
        ]

        try:
            r = requests.post(self.webhook_url, json={"blocks": blocks}, timeout=4)
            return r.status_code == 200
        except Exception as e:
            print(f"| SLACK ERROR | Error enviando solicitud de aprobación: {e}")
            return False

slack_bridge = MiaSlackBridge()
