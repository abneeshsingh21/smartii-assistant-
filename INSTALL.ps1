# SMARTII Complete Installation Script
# Run this ONCE to setup everything

Write-Host ""
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "  SMARTII Complete Installation & Setup" -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ""

$smartiiDir = $PSScriptRoot
$backendDir = Join-Path $smartiiDir "backend"
$frontendDir = Join-Path $smartiiDir "frontend-v2"
$desktopDir = Join-Path $smartiiDir "desktop"

Write-Host "📂 Installation Directory: $smartiiDir" -ForegroundColor Yellow
Write-Host ""

# Step 1: Install Python packages
Write-Host "📦 Step 1/5: Installing Python packages..." -ForegroundColor Cyan
try {
    # Backend packages
    Write-Host "   Installing backend dependencies..."
    Set-Location $backendDir
    pip install -r requirements.txt --quiet
    
    # Desktop packages
    Write-Host "   Installing desktop assistant packages..."
    Set-Location $desktopDir
    pip install -r requirements.txt --quiet
    
    Write-Host "✅ Python packages installed" -ForegroundColor Green
} catch {
    Write-Host "⚠️ Some packages may have failed, but continuing..." -ForegroundColor Yellow
}

# Step 2: Install Node.js packages (if needed)
Write-Host ""
Write-Host "📦 Step 2/5: Checking frontend dependencies..." -ForegroundColor Cyan
Set-Location $frontendDir
if (!(Test-Path "node_modules")) {
    Write-Host "   Installing Node.js packages (this may take a few minutes)..."
    npm install --silent
    Write-Host "✅ Frontend packages installed" -ForegroundColor Green
} else {
    Write-Host "✅ Frontend packages already installed" -ForegroundColor Green
}

# Step 3: Create desktop shortcuts
Write-Host ""
Write-Host "🔗 Step 3/5: Creating desktop shortcuts..." -ForegroundColor Cyan

$desktopPath = [Environment]::GetFolderPath("Desktop")
$startMenuPath = [Environment]::GetFolderPath("StartMenu")

# Create batch file shortcut on desktop
$shortcutPath = Join-Path $desktopPath "SMARTII.lnk"
$batchFile = Join-Path $smartiiDir "SMARTII.bat"

$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut($shortcutPath)
$shortcut.TargetPath = $batchFile
$shortcut.WorkingDirectory = $smartiiDir
$shortcut.IconLocation = "shell32.dll,23"
$shortcut.Description = "Start SMARTII AI Assistant"
$shortcut.Save()

Write-Host "✅ Desktop shortcut created" -ForegroundColor Green

# Step 4: Setup auto-start
Write-Host ""
Write-Host "🚀 Step 4/5: Setting up auto-start on Windows boot..." -ForegroundColor Cyan

$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-ExecutionPolicy Bypass -WindowStyle Hidden -File `"$(Join-Path $smartiiDir 'SMARTII.ps1')`""
$trigger = New-ScheduledTaskTrigger -AtLogon
$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Highest
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable

$taskName = "SMARTII Assistant"

# Remove existing task
$existingTask = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
if ($existingTask) {
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
}

# Register new task
Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Principal $principal -Settings $settings | Out-Null

Write-Host "✅ Auto-start configured" -ForegroundColor Green

# Step 5: Configure Windows Firewall (if needed)
Write-Host ""
Write-Host "🛡️ Step 5/5: Configuring firewall rules..." -ForegroundColor Cyan
try {
    # Allow Python through firewall
    netsh advfirewall firewall add rule name="SMARTII Backend" dir=in action=allow program="python.exe" enable=yes | Out-Null
    netsh advfirewall firewall add rule name="SMARTII Backend" dir=out action=allow program="python.exe" enable=yes | Out-Null
    Write-Host "✅ Firewall rules added" -ForegroundColor Green
} catch {
    Write-Host "⚠️ Run as Administrator to add firewall rules" -ForegroundColor Yellow
}

# Done!
Write-Host ""
Write-Host "================================================================" -ForegroundColor Green
Write-Host "  ✅ SMARTII Installation Complete!" -ForegroundColor Green
Write-Host "================================================================" -ForegroundColor Green
Write-Host ""
Write-Host "🎯 What's Ready:" -ForegroundColor Cyan
Write-Host "   ✅ All packages installed" -ForegroundColor White
Write-Host "   ✅ Desktop shortcut created" -ForegroundColor White
Write-Host "   ✅ Auto-start on boot enabled" -ForegroundColor White
Write-Host "   ✅ System tray integration" -ForegroundColor White
Write-Host "   ✅ Voice commands (works when locked)" -ForegroundColor White
Write-Host ""
Write-Host "🚀 To Start SMARTII:" -ForegroundColor Cyan
Write-Host "   • Double-click 'SMARTII' icon on your desktop" -ForegroundColor White
Write-Host "   • Or just restart your computer (auto-starts)" -ForegroundColor White
Write-Host ""
Write-Host "🎤 Voice Activation:" -ForegroundColor Cyan
Write-Host "   • Say 'Hey SMARTII' to wake up" -ForegroundColor White
Write-Host "   • Press Ctrl+Space for manual activation" -ForegroundColor White
Write-Host ""
Write-Host "💡 Next Steps:" -ForegroundColor Cyan
Write-Host "   1. Double-click SMARTII desktop icon to start" -ForegroundColor Yellow
Write-Host "   2. Wait for system tray icon (bottom-right)" -ForegroundColor Yellow
Write-Host "   3. Say 'Hey SMARTII, hello!' to test" -ForegroundColor Yellow
Write-Host ""
Write-Host "Press any key to start SMARTII now..." -ForegroundColor Green
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

# Start SMARTII
Write-Host ""
Write-Host "🚀 Starting SMARTII..." -ForegroundColor Cyan
Start-Process -FilePath $batchFile -WorkingDirectory $smartiiDir
