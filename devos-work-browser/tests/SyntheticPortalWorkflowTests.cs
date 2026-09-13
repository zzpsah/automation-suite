using Devos.WorkBrowser.Runtime;
using Devos.WorkBrowser.Tasks;
using Xunit;

namespace Devos.WorkBrowser.Tests;

public sealed class SyntheticPortalWorkflowTests
{
    [Fact]
    public async Task Workflow_StopsAt47AndResumesAt48WithoutReprocessing()
    {
        var root = Path.Combine(Path.GetTempPath(), "devos-work-browser-tests", Guid.NewGuid().ToString("N"));
        var checkpointPath = Path.Combine(root, "synthetic-checkpoint.json");
        var outputPath = Path.Combine(root, "export");
        var store = new SyntheticPortalCheckpointStore(checkpointPath);

        var firstAdapter = new SyntheticPortalAdapter();
        var firstRun = await new SyntheticPortalWorkflow(firstAdapter, store)
            .RunAsync(outputPath, stopAfterRecord: 47);

        Assert.False(firstRun.Completed);
        Assert.Equal(47, firstRun.ProcessedCount);
        Assert.Equal(Enumerable.Range(1, 47), firstAdapter.OpenedRecords);
        Assert.Equal(48, store.Load()!.NextRecordId);

        var secondAdapter = new SyntheticPortalAdapter();
        var secondRun = await new SyntheticPortalWorkflow(secondAdapter, store)
            .RunAsync(outputPath);

        Assert.True(secondRun.Completed);
        Assert.Equal(100, secondRun.ProcessedCount);
        Assert.Equal(Enumerable.Range(48, 53), secondAdapter.OpenedRecords);
        Assert.False(File.Exists(checkpointPath));
        Assert.NotNull(secondRun.JsonPath);
        Assert.NotNull(secondRun.CsvPath);
        Assert.True(File.Exists(secondRun.JsonPath!));
        Assert.True(File.Exists(secondRun.CsvPath!));
        Assert.Contains("Student 001", await File.ReadAllTextAsync(secondRun.JsonPath!));
        Assert.Contains("Student 100", await File.ReadAllTextAsync(secondRun.CsvPath!));
    }

    private sealed class SyntheticPortalAdapter : IAutomationAdapter
    {
        private int _page = 1;
        private int? _openedId;
        public List<int> OpenedRecords { get; } = new();

        public Task ClickAsync(string target)
        {
            if (target == "#next")
            {
                _page = Math.Min(10, _page + 1);
                return Task.CompletedTask;
            }

            if (target == "#prev")
            {
                _page = Math.Max(1, _page - 1);
                return Task.CompletedTask;
            }

            const string prefix = "button.open[data-id=\"";
            if (target.StartsWith(prefix, StringComparison.Ordinal) && target.EndsWith("\"]", StringComparison.Ordinal))
            {
                var idText = target[prefix.Length..^2];
                var id = int.Parse(idText);
                var expectedPage = ((id - 1) / SyntheticPortalWorkflow.PageSize) + 1;
                if (expectedPage != _page) throw new InvalidOperationException($"Record {id} is not on page {_page}.");
                _openedId = id;
                OpenedRecords.Add(id);
                return Task.CompletedTask;
            }

            throw new InvalidOperationException($"Unknown click target: {target}");
        }

        public Task TypeAsync(string target, string value) => Task.CompletedTask;

        public Task<string?> ReadTextAsync(string target)
        {
            if (target == "#page") return Task.FromResult<string?>($"Page {_page} of 10");
            if (target == "#status") return Task.FromResult<string?>(_openedId is null ? "ready" : $"opened-{_openedId}");
            if (target == "#detail")
            {
                if (_openedId is null) return Task.FromResult<string?>("Select a record.");
                var status = _openedId.Value % 9 == 0 ? "Needs Review" : "Ready";
                return Task.FromResult<string?>($"{_openedId} | Student {_openedId.Value:000} | {status}");
            }

            return Task.FromResult<string?>(null);
        }

        public Task<bool> WaitForSelectorAsync(string target, TimeSpan timeout, TimeSpan? pollInterval = null)
        {
            if (target is "#students" or "#page" or "#status" or "#detail") return Task.FromResult(true);
            const string prefix = "button.open[data-id=\"";
            if (target.StartsWith(prefix, StringComparison.Ordinal) && target.EndsWith("\"]", StringComparison.Ordinal))
            {
                var id = int.Parse(target[prefix.Length..^2]);
                return Task.FromResult((((id - 1) / SyntheticPortalWorkflow.PageSize) + 1) == _page);
            }
            return Task.FromResult(false);
        }
    }
}
