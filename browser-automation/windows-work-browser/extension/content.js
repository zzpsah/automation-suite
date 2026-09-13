(() => {
  if (window.top !== window) return;
  if (document.getElementById('__devos-work-browser-launcher')) return;

  const host = document.createElement('div');
  host.id = '__devos-work-browser-launcher';
  host.style.cssText = [
    'position:fixed', 'right:18px', 'bottom:18px', 'z-index:2147483647',
    'font-family:system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif'
  ].join(';');

  const shadow = host.attachShadow({ mode: 'closed' });
  const button = document.createElement('button');
  button.type = 'button';
  button.title = 'Open DEVOS AI automation';
  button.setAttribute('aria-label', 'Open DEVOS AI automation');
  button.textContent = 'DEVOS AI';
  button.style.cssText = [
    'border:0', 'border-radius:999px', 'padding:11px 16px', 'cursor:pointer',
    'font-size:13px', 'font-weight:700', 'letter-spacing:.2px',
    'background:#4b2a82', 'color:#fff', 'box-shadow:0 8px 28px rgba(0,0,0,.22)'
  ].join(';');

  const status = document.createElement('span');
  status.style.cssText = 'display:none;margin-left:8px;font-size:11px;color:#4b2a82;background:#fff;padding:5px 8px;border-radius:8px';

  button.addEventListener('click', () => {
    chrome.runtime.sendMessage({ type: 'WWB_OPEN_AGENT', tabId: chrome.devtools?.inspectedWindow?.tabId });
    button.textContent = 'DEVOS';
    window.setTimeout(() => { button.textContent = 'DEVOS AI'; }, 1200);
  });

  shadow.append(button, status);
  document.documentElement.appendChild(host);
})();
