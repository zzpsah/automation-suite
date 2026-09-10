// Apps Script ContentService redirects cause Telegram webhook retries.
// Polling acknowledges updates by offset after the handler succeeds.
function pollTelegramUpdates() {
  const pollLock = LockService.getUserLock();
  if (!pollLock.tryLock(1000)) return;
  try {
    const properties = PropertiesService.getScriptProperties();
    const offset = Number(properties.getProperty('TELEGRAM_POLL_OFFSET') || '0');
    const updates = telegramApi_('getUpdates', {
      offset: offset, limit: 10, timeout: 0,
      allowed_updates: ['message', 'channel_post']
    }).result;
    for (let index = 0; index < updates.length; index++) {
      const update = updates[index];
      const result = doPost({
        parameter: { webhook_secret: getConfig().telegramWebhookSecret },
        postData: { contents: JSON.stringify(update) }
      });
      const status = JSON.parse(result.getContent());
      if (!status.ok && status.error !== 'unauthorized sender') {
        throw new Error('Telegram update not completed; offset retained for retry');
      }
      properties.setProperty('TELEGRAM_POLL_OFFSET', String(update.update_id + 1));
    }
    console.log('Telegram polling completed: ' + updates.length + ' updates handled.');
  } finally {
    pollLock.releaseLock();
  }
}

function installTelegramPolling() {
  // Install the trigger before disabling the webhook. Do not discard updates.
  const exists = ScriptApp.getProjectTriggers().some(function (trigger) {
    return trigger.getHandlerFunction() === 'pollTelegramUpdates';
  });
  if (!exists) ScriptApp.newTrigger('pollTelegramUpdates').timeBased().everyMinutes(1).create();
  telegramApi_('deleteWebhook', { drop_pending_updates: false });
  console.log('Polling enabled. Pending updates preserved; interval approximately one minute.');
}
