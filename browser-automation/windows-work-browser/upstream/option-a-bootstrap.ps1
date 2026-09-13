[CmdletBinding()]
param(
  [Parameter(Mandatory=$true)][string]$ManifestPath,
  [string]$StageRoot = "$env:TEMP\windows-work-browser"
)

$ErrorActionPreference = 'Stop'
$manifest = Get-Content -Raw $ManifestPath | ConvertFrom-Json
if ($manifest.product -ne 'windows-work-browser') { throw 'Wrong product manifest.' }
if ($manifest.artifact.platform -ne 'windows') { throw 'Artifact is not Windows.' }
if ($manifest.artifact.arch -ne 'x64' -and $manifest.artifact.arch -ne 'arm64') { throw 'Unsupported Windows architecture.' }
if ($manifest.verification.status -notin @('VERIFIED_METADATA','VERIFIED_RUNTIME')) { throw 'Artifact is not approved for acquisition.' }
if ($manifest.artifact.sha256 -notmatch '^[0-9a-fA-F]{64}$') { throw 'Pinned SHA-256 is required.' }

New-Item -ItemType Directory -Force -Path $StageRoot | Out-Null
$artifact = Join-Path $StageRoot $manifest.artifact.filename
Invoke-WebRequest -Uri $manifest.artifact.download_url -OutFile $artifact
$actual = (Get-FileHash -Algorithm SHA256 -Path $artifact).Hash.ToLowerInvariant()
if ($actual -ne $manifest.artifact.sha256.ToLowerInvariant()) {
  Remove-Item -Force $artifact
  throw "SHA-256 mismatch. Expected $($manifest.artifact.sha256), got $actual."
}

$signature = Get-AuthenticodeSignature -FilePath $artifact
if ($signature.Status -ne 'Valid') {
  Remove-Item -Force $artifact
  throw "Authenticode verification failed: $($signature.Status)"
}

[ordered]@{
  product = $manifest.product
  release = $manifest.upstream.release
  artifact = $manifest.artifact.filename
  sha256 = $actual
  signature_status = [string]$signature.Status
  signer = [string]$signature.SignerCertificate.Subject
  verified_at = (Get-Date).ToUniversalTime().ToString('o')
  status = 'VERIFIED'
} | ConvertTo-Json | Set-Content (Join-Path $StageRoot 'VERIFICATION.json')

Write-Host "Verified artifact: $artifact"
Write-Host "SHA-256: $actual"
Write-Host "Next gate: isolated install + browser smoke test."
