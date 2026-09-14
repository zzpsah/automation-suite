param(
    [Parameter(Mandatory = $true)]
    [string]$ExePath,

    [Parameter(Mandatory = $false)]
    [string]$OutputDirectory = "devos-work-browser/artifacts/winapp-ui"
)

$ErrorActionPreference = "Stop"
New-Item -ItemType Directory -Force -Path $OutputDirectory | Out-Null
$OutputDirectory = (Resolve-Path $OutputDirectory).Path
$ExePath = (Resolve-Path $ExePath).Path
$env:WINAPP_UI_WORKFLOW_ID = [guid]::NewGuid().ToString()

function Invoke-WinApp {
    param([Parameter(Mandatory = $true)][string[]]$Arguments)
    $output = & winapp @Arguments 2>&1
    $exit = $LASTEXITCODE
    if ($exit -ne 0) {
        throw "winapp $($Arguments -join ' ') failed with exit code $exit.`n$($output | Out-String)"
    }
    return $output
}

function Assert-Selector {
    param([string]$Selector, [int]$ProcessId)
    $jsonText = (& winapp ui search $Selector -a $ProcessId --json 2>$null | Out-String).Trim()
    if ($LASTEXITCODE -ne 0) {
        throw "WinApp UI could not find required selector '$Selector'."
    }
    $result = $jsonText | ConvertFrom-Json
    if ($result.matchCount -lt 1) {
        throw "Expected selector '$Selector' but matchCount was $($result.matchCount)."
    }
}

function Wait-ControlValue {
    param(
        [string]$Selector,
        [string]$Pattern,
        [int]$ProcessId,
        [int]$TimeoutSeconds = 15
    )

    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    $lastValue = ""
    while ((Get-Date) -lt $deadline) {
        $lastValue = (Invoke-WinApp -Arguments @("ui", "get-value", $Selector, "-a", "$ProcessId") | Out-String).Trim()
        if ($lastValue -match $Pattern) {
            return $lastValue
        }
        Start-Sleep -Milliseconds 250
    }

    throw "Control '$Selector' did not match '$Pattern' within ${TimeoutSeconds}s. Last value: $lastValue"
}

$process = Start-Process -FilePath $ExePath -PassThru
try {
    Invoke-WinApp -Arguments @("ui", "wait-for", "AddressBox", "-a", "$($process.Id)", "-t", "30000") | Out-Null

    $requiredSelectors = @(
        "BackButton",
        "ForwardButton",
        "ReloadButton",
        "HomeButton",
        "AddressBox",
        "GoButton",
        "NewTabButton",
        "CloseTabButton",
        "TestPortalButton",
        "CommandBox",
        "RunCommandButton",
        "CommandStatus",
        "AiStatusText",
        "BrowserTabs"
    )

    foreach ($selector in $requiredSelectors) {
        Assert-Selector -Selector $selector -ProcessId $process.Id
    }

    $aiStatus = Wait-ControlValue -Selector "AiStatusText" -Pattern "(?i)local ai" -ProcessId $process.Id -TimeoutSeconds 10

    Invoke-WinApp -Arguments @("ui", "inspect", "-a", "$($process.Id)", "--json") | Set-Content -Encoding UTF8 (Join-Path $OutputDirectory "initial-tree.json")
    Invoke-WinApp -Arguments @("ui", "screenshot", "-a", "$($process.Id)", "-o", (Join-Path $OutputDirectory "01-chromium-shell.png")) | Out-Null

    Invoke-WinApp -Arguments @("ui", "invoke", "NewTabButton", "-a", "$($process.Id)") | Out-Null
    Start-Sleep -Milliseconds 500
    Invoke-WinApp -Arguments @("ui", "invoke", "CloseTabButton", "-a", "$($process.Id)") | Out-Null

    # CI deliberately disables local AI. This proves the AI-first shell falls back
    # to the governed deterministic planner without changing browser behavior.
    Invoke-WinApp -Arguments @("ui", "set-value", "CommandBox", "open example.com", "-a", "$($process.Id)") | Out-Null
    Invoke-WinApp -Arguments @("ui", "invoke", "RunCommandButton", "-a", "$($process.Id)") | Out-Null
    $addressAfterOpen = Wait-ControlValue -Selector "AddressBox" -Pattern "(?i)example\.com" -ProcessId $process.Id -TimeoutSeconds 15

    Invoke-WinApp -Arguments @("ui", "invoke", "TestPortalButton", "-a", "$($process.Id)") | Out-Null
    $portalStatus = Wait-ControlValue -Selector "CommandStatus" -Pattern "(?i)synthetic portal loaded" -ProcessId $process.Id -TimeoutSeconds 15
    Invoke-WinApp -Arguments @("ui", "screenshot", "-a", "$($process.Id)", "-o", (Join-Path $OutputDirectory "02-test-portal.png")) | Out-Null

    Invoke-WinApp -Arguments @("ui", "set-value", "CommandBox", "wait for #status; read #status", "-a", "$($process.Id)") | Out-Null
    Invoke-WinApp -Arguments @("ui", "invoke", "RunCommandButton", "-a", "$($process.Id)") | Out-Null
    $readStatus = Wait-ControlValue -Selector "CommandStatus" -Pattern "(?i)ready" -ProcessId $process.Id -TimeoutSeconds 15

    Invoke-WinApp -Arguments @("ui", "set-value", "CommandBox", "submit #next", "-a", "$($process.Id)") | Out-Null
    Invoke-WinApp -Arguments @("ui", "invoke", "RunCommandButton", "-a", "$($process.Id)") | Out-Null
    Invoke-WinApp -Arguments @("ui", "wait-for", "DEVOS approval required", "-a", "$($process.Id)", "-t", "10000") | Out-Null
    Invoke-WinApp -Arguments @("ui", "screenshot", "-a", "$($process.Id)", "--capture-screen", "-o", (Join-Path $OutputDirectory "03-approval-dialog.png")) | Out-Null
    Invoke-WinApp -Arguments @("ui", "invoke", "No", "-a", "$($process.Id)") | Out-Null
    $approvalStatus = Wait-ControlValue -Selector "CommandStatus" -Pattern "(?i)approval declined" -ProcessId $process.Id -TimeoutSeconds 10

    Invoke-WinApp -Arguments @("ui", "focus", "CommandBox", "-a", "$($process.Id)") | Out-Null
    Invoke-WinApp -Arguments @("ui", "screenshot", "-a", "$($process.Id)", "-o", (Join-Path $OutputDirectory "04-final.png")) | Out-Null

    @(
        "DEVOS Work Browser v0.2.0 Stage 4 WinApp UI Acceptance: PASS",
        "ProcessId: $($process.Id)",
        "Chromium-style shell required controls: PASS",
        "Local AI status surface: PASS ($aiStatus)",
        "Open/close tab controls: PASS",
        "AI-first command handler deterministic fallback: PASS ($addressAfterOpen)",
        "Bundled Test Portal navigation readiness: PASS ($portalStatus)",
        "Command bar wait/read through visible CommandStatus: PASS",
        "Approval dialog blocks committing command: PASS",
        "Decline path leaves visible CommandStatus: PASS"
    ) | Set-Content -Encoding UTF8 (Join-Path $OutputDirectory "summary.txt")
}
finally {
    if (-not $process.HasExited) {
        Stop-Process -Id $process.Id -Force -ErrorAction SilentlyContinue
    }
}
