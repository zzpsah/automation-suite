[CmdletBinding()]
param(
  [string]$BrowserExe = "$env:LOCALAPPDATA\BrowserOS\Application\chrome.exe",
  [int]$Port = 17321,
  [int]$CdpPort = 9222
)

$ErrorActionPreference = 'Stop'
$productRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$dist = Join-Path $productRoot 'dist'
$extension = (Resolve-Path (Join-Path $productRoot 'extension')).Path
$queue = Join-Path $env:LOCALAPPDATA 'WindowsWorkBrowser\tasks.json'
$profile = Join-Path $env:LOCALAPPDATA 'WindowsWorkBrowser\BrowserProfile'

if (-not (Test-Path -LiteralPath $BrowserExe)) {
  throw "BrowserOS executable not found: $BrowserExe"
}
if (-not (Test-Path -LiteralPath (Join-Path $dist 'runtime/local-agent-server.js'))) {
  throw "Agent runtime is not built. Run npm run build first."
}
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $queue) | Out-Null
New-Item -ItemType Directory -Force -Path $profile | Out-Null

$agent = Start-Process -FilePath 'node.exe' -ArgumentList (Join-Path $dist 'runtime/local-agent-server.js') -PassThru -WindowStyle Hidden -WorkingDirectory $productRoot -Environment @{
  WWB_QUEUE_FILE = $queue
  WWB_PORT = [string]$Port
}

Start-Sleep -Milliseconds 700
if ($agent.HasExited) { throw "Local agent server exited during startup." }

$browser = Start-Process -FilePath $BrowserExe -ArgumentList @(
  "--user-data-dir=$profile",
  "--remote-debugging-port=$CdpPort",
  "--load-extension=$extension",
  '--no-first-run',
  '--no-default-browser-check',
  'https://example.com'
) -PassThru

Write-Host "Work Browser started. Agent PID=$($agent.Id), Browser PID=$($browser.Id), CDP=$CdpPort, Agent=$Port"
Write-Host "Close this PowerShell session or stop the child processes to shut down the preview."
