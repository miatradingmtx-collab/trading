@echo off
title MIA WATCHDOG SUPERVISOR & HERDS T1-T6 (SRE Sentinel CLI)
color 0B
cls
echo ==============================================================================
echo        MIA WATCHDOG SUPERVISOR - CONSOLA DE AUDITORIA Y HERDS T1-T6
echo ==============================================================================
echo  Front-Office: Trading Herds (TIDAL, NORO, ZEPHR, LUMEN, RUNE, TF, ATLAS)
echo  Back-Office:  Watchdog Supervisor (T1 DBA, T2 Dev, T3 SRE, T4 Cache, T5 FinOps, T6 UI)
echo ==============================================================================
echo.
cd /d "%~dp0"
python mia_ops_cli.py
pause
