using System.Collections.Generic;
using System.IO;
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
    private readonly string _stateRoot = Path.Combine(
        Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
        "DEVOS", "WorkBrowser");
    private readonly string _profilePath;
    private readonly CheckpointStore _checkpoints;
    private readonly ActiveTaskStore _activeTasks;
    private CoreWebView2Environment? _environment;
    private bool _commandRunning;

    public MainWindow()
    {
        _profilePath = Path.Combine(_stateRoot, "Profile");
        _checkpoints = new CheckpointStore(Path.Combine(_stateRoot, "Tasks"));
        _activeTasks = new ActiveTaskStore(Path.Combine(_stateRoot, "active-task.json"));

        InitializeComponent();
        Loaded += MainWindow_Loaded;
        Closing += (_, _) => SessionStateStore.Save(CaptureSession());
    }

    private WebView2? ActiveView => BrowserTabs.SelectedItem is TabItem tab && _views.TryGetValue(tab, out var view) ? view : null;

    private async void MainWindow_Loaded(object sender, RoutedEventArgs e)
    {
        Directory.CreateDirectory(_profilePath);
        _environment = await CoreWebView2Environment.CreateAsync(userDataFolder: _profilePath);

        var session = SessionStateStore.Load();
        if (session?.Tabs.Count > 0)
        {
            foreach (var url in session.Tabs)
            {
                if (Uri.TryCreate(url, UriKind.Absolute, out var uri)) await CreateTabAsync(uri);
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

        await TryResumePendingTaskAsync();
    }

    private async Task CreateTabAsync(Uri uri)
    {
        _environment ??= await CoreWebView2Environment.CreateAsync(userDataFolder: _profilePath);
        var view = new WebView2();
        await view.EnsureCoreWebView2Async(_environment);

        var tab = new TabItem { Header = "New Tab", Content = view };
        _views[tab] = view;
        BrowserTabs.Items.Add(tab);
        BrowserTabs.SelectedItem = tab;

        view.CoreWebView2.DocumentTitleChanged += (_, _) => tab.Header = string.IsNullOrWhiteSpace(view.CoreWebView2.DocumentTitle) ? "Tab" : view.CoreWebView2.DocumentTitle;
        view.NavigationStarting += (_, args) =>
        {
            if (ReferenceEquals(view, ActiveView)) AddressBox.Text = args.Uri ?? AddressBox.Text;
        };
        view.NavigationCompleted += (_, _) => UpdateNavigationState();
        view.CoreWebView2.DownloadStarting += (_, args) => ConfigureDownload(args);
        view.Source = uri;
        UpdateNavigationState();
    }

    private static void ConfigureDownload(CoreWebView2DownloadStartingEventArgs args)
    {
        var downloads = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.UserProfile), "Downloads", "DEVOS");
        Directory.CreateDirectory(downloads);
        var fileName = Path.GetFileName(args.ResultFilePath);
        if (string.IsNullOrWhiteSpace(fileName)) fileName = $"download-{DateTimeOffset.UtcNow:yyyyMMddHHmmss}";
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
    private void Home_Click(object sender, RoutedEventArgs e) { if (ActiveView is not null) ActiveView.Source = HomeUri; }
    private async void NewTab_Click(object sender, RoutedEventArgs e) => await CreateTabAsync(HomeUri);
    private void BrowserTabs_SelectionChanged(object sender, SelectionChangedEventArgs e) => UpdateNavigationState();

    private async void TestPortal_Click(object sender, RoutedEventArgs e)
    {
        var portalPath = Path.Combine(AppContext.BaseDirectory, "test-portal", "index.html");
        if (!File.Exists(portalPath))
        {
            CommandStatus.Text = "Synthetic portal fixture is missing";
            return;
        }

        var uri = new Uri(portalPath);
        if (ActiveView is null) await CreateTabAsync(uri);
        else ActiveView.Source = uri;
        CommandStatus.Text = "Synthetic portal loaded";
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

        PlannedCommand plan;
        try
        {
            plan = _planner.Plan(CommandBox.Text);
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

    private static bool RequestApproval(string summary, string title)
        => MessageBox.Show(
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

    internal BrowserAutomationAdapter? CreateAutomationAdapter() => ActiveView?.CoreWebView2 is { } core ? new BrowserAutomationAdapter(core) : null;
}
