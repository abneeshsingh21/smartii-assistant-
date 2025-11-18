# SMARTII Desktop Launcher
# Starts backend and system tray app

Write-Host "🚀 Starting SMARTII Desktop Assistant..." -ForegroundColor Cyan

# Get SMARTII directory
$smartiiDir = Split-Path -Parent $PSScriptRoot
$backendDir = Join-Path $smartiiDir "backend"
$desktopDir = Join-Path $smartiiDir "desktop"

# Check if backend is already running
$backendProcess = Get-Process -Name python -ErrorAction SilentlyContinue | Where-Object { $_.Path -like "*backend*" }
if ($backendProcess) {
    Write-Host "✅ Backend already running" -ForegroundColor Green
} else {
    Write-Host "🔧 Starting backend..." -ForegroundColor Yellow
    Start-Process -FilePath "python" -ArgumentList "app.py" -WorkingDirectory $backendDir -WindowStyle Hidden
    Start-Sleep -Seconds 5
    Write-Host "✅ Backend started" -ForegroundColor Green
}

# Start system tray app
Write-Host "🎤 Starting voice assistant..." -ForegroundColor Yellow
python (Join-Path $desktopDir "smartii_tray.py")
