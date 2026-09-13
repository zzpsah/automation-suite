using System.Collections.Generic;
using System.IO;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;
using Devos.WorkBrowser.Automation;
using Devos.WorkBrowser.Browser;
using Devos.WorkBrowser.Planning;
using Devos.WorkBrowser.Runtime;
using Microsoft.Web.WebView2.Core;
using Microsoft.Web.WebView2.Wpf;

namespace Devos.WorkBrowser;

public partial class MainWindow : Window
{
    private static readonly Uri HomeUri = new("https://www.google.com/");
    private readonly Dictionary<TabItem, WebView2> _views = new();
    private readonly NaturalLanguagePlanner _planner = new();
    private readonly string _profilePath = Path.Combine(
        Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
        "DEVOS", "WorkBrowser", "Profile");
    private CoreWebView2Environment? _environment;
    private bool _commandRunning;

    public MainWindow()
    {
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
        var adapter = CreateAutomationAdapter();
        if (adapter is null)
        {
            CommandStatus.Text = "Browser not ready";
            return;
        }

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

        if (plan.RequiresApproval)
        {
            var approval = MessageBox.Show(
                $"DEVOS wants to perform a committing action:\n\n{plan.Summary}\n\nApprove this action?",
                "DEVOS approval required",
                MessageBoxButton.YesNo,
                MessageBoxImage.Warning,
                MessageBoxResult.No);
            if (approval != MessageBoxResult.Yes)
            {
                CommandStatus.Text = "Approval declined";
                return;
            }
        }

        _commandRunning = true;
        RunCommandButton.IsEnabled = false;
        CommandStatus.Text = plan.Summary;
        try
        {
            var executor = new ActionExecutor(adapter);
            foreach (var action in plan.Actions)
            {
                var result = await executor.ExecuteAsync(action);
                if (!result.Success)
                {
                    CommandStatus.Text = $"Failed: {result.Error}";
                    return;
                }

                CommandStatus.Text = string.IsNullOrWhiteSpace(result.Output)
                    ? $"Done ({result.Attempts} attempt{(result.Attempts == 1 ? string.Empty : "s")})"
                    : result.Output;
            }
        }
        finally
        {
            _commandRunning = false;
            RunCommandButton.IsEnabled = true;
        }
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
