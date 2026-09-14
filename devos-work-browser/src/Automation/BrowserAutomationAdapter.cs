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
        var uri = CommandNavigationResolver.Resolve(target);
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

    public async Task<string> GetAgentSnapshotAsync()
    {
        const string script = """
(() => {
  const clean = value => (value ?? '').toString().replace(/\s+/g, ' ').trim();
  const shorten = (value, max) => {
    const text = clean(value);
    return text.length <= max ? text : text.slice(0, max) + '…';
  };

  const candidates = [...document.querySelectorAll('a,button,input,select,textarea,[role="button"],[role="link"],[onclick]')]
    .filter(el => {
      const rect = el.getBoundingClientRect();
      const style = window.getComputedStyle(el);
      return rect.width > 0 && rect.height > 0 && style.visibility !== 'hidden' && style.display !== 'none';
    })
    .slice(0, 120);

  const elements = candidates.map((el, index) => {
    let ref = el.getAttribute('data-devos-ref');
    if (!ref) {
      ref = `d${index + 1}`;
      el.setAttribute('data-devos-ref', ref);
    }

    const type = clean(el.getAttribute('type')).toLowerCase();
    const isPassword = type === 'password';
    return {
      selector: `[data-devos-ref="${ref}"]`,
      tag: el.tagName.toLowerCase(),
      type,
      text: isPassword ? '[password field]' : shorten(el.innerText || el.textContent, 160),
      aria: shorten(el.getAttribute('aria-label'), 120),
      title: shorten(el.getAttribute('title'), 120),
      name: shorten(el.getAttribute('name'), 100),
      placeholder: isPassword ? '[password]' : shorten(el.getAttribute('placeholder'), 120),
      role: shorten(el.getAttribute('role'), 80),
      href: el.tagName.toLowerCase() === 'a' ? shorten(el.href, 260) : ''
    };
  });

  return JSON.stringify({
    url: location.href,
    title: document.title,
    text: shorten(document.body?.innerText, 6500),
    elements
  });
})()
""";

        var result = await _core.ExecuteScriptAsync(script);
        if (string.Equals(result, "null", StringComparison.OrdinalIgnoreCase)) return "{}";
        return JsonSerializer.Deserialize<string>(result) ?? "{}";
    }

    public async Task<string?> GetElementDescriptorAsync(string cssSelector)
    {
        var selector = JsonSerializer.Serialize(cssSelector);
        var result = await _core.ExecuteScriptAsync($"""
(() => {{
  const el = document.querySelector({selector});
  if (!el) return null;
  const clean = value => (value ?? '').toString().replace(/\s+/g, ' ').trim();
  return [
    `tag=${{el.tagName.toLowerCase()}}`,
    `type=${{clean(el.getAttribute('type')).toLowerCase()}}`,
    `text=${{clean(el.innerText || el.textContent).slice(0, 180)}}`,
    `aria=${{clean(el.getAttribute('aria-label')).slice(0, 120)}}`,
    `title=${{clean(el.getAttribute('title')).slice(0, 120)}}`,
    `name=${{clean(el.getAttribute('name')).slice(0, 100)}}`,
    `role=${{clean(el.getAttribute('role')).slice(0, 80)}}`
  ].join(' ');
}})()
""");
        if (string.Equals(result, "null", StringComparison.OrdinalIgnoreCase)) return null;
        return JsonSerializer.Deserialize<string>(result);
    }

    private static bool IsTrue(string json) => string.Equals(json.Trim(), "true", StringComparison.OrdinalIgnoreCase);
}
