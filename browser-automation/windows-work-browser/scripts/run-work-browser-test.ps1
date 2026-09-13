[CmdletBinding()]
param(
  [string]$BrowserExe = "$env:LOCALAPPDATA\BrowserOS\Application\chrome.exe",
  [int]$Port = 9222
)

$ErrorActionPreference = 'Stop'
$extension = Join-Path $PSScriptRoot '..\extension'
$extension = (Resolve-Path $extension).Path

if (-not (Test-Path -LiteralPath $BrowserExe)) {
  throw "Browser executable not found: $BrowserExe. Install the pinned BrowserOS Windows artifact first."
}

& $BrowserExe `
  "--user-data-dir=$env:TEMP\WindowsWorkBrowser-TestProfile" `
  "--remote-debugging-port=$Port" `
  "--load-extension=$extension" `
  '--no-first-run' `
  '--no-default-browser-check' `
  'https://example.com'
