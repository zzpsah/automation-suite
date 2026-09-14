using System.IO;
using System.Windows;
using Devos.WorkBrowser.Browser;

namespace Devos.WorkBrowser;

public partial class App : Application
{
    private static readonly TimeSpan BrowserStartupTimeout = TimeSpan.FromSeconds(10);

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
            if (await WaitForBrowserAsync(window, BrowserStartupTimeout)) return;

            // A valid runtime/loader with a hanging EnsureCoreWebView2Async is commonly
            // caused by a damaged or locked user-data folder. Retry once with a brand-new
            // isolated state/profile root rather than leaving a live but unusable shell.
            try
            {
                window.Close();
            }
            catch
            {
                // Recovery should continue even if the failed WebView instance resists close.
            }

            var recoveryRoot = Path.Combine(
                Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
                "DEVOS", "WorkBrowser-Recovery",
                DateTimeOffset.UtcNow.ToString("yyyyMMdd-HHmmss"));
            Directory.CreateDirectory(recoveryRoot);

            var recoveryWindow = new MainWindow(recoveryRoot, enableRecoveryPrompts: false)
            {
                Title = "DEVOS Work Browser v0.1.2 — Recovery Profile"
            };
            recoveryWindow.Show();

            if (await WaitForBrowserAsync(recoveryWindow, BrowserStartupTimeout))
            {
                MessageBox.Show(
                    "The normal DEVOS browser profile did not initialize, but a fresh recovery profile started successfully.\n\n" +
                    "You can use the browser now. DEVOS will keep this recovery profile isolated from the damaged/locked profile.",
                    "DEVOS Work Browser — Browser recovered",
                    MessageBoxButton.OK,
                    MessageBoxImage.Information);
                return;
            }

            diagnostic = BrowserRuntimeDiagnostics.Probe();
            diagnosticPath = BrowserRuntimeDiagnostics.WriteLog(stateRoot, diagnostic);
            MessageBox.Show(
                $"The embedded WebView2 browser failed with both the normal profile and a fresh recovery profile.\n\n" +
                $"Loader present: {diagnostic.LoaderPresent}\n" +
                $"WebView2 Runtime: {diagnostic.RuntimeVersion ?? "not detected"}\n" +
                $"Recovery profile: {recoveryRoot}\n\n" +
                $"Diagnostic log:\n{diagnosticPath}\n\n" +
                "Please send this diagnostic log when reporting the issue.",
                "DEVOS Work Browser v0.1.2 — Browser initialization failed",
                MessageBoxButton.OK,
                MessageBoxImage.Warning);
            return;
        }

        var selfTestRoot = Path.Combine(Path.GetTempPath(), "devos-work-browser-selftest", Guid.NewGuid().ToString("N"));
        var windowForSelfTest = new MainWindow(selfTestRoot, enableRecoveryPrompts: false)
        {
            Title = "DEVOS Work Browser v0.1.2 — Self Test"
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

    private static async Task<bool> WaitForBrowserAsync(MainWindow window, TimeSpan timeout)
    {
        var deadline = DateTimeOffset.UtcNow + timeout;
        while (DateTimeOffset.UtcNow < deadline && window.IsVisible)
        {
            if (window.CreateAutomationAdapter() is not null) return true;
            await Task.Delay(250);
        }

        return window.IsVisible && window.CreateAutomationAdapter() is not null;
    }
}
