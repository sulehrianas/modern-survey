@echo OFF
echo ###################################
echo #   Building Modern Survey EXE    #
echo ###################################

REM This script builds a standalone executable for the Modern Survey application.
REM It automatically finds the necessary data files for the 'pyproj' library.

REM Ensure pyinstaller is installed
pip install pyinstaller

REM Find the pyproj data directory
echo.
echo [+] Finding pyproj data directory...
for /f "delims=" %%i in ('python -c "import os, pyproj; print(pyproj.datadir.get_data_dir())"') do (
    set PYPROJ_DATA=%%i
)

if not defined PYPROJ_DATA (
    echo [!] ERROR: Could not find the pyproj data directory.
    echo [!] Make sure 'pyproj' is installed ('pip install -r requirements.txt').
    pause
    exit /b
)

echo [!] Found pyproj data at: %PYPROJ_DATA%
echo.

REM Run PyInstaller to create the .exe in a 'dist' folder
echo [+] Running PyInstaller...
pyinstaller --name "ModernSurvey" --onefile --windowed --add-data "%PYPROJ_DATA%;pyproj" main.py

echo.
echo ###################################
echo #           Build Done            #
echo ###################################
echo Your executable can be found in the 'dist' folder.
pause