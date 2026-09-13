using System.IO;
using System.Text.Json;

namespace Devos.WorkBrowser.Browser;

public sealed record SessionState(IReadOnlyList<string> Tabs, int SelectedIndex);

public static class SessionStateStore
{
    private static readonly string StatePath = Path.Combine(
        Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
        "DEVOS", "WorkBrowser", "session.json");

    public static void Save(SessionState state)
    {
        Directory.CreateDirectory(Path.GetDirectoryName(StatePath)!);
        File.WriteAllText(StatePath, JsonSerializer.Serialize(state, new JsonSerializerOptions { WriteIndented = true }));
    }

    public static SessionState? Load()
    {
        if (!File.Exists(StatePath)) return null;
        try
        {
            return JsonSerializer.Deserialize<SessionState>(File.ReadAllText(StatePath));
        }
        catch
        {
            return null;
        }
    }
}
