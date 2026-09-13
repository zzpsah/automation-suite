chrome.runtime.onInstalled.addListener(() => {
  chrome.sidePanel.setPanelBehavior({ openPanelOnActionClick: true }).catch(() => {});
});

async function submitTask(goal, tabId) {
  const response = await fetch('http://127.0.0.1:17321/tasks', {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify({ goal, tabId, source: 'extension' }),
  });
  if (!response.ok) throw new Error(`Local agent returned HTTP ${response.status}.`);
  return response.json();
}

chrome.runtime.onMessage.addListener((message, sender) => {
  if (message?.type === 'WWB_OPEN_AGENT') {
    const tabId = Number.isInteger(message.tabId) ? message.tabId : sender.tab?.id;
    if (tabId) chrome.sidePanel.open({ tabId }).catch(() => {});
    return;
  }

  if (message?.type !== 'WWB_TASK') return;

  const goal = typeof message.goal === 'string' ? message.goal.trim() : '';
  if (!goal) return;

  const tabId = Number.isInteger(message.tabId) ? message.tabId : sender.tab?.id;
  if (!tabId) return;

  submitTask(goal, tabId)
    .then((task) => chrome.runtime.sendMessage({ type: 'WWB_TASK_ACCEPTED', task }).catch(() => {}))
    .catch((error) => chrome.runtime.sendMessage({
      type: 'WWB_TASK_FAILED',
      error: error instanceof Error ? error.message : String(error),
    }).catch(() => {}));
});
