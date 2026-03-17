@echo off
title RolPlay.ai - Conector Nube
echo ==========================================
echo    ROLPLAY.AI - PUENTE A LA NUBE
echo ==========================================
echo.
echo Este script creara un tunel gratuito para que
echo tu link de Streamlit Cloud pueda usar tu PC.
echo.
echo REQUISITOS:
echo 1. Tener Ollama abierto.
echo 2. No cerrar esta ventana mientras uses el link.
echo.
echo Presiona una tecla para activar el tunel...
pause > nul
echo Activando...
cmd /c npx localtunnel --port 11434
pause
