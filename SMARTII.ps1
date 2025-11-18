# SMARTII One-Click Launcher
# Double-click this file to start SMARTII - NO VS CODE NEEDED!

Write-Host ""
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "  ███████╗███╗   ███╗ █████╗ ██████╗ ████████╗██╗██╗" -ForegroundColor Cyan
Write-Host "  ██╔════╝████╗ ████║██╔══██╗██╔══██╗╚══██╔══╝██║██║" -ForegroundColor Cyan
Write-Host "  ███████╗██╔████╔██║███████║██████╔╝   ██║   ██║██║" -ForegroundColor Cyan
Write-Host "  ╚════██║██║╚██╔╝██║██╔══██║██╔══██╗   ██║   ██║██║" -ForegroundColor Cyan
Write-Host "  ███████║██║ ╚═╝ ██║██║  ██║██║  ██║   ██║   ██║██║" -ForegroundColor Cyan
Write-Host "  ╚══════╝╚═╝     ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝   ╚═╝   ╚═╝╚═╝" -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "  Your Intelligent AI Assistant - Starting..." -ForegroundColor Green
Write-Host ""

# Get directory
$smartiiDir = Split-Path -Parent $PSScriptRoot
$desktopDir = Join-Path $smartiiDir "desktop"

# Run launcher
python (Join-Path $desktopDir "smartii_launcher.py")
