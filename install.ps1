$ErrorActionPreference = "Stop"

$installDir = $PSScriptRoot
$launcher = Join-Path $installDir "fr.cmd"

if (-not (Test-Path -LiteralPath $launcher)) {
    throw "Missing launcher: $launcher"
}

$currentPath = [Environment]::GetEnvironmentVariable("Path", "User")
if ($null -eq $currentPath) {
    $currentPath = ""
}

$normalizedInstallDir = $installDir.TrimEnd("\")
$pathItems = $currentPath -split ";" | Where-Object { $_ -ne "" }
$alreadyInstalled = $false

foreach ($item in $pathItems) {
    if ($item.TrimEnd("\").Equals($normalizedInstallDir, [StringComparison]::OrdinalIgnoreCase)) {
        $alreadyInstalled = $true
        break
    }
}

if (-not $alreadyInstalled) {
    $newPath = if ($currentPath.Trim()) { "$currentPath;$installDir" } else { $installDir }
    [Environment]::SetEnvironmentVariable("Path", $newPath, "User")
    $env:Path = "$env:Path;$installDir"
    Write-Host "Added to user PATH: $installDir"
} else {
    Write-Host "Already in user PATH: $installDir"
}

python (Join-Path $installDir "frcmd.py") --install

$signature = @"
using System;
using System.Runtime.InteropServices;

public static class EnvironmentBroadcaster {
    [DllImport("user32.dll", SetLastError = true, CharSet = CharSet.Auto)]
    public static extern IntPtr SendMessageTimeout(
        IntPtr hWnd,
        uint Msg,
        UIntPtr wParam,
        string lParam,
        uint fuFlags,
        uint uTimeout,
        out UIntPtr lpdwResult);
}
"@

Add-Type -TypeDefinition $signature -ErrorAction SilentlyContinue
$result = [UIntPtr]::Zero
[EnvironmentBroadcaster]::SendMessageTimeout(
    [IntPtr]0xffff,
    0x001A,
    [UIntPtr]::Zero,
    "Environment",
    0x0002,
    5000,
    [ref]$result
) | Out-Null

Write-Host ""
Write-Host "Install complete. Open a new terminal, then run:"
Write-Host "  FR QQ"
