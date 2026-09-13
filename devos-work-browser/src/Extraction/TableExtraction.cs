using System.Text.Json;

namespace Devos.WorkBrowser.Extraction;

public static class TableExtraction
{
    public static IReadOnlyList<IReadOnlyList<string>> Parse(string? json)
    {
        if (string.IsNullOrWhiteSpace(json)) return Array.Empty<IReadOnlyList<string>>();
        var rows = JsonSerializer.Deserialize<List<List<string>>>(json);
        return rows?.Select(row => (IReadOnlyList<string>)row).ToList()
            ?? Array.Empty<IReadOnlyList<string>>();
    }

    public static string ToCsv(IReadOnlyList<IReadOnlyList<string>> rows)
        => string.Join(Environment.NewLine, rows.Select(row => string.Join(",", row.Select(Escape))));

    private static string Escape(string value)
    {
        if (!value.ContainsAny(',', '"', '\n', '\r')) return value;
        return $"\"{value.Replace("\"", "\"\"")}\"";
    }

    private static bool ContainsAny(this string value, params char[] chars) => value.IndexOfAny(chars) >= 0;
}
