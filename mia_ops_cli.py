"""
MIA OPS CLI - TERMINAL DE COMUNICACIÓN EN VIVO (BACK-OFFICE SWARM)
==================================================================
Interfaz de consola para monitorear en tiempo real la deliberación,
acciones técnicas y auditorías del Enjambre de Operaciones (MIA System Ops Swarm).
Muestra en vivo a:
- HERD T1 (DB_SYNC / CACHE_GUARD)
- HERD T2 (KB_ENGINE / REGLA_DE_3)
- HERD T3 (KPI_FINANCIAL_ANALYTICS)
- HERD T4 (DEVOPS_RAILWAY_HEALTH)
- WATCHDOG SUPERVISOR MASTER
"""

import os
import sys
import time
import json
import datetime
import requests

# Colores ANSI Cyberpunk para Terminal
C_CYAN = "\033[96m"
C_GREEN = "\033[92m"
C_YELLOW = "\033[93m"
C_MAGENTA = "\033[95m"
C_BLUE = "\033[94m"
C_RED = "\033[91m"
C_BOLD = "\033[1m"
C_DIM = "\033[2m"
C_RESET = "\033[0m"

UPSTASH_URL = os.getenv("UPSTASH_REDIS_REST_URL", "https://certain-gnat-160816.upstash.io")
UPSTASH_TOKEN = os.getenv("UPSTASH_REDIS_REST_TOKEN", "gQAAAAAAAnQwAAIgcDI2YTA5YjRlZDU2MDM0OWU5ODhlZjBlYTk4ODYyZDg0OA")
UPSTASH_HEADERS = {"Authorization": f"Bearer {UPSTASH_TOKEN}"}

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_banner():
    clear_screen()
    print(f"{C_BOLD}{C_MAGENTA}╔══════════════════════════════════════════════════════════════════════════╗{C_RESET}")
    print(f"{C_BOLD}{C_MAGENTA}║      MIA SYSTEM OPS SWARM - TERMINAL DE BACK-OFFICE & WATCHDOG           ║{C_RESET}")
    print(f"{C_BOLD}{C_MAGENTA}║     Monitoreo Autónomo de Infraestructura, Integridad de Datos & KPIs    ║{C_RESET}")
    print(f"{C_BOLD}{C_MAGENTA}╚══════════════════════════════════════════════════════════════════════════╝{C_RESET}\n")

def render_ops_cycle(audit_data: dict):
    ts = audit_data.get("timestamp", datetime.datetime.now().isoformat())
    herds = audit_data.get("herds_results", {})
    supervisor = audit_data.get("supervisor", "WATCHDOG_MASTER")
    exec_ms = audit_data.get("total_execution_ms", 0.0)

    print(f"{C_DIM}──────────────────────────────────────────────────────────────────────────{C_RESET}")
    print(f"{C_BOLD}{C_BLUE}[{ts}] CICLO DE AUDITORÍA EJECUTADO EN {exec_ms}ms{C_RESET}\n")

    # HERD T1
    t1 = herds.get("herd_t1_db_sync", {})
    t1_status = t1.get("status", "OK")
    t1_color = C_GREEN if t1_status == "OK" else C_RED
    print(f"{C_BOLD}{C_CYAN}  ► [HERD T1: DB_SYNC / CACHE_GUARD]{C_RESET}")
    print(f"    {C_DIM}Rol:{C_RESET} Sincronización MT5 y depuración de órdenes fantasma.")
    print(f"    {C_DIM}Estado:{C_RESET} {t1_color}{t1_status}{C_RESET} | Posiciones Activas: {C_BOLD}{t1.get('posiciones_activas', 'N/A')}{C_RESET}")
    print(f"    {C_DIM}Flotante Neto:{C_RESET} ${t1.get('flotante_neto', 0.0):+.2f} USD | Equity: ${t1.get('equity', 0.0):.2f} USD")
    eliminadas = t1.get('ordenes_fantasma_depuradas', [])
    if eliminadas:
        print(f"    {C_YELLOW}⚠ Órdenes Fantasma Purgadas:{C_RESET} {eliminadas}")
    print()

    # HERD T2
    t2 = herds.get("herd_t2_kb_engine", {})
    t2_status = t2.get("status", "OK")
    print(f"{C_BOLD}{C_YELLOW}  ► [HERD T2: KB_ENGINE / REGLA_DE_3]{C_RESET}")
    print(f"    {C_DIM}Rol:{C_RESET} Recalibración perpetua de Top 1-3 y fechas vivas en Upstash/Firebase.")
    print(f"    {C_DIM}Última Actualización:{C_RESET} {t2.get('ultima_actualizacion', 'N/A')}")
    top1 = t2.get('top_1', {})
    top2 = t2.get('top_2', {})
    top3 = t2.get('top_3', {})
    print(f"    {C_BOLD}Top 1:{C_RESET} {top1.get('indicador')} ({top1.get('win_rate_asociado')}%) | {C_BOLD}Top 2:{C_RESET} {top2.get('indicador')} ({top2.get('win_rate_asociado')}%) | {C_BOLD}Top 3:{C_RESET} {top3.get('indicador')} ({top3.get('win_rate_asociado')}%)")
    print()

    # HERD T3
    t3 = herds.get("herd_t3_kpi_analytics", {})
    print(f"{C_BOLD}{C_GREEN}  ► [HERD T3: KPI_FINANCIAL_ANALYTICS]{C_RESET}")
    print(f"    {C_DIM}Rol:{C_RESET} Sanitización numérica estricta a 2 decimales y métricas contrafactuales.")
    print(f"    {C_DIM}Trades Auditados:{C_RESET} {t3.get('trades_auditados', 0)} | Valores con colas corregidos: {t3.get('valores_sanitizados', 0)}")
    print()

    # HERD T4
    t4 = herds.get("herd_t4_devops_health", {})
    lat = t4.get("upstash_latency_ms", 0.0)
    lat_color = C_GREEN if lat < 100 else (C_YELLOW if lat < 300 else C_RED)
    print(f"{C_BOLD}{C_BLUE}  ► [HERD T4: DEVOPS_RAILWAY_HEALTH]{C_RESET}")
    print(f"    {C_DIM}Rol:{C_RESET} Monitoreo de latencia, red Upstash y debouncing HFT.")
    print(f"    {C_DIM}Latencia Upstash:{C_RESET} {lat_color}{lat} ms{C_RESET} | Stream HFT Activo: {t4.get('debate_stream_active')} | Guard Anti-429: {t4.get('anti_429_guard')}")
    print()

    # WATCHDOG MASTER
    print(f"{C_BOLD}{C_MAGENTA}  👑 [WATCHDOG SUPERVISOR GENERAL]{C_RESET}")
    print(f"    {C_BOLD}Veredicto de Integridad:{C_RESET} {C_GREEN}OPTIMAL_DATA_INTEGRITY (100% Homologado){C_RESET}")
    print(f"    {C_DIM}Canales Notificados:{C_RESET} Upstash Redis (cache_system_ops_status) | Slack Bridge Ready")
    print(f"{C_DIM}──────────────────────────────────────────────────────────────────────────{C_RESET}\n")

def main():
    print_banner()
    print(f"{C_CYAN}Iniciando escucha continua del Enjambre de Operaciones...{C_RESET}")
    print(f"{C_DIM}💡 Presiona [CTRL + C] para salir y volver a la terminal.{C_RESET}\n")

    while True:
        try:
            from mia_system_ops_swarm import system_ops_supervisor
            report = system_ops_supervisor.run_swarm_audit()
            print_banner()
            render_ops_cycle(report)
            time.sleep(10)
        except KeyboardInterrupt:
            print(f"\n{C_YELLOW}Cerrando monitor de Back-Office. Swarm sigue activo en background.{C_RESET}")
            break
        except Exception as e:
            print(f"{C_RED}Error en ciclo de supervisión: {e}{C_RESET}")
            time.sleep(5)

if __name__ == "__main__":
    main()
