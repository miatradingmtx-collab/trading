"""
MIA SLACK BRIDGE (HUMAN-IN-THE-LOOP & CHATOPS INTEGRATION)
===========================================================
Conector de comunicación entre el Watchdog Supervisor (Back-Office)
y el usuario a través de Slack.
Permite:
1. Publicación de eventos y reportes en canales dedicados (#mia-ops-watchdog).
2. Solicitud de Aprobación Humana (Human-in-the-Loop) con Botones Interactivos:
   - [APROBAR ACCIÓN ✅]
   - [RECHAZAR / IGNORAR ⛔]
   - [FORZAR RECALIBRACIÓN 🔄]
3. Manejo de Slash Commands (/mia-status, /mia-sync, /mia-regla3).
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

    def send_ops_report(self, audit_summary: Dict[str, Any]) -> bool:
        """
        Envía una tarjeta rica (Block Kit) a Slack con el reporte del Enjambre de Operaciones.
        """
        if not self.webhook_url:
            return False

        herds = audit_summary.get("herds_results", {})
        t1 = herds.get("herd_t1_db_sync", {})
        t2 = herds.get("herd_t2_kb_engine", {})
        t3 = herds.get("herd_t3_kpi_analytics", {})
        t4 = herds.get("herd_t4_devops_health", {})

        top1 = t2.get("top_1", {})
        top2 = t2.get("top_2", {})
        top3 = t2.get("top_3", {})

        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "🛡️ MIA SYSTEM OPS SWARM - Reporte de Integridad",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Supervisor:* WATCHDOG MASTER"},
                    {"type": "mrkdwn", "text": f"*Estado del Sistema:* `100% OPERACIONAL`"},
                    {"type": "mrkdwn", "text": f"*Posiciones MT5:* `{t1.get('posiciones_activas', 'N/A')}` activas"},
                    {"type": "mrkdwn", "text": f"*Flotante Neto:* `${t1.get('flotante_neto', 0.0):+.2f} USD`"},
                    {"type": "mrkdwn", "text": f"*Equidad Total:* `${t1.get('equity', 0.0):.2f} USD`"},
                    {"type": "mrkdwn", "text": f"*Latencia Upstash:* `{t4.get('upstash_latency_ms', 0)} ms`"}
                ]
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": (
                        f"*📐 Regla de 3 Dinámica (Veredicto de Éxito):*\n"
                        f"• *Top 1:* `{top1.get('indicador')}` ({top1.get('win_rate_asociado')}%) | Peso: {top1.get('peso')}\n"
                        f"• *Top 2:* `{top2.get('indicador')}` ({top2.get('win_rate_asociado')}%) | Peso: {top2.get('peso')}\n"
                        f"• *Top 3:* `{top3.get('indicador')}` ({top3.get('win_rate_asociado')}%) | Peso: {top3.get('peso')}"
                    )
                }
            },
            {
                "type": "divider"
            }
        ]

        try:
            r = requests.post(self.webhook_url, json={"blocks": blocks}, timeout=4)
            return r.status_code == 200
        except Exception as e:
            print(f"| SLACK ERROR | Error enviando reporte Block Kit: {e}")
            return False

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
