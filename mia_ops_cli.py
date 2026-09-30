#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
MIA SYSTEM OPS CLI - CONSOLA DE MONITOREO DEL ENJAMBRE DE OPERACIONES
================================================================================
Visualizador en tiempo real de la Malla de 6 Herds de Infraestructura y el
Supervisor General (MIA Watchdog Master).
"""

import sys
import os
import time
import json
import datetime
import io

# Asegurar codificación UTF-8 universal en terminales (Windows CMD, PowerShell, Termux)
if sys.stdout and hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True)
if sys.stderr and hasattr(sys.stderr, "buffer"):
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace", line_buffering=True)

# Códigos de Color ANSI
C_RESET   = "\033[0m"
C_BOLD    = "\033[1m"
C_DIM     = "\033[2m"
C_CYAN    = "\033[96m"
C_YELLOW  = "\033[93m"
C_GREEN   = "\033[92m"
C_RED     = "\033[91m"
C_MAGENTA = "\033[95m"
C_BLUE    = "\033[94m"
C_WHITE   = "\033[97m"

if os.name == "nt":
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
    except Exception:
        pass

def print_banner():
    os.system("cls" if os.name == "nt" else "clear")
    print(f"{C_BOLD}{C_MAGENTA}╔══════════════════════════════════════════════════════════════════════════╗{C_RESET}")
    print(f"{C_BOLD}{C_MAGENTA}║      MIA SYSTEM OPS SWARM - CONSOLA DE OPERACIONES (6 HERDS SRE)         ║{C_RESET}")
    print(f"{C_BOLD}{C_MAGENTA}║      Front-Office: Trading Herds | Back-Office: System Ops & Watchdog     ║{C_RESET}")
    print(f"{C_BOLD}{C_MAGENTA}╚══════════════════════════════════════════════════════════════════════════╝{C_RESET}\n")

def render_ops_cycle(audit_data: dict):
    ts = audit_data.get("timestamp", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    herds = audit_data.get("herds_results", {})
    triage = audit_data.get("triage", {})
    exec_ms = audit_data.get("total_execution_ms", 0.0)

    print(f"{C_DIM}──────────────────────────────────────────────────────────────────────────{C_RESET}")
    print(f"{C_BOLD}{C_BLUE}[{ts}] CICLO SRE EJECUTADO EN {exec_ms}ms | ESTADO: {audit_data.get('estado_general')}{C_RESET}\n")

    # HERD T1 (DBA)
    t1 = herds.get("herd_t1_dba", {})
    t1_status = t1.get("status", "OK")
    t1_color = C_GREEN if t1_status == "OK" else C_RED
    print(f"{C_BOLD}{C_CYAN}  ► [HERD T1: DBA_SENTINEL]{C_RESET}")
    print(f"    {C_DIM}Rol:{C_RESET} Integridad Firestore/Upstash, normalización y anti-null.")
    print(f"    {C_DIM}Estado:{C_RESET} {t1_color}{t1_status}{C_RESET} | {t1.get('resumen', '')}")
    print()

    # HERD T2 (Senior Dev)
    t2 = herds.get("herd_t2_senior_dev", {})
    t2_status = t2.get("status", "OK")
    t2_color = C_GREEN if t2_status == "OK" else C_RED
    print(f"{C_BOLD}{C_YELLOW}  ► [HERD T2: SENIOR_CODE_AUDITOR]{C_RESET}")
    print(f"    {C_DIM}Rol:{C_RESET} Auditoría sintáctica AST, variables, codificación UTF-8 y antipatrones.")
    print(f"    {C_DIM}Estado:{C_RESET} {t2_color}{t2_status}{C_RESET} | Módulos Auditados: {t2.get('archivos_auditados', 0)}")
    if t2.get("errores_sintaxis"):
        print(f"    {C_RED}⚠ Fallos AST:{C_RESET} {t2.get('errores_sintaxis')}")
    print()

    # HERD T3 (Observability SRE)
    t3 = herds.get("herd_t3_observability_sre", {})
    t3_status = t3.get("status", "HEALTHY")
    t3_color = C_GREEN if t3_status == "HEALTHY" else C_YELLOW
    print(f"{C_BOLD}{C_GREEN}  ► [HERD T3: OBSERVABILITY_SRE]{C_RESET}")
    print(f"    {C_DIM}Rol:{C_RESET} Monitoreo activo de endpoints de Railway, OpenRouter, MCPs y Upstash.")
    print(f"    {C_DIM}Estado:{C_RESET} {t3_color}{t3_status}{C_RESET} | Servicios: {t3.get('servicios_auditados', 0)} online")
    for srv in t3.get("telemetria", [])[:4]:
        st = C_GREEN + srv['estado'] + C_RESET if srv['estado'] == "ONLINE" else C_RED + srv['estado'] + C_RESET
        print(f"    {C_DIM}• {srv['nombre']}:{C_RESET} {st} ({srv.get('latencia_ms', 0)}ms)")
    print()

    # HERD T4 (Cache Latency)
    t4 = herds.get("herd_t4_cache_latency", {})
    print(f"{C_BOLD}{C_BLUE}  ► [HERD T4: CACHE_LATENCY_SPECIALIST]{C_RESET}")
    print(f"    {C_DIM}Rol:{C_RESET} Desacoplamiento canónico atómico y latencia sub-35ms.")
    print(f"    {C_DIM}Estado:{C_RESET} {t4.get('status')} | Latencia MGET: {t4.get('mget_latency_ms')}ms | Slots: {t4.get('slots_disponibles')}")
    print(f"    {C_DIM}Última Regla de 3:{C_RESET} {t4.get('ultima_sincronizacion_regla_3')}")
    print()

    # HERD T5 (FinOps)
    t5 = herds.get("herd_t5_finops_billing", {})
    print(f"{C_BOLD}{C_WHITE}  ► [HERD T5: FINOPS_BILLING_CONTROLLER]{C_RESET}")
    print(f"    {C_DIM}Rol:{C_RESET} Control de presupuesto, pagos cloud anticipados y alertas a 48h.")
    print(f"    {C_DIM}Estado:{C_RESET} {C_GREEN}{t5.get('status')}{C_RESET} | {t5.get('firebase_spark_margin')}")
    for serv in t5.get("servicios", []):
        print(f"    {C_DIM}• {serv['plataforma']}:{C_RESET} {serv['costo_estimado_mensual']} ({serv['estado']} - Corte: {serv['dias_para_corte']}d)")
    print()

    # HERD T6 (UI/UX Stitch)
    t6 = herds.get("herd_t6_ui_ux_designer", {})
    print(f"{C_BOLD}{C_CYAN}  ► [HERD T6: UIUX_STITCH_DESIGNER]{C_RESET}")
    print(f"    {C_DIM}Rol:{C_RESET} Diseño con Google Stitch y Plotly Dark; extracción de CSS/HTML modular.")
    print(f"    {C_DIM}Estado:{C_RESET} {C_GREEN}{t6.get('status')}{C_RESET} | Rutas Auditadas: {len(t6.get('rutas_auditadas', []))}")
    print()

    # HERD T7 (Architect & Diagrammer)
    t7 = herds.get("herd_t7_architect_diagrammer", {})
    print(f"{C_BOLD}{C_YELLOW}  ► [HERD T7: ARCHITECT_DIAGRAMMER_INNOVATOR]{C_RESET}")
    print(f"    {C_DIM}Rol:{C_RESET} Diagramas dinámicos de conectividad Mermaid/SVG y diseño de microservicios.")
    print(f"    {C_DIM}Estado:{C_RESET} {C_GREEN}{t7.get('status')}{C_RESET} | Diagrama: Topología actualizada")
    print()

    # HERD T8 (Shadow Compliance)
    t8 = herds.get("herd_t8_shadow_compliance", {})
    print(f"{C_BOLD}{C_MAGENTA}  ► [HERD T8: SHADOW_COMPLIANCE_GATEKEEPER]{C_RESET}")
    print(f"    {C_DIM}Rol:{C_RESET} Candado MT5 (SHADOW_MODE_GLOBAL = True) y custodia del filtro de noticias.")
    print(f"    {C_DIM}Estado:{C_RESET} {C_GREEN}{t8.get('status')}{C_RESET} | Tickets Virtuales: {t8.get('tickets_virtuales_activos')}")
    print()

    # HERD T9 (Slack Dispatcher)
    t9 = herds.get("herd_t9_slack_dispatcher", {})
    print(f"{C_BOLD}{C_BLUE}  ► [HERD T9: SLACK_OPS_DISPATCHER]{C_RESET}")
    print(f"    {C_DIM}Rol:{C_RESET} Aislamiento de #mia-chat y despacho de Block Kit con botones interactivos.")
    print(f"    {C_DIM}Estado:{C_RESET} {C_GREEN}{t9.get('status')}{C_RESET} | Destino: {t9.get('canal_autorizado')}")
    print()

    # HERD T10 (Swarm & Neural Sentry)
    t10 = herds.get("herd_t10_swarm_neural_sentry", {})
    print(f"{C_BOLD}{C_GREEN}  ► [HERD T10: SWARM_NEURAL_SENTRY]{C_RESET}")
    print(f"    {C_DIM}Rol:{C_RESET} Vigilancia del Cerebro TensorFlow Deep Learning y de los 7 Trading Herds.")
    print(f"    {C_DIM}Estado:{C_RESET} {C_GREEN}{t10.get('status')}{C_RESET} | Accuracy: {t10.get('tensorflow_accuracy')}% | Inferencia: {t10.get('tensorflow_latency_ms')}ms")
    print()

    # WATCHDOG MASTER TRIAGE & COGNITIVE EVALUATION (OPENROUTER)
    print(f"{C_BOLD}{C_MAGENTA}  👑 [MIA WATCHDOG MASTER - TRIAGE SENIOR & COGNITIVE EVALUATION]{C_RESET}")
    eval_cog = triage.get("evaluacion_cognitiva", {})
    if eval_cog.get("evaluacion_disponible"):
        print(f"    {C_CYAN}🧠 Evaluador IA:{C_RESET} {eval_cog.get('modelo_evaluador')} {C_DIM}(Grounding Arquitectura MIA){C_RESET}")
    
    autos = triage.get("auto_corregidos_en_caliente", [])
    if autos:
        for a in autos:
            print(f"    {C_GREEN}⚡ [AUTO-CORREGIDO]:{C_RESET} {a}")
    else:
        print(f"    {C_GREEN}⚡ [AUTO-CORREGIDO]:{C_RESET} Cero fallos. Datos íntegros.")

    validadas = triage.get("propuestas_validadas_score_85", [])
    if validadas:
        print(f"    {C_GREEN}⭐ [RECOMENDADAS POR IA - SCORE >= 85]:{C_RESET}")
        for p in validadas:
            print(f"       • [Score {p.get('score', 90)}] {p.get('accion')}: {p.get('detalle', '')[:75]}...")
    else:
        print(f"    {C_DIM}⭐ [SCORE >= 85]:{C_RESET} Cero propuestas en cola.")

    observadas = triage.get("propuestas_observadas_score_menor_85", [])
    if observadas:
        print(f"    {C_YELLOW}⚠️ [OBSERVADAS / DESCARTADAS - SCORE < 85]:{C_RESET}")
        for o in observadas:
            print(f"       • [Score {o.get('score', 60)}] {o.get('accion')} -> Motivo: {o.get('justificacion_ia', '')[:70]}...")

    print(f"{C_DIM}──────────────────────────────────────────────────────────────────────────{C_RESET}\n")

def main():
    print_banner()
    print(f"{C_CYAN}Iniciando escucha continua del Enjambre de Operaciones (6 Herds + Watchdog)...{C_RESET}")
    print(f"{C_DIM}💡 Presiona [CTRL + C] para salir.{C_RESET}\n")

    while True:
        try:
            from mia_system_ops_swarm import system_ops_supervisor
            report = system_ops_supervisor.run_swarm_audit(notify_slack=False)
            print_banner()
            render_ops_cycle(report)
            time.sleep(15)
        except KeyboardInterrupt:
            print(f"\n{C_YELLOW}Cerrando monitor de Back-Office. Swarm sigue activo en background.{C_RESET}")
            break
        except Exception as e:
            print(f"{C_RED}Error en ciclo de auditoría: {e}{C_RESET}")
            time.sleep(10)

if __name__ == "__main__":
    main()
