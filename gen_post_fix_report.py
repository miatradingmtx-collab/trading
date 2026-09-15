import firebase_admin
from firebase_admin import credentials, firestore
import json

if not firebase_admin._apps:
    cred = credentials.Certificate('serviceAccountKey.json')
    firebase_admin.initialize_app(cred)

db = firestore.client()

def run_report():
    print("Obteniendo pesos de ML...")
    weights_ref = db.collection('system_memory').document('mia_collective').get()
    weights = weights_ref.to_dict() if weights_ref.exists else {}

    print("Analizando trades desde el domingo (2026-09-06)...")
    # Para ahorrar cuota (429), usamos un where
    logs = db.collection('mia_audit_logs').where('fecha', '>=', '2026-09-06').stream()
    
    tickets = {}
    for l in logs:
        data = l.to_dict()
        ticket = str(data.get("ticket", ""))
        if not ticket or ticket.startswith("EVAL_"): continue
        
        acc = data.get("accion", "")
        pnl = float(data.get("pnl", 0.0))
        fecha = data.get("fecha", "")
        
        if acc in ["CIERRE_TOTAL", "CIERRE_PARCIAL", "CIERRE_PARCIAL_80", "PROTECCION_BE", "TRAILING_STOP"]:
            if ticket not in tickets:
                tickets[ticket] = {
                    "pnl": 0.0, 
                    "activo": data.get("activo"), 
                    "fecha": fecha, 
                    "estrategia": data.get("detalle_setup", data.get("estrategia", "Desconocida")),
                    "sesion": data.get("sesion_killzone", "N/A"),
                    "parciales": 0,
                    "trailing": False
                }
            tickets[ticket]["pnl"] += pnl
            if acc == "CIERRE_TOTAL":
                tickets[ticket]["fecha"] = fecha
            if acc in ["CIERRE_PARCIAL", "CIERRE_PARCIAL_80"]:
                tickets[ticket]["parciales"] += 1
            if acc == "TRAILING_STOP":
                tickets[ticket]["trailing"] = True

    ganadoras = []
    perdedoras = []
    regla_3 = []
    total_pnl = 0.0

    for t, info in tickets.items():
        total_pnl += info["pnl"]
        
        # Regla de 3
        hit_regla = info["parciales"] >= 2 or info["trailing"]
        if hit_regla:
            regla_3.append(info)
            
        if info["pnl"] > 0:
            ganadoras.append((t, info))
        elif info["pnl"] < 0:
            perdedoras.append((t, info))

    ganadoras.sort(key=lambda x: x[1]["pnl"], reverse=True)
    perdedoras.sort(key=lambda x: x[1]["pnl"])
    
    # Escribir reporte
    with open('reporte_post_fix.txt', 'w', encoding='utf-8') as f:
        f.write(f"PNL NETO DESDE EL DOMINGO: ${total_pnl:.2f}\\n")
        f.write(f"Total Operaciones Cerradas: {len(tickets)}\\n")
        f.write(f"Ganadoras: {len(ganadoras)} | Perdedoras: {len(perdedoras)}\\n\\n")
        
        f.write("--- REGLA DE 3 CUMPLIDA (Escalamiento Perfecto) ---\\n")
        for r in regla_3:
            f.write(f"Activo: {r['activo']} | PnL: ${r['pnl']:.2f} | Estrategia: {r['estrategia']}\\n")
            
        f.write("\\n--- RANKING POSITIVAS (Top 5) ---\\n")
        for t, info in ganadoras[:5]:
            f.write(f"{info['activo']} | ${info['pnl']:.2f} | Sesion: {info['sesion']} | Estrategia: {info['estrategia']}\\n")
            
        f.write("\\n--- RANKING NEGATIVAS (Top 5) ---\\n")
        for t, info in perdedoras[:5]:
            f.write(f"{info['activo']} | ${info['pnl']:.2f} | Sesion: {info['sesion']} | Estrategia: {info['estrategia']}\\n")
            
        f.write("\\n--- PESOS MACHINE LEARNING ---\\n")
        f.write(json.dumps(weights.get('dynamic_weights', weights), indent=2))

    print("Reporte generado en reporte_post_fix.txt")

if __name__ == '__main__':
    run_report()
