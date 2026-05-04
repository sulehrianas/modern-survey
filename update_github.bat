@echo off
cd /d "%~dp0"

echo Staging changes...
git add .

set /p msg="Enter a description of your changes: "
if "%msg%"=="" set msg="Update Modern Survey application and UI components"

echo Committing changes...
git commit -m "%msg%"

echo Pushing to GitHub...
git push origin main

if %errorlevel% neq 0 (
    echo.
    echo Error: Push failed. Ensure your remote 'origin' is configured and you have internet access.
) else (
    echo.
    echo Success: GitHub repository updated!
)
pause