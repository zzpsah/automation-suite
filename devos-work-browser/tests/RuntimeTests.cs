using Devos.WorkBrowser.Runtime;
using Devos.WorkBrowser.Tasks;
using Xunit;

namespace Devos.WorkBrowser.Tests;

public sealed class RuntimeTests
{
    [Fact]
    public async Task Executor_RetriesUntilVerificationPasses()
    {
        var adapter = new FakeAdapter { Reads = new Queue<string?>(new[] { "loading", "done" }) };
        var executor = new ActionExecutor(adapter);
        var result = await executor.ExecuteAsync(new BrowserAction(BrowserActionKind.ReadText, "#status", ExpectedText: "done", MaxAttempts: 2));
        Assert.True(result.Success);
        Assert.Equal(2, result.Attempts);
    }

    [Fact]
    public async Task TaskRunner_ResumesFromCheckpoint()
    {
        var directory = NewTempDirectory();
        var store = new CheckpointStore(directory);
        store.Save(new TaskCheckpoint("t1", 1, DateTimeOffset.UtcNow));
        var adapter = new FakeAdapter();
        var runner = new TaskRunner(new ActionExecutor(adapter), store);
        var steps = new[]
        {
            new BrowserAction(BrowserActionKind.Click, "#first"),
            new BrowserAction(BrowserActionKind.Click, "#second")
        };

        var results = await runner.RunAsync("t1", steps);

        Assert.Single(results);
        Assert.Equal("#second", adapter.Clicked.Single());
        Assert.Equal(2, store.Load("t1")!.NextStepIndex);
    }

    [Fact]
    public async Task TaskRunner_ResumesHundredRecordRunFromRecord47()
    {
        var directory = NewTempDirectory();
        var store = new CheckpointStore(directory);
        store.Save(new TaskCheckpoint("hundred", 47, DateTimeOffset.UtcNow));
        var adapter = new FakeAdapter();
        var runner = new TaskRunner(new ActionExecutor(adapter), store);
        var steps = Enumerable.Range(1, 100)
            .Select(index => new BrowserAction(BrowserActionKind.Click, $"#record-{index}"))
            .ToList();

        var results = await runner.RunAsync("hundred", steps);

        Assert.Equal(53, results.Count);
        Assert.Equal("#record-48", adapter.Clicked.First());
        Assert.Equal("#record-100", adapter.Clicked.Last());
        Assert.Equal(100, store.Load("hundred")!.NextStepIndex);
    }

    [Fact]
    public void ActiveTaskStore_PersistsAndClearsRecoverableTask()
    {
        var directory = NewTempDirectory();
        var path = Path.Combine(directory, "active-task.json");
        var store = new ActiveTaskStore(path);
        var task = new ActiveTask(
            "recover-me",
            "Click then read",
            new BrowserAction[]
            {
                new(BrowserActionKind.Click, "#next"),
                new(BrowserActionKind.ReadText, "#status")
            },
            false,
            DateTimeOffset.UtcNow);

        store.Save(task);
        var loaded = store.Load();

        Assert.NotNull(loaded);
        Assert.Equal(task.TaskId, loaded!.TaskId);
        Assert.Equal(2, loaded.Actions.Count);
        store.Clear();
        Assert.Null(store.Load());
    }

    [Fact]
    public void CheckpointStore_DeleteRemovesCompletedCheckpoint()
    {
        var directory = NewTempDirectory();
        var store = new CheckpointStore(directory);
        store.Save(new TaskCheckpoint("done", 3, DateTimeOffset.UtcNow));
        Assert.NotNull(store.Load("done"));

        store.Delete("done");

        Assert.Null(store.Load("done"));
    }

    private static string NewTempDirectory()
        => Path.Combine(Path.GetTempPath(), "devos-work-browser-tests", Guid.NewGuid().ToString("N"));

    private sealed class FakeAdapter : IAutomationAdapter
    {
        public Queue<string?> Reads { get; init; } = new();
        public List<string> Clicked { get; } = new();
        public Task ClickAsync(string target) { Clicked.Add(target); return Task.CompletedTask; }
        public Task TypeAsync(string target, string value) => Task.CompletedTask;
        public Task<string?> ReadTextAsync(string target) => Task.FromResult(Reads.Count > 0 ? Reads.Dequeue() : "done");
        public Task<bool> WaitForSelectorAsync(string target, TimeSpan timeout, TimeSpan? pollInterval = null) => Task.FromResult(true);
    }
}
