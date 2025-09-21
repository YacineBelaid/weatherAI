@echo off
echo Starting Weather AI - Full Stack
echo ==================================================

echo Starting Backend Services...
start "Backend" cmd /k "python start.py --mode backend"

echo Waiting for backend to start...
timeout /t 8 /nobreak > nul

echo Starting Frontend...
start "Frontend" cmd /k "cd frontend && npm start"

echo.
echo Both services started!
echo URLs:
echo    Frontend: http://localhost:3000
echo    Backend:  http://localhost:8000
echo.
echo Press any key to stop all services
pause > nul

echo Stopping all services...
taskkill /F /IM python.exe 2>nul
taskkill /F /IM node.exe 2>nul
echo All services stopped!
