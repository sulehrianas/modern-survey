@echo off
cd /d "%~dp0"
echo Installing Web Dependencies...
pip install streamlit streamlit-folium
echo Starting Modern Survey Web Edition...
python -m streamlit run streamlit_app.py
pause