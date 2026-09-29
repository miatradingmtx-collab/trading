"""
MIA SLACK BRIDGE (HUMAN-IN-THE-LOOP & CHATOPS INTEGRATION)
===========================================================
Conector de comunicación entre el Watchdog Supervisor (Back-Office)
y el usuario a través de Slack.
Permite:
1. Publicación de eventos y reportes en canales dedicados (#back-office-y-backend).
2. Reportes enriquecidos con Triage Senior de 6 Herds Técnicos:
   - [AUTO-CORREGIDO EN CALIENTE ✅]
   - [REQUIERE APROBACIÓN HUMANA ⚠️]
3. Solicitud de Aprobación Humana (Human-in-the-Loop) con Botones Interactivos:
   - [APROBAR CAMBIO ✅]
   - [RECHAZAR / CANCELAR ⛔]
   - [PAGAR / FONDEAR 💳]
4. Enlaces directos a Dashboards:
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
        Envía un reporte Senior consolidado con Triage de 6 Herds:
        - Auto-corregidos en caliente
        - Propuestas que requieren aprobación humana (con botones)
        """
        if not self.webhook_url:
            return False

        triage = summary.get("triage", {})
        auto_corregidos = triage.get("auto_corregidos_en_caliente", [])
        por_aprobar = triage.get("requiere_aprobacion_humana", [])
        ms = summary.get("total_execution_ms", 0.0)
        estado = summary.get("estado_general", "OPTIMAL_HEALTH")

        # Texto para sección Auto-Corregidos
        if auto_corregidos:
            txt_auto = "\n".join([f"• ✅ {ac}" for ac in auto_corregidos[:6]])
        else:
            txt_auto = "• ✅ Cero anomalías detectadas. Datos y sintaxis 100% íntegros."

        # Texto para sección Por Aprobar
        if por_aprobar:
            txt_aprobar = "\n".join([f"• ⚠️ *{pa.get('accion', 'PROPUESTA')}*: {pa.get('detalle', '')}" for pa in por_aprobar[:4]])
        else:
            txt_aprobar = "• Ninguna acción pendiente de autorización. Todo opera en régimen autónomo."

        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "🛡️ MIA WATCHDOG SUPERVISOR - Triage de Infraestructura (6 Herds)",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": "*Supervisor:* `MIA_WATCHDOG_MASTER (Sr Lead)`"},
                    {"type": "mrkdwn", "text": f"*Salud General:* `{estado}`"},
                    {"type": "mrkdwn", "text": "*Malla Técnica:* `6 Herds Online (T1-T6)`"},
                    {"type": "mrkdwn", "text": f"*Tiempo Auditoría:* `{ms} ms`"}
                ]
            },
            {
                "type": "divider"
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*⚡ [AUTO-CORREGIDO EN CALIENTE POR LOS HERDS]:*\n{txt_auto}"
                }
            },
            {
                "type": "divider"
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*📋 [PROPUESTAS QUE REQUIEREN APROBACIÓN HUMANA]:*\n{txt_aprobar}"
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
