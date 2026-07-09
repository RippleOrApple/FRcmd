$ErrorActionPreference = "Stop"

$root = $PSScriptRoot
Push-Location $root
try {
    python -m PyInstaller --onedir --name fr frcmd.py
    Write-Host "Built: $(Join-Path $root 'dist\fr\fr.exe')"
} finally {
    Pop-Location
}
