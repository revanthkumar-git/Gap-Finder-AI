@echo off
setlocal
cd /d "%~dp0"
echo ===================================================
echo   Starting Nexqile - WealthAgent Portal
echo   Modern Wealth Management & Advisory Architecture
echo ===================================================

echo.
echo [1/2] Starting Python FastAPI Backend on http://127.0.0.1:8000 ...
start "Nexqile Backend" cmd /k "cd /d "%~dp0backend" && python run_backend.py"

echo.
echo [2/2] Starting React Vite Frontend on http://localhost:5173 ...
start "Nexqile Frontend" cmd /k "cd /d "%~dp0frontend" && npm.cmd run dev"

echo.
echo ===================================================
echo   Both services are launching in separate windows.
echo   Frontend: http://localhost:5173
echo   Backend API: http://127.0.0.1:8000/docs
echo ===================================================
echo.
pause
