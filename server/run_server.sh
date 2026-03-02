#!/bin/bash

# Script para iniciar el servidor API con HTTPS en Linux/Mac
# Ejecuta: chmod +x server/run_server.sh && cd server && ./run_server.sh
# O desde raíz: chmod +x server/run_server.sh && ./server/run_server.sh

clear

echo ""
echo "===================================================================="
echo "     API PLANTAS - SERVIDOR HTTPS"
echo "===================================================================="
echo ""
echo "Selecciona cómo quieres ejecutar el servidor:"
echo ""
echo "1. HTTPS en Produccion (RECOMENDADO) - Gunicorn"
echo "2. HTTP en Produccion - Gunicorn"
echo "3. HTTPS en Desarrollo - Flask (con debug)"
echo "4. HTTP en Desarrollo - Flask (con debug)"
echo "5. Salir"
echo ""

read -p "Opcion (1-5): " choice

case $choice in
    1)
        echo ""
        echo "Iniciando servidor HTTPS en produccion..."
        echo ""
        python ../run_server.py --https
        ;;
    2)
        echo ""
        echo "Iniciando servidor HTTP en produccion..."
        echo ""
        python ../run_server.py
        ;;
    3)
        echo ""
        echo "Iniciando servidor HTTPS en desarrollo..."
        echo ""
        python ../run_server.py --dev --https
        ;;
    4)
        echo ""
        echo "Iniciando servidor HTTP en desarrollo..."
        echo ""
        python ../run_server.py --dev
        ;;
    5)
        exit 0
        ;;
    *)
        echo "Opcion invalida"
        ;;
esac
