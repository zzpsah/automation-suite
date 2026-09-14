using System.Collections.Generic;
using System.IO;
using System.Text.Json;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;
using Devos.WorkBrowser.Automation;
using Devos.WorkBrowser.Browser;
using Devos.WorkBrowser.Planning;
using Devos.WorkBrowser.Runtime;
using Devos.WorkBrowser.Tasks;
using Microsoft.Web.WebView2.Core;
using Microsoft.Web.WebView2.Wpf;

namespace Devos.WorkBrowser;

public partial class MainWindow : Window
{
    private static readonly Uri HomeUri = new("https://www.google.com/");
    private readonly Dictionary<TabItem, WebView2> _views = new();
    private readonly NaturalLanguagePlanner _planner = new();
    private readonly string _stateRoot;
    private readonly string _profilePath;
    private readonly CheckpointStore _checkpoints;
    private readonly ActiveTaskStore _activeTasks;
    private readonly SyntheticPortalCheckpointStore _syntheticPortalCheckpoints;
    private readonly bool _enableRecoveryPrompts;
    private readonly TaskCompletionSource<bool> _browserReady = new(TaskCreationOptions.RunContinuationsAsynchronously);
    private CoreWebView2Environment? _environment;
    private bool _commandRunning;

    public MainWindow(string? stateRoot = null, bool enableRecoveryPrompts = true)
    {
        _stateRoot = stateRoot ?? Path.Combine(
            Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
            "DEVOS", "WorkBrowser");
        _profilePath = Path.Combine(_stateRoot, "Profile");
        _checkpoints = new CheckpointStore(Path.Combine(_stateRoot, "Tasks"));
        _activeTasks = new ActiveTaskStore(Path.Combine(_stateRoot, "active-task.json"));
        _syntheticPortalCheckpoints = new SyntheticPortalCheckpointStore(Path.Combine(_stateRoot, "synthetic-portal-checkpoint.json"));
        _enableRecoveryPrompts = enableRecoveryPrompts;

        InitializeComponent();
        Loaded += MainWindow_Loaded;
        Closing += (_, _) => SessionStateStore.Save(CaptureSession());
    }

    private WebView2? ActiveView =>
        BrowserTabs.SelectedItem is TabItem tab && _views.TryGetValue(tab, out var view) ? view : null;

    private async void MainWindow_Loaded(object sender, RoutedEventArgs e)
    {
        try
        {
            Directory.CreateDirectory(_profilePath);
            _environment = await CoreWebView2Environment.CreateAsync(userDataFolder: _profilePath);

            var session = SessionStateStore.Load();
            if (session?.Tabs.Count > 0)
            {
                foreach (var url in session.Tabs)
                {
                    if (Uri.TryCreate(url, UriKind.Absolute, out var uri))
                    {
                        await CreateTabAsync(uri);
                    }
                }

                if (BrowserTabs.Items.Count > 0)
                {
                    BrowserTabs.SelectedIndex = Math.Clamp(session.SelectedIndex, 0, BrowserTabs.Items.Count - 1);
                }
            }
            else
            {
                await CreateTabAsync(HomeUri);
            }

            _browserReady.TrySetResult(true);

            if (_enableRecoveryPrompts)
            {
                await TryResumePendingTaskAsync();
                var portalCheckpoint = _syntheticPortalCheckpoints.Load();
                if (portalCheckpoint is not null)
                {
                    CommandStatus.Text = $"Synthetic portal recovery available at record {portalCheckpoint.NextRecordId}";
                }
            }
        }
        catch (Exception ex)
        {
            _browserReady.TrySetException(ex);
            CommandStatus.Text = $"Startup failed: {ex.Message}";
        }
    }

    private async Task CreateTabAsync(Uri uri)
    {
        _environment ??= await CoreWebView2Environment.CreateAsync(userDataFolder: _profilePath);

        // Important WPF/WebView2 lifecycle ordering:
        // first attach the control to a live visual tree, then wait for Loaded,
        // then initialize CoreWebView2. Some real Windows machines can hang when
        // EnsureCoreWebView2Async runs before the control has an HWND/visual host.
        var view = new WebView2();
        var tab = new TabItem { Header = "Loading…", Content = view };
        _views[tab] = view;
        BrowserTabs.Items.Add(tab);
        BrowserTabs.SelectedItem = tab;

        try
        {
            await WaitForLoadedAsync(view);
            await view.EnsureCoreWebView2Async(_environment);

            view.CoreWebView2.DocumentTitleChanged += (_, _) =>
                tab.Header = string.IsNullOrWhiteSpace(view.CoreWebView2.DocumentTitle)
                    ? "Tab"
                    : view.CoreWebView2.DocumentTitle;
            view.NavigationStarting += (_, args) =>
            {
                if (ReferenceEquals(view, ActiveView)) AddressBox.Text = args.Uri ?? AddressBox.Text;
            };
            view.NavigationCompleted += (_, _) => UpdateNavigationState();
            view.CoreWebView2.DownloadStarting += (_, args) => ConfigureDownload(args);

            tab.Header = "New Tab";
            view.Source = uri;
            UpdateNavigationState();
        }
        catch
        {
            _views.Remove(tab);
            BrowserTabs.Items.Remove(tab);
            view.Dispose();
            throw;
        }
    }

    private static Task WaitForLoadedAsync(FrameworkElement element)
    {
        if (element.IsLoaded) return Task.CompletedTask;

        var completion = new TaskCompletionSource<bool>(TaskCreationOptions.RunContinuationsAsynchronously);
        RoutedEventHandler? handler = null;
        handler = (_, _) =>
        {
            element.Loaded -= handler;
            completion.TrySetResult(true);
        };
        element.Loaded += handler;
        return completion.Task;
    }

    private static void ConfigureDownload(CoreWebView2DownloadStartingEventArgs args)
    {
        var downloads = Path.Combine(
            Environment.GetFolderPath(Environment.SpecialFolder.UserProfile),
            "Downloads", "DEVOS");
        Directory.CreateDirectory(downloads);
        var fileName = Path.GetFileName(args.ResultFilePath);
        if (string.IsNullOrWhiteSpace(fileName))
        {
            fileName = $"download-{DateTimeOffset.UtcNow:yyyyMMddHHmmss}";
        }
        args.ResultFilePath = Path.Combine(downloads, fileName);
    }

    private SessionState CaptureSession()
    {
        var urls = BrowserTabs.Items
            .OfType<TabItem>()
            .Select(tab => _views.TryGetValue(tab, out var view) ? view.Source?.ToString() : null)
            .Where(value => !string.IsNullOrWhiteSpace(value))
            .Cast<string>()
            .ToList();
        return new SessionState(urls, BrowserTabs.SelectedIndex);
    }

    private void NavigateFromAddressBar()
    {
        if (ActiveView is not null) ActiveView.Source = UrlResolver.Resolve(AddressBox.Text);
    }

    private void Go_Click(object sender, RoutedEventArgs e) => NavigateFromAddressBar();

    private void AddressBox_KeyDown(object sender, KeyEventArgs e)
    {
        if (e.Key == Key.Enter)
        {
            NavigateFromAddressBar();
            e.Handled = true;
        }
    }

    private void Back_Click(object sender, RoutedEventArgs e)
    {
        if (ActiveView?.CanGoBack == true) ActiveView.GoBack();
    }

    private void Forward_Click(object sender, RoutedEventArgs e)
    {
        if (ActiveView?.CanGoForward == true) ActiveView.GoForward();
    }

    private void Reload_Click(object sender, RoutedEventArgs e) => ActiveView?.Reload();

    private void Home_Click(object sender, RoutedEventArgs e)
    {
        if (ActiveView is not null) ActiveView.Source = HomeUri;
    }

    private async void NewTab_Click(object sender, RoutedEventArgs e) => await CreateTabAsync(HomeUri);

    private async void CloseTab_Click(object sender, RoutedEventArgs e)
    {
        if (_commandRunning || BrowserTabs.SelectedItem is not TabItem tab) return;
        if (_views.Remove(tab, out var view)) view.Dispose();
        BrowserTabs.Items.Remove(tab);
        if (BrowserTabs.Items.Count == 0) await CreateTabAsync(HomeUri);
        UpdateNavigationState();
    }

    private void BrowserTabs_SelectionChanged(object sender, SelectionChangedEventArgs e) => UpdateNavigationState();

    private async Task NavigateToTestPortalAsync()
    {
        var portalPath = Path.Combine(AppContext.BaseDirectory, "test-portal", "index.html");
        if (!File.Exists(portalPath))
        {
            throw new FileNotFoundException("Synthetic portal fixture is missing.", portalPath);
        }

        var uri = new Uri(portalPath);
        if (ActiveView is null) await CreateTabAsync(uri);
        else ActiveView.Source = uri;
    }

    private async void TestPortal_Click(object sender, RoutedEventArgs e)
    {
        try
        {
            await NavigateToTestPortalAsync();
            CommandStatus.Text = "Synthetic portal loaded";
        }
        catch (Exception ex)
        {
            CommandStatus.Text = ex.Message;
        }
    }

    private async void RunCommand_Click(object sender, RoutedEventArgs e) => await ExecuteCurrentCommandAsync();

    private async void Window_PreviewKeyDown(object sender, KeyEventArgs e)
    {
        if (e.Key == Key.Space && Keyboard.Modifiers.HasFlag(ModifierKeys.Control))
        {
            CommandBox.Focus();
            CommandBox.SelectAll();
            e.Handled = true;
            return;
        }

        if (e.Key == Key.Enter && ReferenceEquals(Keyboard.FocusedElement, CommandBox))
        {
            e.Handled = true;
            await ExecuteCurrentCommandAsync();
        }
    }

    private async Task ExecuteCurrentCommandAsync()
    {
        if (_commandRunning) return;
        var command = CommandBox.Text.Trim();
        if (string.Equals(command, "process synthetic portal", StringComparison.OrdinalIgnoreCase))
        {
            await RunSyntheticPortalAsync();
            return;
        }

        PlannedCommand plan;
        try
        {
            plan = _planner.Plan(command);
        }
        catch (Exception ex)
        {
            CommandStatus.Text = ex.Message;
            return;
        }

        if (plan.RequiresApproval && !RequestApproval(plan.Summary, "DEVOS approval required"))
        {
            CommandStatus.Text = "Approval declined";
            return;
        }

        var task = new ActiveTask(
            Guid.NewGuid().ToString("N"),
            plan.Summary,
            plan.Actions,
            plan.RequiresApproval,
            DateTimeOffset.UtcNow);
        _activeTasks.Save(task);
        await ExecuteTaskAsync(task);
    }

    private async Task RunSyntheticPortalAsync()
    {
        if (_commandRunning) return;
        _commandRunning = true;
        RunCommandButton.IsEnabled = false;
        try
        {
            var adapter = CreateAutomationAdapter();
            if (adapter is null)
            {
                CommandStatus.Text = "Browser not ready";
                return;
            }

            if (!await adapter.WaitForSelectorAsync("#students", TimeSpan.FromSeconds(1)))
            {
                await NavigateToTestPortalAsync();
                if (!await adapter.WaitForSelectorAsync("#students", TimeSpan.FromSeconds(5)))
                {
                    throw new InvalidOperationException("Synthetic portal did not become ready.");
                }
            }

            var outputDirectory = Path.Combine(
                Environment.GetFolderPath(Environment.SpecialFolder.UserProfile),
                "Downloads", "DEVOS", "SyntheticPortalExport");
            var workflow = new SyntheticPortalWorkflow(adapter, _syntheticPortalCheckpoints);
            CommandStatus.Text = "Processing synthetic portal…";
            var result = await workflow.RunAsync(outputDirectory);
            CommandStatus.Text = result.Completed
                ? $"Exported {result.ProcessedCount} records to {outputDirectory}"
                : $"Paused after {result.ProcessedCount} records";
        }
        catch (Exception ex)
        {
            CommandStatus.Text = $"Synthetic portal paused: {ex.Message}";
        }
        finally
        {
            _commandRunning = false;
            RunCommandButton.IsEnabled = true;
        }
    }

    internal async Task<bool> RunAutomatedAcceptanceAsync(CancellationToken cancellationToken = default)
    {
        await _browserReady.Task.WaitAsync(TimeSpan.FromSeconds(30), cancellationToken);
        await NavigateToTestPortalAsync();

        var adapter = CreateAutomationAdapter()
            ?? throw new InvalidOperationException("Self-test browser adapter is unavailable.");
        if (!await adapter.WaitForSelectorAsync("#students", TimeSpan.FromSeconds(15)))
        {
            throw new TimeoutException("Self-test portal did not become ready.");
        }

        var initialStatus = await adapter.ReadTextAsync("#status");
        if (!string.Equals(initialStatus, "ready", StringComparison.OrdinalIgnoreCase))
        {
            throw new InvalidOperationException($"Unexpected initial portal status: {initialStatus}");
        }

        await adapter.ClickAsync("#next");
        var pageDeadline = DateTimeOffset.UtcNow + TimeSpan.FromSeconds(5);
        while (DateTimeOffset.UtcNow < pageDeadline)
        {
            var page = await adapter.ReadTextAsync("#page");
            if (page?.Contains("Page 2 of 10", StringComparison.OrdinalIgnoreCase) == true) break;
            await Task.Delay(75, cancellationToken);
        }

        if ((await adapter.ReadTextAsync("#page"))?.Contains("Page 2 of 10", StringComparison.OrdinalIgnoreCase) != true)
        {
            throw new InvalidOperationException("Real adapter click/read verification failed.");
        }

        _syntheticPortalCheckpoints.Clear();
        var outputDirectory = Path.Combine(_stateRoot, "SelfTestExport");
        if (Directory.Exists(outputDirectory)) Directory.Delete(outputDirectory, recursive: true);

        var firstRun = new SyntheticPortalWorkflow(adapter, _syntheticPortalCheckpoints);
        var interrupted = await firstRun.RunAsync(outputDirectory, stopAfterRecord: 47, cancellationToken);
        if (interrupted.Completed || interrupted.ProcessedCount != 47)
        {
            throw new InvalidOperationException(
                $"Expected self-test interruption at record 47; got {interrupted.ProcessedCount}.");
        }

        var checkpoint = _syntheticPortalCheckpoints.Load();
        if (checkpoint?.NextRecordId != 48 || checkpoint.Records.Count != 47)
        {
            throw new InvalidOperationException("Self-test checkpoint did not preserve the 47→48 recovery boundary.");
        }

        var resumedRun = new SyntheticPortalWorkflow(adapter, _syntheticPortalCheckpoints);
        var completed = await resumedRun.RunAsync(outputDirectory, cancellationToken: cancellationToken);
        if (!completed.Completed || completed.ProcessedCount != SyntheticPortalWorkflow.RecordCount)
        {
            throw new InvalidOperationException(
                $"Self-test recovery completed {completed.ProcessedCount} records instead of 100.");
        }

        if (completed.JsonPath is null || completed.CsvPath is null ||
            !File.Exists(completed.JsonPath) || !File.Exists(completed.CsvPath))
        {
            throw new InvalidOperationException("Self-test JSON/CSV export files are missing.");
        }

        var records = JsonSerializer.Deserialize<List<SyntheticStudentRecord>>(
            await File.ReadAllTextAsync(completed.JsonPath, cancellationToken));
        if (records?.Count != 100 || records[0].Id != 1 || records[^1].Id != 100)
        {
            throw new InvalidOperationException("Self-test JSON export does not contain records 1 through 100.");
        }

        var csvLines = await File.ReadAllLinesAsync(completed.CsvPath, cancellationToken);
        if (csvLines.Length != 101 ||
            !csvLines[1].StartsWith("1,", StringComparison.Ordinal) ||
            !csvLines[^1].StartsWith("100,", StringComparison.Ordinal))
        {
            throw new InvalidOperationException("Self-test CSV export does not contain the expected 100 records.");
        }

        CommandStatus.Text = "Automated acceptance PASS — 100/100 records";
        return true;
    }

    private async Task TryResumePendingTaskAsync()
    {
        var task = _activeTasks.Load();
        if (task is null) return;

        var message = task.RequiresApproval
            ? $"A committing DEVOS task was interrupted:\n\n{task.Summary}\n\nResume it? A fresh approval is required."
            : $"A DEVOS task was interrupted:\n\n{task.Summary}\n\nResume from the last checkpoint?";

        var resume = MessageBox.Show(
            message,
            "DEVOS recovery",
            MessageBoxButton.YesNo,
            task.RequiresApproval ? MessageBoxImage.Warning : MessageBoxImage.Question,
            MessageBoxResult.No);

        if (resume != MessageBoxResult.Yes)
        {
            CancelTask(task.TaskId);
            CommandStatus.Text = "Interrupted task cancelled";
            return;
        }

        await ExecuteTaskAsync(task);
    }

    private async Task ExecuteTaskAsync(ActiveTask task)
    {
        if (_commandRunning) return;
        var adapter = CreateAutomationAdapter();
        if (adapter is null)
        {
            CommandStatus.Text = "Browser not ready; task preserved for recovery";
            return;
        }

        _commandRunning = true;
        RunCommandButton.IsEnabled = false;
        CommandStatus.Text = task.Summary;
        try
        {
            var runner = new TaskRunner(new ActionExecutor(adapter), _checkpoints);
            var results = await runner.RunAsync(task.TaskId, task.Actions);
            var checkpoint = _checkpoints.Load(task.TaskId);
            var completed = checkpoint?.NextStepIndex >= task.Actions.Count;

            if (completed)
            {
                var last = results.LastOrDefault();
                _activeTasks.Clear();
                _checkpoints.Delete(task.TaskId);
                CommandStatus.Text = !string.IsNullOrWhiteSpace(last?.Output)
                    ? last.Output
                    : $"Done: {task.Actions.Count} step{(task.Actions.Count == 1 ? string.Empty : "s")}";
                return;
            }

            var failure = results.LastOrDefault(result => !result.Success);
            CommandStatus.Text = failure is null
                ? "Task paused; checkpoint preserved"
                : $"Paused: {failure.Error}. Checkpoint preserved.";
        }
        finally
        {
            _commandRunning = false;
            RunCommandButton.IsEnabled = true;
        }
    }

    private static bool RequestApproval(string summary, string title) =>
        MessageBox.Show(
            $"DEVOS wants to perform a committing action:\n\n{summary}\n\nApprove this action?",
            title,
            MessageBoxButton.YesNo,
            MessageBoxImage.Warning,
            MessageBoxResult.No) == MessageBoxResult.Yes;

    private void CancelTask(string taskId)
    {
        _activeTasks.Clear();
        _checkpoints.Delete(taskId);
    }

    private void UpdateNavigationState()
    {
        var view = ActiveView;
        BackButton.IsEnabled = view?.CanGoBack == true;
        ForwardButton.IsEnabled = view?.CanGoForward == true;
        if (view?.Source is not null) AddressBox.Text = view.Source.ToString();
    }

    internal BrowserAutomationAdapter? CreateAutomationAdapter() =>
        ActiveView?.CoreWebView2 is { } core ? new BrowserAutomationAdapter(core) : null;
}
