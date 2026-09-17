# DEVOS Print Offline Hotspot — Local Test

This is a small bootstrap helper for the `phone-printer` module.

Goal:

`Windows PC + USB printer + PaperCut Mobility Print + local Wi-Fi hotspot that can stay available without internet.`

The helper wraps the open-source `antoniotejada/WiFiDirectLegacyAP` proof-of-concept. That upstream project creates a Wi-Fi Direct legacy access point and does not share the PC internet connection. Its current implementation requires Windows, Wi-Fi Direct capable hardware, Python 2.7, and `comtypes`.

## First local test

1. Confirm the USB printer already prints from Windows.
2. Keep PaperCut Mobility Print configured with **Local Subnet (mDNS)** for the first test.
3. Install Git for Windows and Python 2.7 if they are not already installed.
4. Double-click:

   `Start-DevosPrintHotspot.cmd`

5. Enter a hotspot password of at least 8 characters.
6. Connect the phone/laptop to Wi-Fi network `DEVOS-PRINT`.
7. `No internet` on the client is expected and is not a failure.
8. Open the client print UI and check whether the PaperCut printer appears.

## PowerShell usage

```powershell
.\Start-DevosPrintHotspot.ps1 -Ssid "DEVOS-PRINT" -Password "YourLocalPassword"
```

On first run the helper downloads the upstream open-source engine to:

`%LOCALAPPDATA%\DevosPrintHotspot\WiFiDirectLegacyAP`

First setup therefore needs internet once. After the dependency is present, the local Wi-Fi access point itself is intended to work without internet.

## Stop

Keep the PowerShell/CMD window open while testing. Press `Ctrl+C` to stop the access point.

## Scope

This is deliberately a **local proof-of-concept**, not the final Phone Printer Hub hotspot implementation. It does not change printer drivers, PaperCut configuration, Windows firewall rules, or production/external services.

If the proof succeeds on the target PC/Wi-Fi adapter, the next step is to replace the Python 2.7 dependency with a modern Windows implementation and integrate start/stop/status into the existing Phone Printer Hub Windows GUI.
