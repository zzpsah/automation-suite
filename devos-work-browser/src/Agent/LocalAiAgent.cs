using System.Net.Http;
using System.Net.Http.Json;
using System.Text.Json;
using Devos.WorkBrowser.Runtime;

namespace Devos.WorkBrowser.Agent;

public sealed record LocalAgentDecision(
    bool Done,
    string Message,
    BrowserAction? Action,
    string Description);

public sealed class LocalAiAgent
{
    private const string DefaultEndpoint = "http://127.0.0.1:11434/";
    private const string DefaultModel = "qwen3:4b";
    private readonly HttpClient _http;

    public LocalAiAgent(HttpClient? httpClient = null, string? model = null)
    {
        Model = string.IsNullOrWhiteSpace(model)
            ? Environment.GetEnvironmentVariable("DEVOS_LOCAL_MODEL") ?? DefaultModel
            : model;

        if (httpClient is not null)
        {
            _http = httpClient;
            if (_http.BaseAddress is null)
            {
                _http.BaseAddress = ResolveEndpoint();
            }
        }
        else
        {
            _http = new HttpClient
            {
                BaseAddress = ResolveEndpoint(),
                Timeout = TimeSpan.FromSeconds(45)
            };
        }
    }

    public string Model { get; }

    public async Task<bool> IsAvailableAsync(CancellationToken cancellationToken = default)
    {
        if (string.Equals(
                Environment.GetEnvironmentVariable("DEVOS_DISABLE_LOCAL_AI"),
                "1",
                StringComparison.OrdinalIgnoreCase))
        {
            return false;
        }

        using var timeout = CancellationTokenSource.CreateLinkedTokenSource(cancellationToken);
        timeout.CancelAfter(TimeSpan.FromMilliseconds(900));

        try
        {
            using var response = await _http.GetAsync("api/tags", timeout.Token);
            if (!response.IsSuccessStatusCode) return false;

            var json = await response.Content.ReadAsStringAsync(timeout.Token);
            using var document = JsonDocument.Parse(json);
            if (!document.RootElement.TryGetProperty("models", out var models) || models.ValueKind != JsonValueKind.Array)
            {
                return false;
            }

            foreach (var item in models.EnumerateArray())
            {
                if (!item.TryGetProperty("name", out var nameElement)) continue;
                var name = nameElement.GetString();
                if (string.Equals(name, Model, StringComparison.OrdinalIgnoreCase) ||
                    name?.StartsWith(Model + ":", StringComparison.OrdinalIgnoreCase) == true)
                {
                    return true;
                }
            }

            return false;
        }
        catch
        {
            return false;
        }
    }

    public async Task<LocalAgentDecision> GetNextStepAsync(
        string goal,
        string pageSnapshot,
        string? previousResult,
        CancellationToken cancellationToken = default)
    {
        var systemPrompt = """
You are the local planning brain for DEVOS Work Browser. You do NOT directly control the computer.
Return exactly one JSON object and no markdown.

Schema:
{"done":false,"message":"short status","description":"what this action does","action":{"kind":"Navigate|Click|Type|ReadText|WaitForSelector","target":"...","value":null}}
Or when the goal is complete or user interaction is required:
{"done":true,"message":"result or required user action","description":"","action":null}

Rules:
- Produce at most ONE browser action per turn. DEVOS will execute it, verify, then ask you again.
- Use CSS selectors exactly as supplied in PAGE SNAPSHOT. Do not invent a selector when a matching supplied selector exists.
- Navigate must use a full http/https URL, a hostname/domain, or a known DEVOS alias. Never turn an open/navigate goal into a search query.
- Never ask DEVOS to solve CAPTCHA, OTP, MFA, or verification challenges. Return done=true and tell the user to complete that step personally.
- Never output shell commands, JavaScript, filesystem operations, or arbitrary code.
- Do not claim an action succeeded until PREVIOUS RESULT or the current page proves it.
- For actions that may submit, save, delete, send, upload, purchase, pay, register, confirm, approve, publish, or otherwise commit data, say that explicitly in description. DEVOS applies its own approval policy.
- PAGE SNAPSHOT intentionally excludes typed field values/password contents. Do not infer hidden values.
""";

        var userPrompt = $"""
GOAL:
{goal}

PREVIOUS RESULT:
{previousResult ?? "<none>"}

PAGE SNAPSHOT:
{pageSnapshot}
""";

        var payload = new
        {
            model = Model,
            stream = false,
            format = "json",
            messages = new object[]
            {
                new { role = "system", content = systemPrompt },
                new { role = "user", content = userPrompt }
            },
            options = new { temperature = 0.1 }
        };

        using var response = await _http.PostAsJsonAsync("api/chat", payload, cancellationToken);
        var body = await response.Content.ReadAsStringAsync(cancellationToken);
        if (!response.IsSuccessStatusCode)
        {
            throw new InvalidOperationException($"Local AI request failed ({(int)response.StatusCode}): {TrimForError(body)}");
        }

        using var envelope = JsonDocument.Parse(body);
        if (!envelope.RootElement.TryGetProperty("message", out var message) ||
            !message.TryGetProperty("content", out var contentElement))
        {
            throw new InvalidOperationException("Local AI response did not contain message.content.");
        }

        var content = contentElement.GetString();
        if (string.IsNullOrWhiteSpace(content))
        {
            throw new InvalidOperationException("Local AI returned an empty decision.");
        }

        return ParseDecision(content);
    }

    public static LocalAgentDecision ParseDecision(string content)
    {
        var json = ExtractJsonObject(content);
        using var document = JsonDocument.Parse(json);
        var root = document.RootElement;

        var done = root.TryGetProperty("done", out var doneElement) && doneElement.ValueKind == JsonValueKind.True;
        var message = root.TryGetProperty("message", out var messageElement)
            ? messageElement.GetString() ?? string.Empty
            : string.Empty;
        var description = root.TryGetProperty("description", out var descriptionElement)
            ? descriptionElement.GetString() ?? string.Empty
            : string.Empty;

        if (done)
        {
            return new LocalAgentDecision(true, message, null, description);
        }

        if (!root.TryGetProperty("action", out var actionElement) || actionElement.ValueKind != JsonValueKind.Object)
        {
            throw new InvalidOperationException("Local AI decision is missing action.");
        }

        var kindText = actionElement.TryGetProperty("kind", out var kindElement)
            ? kindElement.GetString()
            : null;
        if (!Enum.TryParse<BrowserActionKind>(kindText, ignoreCase: true, out var kind))
        {
            throw new InvalidOperationException($"Unsupported local AI action kind: {kindText}");
        }

        var target = actionElement.TryGetProperty("target", out var targetElement)
            ? targetElement.GetString()?.Trim()
            : null;
        if (string.IsNullOrWhiteSpace(target))
        {
            throw new InvalidOperationException("Local AI action target is empty.");
        }

        var value = actionElement.TryGetProperty("value", out var valueElement) && valueElement.ValueKind != JsonValueKind.Null
            ? valueElement.GetString()
            : null;
        if (kind == BrowserActionKind.Type && value is null)
        {
            throw new InvalidOperationException("Local AI Type action requires a value.");
        }

        return new LocalAgentDecision(
            false,
            message,
            new BrowserAction(kind, target, value, MaxAttempts: 2),
            description);
    }

    private static Uri ResolveEndpoint()
    {
        var configured = Environment.GetEnvironmentVariable("DEVOS_LOCAL_AI_ENDPOINT");
        if (Uri.TryCreate(configured, UriKind.Absolute, out var endpoint))
        {
            var text = endpoint.ToString();
            return text.EndsWith('/') ? endpoint : new Uri(text + "/");
        }

        return new Uri(DefaultEndpoint);
    }

    private static string ExtractJsonObject(string content)
    {
        var start = content.IndexOf('{');
        var end = content.LastIndexOf('}');
        if (start < 0 || end <= start)
        {
            throw new InvalidOperationException("Local AI response did not contain a JSON object.");
        }
        return content[start..(end + 1)];
    }

    private static string TrimForError(string value)
    {
        var compact = value.Replace('\r', ' ').Replace('\n', ' ').Trim();
        return compact.Length <= 240 ? compact : compact[..240] + "…";
    }
}

public static class AgentSafetyPolicy
{
    private static readonly string[] CommitKeywords =
    {
        "submit", "save", "delete", "remove", "send", "upload", "pay", "purchase",
        "confirm", "register", "finalize", "finalise", "apply", "approve", "publish", "post",
        "commit", "checkout", "place order"
    };

    private static readonly string[] HumanOnlyKeywords =
    {
        "captcha", "otp", "one time password", "one-time password", "verification code", "2fa", "mfa"
    };

    public static bool RequiresApproval(BrowserAction action, string? description, string? elementDescriptor)
    {
        if (action.Kind is not (BrowserActionKind.Click or BrowserActionKind.Type)) return false;
        var text = $"{description} {elementDescriptor} {action.Target}".ToLowerInvariant();
        return CommitKeywords.Any(keyword => text.Contains(keyword, StringComparison.Ordinal)) ||
               text.Contains("type=submit", StringComparison.Ordinal);
    }

    public static bool RequiresHumanInteraction(string? description, string? elementDescriptor)
    {
        var text = $"{description} {elementDescriptor}".ToLowerInvariant();
        return HumanOnlyKeywords.Any(keyword => text.Contains(keyword, StringComparison.Ordinal));
    }
}
