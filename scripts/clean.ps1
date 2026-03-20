# ============================================
# VidMark - Cleanup Script (PowerShell)
# Removes build artifacts, caches, temp files
# ============================================

$ErrorActionPreference = "SilentlyContinue"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectDir = Split-Path -Parent $ScriptDir

Set-Location $ProjectDir

Write-Host ""
Write-Host "========================================"
Write-Host " VidMark - Cleanup"
Write-Host "========================================"
Write-Host ""

Write-Host "[1/7] Removing __pycache__ directories..."
Get-ChildItem -Path . -Directory -Recurse -Filter "__pycache__" | ForEach-Object {
    Write-Host "  Removing: $($_.FullName)"
    Remove-Item -Recurse -Force $_.FullName
}

Write-Host "[2/7] Removing .pyc and .pyo files..."
Get-ChildItem -Path . -Recurse -Include "*.pyc", "*.pyo" | Remove-Item -Force

Write-Host "[3/7] Removing build/dist directories..."
@("build", "dist") | ForEach-Object {
    if (Test-Path $_) {
        Write-Host "  Removing: $_"
        Remove-Item -Recurse -Force $_
    }
}

Write-Host "[4/7] Removing .spec files..."
Get-ChildItem -Path . -Filter "*.spec" | Remove-Item -Force

Write-Host "[5/7] Removing .egg-info directories..."
Get-ChildItem -Path . -Directory -Recurse -Filter "*.egg-info" | ForEach-Object {
    Write-Host "  Removing: $($_.FullName)"
    Remove-Item -Recurse -Force $_.FullName
}

Write-Host "[6/7] Removing pytest/mypy cache..."
@(".pytest_cache", ".mypy_cache") | ForEach-Object {
    Get-ChildItem -Path . -Directory -Recurse -Filter $_ | ForEach-Object {
        Write-Host "  Removing: $($_.FullName)"
        Remove-Item -Recurse -Force $_.FullName
    }
}

Write-Host "[7/7] Removing user temp/settings directories..."
$TempDir = Join-Path $env:USERPROFILE ".vws_temp"
$SettingsDir = Join-Path $env:USERPROFILE ".vws_settings"

if (Test-Path $TempDir) {
    Write-Host "  Removing: $TempDir"
    Remove-Item -Recurse -Force $TempDir
}
if (Test-Path $SettingsDir) {
    Write-Host "  Removing: $SettingsDir"
    Remove-Item -Recurse -Force $SettingsDir
}

Write-Host ""
Write-Host "========================================"
Write-Host " Cleanup complete!"
Write-Host "========================================"
Write-Host ""

Read-Host "Press Enter to exit"