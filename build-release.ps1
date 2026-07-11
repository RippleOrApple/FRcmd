$ErrorActionPreference = "Stop"

$root = $PSScriptRoot
$releaseDir = Join-Path $root "release"
$tempDir = Join-Path $root ".release-build"
$entryFile = Join-Path $tempDir "fr_release_entry.py"
$workDir = Join-Path $tempDir "pyinstaller-work"

Push-Location $root
try {
    if (Test-Path -LiteralPath $tempDir) {
        Remove-Item -LiteralPath $tempDir -Recurse -Force
    }
    if (Test-Path -LiteralPath $releaseDir) {
        Remove-Item -LiteralPath $releaseDir -Recurse -Force
    }

    New-Item -ItemType Directory -Force -Path $tempDir | Out-Null
    New-Item -ItemType Directory -Force -Path $releaseDir | Out-Null

    @'
from __future__ import annotations

import ctypes
import os
import shutil
import sys
from pathlib import Path

import frcmd


APP_DIR = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local")) / "Programs" / "FRcmd"
APP_EXE = APP_DIR / "fr.exe"


def current_exe() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve()
    return Path(__file__).resolve()


def same_path(left: Path, right: Path) -> bool:
    try:
        return str(left.resolve()).casefold() == str(right.resolve()).casefold()
    except OSError:
        return str(left).casefold() == str(right).casefold()


def add_user_path(path: Path) -> bool:
    if os.name != "nt":
        return False

    import winreg

    path_text = str(path)
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment", 0, winreg.KEY_READ | winreg.KEY_WRITE) as key:
        try:
            value, value_type = winreg.QueryValueEx(key, "Path")
        except FileNotFoundError:
            value = ""
            value_type = winreg.REG_EXPAND_SZ

        parts = [item for item in value.split(";") if item]
        if any(item.casefold() == path_text.casefold() for item in parts):
            return False

        winreg.SetValueEx(key, "Path", 0, value_type, ";".join([*parts, path_text]))

    ctypes.windll.user32.SendMessageTimeoutW(0xFFFF, 0x001A, 0, "Environment", 0x0002, 5000, None)
    return True


def install_if_needed() -> bool:
    if os.environ.get("FRCMD_HOME"):
        return False

    source = current_exe()
    if same_path(source, APP_EXE):
        os.environ["FRCMD_HOME"] = str(APP_DIR)
        return False

    APP_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, APP_EXE)
    add_user_path(APP_DIR)
    os.environ["FRCMD_HOME"] = str(APP_DIR)
    frcmd.bootstrap_default_config()

    print("FRcmd \u5df2\u5b89\u88c5\u5230\uff1a" + str(APP_DIR))
    print("\u8bf7\u91cd\u65b0\u6253\u5f00\u4e00\u4e2a\u7ec8\u7aef\uff0c\u7136\u540e\u8fd0\u884c\uff1a")
    print("  fr QQ")
    return True


def main() -> int:
    installed_now = install_if_needed() if getattr(sys, "frozen", False) else False
    os.environ.setdefault("FRCMD_HOME", str(APP_DIR))
    if installed_now and len(sys.argv) == 1:
        return 0
    return frcmd.main(sys.argv[1:])


if __name__ == "__main__":
    raise SystemExit(main())
'@ | Set-Content -LiteralPath $entryFile -Encoding UTF8

    python -m PyInstaller `
        --noconfirm `
        --clean `
        --onefile `
        --name fr `
        --paths $root `
        --distpath $releaseDir `
        --workpath $workDir `
        --specpath $tempDir `
        $entryFile

    if ($LASTEXITCODE -ne 0) {
        throw "PyInstaller failed with exit code $LASTEXITCODE."
    }

    $outputExe = Join-Path $releaseDir "fr.exe"
    if (-not (Test-Path -LiteralPath $outputExe)) {
        throw "Release executable was not created: $outputExe"
    }

    Write-Host "Built release executable: $outputExe"
    Write-Host "First run installs FRcmd to: %LOCALAPPDATA%\Programs\FRcmd"
} finally {
    Pop-Location
    if (Test-Path -LiteralPath $tempDir) {
        Remove-Item -LiteralPath $tempDir -Recurse -Force
    }
}
