# SMARTII Auto-Start Setup
# Run this once to setup SMARTII to start on Windows boot

Write-Host "⚙️ Setting up SMARTII Auto-Start..." -ForegroundColor Cyan

# Get paths
$smartiiDir = Split-Path -Parent $PSScriptRoot
$desktopDir = Join-Path $smartiiDir "desktop"
$startupScript = Join-Path $desktopDir "start_smartii.ps1"

# Create startup task
$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-ExecutionPolicy Bypass -WindowStyle Hidden -File `"$startupScript`""
$trigger = New-ScheduledTaskTrigger -AtLogon
$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Highest
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable

$taskName = "SMARTII Assistant"

# Remove existing task if present
$existingTask = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
if ($existingTask) {
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
    Write-Host "🗑️ Removed existing task" -ForegroundColor Yellow
}

# Register new task
Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Principal $principal -Settings $settings | Out-Null

Write-Host ""
Write-Host "✅ SMARTII Auto-Start Setup Complete!" -ForegroundColor Green
Write-Host ""
Write-Host "What this does:" -ForegroundColor Cyan
Write-Host "  • SMARTII will start automatically when you log in" -ForegroundColor White
Write-Host "  • Backend runs in background 24/7" -ForegroundColor White
Write-Host "  • Voice assistant always listening" -ForegroundColor White
Write-Host "  • Works even when screen is locked" -ForegroundColor White
Write-Host ""
Write-Host "Usage:" -ForegroundColor Cyan
Write-Host "  • Say 'Hey SMARTII' to activate" -ForegroundColor White
Write-Host "  • Press Ctrl+Space for manual activation" -ForegroundColor White
Write-Host "  • Right-click system tray icon for settings" -ForegroundColor White
Write-Host ""
Write-Host "To start now: Run .\start_smartii.ps1" -ForegroundColor Yellow
Write-Host ""
