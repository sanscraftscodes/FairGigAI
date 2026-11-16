@echo off
echo ========================================================
echo Launching FairGig AI (Backend + Frontend)
echo ========================================================
echo Starting Backend in separate window...
start "FairGig AI Backend" cmd /k "start_backend.bat"

echo Starting Frontend in separate window...
start "FairGig AI Frontend" cmd /k "start_frontend.bat"

echo.
echo Both servers launched!
echo Backend:  http://127.0.0.1:8000 (Docs: http://127.0.0.1:8000/docs)
echo Frontend: http://localhost:5173
echo.
pause
