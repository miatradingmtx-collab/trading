"""
=============================================================================
MÓDULO DE BIFURCACIÓN Y EVALUACIÓN A/B EN TIEMPO REAL · MIA TRADING CORE
=============================================================================
Misión: Gestionar el doble muestreo paralelo desde el trade 710 (baseline)
hasta el cierre de semana (~750 trades) sin contaminar los tensores de TensorFlow:

1. MUESTRA CHAMPION (Control - Sin Enjambres):
   Continúa registrándose en el flujo normal (mia_audit_logs, mia_ml_history).
   
2. MUESTRA CHALLENGER (Prueba - Con Enjambres 7 Herds + TensorFlow + ATLAS):
   Se alimenta de los 710 trades aprendidos, mia_kb, Regla de 3 y CBR para
   determinar puntos de entrada, SL, TP y vetos.
   Se registra en paralelo en 'mia_herds_live_trials' y 'cache_herds_ab_evaluation'
   con tag 'cuarentena_tf: True' para evitar contaminar futuros reentrenamientos
   neuronales hasta la validación humana HITL.
=============================================================================
"""

import os
import json
import time
import datetime
import requests

UPSTASH_URL = os.getenv("UPSTASH_REDIS_REST_URL", "https://firm-koi-93555.upstash.io")
UPSTASH_TOKEN = os.getenv("UPSTASH_REDIS_REST_TOKEN", "gQAAAAAAAW1zAAIgcDFmZGI5MGViNWY4Mjc0MGE1Yjg3NDZiOTdiN2MyMjg5Yg")
HEADERS = {"Authorization": f"Bearer {UPSTASH_TOKEN}"}

BASELINE_TRADE_OFFSET = 710

def _get_db():
    try:
        import firebase_admin
        from firebase_admin import firestore
        if firebase_admin._apps:
            return firestore.client()
    except Exception:
        pass
    return None

def get_swarm_latest_verdict():
    """Lee el debate más reciente de los 7 Herds desde Upstash Redis"""
    try:
        r = requests.get(f"{UPSTASH_URL}/get/cache_herd_debate_latest", headers=HEADERS, timeout=1.5)
        if r.status_code == 200 and r.json().get("result"):
            raw = r.json().get("result")
            data = json.loads(raw) if isinstance(raw, str) else (raw or {})
            debate = data.get("debate", {})
            estado = debate.get("estado", "APROBADO")
            return {
                "estado": estado,
                "aprobado": "VETADO" not in estado.upper() and "VETA" not in estado.upper(),
                "debate": debate,
                "timestamp": data.get("timestamp")
            }
    except Exception as e:
        print(f"| SWARM VERDICT WARN | Error leyendo cache_herd_debate_latest: {e}")
    return {"estado": "APROBADO", "aprobado": True, "debate": {}, "timestamp": None}

def get_ab_state():
    """Lee el estado acumulado de la evaluación A/B desde Upstash Redis"""
    try:
        r = requests.get(f"{UPSTASH_URL}/get/cache_herds_ab_evaluation", headers=HEADERS, timeout=1.5)
        if r.status_code == 200 and r.json().get("result"):
            raw = r.json().get("result")
            return json.loads(raw) if isinstance(raw, str) else (raw or {})
    except Exception:
        pass
        
    # Estado inicial si no existe
    return {
        "baseline_trade_offset": BASELINE_TRADE_OFFSET,
        "champion_control": {
            "total_trades": 0,
            "wins": 0,
            "losses": 0,
            "breakevens": 0,
            "win_rate": 0.0,
            "pnl_acumulado": 0.0,
            "max_drawdown": 0.0
        },
        "challenger_herds": {
            "total_trades": 0,
            "trades_ejecutados": 0,
            "trades_vetados": 0,
            "wins": 0,
            "losses": 0,
            "breakevens": 0,
            "win_rate": 0.0,
            "pnl_acumulado": 0.0,
            "perdidas_evitadas_por_veto": 0.0,
            "costo_oportunidad_vetos": 0.0,
            "max_drawdown": 0.0
        },
        "trials": [],
        "ultima_actualizacion": datetime.datetime.now(datetime.timezone.utc).isoformat()
    }

def save_ab_state(state):
    """Persiste el estado A/B en Upstash Redis y Firebase"""
    try:
        state["ultima_actualizacion"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        payload_str = json.dumps(state, default=str)
        requests.post(f"{UPSTASH_URL}/set/cache_herds_ab_evaluation", headers=HEADERS, data=payload_str, timeout=3)
    except Exception as e:
        print(f"| AB EVAL WARN | Error guardando cache_herds_ab_evaluation en Upstash: {e}")

    db = _get_db()
    if db:
        try:
            db.collection("mia_herds_history").document("evaluacion_ab_semanal").set(state, merge=True)
        except Exception as e:
            print(f"| AB EVAL WARN | Error guardando evaluacion_ab_semanal en Firestore: {e}")

def record_trade_setup_ab(ticket, activo, accion, precio, sl, tp, score, juez_authorized=True, amd_context=None):
    """
    Registra el punto de entrada bifurcado para el trade en evaluación.
    Determina si el Enjambre (7 Herds + TF + ATLAS) aprueba o veta.
    """
    swarm_info = get_swarm_latest_verdict()
    ticket_str = str(ticket)
    now_utc = datetime.datetime.now(datetime.timezone.utc).isoformat()
    
    # Determinar sesion
    hora_utc = datetime.datetime.now(datetime.timezone.utc).hour
    sesion = "asia"
    if 7 <= hora_utc < 12: sesion = "london"
    elif 12 <= hora_utc < 19: sesion = "new_york"

    trial_entry = {
        "ticket": ticket_str,
        "activo": activo,
        "accion": accion,
        "precio": precio,
        "sl": sl,
        "tp": tp,
        "score_juez": score,
        "juez_authorized": juez_authorized,
        "sesion": sesion,
        "swarm_estado": swarm_info["estado"],
        "swarm_aprobado": swarm_info["aprobado"],
        "swarm_debate_resumen": {
            "tidal": swarm_info["debate"].get("herd_1_tidal", "N/A"),
            "noro": swarm_info["debate"].get("herd_2_noro", "N/A"),
            "zephr": swarm_info["debate"].get("herd_3_zephr", "N/A"),
            "lumen": swarm_info["debate"].get("herd_4_lumen", "N/A"),
            "rune": swarm_info["debate"].get("herd_5_rune", "N/A"),
            "tensorflow": swarm_info["debate"].get("herd_6_tensorflow", "N/A"),
            "atlas": swarm_info["debate"].get("herd_7_atlas", "N/A"),
        },
        "amd_context": amd_context or {},
        "bifurcacion": "challenger_herds_7",
        "baseline_trade_offset": BASELINE_TRADE_OFFSET,
        "cuarentena_tf": True,  # Filtro estricto anti-contaminación para la red neuronal
        "estado_resultado": "PENDIENTE",
        "pnl": 0.0,
        "timestamp": now_utc
    }

    # Guardar en Firestore colección independiente 'mia_herds_live_trials'
    db = _get_db()
    if db:
        try:
            db.collection("mia_herds_live_trials").document(ticket_str).set(trial_entry, merge=True)
            print(f"| AB TRIAL | Setup {ticket_str} ({activo}) archivado en mia_herds_live_trials [Cuarentena TF: True]")
        except Exception as e:
            print(f"| AB TRIAL ERROR | No se pudo guardar trial en Firestore: {e}")

    # Actualizar estado A/B en Upstash
    state = get_ab_state()
    # Agregar a trials evitando duplicados
    existing = [t for t in state.get("trials", []) if t.get("ticket") != ticket_str]
    existing.append(trial_entry)
    state["trials"] = existing[-50:]  # Mantener últimos 50 trials en hot cache
    save_ab_state(state)

    return trial_entry

def record_trade_close_ab(ticket, pnl, accion="CIERRE_TOTAL"):
    """
    Registra el cierre del trade y compara el impacto de la decisión:
    - Champion: Asume el resultado real del trade.
    - Challenger: Si fue aprobado asume el resultado. Si fue vetado, calcula si salvó capital.
    """
    ticket_str = str(ticket)
    pnl = float(pnl or 0.0)
    db = _get_db()
    
    # 1. Recuperar trial de Firestore o del estado en Redis
    trial_data = None
    if db:
        try:
            doc = db.collection("mia_herds_live_trials").document(ticket_str).get()
            if doc.exists:
                trial_data = doc.to_dict()
        except Exception:
            pass
            
    state = get_ab_state()
    if not trial_data:
        for t in state.get("trials", []):
            if str(t.get("ticket")) == ticket_str:
                trial_data = t
                break

    swarm_aprobado = trial_data.get("swarm_aprobado", True) if trial_data else True
    es_win = pnl > 0.0
    es_be = abs(pnl) < 0.1
    resultado_str = "WIN" if es_win else ("BE" if es_be else "LOSS")

    # 2. Actualizar Champion (Control)
    champ = state["champion_control"]
    champ["total_trades"] += 1
    champ["pnl_acumulado"] = round(champ["pnl_acumulado"] + pnl, 2)
    if es_win: champ["wins"] += 1
    elif es_be: champ["breakevens"] += 1
    else: champ["losses"] += 1
    if champ["total_trades"] > 0:
        champ["win_rate"] = round((champ["wins"] / champ["total_trades"]) * 100, 2)

    # 3. Actualizar Challenger (Herds 7 + TF + ATLAS)
    chal = state["challenger_herds"]
    chal["total_trades"] += 1

    if swarm_aprobado:
        chal["trades_ejecutados"] += 1
        chal["pnl_acumulado"] = round(chal["pnl_acumulado"] + pnl, 2)
        if es_win: chal["wins"] += 1
        elif es_be: chal["breakevens"] += 1
        else: chal["losses"] += 1
    else:
        chal["trades_vetados"] += 1
        if pnl < 0:
            # ¡VETO SALVADOR! El Enjambre evitó una pérdida
            chal["perdidas_evitadas_por_veto"] = round(chal["perdidas_evitadas_por_veto"] + abs(pnl), 2)
        elif pnl > 0:
            # Costo de oportunidad: vetó un trade que hubiera ganado
            chal["costo_oportunidad_vetos"] = round(chal["costo_oportunidad_vetos"] + pnl, 2)

    if chal["trades_ejecutados"] > 0:
        chal["win_rate"] = round((chal["wins"] / chal["trades_ejecutados"]) * 100, 2)

    # 4. Actualizar documento de Firestore
    if db:
        try:
            update_payload = {
                "estado_resultado": resultado_str,
                "pnl": pnl,
                "accion_cierre": accion,
                "veto_salvador": (not swarm_aprobado and pnl < 0),
                "perdida_evitada": abs(pnl) if (not swarm_aprobado and pnl < 0) else 0.0,
                "cerrado_en": datetime.datetime.now(datetime.timezone.utc).isoformat()
            }
            db.collection("mia_herds_live_trials").document(ticket_str).set(update_payload, merge=True)
        except Exception as e:
            print(f"| AB TRIAL ERROR | No se pudo actualizar cierre en Firestore: {e}")

    # 5. Persistir estado consolidado
    save_ab_state(state)
    return state

def generate_ab_report():
    """Genera el reporte ejecutivo comparativo entre Champion y Challenger"""
    state = get_ab_state()
    champ = state.get("champion_control", {})
    chal = state.get("challenger_herds", {})
    
    delta_wr = round(chal.get("win_rate", 0.0) - champ.get("win_rate", 0.0), 2)
    delta_pnl = round(chal.get("pnl_acumulado", 0.0) - champ.get("pnl_acumulado", 0.0), 2)
    
    return {
        "status": "active_trial",
        "baseline_trade_offset": BASELINE_TRADE_OFFSET,
        "cuarentena_tf_activa": True,
        "champion_control": champ,
        "challenger_herds": chal,
        "comparativa": {
            "delta_win_rate": f"{delta_wr:+.2f}%",
            "delta_pnl_usd": f"${delta_pnl:+.2f}",
            "capital_salvado_por_vetos": f"${chal.get('perdidas_evitadas_por_veto', 0.0):.2f}",
            "total_vetos_emitidos": chal.get("trades_vetados", 0)
        },
        "ultima_actualizacion": state.get("ultima_actualizacion")
    }
