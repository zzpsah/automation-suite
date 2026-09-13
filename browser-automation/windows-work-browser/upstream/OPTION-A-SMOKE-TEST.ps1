# Option A Windows smoke harness
# This validates an already-installed browser executable. It does not install or claim release readiness.

[CmdletBinding()]
param(
  [Parameter(Mandatory=$true)][string]$BrowserExe,
  [string]$EvidenceDir = "$PSScriptRoot\..\..\..\..\..\_build\option-a\evidence"
)

$ErrorActionPreference = 'Stop'
New-Item -ItemType Directory -Force -Path $EvidenceDir | Out-Null

$started = Get-Date
if (-not (Test-Path -LiteralPath $BrowserExe)) { throw "Browser executable not found: $BrowserExe" }

$hash = (Get-FileHash -Algorithm SHA256 -LiteralPath $BrowserExe).Hash
$proc = Start-Process -FilePath $BrowserExe -ArgumentList '--new-window','about:blank' -PassThru
Start-Sleep -Seconds 5

$running = -not $proc.HasExited
$result = [ordered]@{
  test = 'option-a-browser-launch'
  browser_exe = (Resolve-Path -LiteralPath $BrowserExe).Path
  executable_sha256 = $hash
  started_utc = $started.ToUniversalTime().ToString('o')
  process_started = $true
  process_running_after_5s = $running
  status = if ($running) { 'PASS' } else { 'FAIL' }
}
$result | ConvertTo-Json | Set-Content -Encoding UTF8 (Join-Path $EvidenceDir 'browser-launch.json')

if (-not $running) { throw 'Browser exited before launch smoke checkpoint.' }
Write-Host 'PASS: browser launch checkpoint.'
Write-Host 'Manual/integration gates still required: HTTPS render, tabs, profiles, downloads, Playwright/CDP, native bridge and policy checks.'
