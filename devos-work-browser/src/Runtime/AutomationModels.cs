namespace Devos.WorkBrowser.Runtime;

public enum BrowserActionKind
{
    Navigate,
    Click,
    Type,
    ReadText,
    WaitForSelector
}

public sealed record BrowserAction(
    BrowserActionKind Kind,
    string Target,
    string? Value = null,
    string? ExpectedText = null,
    int MaxAttempts = 2);

public sealed record ActionResult(bool Success, string? Output, int Attempts, string? Error = null);

public interface IAutomationAdapter
{
    Task NavigateAsync(string target)
        => Task.FromException(new NotSupportedException("Navigation is not supported by this adapter."));
    Task ClickAsync(string target);
    Task TypeAsync(string target, string value);
    Task<string?> ReadTextAsync(string target);
    Task<bool> WaitForSelectorAsync(string target, TimeSpan timeout, TimeSpan? pollInterval = null);
}
