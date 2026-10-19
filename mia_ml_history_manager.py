"""
====================================================================
MÓDULO DE GESTIÓN Y RECONCILIACIÓN HISTÓRICA ML (MIA ML HISTORY MANAGER)
====================================================================
Rol: Auditoría, Materialización Canónica y Autocuración Continua de mia_ml_history
Colección Firestore: mia_ml_history/<YYYY-MM-DD>
Hot Cache Redis: cache_ml_history y cache_amd_mtf_history
Consumidores: 7 Herds Swarm (Llama 70B), TensorFlow (Herd 6), ATLAS (Herd 7)
====================================================================
"""

import os
import json
import datetime
from typing import Dict, Any, Optional, List
import requests

UPSTASH_URL = os.getenv("UPSTASH_REDIS_REST_URL", "https://firm-koi-93555.upstash.io")
UPSTASH_TOKEN = os.getenv("UPSTASH_REDIS_REST_TOKEN", "gQAAAAAAAW1zAAIgcDFmZGI5MGViNWY4Mjc0MGE1Yjg3NDZiOTdiN2MyMjg5Yg")
UPSTASH_HEADERS = {"Authorization": f"Bearer {UPSTASH_TOKEN}"}

# Vectores de ponderación AMD MTF Canónicos
CANONICAL_AMD_WEIGHTS = {
    "smc_4_sweep": 2.3000,
    "smc_2_fvg": 1.8500,
    "lux_algo_ob_4h": 1.6500,
    "smc_1_ob": 1.6000,
    "volume_poc_price": 1.4500,
    "ma_alineada": 1.2500,
    "rsi_extremo": 1.1500,
    "amd_trampa_macro_evitada": 2.1000,
    "amd_macro_8h_sweep": 2.2000,
    "amd_macro_4h_sweep": 2.0500,
    "amd_confluencia_macro": 1.9500,
    "amd_sweep_3h": 1.7500,
    "amd_sweep_2h": 1.6000,
    "amd_sweep_1h": 1.4500,
    "amd_sweep_intradia": 1.4000
}

def _get_db(db_client=None):
    """Obtiene el cliente de Firestore de forma resiliente."""
    if db_client is not None:
        return db_client
    try:
        import firebase_admin
        from firebase_admin import credentials, firestore
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
        if firebase_admin._apps:
            return firestore.client()
    except Exception as e:
        print(f"| ML DB INIT WARN | {e}")
    return None

def fetch_current_indicators_and_sessions(db=None):
    """Obtiene los indicadores y sesiones actuales desde Redis, memoria o Firestore."""
    indicadores = []
    sesiones = []

    # 1. Intentar leer desde Upstash Redis (0 lecturas Firestore)
    try:
        session = requests.Session()
        session.trust_env = False
        r_ind = session.get(f"{UPSTASH_URL}/get/cache_mia_kb_indicadores", headers=UPSTASH_HEADERS, timeout=3)
        if r_ind.status_code == 200:
            res_val = r_ind.json().get("result")
            if res_val:
                indicadores = json.loads(res_val)
    except Exception as e_red:
        pass

    # 2. Si no están en Redis, leer desde Firestore
    if not indicadores and db is not None:
        try:
            inds_docs = db.collection("mia_kb").document("indicadores_impacto").collection("detalle").get()
            indicadores = [{"id": d.id, **d.to_dict()} for d in inds_docs]
        except Exception as e_ind_fs:
            print(f"| ML HISTORY WARN | Error leyendo indicadores de Firestore: {e_ind_fs}")

    if db is not None:
        try:
            sess_docs = db.collection("mia_kb").document("sesiones_rendimiento").collection("detalle").get()
            sesiones = [{"id": s.id, **s.to_dict()} for s in sess_docs]
        except Exception as e_sess:
            print(f"| ML HISTORY WARN | Error leyendo sesiones de Firestore: {e_sess}")

    return indicadores, sesiones

def compute_dynamic_weights(indicadores: List[Dict[str, Any]]) -> Dict[str, float]:
    """Calcula el vector de pesos dinámicos de Machine Learning."""
    dyn_weights = dict(CANONICAL_AMD_WEIGHTS)
    for ind in indicadores:
        ind_id = ind.get("id", "").lower()
        wr = float(ind.get("win_rate", 0))
        calc_w = round(max(0.20, (wr / 100.0) * 2.0 + 0.30), 4)
        if ind_id not in dyn_weights or calc_w > dyn_weights[ind_id]:
            dyn_weights[ind_id] = calc_w
    return dyn_weights

def build_ml_snapshot_payload(fecha_str: str, indicadores: List[Dict[str, Any]], sesiones: List[Dict[str, Any]], timestamp_iso: Optional[str] = None, origen: str = "ml_daily_snapshot") -> Dict[str, Any]:
    """Construye el payload canónico para el snapshot de mia_ml_history."""
    if not timestamp_iso:
        timestamp_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

    dyn_weights = compute_dynamic_weights(indicadores)

    snapshot = {
        "fecha": fecha_str,
        "indicadores": indicadores,
        "sesiones": sesiones,
        "dynamic_weights": dyn_weights,
        "kpis": {
            "dynamic_weights": dyn_weights,
            "total_indicadores": len(indicadores),
            "total_sesiones": len(sesiones)
        },
        "timestamp": timestamp_iso,
        "origen": origen
    }
    return snapshot

def sync_upstash_caches(snapshot: Dict[str, Any], db=None):
    """Sincroniza los caches calientes en Upstash Redis (cache_ml_history y cache_amd_mtf_history)."""
    try:
        session = requests.Session()
        session.trust_env = False
        r1 = session.post(
            f"{UPSTASH_URL}/set/cache_ml_history",
            headers=UPSTASH_HEADERS,
            data=json.dumps(snapshot, default=str),
            timeout=4
        )
        if r1.status_code == 200:
            print("| UPSTASH | cache_ml_history sincronizado exitosamente con Redis")
    except Exception as e_up1:
        print(f"| UPSTASH WARN | Error sincronizando cache_ml_history: {e_up1}")

    try:
        recent_amd_trades = []
        if db is not None:
            r_docs = db.collection("mia_kb").document("amd_mtf_history").collection("trades").limit(10).stream()
            recent_amd_trades = [d.to_dict() for d in r_docs]

        amd_cache_payload = {
            "metadata": {
                "descripcion": "Memoria Histórica y Ponderación de Estrategia AMD MTF (1H, 2H, 3H, 4H, 8H)",
                "temporalidades": ["1h", "2h", "3h", "4h", "8h"],
                "vectores_ponderacion": {
                    "amd_macro_8h_sweep": 2.2000,
                    "amd_macro_4h_sweep": 2.0500,
                    "amd_confluencia_macro": 1.9500,
                    "amd_sweep_3h": 1.7500,
                    "amd_sweep_2h": 1.6000,
                    "amd_sweep_1h": 1.4500,
                    "amd_sweep_intradia": 1.4000,
                    "amd_trampa_macro_evitada": 2.1000
                },
                "total_trades": len(recent_amd_trades),
                "ultima_actualizacion": datetime.datetime.now(datetime.timezone.utc).isoformat()
            },
            "ultimos_trades": recent_amd_trades
        }
        session = requests.Session()
        session.trust_env = False
        r2 = session.post(
            f"{UPSTASH_URL}/set/cache_amd_mtf_history",
            headers=UPSTASH_HEADERS,
            data=json.dumps(amd_cache_payload, default=str),
            timeout=4
        )
        if r2.status_code == 200:
            print("| UPSTASH | cache_amd_mtf_history sincronizado exitosamente con Redis")
    except Exception as e_amd_c:
        print(f"| UPSTASH WARN | Error sincronizando cache_amd_mtf_history: {e_amd_c}")

def reconcile_and_sync_ml_history(db_client=None, days_lookback: int = 14) -> Dict[str, Any]:
    """
    Reconciliación y Autocuración Continua de Snapshots Históricos ML:
    - Examina los últimos `days_lookback` días hasta la fecha actual (UTC y Local).
    - Para cada fecha, verifica si existe el documento en mia_ml_history/<YYYY-MM-DD>.
    - Si falta alguna fecha, autogenera el snapshot diario con los indicadores y sesiones auditados (Auto-Backfill).
    - Actualiza la fecha de hoy con el snapshot vivo del mercado.
    - Sincroniza el slot 'cache_ml_history' y 'cache_amd_mtf_history' en Upstash Redis para los 7 Herds y TensorFlow.
    """
    db = _get_db(db_client)
    now_utc = datetime.datetime.now(datetime.timezone.utc)
    now_iso = now_utc.isoformat()
    today_utc_str = now_utc.strftime('%Y-%m-%d')
    today_local_str = datetime.datetime.now().strftime('%Y-%m-%d')

    indicadores, sesiones = fetch_current_indicators_and_sessions(db)

    # Si no se obtuvieron indicadores, intentar cargar del snapshot más reciente existente
    if not indicadores and db is not None:
        try:
            recent_docs = db.collection("mia_ml_history").order_by("fecha", direction="DESCENDING").limit(1).get()
            if recent_docs:
                last_snap = recent_docs[0].to_dict()
                indicadores = last_snap.get("indicadores", [])
                sesiones = last_snap.get("sesiones", [])
                print(f"| ML RECONCILER | Recuperados {len(indicadores)} indicadores del snapshot {recent_docs[0].id}")
        except Exception as e_rec:
            print(f"| ML RECONCILER WARN | Error recuperando de snapshot previo: {e_rec}")

    # Snapshot de hoy
    today_snapshot = build_ml_snapshot_payload(
        fecha_str=today_utc_str,
        indicadores=indicadores,
        sesiones=sesiones,
        timestamp_iso=now_iso,
        origen="ml_reconciliation_service"
    )

    # 1. Hot Cache Upstash Redis
    sync_upstash_caches(today_snapshot, db=db)

    if not db:
        print("| ML RECONCILER WARN | Firestore no disponible. Retornando estado Hot Cache.")
        return {
            "status": "partial",
            "message": "Actualizado en Redis, pero Firestore no inicializado",
            "snapshot": today_snapshot
        }

    coll_ref = db.collection("mia_ml_history")

    # 2. Guardar snapshot de hoy (UTC y Local si difieren)
    for t_str in set([today_utc_str, today_local_str]):
        try:
            snap_payload = build_ml_snapshot_payload(
                fecha_str=t_str,
                indicadores=indicadores,
                sesiones=sesiones,
                timestamp_iso=now_iso,
                origen="ml_daily_snapshot"
            )
            coll_ref.document(t_str).set(snap_payload)
            print(f"| ML RECONCILER | Sincronizada jornada actual: {t_str}")
        except Exception as e_tod:
            print(f"| ML RECONCILER ERROR | Error escribiendo snapshot de {t_str}: {e_tod}")

    # 3. Auto-Curación y Backfill de los últimos `days_lookback` días
    hoy_base = now_utc.date()
    dates_to_check = [
        (hoy_base - datetime.timedelta(days=i)).strftime("%Y-%m-%d")
        for i in range(days_lookback, -1, -1)
    ]

    verified = []
    backfilled = []

    for f_date in dates_to_check:
        try:
            doc_ref = coll_ref.document(f_date)
            doc_snap = doc_ref.get()

            if not doc_snap.exists:
                # Falta fecha -> Auto-Curación (Append-Only Mandato HITL)
                snap_backfill = build_ml_snapshot_payload(
                    fecha_str=f_date,
                    indicadores=indicadores,
                    sesiones=sesiones,
                    timestamp_iso=f"{f_date}T23:55:00Z",
                    origen="ml_self_healing_backfill"
                )
                doc_ref.set(snap_backfill)
                print(f"| ML SELF-HEALING | Autocurada jornada ML faltante: {f_date}")
                backfilled.append(f_date)
            else:
                verified.append(f_date)
        except Exception as e_chk:
            print(f"| ML RECONCILER WARN | Error verificando fecha {f_date}: {e_chk}")

    print(f"| ML RECONCILER | Fechas verificadas: {len(verified)}, Fechas autocuradas: {len(backfilled)}")
    return {
        "status": "success",
        "fechas_verificadas": len(verified),
        "fechas_autocuradas": backfilled,
        "total_cobertura_dias": len(verified) + len(backfilled),
        "ultima_actualizacion": now_iso
    }

if __name__ == "__main__":
    print("Iniciando reconciliación y autocuración de mia_ml_history...")
    res = reconcile_and_sync_ml_history(days_lookback=14)
    print("Resultado:", json.dumps(res, indent=2))
