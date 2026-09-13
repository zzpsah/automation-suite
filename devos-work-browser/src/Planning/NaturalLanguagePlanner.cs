using Devos.WorkBrowser.Runtime;

namespace Devos.WorkBrowser.Planning;

public sealed record PlannedCommand(IReadOnlyList<BrowserAction> Actions, bool RequiresApproval, string Summary);

public sealed class NaturalLanguagePlanner
{
    private readonly ApprovalPolicy _approvalPolicy = new();

    public PlannedCommand Plan(string input)
    {
        var text = (input ?? string.Empty).Trim();
        if (text.Length == 0) throw new ArgumentException("Command cannot be empty.", nameof(input));

        var lower = text.ToLowerInvariant();
        if (lower.StartsWith("read "))
        {
            var target = text[5..].Trim();
            return Build(new[] { new BrowserAction(BrowserActionKind.ReadText, target) }, OperationKind.Read, $"Read {target}");
        }

        if (lower.StartsWith("click "))
        {
            var target = text[6..].Trim();
            return Build(new[] { new BrowserAction(BrowserActionKind.Click, target) }, OperationKind.Click, $"Click {target}");
        }

        if (lower.StartsWith("type ") && lower.Contains(" into "))
        {
            var splitIndex = lower.IndexOf(" into ", StringComparison.Ordinal);
            var value = text[5..splitIndex].Trim();
            var target = text[(splitIndex + 6)..].Trim();
            return Build(new[] { new BrowserAction(BrowserActionKind.Type, target, value) }, OperationKind.Type, $"Type into {target}");
        }

        if (lower.StartsWith("wait for "))
        {
            var target = text[9..].Trim();
            return Build(new[] { new BrowserAction(BrowserActionKind.WaitForSelector, target) }, OperationKind.Read, $"Wait for {target}");
        }

        if (lower.StartsWith("submit "))
        {
            var target = text[7..].Trim();
            return Build(new[] { new BrowserAction(BrowserActionKind.Click, target) }, OperationKind.Submit, $"Submit via {target}");
        }

        throw new NotSupportedException("Command is outside the constrained planner grammar.");
    }

    private PlannedCommand Build(IReadOnlyList<BrowserAction> actions, OperationKind kind, string summary)
        => new(actions, _approvalPolicy.RequiresApproval(kind), summary);
}

public enum OperationKind
{
    Navigate,
    Read,
    Click,
    Type,
    Download,
    Upload,
    Submit,
    Delete,
    Send
}

public sealed class ApprovalPolicy
{
    public bool RequiresApproval(OperationKind kind) => kind is OperationKind.Upload or OperationKind.Submit or OperationKind.Delete or OperationKind.Send;
}
