@echo off
cd /d "%~dp0frontend"
echo Starting frontend dev server (Vite)...
call npm run dev
pause
