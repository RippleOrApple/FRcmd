@echo off
setlocal

set "ROOT=%~dp0"
set "FRCMD_HOME=%ROOT%"

if exist "%ROOT%dist\fr.exe" (
    "%ROOT%dist\fr.exe" %*
    exit /b %ERRORLEVEL%
)

python "%ROOT%frcmd.py" %*
