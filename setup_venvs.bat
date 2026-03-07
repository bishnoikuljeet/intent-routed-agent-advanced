@echo off
echo Setting Up Separate Virtual Environments
echo.

echo Cleaning up old virtual environments...
if exist .venv-backend (
    echo Removing old backend venv...
    rmdir /s /q .venv-backend 2>nul
)
if exist frontend\.venv-frontend (
    echo Removing old frontend venv...
    rmdir /s /q frontend\.venv-frontend 2>nul
)

echo.
echo Creating backend virtual environment...
python -m venv .venv-backend
if errorlevel 1 (
    echo ERROR: Failed to create backend virtual environment
    pause
    exit /b 1
)

echo Creating frontend virtual environment...
python -m venv frontend\.venv-frontend
if errorlevel 1 (
    echo ERROR: Failed to create frontend virtual environment
    pause
    exit /b 1
)

echo.
echo Installing backend dependencies...
call .venv-backend\Scripts\activate.bat
if errorlevel 1 (
    echo ERROR: Failed to activate backend virtual environment
    pause
    exit /b 1
)
pip install -e .
if errorlevel 1 (
    echo ERROR: Failed to install backend dependencies
    pause
    exit /b 1
)
call deactivate

echo.
echo Installing frontend dependencies...
call frontend\.venv-frontend\Scripts\activate.bat
if errorlevel 1 (
    echo ERROR: Failed to activate frontend virtual environment
    pause
    exit /b 1
)
pip install -r frontend\requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install frontend dependencies
    pause
    exit /b 1
)
call deactivate

echo.
echo ========================================
echo Setup complete!
echo ========================================
echo.
echo To start services:
echo   - Backend only:  start_backend.bat
echo   - Frontend only: start_frontend.bat  
echo   - Both services: start_both.bat
echo.
pause
