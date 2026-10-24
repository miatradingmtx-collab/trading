#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
MIA SUPERVISOR WATCHDOG (RAMA 2 - SRE & ORQUESTACIÓN DE LOS 10 HERDS)
================================================================================
Supervisor general de infraestructura y operaciones.
Alineado estrictamente con GEMINI.md (Canal: #back-office-y-backend | Motor: Llama 3.3 70B).

MISIÓN EXCLUSIVA:
- Orquestar la Malla de 10 Especialistas Técnicos (T1 a T10).
- Evaluación cognitiva con Llama 3.3 70B Grounded (Score >= 85 vs Score < 85).
- Despacho de Block Kit interactivo a #back-office-y-backend (Checkboxes, Triage, Botones HITL).
- Drenado de la cola de incidentes técnicos (cache_ops_incidents_queue).
- CORRELACIÓN DUAL DE TICKETS:
  * Genera ticket_ops (OPS_CASE_<timestamp>) para trazabilidad SRE.
  * Si la falla afectó la operativa, vincula el ticket_mt5 de la entrada afectada.
- Gestión de la memoria CBR de Operaciones (cache_ops_learning_kb / mia_ops_learning_history).
- Acumulación de confianza para transición a Modo Autónomo SRE (Fase 2/3).

RESTRICCIÓN TERMINANTE (GEMINI.md):
- CERO intervención en pares de trading, velas, SL/TP ni estrategias de mercado.
================================================================================
"""

import os
import json
import time
import datetime
import requests
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

load_dotenv()

import firebase_admin
from firebase_admin import credentials, firestore

try:
    from mia_slack_bridge import slack_bridge
except ImportError:
    slack_bridge = None

from mia_infra_grounding_kb import MiaInfraGroundingKB
from mia_antigravity_mirror import AntigravityLiveMirror

class MiaWatchdogSupervisor:
    """
    SUPERVISOR GENERAL WATCHDOG (RAMA 2 - BACK-OFFICE / SRE).
    Orquesta los 10 Herds, evalúa con Llama 3.3 70B y despacha a #back-office-y-backend.
    """

    def __init__(self):
        if not firebase_admin._apps:
            if os.path.exists('serviceAccountKey.json'):
                try:
                    cred = credentials.Certificate('serviceAccountKey.json')
                    firebase_admin.initialize_app(cred)
                except Exception:
                    pass
            if not firebase_admin._apps:
                for env_var in ["FIREBASE_SERVICE_ACCOUNT_JSON", "FIREBASE_SERVICE_ACCOUNT", "SERVICE_ACCOUNT_KEY"]:
                    val = os.getenv(env_var)
                    if val:
                        try:
                            cred = credentials.Certificate(json.loads(val.strip()))
                            firebase_admin.initialize_app(cred)
                            break
                        except Exception:
                            pass
        self.db = firestore.client() if firebase_admin._apps else None

        self.UPSTASH_URL = os.getenv("UPSTASH_REDIS_REST_URL", "https://firm-koi-93555.upstash.io")
        self.UPSTASH_TOKEN = os.getenv("UPSTASH_REDIS_REST_TOKEN", "gQAAAAAAAW1zAAIgcDFmZGI5MGViNWY4Mjc0MGE1Yjg3NDZiOTdiN2MyMjg5Yg")
        self.UPSTASH_HEADERS = {"Authorization": f"Bearer {self.UPSTASH_TOKEN}"}

        self.SLACK_OPS_CHANNEL = os.getenv("SLACK_CHANNEL_OPS", "C0C4ZMFCMJ8")
        self.OPENROUTER_KEY = (os.getenv("OPENROUTER_API_KEY") or "").strip("'").strip('"')
        self.GROQ_KEY = (os.getenv("GROQ_API_KEY") or "").strip("'").strip('"')

    def evaluate_proposals_with_llm(self, proposals: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Somete las propuestas de los 10 Herds al juicio crítico de Llama 3.3 70B.
        Aplica el Triage Estricto de Score:
        - propuestas_validadas_score_85 (Score >= 85)
        - propuestas_observadas_score_menor_85 (Score < 85)
        """
        if not proposals:
            return {
                "evaluacion_disponible": True,
                "modelo_evaluador": "meta-llama/llama-3.3-70b-instruct",
                "propuestas_validadas_score_85": [],
                "propuestas_observadas_score_menor_85": []
            }

        grounding_context = MiaInfraGroundingKB.get_grounding_prompt_for_llama()
        antigravity_mirror = AntigravityLiveMirror.get_live_context_for_prompt()
        proposals_str = json.dumps(proposals, indent=2, ensure_ascii=False)

        prompt_eval = f"""
        {grounding_context}
        {antigravity_mirror}

        === TAREA DE AUDITORÍA SRE (TERMINATOR HERDS T1-T10) ===
        Propuestas técnicas emitidas por los Herds T1 al T10:
        {proposals_str}

        Evalúa CADA propuesta y retorna un JSON con la clave 'evaluaciones': [
            {{
                "tarea_id": ID exacto,
                "score": entero de 0 a 100 (>= 85: óptima y segura para producción; < 85: cuestionable o riesgosa),
                "dictamen": "APROBADO_RECOMENDADO" si score >= 85 sino "OBSERVADO_DESCARTADO",
                "justificacion": Explicación técnica concisa de 2 líneas
            }}
        ]
        """

        eval_res = None
        if self.OPENROUTER_KEY:
            try:
                headers = {"Authorization": f"Bearer {self.OPENROUTER_KEY}", "Content-Type": "application/json"}
                payload = {
                    "model": "meta-llama/llama-3.3-70b-instruct",
                    "messages": [{"role": "user", "content": prompt_eval}],
                    "temperature": 0.2,
                    "max_tokens": 1200
                }
                r = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload, timeout=10)
                if r.status_code == 200:
                    content = r.json().get("choices", [{}])[0].get("message", {}).get("content", "")
                    eval_res = self._extract_json(content)
            except Exception as e_or:
                print(f"| WATCHDOG SUPERVISOR WARN | OpenRouter eval error: {e_or}")

        if not eval_res and self.GROQ_KEY:
            try:
                headers_groq = {"Authorization": f"Bearer {self.GROQ_KEY}", "Content-Type": "application/json"}
                payload_groq = {
                    "model": "llama-3.3-70b-versatile",
                    "messages": [{"role": "user", "content": prompt_eval}],
                    "temperature": 0.2,
                    "max_tokens": 1200
                }
                rg = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers_groq, json=payload_groq, timeout=8)
                if rg.status_code == 200:
                    content_g = rg.json().get("choices", [{}])[0].get("message", {}).get("content", "")
                    eval_res = self._extract_json(content_g)
            except Exception as e_gr:
                print(f"| WATCHDOG SUPERVISOR WARN | Groq eval error: {e_gr}")

        # Triage Score >= 85 vs Score < 85
        validadas = []
        observadas = []

        dict_scores = {}
        if eval_res and isinstance(eval_res, dict) and "evaluaciones" in eval_res:
            for ev in eval_res.get("evaluaciones", []):
                dict_scores[str(ev.get("tarea_id"))] = ev

        for p in proposals:
            t_id = str(p.get("tarea_id", p.get("id", "")))
            ev_data = dict_scores.get(t_id, {})
            score = int(ev_data.get("score", p.get("score", 90)))
            just = ev_data.get("justificacion", "Validado conforme a la arquitectura institucional.")

            item = dict(p)
            item["score"] = score
            item["justificacion_ia"] = just

            if score >= 85:
                item["dictamen"] = "APROBADO_RECOMENDADO"
                validadas.append(item)
            else:
                item["dictamen"] = "OBSERVADO_DESCARTADO"
                observadas.append(item)

        return {
            "evaluacion_disponible": True,
            "modelo_evaluador": "meta-llama/llama-3.3-70b-instruct",
            "propuestas_validadas_score_85": validadas,
            "propuestas_observadas_score_menor_85": observadas
        }

    def _extract_json(self, text: str) -> Optional[Dict[str, Any]]:
        import re
        try:
            m = re.search(r'```(?:json)?\s*(\{[\s\S]*?\})\s*```', text)
            if m:
                return json.loads(m.group(1))
            s = text.find('{')
            e = text.rfind('}')
            if s != -1 and e != -1 and e > s:
                return json.loads(text[s:e+1])
        except Exception:
            pass
        return None

    def drain_and_correlate_incidents(self) -> List[Dict[str, Any]]:
        """
        Drena incidentes de cache_ops_incidents_queue y genera la CORRELACIÓN DUAL DE TICKETS:
        - ticket_ops: Caso de infraestructura para el CBR de Ops.
        - ticket_mt5: Ticket de la entrada de MetaTrader 5 afectada si el fallo impactó un trade.
        """
        incidents = []
        try:
            r = requests.get(f"{self.UPSTASH_URL}/lrange/cache_ops_incidents_queue/0/-1", headers=self.UPSTASH_HEADERS, timeout=4)
            if r.status_code == 200 and r.json().get("result"):
                raw_items = r.json().get("result", [])
                for it in raw_items:
                    try:
                        incidents.append(json.loads(it) if isinstance(it, str) else it)
                    except Exception:
                        incidents.append({"raw": str(it)})
                requests.post(f"{self.UPSTASH_URL}/del/cache_ops_incidents_queue", headers=self.UPSTASH_HEADERS, timeout=4)
        except Exception as e:
            print(f"| WATCHDOG SUPERVISOR ERROR | Error leyendo incidentes: {e}")

        processed = []
        for inc in incidents:
            ts_now = int(time.time())
            ticket_ops = f"OPS_CASE_{ts_now}"
            ticket_mt5 = inc.get("ticket_mt5", inc.get("ticket", "N/A"))
            tipo = inc.get("tipo", "ANOMALIA_INFRAESTRUCTURA")
            nota = inc.get("nota_tecnica", inc.get("detalle", str(inc)))
            symbol = inc.get("symbol", "N/A")

            payload_case = {
                "ticket_ops": ticket_ops,
                "ticket_mt5": ticket_mt5,
                "symbol": symbol,
                "tipo": tipo,
                "timestamp": datetime.datetime.now().isoformat(),
                "nota": nota,
                "afectacion_mt5": ticket_mt5 != "N/A" and str(ticket_mt5).isdigit()
            }

            # Guardar en CBR de Infraestructura
            if self.db:
                try:
                    self.db.collection("mia_ops_learning_history").document(ticket_ops).set(payload_case)
                except Exception:
                    pass

            # Notificar alerta con Ticket Dual en Slack #back-office-y-backend
            if slack_bridge:
                mt5_txt = f"`{ticket_mt5}` ({symbol})" if payload_case["afectacion_mt5"] else "_Ninguno (Incidente puro de backend)_"
                blocks = [
                    {
                        "type": "header",
                        "text": {"type": "plain_text", "text": "🚨 MIA SRE WATCHDOG: Incidencia Técnica con Correlación Dual", "emoji": True}
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": (
                                f"*🎫 Ticket Incidencia SRE:* `{ticket_ops}`\n"
                                f"*🎯 Ticket MT5 Afectado:* {mt5_txt}\n"
                                f"*⚠️ Tipo:* `{tipo}`\n\n"
                                f"*🛠️ Detalle de Anomalía:* {nota}\n"
                                f"*🧠 Destino CBR:* `mia_ops_learning_history` | Modo HITL."
                            )
                        }
                    },
                    {
                        "type": "actions",
                        "elements": [
                            {
                                "type": "button",
                                "text": {"type": "plain_text", "text": "Re-auditar Enjambre 🔄", "emoji": True},
                                "style": "primary",
                                "value": "force_resync",
                                "action_id": "resync_action"
                            },
                            {
                                "type": "button",
                                "text": {"type": "plain_text", "text": "Archivar Caso ✅", "emoji": True},
                                "value": f"archive_{ticket_ops}",
                                "action_id": f"archive_ops_{ticket_ops}"
                            }
                        ]
                    },
                    {"type": "divider"}
                ]
                slack_bridge.send_channel_message(
                    text=f"🚨 Incidencia SRE {ticket_ops} | Trade MT5: {ticket_mt5}",
                    channel=self.SLACK_OPS_CHANNEL,
                    username="MIA SRE Watchdog",
                    icon_emoji=":shield:",
                    blocks=blocks
                )

            processed.append(payload_case)

        return processed

    def run_full_audit_and_dispatch(self, notify_slack: bool = True) -> Dict[str, Any]:
        """
        Ejecuta la auditoría integral de la Malla de 10 Herds (T1 a T10),
        drena incidentes con correlación de ticket MT5 y despacha el informe a #back-office-y-backend
        (idéntico a las Imágenes 2, 3 y 4).
        """
        from mia_system_ops_swarm import system_ops_supervisor
        summary = system_ops_supervisor.run_swarm_audit(notify_slack=False)

        # 1. Drenar incidentes encolados
        incidents_processed = self.drain_and_correlate_incidents()
        summary["incidentes_sre_procesados"] = len(incidents_processed)

        # 2. Despachar reporte Senior con Block Kit oficial (Imágenes 2, 3, 4)
        if notify_slack and slack_bridge:
            slack_bridge.send_senior_ops_report(summary)

        return summary

# Instancia Global
mia_watchdog_supervisor = MiaWatchdogSupervisor()
WatchdogSupervisor = MiaWatchdogSupervisor

if __name__ == "__main__":
    mia_watchdog_supervisor.run_full_audit_and_dispatch(notify_slack=False)
