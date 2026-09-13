using Devos.WorkBrowser.Runtime;

namespace Devos.WorkBrowser.Tasks;

public sealed class TaskRunner
{
    private readonly ActionExecutor _executor;
    private readonly CheckpointStore _checkpoints;

    public TaskRunner(ActionExecutor executor, CheckpointStore checkpoints)
    {
        _executor = executor;
        _checkpoints = checkpoints;
    }

    public async Task<IReadOnlyList<ActionResult>> RunAsync(
        string taskId,
        IReadOnlyList<BrowserAction> steps,
        CancellationToken cancellationToken = default)
    {
        var checkpoint = _checkpoints.Load(taskId);
        var startIndex = checkpoint?.NextStepIndex ?? 0;
        var results = new List<ActionResult>();

        for (var index = startIndex; index < steps.Count; index++)
        {
            cancellationToken.ThrowIfCancellationRequested();
            var result = await _executor.ExecuteAsync(steps[index], cancellationToken);
            results.Add(result);
            if (!result.Success) break;
            _checkpoints.Save(new TaskCheckpoint(taskId, index + 1, DateTimeOffset.UtcNow));
        }

        return results;
    }
}
