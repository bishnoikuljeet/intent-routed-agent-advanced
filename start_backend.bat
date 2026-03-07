@echo off
echo Starting Backend with Dedicated Virtual Environment
echo.

echo Activating backend virtual environment...
call .venv-backend\Scripts\activate.bat

echo Starting backend server...
python main.py

echo.
echo Backend started!
echo Backend API: http://localhost:8001
echo API Docs: http://localhost:8001/docs
pause
