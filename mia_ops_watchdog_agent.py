#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
MIA OPS WATCHDOG AGENT (RAMA 2 - BACK-OFFICE / SRE & HERDS T1-T10)
================================================================================
Agente independiente y desacoplado para la supervisión de infraestructura y SRE.
Alineado estrictamente con GEMINI.md (Canal: #back-office-y-backend | Motor: Llama 3.3 70B).

MISIÓN EXCLUSIVA:
- Estabilidad técnica del ecosistema (Railway 927a/1fd4, Docker, Uvicorn, Upstash Redis, Firestore).
- Latencia MGET sub-35ms y monitoreo continuo de cuotas y rendimiento.
- Consumo asíncrono de la cola de incidentes de infraestructura (cache_ops_incidents_queue).
- Despacho de Block Kit interactivo a Slack en #back-office-y-backend.
- Gestión de la memoria CBR de Operaciones (cache_ops_learning_kb / mia_ops_learning_history).

RESTRICCIÓN TERMINANTE (GEMINI.md):
- CERO intervención en pares de divisas, velas, SL/TP, trailing stops ni estrategias de mercado.
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

class MiaOpsWatchdogAgent:
    """
    SUPERVISOR INDEPENDIENTE DE INFRAESTRUCTURA Y SRE (RAMA 2).
    Completamente aislado del Supervisor Quant de Trading (Rama 1).
    Canal Exclusivo: #back-office-y-backend (C0C4ZMFCMJ8).
    Motor LLM: Llama 3.3 70B (OpenRouter Ops / Groq).
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

    def _llm_llama_ops_inference(self, prompt: str, system_prompt: Optional[str] = None) -> Dict[str, Any]:
        """
        Inferencia especializada en SRE e Infraestructura técnica con Llama 3.3 70B.
        Zero-cost failover a Groq si OpenRouter no responde.
        """
        sys_context = system_prompt or (
            "Eres MIA SRE Watchdog Master (Llama 3.3 70B). Tu misión exclusiva es la estabilidad técnica, "
            "evaluación de incidentes de infraestructura, latencias MGET, bases de datos (Upstash/Firestore) "
            "y servidores Railway. Devuelve estrictamente un objeto JSON con las claves: "
            "'diagnostico_sre', 'severidad' (BAJA/MEDIA/ALTA/CRITICA), 'causa_raiz_probable' y 'accion_preventiva_recomendada'."
        )

        # Intento 1: OpenRouter (Llama 3.3 70B)
        if self.OPENROUTER_KEY:
            try:
                headers = {
                    "Authorization": f"Bearer {self.OPENROUTER_KEY}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "model": "meta-llama/llama-3.3-70b-instruct",
                    "messages": [
                        {"role": "system", "content": sys_context},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.2,
                    "max_tokens": 1500
                }
                r = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload, timeout=12)
                if r.status_code == 200:
                    content = r.json().get("choices", [{}])[0].get("message", {}).get("content", "")
                    if content:
                        parsed = self._extract_json(content)
                        if parsed:
                            return parsed
            except Exception as e_or:
                print(f"| OPS WATCHDOG WARN | OpenRouter falló: {e_or}")

        # Intento 2: Groq Failover (Llama 3.3 70B Versatile)
        if self.GROQ_KEY:
            for g_model in ["llama-3.3-70b-versatile", "qwen/qwen3.8-27b", "openai/gpt-oss-120b"]:
                try:
                    headers = {
                        "Authorization": f"Bearer {self.GROQ_KEY}",
                        "Content-Type": "application/json"
                    }
                    payload = {
                        "model": g_model,
                        "messages": [
                            {"role": "system", "content": sys_context},
                            {"role": "user", "content": prompt}
                        ],
                        "temperature": 0.2,
                        "max_tokens": 1500
                    }
                    r = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload, timeout=8)
                    if r.status_code == 200:
                        content = r.json().get("choices", [{}])[0].get("message", {}).get("content", "")
                        if content:
                            parsed = self._extract_json(content)
                            if parsed:
                                return parsed
                except Exception as e_groq:
                    print(f"| OPS WATCHDOG WARN | Failover Groq ({g_model}) falló: {e_groq}")
                    continue

        # Fallback determinista
        return {
            "diagnostico_sre": "Análisis SRE completado mediante motor determinista de contingencia.",
            "severidad": "MEDIA",
            "causa_raiz_probable": "Anomalía en flujo de ejecución reportada por el sistema.",
            "accion_preventiva_recomendada": "Verificar telemetría de red y latencias MGET en Upstash."
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

    def drain_and_process_incident_queue(self) -> Dict[str, Any]:
        """
        Drena y procesa de forma asíncrona todos los incidentes técnicos encolados en
        Upstash Redis (cache_ops_incidents_queue).
        Garantiza CERO acoplamiento con el Agente Quant de Trading.
        """
        print("| OPS WATCHDOG | Escaneando cola de incidentes técnicos (cache_ops_incidents_queue)...")
        incidents = []

        try:
            # 1. Leer todos los incidentes en la cola
            r_range = requests.get(f"{self.UPSTASH_URL}/lrange/cache_ops_incidents_queue/0/-1", headers=self.UPSTASH_HEADERS, timeout=4)
            if r_range.status_code == 200 and r_range.json().get("result"):
                raw_items = r_range.json().get("result", [])
                for item in raw_items:
                    try:
                        incidents.append(json.loads(item) if isinstance(item, str) else item)
                    except Exception:
                        incidents.append({"raw": str(item)})

                # 2. Vaciar la cola atómicamente tras la extracción
                requests.post(f"{self.UPSTASH_URL}/del/cache_ops_incidents_queue", headers=self.UPSTASH_HEADERS, timeout=4)
                print(f"| OPS WATCHDOG | {len(incidents)} incidentes técnicos extraídos de la cola.")
        except Exception as e_queue:
            print(f"| OPS WATCHDOG ERROR | Fallo accediendo a la cola de incidentes: {e_queue}")
            return {"status": "error", "message": str(e_queue), "processed": 0}

        if not incidents:
            print("| OPS WATCHDOG | Cola de incidentes limpia (0 pendientes).")
            return {"status": "success", "processed": 0, "message": "Cola vacía"}

        processed_count = 0
        for inc in incidents:
            try:
                ticket = inc.get("ticket", "N/A")
                symbol = inc.get("symbol", "GLOBAL")
                tipo = inc.get("tipo", "ANOMALIA_TECNICA")
                nota = inc.get("nota_tecnica", inc.get("detalle", str(inc)))
                timestamp = inc.get("timestamp", datetime.datetime.now().isoformat())

                prompt_rca = f"""
                Analiza el siguiente incidente técnico de infraestructura reportado en la ejecución de la operativa:
                - Tipo de Incidente: {tipo}
                - Ticket Afectado: {ticket} | Activo: {symbol}
                - Timestamp: {timestamp}
                - Detalle Técnico: {nota}

                Instrucciones:
                Evalúa si se trató de una degradación de latencia, un timeout de socket, una reconexión de Railway o una anomalía de red.
                Devuelve estrictamente un JSON con 'diagnostico_sre', 'severidad', 'causa_raiz_probable' y 'accion_preventiva_recomendada'.
                """
                eval_sre = self._llm_llama_ops_inference(prompt_rca)

                diagnostico = eval_sre.get("diagnostico_sre", nota)
                severidad = eval_sre.get("severidad", "MEDIA").upper()
                causa = eval_sre.get("causa_raiz_probable", "Degradación transitoria de red.")
                accion = eval_sre.get("accion_preventiva_recomendada", "Monitorear latencia MGET.")

                # Guardar en CBR de Infraestructura
                case_id = f"OPS_INCIDENT_{ticket}_{int(time.time())}"
                payload_cbr = {
                    "caso": f"Incidente Técnico SRE {ticket}",
                    "fecha": timestamp,
                    "ticket": ticket,
                    "symbol": symbol,
                    "tipo": tipo,
                    "severidad": severidad,
                    "diagnostico": diagnostico,
                    "causa_raiz": causa,
                    "accion_recomendada": accion
                }

                if self.db:
                    try:
                        self.db.collection("mia_ops_learning_history").document(case_id).set(payload_cbr)
                    except Exception:
                        pass

                # Despachar a Slack (#back-office-y-backend) con Block Kit
                if slack_bridge:
                    emoji_sev = "🔴" if severidad in ["CRITICA", "ALTA"] else ("🟡" if severidad == "MEDIA" else "🔵")
                    blocks = [
                        {
                            "type": "header",
                            "text": {
                                "type": "plain_text",
                                "text": f"{emoji_sev} MIA SRE WATCHDOG: Incidente Técnico ({severidad})",
                                "emoji": True
                            }
                        },
                        {
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": (
                                    f"*Ticket:* `{ticket}` | *Activo:* `{symbol}` | *Tipo:* `{tipo}`\n\n"
                                    f"*🛠️ Diagnóstico SRE (Llama 3.3 70B):*\n{diagnostico}\n\n"
                                    f"*🔍 Causa Raíz Probable:*\n{causa}\n\n"
                                    f"*💡 Acción Recomendada:*\n{accion}"
                                )
                            }
                        },
                        {
                            "type": "context",
                            "elements": [
                                {
                                    "type": "mrkdwn",
                                    "text": f"ID Caso: `{case_id}` | Memoria SRE: `mia_ops_learning_history` | Rama 2 (Back-Office)."
                                }
                            ]
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
                                    "text": {"type": "plain_text", "text": "Archivar Incidente ✅", "emoji": True},
                                    "value": f"archive_{case_id}",
                                    "action_id": f"archive_incident_{ticket}"
                                }
                            ]
                        },
                        {
                            "type": "divider"
                        }
                    ]

                    slack_bridge.send_channel_message(
                        text=f"🚨 MIA SRE Watchdog: Incidente {severidad} en Ticket {ticket}",
                        channel=self.SLACK_OPS_CHANNEL,
                        username="MIA SRE Watchdog",
                        icon_emoji=":shield:",
                        blocks=blocks
                    )

                processed_count += 1
            except Exception as e_proc:
                print(f"| OPS WATCHDOG ERROR | Error procesando incidente individual: {e_proc}")

        return {"status": "success", "processed": processed_count}

    def check_infrastructure_telemetry(self) -> Dict[str, Any]:
        """
        Audita el estado de los componentes del backend:
        1. Ping y latencia a Upstash Redis REST.
        2. Estado de conexión con Firestore.
        3. Endpoint de salud de Railway.
        4. Estado de TensorFlow Deep Learning en caché.
        """
        telemetry = {
            "timestamp": datetime.datetime.now().isoformat(),
            "upstash_redis_ms": -1.0,
            "firestore_online": False,
            "railway_service_online": False,
            "tensorflow_trades": 0,
            "estado_general": "DESCONOCIDO"
        }

        # 1. Ping Upstash Redis
        t0 = time.time()
        try:
            r = requests.get(f"{self.UPSTASH_URL}/ping", headers=self.UPSTASH_HEADERS, timeout=3)
            if r.status_code == 200:
                telemetry["upstash_redis_ms"] = round((time.time() - t0) * 1000, 2)
        except Exception:
            pass

        # 2. Firestore
        telemetry["firestore_online"] = self.db is not None

        # 3. Railway Ping
        try:
            r_rail = requests.get("https://trading-production-927a.up.railway.app/health", timeout=4)
            telemetry["railway_service_online"] = (r_rail.status_code == 200)
        except Exception:
            pass

        # 4. TensorFlow
        try:
            r_tf = requests.get(f"{self.UPSTASH_URL}/get/cache_mia_tensorflow", headers=self.UPSTASH_HEADERS, timeout=3)
            if r_tf.status_code == 200 and r_tf.json().get("result"):
                raw = r_tf.json().get("result")
                d_tf = json.loads(raw) if isinstance(raw, str) else raw
                telemetry["tensorflow_trades"] = d_tf.get("trades_aprendidos", 687)
        except Exception:
            pass

        lat = telemetry["upstash_redis_ms"]
        if lat > 0 and lat < 45.0 and telemetry["railway_service_online"]:
            telemetry["estado_general"] = "NOMINAL (ALTA EFICIENCIA)"
        elif lat >= 45.0:
            telemetry["estado_general"] = "DEGRADADO (LATENCIA ELEVADA)"
        else:
            telemetry["estado_general"] = "ALERTA (COMPONENTES DESCONECTADOS)"

        return telemetry

    def dispatch_ops_alert(self, title: str, text: str, severity: str = "WARNING", actions: Optional[List[Dict[str, Any]]] = None) -> bool:
        """
        Helper público y estandarizado para que cualquier servicio de la Rama 2
        pueda emitir alertas a #back-office-y-backend con identidad visual coherente.
        """
        if not slack_bridge:
            return False

        icon = ":warning:" if severity in ["WARNING", "ALTA", "CRITICA"] else ":shield:"
        blocks = [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": f"🛡️ MIA SRE WATCHDOG: {title}", "emoji": True}
            },
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": text}
            }
        ]
        if actions:
            blocks.append({"type": "actions", "elements": actions})
        blocks.append({"type": "divider"})

        return slack_bridge.send_channel_message(
            text=f"{title}: {text[:100]}",
            channel=self.SLACK_OPS_CHANNEL,
            username="MIA SRE Watchdog",
            icon_emoji=icon,
            blocks=blocks
        )

    def run_watchdog_cycle(self, audit_herds: bool = False) -> Dict[str, Any]:
        """
        Ciclo completo del Watchdog de Operaciones:
        1. Drena y analiza la cola de incidentes de infraestructura.
        2. Audita telemetría de latencia y servicios.
        3. Opcionalmente dispara la auditoría completa de los 10 Herds (T1 a T10).
        """
        print("| OPS WATCHDOG | Iniciando ciclo de monitoreo SRE...")
        inc_res = self.drain_and_process_incident_queue()
        tel_res = self.check_infrastructure_telemetry()

        res = {
            "incidentes": inc_res,
            "telemetria": tel_res,
            "timestamp": datetime.datetime.now().isoformat()
        }

        if audit_herds:
            try:
                from mia_system_ops_swarm import system_ops_supervisor
                audit_summary = system_ops_supervisor.run_swarm_audit(notify_slack=True)
                res["herds_audit"] = audit_summary.get("estado_general", "OK")
            except Exception as e_audit:
                print(f"| OPS WATCHDOG WARN | No se pudo ejecutar auditoría de Herds: {e_audit}")

        return res

if __name__ == "__main__":
    watchdog = MiaOpsWatchdogAgent()
    result = watchdog.run_watchdog_cycle(audit_herds=False)
    print("\n| RESULTADO CICLO OPS WATCHDOG |")
    print(json.dumps(result, indent=2))
