@echo off
echo Starting Both Services with Separate Virtual Environments
echo.

echo Starting Backend...
start "Backend Server" cmd /k "call .venv-backend\Scripts\activate.bat && python main.py"

echo Waiting for backend to initialize (loading RAG documents)...
echo This may take 40-50 seconds on first startup...
timeout /t 50 /nobreak

echo Starting Frontend...
start "Frontend Server" cmd /k "call frontend\.venv-frontend\Scripts\activate.bat && cd frontend && streamlit run app.py"

echo.
echo Both services started!
echo Frontend: http://localhost:8501
echo Backend:  http://localhost:8001
echo.
echo Press any key to exit...
pause
