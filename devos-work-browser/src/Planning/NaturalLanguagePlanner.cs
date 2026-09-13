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

        var segments = text.Split(';', StringSplitOptions.RemoveEmptyEntries | StringSplitOptions.TrimEntries);
        if (segments.Length == 0) throw new ArgumentException("Command cannot be empty.", nameof(input));

        var actions = new List<BrowserAction>();
        var summaries = new List<string>();
        var requiresApproval = false;

        foreach (var segment in segments)
        {
            var planned = PlanSingle(segment);
            actions.AddRange(planned.Actions);
            summaries.Add(planned.Summary);
            requiresApproval |= planned.RequiresApproval;
        }

        return new PlannedCommand(actions, requiresApproval, string.Join(" → ", summaries));
    }

    private PlannedCommand PlanSingle(string text)
    {
        var lower = text.ToLowerInvariant();
        if (lower.StartsWith("read "))
        {
            var target = RequireTarget(text[5..], "read");
            return Build(new[] { new BrowserAction(BrowserActionKind.ReadText, target) }, OperationKind.Read, $"Read {target}");
        }

        if (lower.StartsWith("click "))
        {
            var target = RequireTarget(text[6..], "click");
            return Build(new[] { new BrowserAction(BrowserActionKind.Click, target) }, OperationKind.Click, $"Click {target}");
        }

        if (lower.StartsWith("type ") && lower.Contains(" into "))
        {
            var splitIndex = lower.IndexOf(" into ", StringComparison.Ordinal);
            var value = text[5..splitIndex].Trim();
            var target = RequireTarget(text[(splitIndex + 6)..], "type");
            return Build(new[] { new BrowserAction(BrowserActionKind.Type, target, value) }, OperationKind.Type, $"Type into {target}");
        }

        if (lower.StartsWith("wait for "))
        {
            var target = RequireTarget(text[9..], "wait for");
            return Build(new[] { new BrowserAction(BrowserActionKind.WaitForSelector, target) }, OperationKind.Read, $"Wait for {target}");
        }

        if (lower.StartsWith("submit "))
        {
            var target = RequireTarget(text[7..], "submit");
            return Build(new[] { new BrowserAction(BrowserActionKind.Click, target) }, OperationKind.Submit, $"Submit via {target}");
        }

        throw new NotSupportedException($"Command is outside the constrained planner grammar: {text}");
    }

    private PlannedCommand Build(IReadOnlyList<BrowserAction> actions, OperationKind kind, string summary)
        => new(actions, _approvalPolicy.RequiresApproval(kind), summary);

    private static string RequireTarget(string value, string operation)
    {
        var target = value.Trim();
        if (target.Length == 0) throw new ArgumentException($"{operation} requires a target.");
        return target;
    }
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
