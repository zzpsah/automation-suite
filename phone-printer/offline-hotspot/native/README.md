# DEVOS Print Hotspot — Native Windows EXE

This is the Python-free local Wi-Fi Direct access-point helper for the Phone Printer Hub.

## Goal

Create a local Wi-Fi network from the Windows PC for nearby phones/laptops so they can reach PaperCut Mobility Print or another local print service even when the PC has no internet connection.

## Use

1. Download `DevosPrintHotspot.exe` from the `DEVOS-Print-Hotspot-Windows-x64` GitHub Actions artifact.
2. Double-click the EXE.
3. Keep the default SSID `DEVOS-PRINT` or type another name.
4. Enter an 8-63 character password.
5. Connect the phone/laptop to that Wi-Fi network.
6. Keep this EXE window open while printing.
7. PaperCut can stay on mDNS/local-subnet discovery for the first test. If discovery is unreliable, use PaperCut Known Host with the PC's Wi-Fi Direct adapter IP.

The executable is self-contained for Windows x64 and does not require Python or a separately installed .NET runtime.

## Command-line use

```powershell
DevosPrintHotspot.exe --ssid DEVOS-PRINT --password YourPasswordHere
```

Avoid putting real passwords into shared scripts or Git history.

## Requirements

- Windows 10/11 x64.
- Wi-Fi adapter/driver with Wi-Fi Direct support.
- A working local print service (for example PaperCut Mobility Print) and a Windows-installed USB printer.

## Boundary

This helper creates the local Wi-Fi Direct AP only. It does not configure PaperCut, printer drivers, Windows Firewall, or internet sharing. It intentionally does not depend on internet sharing.
