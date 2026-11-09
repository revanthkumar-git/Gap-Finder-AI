Write-Host "===================================================" -ForegroundColor Cyan
Write-Host "  Starting Nexqile - WealthAgent Portal" -ForegroundColor Cyan
Write-Host "  Modern Wealth Management & Advisory Architecture" -ForegroundColor Cyan
Write-Host "===================================================" -ForegroundColor Cyan

$root = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "`n[1/2] Starting Python FastAPI Backend on http://127.0.0.1:8000 ..." -ForegroundColor Green
Start-Process cmd -ArgumentList "/k", "cd /d `"$root\backend`" && python run_backend.py"

Write-Host "`n[2/2] Starting React Vite Frontend on http://localhost:5173 ..." -ForegroundColor Green
Start-Process cmd -ArgumentList "/k", "cd /d `"$root\frontend`" && npm.cmd run dev"

Write-Host "`n===================================================" -ForegroundColor Cyan
Write-Host "  Both services launched in separate windows!" -ForegroundColor Yellow
Write-Host "  Frontend:    http://localhost:5173" -ForegroundColor White
Write-Host "  Backend API: http://127.0.0.1:8000/docs" -ForegroundColor White
Write-Host "===================================================`n" -ForegroundColor Cyan
