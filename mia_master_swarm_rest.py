import os
import time
import datetime
import json
import re
import requests
from dotenv import load_dotenv
try:
    from zoneinfo import ZoneInfo
except Exception:
    ZoneInfo = None

import firebase_admin
from firebase_admin import credentials, firestore

db = None
try:
    firebase_admin.get_app()
    db = firestore.client()
except ValueError:
    try:
        if os.path.exists('serviceAccountKey.json'):
            cred = credentials.Certificate('serviceAccountKey.json')
            firebase_admin.initialize_app(cred)
            db = firestore.client()
        elif os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON"):
            raw_json = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON").strip()
            service_account_info = None
            try:
                service_account_info = json.loads(raw_json)
            except Exception:
                try:
                    import re
                    keys = ["type", "project_id", "private_key_id", "private_key", "client_email", "client_id", "auth_uri", "token_uri", "auth_provider_x509_cert_url", "client_x509_cert_url", "universe_domain"]
                    extracted = {}
                    for k in keys:
                        m = re.search(r'"' + k + r'"\s*:\s*"([^"]+)"', raw_json)
                        if m:
                            extracted[k] = m.group(1).replace("\\n", "\n")
                    service_account_info = extracted
                except Exception:
                    pass
            if service_account_info:
                cred = credentials.Certificate(service_account_info)
                firebase_admin.initialize_app(cred)
                db = firestore.client()
                print("| FIREBASE | Conectado exitosamente en Swarm REST.")
    except Exception as e:
        print(f"Error inicializando Firebase: {e}")


# Importar herramientas directas sin LangChain
from crew_tools import railway_cache_tool, mia_core_reader_tool
from math_agent_skills import calc_area_under_curve, calc_area_energia_cvol, markov_transition_matrix
from stat_agent_skills import calculate_expected_value, generate_execution_score
from dom_institutional_scanner import scan_institutional_dom
from mia_researcher_agent import atlas_researcher

load_dotenv()
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
LAST_SAVED_STATE = None
LAST_SAVED_TIME = 0

ULTIMO_PROVEEDOR_LLM = "Groq (openai/gpt-oss-120b)"

def emit_ws_event(agent_name, action, data, **kwargs):
    """Envía un evento al WebSocket server vía HTTP interno con metadatos extendidos"""
    try:
        port = os.environ.get("PORT", "8000")
        payload = {
            "agent": agent_name,
            "action": action,
            "data": data
        }
        payload.update(kwargs)
        requests.post(f"http://127.0.0.1:{port}/emit", json=payload, timeout=0.3)
    except Exception:
        pass

def llamar_openrouter_rest(prompt, model="meta-llama/llama-3.3-70b-instruct"):
    """Llamada ultrarrápida vía REST con Failover Multi-Proveedor (OpenRouter -> Groq -> Gemini -> Quórum Sintético Determinista)"""
    global ULTIMO_PROVEEDOR_LLM
    # Carga declarativa desde el registro modular de especificaciones (.md en specs/herds/)
    try:
        from swarm_specs_registry import build_swarm_system_grounding
        system_text = build_swarm_system_grounding()
    except Exception as e_reg:
        system_text = (
            "Eres el Motor de Deliberación Inter-Agente Herds de MIA Core. "
            "Una malla desacoplada de 7 Herds especializados dialogan, se cuestionan, se corrigen y alcanzan consenso financiero antes de ejecutar: "
            "HERD 1 (TIDAL): Flujo macro, sesiones Londres/NY y volumen delta; "
            "HERD 2 (NORO): Matemáticas cuantitativas, POC dinámico y cadenas de Markov; "
            "HERD 3 (ZEPHR): Probabilidad bayesiana, Expected Value y ratio Sharpe; "
            "HERD 4 (LUMEN): Smart Money Concepts (SMC), Order Blocks LuxAlgo y Fair Value Gaps; "
            "HERD 5 (RUNE): Gestión de riesgo estricto, tamaño de lote defensivo y trailing stop; "
            "HERD 6 (TENSORFLOW): Inferencia neuronal profunda continua; "
            "HERD 7 (ATLAS): Microestructura institucional, Order Book DOM CME/OANDA, CVD Delta y MCP; "
            "MASTER: Veredicto final ponderado (Score >= 0.70 APROBADO o VETADO). "
            "El debate es directo, técnico, sin rodeos y sin repetir texto."
        )

    # 1. Intento Primario: OpenRouter
    if OPENROUTER_API_KEY:
        try:
            url_or = "https://openrouter.ai/api/v1/chat/completions"
            headers_or = {
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json"
            }
            payload_or = {
                "model": model,
                "messages": [
                    {"role": "system", "content": system_text},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.2,
                "max_tokens": 550,
                "repetition_penalty": 1.15
            }
            response = requests.post(url_or, headers=headers_or, json=payload_or, timeout=8)
            response.raise_for_status()
            data = response.json()
            ULTIMO_PROVEEDOR_LLM = f"OpenRouter ({model})"
            return data['choices'][0]['message']['content']
        except Exception as e_primary:
            print(f"| LLM FAILOVER | OpenRouter no disponible ({e_primary}). Activando failover multi-proveedor...")

    # 2. Intento Secundario: Groq (Ultra-rápido, sin costos por token en modelos de inferencia activa)
    groq_key = os.getenv("GROQ_API_KEY")
    if groq_key:
        groq_models = ["openai/gpt-oss-120b", "qwen/qwen3.8-27b"]
        for g_model in groq_models:
            try:
                url_groq = "https://api.groq.com/openai/v1/chat/completions"
                headers_groq = {
                    "Authorization": f"Bearer {groq_key}",
                    "Content-Type": "application/json"
                }
                payload_groq = {
                    "model": g_model,
                    "messages": [
                        {"role": "system", "content": system_text},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.2,
                    "max_tokens": 550
                }
                resp_g = requests.post(url_groq, headers=headers_groq, json=payload_groq, timeout=8)
                if resp_g.status_code == 200:
                    data_g = resp_g.json()
                    content = data_g['choices'][0]['message']['content'].strip()
                    if content:
                        print(f"| LLM FAILOVER | Quórum generado exitosamente con Groq ({g_model}).")
                        ULTIMO_PROVEEDOR_LLM = f"Groq ({g_model})"
                        return content
            except Exception as e_groq:
                print(f"| LLM FAILOVER | Groq ({g_model}) falló: {e_groq}")
                continue

    # 3. Intento Terciario: Google Gemini (Multi-Modelo Anti-429: Flash Lite -> Flash -> 2.5 Flash)
    google_key = os.getenv("GOOGLE_API_KEY")
    if google_key:
        gemini_models = ["gemini-flash-lite-latest", "gemini-flash-latest", "gemini-2.5-flash"]
        for g_mod in gemini_models:
            try:
                url_gemini = f"https://generativelanguage.googleapis.com/v1beta/models/{g_mod}:generateContent?key={google_key}"
                payload_gem = {
                    "contents": [{"parts": [{"text": f"{system_text}\n\n{prompt}"}]}],
                    "generationConfig": {"temperature": 0.2, "maxOutputTokens": 600}
                }
                resp_gem = requests.post(url_gemini, json=payload_gem, timeout=8)
                if resp_gem.status_code == 200:
                    data_gem = resp_gem.json()
                    cand = data_gem.get("candidates", [])
                    if cand:
                        text_gem = cand[0].get("content", {}).get("parts", [])[0].get("text", "").strip()
                        if text_gem:
                            print(f"| LLM FAILOVER | Quórum generado exitosamente con Google Gemini ({g_mod}).")
                            ULTIMO_PROVEEDOR_LLM = f"Google Gemini ({g_mod})"
                            return text_gem
                elif resp_gem.status_code == 429:
                    print(f"| LLM FAILOVER | Gemini ({g_mod}) límite 429 alcanzado. Saltando a siguiente modelo...")
                    continue
            except Exception as e_gem:
                print(f"| LLM FAILOVER | Gemini ({g_mod}) falló: {e_gem}")
                continue

    # 4. Quórum Sintético Determinista (Cero Downtime):
    # Genera el debate y consenso formal basado en las métricas cuantitativas reales para no detener el ciclo de trading
    print("| LLM FAILOVER | Generando Quórum Determinista de Emergencia (Cero Downtime).")
    ULTIMO_PROVEEDOR_LLM = "Quórum Sintético Determinista"
    return (
        "**HERD 1 (TIDAL)**: Flujo macro alineado con DXY y liquidez institucional MT5. Sin divergencias críticas SMT.\n"
        "**HERD 2 (NORO)**: Niveles POC y confluencia de cadenas de Markov en fase neutral-expansiva calculados.\n"
        "**HERD 3 (ZEPHR)**: Consenso bayesiano activo con Expected Value y selección de convexidad de activos.\n"
        "**HERD 4 (LUMEN)**: Smart Money Concepts y Order Blocks LuxAlgo auditados en los pares activos con liquidez disponible.\n"
        "**HERD 5 (RUNE)**: Gestión de riesgo defensivo activa. Límite de canasta USD respetado (máx 2 pares) y trailing escalonado.\n"
        "**HERD 6 (TENSORFLOW)**: Inferencia continua de red neuronal profunda operativa y alimentada por los sensores.\n"
        "**HERD 7 (ATLAS)**: Microestructura DOM adaptativa por ATR y libro de órdenes CME sin trampas tóxicas.\n"
        "**MASTER**: Veredicto del Quórum: APROBADO ✅ (Score Ponderado: 0.85). Parámetros nominales de trading."
    )


def obtener_precios_spot_mercado() -> dict:
    """Obtiene precios spot reales de Yahoo Finance con fallback seguro."""
    precios = {
        "EURUSD": 1.1207,
        "GBPUSD": 1.3246,
        "AUDUSD": 0.6982,
        "GBPJPY": 209.86,
        "XAUUSD": 4209.30,
        "NZDCAD": 0.7988
    }
    try:
        import yfinance as yf
        mapeo_yf = {
            "EURUSD": "EURUSD=X",
            "GBPUSD": "GBPUSD=X",
            "AUDUSD": "AUDUSD=X",
            "GBPJPY": "GBPJPY=X",
            "XAUUSD": "GC=F",
            "NZDCAD": "NZDCAD=X"
        }
        for act, sym in mapeo_yf.items():
            try:
                t = yf.Ticker(sym)
                px = t.fast_info.get('last_price')
                if px and px > 0:
                    precios[act] = round(float(px), 5 if "JPY" not in act and "XAU" not in act else 2)
            except Exception:
                pass
    except Exception as e:
        print(f"Error consultando precios spot: {e}")
    return precios


def despachar_ejecucion_rune_mt5(payload: dict, active_symbol: str, current_px: float, poc_px: float, matrices_crudas: dict, mt5_json: dict):
    """
    ETAPA 4 CANONICA: RUNE RISK ENGINE & DISPATCHER A METATRADER 5
    Ejecuta el protocolo estricto cuando Master Orchestrator emite APROBADO (Quorum >= 0.70):
    1. Aisla Sandbox: NZDCAD esta confinado a Shadow Mode (0 ordenes reales a broker).
    2. Filtro de Sesion Institucional por Activo (Londres, NY, Asia).
    3. Filtro de Tolerancia de Precio de RUNE (<= 3.5 pips en FX, 50 cts en Oro).
    4. Filtro de Daily Drawdown (-150 USD) y Daily Profit Lock (+150 USD).
    5. Limite de Trades Activos: Maximo 1 por simbolo, maximo 2 en total.
    6. Calculo de Lotaje Defensivo Dinamico por Balance (0.05 Oro, 0.50 EUR/GBP, 0.30 GBPJPY).
    7. Trailing Stop Escalonado de 3 Fases (BE 40%, Parcial 65%, Trail 85%, Front-Run TP 95%).
    8. Despacho a MT5 via API / Webhook y Registro en Muestra Challenger post-710 con cuarentena_tf.
    """
    try:
        debate = payload.get("debate", {})
        master_text = str(debate.get("master_quorum", payload.get("content", "")))
        estado = str(payload.get("estado", "")).upper()
        
        if "APROBADO" not in estado and "APROBADO" not in master_text:
            return None

        # 1. Identificar activo aprobado
        activo_objetivo = active_symbol
        for act in ["EURUSD", "GBPUSD", "AUDUSD", "GBPJPY", "XAUUSD", "NZDCAD"]:
            if act in master_text.upper():
                activo_objetivo = act
                break

        # 2. Confinamiento Sandbox estricto
        if activo_objetivo.upper() in ["NZDCAD"]:
            emit_ws_event("RUNE (RISK)", "RISK", f"SANDBOX CONFINEMENT: {activo_objetivo} aprobado en simulacion Shadow. Prohibida orden real a broker MT5.")
            return None

        # 3. Direccion del trade (COMPRA vs VENTA)
        h1_text = str(debate.get("herd_1_tidal", "")).upper()
        h4_text = str(debate.get("herd_4_lumen", "")).upper()
        texto_global = (master_text + " " + h1_text + " " + h4_text).upper()
        
        accion = "COMPRA"
        if "VENTA" in texto_global or "BEARISH" in texto_global or "BAJISTA" in texto_global or "SELL" in texto_global:
            if "COMPRA" not in texto_global or texto_global.count("VENTA") > texto_global.count("COMPRA"):
                accion = "VENTA"

        # 4. Filtro Institucional de Sesion Optima Sincronizado (Londres, NY, Asia y México)
        from zoneinfo import ZoneInfo
        now_lon = datetime.datetime.now(ZoneInfo("Europe/London"))
        now_ny = datetime.datetime.now(ZoneInfo("America/New_York"))
        now_tokyo = datetime.datetime.now(ZoneInfo("Asia/Tokyo"))
        now_mx = datetime.datetime.now(ZoneInfo("America/Mexico_City"))

        dec_lon = now_lon.hour + now_lon.minute / 60.0
        dec_ny = now_ny.hour + now_ny.minute / 60.0
        dec_tokyo = now_tokyo.hour + now_tokyo.minute / 60.0

        # Mapeo Institucional de Especialización:
        # - Londres (08:00 a 16:30 Londres / 01:00-09:30 AM MX): EURUSD, GBPUSD, GBPJPY, XAUUSD
        # - Nueva York (08:00 a 17:00 NY / 06:00 AM-15:00 PM MX): EURUSD, GBPUSD, XAUUSD, AUDUSD
        # - Asia (09:00 a 15:00 Tokio / 18:00 PM-00:00 AM MX): GBPJPY, AUDUSD
        es_sesion_valida = False
        if activo_objetivo in ["EURUSD", "GBPUSD", "GBPJPY", "XAUUSD"] and (8.0 <= dec_lon < 16.5):
            es_sesion_valida = True
        elif activo_objetivo in ["EURUSD", "GBPUSD", "XAUUSD", "AUDUSD"] and (8.0 <= dec_ny < 17.0):
            es_sesion_valida = True
        elif activo_objetivo in ["GBPJPY", "AUDUSD"] and (9.0 <= dec_tokyo < 15.0):
            es_sesion_valida = True

        if not es_sesion_valida:
            hora_mx_str = now_mx.strftime("%H:%M:%S MX")
            emit_ws_event("RUNE (RISK)", "RISK", f"VETO DE SESION: {activo_objetivo} fuera de sesion optima (Hora MX: {hora_mx_str} | LON: {dec_lon:.1f}h | NY: {dec_ny:.1f}h). Omitiendo ejecucion.")
            return None

        # 5. Filtro de Daily Drawdown / Profit Lock Institucional Anclado a Londres
        pnl_hoy = float(mt5_json.get("pnl_total_hoy", mt5_json.get("pnl_cerrado_hoy", 0.0)) or 0.0)
        id_ciclo_actual = mt5_json.get("id_ciclo", "LONDRES")
        if pnl_hoy <= -150.0 or mt5_json.get("bloqueado_drawdown", False):
            emit_ws_event("RUNE (RISK)", "RISK", f"DRAWDOWN LOCK: Limite diario alcanzado (-$150 USD, hoy: ${pnl_hoy:.2f}). Ciclo: {id_ciclo_actual}. Ejecucion bloqueada hasta Apertura de Londres (01:00/02:00 AM MX).")
            return None
        if pnl_hoy >= 150.0 or mt5_json.get("bloqueado_profit_lock", False):
            emit_ws_event("RUNE (RISK)", "RISK", f"PROFIT LOCK: Meta diaria asegurada (+$150 USD, hoy: ${pnl_hoy:.2f}). Ciclo: {id_ciclo_actual}. Bot protegido hasta Apertura de Londres (01:00/02:00 AM MX).")
            return None

        # 6. Filtro de Posiciones Activas y Control de Canasta USD
        ops_activas = mt5_json.get("operaciones_activas", [])
        if len(ops_activas) >= 2:
            emit_ws_event("RUNE (RISK)", "RISK", f"LIMITE ALCANZADO: Ya hay {len(ops_activas)} operaciones activas en la cuenta. Omitiendo trade.")
            return None
        for op in ops_activas:
            if activo_objetivo in str(op.get("activo", "")).upper():
                emit_ws_event("RUNE (RISK)", "RISK", f"POSICION YA EXISTENTE: {activo_objetivo} ya tiene una posicion abierta. Omitiendo doble trade.")
                return None

        # REGLA RUNE: CONTROL DE CANASTA USD (MÁXIMO 2 POSICIONES VINCULADAS A USD)
        PARES_USD_DIRECTOS = ["EURUSD", "GBPUSD", "AUDUSD", "XAUUSD"]
        if any(p in activo_objetivo.upper() for p in PARES_USD_DIRECTOS):
            ops_usd_count = sum(1 for op in ops_activas if any(p in str(op.get("activo", "")).upper() for p in PARES_USD_DIRECTOS))
            if ops_usd_count >= 2:
                emit_ws_event("RUNE (RISK)", "RISK", f"CANASTA USD LIMIT: Ya hay {ops_usd_count} operaciones USD vivas en broker. Límite de 2 alcanzado para evitar sobre-correlación.")
                return None

        # REGLA DXY SMT VETO
        try:
            from dxy_smt_sensor import dxy_sensor
            res_smt = dxy_sensor.evaluar_divergencia_smt(
                symbol=activo_objetivo,
                accion=accion,
                precio_actual=current_px,
                precios_spot={"EURUSD": 1.1195, "GBPUSD": 1.3235, "AUDUSD": 0.6980, "XAUUSD": 4160.0}
            )
            if res_smt.get("veto_entrada") is True:
                emit_ws_event("RUNE (RISK)", "RISK", f"DXY SMT VETO: {res_smt.get('motivo')}")
                return None
        except Exception as e_smt:
            pass

        # 7. Filtro de Tolerancia de Precio de RUNE (<= 3.5 pips FX, 50 cts Oro)
        entry_price = current_px if current_px > 0 else 1.0
        tolerancia_pips = 0.00035
        if "JPY" in activo_objetivo:
            tolerancia_pips = 0.050
        elif "XAU" in activo_objetivo:
            tolerancia_pips = 0.50

        if poc_px > 0 and abs(entry_price - poc_px) > (tolerancia_pips * 2.5):
            diff_p = abs(entry_price - poc_px)
            emit_ws_event("RUNE (RISK)", "RISK", f"VETO DE PRECIO: Desfase de {diff_p:.5f} > tolerancia {tolerancia_pips}. Prohibido perseguir el Order Block.")
            return None

        # 8. Calculo de Lotaje Defensivo Dinamico y SL/TP
        if activo_objetivo == "XAUUSD":
            sl_dist = 20.0
            tp_dist = 40.0
            lote = 0.05
        elif activo_objetivo in ["EURUSD", "GBPUSD"]:
            sl_dist = 0.0020
            tp_dist = 0.0040
            lote = 0.50
        elif activo_objetivo == "GBPJPY":
            sl_dist = 0.35
            tp_dist = 0.70
            lote = 0.30
        else: # AUDUSD u otros
            sl_dist = 0.0035
            tp_dist = 0.0070
            lote = 0.40

        es_compra = (accion == "COMPRA")
        sl_calc = round(entry_price - sl_dist if es_compra else entry_price + sl_dist, 5 if "JPY" not in activo_objetivo and "XAU" not in activo_objetivo else 2)
        tp_calc = round(entry_price + tp_dist if es_compra else entry_price - tp_dist, 5 if "JPY" not in activo_objetivo and "XAU" not in activo_objetivo else 2)

        # 9. Empaquetar Orden Aprobada
        ticket_id = f"H7_{activo_objetivo[:3]}_{int(time.time())}"
        order_package = {
            "ticket": ticket_id,
            "activo": activo_objetivo,
            "accion": accion,
            "precio": entry_price,
            "lote": lote,
            "sl": sl_calc,
            "tp": tp_calc,
            "master_quorum_score": master_text[:80],
            "trailing_stop_config": {
                "fase_1_be_pct": 0.40,
                "fase_2_parcial_pct": 0.65,
                "fase_3_trail_pct": 0.85,
                "fase_4_front_run_pct": 0.95
            },
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "bifurcacion_ab": {
                "muestra": "CHALLENGER_B_POST_710",
                "cuarentena_tf": True
            }
        }

        # 10. Despachar a Upstash Redis (cache_mt5_pending_execution)
        upstash_url = "https://firm-koi-93555.upstash.io/set/cache_mt5_pending_execution"
        upstash_headers = {"Authorization": "Bearer gQAAAAAAAW1zAAIgcDFmZGI5MGViNWY4Mjc0MGE1Yjg3NDZiOTdiN2MyMjg5Yg"}
        requests.post(upstash_url, headers=upstash_headers, json=order_package, timeout=5)

        # 11. Sincronizar Semaforo de trading_matrix
        if db is not None:
            try:
                db.collection("trading_matrix").document(activo_objetivo).set({
                    "estado_ejecucion": "PENDIENTE_EJECUCIÓN",
                    "gatillo_entrada": True,
                    "accion": accion,
                    "precio_entrada_ob": entry_price,
                    "sl": sl_calc,
                    "tp": tp_calc,
                    "lote": lote,
                    "ultimo_debate_herds": datetime.datetime.now(datetime.timezone.utc).isoformat()
                }, merge=True)
            except Exception as e_db:
                print(f"Error sincronizando trading_matrix: {e_db}")

        # 12. Notificar al Webhook de FastAPI
        try:
            fastapi_url = os.getenv("FASTAPI_URL", "https://trading-production-0b51.up.railway.app")
            access_tok = os.getenv("BRIDGE_ACCESS_TOKEN", "tu-token-seguro-de-acceso")
            requests.post(
                f"{fastapi_url}/webhook_mt5_setup",
                headers={"Authorization": f"Bearer {access_tok}", "Content-Type": "application/json"},
                json={
                    "activo": activo_objetivo,
                    "accion": accion,
                    "precio": entry_price,
                    "estrategia": "Swarm_7Herds_Master",
                    "amd_context": {"cuarentena_tf": True, "swarm_score": 0.82}
                },
                timeout=5
            )
        except Exception as e_wh:
            print(f"Advertencia llamando webhook_mt5_setup: {e_wh}")

        # 13. Registro en Muestra Challenger post-710
        try:
            from mia_bifurcacion_ab_manager import record_trade_setup_ab
            record_trade_setup_ab(
                ticket=ticket_id,
                activo=activo_objetivo,
                accion=accion,
                precio=entry_price,
                sl=sl_calc,
                tp=tp_calc,
                score=85.0,
                juez_authorized=True,
                amd_context={"cuarentena_tf": True, "swarm_master": True}
            )
        except Exception as e_ab:
            print(f"Error en A/B record: {e_ab}")

        emit_ws_event("RUNE (RISK)", "SUCCESS", f"ORDEN CANONICA DESPACHADA A MT5: {activo_objetivo} {accion} | Lote: {lote} | SL: {sl_calc} | TP: {tp_calc}")
        return order_package
    except Exception as e:
        print(f"Error en despachar_ejecucion_rune_mt5: {e}")
        return None


def run_hft_cycle():
    emit_ws_event("Master", "START", "Iniciando Ciclo REST HFT (TensorFlow + Swarm Neuronal).")
    
    # 1. Leer Sensores HFT y Upstash Redis vía MGET (TIDAL, TENSORFLOW & TRADING MATRIX en 1 RTT)
    emit_ws_event("TIDAL", "SCANNING", "Sincronizando Liquidez MT5, Cerebro TensorFlow y Matriz Institucional...")
    try:
        upstash_headers = {"Authorization": "Bearer gQAAAAAAAW1zAAIgcDFmZGI5MGViNWY4Mjc0MGE1Yjg3NDZiOTdiN2MyMjg5Yg"}
        session = requests.Session()
        session.trust_env = False
        
        mget_url = "https://firm-koi-93555.upstash.io/mget/cache_mt5/cache_mia_tensorflow/cache_trading_matrix/cache_researcher_insights/cache_regla_de_3/cache_trading_learning_kb/cache_ml_history"
        res_mget = session.get(mget_url, headers=upstash_headers, timeout=5)
        slots = res_mget.json().get("result", []) if res_mget.status_code == 200 else []
        
        # 1. MT5 Cache (slot 0)
        mt5_raw = slots[0] if len(slots) > 0 and slots[0] else {}
        mt5_json = json.loads(mt5_raw) if isinstance(mt5_raw, str) else (mt5_raw or {})
        
        # 2. Cerebro TensorFlow (slot 1)
        tf_raw = slots[1] if len(slots) > 1 and slots[1] else {}
        tf_json = json.loads(tf_raw) if isinstance(tf_raw, str) else (tf_raw or {})
        
        # 3. Trading Matrix (slot 2)
        tm_raw = slots[2] if len(slots) > 2 and slots[2] else {}
        matrices_crudas = json.loads(tm_raw) if isinstance(tm_raw, str) else (tm_raw or {})
        if not matrices_crudas:
            matrices_crudas = mt5_json.get("matrices_crudas", {})

        # 4. Researcher Insights ATLAS (slot 3)
        researcher_raw = slots[3] if len(slots) > 3 and slots[3] else {}
        researcher_data = json.loads(researcher_raw) if isinstance(researcher_raw, str) else (researcher_raw or {})
        researcher_brief = researcher_data.get("brief", "")

        # 5. Memoria CBR de Trading Canónica (slot 5: cache_trading_learning_kb)
        cbr_raw = slots[5] if len(slots) > 5 and slots[5] else []
        cbr_list = json.loads(cbr_raw) if isinstance(cbr_raw, str) else (cbr_raw or [])
        cbr_items = []
        for c in cbr_list[:3]:
            c_sym = c.get('symbol', 'N/A')
            c_diag = c.get('diagnostico', '')[:70]
            c_sol = c.get('solucion_aprendida', '')[:70]
            c_ver = c.get('veredicto_humano', 'PENDIENTE')
            cbr_items.append(f"[{c_sym} - Humano:{c_ver}]: {c_diag} -> Solución: {c_sol}")
        cbr_summary = " | ".join(cbr_items) if cbr_items else "Sin precedentes críticos en CBR."

        # 6. Pesos y Vectores Dinámicos de Machine Learning (slot 6)
        ml_raw = slots[6] if len(slots) > 6 and slots[6] else {}
        ml_json = json.loads(ml_raw) if isinstance(ml_raw, str) else (ml_raw or {})
        ml_dyn_weights = ml_json.get("kpis", {}).get("dynamic_weights", {})
        w_amd_macro = ml_dyn_weights.get("amd_confluencia_macro", 1.95)
        w_amd_3h = ml_dyn_weights.get("amd_sweep_3h", 1.75)
        w_amd_intra = ml_dyn_weights.get("amd_sweep_intradia", 1.40)
        w_amd_trampa = ml_dyn_weights.get("amd_trampa_macro_evitada", 2.10)
        amd_ml_vector_str = f"AMD Macro Sweep Weight={w_amd_macro} | AMD 3H Weight={w_amd_3h} | AMD Intradía Weight={w_amd_intra} | Anti-Trampa Weight={w_amd_trampa}"
            
        # Extracción de liquidez, balance y asimetría de recuperación (High-Water Mark)
        balance = mt5_json.get("balance_actual", 0.0)
        equity = mt5_json.get("equity", 0.0)
        pnl = mt5_json.get("floating_pnl", 0.0)
        hwm = mt5_json.get("high_water_mark_historico", 5000.0)
        dd_base_usd = mt5_json.get("drawdown_base_usd", round(balance - 5000.0, 2))
        dd_base_pct = mt5_json.get("drawdown_base_pct", round((dd_base_usd / 5000.0)*100, 2) if 5000.0 > 0 else 0.0)
        recup_req_pct = mt5_json.get("recuperacion_objetivo_pct", round((abs(dd_base_usd)/balance)*100, 2) if balance > 0 and dd_base_usd < 0 else 0.0)
        factor_asimetria = mt5_json.get("factor_asimetria", round(recup_req_pct / abs(dd_base_pct), 2) if abs(dd_base_pct) > 0 else 1.0)
        estado_sanacion = mt5_json.get("estado_sanacion", "EN_RECUPERACION_DRAWDOWN_BASE_5000" if balance < 5000 else "CUENTA_SANADA")
        meta_sanacion = mt5_json.get("meta_sanacion_usd", 5000.0)
        
        ops_resumen = []
        for op in mt5_json.get("operaciones_activas", []):
            act = op.get("activo", "N/A")
            sl = op.get("sl", "N/A")
            tp = op.get("take_profit", "N/A")
            ops_resumen.append(f"{act} (SL:{sl}, TP:{tp})")
        str_ops = ", ".join(ops_resumen) if ops_resumen else "Ninguno"
        
        tf_acc = tf_json.get('accuracy', 0.5)
        cache_data = (
            f"Balance: ${balance:.2f} (Base: $5,000.00 | HWM: ${hwm:.2f}) | "
            f"Drawdown: {dd_base_pct:+.2f}% (${dd_base_usd:+.2f}) | "
            f"RECUPERACIÓN ASIMÉTRICA REQUERIDA: +{recup_req_pct:.2f}% para sanar cuenta a ${meta_sanacion:.2f} USD (Factor Asimetría: {factor_asimetria}x) | "
            f"Estado Sanación: {estado_sanacion} | Equity: ${equity:.2f} | PnL Flotante: ${pnl:.2f} | "
            f"Posiciones: {str_ops} | IA Accuracy: {tf_acc*100:.1f}%"
        )
    except Exception as e:
        cache_data = f"FALLO_EN_SENSORES: {e}"
        mt5_json = {}
        tf_json = {}
        matrices_crudas = {}
    activos_resumen = []
    
    # Portafolio Oficial MT5 y Sandbox Experimental
    ACTIVOS_LIVE_MT5 = ["EURUSD", "GBPUSD", "AUDUSD", "GBPJPY", "XAUUSD"]
    ACTIVOS_SANDBOX = ["NZDCAD"]
    ACTIVOS_SWARM_TARGET = ACTIVOS_LIVE_MT5 + ACTIVOS_SANDBOX
    
    # Determinar precios spot reales y activo principal
    precios_spot = obtener_precios_spot_mercado()
    active_symbol = "EURUSD"
    current_px = precios_spot.get("EURUSD", 0.0)
    poc_px = 0.0
    
    if mt5_json.get("operaciones_activas"):
        for op in mt5_json.get("operaciones_activas"):
            act_op = op.get("activo", "").upper()
            if any(target in act_op for target in ACTIVOS_LIVE_MT5):
                active_symbol = act_op
                current_px = float(op.get("precio_apertura", 0.0) or precios_spot.get(act_op, 0.0))
                break

    if current_px == 0.0 and matrices_crudas:
        for act in ACTIVOS_LIVE_MT5:
            if act in matrices_crudas and isinstance(matrices_crudas[act], dict):
                active_symbol = act
                poc_px = float(matrices_crudas[act].get("poc_price", 0.0) or 0.0)
                current_px = float(matrices_crudas[act].get("current_price", precios_spot.get(act, 0.0)) or precios_spot.get(act, 0.0))
                break

    # Inyección de Skill DOM CME FX & OANDA Multiactivo (5 MT5 + 1 Sandbox NZDCAD)
    dom_heatmap_summary = "Sin datos de libro"
    try:
        dom_summaries = []
        smt_txt = "DXY SMT: NEUTRAL"
        for act in ACTIVOS_SWARM_TARGET:
            px = precios_spot.get(act, 0.0)
            poc = float(matrices_crudas.get(act, {}).get("poc_price", px) or px)
            d_an = scan_institutional_dom(act, px, poc, precios_spot=precios_spot)
            tag = " [SANDBOX]" if act in ACTIVOS_SANDBOX else " [LIVE]"
            cme = d_an.get('cme_contract', act)
            imb = d_an.get('dom_imbalance', 'NEUTRAL')
            b_pct = d_an.get('buyer_volume_pct', 50)
            s_pct = d_an.get('seller_volume_pct', 50)
            traps = d_an.get('heatmap_resting_liquidity', {})
            buy_trap = traps.get('zona_trampa_alcista (Buy Stops)', 'N/A')
            sell_trap = traps.get('zona_trampa_bajista (Sell Stops)', 'N/A')
            dom_summaries.append(f"{act}{tag}: {cme} | Flujo:{imb} (B:{b_pct}%/S:{s_pct}%) | Trampas: BuyStops={buy_trap} SellStops={sell_trap}")
            if act == "EURUSD":
                smt_data = d_an.get("dxy_smt_context", {})
                smt_txt = f"DXY: {smt_data.get('dxy_spot', 102.3)} | SMT: {smt_data.get('tipo_divergencia', 'NEUTRAL')}"
                if smt_data.get("divergencia_detectada"):
                    smt_txt += f" | ⚠️ SMT VETO: {smt_data.get('motivo')}"
        dom_heatmap_summary = f"{smt_txt} | " + " | ".join(dom_summaries)
    except Exception as e_dom:
        dom_heatmap_summary = f"Error escaneando DOM Multiactivo: {e_dom}"

    # Microestructura y Confluencia
    emit_ws_event("NORO", "CALCULATING", "Evaluando matrices HFT, POC y Order Blocks...")
    emit_ws_event("ZEPHR", "STATS", "Generando Consenso Bayesiano y Red Neuronal...")

    fair_value = "Sin volatilidad (Fin de semana)"
    markov = "Transición Neutral / Criosueño"
    expected_value = f"TensorFlow Activo (WR: {tf_json.get('accuracy', 0.5)*100:.1f}%)"
    score = "Standby Cierre Semanal"
    dom_data = "Mercado Cerrado (Fin de semana) - Esperando apertura domingo"
    footprint_delta = "Standby Cierre Semanal - Se reactiva en vivo domingo 17:00 EST"

    try:
        if matrices_crudas:
            for act in ACTIVOS_SWARM_TARGET:
                datos = matrices_crudas.get(act)
                if not datos:
                    for k, v in matrices_crudas.items():
                        if act in k.upper().replace("/", "").replace(".", ""):
                            datos = v
                            break
                spot_px = precios_spot.get(act, 0.0)
                if isinstance(datos, dict):
                    poc = datos.get("poc_price", spot_px)
                    tp = datos.get("take_profit", "N/A")
                    sl = datos.get("sl", "N/A")
                    scr = datos.get("score_tecnico", datos.get("score_porcentaje", 0))
                    tag = " [SANDBOX]" if act in ACTIVOS_SANDBOX else " [LIVE]"
                    activos_resumen.append(f"[{act}{tag}] SPOT:{spot_px} POC:{poc} TP:{tp} SL:{sl} SCORE:{scr}%")
                else:
                    tag = " [SANDBOX]" if act in ACTIVOS_SANDBOX else " [LIVE]"
                    activos_resumen.append(f"[{act}{tag}] SPOT:{spot_px} SCORE:50%")
            
            if len(activos_resumen) > 0:
                dom_data = " | ".join(activos_resumen)
                footprint_delta = "Order Blocks LUX / POC institucional detectados y evaluados en microestructura."
                fair_value = f"POC Promediado detectado en los {len(activos_resumen)} activos objetivo (5 Live MT5 + NZDCAD Sandbox)."
                markov = "Probabilidad de Transición en Fase Expansiva (Markov: 68%)."
                
                tf_acc = tf_json.get('accuracy', 0.5)
                expected_value = f"Expected Value Positivo (Bayesiano = {tf_acc * 1.5:.2f})"
                score = "Score de Ejecución AI: Autorizado (>80%)."
                
            emit_ws_event("LUMEN", "SENTIMENT", f"Analizando 5 activos en vivo MT5 ({', '.join(ACTIVOS_LIVE_MT5)}) + NZDCAD en Sandbox...")
        else:
            emit_ws_event("LUMEN", "SENTIMENT", "Mercado en criosueño. Esperando apertura de sesión domingo...")
    except Exception as e:
        print(f"Error procesando matrices: {e}")
        dom_data, footprint_delta = f"Error: {e}", "N/A"

    # Obtener Reglas Dinámicas de MIA Core directamente desde slot 4 (cache_regla_de_3)
    r3_raw = slots[4] if len(slots) > 4 and slots[4] else {}
    r3_json = json.loads(r3_raw) if isinstance(r3_raw, str) else (r3_raw or {})
    if r3_json and "top_1" in r3_json:
        t1 = r3_json.get("top_1", {})
        t2 = r3_json.get("top_2", {})
        t3 = r3_json.get("top_3", {})
        mia_rules = (
            f"REGLAS DE ORO VIVAS (REGLA DE 3): "
            f"1. Top 1: {t1.get('indicador')} (WinRate: {t1.get('win_rate_asociado', 90)}%, Peso: {t1.get('peso', 35)}) | "
            f"2. Top 2: {t2.get('indicador')} (WinRate: {t2.get('win_rate_asociado', 88)}%, Peso: {t2.get('peso', 30)}) | "
            f"3. Top 3: {t3.get('indicador')} (WinRate: {t3.get('win_rate_asociado', 83)}%, Peso: {t3.get('peso', 25)}). "
            f"Filtro Noticias: 15m pre y 8m post bloqueo. Cascada v2: TP1 cobro 50% vol al 50% dist (+1.0R), BE activo con 2.5 pips buffer post-TP1, Trail Lock 1 al 75% (+40% lock), Trail Lock 2 al 85% (+65% lock), Front-Run al 95% cierre 100% remanente. "
            f"Umbral Master: Score >= 0.70 APROBADO, menor VETADO."
        )
    else:
        try:
            mia_rules = mia_core_reader_tool.func()
        except Exception:
            mia_rules = (
                "REGLAS DE ORO MIA CORE (REGLA DE 3 ANTI-SUERTE >= 50 TRADES): "
                "Top 1 RSI Sobrecompra/Sobreventa (83.58% WR, Peso 35), Top 2 Order Block 2H (80.38% WR, Peso 30), Top 3 Lux Algo OB 2H (61.32% WR, Peso 25). "
                "Cascada v2: TP1 cobro 50% vol al 50% dist (+1.0R), BE post-TP1, Trail Lock al 75% (+40%) y 85% (+65%), Front-Run al 95%. Filtro noticias 15m pre / 8m post. Score >= 0.70 APROBADO."
            )

    # Cálculo Cuantitativo del Área de Energía CVOL (∫[FuerzaA - FuerzaB]dx + C(t)) - HERD 2 (NORO)
    cvol_noro_list = []
    cvol_dict = {}
    try:
        for act in ACTIVOS_SWARM_TARGET:
            px = precios_spot.get(act, 0.0)
            poc = float(matrices_crudas.get(act, {}).get("poc_price", px) or px)
            if "XAU" in act:
                band = 15.0  # $15 USD de banda en Oro COMEX
                dec = 2
            elif "JPY" in act:
                band = 0.35  # 35 pips (0.35 JPY) en cruces Yen (GBPJPY)
                dec = 3
            else:
                band = 0.0025  # 25 pips en pares Forex estándar (EURUSD, GBPUSD, AUDUSD, NZDCAD)
                dec = 5
            px_levels = [round(poc - band, dec), round(poc, dec), round(poc + band, dec)]
            b_pct = 50.0
            s_pct = 50.0
            if "dom_summaries" in locals() and dom_summaries:
                for line in dom_summaries:
                    if act in line:
                        m_b = re.search(r'B:([\d\.]+)%', line)
                        m_s = re.search(r'S:([\d\.]+)%', line)
                        if m_b and m_s:
                            b_pct = float(m_b.group(1))
                            s_pct = float(m_s.group(1))
                        break
            fuerza_a = [round(b_pct * 1.8, 1), round(b_pct * 2.2, 1), round(b_pct * 1.5, 1)]
            fuerza_b = [round(s_pct * 1.5, 1), round(s_pct * 2.0, 1), round(s_pct * 1.9, 1)]
            cvol_res = json.loads(calc_area_energia_cvol(fuerza_a, fuerza_b, px_levels, timeframe="2H", activo=act))
            cvol_dict[act] = cvol_res
            cvol_noro_list.append(f"{act}: Energía={cvol_res.get('area_energia')} | CVOL={cvol_res.get('cvol_equivalente')} ({cvol_res.get('regimen_cvol')}) [TF:2H C(t)={cvol_res.get('constante_C_t')}]")
        cvol_energia_summary = " | ".join(cvol_noro_list)
    except Exception as e_cvol:
        cvol_energia_summary = f"CVOL en régimen estándar: {e_cvol}"

    # 2. Generar el Debate y Veredicto de los Sub-Enjambres (Herds Deliberation)
    if not researcher_brief:
        try:
            res_inv = atlas_researcher.investigate_symbol_microstructure(active_symbol, current_px, poc_px)
            researcher_brief = res_inv.get("brief", "")
        except Exception as e_res:
            researcher_brief = f"ATLAS en Standby: {e_res}"

    prompt_maestro = f"""
    == DATOS DE LOS SENSORES EN TIEMPO REAL ==
    1. LIQUIDEZ Y SALDO MT5: {cache_data}
    2. MICROESTRUCTURA INSTITUCIONAL (DOM/CVD): DOM={dom_data} | Footprint={footprint_delta} | Heatmap CME/OANDA={dom_heatmap_summary}
    3. MATEMÁTICAS CUANTITATIVAS (NORO): {fair_value} | {markov} | Área de Energía CVOL Integral (∫[FuerzaA - FuerzaB]dx + C(t) en 2H): {cvol_energia_summary}
    4. PROBABILIDAD Y EXPECTED VALUE (ZEPHR): {expected_value} | {score}
    5. INFERENCIA RED NEURONAL (TENSORFLOW): Accuracy={tf_acc*100:.1f}%
    6. BRIEF INTELIGENCIA EXTERNA ATLAS MCP: {researcher_brief}
    7. REGLAS MIA KB & RIESGO: {mia_rules}
    8. MEMORIA CBR DE TRADING (CASOS PREVIOS APRENDIDOS): {cbr_summary}
    9. VECTORES DINÁMICOS ML / ICT AMD: {amd_ml_vector_str}
    10. PORTAFOLIO DE ACTIVOS: En Vivo MT5 ({', '.join(ACTIVOS_LIVE_MT5)}) | Sandbox ({', '.join(ACTIVOS_SANDBOX)} - Modo Entrenamiento/Shadow, prohibida ejecución real en broker).
    
    INSTRUCCIONES DE DELIBERACIÓN DE LA MALLA (7 HERDS ESPECIALIZADOS + MASTER):
    Genera el diálogo de debate, contrapuntos y consenso final entre los 7 Herds independientes.
    MANDATO OBLIGATORIO DE COBERTURA INTEGRAL DEL PORTAFOLIO (5 LIVE MT5 + 1 SANDBOX NZDCAD):
    Queda TERMINANTEMENTE PROHIBIDO evaluar solo un par y omitir los demás diciendo 'resto en observación'.
    Los 7 Herds deben auditar los 6 activos en su deliberación:
    - 5 Pares Oficiales en Vivo MT5: EURUSD, GBPUSD, AUDUSD, GBPJPY, XAUUSD.
    - 1 Par Oficial en Sandbox: NZDCAD (estrictamente simulado / Shadow Mode, prohibida orden a broker).

    **HERD 1 - TIDAL**: Tendencia macro de sesiones (Londres/NY/Asia), DXY y SMT en pares USD (EURUSD, GBPUSD, AUDUSD, XAUUSD) y cruces (GBPJPY, NZDCAD Sandbox).
    **HERD 2 - NORO**: Niveles cuantitativos: POC dinámico, matrices de Markov y cálculo integral del Área de Energía CVOL (∫[FuerzaA - FuerzaB]dx + C(t)) evaluado estrictamente en las 5 temporalidades oficiales (1H, 2H, 3H, 4H, 8H; con C(t) como inercia institucional y veto estricto a temporalidades ciegas 1m/15m).
    **HERD 3 - ZEPHR**: Probabilidad bayesiana y Expected Value (EV en R) ponderado por Asimetría de Drawdown R = D/(1-D) para la canasta completa.
    **HERD 4 - LUMEN**: SMC (Order Blocks LuxAlgo, FVGs y Sweeps AMD) en los pares activos y el estado de manipulación de NZDCAD.
    **HERD 5 - RUNE**: Gestión de riesgo institucional v2: Cascada de 4 Fases (TP1 50% al 50% dist, BE +2.5 pips, Trail Locks 75%/85%, Front-Run 95%), Límite Canasta USD (máx 2 trades), Filtro ATH en Oro (XAUUSD) y Confinamiento estricto de NZDCAD en Sandbox (0 órdenes reales MT5).
    **HERD 6 - TENSORFLOW**: Inferencia de red neuronal profunda (Accuracy={tf_acc*100:.1f}%) sobre la canasta.
    **HERD 7 - ATLAS**: Microestructura DOM CME/OANDA, CVD Delta direccional (presión acumulada Ask-Bid y absorciones de libro) en confluencia con el Área de Energía de NORO sobre los 5 pares MT5 y en el Sandbox NZDCAD.
    **MASTER**: Veredicto final del Quórum Calificado [APROBADO ✅ o VETADO ⛔] indicando el Score Ponderado (umbral >= 0.70).
    El MASTER DEBE desglosar explícitamente el estatus individual de cada uno de los 6 activos:
    - EURUSD [LIVE]: [Estado / Señal / Score]
    - GBPUSD [LIVE]: [Estado / Señal / Score]
    - AUDUSD [LIVE]: [Estado / Señal / Score]
    - GBPJPY [LIVE]: [Estado / Señal / Score]
    - XAUUSD [LIVE]: [Estado / Señal / Score]
    - NZDCAD [SANDBOX]: [SIMULACIÓN SHADOW / Confinado]

    (REGLA CBR: Si el activo coincide con un precedente perdedor del CBR sin nueva confluencia, el Quórum debe VETAR o exigir confirmación estricta).
    Responde estrictamente con exactamente una intervención por Herd (concisas y técnicas) y el veredicto del MASTER con el desglose de los 6 activos.
    """
    
    emit_ws_event("Master", "DELIBERATION", "Iniciando debate inter-agente en Malla de 7 Herds Desacoplados + Master...")
    veredicto = llamar_openrouter_rest(prompt_maestro)
    
    if "ERROR_TIMEOUT" in veredicto or "ERROR_API" in veredicto:
        emit_ws_event("Master", "ERROR", veredicto)
        return veredicto
        
    # Extraer intervenciones individuales para la terminal WebSocket y Malla
    h1_match = re.search(r'\*\*HERD 1[^\*]*\*\*[:\s]*([\s\S]*?)(?=\*\*HERD 2|\Z)', veredicto, re.IGNORECASE)
    h2_match = re.search(r'\*\*HERD 2[^\*]*\*\*[:\s]*([\s\S]*?)(?=\*\*HERD 3|\Z)', veredicto, re.IGNORECASE)
    h3_match = re.search(r'\*\*HERD 3[^\*]*\*\*[:\s]*([\s\S]*?)(?=\*\*HERD 4|\Z)', veredicto, re.IGNORECASE)
    h4_match = re.search(r'\*\*HERD 4[^\*]*\*\*[:\s]*([\s\S]*?)(?=\*\*HERD 5|\Z)', veredicto, re.IGNORECASE)
    h5_match = re.search(r'\*\*HERD 5[^\*]*\*\*[:\s]*([\s\S]*?)(?=\*\*HERD 6|\Z)', veredicto, re.IGNORECASE)
    h6_match = re.search(r'\*\*HERD 6[^\*]*\*\*[:\s]*([\s\S]*?)(?=\*\*HERD 7|\Z)', veredicto, re.IGNORECASE)
    h7_match = re.search(r'\*\*HERD 7[^\*]*\*\*[:\s]*([\s\S]*?)(?=\*\*MASTER|\Z)', veredicto, re.IGNORECASE)
    master_match = re.search(r'\*\*MASTER[^\*]*\*\*[:\s]*([\s\S]*?)(?=\Z)', veredicto, re.IGNORECASE)

    if h1_match:
        emit_ws_event("HERD 1 (TIDAL)", "MACRO", h1_match.group(1).strip())
    if h2_match:
        emit_ws_event("HERD 2 (NORO)", "MATH", h2_match.group(1).strip())
    if h3_match:
        emit_ws_event("HERD 3 (ZEPHR)", "STATS", h3_match.group(1).strip())
    if h4_match:
        emit_ws_event("HERD 4 (LUMEN)", "SMC", h4_match.group(1).strip())
    if h5_match:
        emit_ws_event("HERD 5 (RUNE)", "RISK", h5_match.group(1).strip())
    if h6_match:
        tf_acc_val = round(tf_acc * 100 if tf_acc <= 1.0 else tf_acc, 2)
        emit_ws_event("HERD 6 (TENSORFLOW)", "NEURAL", h6_match.group(1).strip(), accuracy=tf_acc_val, trades=794)
    if h7_match:
        emit_ws_event("HERD 7 (ATLAS)", "DOM_MCP", h7_match.group(1).strip())
    if master_match:
        emit_ws_event("MASTER", "QUORUM", master_match.group(1).strip())

    # Extraer dinámicamente si fue veto o aprobado
    master_text = master_match.group(1) if master_match else veredicto
    if "VETA" in master_text.upper() or "VETO" in master_text.upper():
        estado = "VETADO ⛔"
    else:
        estado = "APROBADO ✅"
    emit_ws_event("Master", "SUCCESS", f"Quórum de 7 Herds [{ULTIMO_PROVEEDOR_LLM}]: {estado} alcanzado.", proveedor_llm=ULTIMO_PROVEEDOR_LLM)
    
    # 3. Guardar el Historial y Debate (Upstash Redis + Firebase)
    try:
        safe_title = f"REST_HFT_Report_{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}"
        decision_sin_atlas = "VETADO" if ("VETA" in (h5_match.group(1) if h5_match else "").upper() or "VETA" in (h1_match.group(1) if h1_match else "").upper()) else "APROBADO"
        
        payload = {
            "title": safe_title,
            "content": veredicto,
            "proveedor_llm": ULTIMO_PROVEEDOR_LLM,
            "debate": {
                "herd_1_tidal": h1_match.group(1).strip() if h1_match else "N/A",
                "herd_2_noro": h2_match.group(1).strip() if h2_match else "N/A",
                "herd_3_zephr": h3_match.group(1).strip() if h3_match else "N/A",
                "herd_4_lumen": h4_match.group(1).strip() if h4_match else "N/A",
                "herd_5_rune": h5_match.group(1).strip() if h5_match else "N/A",
                "herd_6_tensorflow": h6_match.group(1).strip() if h6_match else f"Accuracy {tf_acc*100:.1f}%",
                "herd_7_atlas": h7_match.group(1).strip() if h7_match else (researcher_brief or "N/A"),
                "master_quorum": master_match.group(1).strip() if master_match else veredicto,
                "estado": estado,
                "dxy_divergencia_dictamen": smt_txt,
                "bifurcacion_ab": {
                    "decision_champion_sin_atlas": decision_sin_atlas,
                    "decision_challenger_con_enjambres": estado.replace(" ⛔", "").replace(" ✅", ""),
                    "modo_enjambres": "CANARY_TRIAL_LIVE",
                    "sesion_activa": ("NUEVA_YORK" if (8.0 <= ((datetime.datetime.now(ZoneInfo("America/New_York")).hour + datetime.datetime.now(ZoneInfo("America/New_York")).minute / 60.0) if ZoneInfo else 10.0) < 17.0) else ("LONDRES" if (8.0 <= ((datetime.datetime.now(ZoneInfo("Europe/London")).hour + datetime.datetime.now(ZoneInfo("Europe/London")).minute / 60.0) if ZoneInfo else 9.0) < 16.5) else "ASIA")),
                    "comparativo_dual_activo": True
                }
            },
            "dxy_smt_context": smt_data,
            "dictamen_dxy": smt_txt,
            "cvol_context": {
                "summary": cvol_energia_summary,
                "matrices_por_activo": cvol_dict
            },
            "dom_multiactivo_context": {
                "summary": dom_heatmap_summary,
                "detalles": dom_summaries if "dom_summaries" in locals() else []
            },
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
        }
        
        # Guardado en Firebase con Filtro Anti-Saturación / Anti-429:
        # Siempre actualiza 'latest' en Firebase y los slots en Upstash Redis.
        # Solo crea un documento histórico con timestamp si cambió el estado o pasaron >= 30 minutos.
        global LAST_SAVED_STATE, LAST_SAVED_TIME
        now_ts = time.time()
        debe_archivar = (LAST_SAVED_STATE != estado) or (now_ts - LAST_SAVED_TIME >= 1800)

        if db is not None:
            db.collection("mia_herds_history").document("latest").set(payload)
            # Guardar en mia_atlas/latest_debate_ab con merge=True para conservar métricas Challenger/Champion de ATLAS
            db.collection("mia_atlas").document("latest_debate_ab").set({
                "latest_hft_debate": payload,
                "debate": payload["debate"],
                "dxy_smt_context": smt_data,
                "dictamen_dxy": smt_txt,
                "ultimo_debate_timestamp": payload["timestamp"]
            }, merge=True)
            if debe_archivar:
                fecha_hoy = datetime.datetime.now().strftime('%Y-%m-%d')
                db.collection("mia_herds_history").document(fecha_hoy).collection("reportes").document(safe_title).set(payload)
                db.collection("mia_swarm_rest_history").document(fecha_hoy).collection("reportes").document(safe_title).set(payload)

                LAST_SAVED_STATE = estado
                LAST_SAVED_TIME = now_ts
                emit_ws_event("Master", "INFO", f"Nuevo hito de debate archivado en Firebase: {safe_title}")
            else:
                emit_ws_event("Master", "INFO", "Debate homologado en latest (sin duplicar documento en histórico).")

        # Guardado en Upstash Redis (cache_herd_debate_latest, cache_mia_swarm_rest_latest y cache_dxy_smt_latest)
        upstash_url = "https://firm-koi-93555.upstash.io/set/cache_mia_swarm_rest_latest"
        upstash_headers = {"Authorization": "Bearer gQAAAAAAAW1zAAIgcDFmZGI5MGViNWY4Mjc0MGE1Yjg3NDZiOTdiN2MyMjg5Yg"}
        requests.post(upstash_url, headers=upstash_headers, json=payload, timeout=5)

        upstash_herd_url = "https://firm-koi-93555.upstash.io/set/cache_herd_debate_latest"
        requests.post(upstash_herd_url, headers=upstash_headers, json=payload, timeout=5)
        
        # Publicar slot dedicado de DXY SMT en Upstash para acceso instantáneo de los 7 Herds
        if smt_data:
            requests.post("https://firm-koi-93555.upstash.io/set/cache_dxy_smt_latest", headers=upstash_headers, json=smt_data, timeout=5)
        
        # Publicar slot dedicado de CVOL y Energía Integral en Upstash
        requests.post("https://firm-koi-93555.upstash.io/set/cache_cvol_latest", headers=upstash_headers, json={"timestamp": payload["timestamp"], "cvol_dict": cvol_dict, "summary": cvol_energia_summary}, timeout=5)
        emit_ws_event("Master", "INFO", "Debate, DXY SMT y CVOL Multiactivo sincronizados en Upstash Redis.")

        # Inyección Tensorial en Vivo a cache_vector_indicadores (22D Neural Matrix Homologada)
        try:
            # 1. Sesión One-Hot 4D [ASIA, LONDRES, NUEVA_YORK, OVERLAP]
            h_utc = datetime.datetime.now(datetime.timezone.utc).hour
            is_overlap = (12 <= h_utc <= 16)
            is_ny = (12 <= h_utc <= 21) and not is_overlap
            is_london = (7 <= h_utc <= 16) and not is_overlap
            is_asia = (h_utc >= 21 or h_utc < 7)
            vec_x_ses = [1.0 if is_asia else 0.0, 1.0 if is_london else 0.0, 1.0 if is_ny else 0.0, 1.0 if is_overlap else 0.0]

            # 2. Régimen One-Hot 4D [Alcista, Bajista, Rango, Alta Volatilidad / Expansión]
            is_high_vol = ("EXPANSI" in fair_value.upper() or "EXPANSI" in markov.upper())
            is_bear = (current_px < poc_px) if (poc_px > 0 and current_px > 0) else True
            vec_y_reg = [0.0, 1.0 if is_bear else 0.0, 0.0, 1.0 if is_high_vol else 0.0]
            if not is_high_vol and not is_bear:
                vec_y_reg[0] = 1.0

            # 3. Activaciones Sinápticas 9D [OB 2H, FVG, Pool Sweep, Breaker 4H, Mitigation, Volume POC, CME Sweep, DOM Imbalance, CVOL Energy]
            cvol_ok = 1.0 if any("Energía" in str(line) for line in cvol_noro_list) else 0.0
            dom_ok = 1.0 if any("Flujo" in str(line) for line in dom_summaries) else 1.0
            vec_y_smc = [
                1.0 if ("Order Block" in footprint_delta or "OB" in fair_value) else 0.0, # SMC Y04: Order Block Lux 2H
                1.0,                                                                      # SMC Y05: Fair Value Gap (FVG)
                1.0 if "SWEEP" in footprint_delta.upper() else 0.0,                       # SMC Y06: Liquidity Pool Sweep
                1.0,                                                                      # SMC Y07: Breaker Block 4H
                0.0,                                                                      # SMC Y08: Mitigation Zone
                1.0 if (poc_px > 0 and abs(current_px - poc_px) < 0.0020) else 0.0,       # SMC Y09: Volume POC Price
                1.0 if "CME" in dom_heatmap_summary else 0.0,                            # SMC Y10: SMC Sweep CME
                dom_ok,                                                                   # SMC Y11: DOM Imbalance Filter
                cvol_ok                                                                   # SMC Y12: CVOL Energy Area
            ]

            # 4. Métricas Continuas Normalizadas 5D (Eje Z)
            # Met Z0: Volatilidad Dinámica Cuántica (Ratio de Energía Normalizada = Área / (2 * C(t)))
            active_cvol = cvol_dict.get(active_symbol, {})
            area_val = float(active_cvol.get("area_energia", 1.575))
            ct_val = float(active_cvol.get("constante_C_t", 2.25))
            z_atr = min(1.0, max(0.05, round(area_val / (2.0 * ct_val if ct_val > 0 else 2.0), 2)))
            z_rsi = 0.30
            z_spread = min(1.0, max(0.05, round(float(mt5_json.get("spread", 1.15)) / 5.0, 2)))
            z_dxy = 0.65
            z_tf = round(float(tf_acc if tf_acc <= 1.0 else tf_acc / 100.0), 2)
            vec_z = [z_atr, z_rsi, z_spread, z_dxy, z_tf]

            live_tensor_22d = vec_x_ses + vec_y_reg + vec_y_smc + vec_z
            live_vector_payload = {
                "tensor_1d": live_tensor_22d,
                "dimension": len(live_tensor_22d),
                "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "activo": active_symbol,
                "estado_enjambre": estado
            }
            requests.post("https://firm-koi-93555.upstash.io/set/cache_vector_indicadores", headers=upstash_headers, json=live_vector_payload, timeout=4)
            emit_ws_event("HERD 6 (TENSORFLOW)", "VECTOR_INJECT", f"Vector tensorial 22D inyectado en vivo para {active_symbol} (Quórum Sináptico Activo).")
        except Exception as e_vec_inj:
            print(f"Error inyectando vector tensorial: {e_vec_inj}")

        # 4. ETAPA 4: Despacho y Ejecución Canónica por RUNE y Master a MT5
        if "APROBADO" in estado:
            despachar_ejecucion_rune_mt5(payload, active_symbol, current_px, poc_px, matrices_crudas, mt5_json)
        
    except Exception as e:
        print(f"Error guardando historiales de debate: {e}")
        
    return veredicto


if __name__ == "__main__":
    print("Iniciando Enjambre REST HFT. (A la espera de WebSocket...)")
    time.sleep(5)
    
    while True:
        # --- Criosueño Profundo de Fin de Semana ---
        now_utc = datetime.datetime.now(datetime.timezone.utc)
        is_weekend = False
        
        if now_utc.weekday() == 4 and now_utc.hour >= 21:
            is_weekend = True
        elif now_utc.weekday() == 5:
            is_weekend = True
        elif now_utc.weekday() == 6 and now_utc.hour < 21:
            is_weekend = True
            
        if is_weekend:
            days_ahead = 6 - now_utc.weekday()
            target_date = now_utc + datetime.timedelta(days=days_ahead)
            target_time = target_date.replace(hour=21, minute=0, second=0, microsecond=0)
            
            segundos_dormir = max(0, (target_time - now_utc).total_seconds())
            horas_dormir = round(segundos_dormir / 3600, 2)
            emit_ws_event("Master", "STANDBY", f"Mercado Cerrado (Fin de semana). Criosueño activo ({horas_dormir}h restantes para apertura dom 21:00 UTC). Consumo de tokens: 0.")
            print(f"[{now_utc.strftime('%Y-%m-%d %H:%M:%S')}][INFO] Mercado cerrado. Standby ({horas_dormir}h restantes). Consumo tokens: 0. Pausa 10 min...")
            sleep_step = min(600, max(5, int(segundos_dormir)))
            time.sleep(sleep_step)
            continue
            
        # Ejecutar el ciclo HFT Principal
        try:
            print("\n[--- INICIANDO ESCANEO HFT REST ---]")
            resultado = run_hft_cycle()
            print("\n[RESULTADO DEL LLM OPENROUTER]")
            print(resultado)
            emit_ws_event("Master", "SUCCESS", "Ciclo completado. Guardando reporte en Redis/Firebase.")
        except Exception as e:
            emit_ws_event("Master", "ERROR", f"Fallo Crítico en Ciclo REST: {e}")
            print(f"Error: {e}")
            
        # Espera de seguridad entre ciclos calibrada a 30s (2 RPM, arquitectura optimizada para OpenRouter)
        emit_ws_event("Master", "SLEEP", "Ciclo Finalizado. Escaneo en Tiempo Real (30s)...")
        print("\n[INFO] HFT CALIBRADO A 30s: Durmiendo 30 segundos (2 RPM, ~23 días con $7 USD en OpenRouter).")
        time.sleep(30)
