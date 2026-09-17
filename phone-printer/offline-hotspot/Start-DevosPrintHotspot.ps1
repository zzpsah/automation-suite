param(
    [string]$Ssid = "DEVOS-PRINT",
    [string]$Password,
    [string]$EngineRoot = "$env:LOCALAPPDATA\DevosPrintHotspot"
)

$ErrorActionPreference = "Stop"

function Write-Step($message) {
    Write-Host "[DEVOS-PRINT] $message" -ForegroundColor Cyan
}

function Fail($message) {
    Write-Host "[DEVOS-PRINT] ERROR: $message" -ForegroundColor Red
    exit 1
}

if ($env:OS -ne "Windows_NT") {
    Fail "This helper is for Windows only."
}

if ([string]::IsNullOrWhiteSpace($Password)) {
    $Password = Read-Host "Hotspot password (minimum 8 characters)"
}

if ($Password.Length -lt 8) {
    Fail "Password must contain at least 8 characters."
}

$git = Get-Command git -ErrorAction SilentlyContinue
if (-not $git) {
    Fail "Git is required for first-time setup. Install Git for Windows, then run this script again."
}

# Resolve a Python 2.7 launcher because the upstream WiFiDirectLegacyAP project currently requires it.
$PythonExe = $null
$PythonPrefixArgs = @()

$pyLauncher = Get-Command py -ErrorAction SilentlyContinue
if ($pyLauncher) {
    try {
        & py -2.7 -V *> $null
        if ($LASTEXITCODE -eq 0) {
            $PythonExe = "py"
            $PythonPrefixArgs = @("-2.7")
        }
    } catch {}
}

if (-not $PythonExe) {
    $python2 = Get-Command python2 -ErrorAction SilentlyContinue
    if ($python2) {
        $PythonExe = $python2.Source
    }
}

if (-not $PythonExe) {
    Fail "Python 2.7 was not found. This first proof-of-concept wraps the open-source WiFiDirectLegacyAP engine, which currently requires Python 2.7."
}

$EngineDir = Join-Path $EngineRoot "WiFiDirectLegacyAP"
$EngineScript = Join-Path $EngineDir "WiFiDirectLegacyAP.py"

if (-not (Test-Path $EngineScript)) {
    Write-Step "First run: downloading the open-source WiFiDirectLegacyAP engine..."
    New-Item -ItemType Directory -Force -Path $EngineRoot | Out-Null
    & git clone --depth 1 https://github.com/antoniotejada/WiFiDirectLegacyAP.git $EngineDir
    if ($LASTEXITCODE -ne 0) {
        Fail "Could not clone WiFiDirectLegacyAP. First run needs internet access; after installation the hotspot itself does not need internet."
    }
}

Write-Step "Checking Python dependency comtypes..."
$checkArgs = @($PythonPrefixArgs + @("-c", "import comtypes"))
& $PythonExe @checkArgs 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Step "Installing comtypes into Python 2.7..."
    $pipArgs = @($PythonPrefixArgs + @("-m", "pip", "install", "comtypes"))
    & $PythonExe @pipArgs
    if ($LASTEXITCODE -ne 0) {
        Fail "Could not install comtypes."
    }
}

$OutDir = Join-Path $EngineDir "_out"
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
$CredentialFile = Join-Path $OutDir "ssid_password.txt"
@($Ssid, $Password) | Set-Content -Path $CredentialFile -Encoding ASCII

Write-Step "Starting offline local Wi-Fi access point..."
Write-Host "SSID: $Ssid" -ForegroundColor Green
Write-Host "Internet sharing: OFF by design" -ForegroundColor Yellow
Write-Host "Keep this window open. Press Ctrl+C to stop the hotspot." -ForegroundColor Yellow
Write-Host "After your phone connects, keep PaperCut Mobility Print on Local Subnet (mDNS) for the first test." -ForegroundColor Yellow

Push-Location $EngineDir
try {
    $runArgs = @($PythonPrefixArgs + @($EngineScript))
    & $PythonExe @runArgs
} finally {
    Pop-Location
}
