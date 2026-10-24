@echo off
cd /d "%~dp0frontend"
if not exist "node_modules" (
  echo Run setup.ps1 first.
  pause
  exit /b 1
)
npm run dev
pause
