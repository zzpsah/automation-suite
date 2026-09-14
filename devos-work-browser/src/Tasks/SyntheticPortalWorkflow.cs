using System.Globalization;
using System.IO;
using System.Text;
using System.Text.Json;
using Devos.WorkBrowser.Runtime;

namespace Devos.WorkBrowser.Tasks;

public sealed record SyntheticStudentRecord(int Id, string Name, string Status);
public sealed record SyntheticPortalCheckpoint(int NextRecordId, IReadOnlyList<SyntheticStudentRecord> Records, DateTimeOffset UpdatedAtUtc);
public sealed record SyntheticPortalRunResult(bool Completed, int ProcessedCount, string? JsonPath, string? CsvPath);

public sealed class SyntheticPortalCheckpointStore
{
    private readonly string _path;

    public SyntheticPortalCheckpointStore(string path) => _path = path;

    public void Save(SyntheticPortalCheckpoint checkpoint)
    {
        var directory = Path.GetDirectoryName(_path);
        if (!string.IsNullOrWhiteSpace(directory)) Directory.CreateDirectory(directory);
        File.WriteAllText(_path, JsonSerializer.Serialize(checkpoint, new JsonSerializerOptions { WriteIndented = true }));
    }

    public SyntheticPortalCheckpoint? Load()
    {
        if (!File.Exists(_path)) return null;
        try
        {
            return JsonSerializer.Deserialize<SyntheticPortalCheckpoint>(File.ReadAllText(_path));
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

public sealed class SyntheticPortalWorkflow
{
    public const int RecordCount = 100;
    public const int PageSize = 10;

    private readonly IAutomationAdapter _adapter;
    private readonly SyntheticPortalCheckpointStore _store;

    public SyntheticPortalWorkflow(IAutomationAdapter adapter, SyntheticPortalCheckpointStore store)
    {
        _adapter = adapter;
        _store = store;
    }

    public async Task<SyntheticPortalRunResult> RunAsync(
        string outputDirectory,
        int? stopAfterRecord = null,
        CancellationToken cancellationToken = default)
    {
        var checkpoint = _store.Load();
        var nextRecordId = Math.Clamp(checkpoint?.NextRecordId ?? 1, 1, RecordCount + 1);
        var records = checkpoint?.Records?.ToList() ?? new List<SyntheticStudentRecord>();

        await ReturnToFirstPageAsync(cancellationToken);
        var targetPage = nextRecordId > RecordCount ? 10 : ((nextRecordId - 1) / PageSize) + 1;
        await NavigateToPageAsync(targetPage, cancellationToken);

        for (var id = nextRecordId; id <= RecordCount; id++)
        {
            cancellationToken.ThrowIfCancellationRequested();
            var expectedPage = ((id - 1) / PageSize) + 1;
            var actualPage = await ReadCurrentPageAsync();
            if (actualPage != expectedPage)
            {
                await NavigateToPageAsync(expectedPage, cancellationToken);
            }

            var selector = $"button.open[data-id=\"{id}\"]";
            if (!await _adapter.WaitForSelectorAsync(selector, TimeSpan.FromSeconds(5)))
            {
                throw new InvalidOperationException($"Synthetic portal record button not found: {id}");
            }

            await _adapter.ClickAsync(selector);
            await WaitForTextAsync("#status", $"opened-{id}", cancellationToken);
            var detail = await _adapter.ReadTextAsync("#detail")
                ?? throw new InvalidOperationException($"Synthetic portal detail missing for record {id}");
            var record = ParseDetail(detail, id);

            records.RemoveAll(existing => existing.Id == record.Id);
            records.Add(record);
            records.Sort((left, right) => left.Id.CompareTo(right.Id));
            _store.Save(new SyntheticPortalCheckpoint(id + 1, records.ToList(), DateTimeOffset.UtcNow));

            if (stopAfterRecord == id)
            {
                return new SyntheticPortalRunResult(false, records.Count, null, null);
            }
        }

        if (records.Count != RecordCount)
        {
            throw new InvalidOperationException($"Expected {RecordCount} records but checkpoint contains {records.Count}.");
        }

        Directory.CreateDirectory(outputDirectory);
        var jsonPath = Path.Combine(outputDirectory, "students.json");
        var csvPath = Path.Combine(outputDirectory, "students.csv");
        File.WriteAllText(jsonPath, JsonSerializer.Serialize(records, new JsonSerializerOptions { WriteIndented = true }));
        File.WriteAllText(csvPath, ToCsv(records));
        _store.Clear();
        return new SyntheticPortalRunResult(true, records.Count, jsonPath, csvPath);
    }

    private async Task ReturnToFirstPageAsync(CancellationToken cancellationToken)
    {
        for (var attempt = 0; attempt < 12; attempt++)
        {
            cancellationToken.ThrowIfCancellationRequested();
            var page = await ReadCurrentPageAsync();
            if (page <= 1) return;
            var before = await _adapter.ReadTextAsync("#page");
            await _adapter.ClickAsync("#prev");
            await WaitForTextChangeAsync("#page", before, cancellationToken);
        }

        throw new InvalidOperationException("Could not return synthetic portal to page 1.");
    }

    private async Task NavigateToPageAsync(int targetPage, CancellationToken cancellationToken)
    {
        if (targetPage is < 1 or > 10) throw new ArgumentOutOfRangeException(nameof(targetPage));

        for (var attempt = 0; attempt < 12; attempt++)
        {
            cancellationToken.ThrowIfCancellationRequested();
            var page = await ReadCurrentPageAsync();
            if (page == targetPage) return;

            var before = await _adapter.ReadTextAsync("#page");
            await _adapter.ClickAsync(page < targetPage ? "#next" : "#prev");
            await WaitForTextChangeAsync("#page", before, cancellationToken);
        }

        throw new InvalidOperationException($"Could not navigate synthetic portal to page {targetPage}.");
    }

    private async Task<int> ReadCurrentPageAsync()
    {
        var text = await _adapter.ReadTextAsync("#page") ?? string.Empty;
        var parts = text.Split(' ', StringSplitOptions.RemoveEmptyEntries);
        return parts.Length >= 2 && int.TryParse(parts[1], NumberStyles.Integer, CultureInfo.InvariantCulture, out var page)
            ? page
            : 1;
    }

    private async Task WaitForTextAsync(string selector, string expected, CancellationToken cancellationToken)
    {
        var deadline = DateTimeOffset.UtcNow + TimeSpan.FromSeconds(5);
        while (DateTimeOffset.UtcNow < deadline)
        {
            cancellationToken.ThrowIfCancellationRequested();
            var text = await _adapter.ReadTextAsync(selector);
            if (string.Equals(text, expected, StringComparison.OrdinalIgnoreCase)) return;
            await Task.Delay(75, cancellationToken);
        }

        throw new TimeoutException($"Timed out waiting for {selector} to equal {expected}.");
    }

    private async Task WaitForTextChangeAsync(string selector, string? before, CancellationToken cancellationToken)
    {
        var deadline = DateTimeOffset.UtcNow + TimeSpan.FromSeconds(3);
        while (DateTimeOffset.UtcNow < deadline)
        {
            cancellationToken.ThrowIfCancellationRequested();
            var current = await _adapter.ReadTextAsync(selector);
            if (!string.Equals(current, before, StringComparison.Ordinal)) return;
            await Task.Delay(50, cancellationToken);
        }

        throw new TimeoutException($"Timed out waiting for {selector} to change.");
    }

    private static SyntheticStudentRecord ParseDetail(string detail, int expectedId)
    {
        var parts = detail.Split('|', StringSplitOptions.TrimEntries);
        if (parts.Length != 3 || !int.TryParse(parts[0], NumberStyles.Integer, CultureInfo.InvariantCulture, out var id) || id != expectedId)
        {
            throw new InvalidOperationException($"Unexpected synthetic portal detail: {detail}");
        }

        return new SyntheticStudentRecord(id, parts[1], parts[2]);
    }

    private static string ToCsv(IEnumerable<SyntheticStudentRecord> records)
    {
        var builder = new StringBuilder("Id,Name,Status");
        foreach (var record in records)
        {
            builder.AppendLine();
            builder.Append(record.Id.ToString(CultureInfo.InvariantCulture));
            builder.Append(',').Append(EscapeCsv(record.Name));
            builder.Append(',').Append(EscapeCsv(record.Status));
        }
        return builder.ToString();
    }

    private static string EscapeCsv(string value)
    {
        if (value.IndexOfAny(new[] { ',', '"', '\r', '\n' }) < 0) return value;
        return $"\"{value.Replace("\"", "\"\"")}\"";
    }
}
