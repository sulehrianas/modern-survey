@echo off
echo Installing PyInstaller...
pip install pyinstaller

echo Cleaning up previous builds...
rmdir /s /q build
rmdir /s /q dist
del /f /q "Modern Survey.spec"

echo Building Modern Survey...
:: --noconsole: Hides the black command window
:: --onefile: Bundles everything into a single .exe file
:: --add-data: Includes the 'ui' folder (for styles) inside the exe
pyinstaller --noconsole --onefile --name "Modern Survey" --add-data "ui;ui" --hidden-import="PyQt6" --hidden-import="pandas" --hidden-import="numpy" --hidden-import="pyproj" main.py

echo.
echo Build Complete! You can find "Modern Survey.exe" in the "dist" folder.
pause