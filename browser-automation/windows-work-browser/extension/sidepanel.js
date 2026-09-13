const status = document.getElementById('status');
const goal = document.getElementById('goal');
const run = document.getElementById('run');
const activity = document.getElementById('activity');
const approval = document.getElementById('approval');
const approvalTitle = document.getElementById('approvalTitle');
const approvalText = document.getElementById('approvalText');

function log(message) {
  const stamp = new Date().toLocaleTimeString();
  const current = activity.textContent === 'No activity yet.' ? '' : `${activity.textContent}\n`;
  activity.textContent = `${current}[${stamp}] ${message}`;
  activity.scrollTop = activity.scrollHeight;
}

async function activeTab() {
  const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
  return tabs[0];
}

run.addEventListener('click', async () => {
  const text = goal.value.trim();
  if (!text) return;
  const tab = await activeTab();
  status.textContent = 'Planning';
  log(`Task received for ${tab?.url || 'active tab'}`);
  log(text);
  chrome.runtime.sendMessage({ type: 'WWB_TASK', goal: text, tabId: tab?.id });
  status.textContent = 'Ready';
});

document.querySelectorAll('[data-action]').forEach((button) => {
  button.addEventListener('click', () => {
    const action = button.dataset.action;
    goal.value = {
      extract: 'Extract the useful records from the current site and prepare a clean dataset.',
      pdf: 'Open the available PDF tools for the current document.',
      image: 'Prepare the selected image for crop, deskew, resize or compression.',
      files: 'Open the file workspace and inspect available local or remote files.'
    }[action] || '';
    goal.focus();
  });
});

chrome.runtime.onMessage.addListener((message) => {
  if (message?.type === 'WWB_APPROVAL') {
    approval.hidden = false;
    approvalTitle.textContent = message.title || 'Approval required';
    approvalText.textContent = message.summary || 'This action has an external side effect.';
    log(`Approval requested: ${message.summary || 'external side effect'}`);
  }
});

document.getElementById('deny').addEventListener('click', () => {
  approval.hidden = true;
  log('Approval denied.');
});

document.getElementById('allow').addEventListener('click', () => {
  approval.hidden = true;
  log('Approved once.');
});
