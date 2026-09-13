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
        var directory = Path.Combine(Path.GetTempPath(), "devos-work-browser-tests", Guid.NewGuid().ToString("N"));
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
