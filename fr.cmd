@echo off
setlocal

set "ROOT=%~dp0"
if exist "%ROOT%dist\fr\fr.exe" (
    "%ROOT%dist\fr\fr.exe" %*
    exit /b %ERRORLEVEL%
)

python "%ROOT%frcmd.py" %*
