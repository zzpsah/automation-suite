using System.Text;
using Windows.Devices.WiFiDirect;
using Windows.Security.Credentials;

namespace DevosPrintHotspot;

internal static class Program
{
    private static readonly TaskCompletionSource<WiFiDirectAdvertisementPublisherStatus> StartTcs =
        new(TaskCreationOptions.RunContinuationsAsynchronously);

    private static WiFiDirectAdvertisementPublisher? _publisher;

    public static async Task<int> Main(string[] args)
    {
        Console.OutputEncoding = Encoding.UTF8;
        Console.Title = "DEVOS Print Hotspot";

        var ssid = GetArg(args, "--ssid") ?? "DEVOS-PRINT";
        var password = GetArg(args, "--password");

        if (string.IsNullOrWhiteSpace(password))
        {
            Console.WriteLine("DEVOS Print Hotspot (native Windows build)");
            Console.WriteLine("Internet connection is not required for this local Wi-Fi Direct AP.");
            Console.WriteLine();
            Console.Write($"SSID [{ssid}]: ");
            var enteredSsid = Console.ReadLine();
            if (!string.IsNullOrWhiteSpace(enteredSsid))
                ssid = enteredSsid.Trim();

            password = ReadPassword("Password (8-63 characters): ");
        }

        if (ssid.Length is < 1 or > 32)
        {
            Console.Error.WriteLine("ERROR: SSID must be 1-32 characters.");
            return 2;
        }

        if (password.Length is < 8 or > 63)
        {
            Console.Error.WriteLine("ERROR: Password must be 8-63 characters.");
            return 2;
        }

        try
        {
            _publisher = new WiFiDirectAdvertisementPublisher();
            var legacy = _publisher.Advertisement.LegacySettings;
            legacy.IsEnabled = true;
            legacy.Ssid = ssid;

            var credential = new PasswordCredential
            {
                Password = password
            };
            legacy.Passphrase = credential;

            _publisher.StatusChanged += (_, eventArgs) =>
            {
                Console.WriteLine($"Status: {eventArgs.Status}");
                if (eventArgs.Status == WiFiDirectAdvertisementPublisherStatus.Aborted)
                    Console.Error.WriteLine($"Wi-Fi Direct error: {eventArgs.Error}");

                if (eventArgs.Status is WiFiDirectAdvertisementPublisherStatus.Started
                    or WiFiDirectAdvertisementPublisherStatus.Aborted)
                {
                    StartTcs.TrySetResult(eventArgs.Status);
                }
            };

            Console.CancelKeyPress += (_, eventArgs) =>
            {
                eventArgs.Cancel = true;
                StopPublisher();
            };

            Console.WriteLine();
            Console.WriteLine($"Starting local access point '{ssid}'...");
            _publisher.Start();

            var completed = await Task.WhenAny(StartTcs.Task, Task.Delay(TimeSpan.FromSeconds(20)));
            if (completed != StartTcs.Task)
            {
                Console.Error.WriteLine("ERROR: Timed out waiting for Wi-Fi Direct to start.");
                Console.Error.WriteLine("Your Wi-Fi adapter/driver may not support Wi-Fi Direct Group Owner mode.");
                StopPublisher();
                return 3;
            }

            var status = await StartTcs.Task;
            if (status != WiFiDirectAdvertisementPublisherStatus.Started)
            {
                Console.Error.WriteLine("ERROR: Hotspot could not start.");
                StopPublisher();
                return 4;
            }

            Console.WriteLine();
            Console.WriteLine("HOTSPOT STARTED ✅");
            Console.WriteLine($"SSID     : {ssid}");
            Console.WriteLine("Internet : not required");
            Console.WriteLine("Purpose  : local PaperCut / print-server LAN");
            Console.WriteLine();
            Console.WriteLine("Keep this window open. Press ENTER or Ctrl+C to stop.");
            Console.ReadLine();
            StopPublisher();
            return 0;
        }
        catch (Exception ex)
        {
            Console.Error.WriteLine($"ERROR: {ex.Message}");
            Console.Error.WriteLine("If this persists, update the Wi-Fi driver and confirm Wi-Fi Direct support.");
            StopPublisher();
            return 5;
        }
    }

    private static string? GetArg(string[] args, string name)
    {
        for (var i = 0; i < args.Length; i++)
        {
            if (args[i].Equals(name, StringComparison.OrdinalIgnoreCase) && i + 1 < args.Length)
                return args[i + 1];

            if (args[i].StartsWith(name + "=", StringComparison.OrdinalIgnoreCase))
                return args[i][(name.Length + 1)..];
        }
        return null;
    }

    private static string ReadPassword(string prompt)
    {
        Console.Write(prompt);
        var buffer = new StringBuilder();
        while (true)
        {
            var key = Console.ReadKey(intercept: true);
            if (key.Key == ConsoleKey.Enter)
            {
                Console.WriteLine();
                return buffer.ToString();
            }
            if (key.Key == ConsoleKey.Backspace)
            {
                if (buffer.Length > 0)
                    buffer.Length--;
                continue;
            }
            if (!char.IsControl(key.KeyChar))
                buffer.Append(key.KeyChar);
        }
    }

    private static void StopPublisher()
    {
        try
        {
            if (_publisher is not null &&
                _publisher.Status == WiFiDirectAdvertisementPublisherStatus.Started)
            {
                Console.WriteLine("Stopping hotspot...");
                _publisher.Stop();
            }
        }
        catch
        {
            // Best-effort shutdown only.
        }
    }
}
