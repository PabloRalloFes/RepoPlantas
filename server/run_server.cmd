@echo off
REM Script para iniciar el servidor API con HTTPS en Windows
REM Doble clic para ejecutar desde server/ o ejecuta: cd server && run_server.cmd

setlocal enabledelayedexpansion

title API Plantas - Servidor HTTPS
cls

echo.
echo ====================================================================
echo     API PLANTAS - SERVIDOR HTTPS
echo ====================================================================
echo.
echo Selecciona cómo quieres ejecutar el servidor:
echo.
echo 1. HTTPS en Produccion (RECOMENDADO) - Gunicorn
echo 2. HTTP en Produccion - Gunicorn
echo 3. HTTPS en Desarrollo - Flask (con debug)
echo 4. HTTP en Desarrollo - Flask (con debug)
echo 5. Salir
echo.

set /p choice="Opcion (1-5): "

if "%choice%"=="1" (
    echo.
    echo Iniciando servidor HTTPS en produccion...
    echo.
    python ../run_server.py --https
    pause
) else if "%choice%"=="2" (
    echo.
    echo Iniciando servidor HTTP en produccion...
    echo.
    python ../run_server.py
    pause
) else if "%choice%"=="3" (
    echo.
    echo Iniciando servidor HTTPS en desarrollo...
    echo.
    python ../run_server.py --dev --https
    pause
) else if "%choice%"=="4" (
    echo.
    echo Iniciando servidor HTTP en desarrollo...
    echo.
    python ../run_server.py --dev
    pause
) else if "%choice%"=="5" (
    exit /b 0
) else (
    echo Opcion invalida
    pause
    goto start
)

endlocal
