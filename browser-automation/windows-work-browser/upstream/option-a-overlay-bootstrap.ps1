[CmdletBinding()]
param(
  [string]$StageRoot = "$env:TEMP\windows-work-browser-overlay"
)

$ErrorActionPreference = 'Stop'
$extensionUrl = 'https://github.com/browseros-ai/BrowserOS/releases/download/ext-agent/v0.0.156.0/agent-0.0.156.0.crx'
$expectedSha256 = 'd1074b2d4ec15b9a6305090be5006222a150d336a7b0ebebfcdb414d7b9847cf'
$extensionPath = Join-Path $StageRoot 'agent-0.0.156.0.crx'

New-Item -ItemType Directory -Force -Path $StageRoot | Out-Null
Invoke-WebRequest -Uri $extensionUrl -OutFile $extensionPath
$actual = (Get-FileHash -Algorithm SHA256 -Path $extensionPath).Hash.ToLowerInvariant()
if ($actual -ne $expectedSha256) {
  Remove-Item -Force $extensionPath
  throw "Agent extension SHA-256 mismatch. Expected $expectedSha256, got $actual."
}

[ordered]@{
  component = 'BrowserOS Agent Extension'
  version = '0.0.156.0'
  sha256 = $actual
  status = 'VERIFIED'
  deployment = 'STAGED_ONLY'
  note = 'Do not force-install or bypass browser policy. Deploy through a supported BrowserOS extension/agent integration path.'
  verified_at = (Get-Date).ToUniversalTime().ToString('o')
} | ConvertTo-Json | Set-Content (Join-Path $StageRoot 'OVERLAY-VERIFICATION.json')

Write-Host "Verified agent overlay: $extensionPath"
