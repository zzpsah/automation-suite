using System.IO;
using System.Windows;

namespace Devos.WorkBrowser;

public partial class App : Application
{
    protected override async void OnStartup(StartupEventArgs e)
    {
        base.OnStartup(e);

        var selfTest = e.Args.Any(arg => string.Equals(arg, "--self-test", StringComparison.OrdinalIgnoreCase));
        if (!selfTest)
        {
            new MainWindow().Show();
            return;
        }

        var selfTestRoot = Path.Combine(Path.GetTempPath(), "devos-work-browser-selftest", Guid.NewGuid().ToString("N"));
        var window = new MainWindow(selfTestRoot, enableRecoveryPrompts: false)
        {
            Title = "DEVOS Work Browser — Self Test"
        };

        window.Show();
        var exitCode = 1;
        try
        {
            var result = await window.RunAutomatedAcceptanceAsync();
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
                window.Close();
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
