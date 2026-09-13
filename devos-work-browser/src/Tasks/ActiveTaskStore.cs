using System.IO;
using System.Text.Json;
using Devos.WorkBrowser.Runtime;

namespace Devos.WorkBrowser.Tasks;

public sealed record ActiveTask(
    string TaskId,
    string Summary,
    IReadOnlyList<BrowserAction> Actions,
    bool RequiresApproval,
    DateTimeOffset CreatedAtUtc);

public sealed class ActiveTaskStore
{
    private readonly string _path;

    public ActiveTaskStore(string path) => _path = path;

    public void Save(ActiveTask task)
    {
        var directory = Path.GetDirectoryName(_path);
        if (!string.IsNullOrWhiteSpace(directory)) Directory.CreateDirectory(directory);
        File.WriteAllText(_path, JsonSerializer.Serialize(task, new JsonSerializerOptions { WriteIndented = true }));
    }

    public ActiveTask? Load()
    {
        if (!File.Exists(_path)) return null;
        try
        {
            return JsonSerializer.Deserialize<ActiveTask>(File.ReadAllText(_path));
        }
        catch
        {
            return null;
        }
    }

    public void Clear()
    {
        if (File.Exists(_path)) File.Delete(_path);
    }
}
