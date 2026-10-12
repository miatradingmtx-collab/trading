@echo off
chcp 65001 > nul
:MENU
title MIA TRADING ENGINE · PANEL DE CONTROL DE MONITORES CLI
cls
echo ========================================================================
echo        MIA TRADING ENGINE · MENÚ DE MONITORES CLI EN TIEMPO REAL
echo ========================================================================
echo.
echo  [1] Monitor 3D de Vectores 20D TensorFlow (tensor_matrix_monitor.py)
echo  [2] Libro de Ordenes DOM Level 2 - EURUSD (atlas_dom_visualizer.py)
echo  [3] Libro de Ordenes DOM Level 2 - GBPUSD (atlas_dom_visualizer.py)
echo  [4] Libro de Ordenes DOM Level 2 - XAUUSD (atlas_dom_visualizer.py)
echo  [5] Libro de Ordenes DOM Level 2 - GBPJPY (atlas_dom_visualizer.py)
echo  [6] Libro de Ordenes DOM Level 2 - AUDUSD (atlas_dom_visualizer.py)
echo  [7] Iniciar Swarm REST (7 Herds + TensorFlow + ATLAS en Vivo)
echo  [8] Salir
echo.
echo ========================================================================
set /p OPCION="Selecciona una opción [1-8]: "

if "%OPCION%"=="1" (
    cls
    python tensor_matrix_monitor.py
    pause
    goto MENU
)
if "%OPCION%"=="2" (
    cls
    python atlas_dom_visualizer.py EURUSD
    pause
    goto MENU
)
if "%OPCION%"=="3" (
    cls
    python atlas_dom_visualizer.py GBPUSD
    pause
    goto MENU
)
if "%OPCION%"=="4" (
    cls
    python atlas_dom_visualizer.py XAUUSD
    pause
    goto MENU
)
if "%OPCION%"=="5" (
    cls
    python atlas_dom_visualizer.py GBPJPY
    pause
    goto MENU
)
if "%OPCION%"=="6" (
    cls
    python atlas_dom_visualizer.py AUDUSD
    pause
    goto MENU
)
if "%OPCION%"=="7" (
    cls
    python mia_master_swarm_rest.py
    pause
    goto MENU
)
if "%OPCION%"=="8" (
    exit
)

echo Opción no válida. Intenta de nuevo.
timeout /t 2 > nul
goto MENU
