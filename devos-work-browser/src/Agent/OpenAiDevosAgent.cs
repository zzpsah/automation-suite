using System.Net.Http;
using System.Net.Http.Headers;
using System.Text;
using System.Text.Json;
using Devos.WorkBrowser.Planning;
using Devos.WorkBrowser.Runtime;

namespace Devos.WorkBrowser.Agent;

public sealed class OpenAiDevosAgent
{
    private const int MaxActions = 12;
    private const string DefaultModel = "gpt-5.6-luna";
    private readonly HttpClient _http;
    private readonly string _apiKey;
    private readonly string _model;

    public OpenAiDevosAgent(HttpClient http, string apiKey, string? model = null)
    {
        _http = http;
        _apiKey = apiKey;
        _model = string.IsNullOrWhiteSpace(model) ? DefaultModel : model.Trim();
    }

    public string Model => _model;

    public static OpenAiDevosAgent? TryCreateFromEnvironment(HttpClient? http = null)
    {
        var key = Environment.GetEnvironmentVariable("OPENAI_API_KEY");
        if (string.IsNullOrWhiteSpace(key)) return null;
        var model = Environment.GetEnvironmentVariable("DEVOS_OPENAI_MODEL");
        return new OpenAiDevosAgent(http ?? new HttpClient(), key, model);
    }

    public async Task<PlannedCommand> PlanAsync(
        string goal,
        string browserContextJson,
        CancellationToken cancellationToken = default)
    {
        if (string.IsNullOrWhiteSpace(goal))
            throw new ArgumentException("Goal cannot be empty.", nameof(goal));

        using var request = new HttpRequestMessage(HttpMethod.Post, "https://api.openai.com/v1/responses");
        request.Headers.Authorization = new AuthenticationHeaderValue("Bearer", _apiKey);
        request.Content = new StringContent(BuildRequestJson(goal, browserContextJson), Encoding.UTF8, "application/json");

        using var response = await _http.SendAsync(request, cancellationToken);
        var responseJson = await response.Content.ReadAsStringAsync(cancellationToken);
        if (!response.IsSuccessStatusCode)
        {
            throw new InvalidOperationException($"OpenAI agent request failed ({(int)response.StatusCode}).");
        }

        return ParseResponseJson(responseJson, goal);
    }

    public string BuildRequestJson(string goal, string browserContextJson)
    {
        var instructions = """
You are the DEVOS Work Browser planner. Convert the user's browser goal into a short, deterministic browser plan.
Return JSON only. Do not use markdown.
Schema:
{"summary":"short summary","actions":[{"operation":"navigate|click|type|read|wait|submit|delete|upload|send","target":"URL or exact CSS selector","value":"text only for type, otherwise null"}]}
Rules:
- Maximum 12 actions.
- Use navigate only with a full http/https URL.
- For click/type/read/wait/submit/delete/upload/send, use ONLY a selector listed in the supplied browser context. Never invent a selector.
- Never include passwords, OTPs, CAPTCHA answers, API keys, cookies, tokens, or other credentials in a type action.
- Label committing actions accurately: submit, delete, upload, or send. DEVOS will require human approval locally.
- Prefer read-only actions when the user only asks for information.
- If the page context is insufficient, return the safest useful partial plan, such as navigate or wait; do not guess destructive actions.
""";

        var input = $"User goal:\n{goal}\n\nCurrent browser structural context (no form values):\n{browserContextJson}";
        return JsonSerializer.Serialize(new
        {
            model = _model,
            instructions,
            input,
            max_output_tokens = 1600
        });
    }

    public static PlannedCommand ParseResponseJson(string responseJson, string originalGoal)
    {
        using var document = JsonDocument.Parse(responseJson);
        var outputText = ExtractOutputText(document.RootElement);
        if (string.IsNullOrWhiteSpace(outputText))
            throw new InvalidOperationException("OpenAI agent returned no plan text.");

        var json = StripCodeFence(outputText.Trim());
        using var planDocument = JsonDocument.Parse(json);
        var root = planDocument.RootElement;
        var summary = root.TryGetProperty("summary", out var summaryNode)
            ? summaryNode.GetString()?.Trim()
            : null;
        summary = string.IsNullOrWhiteSpace(summary) ? originalGoal.Trim() : summary;

        if (!root.TryGetProperty("actions", out var actionsNode) || actionsNode.ValueKind != JsonValueKind.Array)
            throw new InvalidOperationException("OpenAI agent plan is missing actions.");

        var actions = new List<BrowserAction>();
        var requiresApproval = SafetyApprovalClassifier.RequiresApprovalForGoal(originalGoal);
        foreach (var item in actionsNode.EnumerateArray())
        {
            if (actions.Count >= MaxActions)
                throw new InvalidOperationException($"OpenAI agent plan exceeded the {MaxActions}-action safety limit.");

            var operation = RequiredString(item, "operation").ToLowerInvariant();
            var target = RequiredString(item, "target");
            var value = item.TryGetProperty("value", out var valueNode) && valueNode.ValueKind == JsonValueKind.String
                ? valueNode.GetString()
                : null;

            switch (operation)
            {
                case "navigate":
                    var uri = Browser.CommandNavigationResolver.Resolve(target);
                    actions.Add(new BrowserAction(BrowserActionKind.Navigate, uri.ToString()));
                    break;
                case "click":
                    actions.Add(new BrowserAction(BrowserActionKind.Click, target));
                    break;
                case "type":
                    if (value is null) throw new InvalidOperationException("AI type action is missing text value.");
                    actions.Add(new BrowserAction(BrowserActionKind.Type, target, value));
                    break;
                case "read":
                    actions.Add(new BrowserAction(BrowserActionKind.ReadText, target));
                    break;
                case "wait":
                    actions.Add(new BrowserAction(BrowserActionKind.WaitForSelector, target));
                    break;
                case "submit":
                case "delete":
                case "upload":
                case "send":
                    requiresApproval = true;
                    actions.Add(new BrowserAction(BrowserActionKind.Click, target));
                    break;
                default:
                    throw new InvalidOperationException($"OpenAI agent returned unsupported operation: {operation}");
            }
        }

        if (actions.Count == 0)
            throw new InvalidOperationException("OpenAI agent returned an empty plan.");

        return new PlannedCommand(actions, requiresApproval, summary!);
    }

    private static string RequiredString(JsonElement item, string name)
    {
        if (!item.TryGetProperty(name, out var node) || node.ValueKind != JsonValueKind.String || string.IsNullOrWhiteSpace(node.GetString()))
            throw new InvalidOperationException($"OpenAI agent action is missing {name}.");
        return node.GetString()!.Trim();
    }

    private static string? ExtractOutputText(JsonElement root)
    {
        if (!root.TryGetProperty("output", out var output) || output.ValueKind != JsonValueKind.Array) return null;
        foreach (var item in output.EnumerateArray())
        {
            if (!item.TryGetProperty("content", out var content) || content.ValueKind != JsonValueKind.Array) continue;
            foreach (var part in content.EnumerateArray())
            {
                if (part.TryGetProperty("type", out var type) && type.GetString() == "output_text" &&
                    part.TryGetProperty("text", out var text) && text.ValueKind == JsonValueKind.String)
                {
                    return text.GetString();
                }
            }
        }
        return null;
    }

    private static string StripCodeFence(string text)
    {
        if (!text.StartsWith("```", StringComparison.Ordinal)) return text;
        var firstNewLine = text.IndexOf('\n');
        var lastFence = text.LastIndexOf("```", StringComparison.Ordinal);
        return firstNewLine >= 0 && lastFence > firstNewLine
            ? text[(firstNewLine + 1)..lastFence].Trim()
            : text;
    }
}

public static class SafetyApprovalClassifier
{
    private static readonly string[] CommittingWords =
    [
        "submit", "save", "delete", "remove", "upload", "send", "post", "publish", "confirm", "approve", "pay", "payment", "register", "finalize"
    ];

    public static bool RequiresApprovalForGoal(string goal)
    {
        var text = $" {goal.ToLowerInvariant()} ";
        return CommittingWords.Any(word => text.Contains($" {word} ", StringComparison.Ordinal));
    }
}
