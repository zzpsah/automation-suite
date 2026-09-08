# Phone Printer MVP

Print from an Android phone to a USB printer connected to a Windows PC.

## Network

1. Turn on the Android phone hotspot.
2. Connect the Windows PC to that hotspot.
3. Connect the printer to Windows by USB and ensure it prints normally from Windows first.
4. Run `PhonePrinterBridge.exe` on Windows.
5. Allow the app through Windows Firewall if prompted.
6. Note the Windows hotspot IP shown by the bridge.
7. In the Android app, enter that IP and tap **Connect / Refresh Printers**.
8. Select the installed printer, choose a PDF/image, and tap **PRINT**.

## Build outputs

GitHub Actions builds two artifacts:

- `PhonePrinter-APK` — Android debug APK
- `PhonePrinter-Windows` — Windows EXE

Open the repository Actions tab, select **Build Phone Printer**, and download the artifacts from a successful run.

## Current MVP limitations

- Local hotspot/LAN only.
- PDF and common image files only.
- No authentication in this first local-network prototype.
- Windows uses the file type's registered print handler, so a PDF reader with Windows `printto` support may be required for PDF printing.
