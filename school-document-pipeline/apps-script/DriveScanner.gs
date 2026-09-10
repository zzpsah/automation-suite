function scanDriveInbox() {
  const lock = LockService.getScriptLock();
  if (!lock.tryLock(1000)) return;
  try {
    const config = getConfig();
    requireConfig_(config, ['inboxFolderId', 'processingFolderId']);
    const files = DriveApp.getFolderById(config.inboxFolderId).getFiles();
    let processed = 0;
    while (files.hasNext() && processed < config.batchSize) {
      const file = files.next();
      try {
        const result = registerDriveFile_(file, 'Google Drive', file.getId(), 'Drive Inbox');
        moveToProcessing_(file);
        processed += 1;
        console.log((result.created ? 'Registered and moved: ' : 'Moved previously registered file: ') + file.getName());
      } catch (error) {
        console.error('Failed to process ' + file.getName() + ': ' + error.message);
      }
    }
    console.log('Drive inbox scan finished. New files processed: ' + processed);
  } finally {
    lock.releaseLock();
  }
}

function syncDriveDocuments() {
  const lock = LockService.getScriptLock();
  if (!lock.tryLock(1000)) return;
  try {
    const docs = listDocumentsForDriveSync_();
    docs.forEach(function (doc) {
      try {
        const file = DriveApp.getFileById(doc.private_drive_file_id);
        if (file.isTrashed()) {
          markDriveDocumentUnavailable_(doc, 'Source file unavailable');
          return;
        }
        const modified = file.getLastUpdated().toISOString();
        if (doc.source_file_modified_at && modified === doc.source_file_modified_at) return;

        updateDocument_(doc.id, {
          source_file_modified_at: modified,
          approved_for_publication: false,
          publication_status: 'Unpublished',
          publication_reason: 'Source file changed; awaiting automatic re-index',
          unpublished_at: new Date().toISOString(),
          processing_status: 'Queued',
          ai_suggestion_status: 'Queued'
        });
        enqueueAiReviewJob_(doc.id);
        addDocumentEvent_(doc.id, 'SOURCE_FILE_CHANGED', { modified_at: modified });
      } catch (error) {
        markDriveDocumentUnavailable_(doc, 'Source file unavailable');
      }
    });
  } finally {
    lock.releaseLock();
  }
}

function listDocumentsForDriveSync_() {
  return supabaseRequest_('get', 'documents', '?select=id,private_drive_file_id,source_file_modified_at,publication_status&private_drive_file_id=not.is.null&limit=1000');
}

function markDriveDocumentUnavailable_(doc, reason) {
  updateDocument_(doc.id, {
    approved_for_publication: false,
    publication_status: 'Unavailable',
    publication_reason: reason,
    unpublished_at: new Date().toISOString()
  });
  addDocumentEvent_(doc.id, 'SOURCE_FILE_UNAVAILABLE', { reason: reason });
}

function enqueueAiReviewJob_(documentId) {
  const existing = supabaseRequest_('get', 'processing_jobs', '?select=id&document_id=eq.' + encodeURIComponent(documentId) + '&job_type=eq.AI_REVIEW&status=in.(Queued,Processing)&limit=1');
  if (existing.length) return existing[0];
  return supabaseRequest_('post', 'processing_jobs', '', { document_id: documentId, job_type: 'AI_REVIEW', status: 'Queued' })[0];
}

function installDriveScanTrigger() {
  ScriptApp.getProjectTriggers().filter(function (trigger) {
    return trigger.getHandlerFunction() === 'scanDriveInbox';
  }).forEach(function (trigger) { ScriptApp.deleteTrigger(trigger); });
  ScriptApp.newTrigger('scanDriveInbox').timeBased().everyMinutes(10).create();
}

function installDriveSyncTrigger() {
  ScriptApp.getProjectTriggers().filter(function (trigger) {
    return trigger.getHandlerFunction() === 'syncDriveDocuments';
  }).forEach(function (trigger) { ScriptApp.deleteTrigger(trigger); });
  ScriptApp.newTrigger('syncDriveDocuments').timeBased().everyMinutes(10).create();
}
