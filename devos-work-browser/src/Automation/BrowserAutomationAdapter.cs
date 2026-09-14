using System.Text.Json;
using Devos.WorkBrowser.Browser;
using Devos.WorkBrowser.Runtime;
using Microsoft.Web.WebView2.Core;

namespace Devos.WorkBrowser.Automation;

public sealed class BrowserAutomationAdapter : IAutomationAdapter
{
    private readonly CoreWebView2 _core;

    public BrowserAutomationAdapter(CoreWebView2 core) => _core = core;

    public Task<string> ExecuteScriptAsync(string script) => _core.ExecuteScriptAsync(script);

    public Task NavigateAsync(string target)
    {
        var uri = UrlResolver.Resolve(target);
        _core.Navigate(uri.ToString());
        return Task.CompletedTask;
    }

    public async Task ClickAsync(string cssSelector)
    {
        var selector = JsonSerializer.Serialize(cssSelector);
        var result = await _core.ExecuteScriptAsync($"(() => {{ const el = document.querySelector({selector}); if (!el) return false; el.click(); return true; }})()");
        if (!IsTrue(result)) throw new InvalidOperationException($"Element not found: {cssSelector}");
    }

    public async Task TypeAsync(string cssSelector, string text)
    {
        var selector = JsonSerializer.Serialize(cssSelector);
        var value = JsonSerializer.Serialize(text);
        var result = await _core.ExecuteScriptAsync($"(() => {{ const el = document.querySelector({selector}); if (!el) return false; el.focus(); el.value = {value}; el.dispatchEvent(new Event('input', {{ bubbles: true }})); el.dispatchEvent(new Event('change', {{ bubbles: true }})); return true; }})()");
        if (!IsTrue(result)) throw new InvalidOperationException($"Element not found: {cssSelector}");
    }

    public async Task<string?> ReadTextAsync(string cssSelector)
    {
        var selector = JsonSerializer.Serialize(cssSelector);
        var result = await _core.ExecuteScriptAsync($"(() => {{ const el = document.querySelector({selector}); return el ? (el.innerText ?? el.textContent ?? '') : null; }})()");
        if (string.Equals(result, "null", StringComparison.OrdinalIgnoreCase)) return null;
        return JsonSerializer.Deserialize<string>(result);
    }

    public async Task<bool> ExistsAsync(string cssSelector)
    {
        var selector = JsonSerializer.Serialize(cssSelector);
        var result = await _core.ExecuteScriptAsync($"document.querySelector({selector}) !== null");
        return IsTrue(result);
    }

    public async Task<bool> WaitForSelectorAsync(string cssSelector, TimeSpan timeout, TimeSpan? pollInterval = null)
    {
        var interval = pollInterval ?? TimeSpan.FromMilliseconds(200);
        var deadline = DateTimeOffset.UtcNow + timeout;
        while (DateTimeOffset.UtcNow < deadline)
        {
            if (await ExistsAsync(cssSelector)) return true;
            await Task.Delay(interval);
        }
        return false;
    }

    public async Task<string?> ExtractTableJsonAsync(string cssSelector)
    {
        var selector = JsonSerializer.Serialize(cssSelector);
        var result = await _core.ExecuteScriptAsync($"(() => {{ const table = document.querySelector({selector}); if (!table) return null; const rows = [...table.querySelectorAll('tr')].map(r => [...r.querySelectorAll('th,td')].map(c => (c.innerText ?? '').trim())); return JSON.stringify(rows); }})()");
        if (string.Equals(result, "null", StringComparison.OrdinalIgnoreCase)) return null;
        return JsonSerializer.Deserialize<string>(result);
    }

    private static bool IsTrue(string json) => string.Equals(json.Trim(), "true", StringComparison.OrdinalIgnoreCase);
}
