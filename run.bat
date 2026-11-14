@echo off
setlocal
cd /d "%~dp0"
set "PYTHONPATH=%~dp0src"
set "PYTHONDONTWRITEBYTECODE=1"
where py >nul 2>&1
if errorlevel 1 goto use_python
py -3 -B -m apkgraph %*
exit /b %errorlevel%
:use_python
python -B -m apkgraph %*
exit /b %errorlevel%
