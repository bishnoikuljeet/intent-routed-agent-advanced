@echo off
echo Starting Frontend Service
echo.

echo Activating Frontend Virtual Environment...
call frontend\.venv-frontend\Scripts\activate.bat

echo Changing to Frontend Directory...
cd frontend

echo Starting Streamlit Frontend...
echo Frontend will be available at: http://localhost:8501
echo.
streamlit run app.py

echo.
echo Frontend stopped!
pause
