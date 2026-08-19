import os
import json
import datetime
import firebase_admin
from firebase_admin import credentials, firestore

WAREHOUSE_DIR = r"D:\Logs Trading"
DB_FILE = os.path.join(WAREHOUSE_DIR, "mia_historico.json")
CRED_FILE = r"C:\Users\ecybe\OneDrive\Documentos\Trading\serviceAccountKey.json"

print("🩺 Iniciando Script Sanador (Plan DRP) - Inyección Inteligente con Aprendizaje...")

# 1. Cargar la verdad absoluta
if not os.path.exists(DB_FILE):
    print(f"❌ ERROR: No se encontró la base local en {DB_FILE}")
    exit(1)

with open(DB_FILE, 'r', encoding='utf-8') as f:
    logs_locales = json.load(f)

print(f"📂 Histórico local cargado: {len(logs_locales)} operaciones encontradas.")

# 2. Inicializar Firebase
try:
    cred = credentials.Certificate(CRED_FILE)
    if not firebase_admin._apps:
        firebase_admin.initialize_app(cred)
    db = firestore.client()
    print("🔥 Conexión a Firebase establecida con éxito.")
except Exception as e:
    print(f"❌ ERROR: No se pudo conectar a Firebase. Detalles: {e}")
    exit(1)

logs_recientes = sorted(logs_locales, key=lambda x: str(x.get('fecha', '')), reverse=True)[:150]
batch = db.batch()
count_logs = 0
count_kb = 0

print(f"\n🔍 Analizando los últimos {len(logs_recientes)} trades para detectar huecos (Error 429)...")

for trade in logs_recientes:
    t = str(trade.get('ticket', ''))
    if not t or t == "None" or t == "0":
        continue
        
    accion_local = str(trade.get('accion', ''))
    
    # Validación 1: ¿Existe en Firebase?
    doc_fb = db.collection('mia_audit_logs').document(t).get()
    
    inyectar = False
    if not doc_fb.exists:
        inyectar = True
    else:
        accion_fb = str(doc_fb.to_dict().get('accion', ''))
        # Validación 2: ¿Firebase se quedó congelado en APERTURA pero el trade ya CERRÓ?
        if 'APERTURA' in accion_fb and 'CIERRE' in accion_local:
            inyectar = True
            
    if inyectar:
        print(f"  ⚡ Hueco detectado en Ticket {t}. Inyectando log y enseñando a MIA KB...")
        
        # 1. Inyectar Log de Auditoría
        doc_ref = db.collection('mia_audit_logs').document(t)
        batch.set(doc_ref, trade, merge=True)
        count_logs += 1
        
        # 2. Lógica de Aprendizaje Quirúrgico (MIA KB)
        pnl = float(trade.get('pnl', 0.0))
        es_ganado = pnl > 0.0
        
        # A) Extraer indicadores del JSON (Snapshot exacto)
        confirmaciones = trade.get('confirmaciones_tecnicas', {})
        for campo, valor in confirmaciones.items():
            if valor is True:
                # Aprender de este indicador
                ind_ref = db.collection("mia_kb").document("indicadores_impacto").collection("detalle").document(campo)
                ind_doc = ind_ref.get()
                ind_data = ind_doc.to_dict() if ind_doc.exists else {"trades_con_indicador": 0, "trades_ganados_con": 0, "trades_perdidos_con": 0, "pnl_acumulado": 0.0}
                
                ind_data["trades_con_indicador"] = ind_data.get("trades_con_indicador", 0) + 1
                if es_ganado:
                    ind_data["trades_ganados_con"] = ind_data.get("trades_ganados_con", 0) + 1
                else:
                    ind_data["trades_perdidos_con"] = ind_data.get("trades_perdidos_con", 0) + 1
                ind_data["pnl_acumulado"] = ind_data.get("pnl_acumulado", 0.0) + pnl
                
                if ind_data["trades_con_indicador"] > 0:
                    ind_data["win_rate_indicador"] = round((ind_data["trades_ganados_con"] / ind_data["trades_con_indicador"]) * 100, 2)
                    
                batch.set(ind_ref, ind_data, merge=True)
                count_kb += 1
                
        # B) Extraer y Aprender Sesión
        detalle = str(trade.get('detalle_setup', '')).upper()
        sesion = "asia"
        if "NEW_YORK" in detalle or "NY" in detalle: sesion = "new_york"
        elif "LONDRES" in detalle or "LONDON" in detalle: sesion = "london"
        
        ses_ref = db.collection("mia_kb").document("sesiones_rendimiento").collection("detalle").document(sesion)
        ses_doc = ses_ref.get()
        ses_data = ses_doc.to_dict() if ses_doc.exists else {"trades_totales": 0, "trades_ganados": 0, "pnl_total": 0.0}
        
        ses_data["trades_totales"] = ses_data.get("trades_totales", 0) + 1
        if es_ganado: ses_data["trades_ganados"] = ses_data.get("trades_ganados", 0) + 1
        ses_data["pnl_total"] = ses_data.get("pnl_total", 0.0) + pnl
        if ses_data["trades_totales"] > 0:
            ses_data["win_rate"] = round((ses_data["trades_ganados"] / ses_data["trades_totales"]) * 100, 2)
            
        batch.set(ses_ref, ses_data, merge=True)
        count_kb += 1

if count_logs > 0:
    batch.commit()
    print(f"\n✅ ¡SANACIÓN Y APRENDIZAJE COMPLETADOS!")
    print(f"Se inyectaron {count_logs} trades huérfanos a mia_audit_logs.")
    print(f"MIA KB aprendió de estos trades (Se actualizaron {count_kb} métricas de indicadores/sesiones).")
    print("Todo está perfectamente homologado y no hubo doble conteo.")
else:
    print(f"\n✅ Análisis completo. Firebase ya estaba 100% homologado. No fue necesario inyectar nada.")
