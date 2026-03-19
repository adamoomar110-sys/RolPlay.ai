$host.UI.RawUI.WindowTitle = "RolPlay.ai v1.0 - Iniciando"
Write-Host "Iniciando RolPlay.ai v1.0 Monolitico..." -ForegroundColor Cyan

# Directorio base
$scriptDir = $PSScriptRoot
if (-not $scriptDir) { $scriptDir = Get-Location }

cd $scriptDir
streamlit run app.py --server.port 8002 --browser.gatherUsageStats false
