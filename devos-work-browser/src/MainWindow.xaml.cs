using System.Windows;
using System.Windows.Input;
using Devos.WorkBrowser.Browser;

namespace Devos.WorkBrowser;

public partial class MainWindow : Window
{
    private static readonly Uri HomeUri = new("https://www.google.com/");

    public MainWindow()
    {
        InitializeComponent();
        Loaded += MainWindow_Loaded;
        BrowserView.NavigationStarting += (_, args) => AddressBox.Text = args.Uri ?? AddressBox.Text;
        BrowserView.NavigationCompleted += (_, _) => UpdateNavigationState();
    }

    private async void MainWindow_Loaded(object sender, RoutedEventArgs e)
    {
        await BrowserView.EnsureCoreWebView2Async();
        AddressBox.Text = BrowserView.Source?.ToString() ?? HomeUri.ToString();
        UpdateNavigationState();
        AddressBox.Focus();
    }

    private void NavigateFromAddressBar()
    {
        BrowserView.Source = UrlResolver.Resolve(AddressBox.Text);
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
        if (BrowserView.CanGoBack)
        {
            BrowserView.GoBack();
        }
    }

    private void Forward_Click(object sender, RoutedEventArgs e)
    {
        if (BrowserView.CanGoForward)
        {
            BrowserView.GoForward();
        }
    }

    private void Reload_Click(object sender, RoutedEventArgs e) => BrowserView.Reload();

    private void Home_Click(object sender, RoutedEventArgs e) => BrowserView.Source = HomeUri;

    private void UpdateNavigationState()
    {
        BackButton.IsEnabled = BrowserView.CanGoBack;
        ForwardButton.IsEnabled = BrowserView.CanGoForward;
        if (BrowserView.Source is not null)
        {
            AddressBox.Text = BrowserView.Source.ToString();
        }
    }
}
