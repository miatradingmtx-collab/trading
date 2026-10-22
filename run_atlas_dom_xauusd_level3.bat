@echo off
chcp 65001 > nul
set TF=%1
if "%TF%"=="" set TF=4H
title ATLAS CME DOM LEVEL 3 (MBO) · XAUUSD [%TF%]
cls
python atlas_dom_visualizer_l3.py XAUUSD %TF%
echo.
pause
