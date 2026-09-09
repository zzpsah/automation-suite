function scanDriveInbox() {
  const lock = LockService.getScriptLock();
  if (!lock.tryLock(1000)) {
    console.log('Drive scan skipped because another scan is active.');
    return;
  }

  try {
    const config = getConfig();
    requireConfig_(config, ['inboxFolderId']);
    const files = DriveApp.getFolderById(config.inboxFolderId).getFiles();
    let processed = 0;

    while (files.hasNext() && processed < config.batchSize) {
      const file = files.next();
      const sourceMessageId = file.getId();
      try {
        const result = registerDriveFile_(file, 'Google Drive', sourceMessageId, 'Drive Inbox');
        if (result.created) processed += 1;
      } catch (error) {
        console.error('Failed to process ' + file.getName() + ': ' + error.message);
      }
    }
    console.log('Drive scan finished. New files processed: ' + processed);
  } finally {
    lock.releaseLock();
  }
}

function installDriveScanTrigger() {
  ScriptApp.getProjectTriggers()
    .filter(function (trigger) { return trigger.getHandlerFunction() === 'scanDriveInbox'; })
    .forEach(function (trigger) { ScriptApp.deleteTrigger(trigger); });

  ScriptApp.newTrigger('scanDriveInbox').timeBased().everyMinutes(10).create();
}
