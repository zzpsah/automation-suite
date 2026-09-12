# Windows Work Browser - pinned upstream bootstrap
# Run from a Windows build machine with Git, Python and required Chromium tooling installed.
# This script ACQUIRES source; it does not claim that compilation has succeeded.

[CmdletBinding()]
param(
  [string]$Root = "$PSScriptRoot\..\..\..\..\..\_build\windows-work-browser"
)

$ErrorActionPreference = 'Stop'
$BrowserOsRepo = 'https://github.com/browseros-ai/BrowserOS.git'
$BrowserOsRevision = '8f5d36bc16f57115aeeff34baf4ad6aa964d509c'
$OpenBrowserUseRepo = 'https://github.com/open-browser-use/open-browser-use.git'
$OpenBrowserUseRevision = '7765002ac88040aedc781be89afe68475a9d6c88'

function Require-Command([string]$Name) {
  if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
    throw "Required command not found: $Name"
  }
}

Require-Command 'git'
New-Item -ItemType Directory -Force -Path $Root | Out-Null

$BrowserOsDir = Join-Path $Root 'BrowserOS'
if (-not (Test-Path (Join-Path $BrowserOsDir '.git'))) {
  git clone $BrowserOsRepo $BrowserOsDir
}
git -C $BrowserOsDir fetch --tags --force origin
git -C $BrowserOsDir checkout --detach $BrowserOsRevision

$ObuDir = Join-Path $Root 'open-browser-use'
if (-not (Test-Path (Join-Path $ObuDir '.git'))) {
  git clone $OpenBrowserUseRepo $ObuDir
}
git -C $ObuDir fetch --tags --force origin
git -C $ObuDir checkout --detach $OpenBrowserUseRevision

$Manifest = [ordered]@{
  generated_utc = [DateTime]::UtcNow.ToString('o')
  browseros_repo = $BrowserOsRepo
  browseros_revision = (git -C $BrowserOsDir rev-parse HEAD).Trim()
  browseros_expected_revision = $BrowserOsRevision
  open_browser_use_repo = $OpenBrowserUseRepo
  open_browser_use_revision = (git -C $ObuDir rev-parse HEAD).Trim()
  open_browser_use_expected_revision = $OpenBrowserUseRevision
}

if ($Manifest.browseros_revision -ne $BrowserOsRevision) { throw 'BrowserOS revision verification failed.' }
if ($Manifest.open_browser_use_revision -ne $OpenBrowserUseRevision) { throw 'open-browser-use revision verification failed.' }

$Manifest | ConvertTo-Json | Set-Content -Encoding UTF8 (Join-Path $Root 'SOURCE-MANIFEST.json')
Write-Host 'Pinned upstream source acquired and verified.'
Write-Host 'Next gate: apply product overlays, dependency/license audit, then Windows build.'
