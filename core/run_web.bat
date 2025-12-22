@echo off
cd /d "%~dp0"
cd ..
echo Installing dependencies...
pip install -r requirements.txt
echo Starting Modern Survey Web Edition...
python -m streamlit run streamlit_app.py
pause