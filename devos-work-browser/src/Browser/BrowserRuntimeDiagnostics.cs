using System.IO;
using Microsoft.Web.WebView2.Core;

namespace Devos.WorkBrowser.Browser;

internal sealed record BrowserRuntimeDiagnostic(
    bool LoaderPresent,
    string LoaderPath,
    bool RuntimeAvailable,
    string? RuntimeVersion,
    string? Error)
{
    public bool IsReady => LoaderPresent && RuntimeAvailable;
}

internal static class BrowserRuntimeDiagnostics
{
    public static BrowserRuntimeDiagnostic Probe()
    {
        var loaderPath = Path.Combine(AppContext.BaseDirectory, "WebView2Loader.dll");
        var loaderPresent = File.Exists(loaderPath);

        try
        {
            var version = CoreWebView2Environment.GetAvailableBrowserVersionString();
            var runtimeAvailable = !string.IsNullOrWhiteSpace(version);
            return new BrowserRuntimeDiagnostic(
                loaderPresent,
                loaderPath,
                runtimeAvailable,
                version,
                runtimeAvailable ? null : "Microsoft Edge WebView2 Runtime was not detected.");
        }
        catch (Exception ex)
        {
            return new BrowserRuntimeDiagnostic(
                loaderPresent,
                loaderPath,
                false,
                null,
                $"{ex.GetType().Name}: {ex.Message}");
        }
    }

    public static string WriteLog(string stateRoot, BrowserRuntimeDiagnostic diagnostic, Exception? startupException = null)
    {
        Directory.CreateDirectory(stateRoot);
        var path = Path.Combine(stateRoot, "startup-diagnostics.txt");
        var lines = new List<string>
        {
            $"TimestampUtc: {DateTimeOffset.UtcNow:O}",
            $"AppBaseDirectory: {AppContext.BaseDirectory}",
            $"ProcessArchitecture: {System.Runtime.InteropServices.RuntimeInformation.ProcessArchitecture}",
            $"OSDescription: {System.Runtime.InteropServices.RuntimeInformation.OSDescription}",
            $"LoaderPresent: {diagnostic.LoaderPresent}",
            $"LoaderPath: {diagnostic.LoaderPath}",
            $"RuntimeAvailable: {diagnostic.RuntimeAvailable}",
            $"RuntimeVersion: {diagnostic.RuntimeVersion ?? "<none>"}",
            $"ProbeError: {diagnostic.Error ?? "<none>"}"
        };

        if (startupException is not null)
        {
            lines.Add($"StartupExceptionType: {startupException.GetType().FullName}");
            lines.Add($"StartupException: {startupException}");
        }

        File.WriteAllLines(path, lines);
        return path;
    }
}
