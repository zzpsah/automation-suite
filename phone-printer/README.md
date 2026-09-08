# Phone Printer Hub

Print from Android or any browser to a USB printer connected to a Windows PC.

## Supported network modes

### Phone hotspot mode

1. Turn on the Android phone hotspot.
2. Connect the Windows PC to that hotspot.
3. Connect the USB printer to Windows and confirm it prints normally from Windows.
4. Run `PhonePrinterBridge.exe`.
5. Allow it through Windows Firewall when prompted.
6. Open the Android app. It listens for the Windows Print Hub beacon and also sends a UDP discovery request.
7. The PC is discovered automatically even when DHCP changes its IP.
8. Select printer/file/settings and tap **PRINT**.

Manual IP is available only under **Advanced** as a fallback.

### Windows hotspot / normal LAN mode

Any phone, tablet or laptop on the same network can open the Windows Print Hub in a browser at:

`http://<windows-ip>:8765`

No Android app is required for browser printing.

## Android app features

- Automatic Windows Print Hub discovery over UDP.
- Manual IP fallback under Advanced.
- Installed printer list from Windows.
- PDF and image selection.
- First-page PDF preview / image preview.
- Copies: 1-99.
- Color or Black & White.
- Duplex: Simplex, Long edge, Short edge.
- Orientation: Portrait or Landscape.
- Paper size: A4, Letter, Legal, A5.
- Live job polling: queued, printing, completed, failed.

## Windows Print Hub features

- Browser print page.
- Installed printer detection and basic online/status information.
- Direct Windows printer-device rendering for PDF/images.
- SQLite job history.
- Job status and error details.
- REST endpoints for Android/browser clients.
- UDP beacon plus request/response discovery for hotspot networks.

## Printer-driver note

Color, duplex, orientation and paper-size settings are passed through the Windows printer DEVMODE. A setting only works if the installed printer and its Windows driver support that option. For example, a simplex-only printer cannot physically duplex even if Duplex is selected.

## Build outputs

GitHub Actions builds:

- `PhonePrinter-APK` — Android debug APK
- `PhonePrinter-Windows` — Windows EXE

Open the repository **Actions → Build Phone Printer** and download the artifacts from a successful run.

## Local network security

This prototype is intended for a trusted hotspot/LAN. Authentication is not enabled yet, so do not expose port `8765` directly to the public internet.
