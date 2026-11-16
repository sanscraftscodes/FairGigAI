@echo off
echo ========================================================
echo Starting FairGig AI Backend (FastAPI + ML Services)
echo ========================================================
set PYTHONIOENCODING=utf-8
cd backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
pause
