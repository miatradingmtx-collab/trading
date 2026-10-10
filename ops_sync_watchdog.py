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

# 2. Sync MGET History vía Reconciliador Continuo
try:
    from mia_mget_manager import reconcile_and_sync_mget_history
    res_mget = reconcile_and_sync_mget_history(db_client=db, days_lookback=14)
    print(f"MGET_HISTORY reconciliado y homologado en Firebase y Upstash Cache: {res_mget}")
except Exception as e_mget:
    print(f"Error sincronizando MGET en ops_sync_watchdog: {e_mget}")

print("Sync completado con exito.")
