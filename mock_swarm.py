import requests
import time

eventos = [
    {"agent": "Inbox", "action": "thinking", "data": "Consultando Firebase por nuevos trades de hoy..."},
    {"agent": "Inbox", "action": "success", "data": "3 trades encontrados. Enviando a DAILY."},
    {"agent": "Daily", "action": "thinking", "data": "Analizando temporalidades mayores y Killzones..."},
    {"agent": "Daily", "action": "success", "data": "Sesión NY fue la más rentable hoy."},
    {"agent": "MOC", "action": "thinking", "data": "Aplicando Regla de 3 de Mia a los datos estadísticos..."},
    {"agent": "MOC", "action": "success", "data": "Regla validada. SMC_OB tiene 75% WR."},
    {"agent": "Tags", "action": "thinking", "data": "Indexando metadatos para Obsidian..."},
    {"agent": "Tags", "action": "success", "data": "Tags generados: #smc #win #ny_session"},
    {"agent": "Master", "action": "thinking", "data": "Leyendo DOCUMENTACION_MIA_CORE.md y validando reglas de riesgo..."},
    {"agent": "Master", "action": "success", "data": "Todo en orden. Aprobando reporte final para la Bóveda."},
    {"agent": "Vault", "action": "writing", "data": "Guardando archivo .md en el disco duro..."},
    {"agent": "Vault", "action": "success", "data": "Archivo guardado exitosamente. Ciclo completado."}
]

print("Iniciando simulador de Enjambre (Enviando telemetría al UI 3D)...")

for evento in eventos:
    print(f"Enviando: {evento['agent']} -> {evento['data']}")
    try:
        requests.post("http://localhost:8000/emit", json=evento)
    except Exception as e:
        print(f"Error enviando evento: {e}")
    time.sleep(3) # Espera 3 segundos entre cada acción para que veas la animación
    
print("Simulación terminada.")
