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

$process = Start-Process -FilePath $ExePath -PassThru
try {
    # In process-scoped WinApp UI queries the top-level window is the scope root,
    # so wait on a stable child AutomationId rather than searching for the root itself.
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
        "BrowserTabs"
    )

    foreach ($selector in $requiredSelectors) {
        Assert-Selector -Selector $selector -ProcessId $process.Id
    }

    Invoke-WinApp -Arguments @("ui", "inspect", "-a", "$($process.Id)", "--json") | Set-Content -Encoding UTF8 (Join-Path $OutputDirectory "initial-tree.json")
    Invoke-WinApp -Arguments @("ui", "screenshot", "-a", "$($process.Id)", "-o", (Join-Path $OutputDirectory "01-launch.png")) | Out-Null

    Invoke-WinApp -Arguments @("ui", "invoke", "NewTabButton", "-a", "$($process.Id)") | Out-Null
    Start-Sleep -Milliseconds 500
    Invoke-WinApp -Arguments @("ui", "invoke", "CloseTabButton", "-a", "$($process.Id)") | Out-Null

    Invoke-WinApp -Arguments @("ui", "invoke", "TestPortalButton", "-a", "$($process.Id)") | Out-Null
    Start-Sleep -Milliseconds 750
    Invoke-WinApp -Arguments @("ui", "screenshot", "-a", "$($process.Id)", "-o", (Join-Path $OutputDirectory "02-test-portal.png")) | Out-Null

    Invoke-WinApp -Arguments @("ui", "set-value", "CommandBox", "read #status", "-a", "$($process.Id)") | Out-Null
    Invoke-WinApp -Arguments @("ui", "invoke", "RunCommandButton", "-a", "$($process.Id)") | Out-Null
    Invoke-WinApp -Arguments @("ui", "wait-for", "ready", "-a", "$($process.Id)", "-t", "10000") | Out-Null
    $readStatus = (Invoke-WinApp -Arguments @("ui", "get-text", "CommandStatus", "-a", "$($process.Id)") | Out-String).Trim()
    if ($readStatus -notmatch "(?i)ready") {
        throw "Command bar did not surface expected portal status. Output: $readStatus"
    }

    Invoke-WinApp -Arguments @("ui", "set-value", "CommandBox", "submit #next", "-a", "$($process.Id)") | Out-Null
    Invoke-WinApp -Arguments @("ui", "invoke", "RunCommandButton", "-a", "$($process.Id)") | Out-Null
    Invoke-WinApp -Arguments @("ui", "wait-for", "DEVOS approval required", "-a", "$($process.Id)", "-t", "10000") | Out-Null
    Invoke-WinApp -Arguments @("ui", "screenshot", "-a", "$($process.Id)", "--capture-screen", "-o", (Join-Path $OutputDirectory "03-approval-dialog.png")) | Out-Null
    Invoke-WinApp -Arguments @("ui", "invoke", "No", "-a", "$($process.Id)") | Out-Null
    Invoke-WinApp -Arguments @("ui", "wait-for", "Approval declined", "-a", "$($process.Id)", "-t", "10000") | Out-Null
    $approvalStatus = (Invoke-WinApp -Arguments @("ui", "get-text", "CommandStatus", "-a", "$($process.Id)") | Out-String).Trim()
    if ($approvalStatus -notmatch "(?i)approval declined") {
        throw "Declined approval did not leave the expected visible status. Output: $approvalStatus"
    }

    Invoke-WinApp -Arguments @("ui", "focus", "CommandBox", "-a", "$($process.Id)") | Out-Null
    Invoke-WinApp -Arguments @("ui", "screenshot", "-a", "$($process.Id)", "-o", (Join-Path $OutputDirectory "04-final.png")) | Out-Null

    @(
        "DEVOS Work Browser WinApp UI Acceptance: PASS",
        "ProcessId: $($process.Id)",
        "Stable child AutomationIds: PASS",
        "Open/close tab controls: PASS",
        "Bundled Test Portal navigation: PASS",
        "Command bar read through real UI: PASS",
        "Approval dialog blocks committing command: PASS",
        "Decline path leaves visible status: PASS"
    ) | Set-Content -Encoding UTF8 (Join-Path $OutputDirectory "summary.txt")
}
finally {
    if (-not $process.HasExited) {
        Stop-Process -Id $process.Id -Force -ErrorAction SilentlyContinue
    }
}
