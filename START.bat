@echo off
setlocal
cd /d %~dp0
echo ==========================================
echo    ROLPLAY.AI v1.0 - LAUNCHER
echo ==========================================

rem Check for Python
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo ERROR: Python no encontrado.
    pause
    exit /b 1
)

echo [+] Iniciando Simulador (Streamlit)...
streamlit run app.py --server.port 8002 --browser.gatherUsageStats false

pause
