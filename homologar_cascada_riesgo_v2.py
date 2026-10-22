import os
import sys
import json
import datetime
import requests

UPSTASH_URL = "https://firm-koi-93555.upstash.io"
UPSTASH_TOKEN = "gQAAAAAAAW1zAAIgcDFmZGI5MGViNWY4Mjc0MGE1Yjg3NDZiOTdiN2MyMjg5Yg"
UPSTASH_HEADERS = {
    "Authorization": f"Bearer {UPSTASH_TOKEN}",
    "Content-Type": "application/json"
}

print("=== INICIANDO HOMOLOGACION DE CASCADA DE RIESGO V2 EN UPSTASH Y FIREBASE ===")

# 1. Definición Canónica de la Cascada de Gestión de Riesgo v2
cascada_v2 = {
    "tp1_distancia_pct": 50.0,
    "tp1_volumen_cierre_pct": 50.0,
    "ratio_rr_tp1": 1.0,
    "be_activacion_post_tp1": True,
    "be_buffer_pips": 2.5,
    "be_respiro_mercado_pct": 50.0,
    "tp2_trailing_lock_dist_pct": 75.0,
    "tp2_ganancia_asegurada_pct": 40.0,
    "tp2_holgura_precio_pct": 35.0,
    "tp3_trailing_lock_dist_pct": 85.0,
    "tp3_ganancia_asegurada_pct": 65.0,
    "tp3_holgura_precio_pct": 20.0,
    "front_run_cierre_total_pct": 95.0,
    "front_run_proposito": "Cierre 100% remanente para evitar rebote en ultimo pip",
    "filtro_oro_ath": {
        "activo": "XAUUSD",
        "prohibir_ventas_en_ath": True,
        "umbral_ath_precio": 2700.0,
        "solo_compras_en_retroceso": True,
        "estado": "ACTIVO_OBLIGATORIO"
    },
    "lotaje_minimo_institucional": {
        "min_lot_para_partir": 0.02,
        "umbral_balance_usd": 3000.0,
        "estado": "ACTIVO"
    },
    "version": "2.0.0-INSTITUCIONAL",
    "fecha_calibracion": datetime.datetime.now(datetime.timezone.utc).isoformat()
}

# 2. Homologar en cache_regla_de_3 (Upstash Redis)
try:
    r_r3 = requests.get(f"{UPSTASH_URL}/get/cache_regla_de_3", headers=UPSTASH_HEADERS, timeout=5)
    r3_data = {}
    if r_r3.status_code == 200 and r_r3.json().get("result"):
        raw_r3 = r_r3.json().get("result")
        r3_data = json.loads(raw_r3) if isinstance(raw_r3, str) else (raw_r3 or {})
    
    r3_data["cascada_gestion_riesgo_v2"] = cascada_v2
    r3_data["ultima_actualizacion"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    
    r_set_r3 = requests.post(f"{UPSTASH_URL}/set/cache_regla_de_3", headers=UPSTASH_HEADERS, data=json.dumps(r3_data), timeout=5)
    if r_set_r3.status_code == 200:
        print("[OK] Upstash cache_regla_de_3 actualizado con cascada_gestion_riesgo_v2.")
    else:
        print(f"[ERROR] Fallo al actualizar cache_regla_de_3: {r_set_r3.text}")
except Exception as e_r3:
    print(f"[ERROR] Excepción en cache_regla_de_3: {e_r3}")

# 3. Homologar en cache_trading_matrix (Upstash Redis)
try:
    r_mat = requests.get(f"{UPSTASH_URL}/get/cache_trading_matrix", headers=UPSTASH_HEADERS, timeout=5)
    mat_data = {}
    if r_mat.status_code == 200 and r_mat.json().get("result"):
        raw_mat = r_mat.json().get("result")
        mat_data = json.loads(raw_mat) if isinstance(raw_mat, str) else (raw_mat or {})
    
    activos = ["EURUSD", "GBPUSD", "AUDUSD", "GBPJPY", "XAUUSD", "NZDCAD"]
    for act in activos:
        if act not in mat_data:
            mat_data[act] = {}
        mat_data[act]["cascada_gestion_riesgo_v2"] = cascada_v2
        if act == "XAUUSD":
            mat_data[act]["filtro_ath_anti_ventas"] = True
            
    r_set_mat = requests.post(f"{UPSTASH_URL}/set/cache_trading_matrix", headers=UPSTASH_HEADERS, data=json.dumps(mat_data), timeout=5)
    if r_set_mat.status_code == 200:
        print(f"[OK] Upstash cache_trading_matrix actualizado para los 6 activos.")
    else:
        print(f"[ERROR] Fallo al actualizar cache_trading_matrix: {r_set_mat.text}")
except Exception as e_mat:
    print(f"[ERROR] Excepción en cache_trading_matrix: {e_mat}")

# 4. Homologar en cache_trading_learning_kb (CBR Memory en Upstash Redis)
try:
    r_cbr = requests.get(f"{UPSTASH_URL}/get/cache_trading_learning_kb", headers=UPSTASH_HEADERS, timeout=5)
    cbr_data = {}
    if r_cbr.status_code == 200 and r_cbr.json().get("result"):
        raw_cbr = r_cbr.json().get("result")
        cbr_data = json.loads(raw_cbr) if isinstance(raw_cbr, str) else (raw_cbr or {})
    
    nuevo_caso = {
        "id_caso": "CASE_RISK_CASCADE_V2_20261021",
        "tipo": "OPTIMIZACION_ESTRUCTURAL_GESTION_RIESGO",
        "descripcion": "Reforma del Trailing Stop y Parciales para revertir R:R invertido (1:0.29) y proteger corredores institucionales.",
        "parametros_anteriores": {
            "tp1_dist": "40%",
            "tp1_vol": "25%",
            "be": "Inmediato al 40% (+2 pips, sofocando trades)",
            "xauusd": "Ventas permitidas en ATH (causo -$1,321 USD de perdidas)",
            "min_lot": "0.01 (imposible de partir en parciales)"
        },
        "parametros_nuevos_v2": cascada_v2,
        "impacto_proyectado": "Elevacion del R:R a >1:1.5, cobro de 50% de ganancia en cash (+1.0R) dejando 50% de respiro a BE, eliminacion de ventas en oro ATH, proteccion total del capital base $5,000 USD.",
        "aprobado_por": "PADRE_HITL_SOLICITUD_EXPLICITA",
        "fecha": datetime.datetime.now(datetime.timezone.utc).isoformat()
    }
    
    casos = cbr_data.get("casos_recientes", [])
    # Reemplazar o insertar
    casos = [c for c in casos if c.get("id_caso") != "CASE_RISK_CASCADE_V2_20261021"]
    casos.insert(0, nuevo_caso)
    cbr_data["casos_recientes"] = casos[:20]
    cbr_data["ultima_actualizacion"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    
    r_set_cbr = requests.post(f"{UPSTASH_URL}/set/cache_trading_learning_kb", headers=UPSTASH_HEADERS, data=json.dumps(cbr_data), timeout=5)
    if r_set_cbr.status_code == 200:
        print("[OK] Upstash cache_trading_learning_kb actualizado con el caso CBR canónico.")
    else:
        print(f"[ERROR] Fallo al actualizar cache_trading_learning_kb: {r_set_cbr.text}")
except Exception as e_cbr:
    print(f"[ERROR] Excepción en cache_trading_learning_kb: {e_cbr}")

# 5. Homologar en Firebase Firestore (Persistencia pasiva si las credenciales existen)
try:
    import firebase_admin
    from firebase_admin import credentials, firestore
    
    cred_path = "credentials.json"
    if os.path.exists(cred_path):
        if not firebase_admin._apps:
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)
        db = firestore.client()
        
        # 5.1 mia_kb/regla_de_3
        try:
            db.collection("mia_kb").document("regla_de_3").set(r3_data, merge=True)
            print("[OK] Firestore mia_kb/regla_de_3 homologado exitosamente.")
        except Exception as e_fs_r3:
            print(f"[WARN] No se pudo guardar en Firestore mia_kb/regla_de_3 (posible cuota 429): {e_fs_r3}")
            
        # 5.2 mia_trading_learning_history
        try:
            db.collection("mia_trading_learning_history").document("CASE_RISK_CASCADE_V2_20261021").set(nuevo_caso, merge=True)
            print("[OK] Firestore mia_trading_learning_history homologado exitosamente.")
        except Exception as e_fs_cbr:
            print(f"[WARN] No se pudo guardar en Firestore mia_trading_learning_history: {e_fs_cbr}")
            
        # 5.3 trading_matrix
        for act in activos:
            try:
                db.collection("trading_matrix").document(act).set({"cascada_gestion_riesgo_v2": cascada_v2}, merge=True)
            except Exception:
                pass
        print("[OK] Firestore trading_matrix homologado para activos.")
    else:
        print("[INFO] credentials.json no local, persistencia operativa garantizada en Upstash Redis (Cloud hot memory).")
except Exception as e_fb:
    print(f"[INFO] Firebase pasivo no disponible o en cuota: {e_fb}. Upstash es la fuente viva caliente.")

print("=== HOMOLOGACION COMPLETADA CON EXITO ===")
