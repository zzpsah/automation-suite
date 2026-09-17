namespace Devos.WorkBrowser.Browser;

public static class CommandNavigationResolver
{
    private static readonly IReadOnlyDictionary<string, string> KnownSites =
        new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase)
        {
            ["eshikshakosh"] = "https://eshikshakosh.bihar.gov.in/",
            ["e-shikshakosh"] = "https://eshikshakosh.bihar.gov.in/",
            ["e shikshakosh"] = "https://eshikshakosh.bihar.gov.in/",
            ["e shiksha kosh"] = "https://eshikshakosh.bihar.gov.in/"
        };

    public static Uri Resolve(string input)
    {
        var text = (input ?? string.Empty).Trim();
        if (text.Length == 0)
        {
            throw new ArgumentException("Navigation target cannot be empty.", nameof(input));
        }

        if (KnownSites.TryGetValue(text, out var knownUrl))
        {
            return new Uri(knownUrl, UriKind.Absolute);
        }

        if (Uri.TryCreate(text, UriKind.Absolute, out var absolute) &&
            (absolute.Scheme == Uri.UriSchemeHttp || absolute.Scheme == Uri.UriSchemeHttps))
        {
            return absolute;
        }

        if (!text.Any(char.IsWhiteSpace) && text.Contains('.'))
        {
            if (Uri.TryCreate($"https://{text}", UriKind.Absolute, out var hostUri))
            {
                return hostUri;
            }
        }

        throw new InvalidOperationException(
            $"Unknown direct site name: {text}. Use a full domain such as example.com, or a known DEVOS portal alias.");
    }
}
