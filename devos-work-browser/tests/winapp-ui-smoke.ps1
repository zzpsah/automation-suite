param(
    [Parameter(Mandatory = $true)]
    [string]$AppDirectory,
    [Parameter(Mandatory = $true)]
    [string]$OutputDirectory
)

$ErrorActionPreference = 'Stop'
New-Item -ItemType Directory -Force -Path $OutputDirectory | Out-Null

$exe = Resolve-Path (Join-Path $AppDirectory 'DEVOS.WorkBrowser.exe')
$reportPath = Join-Path $OutputDirectory 'winapp-ui-report.txt'
$treePath = Join-Path $OutputDirectory 'accessibility-tree.json'
$initialShot = Join-Path $OutputDirectory '01-initial.png'
$portalShot = Join-Path $OutputDirectory '02-test-portal.png'
$commandShot = Join-Path $OutputDirectory '03-command-result.png'

$results = [System.Collections.Generic.List[string]]::new()
function Pass([string]$name) { $results.Add("PASS`t$name") }

$process = Start-Process -FilePath $exe -PassThru
try {
    $pidValue = $process.Id

    winapp ui wait-for AddressBox -a $pidValue --timeout 30000 | Out-Null
    Pass 'Main window and address bar visible'

    winapp ui wait-for BackButton -a $pidValue --timeout 5000 | Out-Null
    winapp ui wait-for ForwardButton -a $pidValue --timeout 5000 | Out-Null
    winapp ui wait-for ReloadButton -a $pidValue --timeout 5000 | Out-Null
    winapp ui wait-for HomeButton -a $pidValue --timeout 5000 | Out-Null
    winapp ui wait-for NewTabButton -a $pidValue --timeout 5000 | Out-Null
    winapp ui wait-for CloseTabButton -a $pidValue --timeout 5000 | Out-Null
    winapp ui wait-for TestPortalButton -a $pidValue --timeout 5000 | Out-Null
    winapp ui wait-for CommandBox -a $pidValue --timeout 5000 | Out-Null
    winapp ui wait-for RunCommandButton -a $pidValue --timeout 5000 | Out-Null
    Pass 'Core interactive controls exposed through UI Automation'

    winapp ui inspect -a $pidValue --json | Out-File -FilePath $treePath -Encoding utf8
    winapp ui screenshot -a $pidValue -o $initialShot | Out-Null
    Pass 'Accessibility tree and initial screenshot captured'

    winapp ui invoke NewTabButton -a $pidValue | Out-Null
    Start-Sleep -Milliseconds 500
    winapp ui invoke CloseTabButton -a $pidValue | Out-Null
    Pass 'New tab and close tab buttons invoke successfully'

    winapp ui invoke TestPortalButton -a $pidValue | Out-Null
    winapp ui wait-for CommandStatus -a $pidValue --value 'Synthetic portal loaded' --timeout 10000 | Out-Null
    winapp ui screenshot -a $pidValue -o $portalShot | Out-Null
    Pass 'Bundled Test Portal opens through outer Windows UI'

    winapp ui set-value CommandBox 'read #status' -a $pidValue | Out-Null
    winapp ui invoke RunCommandButton -a $pidValue | Out-Null
    winapp ui wait-for CommandStatus -a $pidValue --value 'ready' --timeout 10000 | Out-Null
    winapp ui screenshot -a $pidValue -o $commandShot | Out-Null
    Pass 'Command box drives same-browser read command and returns ready'

    $results.Add('PASS`tWINAPP_UI_ACCEPTANCE_SMOKE')
    $results | Out-File -FilePath $reportPath -Encoding utf8
    Get-Content $reportPath
}
finally {
    if (-not $process.HasExited) {
        Stop-Process -Id $process.Id -Force -ErrorAction SilentlyContinue
    }
}
