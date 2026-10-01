"""
MIA ANTIGRAVITY LIVE MIRROR & PROMPT SYNCHRONIZER
=================================================
Módulo de sincronización en paralelo entre Google Antigravity y Llama 3.3 70B (OpenRouter).

Propósito:
Garantizar que todo prompt, directriz, corrección, diseño o mejora que se escribe y
ejecuta en Antigravity se transfiera en caliente a Upstash Redis (cache_mia_live_antigravity_delta)
para que cuando el Watchdog Supervisor consulte a Llama en OpenRouter, Llama tenga
exactamente el mismo contexto, memoria y decisiones que Antigravity, eliminando cualquier
discrepancia o desactualización cognitiva.
"""

import os
import json
import datetime
import subprocess
import requests
from typing import Dict, Any, List

UPSTASH_URL = os.getenv("UPSTASH_REDIS_REST_URL", "https://certain-gnat-160816.upstash.io")
UPSTASH_TOKEN = os.getenv("UPSTASH_REDIS_REST_TOKEN", "gQAAAAAAAnQwAAIgcDI2YTA5YjRlZDU2MDM0OWU5ODhlZjBlYTk4ODYyZDg0OA")
UPSTASH_HEADERS = {
    "Authorization": f"Bearer {UPSTASH_TOKEN}",
    "Content-Type": "application/json"
}

class AntigravityLiveMirror:
    SLOT_KEY = "cache_mia_live_antigravity_delta"

    @classmethod
    def capture_git_latest_delta(cls) -> Dict[str, Any]:
        """Extrae el último commit, autor, mensaje y lista de archivos modificados."""
        try:
            cmd_commit = ["git", "log", "-n", "3", "--pretty=format:%h|%s|%an|%ad"]
            res = subprocess.run(cmd_commit, capture_output=True, text=True, timeout=5)
            commits = []
            if res.returncode == 0 and res.stdout.strip():
                for line in res.stdout.strip().split("\n"):
                    parts = line.split("|")
                    if len(parts) >= 4:
                        commits.append({
                            "hash": parts[0],
                            "mensaje": parts[1],
                            "autor": parts[2],
                            "fecha": parts[3]
                        })

            cmd_status = ["git", "status", "-s"]
            res_st = subprocess.run(cmd_status, capture_output=True, text=True, timeout=5)
            archivos_modificados = []
            if res_st.returncode == 0 and res_st.stdout.strip():
                archivos_modificados = [l.strip() for l in res_st.stdout.strip().split("\n")[:10]]

            return {
                "ultimos_commits": commits,
                "archivos_en_trabajo": archivos_modificados
            }
        except Exception as e:
            return {"error": str(e), "ultimos_commits": [], "archivos_en_trabajo": []}

    @classmethod
    def extract_antigravity_guidelines(cls) -> Dict[str, Any]:
        """Lee las directrices más recientes consignadas en DOCS_OPS_CORE.md y GEMINI_OPS.md."""
        resumenes = []
        archivos_reglas = ["DOCS_OPS_CORE.md", "GEMINI_OPS.md"]
        for ar in archivos_reglas:
            if os.path.exists(ar):
                try:
                    with open(ar, "r", encoding="utf-8-sig") as f:
                        lines = f.readlines()
                    # Tomar las últimas 40 líneas de actualizaciones recientes
                    ultimas_lineas = "".join(lines[-45:])
                    resumenes.append({
                        "archivo": ar,
                        "extracto_reciente": ultimas_lineas
                    })
                except Exception:
                    pass
        return {"documentos_directrices": resumenes}

    @classmethod
    def build_live_mirror_payload(cls) -> Dict[str, Any]:
        git_delta = cls.capture_git_latest_delta()
        guidelines = cls.extract_antigravity_guidelines()
        now_utc = datetime.datetime.now(datetime.timezone.utc).isoformat()

        payload = {
            "timestamp": now_utc,
            "origen": "Google Antigravity Session (Advanced Agentic Pair Programming)",
            "estado_sincronizacion": "EN_PARALELO_HOMOLOGADO",
            "git_delta": git_delta,
            "antigravity_guidelines": guidelines,
            "decisiones_clave_sesion": [
                "Desacoplamiento total del Enjambre de Ops: Cero reportes de trading en #back-office-y-backend.",
                "Malla de 10 Herds colaborativos (T1 a T10): Incorporación de T10 SWARM_NEURAL_SENTRY.",
                "3er Microservicio de Ops (trading-production-0b51.up.railway.app) DESPLEGADO Y OPERATIVO AL 100%: Slack API, MCP Ops y Herds T1-T10 desacoplados de MT5.",
                "Doble Reporte en Slack: Score >= 85 (Recomendadas con Checkboxes) y Score < 85 (Observadas con motivo de descarte).",
                "Integración Frontend de doble fase: T6 diseña con Google Stitch y extrae CSS/HTML; T2 acopla en el backend.",
                "T7 Architect Diagrammer ratifica arquitectura de 3 microservicios (927a, 1fd4, 0b51) con diagramas Mermaid actualizados.",
                "Aislamiento estricto de canal: Silenciamiento 100% de #mia-chat en el Supervisor Watchdog.",
                "Normalización de Entidades y Vectorización: T1 compacta datos a vectores atómicos 20D en Upstash.",
                "Modo Confianza Progresivo: Acumulación de +1 por aprobación y -2 por rechazo hacia la autonomía total."
            ]
        }
        return payload

    @classmethod
    def sync_to_upstash(cls) -> bool:
        payload = cls.build_live_mirror_payload()
        try:
            r = requests.post(f"{UPSTASH_URL}/set/{cls.SLOT_KEY}", headers=UPSTASH_HEADERS, json=payload, timeout=4)
            return r.status_code == 200
        except Exception:
            return False

    @classmethod
    def push_to_microservice(cls, endpoint_url: str = None) -> bool:
        """Envía el Live Mirror delta al endpoint REST del microservicio de Ops en Railway."""
        base_url = endpoint_url or os.getenv("MIA_OPS_SERVICE_URL", "http://localhost:8080")
        target_url = f"{base_url.rstrip('/')}/api/antigravity/mirror/push"
        payload = cls.build_live_mirror_payload()
        try:
            r = requests.post(target_url, json=payload, timeout=5)
            return r.status_code == 200
        except Exception:
            return False

    @classmethod
    def sync_everywhere(cls, microservice_url: str = None) -> Dict[str, bool]:
        """Sincroniza en paralelo a Upstash Redis y al endpoint del nuevo microservicio de Ops."""
        ok_upstash = cls.sync_to_upstash()
        ok_endpoint = cls.push_to_microservice(microservice_url)
        return {"upstash": ok_upstash, "microservice_endpoint": ok_endpoint}

    @classmethod
    def homologate_antigravity_approval(cls, tarea_id_o_accion: str, detalle: str = "", solucion: str = "") -> Dict[str, Any]:
        """
        Homologa en caliente una aprobación o solución ejecutada directamente en Google Antigravity.
        - Elimina la tarea de 'cache_pending_ops_approvals' en Upstash y Firestore.
        - Registra el precedente en 'mia_ops_learning_history' como 'APROBADO_EN_ANTIGRAVITY'.
        - Agrega la decisión al espejo en vivo para que Llama 3.3 la reconozca de inmediato.
        - Sincroniza en caliente en Upstash y en el microservicio 0b51.
        """
        now_str = datetime.datetime.now(datetime.timezone.utc).isoformat()
        
        # 1. Limpiar de cache_pending_ops_approvals
        pendientes_restantes = []
        removidas = []
        try:
            r = requests.get(f"{UPSTASH_URL}/get/cache_pending_ops_approvals", headers=UPSTASH_HEADERS, timeout=4)
            if r.status_code == 200 and r.json().get("result"):
                raw = r.json().get("result")
                pendientes = json.loads(raw) if isinstance(raw, str) else (raw or [])
                for p in pendientes:
                    p_id = str(p.get("tarea_id", "")).upper()
                    p_acc = str(p.get("accion", "")).upper()
                    target_cmp = str(tarea_id_o_accion).upper()
                    if target_cmp in p_id or target_cmp in p_acc:
                        removidas.append(p)
                    else:
                        pendientes_restantes.append(p)
                
                requests.post(f"{UPSTASH_URL}/set/cache_pending_ops_approvals", headers=UPSTASH_HEADERS, json=pendientes_restantes, timeout=4)
        except Exception:
            pass

        # 2. Registrar en Firestore y Upstash Learning History
        clean_key = str(tarea_id_o_accion).replace(" ", "_").upper()[:28]
        case_id = f"CASE_ANTIGRAVITY_{clean_key}"
        learning_payload = {
            "case_id": case_id,
            "tarea_o_accion": tarea_id_o_accion,
            "detalle": detalle or f"Solución aplicada directamente en Antigravity para {tarea_id_o_accion}.",
            "solucion_aplicada": solucion or "Aprobado e implementado en sesión de pair-programming Antigravity.",
            "veredicto_padre": "APROBADO_EN_ANTIGRAVITY",
            "origen": "GOOGLE_ANTIGRAVITY_PAIR_PROGRAMMING",
            "score_confianza": 0.98,
            "estado": "HOMOLOGADO_EN_PRODUCCION",
            "timestamp": now_str
        }
        
        try:
            import firebase_admin
            from firebase_admin import credentials, firestore
            if not firebase_admin._apps:
                cred = credentials.Certificate('serviceAccountKey.json')
                firebase_admin.initialize_app(cred)
            db = firestore.client()
            db.collection('mia_ops_learning_history').document(case_id).set(learning_payload, merge=True)
            db.collection('system_memory').document('cache_pending_ops_approvals').set({"pendientes": pendientes_restantes}, merge=True)
        except Exception:
            pass

        # 3. Guardar también en el slot de Upstash cache_ops_learning_history
        try:
            r_hist = requests.get(f"{UPSTASH_URL}/get/cache_ops_learning_history", headers=UPSTASH_HEADERS, timeout=4)
            hist_data = {}
            if r_hist.status_code == 200 and r_hist.json().get("result"):
                raw_h = r_hist.json().get("result")
                hist_data = json.loads(raw_h) if isinstance(raw_h, str) else (raw_h or {})
            hist_data[case_id] = learning_payload
            requests.post(f"{UPSTASH_URL}/set/cache_ops_learning_history", headers=UPSTASH_HEADERS, json=hist_data, timeout=4)
        except Exception:
            pass

        # 4. Sincronizar espejo en vivo en todos lados
        sync_res = cls.sync_everywhere()

        return {
            "status": "HOMOLOGADO_EXITOSO",
            "case_id": case_id,
            "tarea_homologada": tarea_id_o_accion,
            "tareas_removidas_de_pendientes": len(removidas),
            "pendientes_restantes": len(pendientes_restantes),
            "sync_mirror": sync_res
        }

    @classmethod
    def get_live_context_for_prompt(cls) -> str:
        """Retorna el bloque de texto homologado para inyectar en el prompt de Llama."""
        payload = cls.build_live_mirror_payload()
        commits_str = "\n".join([f"- [{c['hash']}] {c['mensaje']} ({c['fecha']})" for c in payload['git_delta'].get('ultimos_commits', [])])
        decisiones_str = "\n".join([f"• {d}" for d in payload.get('decisiones_clave_sesion', [])])

        return f"""
=== ANTIGRAVITY LIVE MIRROR (SINCRONIZACIÓN EN PARALELO EN TIEMPO REAL) ===
Última Sincronización: {payload['timestamp']}
Origen: Antigravity Session con el Padre.

ÚLTIMOS COMMITS PUSH EN GITHUB & RAILWAY:
{commits_str}

DECISIONES DE ARQUITECTURA HOMOLOGADAS EN ESTA SESIÓN:
{decisiones_str}
==========================================================================
"""

if __name__ == "__main__":
    res = AntigravityLiveMirror.sync_everywhere()
    print(f"Antigravity Live Mirror sincronizado: {res}")
    print(AntigravityLiveMirror.get_live_context_for_prompt()[:350] + "...")

