chrome.runtime.onInstalled.addListener(() => {
  chrome.sidePanel.setPanelBehavior({ openPanelOnActionClick: true }).catch(() => {});
});

chrome.runtime.onMessage.addListener(async (message, sender) => {
  if (message?.type !== 'WWB_TASK') return;

  const goal = typeof message.goal === 'string' ? message.goal.trim() : '';
  if (!goal) return;

  const tabId = Number.isInteger(message.tabId) ? message.tabId : sender.tab?.id;
  if (!tabId) return;

  // The extension only submits user intent. The agent runtime consumes it
  // through the declared AutomationAction/MCP gate; there is no arbitrary
  // shell, PowerShell, AHK, or script execution path here.
  chrome.runtime.sendMessage({
    type: 'WWB_TASK_ACCEPTED',
    task: { goal, tabId, receivedAt: new Date().toISOString() },
  }).catch(() => {});
});
