@echo off
setlocal
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" goto install
where py >nul 2>nul
if errorlevel 1 goto no_interpreter
py -3.11 --version >nul 2>nul
if not errorlevel 1 (
  py -3.11 -m venv .venv
  goto install
)
py -3.12 --version >nul 2>nul
if not errorlevel 1 (
  py -3.12 -m venv .venv
  goto install
)
py -3.13 --version >nul 2>nul
if not errorlevel 1 (
  py -3.13 -m venv .venv
  goto install
)
goto no_interpreter
:install
.venv\Scripts\python.exe --version
.venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 goto fail
if not exist .env copy .env.example .env >nul
echo.
echo Setup successful. Run configure-groq.bat or configure-hf.bat, then start.bat.
pause
exit /b 0
:no_interpreter
echo Python 3.11, 3.12 or 3.13 is required. Do not use Python 3.15 beta.
pause
exit /b 1
:fail
echo Installation failed. Check the errors above.
pause
exit /b 1
