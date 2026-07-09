$ErrorActionPreference = "Stop"

$root = $PSScriptRoot
Push-Location $root
try {
    python -m PyInstaller --noconfirm --onedir --name fr frcmd.py

    $bundleDir = Join-Path $root "dist\fr"
    $flatDist = Join-Path $root "dist"
    Get-ChildItem -LiteralPath $bundleDir -Force | ForEach-Object {
        $target = Join-Path $flatDist $_.Name
        if (Test-Path -LiteralPath $target) {
            Remove-Item -LiteralPath $target -Recurse -Force
        }
        Move-Item -LiteralPath $_.FullName -Destination $flatDist -Force
    }
    Remove-Item -LiteralPath $bundleDir -Force

    Write-Host "Built: $(Join-Path $root 'dist\fr.exe')"
} finally {
    Pop-Location
}
