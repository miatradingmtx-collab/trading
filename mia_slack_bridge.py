"""
MIA SLACK BRIDGE (HUMAN-IN-THE-LOOP & CHATOPS INTEGRATION)
===========================================================
Conector de comunicación entre el Watchdog Supervisor (Back-Office)
y el usuario a través de Slack.
Permite:
1. Transparencia total: cada uno de los 6 Herds reporta qué está haciendo y qué detectó.
2. Veredicto Senior del Supervisor Watchdog.
3. Modo FASE 1 STRICT HUMAN-IN-THE-LOOP: Cero cambios automáticos sin aprobación previa.
4. Selección con checkboxes para autorizar propuestas individuales o todas.
5. Botones interactivos de acción directa:
   - [Aprobar Seleccionadas ☑️]
   - [Aprobar Todas ✅]
   - [Rechazar / Mantener Actual ⛔]
   - [Forzar Resync 🔄]
6. Enlaces directos a Dashboards:
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
    def __init__(self, webhook_url: Optional[str] = None, bot_token: Optional[str] = None):
        self.webhook_url = webhook_url or os.getenv("SLACK_WEBHOOK_URL", "")
        self.bot_token = bot_token or os.getenv("SLACK_BOT_TOKEN", "")

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

    def send_channel_message(self, text: str, channel: Optional[str] = None) -> bool:
        """
        Envía un mensaje a un canal específico (ej: #mia-chat o #back-office-y-backend).
        Si SLACK_BOT_TOKEN está configurado, usa chat.postMessage al canal indicado.
        Si no, utiliza el webhook configurado por defecto.
        """
        if self.bot_token and channel:
            try:
                headers = {
                    "Authorization": f"Bearer {self.bot_token}",
                    "Content-Type": "application/json"
                }
                payload = {"channel": channel, "text": text}
                r = requests.post("https://slack.com/api/chat.postMessage", headers=headers, json=payload, timeout=5)
                if r.status_code == 200 and r.json().get("ok", False):
                    return True
            except Exception as e:
                print(f"| SLACK ERROR | Error enviando a {channel} vía API: {e}")

        return self.send_raw_message(text)

    def send_senior_ops_report(self, summary: Dict[str, Any]) -> bool:
        """
        Envía un reporte Senior consolidado con transparencia de los 6 Herds,
        Veredicto del Supervisor, checkboxes para seleccionar propuestas individuales
        y Botones para Aprobación Humana estricta.
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
        options_checkboxes = []
        if por_aprobar:
            txt_aprobar = "\n".join([
                f"{i+1}. ⚠️ *{pa.get('accion', 'PROPUESTA')}*: {pa.get('detalle', pa.get('propuesta', ''))}"
                for i, pa in enumerate(por_aprobar[:6])
            ])
            for i, pa in enumerate(por_aprobar[:6]):
                act_label = pa.get('accion', f'PROPUESTA_{i+1}')
                desc_label = pa.get('detalle', pa.get('propuesta', ''))[:40]
                options_checkboxes.append({
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*{i+1}. {act_label}*: {desc_label}"[:75]
                    },
                    "value": f"propuesta_{i}"
                })
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
            }
        ]

        # Agregar bloque de selección interactiva con checkboxes si hay propuestas
        if options_checkboxes:
            blocks.append({
                "type": "section",
                "block_id": "proposals_selection_block",
                "text": {
                    "type": "mrkdwn",
                    "text": "*☑️ Selecciona qué propuestas específicas deseas autorizar:*"
                },
                "accessory": {
                    "type": "checkboxes",
                    "action_id": "selected_proposals_checkbox",
                    "options": options_checkboxes
                }
            })

            # Botones con opción de autorizar seleccionadas, todas o rechazar
            blocks.append({
                "type": "actions",
                "block_id": "watchdog_triage_actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "Aprobar Seleccionadas ☑️", "emoji": True},
                        "style": "primary",
                        "value": "approve_selected",
                        "action_id": "approve_selected_action"
                    },
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "Aprobar Todas ✅", "emoji": True},
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
            })
        else:
            blocks.append({
                "type": "actions",
                "block_id": "watchdog_triage_actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "Forzar Resync 🔄", "emoji": True},
                        "value": "force_resync",
                        "action_id": "resync_action"
                    }
                ]
            })

        # Agregar enlace de inspección previa si hay propuestas visuales
        if any("PLOTLY" in str(p) or "DASHBOARD" in str(p) for p in por_aprobar):
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "🎨 *Inspección Visual Requerida:* Puedes comparar los cambios de interfaz antes de aprobar:\n👉 <https://trading-production-927a.up.railway.app/dashboard/preview|*Haga clic aquí para Ver Previsualización Interactiva (Antes vs Después)*>"
                }
            })

        blocks.append({
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": (
                        "🔗 *Dashboards:* "
                        "<https://trading-production-1fd4.up.railway.app/brain|🧠 Red Neuronal> | "
                        "<https://trading-production-1fd4.up.railway.app/|🌐 Enjambres 3D> | "
                        "<https://trading-production-927a.up.railway.app/dashboard|📊 Dashboard MT5> | "
                        "<https://trading-production-927a.up.railway.app/dashboard/preview|🎨 Visual Diff>"
                    )
                }
            ]
        })

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
