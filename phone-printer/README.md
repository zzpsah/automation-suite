# Phone Printer Hub

Print from Android or any browser to a USB printer connected to a Windows PC.

## Windows GUI

The Windows EXE now uses a desktop GUI and runs the print server internally. No console window is required.

Tabs in the Windows app:

- **Dashboard** — server status, PC name, current local IP, print URL, startup-at-login toggle, open browser print page, exit service.
- **Hotspot** — SSID, password, configure/start hotspot, stop hotspot, refresh status, and open Windows Mobile Hotspot settings.
- **Printers** — installed Windows printers and current status.
- **Print Queue** — job ID, file, printer, source device, status, print options, submitted time, and error details.
- **Logs** — live scrolling application log for server startup, hotspot actions, queue state changes, errors, and admin actions.

Closing the GUI window hides it to the system tray and keeps the print service running. Use the tray icon to reopen it or exit completely.

Enable **Start Phone Printer Hub automatically when I sign in** from the Dashboard to run it in background at Windows login.

## Supported network modes

### Phone hotspot mode

1. Turn on the Android phone hotspot.
2. Connect the Windows PC to that hotspot.
3. Connect the USB printer to Windows and confirm it prints normally from Windows.
4. Run `PhonePrinterBridge.exe`.
5. Allow it through Windows Firewall when prompted.
6. Open the Android app. It discovers the Windows Print Hub over UDP even if DHCP changes the PC IP.
7. Select printer/file/settings and tap **PRINT**.

Manual IP is available only under **Advanced** as a fallback.

### Windows hotspot / normal LAN mode

Use the **Hotspot** tab in the Windows GUI to configure/start the hotspot where the Wi-Fi driver supports the hosted-network command. On newer Windows 11 drivers where that API is disabled, click **Open Windows Mobile Hotspot Settings** and enable the hotspot there.

Any phone, tablet or laptop on the same network can open the browser print page at:

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

## Printer-driver note

Color, duplex, orientation and paper-size settings are passed through the Windows printer DEVMODE. A setting only works if the installed printer and its Windows driver support that option.

## Build outputs

GitHub Actions builds:

- `PhonePrinter-APK` — Android debug APK
- `PhonePrinter-Windows` — Windows GUI EXE

Open the repository **Actions → Build Phone Printer** and download the artifacts from a successful run.

## Local network security

This prototype is intended for a trusted hotspot/LAN. Do not expose port `8765` directly to the public internet.
