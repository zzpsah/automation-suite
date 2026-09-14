using System.IO;
using System.Windows;
using Devos.WorkBrowser.Browser;

namespace Devos.WorkBrowser;

public partial class App : Application
{
    protected override async void OnStartup(StartupEventArgs e)
    {
        base.OnStartup(e);

        var selfTest = e.Args.Any(arg => string.Equals(arg, "--self-test", StringComparison.OrdinalIgnoreCase));
        if (!selfTest)
        {
            var stateRoot = Path.Combine(
                Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
                "DEVOS", "WorkBrowser");
            var diagnostic = BrowserRuntimeDiagnostics.Probe();
            var diagnosticPath = BrowserRuntimeDiagnostics.WriteLog(stateRoot, diagnostic);

            if (!diagnostic.IsReady)
            {
                var problem = !diagnostic.LoaderPresent
                    ? $"WebView2Loader.dll is missing from the application folder.\nExpected: {diagnostic.LoaderPath}"
                    : $"Microsoft Edge WebView2 Runtime is unavailable.\n{diagnostic.Error}";

                MessageBox.Show(
                    $"DEVOS Work Browser cannot start its browser engine.\n\n{problem}\n\nDiagnostic log:\n{diagnosticPath}",
                    "DEVOS Work Browser — Browser startup failed",
                    MessageBoxButton.OK,
                    MessageBoxImage.Error);
                Shutdown(2);
                return;
            }

            var window = new MainWindow();
            window.Show();

            // The outer WPF shell can remain alive even when WebView2 initialization
            // fails. Verify that a real CoreWebView2-backed adapter becomes available,
            // otherwise surface the failure instead of leaving apparently dead buttons.
            var deadline = DateTimeOffset.UtcNow + TimeSpan.FromSeconds(20);
            while (DateTimeOffset.UtcNow < deadline && window.IsVisible)
            {
                if (window.CreateAutomationAdapter() is not null) return;
                await Task.Delay(250);
            }

            if (window.IsVisible && window.CreateAutomationAdapter() is null)
            {
                diagnostic = BrowserRuntimeDiagnostics.Probe();
                diagnosticPath = BrowserRuntimeDiagnostics.WriteLog(stateRoot, diagnostic);
                MessageBox.Show(
                    $"The DEVOS window opened, but the embedded WebView2 browser did not initialize within 20 seconds.\n\n" +
                    $"Loader present: {diagnostic.LoaderPresent}\n" +
                    $"WebView2 Runtime: {diagnostic.RuntimeVersion ?? "not detected"}\n\n" +
                    $"Diagnostic log:\n{diagnosticPath}\n\n" +
                    "Please send this diagnostic log when reporting the issue.",
                    "DEVOS Work Browser — Browser initialization failed",
                    MessageBoxButton.OK,
                    MessageBoxImage.Warning);
            }
            return;
        }

        var selfTestRoot = Path.Combine(Path.GetTempPath(), "devos-work-browser-selftest", Guid.NewGuid().ToString("N"));
        var windowForSelfTest = new MainWindow(selfTestRoot, enableRecoveryPrompts: false)
        {
            Title = "DEVOS Work Browser — Self Test"
        };

        windowForSelfTest.Show();
        var exitCode = 1;
        try
        {
            var result = await windowForSelfTest.RunAutomatedAcceptanceAsync();
            exitCode = result ? 0 : 1;
        }
        catch (Exception ex)
        {
            Console.Error.WriteLine(ex);
            exitCode = 1;
        }
        finally
        {
            try
            {
                windowForSelfTest.Close();
                if (Directory.Exists(selfTestRoot)) Directory.Delete(selfTestRoot, recursive: true);
            }
            catch
            {
                // Self-test cleanup must not hide the actual acceptance result.
            }
        }

        Shutdown(exitCode);
    }
}
