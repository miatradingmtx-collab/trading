import json, datetime, os
import requests
from firebase_admin import credentials, firestore
import firebase_admin

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
db = firestore.client() if firebase_admin._apps else None

UPSTASH_URL = "https://certain-gnat-160816.upstash.io"
UPSTASH_TOKEN = "gQAAAAAAAnQwAAIgcDI2YTA5YjRlZDU2MDM0OWU5ODhlZjBlYTk4ODYyZDg0OA"
headers = {"Authorization": f"Bearer {UPSTASH_TOKEN}"}

print("Iniciando MGET Watchdog Sync (Herd T1 & T4)...")

# 1. Sync ATLAS vía Autocuración Reconciliadora
try:
    from mia_researcher_agent import atlas_researcher
    res_recon = atlas_researcher.reconcile_and_sync_atlas_snapshots(db_client=db, days_lookback=14)
    print(f"ATLAS homologado en Firebase snapshots_historicos: {res_recon}")
except Exception as e_atl:
    print(f"Error sincronizando ATLAS: {e_atl}")

# 2. Sync MGET History
res_mget = requests.get(f"https://trading-production-1fd4.up.railway.app/api/cache_mget")
if res_mget.status_code == 200:
    mget_data = res_mget.json().get('data', {})
    fecha_hoy = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    doc_id = f"MGET_SNAPSHOT_{fecha_hoy}"
    # Guardamos solo lo critico para no inflar Firebase (ya que la cache es grande)
    payload = {
        "balance_actual": mget_data.get("balance_actual", 0),
        "kpis": json.loads(mget_data.get("kpis", "{}")) if isinstance(mget_data.get("kpis"), str) else mget_data.get("kpis", {}),
        "timestamp": str(datetime.datetime.now(datetime.timezone.utc))
    }
    fecha_corta = datetime.datetime.now().strftime('%Y-%m-%d')
    db.collection('mia_mget_history').document(fecha_corta).collection('snapshots').document(doc_id).set(payload)
    
    # Enviar copia fresca a Upstash (Hot Cache) para que TF y Enjambres lo lean en milisegundos
    import requests
    UPSTASH_URL = os.getenv("UPSTASH_REDIS_REST_URL", "https://certain-gnat-160816.upstash.io")
    UPSTASH_TOKEN = os.getenv("UPSTASH_REDIS_REST_TOKEN", "gQAAAAAAAnQwAAIgcDI2YTA5YjRlZDU2MDM0OWU5ODhlZjBlYTk4ODYyZDg0OA")
    headers = {"Authorization": f"Bearer {UPSTASH_TOKEN}"}
    
    try:
        requests.post(f"{UPSTASH_URL}/set/cache_mia_mget_latest", headers=headers, json=payload, timeout=3)
    except Exception:
        pass
    
    print(f"MGET_HISTORY homologado en Firebase ({fecha_corta}) y en Upstash Cache")

print("Sync completado con exito.")
