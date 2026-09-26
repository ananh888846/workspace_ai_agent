param(
    [ValidateSet("start","stop","status","health")]
    [string]$Action = "status",
    [string]$WebPath = $env:WORKSPACE_AI_AGENT_WEB_PATH
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
$VenvPython = Join-Path $RepoRoot ".venv\Scripts\python.exe"
$PidDir = Join-Path $RepoRoot ".local-run"
$AgentPidFile = Join-Path $PidDir "agent.pid"
$WebPidFile = Join-Path $PidDir "web.pid"

function Write-Info($Message) { Write-Host "[local-server] $Message" }
function Get-PidFromFile($Path) {
    if (Test-Path $Path) {
        $raw = (Get-Content $Path -Raw).Trim()
        if ($raw -match "^\d+$") { return [int]$raw }
    }
    return $null
}
function Test-Port($Port) {
    return $null -ne (Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue)
}
function Remove-StalePid($Path) {
    $processId = Get-PidFromFile $Path
    if ($null -ne $processId -and -not (Get-Process -Id $processId -ErrorAction SilentlyContinue)) { Remove-Item $Path -Force -ErrorAction SilentlyContinue }
}
function Start-Agent {
    if (Test-Port 8000) { Write-Info "Agent port 8000 is already listening."; return }
    if (-not (Test-Path $VenvPython)) { throw "Missing .venv Python: $VenvPython" }
    New-Item -ItemType Directory -Force -Path $PidDir | Out-Null
    $process = Start-Process -FilePath $VenvPython -WorkingDirectory $RepoRoot -ArgumentList "-m uvicorn app.main:app --host 127.0.0.1 --port 8000" -PassThru
    Set-Content -Path $AgentPidFile -Value $process.Id
    Write-Info "Started Agent PID $($process.Id) on 127.0.0.1:8000."
}
function Start-Web {
    if ([string]::IsNullOrWhiteSpace($WebPath)) { Write-Info "WORKSPACE_AI_AGENT_WEB_PATH is not set; skipping Laravel Web."; return }
    if (-not (Test-Path (Join-Path $WebPath "artisan"))) { throw "Laravel path does not contain artisan: $WebPath" }
    if (Test-Port 8001) { Write-Info "Web port 8001 is already listening."; return }
    New-Item -ItemType Directory -Force -Path $PidDir | Out-Null
    $process = Start-Process -FilePath "php" -WorkingDirectory $WebPath -ArgumentList "artisan serve --host=127.0.0.1 --port=8001" -PassThru
    Set-Content -Path $WebPidFile -Value $process.Id
    Write-Info "Started Laravel PID $($process.Id) on 127.0.0.1:8001."
}
function Stop-PidFile($Path, $Name) {
    $processId = Get-PidFromFile $Path
    if ($null -eq $processId) { Write-Info "$Name PID file not found."; return }
    $process = Get-Process -Id $processId -ErrorAction SilentlyContinue
    if ($null -ne $process) { Stop-Process -Id $processId -Force; Write-Info "Stopped $Name PID $processId." } else { Write-Info "$Name PID $processId is already stopped." }
    Remove-Item $Path -Force -ErrorAction SilentlyContinue
}
function Show-Status {
    Write-Info "Repository: $RepoRoot"
    Write-Info "Agent 8000: $(if (Test-Port 8000) { "LISTENING" } else { "STOPPED" })"
    Write-Info "Web   8001: $(if (Test-Port 8001) { "LISTENING" } else { "STOPPED" })"
    docker compose -f (Join-Path $RepoRoot "docker-compose.yml") ps
}
function Show-Health {
    Write-Info "Agent:"
    try { Invoke-RestMethod "http://127.0.0.1:8000/health" | ConvertTo-Json -Compress } catch { Write-Host "UNHEALTHY: $($_.Exception.Message)" }
    Write-Info "Agent dependencies:"
    try { Invoke-RestMethod "http://127.0.0.1:8000/health/dependencies" | ConvertTo-Json -Depth 5 } catch { Write-Host "UNAVAILABLE: $($_.Exception.Message)" }
    if (Test-Port 8001) {
        Write-Info "Laravel Web:"
        try { (Invoke-WebRequest "http://127.0.0.1:8001/up" -UseBasicParsing).StatusCode } catch { Write-Host "UNHEALTHY: $($_.Exception.Message)" }
    }
}
switch ($Action) {
    "start" {
        New-Item -ItemType Directory -Force -Path $PidDir | Out-Null
        docker compose -f (Join-Path $RepoRoot "docker-compose.yml") up -d
        Start-Agent
        Start-Web
        Start-Sleep -Seconds 2
        Show-Health
    }
    "stop" { Stop-PidFile $WebPidFile "Laravel"; Stop-PidFile $AgentPidFile "Agent"; docker compose -f (Join-Path $RepoRoot "docker-compose.yml") stop }
    "status" { Remove-StalePid $AgentPidFile; Remove-StalePid $WebPidFile; Show-Status }
    "health" { Show-Health }
}
