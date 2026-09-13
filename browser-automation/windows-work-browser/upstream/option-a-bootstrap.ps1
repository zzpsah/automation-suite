# Option A artifact bootstrap for Windows Work Browser
# Requires an approved manifest. Refuses to execute an unverified artifact.

[CmdletBinding()]
param(
  [Parameter(Mandatory=$true)][string]$ManifestPath,
  [string]$StageRoot = "$PSScriptRoot\..\..\..\..\..\_build\option-a"
)

$ErrorActionPreference = 'Stop'

function Fail([string]$Message) { throw "OPTION-A: $Message" }

if (-not (Test-Path -LiteralPath $ManifestPath)) { Fail "Manifest not found: $ManifestPath" }
$manifest = Get-Content -Raw -LiteralPath $ManifestPath | ConvertFrom-Json

if ($manifest.product -ne 'windows-work-browser') { Fail 'Manifest product mismatch.' }
if ($manifest.artifact.platform -ne 'windows') { Fail 'Artifact is not a Windows artifact.' }
if ($manifest.artifact.architecture -notin @('x64','arm64')) { Fail 'Unsupported architecture.' }
if ($manifest.verification.status -ne 'VERIFIED') { Fail 'Artifact is not VERIFIED.' }
if ([string]::IsNullOrWhiteSpace($manifest.artifact.sha256) -or $manifest.artifact.sha256 -notmatch '^[A-Fa-f0-9]{64}$') { Fail 'Trusted SHA-256 is required.' }

$stage = Join-Path $StageRoot 'staged'
New-Item -ItemType Directory -Force -Path $stage | Out-Null
$file = Join-Path $stage $manifest.artifact.filename

Write-Host "Downloading approved artifact..."
Invoke-WebRequest -Uri $manifest.artifact.download_url -OutFile $file

$actual = (Get-FileHash -Algorithm SHA256 -LiteralPath $file).Hash
if ($actual -ne $manifest.artifact.sha256.ToUpperInvariant()) {
  Remove-Item -Force -LiteralPath $file
  Fail "SHA-256 mismatch. Expected $($manifest.artifact.sha256), got $actual."
}

$verification = [ordered]@{
  product = $manifest.product
  artifact = $manifest.artifact.filename
  expected_sha256 = $manifest.artifact.sha256.ToUpperInvariant()
  actual_sha256 = $actual
  status = 'VERIFIED'
  verified_utc = [DateTime]::UtcNow.ToString('o')
}
$verification | ConvertTo-Json | Set-Content -Encoding UTF8 (Join-Path $stage 'VERIFICATION.json')

Write-Host "Artifact verified and staged: $file"
Write-Host "Next: install/launch on Windows and run the Option A smoke suite."
