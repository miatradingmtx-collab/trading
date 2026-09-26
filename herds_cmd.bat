@echo off
REM ==============================================================================
REM MIA HERDS CLI - Lanzador para Windows CMD / Terminal
REM ==============================================================================
title MIA HERDS TERMINAL - Inter-Agent Live Deliberation
color 0A
python mia_herds_cli.py %*
if errorlevel 1 (
    echo.
    echo [!] Si no tienes websockets instalado, ejecuta: pip install websockets
    pause
)
