@echo off
setlocal

cd /d "%~dp0"

echo ==========================================
echo YouTube Exporter - Setup and Start
echo ==========================================

python --version >nul 2>&1
if errorlevel 1 (
  echo Python not found. Please install Python 3.10+ and try again.
  pause
  exit /b 1
)

echo Installing dependencies...
python -m pip install --upgrade pip >nul 2>&1
python -m pip install -r requirements.txt
if errorlevel 1 (
  echo Failed to install requirements.
  pause
  exit /b 1
)

echo Starting app...
python -m youtube_exporter.main
pause
