function getConfig() {
  const properties = PropertiesService.getScriptProperties();
  const requestedBatchSize = Number(properties.getProperty('DRIVE_SCAN_BATCH_SIZE') || '10');
  const safeBatchSize = Number.isFinite(requestedBatchSize)
    ? Math.max(1, Math.min(50, Math.floor(requestedBatchSize)))
    : 10;
  return {
    telegramToken: properties.getProperty('TELEGRAM_BOT_TOKEN') || '',
    telegramWebhookSecret: properties.getProperty('TELEGRAM_WEBHOOK_SECRET') || '',
    telegramUsers: parseIdList_(properties.getProperty('AUTHORIZED_TELEGRAM_USER_IDS')),
    telegramChats: parseIdList_(properties.getProperty('AUTHORIZED_TELEGRAM_CHAT_IDS')),
    inboxFolderId: properties.getProperty('DRIVE_INBOX_FOLDER_ID') || '',
    processingFolderId: properties.getProperty('DRIVE_PROCESSING_FOLDER_ID') || '',
    supabaseUrl: properties.getProperty('SUPABASE_URL') || '',
    supabaseSecret: properties.getProperty('SUPABASE_SERVER_SECRET') || '',
    extractionMode: properties.getProperty('EXTRACTION_MODE') || 'MANUAL_ONLY',
    batchSize: safeBatchSize
  };
}

function parseIdList_(value) {
  if (!value) return [];
  return value.split(',').map(function (item) { return item.trim(); }).filter(String);
}

function requireConfig_(config, names) {
  names.forEach(function (name) {
    if (!config[name]) throw new Error('Missing required configuration: ' + name);
  });
}
