@echo off
echo Starting LangGraph Studio
echo.

echo Activating backend virtual environment...
call .venv-backend\Scripts\activate.bat
if errorlevel 1 (
    echo ERROR: Failed to activate backend virtual environment
    echo Please run setup_venvs.bat first
    pause
    exit /b 1
)

echo.
echo Starting LangGraph Studio...
echo.
echo Studio will be available at: http://localhost:8123
echo Graph: agent_workflow
echo.
echo To test the workflow, run: python scripts\run_langgraph_studio.py
echo.

langgraph dev

pause
