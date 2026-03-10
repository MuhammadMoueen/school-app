@echo off
REM Quick Push to GitHub - Windows Batch Script
REM Double-click this file to push changes to GitHub

echo.
echo ========================================
echo   Auto Push to GitHub
echo ========================================
echo.

cd /d "%~dp0"

REM Check if git is initialized
if not exist ".git" (
    echo Error: Git repository not found!
    pause
    exit /b 1
)

REM Add all changes
echo Adding changes...
git add .

REM Check if there are changes to commit
git diff-index --quiet HEAD --
if %errorlevel% equ 0 (
    echo No changes to commit.
    pause
    exit /b 0
)

REM Get commit message from user or use default
set /p message="Enter commit message (or press Enter for default): "
if "%message%"=="" set message=Update: School Management System changes

REM Commit changes
echo Committing changes...
git commit -m "%message%"

REM Push to GitHub
echo Pushing to GitHub...
git push origin main

if %errorlevel% equ 0 (
    echo.
    echo ========================================
    echo   Success! Changes pushed to GitHub
    echo ========================================
) else (
    echo.
    echo ========================================
    echo   Error: Failed to push to GitHub
    echo ========================================
)

echo.
pause
