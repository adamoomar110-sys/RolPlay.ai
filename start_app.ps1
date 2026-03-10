$host.UI.RawUI.WindowTitle = "RolPlay.ai - Servidores"
Write-Host "Iniciando Servidor API Backend..." -ForegroundColor Cyan
Start-Process powershell.exe -ArgumentList "-NoExit -Command `"cd backend; uvicorn main:app --host 0.0.0.0 --port 8000`"" -WindowStyle Minimized

Write-Host "Iniciando Interfaz React Frontend..." -ForegroundColor Cyan 
Start-Process powershell.exe -ArgumentList "-NoExit -Command `"cd frontend; npm run dev`"" -WindowStyle Minimized

Write-Host "Iniciando navegador web..." -ForegroundColor Green
Start-Sleep -Seconds 3
Start-Process "http://localhost:5173"
