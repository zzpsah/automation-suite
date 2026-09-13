(() => {
  if (window.__DEVOS_OVERLAY__) return;
  window.__DEVOS_OVERLAY__ = true;

  const root = document.createElement('div');
  root.id = 'devos-overlay-root';
  root.innerHTML = `
    <style>
      :host, * { box-sizing: border-box; }
      #devos-root {
        position: fixed;
        right: 20px;
        bottom: 20px;
        z-index: 2147483647;
        font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      }
      #devos-fab {
        width: 54px;
        height: 54px;
        border: 0;
        border-radius: 16px;
        cursor: pointer;
        background: #111827;
        color: white;
        font-weight: 700;
        box-shadow: 0 10px 30px rgba(0,0,0,.25);
      }
      #devos-panel {
        display: none;
        width: min(380px, calc(100vw - 40px));
        margin-bottom: 10px;
        padding: 14px;
        border-radius: 18px;
        background: rgba(255,255,255,.98);
        border: 1px solid rgba(17,24,39,.12);
        box-shadow: 0 20px 60px rgba(0,0,0,.25);
      }
      #devos-panel.open { display: block; }
      #devos-title { font-weight: 800; font-size: 15px; margin-bottom: 8px; }
      #devos-goal {
        width: 100%;
        min-height: 92px;
        resize: vertical;
        border: 1px solid #d1d5db;
        border-radius: 12px;
        padding: 10px;
        font: inherit;
        outline: none;
      }
      #devos-actions { display: flex; gap: 8px; margin-top: 9px; }
      #devos-run, #devos-close {
        border: 0;
        border-radius: 10px;
        padding: 9px 12px;
        cursor: pointer;
        font-weight: 700;
      }
      #devos-run { background: #111827; color: #fff; flex: 1; }
      #devos-close { background: #f3f4f6; color: #111827; }
      #devos-status { margin-top: 8px; min-height: 18px; color: #4b5563; font-size: 12px; }
      #devos-presets { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 9px; }
      .devos-preset { border: 1px solid #e5e7eb; background: #f9fafb; border-radius: 999px; padding: 6px 9px; cursor: pointer; font-size: 11px; }
    </style>
    <div id="devos-root">
      <section id="devos-panel" aria-label="DEVOS AI command panel">
        <div id="devos-title">DEVOS AI</div>
        <textarea id="devos-goal" placeholder="What should I do on this page?"></textarea>
        <div id="devos-presets">
          <button class="devos-preset" data-goal="Extract the useful records from this page and prepare a clean dataset.">Extract</button>
          <button class="devos-preset" data-goal="Prepare the selected image for crop, resize and compression.">Image</button>
          <button class="devos-preset" data-goal="Open the available PDF tools for the current document.">PDF</button>
          <button class="devos-preset" data-goal="Inspect the available files and prepare an export.">Files</button>
        </div>
        <div id="devos-actions">
          <button id="devos-run">Run task</button>
          <button id="devos-close">Close</button>
        </div>
        <div id="devos-status">Ready</div>
      </section>
      <button id="devos-fab" title="Open DEVOS AI">AI</button>
    </div>
  `;

  const mount = document.body || document.documentElement;
  mount.appendChild(root);

  const panel = root.querySelector('#devos-panel');
  const fab = root.querySelector('#devos-fab');
  const goal = root.querySelector('#devos-goal');
  const run = root.querySelector('#devos-run');
  const close = root.querySelector('#devos-close');
  const status = root.querySelector('#devos-status');

  fab.addEventListener('click', () => {
    panel.classList.toggle('open');
    if (panel.classList.contains('open')) goal.focus();
  });

  close.addEventListener('click', () => panel.classList.remove('open'));

  root.querySelectorAll('.devos-preset').forEach((button) => {
    button.addEventListener('click', () => {
      goal.value = button.dataset.goal || '';
      goal.focus();
    });
  });

  run.addEventListener('click', () => {
    const text = goal.value.trim();
    if (!text) {
      status.textContent = 'Enter a task first.';
      goal.focus();
      return;
    }
    status.textContent = 'Sending task to DEVOS agent...';
    chrome.runtime.sendMessage({ type: 'WWB_TASK', goal: text })
      .catch((error) => {
        status.textContent = `Agent bridge unavailable: ${error?.message || error}`;
      });
  });

  chrome.runtime.onMessage.addListener((message) => {
    if (message?.type === 'WWB_TASK_ACCEPTED') {
      status.textContent = `Task accepted: ${message.task?.id || 'queued'}`;
    } else if (message?.type === 'WWB_TASK_FAILED') {
      status.textContent = `Task failed: ${message.error || 'unknown error'}`;
    }
  });
})();
