import fs from 'node:fs';
import vm from 'node:vm';
import assert from 'node:assert/strict';

const code = fs.readFileSync(new URL('../apps-script/TelegramWebhook.gs', import.meta.url), 'utf8');
let notifications = 0;
let released = 0;
const context = vm.createContext({
  console,
  LockService: { getScriptLock: () => ({ waitLock() {}, hasLock: () => true, releaseLock: () => released++ }) },
  getConfig: () => ({ telegramToken: 'test', telegramWebhookSecret: 'test-secret', inboxFolderId: 'test', processingFolderId: 'test', telegramUsers: ['123'], telegramChats: [] }),
  requireConfig_() {},
  findDocumentBySource_: () => ({ id: 'existing-document' }),
  ContentService: { createTextOutput: text => ({ text, setMimeType() { return this; } }), MimeType: { JSON: 'json' } },
  UrlFetchApp: { fetch() { notifications++; throw new Error('Unexpected network request on repeated delivery'); } }
});
vm.runInContext(code, context);
const event = { parameter: { webhook_secret: 'test-secret' }, postData: { contents: JSON.stringify({ update_id: 1, message: { from: { id: 123 }, chat: { id: 123 }, message_id: 2 } }) } };
for (let attempt = 0; attempt < 5; attempt++) {
  assert.equal(JSON.parse(context.doPost(event).text).duplicate, true);
}
assert.equal(notifications, 0);
assert.equal(released, 5);
console.log('Five repeated deliveries: zero notifications; all locks released.');
