namespace Devos.WorkBrowser.Runtime;

public sealed class ActionExecutor
{
    private readonly IAutomationAdapter _adapter;

    public ActionExecutor(IAutomationAdapter adapter) => _adapter = adapter;

    public async Task<ActionResult> ExecuteAsync(BrowserAction action, CancellationToken cancellationToken = default)
    {
        var maxAttempts = Math.Max(1, action.MaxAttempts);
        string? lastError = null;

        for (var attempt = 1; attempt <= maxAttempts; attempt++)
        {
            cancellationToken.ThrowIfCancellationRequested();
            try
            {
                var output = await ExecuteOnceAsync(action);
                if (await VerifyAsync(action, output))
                {
                    return new ActionResult(true, output, attempt);
                }

                lastError = "Verification failed";
            }
            catch (Exception ex)
            {
                lastError = ex.Message;
            }

            if (attempt < maxAttempts)
            {
                await Task.Delay(TimeSpan.FromMilliseconds(150 * attempt), cancellationToken);
            }
        }

        return new ActionResult(false, null, maxAttempts, lastError ?? "Action failed");
    }

    private async Task<string?> ExecuteOnceAsync(BrowserAction action)
    {
        switch (action.Kind)
        {
            case BrowserActionKind.Navigate:
                await _adapter.NavigateAsync(action.Target);
                return action.Target;
            case BrowserActionKind.Click:
                await _adapter.ClickAsync(action.Target);
                return null;
            case BrowserActionKind.Type:
                await _adapter.TypeAsync(action.Target, action.Value ?? string.Empty);
                return null;
            case BrowserActionKind.ReadText:
                return await _adapter.ReadTextAsync(action.Target);
            case BrowserActionKind.WaitForSelector:
                return (await _adapter.WaitForSelectorAsync(action.Target, TimeSpan.FromSeconds(5))).ToString();
            default:
                throw new NotSupportedException($"Unsupported action kind: {action.Kind}");
        }
    }

    private async Task<bool> VerifyAsync(BrowserAction action, string? output)
    {
        if (action.ExpectedText is null)
        {
            return action.Kind != BrowserActionKind.WaitForSelector || string.Equals(output, "True", StringComparison.OrdinalIgnoreCase);
        }

        var text = action.Kind == BrowserActionKind.ReadText
            ? output
            : await _adapter.ReadTextAsync(action.Target);

        return text?.Contains(action.ExpectedText, StringComparison.OrdinalIgnoreCase) == true;
    }
}
