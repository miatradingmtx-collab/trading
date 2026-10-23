def tool(name=None):
    def decorator(func):
        func.tool_name = name or func.__name__
        func.func = func
        return func
    if callable(name):
        f = name
        name = f.__name__
        return decorator(f)
    return decorator

import firebase_admin
from firebase_admin import firestore
import datetime

@tool("Ejecutar Trade (Gatillo RUNE)")
def trade_execution_tool(activo: str, accion: str, lotaje: float, razon: str) -> str:
    """
    HERRAMIENTA LETAL: Úsala SOLO cuando RUNE apruebe un trade.
    Envía la orden de ejecución directamente a Firebase para que el servidor de MetaAPI dispare la compra/venta real.
    activo: e.g. 'US30' o 'XAUUSD'
    accion: 'COMPRA' o 'VENTA'
    lotaje: Tamaño de la posición (e.g. 0.01)
    razon: Por qué RUNE autoriza el trade.
    """
    try:
        db = firestore.client()
        # Normalizar activo
        activo = activo.replace('/', '').replace('.cash', '').upper()
        
        # Escribir en la matriz para que mt5_executor_cloud lo intercepte
        payload = {
            "rune_signal": {
                "accion": accion,
                "lotaje": lotaje,
                "razon": razon,
                "timestamp": datetime.datetime.now().isoformat(),
                "ejecutado": False
            }
        }
        db.collection("trading_matrix").document(activo).update(payload)
        return f"ÉXITO: Señal de {accion} para {activo} (Lote: {lotaje}) enviada a Firebase. MetaAPI la ejecutará en breve."
    except Exception as e:
        return f"ERROR ejecutando trade en Firebase: {e}"
