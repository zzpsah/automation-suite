using System.IO;
using System.Text.Json;

namespace Devos.WorkBrowser.Tasks;

public sealed record TaskCheckpoint(string TaskId, int NextStepIndex, DateTimeOffset UpdatedAtUtc);

public sealed class CheckpointStore
{
    private readonly string _directory;

    public CheckpointStore(string directory) => _directory = directory;

    public void Save(TaskCheckpoint checkpoint)
    {
        Directory.CreateDirectory(_directory);
        var path = Path.Combine(_directory, $"{checkpoint.TaskId}.json");
        File.WriteAllText(path, JsonSerializer.Serialize(checkpoint, new JsonSerializerOptions { WriteIndented = true }));
    }

    public TaskCheckpoint? Load(string taskId)
    {
        var path = Path.Combine(_directory, $"{taskId}.json");
        if (!File.Exists(path)) return null;
        return JsonSerializer.Deserialize<TaskCheckpoint>(File.ReadAllText(path));
    }
}
