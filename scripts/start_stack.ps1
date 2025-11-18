<#
Smartii Local Stack Launcher (Windows PowerShell)
- Starts services in separate PowerShell windows:
  * Backend (FastAPI) on http://localhost:8000
  * Node Realtime Gateway on http://localhost:8080 (WS: ws://localhost:8080)
  * Go Worker (optional; health on http://localhost:8090/health)
- Performs basic health checks

Usage:
  1) Open PowerShell as your user
  2) Set execution policy for this session if needed:
     Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
  3) Run:
     .\scripts\start_stack.ps1

Requirements:
  - Python (3.9+), Node.js (16+), npm
  - Optional: Go (1.20+) for Go Worker
  - Optional: Redis & Postgres for full pipeline; otherwise backend will fallback
#>
param(
  [switch]$SkipInstall
)

$ErrorActionPreference = 'Stop'

function Write-Info($msg) { Write-Host "[INFO] $msg" -ForegroundColor Cyan }
function Write-Warn($msg) { Write-Host "[WARN] $msg" -ForegroundColor Yellow }
function Write-Err($msg)  { Write-Host "[ERR ] $msg" -ForegroundColor Red }

# Resolve repo root
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Resolve-Path "$ScriptDir\.."
Set-Location $RepoRoot
Write-Info "Repo root: $RepoRoot"

# Helpers
function Test-Command($name) {
  try { $null = Get-Command $name -ErrorAction Stop; return $true } catch { return $false }
}

function Ensure-PythonVenv() {
  $venvPath = Join-Path $RepoRoot 'backend\venv'
  if (!(Test-Path $venvPath)) {
    Write-Info "Creating Python venv at $venvPath"
    python -m venv $venvPath
  } else {
    Write-Info "Python venv exists"
  }
  return $venvPath
}

function Pip-Install($venvPath) {
  $pipExe = Join-Path $venvPath 'Scripts\pip.exe'
  $req = Join-Path $RepoRoot 'requirements.txt'
  if (!(Test-Path $pipExe)) { throw "pip not found at $pipExe" }
  if (!(Test-Path $req)) { throw "requirements.txt not found at $req" }
  Write-Info "Installing Python requirements"
  & $pipExe install -r $req
}

function Npm-Install() {
  $nodeDir = Join-Path $RepoRoot 'node-realtime'
  if (!(Test-Path $nodeDir)) { throw "node-realtime directory not found" }
  Write-Info "Installing npm packages in node-realtime"
  Push-Location $nodeDir
  npm install
  Pop-Location
}

function Start-Backend($venvPath) {
  $pyExe = Join-Path $venvPath 'Scripts\python.exe'
  $backendDir = Join-Path $RepoRoot 'backend'
  $cmd = "cd `"$backendDir`"; & `"$pyExe`" app.py"
  Write-Info "Starting Backend: $cmd"
  Start-Process powershell -ArgumentList "-NoExit","-Command", $cmd | Out-Null
}

function Start-Realtime() {
  $nodeDir = Join-Path $RepoRoot 'node-realtime'
  $cmd = "cd `"$nodeDir`"; npm start"
  Write-Info "Starting Node Realtime: $cmd"
  Start-Process powershell -ArgumentList "-NoExit","-Command", $cmd | Out-Null
}

function Start-Worker() {
  $goDir = Join-Path $RepoRoot 'go-worker'
  $cmd = "cd `"$goDir`"; go run main.go"
  Write-Info "Starting Go Worker: $cmd"
  Start-Process powershell -ArgumentList "-NoExit","-Command", $cmd | Out-Null
}

function Test-Http($url) {
  try {
    $resp = Invoke-WebRequest -UseBasicParsing -Uri $url -TimeoutSec 5
    return $resp.StatusCode
  } catch { return $null }
}

# Pre-flight checks
if (-not (Test-Command python)) { Write-Err "Python not found in PATH. Please install Python 3.9+ from https://www.python.org/downloads/ and re-run."; return }
if (-not (Test-Command npm))    { Write-Err "npm not found in PATH. Please install Node.js (includes npm) from https://nodejs.org/ and re-run."; return }

$hasGo = Test-Command go
if (-not $hasGo) { Write-Warn "Go not found in PATH. Go Worker will be skipped. Install Go from https://go.dev/dl/ to enable." }

# Install dependencies unless skipped
if (-not $SkipInstall) {
  $venvPath = Ensure-PythonVenv
  Pip-Install $venvPath
  Npm-Install
} else {
  $venvPath = Join-Path $RepoRoot 'backend\venv'
  if (!(Test-Path $venvPath)) { Write-Err "Venv missing and SkipInstall set. Re-run without -SkipInstall."; return }
}

# Start services
Start-Backend $venvPath
Start-Realtime
if ($hasGo) { Start-Worker } else { Write-Warn "Skipping Go Worker (Go not installed)" }

Write-Info "Waiting for services to boot..."
Start-Sleep -Seconds 5

$backendStatus = Test-Http 'http://localhost:8000/health'
$realtimeStatus = Test-Http 'http://localhost:8080/health'

if ($backendStatus) { Write-Info "Backend OK: $backendStatus" } else { Write-Warn "Backend health check failed" }
if ($realtimeStatus) { Write-Info "Realtime OK: $realtimeStatus" } else { Write-Warn "Realtime health check failed" }

if ($hasGo) {
  $workerStatus = Test-Http 'http://localhost:8090/health'
  if ($workerStatus) { Write-Info "Worker OK: $workerStatus" } else { Write-Warn "Worker health check failed" }
}

Write-Host "" 
Write-Info "Stack started. Next steps:"
Write-Host " - Connect a WebSocket client to ws://localhost:8080 (should receive realtime.connected)" -ForegroundColor Gray
Write-Host " - Test backend health: curl http://localhost:8000/health" -ForegroundColor Gray
Write-Host " - Test auto tool selection: POST http://localhost:8000/v1/chat with {\"message\":\"weather in Paris\",\"client_id\":\"u1\"}" -ForegroundColor Gray
Write-Host " - Enable developer mode: POST http://localhost:8000/v1/mode {\"developer\":true}" -ForegroundColor Gray
Write-Host " - Query audit logs: GET http://localhost:8000/v1/audit?kind=actions&limit=20" -ForegroundColor Gray
