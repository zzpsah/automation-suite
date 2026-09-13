namespace Devos.WorkBrowser.Browser;

public static class UrlResolver
{
    private const string HomeUrl = "https://www.google.com/";
    private const string SearchBase = "https://www.google.com/search?q=";

    public static Uri Resolve(string? input)
    {
        var value = (input ?? string.Empty).Trim();
        if (value.Length == 0)
        {
            return new Uri(HomeUrl);
        }

        if (Uri.TryCreate(value, UriKind.Absolute, out var absolute) &&
            (absolute.Scheme == Uri.UriSchemeHttp || absolute.Scheme == Uri.UriSchemeHttps))
        {
            return absolute;
        }

        if (!value.Any(char.IsWhiteSpace) && value.Contains('.'))
        {
            var candidate = $"https://{value}";
            if (Uri.TryCreate(candidate, UriKind.Absolute, out var hostUri))
            {
                return hostUri;
            }
        }

        var escaped = Uri.EscapeDataString(value);
        return new Uri($"{SearchBase}{escaped}");
    }
}
