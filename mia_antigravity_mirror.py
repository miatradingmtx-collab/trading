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

