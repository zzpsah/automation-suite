function doPost(e) {
  try {
    const config = getConfig();
    requireConfig_(config, ['telegramToken', 'telegramWebhookSecret', 'inboxFolderId', 'processingFolderId']);

    const suppliedSecret = String(e && e.parameter && e.parameter.webhook_secret || '');
    if (!safeEqual_(suppliedSecret, config.telegramWebhookSecret)) {
      return jsonResponse_({ ok: false, error: 'unauthorized webhook' });
    }

    const update = JSON.parse((e && e.postData && e.postData.contents) || '{}');
    const message = update.message || update.channel_post;
    if (!message) return jsonResponse_({ ok: true, ignored: 'unsupported update' });

    const userId = String(message.from && message.from.id || '');
    const chatId = String(message.chat && message.chat.id || '');
    const userAllowed = config.telegramUsers.indexOf(userId) >= 0;
    const chatAllowed = config.telegramChats.indexOf(chatId) >= 0;
    if (!userAllowed && !chatAllowed) return jsonResponse_({ ok: false, error: 'unauthorized sender' });

    const sourceMessageId = chatId + ':' + String(message.message_id);
    const existing = findDocumentBySource_('Telegram', sourceMessageId);
    if (existing) {
      sendTelegramMessage_(chatId, 'Document already registered.');
      return jsonResponse_({ ok: true, duplicate: true });
    }

    const media = telegramMedia_(message);
    if (!media) {
      sendTelegramMessage_(chatId, 'Please send a PDF, document, or image.');
      return jsonResponse_({ ok: true, ignored: 'no supported attachment' });
    }

    const fileInfo = telegramApi_('getFile', { file_id: media.fileId });
    const downloadUrl = 'https://api.telegram.org/file/bot' + config.telegramToken + '/' + fileInfo.result.file_path;
    const blob = UrlFetchApp.fetch(downloadUrl).getBlob().setName(media.fileName);
    const file = DriveApp.getFolderById(config.inboxFolderId).createFile(blob);
    const result = registerDriveFile_(file, 'Telegram', sourceMessageId, 'Telegram chat ' + chatId);
    moveToProcessing_(file);
    sendTelegramMessage_(chatId, 'Document registered: ' + result.document.id);
    return jsonResponse_({ ok: true });
  } catch (error) {
    console.error('Telegram webhook failed: ' + error.message);
    return jsonResponse_({ ok: false, error: 'processing failed' });
  }
}

function registerTelegramWebhook() {
  const config = getConfig();
  requireConfig_(config, ['telegramToken', 'telegramWebhookSecret']);

  const webAppUrl = PropertiesService.getScriptProperties().getProperty('TELEGRAM_WEBAPP_URL') || '';
  requireConfig_({ webAppUrl: webAppUrl }, ['webAppUrl']);

  const separator = webAppUrl.indexOf('?') >= 0 ? '&' : '?';
  const webhookUrl = webAppUrl + separator + 'webhook_secret=' + encodeURIComponent(config.telegramWebhookSecret);
  const result = telegramApi_('setWebhook', {
    url: webhookUrl,
    allowed_updates: ['message', 'channel_post']
  });
  console.log('Telegram webhook registered: ' + JSON.stringify(result));
  return result;
}

function safeEqual_(left, right) {
  if (!left || !right || left.length !== right.length) return false;
  let difference = 0;
  for (let index = 0; index < left.length; index += 1) {
    difference |= left.charCodeAt(index) ^ right.charCodeAt(index);
  }
  return difference === 0;
}

function telegramMedia_(message) {
  if (message.document) {
    return {
      fileId: message.document.file_id,
      fileName: message.document.file_name || ('telegram-document-' + message.message_id)
    };
  }
  if (message.photo && message.photo.length) {
    const photo = message.photo[message.photo.length - 1];
    return { fileId: photo.file_id, fileName: 'telegram-photo-' + message.message_id + '.jpg' };
  }
  return null;
}

function telegramApi_(method, payload) {
  const token = getConfig().telegramToken;
  const response = UrlFetchApp.fetch('https://api.telegram.org/bot' + token + '/' + method, {
    method: 'post',
    contentType: 'application/json',
    payload: JSON.stringify(payload),
    muteHttpExceptions: true
  });
  const data = JSON.parse(response.getContentText());
  if (!data.ok) throw new Error('Telegram API request failed');
  return data;
}

function sendTelegramMessage_(chatId, text) {
  telegramApi_('sendMessage', { chat_id: chatId, text: text });
}

function jsonResponse_(value) {
  return ContentService.createTextOutput(JSON.stringify(value)).setMimeType(ContentService.MimeType.JSON);
}
