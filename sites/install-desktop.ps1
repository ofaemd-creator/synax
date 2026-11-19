$ErrorActionPreference = "Stop"
Write-Host "==================================================================" -ForegroundColor Cyan
Write-Host "  SYNAX Studio & 3D Pixar-Tycoon Agent Office v4.0 — Windows Setup" -ForegroundColor Cyan
Write-Host "==================================================================" -ForegroundColor Cyan
$InstallDir = Join-Path $env:USERPROFILE ".synax-desktop"
if (Test-Path $InstallDir) { Remove-Item -Recurse -Force $InstallDir }
git clone --depth 1 https://github.com/ofaemd-creator/synax-agent-office.git $InstallDir
Start-Process python -ArgumentList "$InstallDir\src\synax\agent_office.py --serve --port 8795" -WindowStyle Hidden
Start-Sleep -Seconds 2
Start-Process "http://127.0.0.1:8795"
Write-Host "SUCCESS! SYNAX Studio v4.0 is running on your computer at http://127.0.0.1:8795" -ForegroundColor Green
