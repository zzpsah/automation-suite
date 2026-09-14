using System.Windows;
using System.Windows.Input;
using Devos.WorkBrowser.Agent;
using Devos.WorkBrowser.Automation;
using Devos.WorkBrowser.Runtime;

namespace Devos.WorkBrowser;

public partial class MainWindow
{
    private readonly LocalAiAgent _localAiAgent = new();
    private bool _localAiReady;
    private DateTimeOffset _localAiLastProbe = DateTimeOffset.MinValue;

    private async void AgentShell_Loaded(object sender, RoutedEventArgs e)
    {
        await RefreshLocalAiStatusAsync();
    }

    private async void RunAgentCommand_Click(object sender, RoutedEventArgs e)
        => await ExecuteAgentFirstCommandAsync();

    private async void Window_AgentPreviewKeyDown(object sender, KeyEventArgs e)
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
            await ExecuteAgentFirstCommandAsync();
        }
    }

    private async void TestPortalAgent_Click(object sender, RoutedEventArgs e)
    {
        try
        {
            await NavigateToTestPortalAsync();
            var adapter = CreateAutomationAdapter();
            if (adapter is not null &&
                !await adapter.WaitForSelectorAsync("#students", TimeSpan.FromSeconds(10)))
            {
                throw new TimeoutException("Synthetic portal did not finish loading.");
            }

            CommandStatus.Text = "Synthetic portal loaded";
        }
        catch (Exception ex)
        {
            CommandStatus.Text = ex.Message;
        }
    }

    private async Task ExecuteAgentFirstCommandAsync()
    {
        if (_commandRunning) return;

        var command = CommandBox.Text.Trim();
        if (command.Length == 0)
        {
            CommandStatus.Text = "Tell DEVOS what you want the browser to do.";
            return;
        }

        // Preserve the deterministic 100-record acceptance workflow exactly.
        if (string.Equals(command, "process synthetic portal", StringComparison.OrdinalIgnoreCase))
        {
            await ExecuteCurrentCommandAsync();
            return;
        }

        var adapter = CreateAutomationAdapter();
        if (adapter is not null && await EnsureLocalAiReadyAsync())
        {
            try
            {
                await RunLocalAgentAsync(command, adapter);
                return;
            }
            catch (Exception ex)
            {
                _localAiReady = false;
                AiStatusText.Text = "LOCAL AI ERROR";
                AiStatusText.ToolTip = ex.Message;
                CommandStatus.Text = "Local AI failed; using deterministic fallback…";
            }
        }

        await ExecuteCurrentCommandAsync();
    }

    private async Task RunLocalAgentAsync(string goal, BrowserAutomationAdapter adapter)
    {
        _commandRunning = true;
        RunCommandButton.IsEnabled = false;
        var executor = new ActionExecutor(adapter);
        string? previousResult = null;

        try
        {
            for (var step = 1; step <= 8; step++)
            {
                CommandStatus.Text = $"DEVOS AI planning step {step}/8…";
                var snapshot = await adapter.GetAgentSnapshotAsync();
                var decision = await _localAiAgent.GetNextStepAsync(goal, snapshot, previousResult);

                if (decision.Done)
                {
                    CommandStatus.Text = string.IsNullOrWhiteSpace(decision.Message)
                        ? "DEVOS AI finished"
                        : decision.Message;
                    return;
                }

                var action = decision.Action
                    ?? throw new InvalidOperationException("Local AI did not provide an action.");
                string? descriptor = null;
                if (action.Kind is BrowserActionKind.Click or BrowserActionKind.Type)
                {
                    descriptor = await adapter.GetElementDescriptorAsync(action.Target);
                }

                if (AgentSafetyPolicy.RequiresHumanInteraction(decision.Description, descriptor))
                {
                    CommandStatus.Text = "User action required: complete the OTP/CAPTCHA/verification step personally, then run the goal again.";
                    return;
                }

                if (AgentSafetyPolicy.RequiresApproval(action, decision.Description, descriptor) &&
                    !RequestApproval(
                        string.IsNullOrWhiteSpace(decision.Description) ? decision.Message : decision.Description,
                        "DEVOS AI approval required"))
                {
                    CommandStatus.Text = "Approval declined";
                    return;
                }

                CommandStatus.Text = string.IsNullOrWhiteSpace(decision.Message)
                    ? $"DEVOS AI: {action.Kind}"
                    : decision.Message;

                var result = await executor.ExecuteAsync(action);
                previousResult = result.Success
                    ? $"SUCCESS action={action.Kind} target={action.Target} output={result.Output ?? "<none>"}"
                    : $"FAILED action={action.Kind} target={action.Target} error={result.Error ?? "unknown"}";

                if (action.Kind == BrowserActionKind.Navigate)
                {
                    await WaitForDocumentReadyAsync(adapter, TimeSpan.FromSeconds(12));
                }
                else
                {
                    await Task.Delay(180);
                }
            }

            CommandStatus.Text = "DEVOS AI paused after 8 verified steps. Run the goal again to continue.";
        }
        finally
        {
            _commandRunning = false;
            RunCommandButton.IsEnabled = true;
        }
    }

    private async Task<bool> EnsureLocalAiReadyAsync()
    {
        if (_localAiReady && DateTimeOffset.UtcNow - _localAiLastProbe < TimeSpan.FromSeconds(20))
        {
            return true;
        }

        await RefreshLocalAiStatusAsync();
        return _localAiReady;
    }

    private async Task RefreshLocalAiStatusAsync()
    {
        _localAiLastProbe = DateTimeOffset.UtcNow;
        _localAiReady = await _localAiAgent.IsAvailableAsync();
        AiStatusText.Text = _localAiReady
            ? $"LOCAL AI · {_localAiAgent.Model}"
            : "LOCAL AI OFFLINE";
        AiStatusText.ToolTip = _localAiReady
            ? "Local model is ready. Browser goals are planned on this PC."
            : $"Start Ollama and install {_localAiAgent.Model}, or use deterministic DEVOS commands.";
    }

    private static async Task WaitForDocumentReadyAsync(BrowserAutomationAdapter adapter, TimeSpan timeout)
    {
        var deadline = DateTimeOffset.UtcNow + timeout;
        while (DateTimeOffset.UtcNow < deadline)
        {
            try
            {
                var state = await adapter.ExecuteScriptAsync("document.readyState");
                if (state.Contains("complete", StringComparison.OrdinalIgnoreCase) ||
                    state.Contains("interactive", StringComparison.OrdinalIgnoreCase))
                {
                    return;
                }
            }
            catch
            {
                // Navigation can temporarily reject script execution. Retry until timeout.
            }

            await Task.Delay(200);
        }
    }
}
