import firebase_admin
from firebase_admin import credentials, firestore
from mia_post_mortem_agent import MiaQuantSupervisor
import datetime
import time

def run_batch_analysis():
    print("Iniciando análisis Batch Quant desde el Domingo...")
    
    if not firebase_admin._apps:
        cred = credentials.Certificate('serviceAccountKey.json')
        firebase_admin.initialize_app(cred)
    db = firestore.client()

    # Fecha del Domingo (2026-10-04)
    docs = db.collection('mia_audit_logs').where('fecha', '>=', '2026-10-04').stream()
    
    trades = []
    for doc in docs:
        data = doc.to_dict()
        # Filtrar solo acciones de cierre o toques de TP/SL/BE
        if data.get('accion') in ['CIERRE_TOTAL', 'CERRAR_TP', 'CIERRE_PARCIAL', 'TRAILING_STOP', 'PROTECCION_BE']:
            # Formatear el diccionario para que _generate_and_register_case lo entienda
            trade = {
                'ticket': str(data.get('ticket', 'DESC')),
                'symbol': data.get('activo', 'UNKNOWN'),
                'profit': data.get('pnl', 0.0),
                'type': data.get('accion'),
                'motivo': data.get('motivo', ''),
                'score': data.get('score', 0)
            }
            trades.append(trade)
            
    print(f"Total de trades encontrados desde el domingo: {len(trades)}")
    
    agent = MiaQuantSupervisor()
    
    for t in trades:
        print(f"Procesando trade {t['ticket']} ({t['symbol']}) - PNL: {t['profit']} ...")
        agent._generate_and_register_case(t)
        # Pausa para no detonar Rate Limits de Gemini
        time.sleep(3)
        
    print("Análisis Batch completado.")

if __name__ == "__main__":
    run_batch_analysis()
