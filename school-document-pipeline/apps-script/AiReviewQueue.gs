function processAiReviewQueue() {
  const workerLock = LockService.getScriptLock();
  if (!workerLock.tryLock(1000)) return;
  try {
    const jobs = listQueuedAiReviewJobs_(5);
    jobs.forEach(function (job) { processAiReviewJob_(job); });
    console.log('AI review queue checked: ' + jobs.length + ' job(s).');
  } finally {
    workerLock.releaseLock();
  }
}

function processAiReviewJob_(job) {
  try {
    claimAiReviewJob_(job.id);
    updateDocument_(job.document_id, { ai_suggestion_status: 'Processing', processing_status: 'Processing' });

    const document = getDocumentForAiReview_(job.document_id);
    if (!document || !document.private_drive_file_id) throw new Error('Drive file reference missing');
    const file = DriveApp.getFileById(document.private_drive_file_id);
    const extraction = extractDocument_(file);
    const suggestion = reviewSuggest_(file, extraction);
    const changes = geminiSuggestionChanges_(suggestion);

    changes.ai_suggestion_status = 'Completed';
    changes.reference_number = suggestion.reference_number || document.reference_number || null;
    changes.issue_date_as_printed = suggestion.date_as_printed || document.issue_date_as_printed || null;
    changes.issuing_authority = suggestion.issuing_authority || document.issuing_authority || null;
    changes.subject = suggestion.title || document.subject || null;
    changes.short_description = suggestion.portal_description || document.short_description || null;
    changes.required_action = suggestion.required_action || document.required_action;
    changes.deadline_as_printed = suggestion.deadline_as_printed || document.deadline_as_printed || null;
    changes.category_key = normalizeCategoryKey_(suggestion.category) || document.category_key || 'other';
    changes.category_source = suggestion.category ? 'ai' : (document.category_source || 'legacy');
    changes.category_confidence = normalizeExtractionConfidence_(suggestion.confidence || extraction.confidence);
    changes.priority = normalizePriority_(suggestion.priority || document.priority);
    changes.full_text_ocr = extraction.text || null;
    changes.extraction_method = extraction.method;
    changes.extraction_confidence = extraction.confidence;
    changes.source_file_modified_at = file.getLastUpdated().toISOString();

    const botVerified = String(document.source_app || '').toLowerCase() === 'telegram';
    const publicSafe = botVerified || isAiPublicSafe_(suggestion, extraction);
    changes.sensitive = false;

    if (publicSafe) {
      const publicUrl = publishDriveFile_(file);
      const published = autoPublishDocument_(document.id, publicUrl, botVerified ? 'Telegram bot verified automatic publication' : 'AI automatic publication');
      changes.public_file_url = published.public_file_url;
      changes.approved_for_publication = true;
      changes.publication_status = 'Published';
      changes.publication_reason = botVerified ? 'Telegram bot verified automatic publication' : 'AI automatic publication';
      changes.processing_status = 'Approved';
      changes.reviewed_by = null;
      changes.reviewed_at = null;
      updateDocument_(document.id, changes);
      addDocumentEvent_(document.id, botVerified ? 'BOT_AUTO_PUBLISHED' : 'AI_AUTO_PUBLISHED', {
        provider: suggestion.provider, model: suggestion.model, public_safe: publicSafe,
        bot_verified: botVerified, category_key: changes.category_key, confidence: changes.category_confidence
      });
      if (botVerified) moveToReviewedArchive_(file);
    } else {
      changes.approved_for_publication = false;
      changes.publication_status = 'Unpublished';
      changes.publication_reason = 'AI marked document as not public-safe';
      changes.processing_status = 'Processing';
      changes.reviewed_by = null;
      changes.reviewed_at = null;
      updateDocument_(document.id, changes);
      addDocumentEvent_(document.id, 'AI_REVIEW_COMPLETED', {
        provider: suggestion.provider, model: suggestion.model,
        public_safe: false, human_review_required: false, reason: changes.publication_reason
      });
    }

    completeAiReviewJob_(job.id);
  } catch (error) {
    failAiReviewJob_(job.id, error);
    updateDocument_(job.document_id, {
      ai_suggestion_status: 'Failed',
      processing_status: 'Processing Failed',
      approved_for_publication: false,
      publication_status: 'Unpublished',
      publication_reason: String(error.message).slice(0, 500),
      reviewed_by: null,
      reviewed_at: null
    });
    addDocumentEvent_(job.document_id, 'AI_REVIEW_FAILED', { error: String(error.message).slice(0, 500) });
    try {
      const failedDocument = getDocumentForAiReview_(job.document_id);
      if (failedDocument && failedDocument.private_drive_file_id) {
        moveToManualReviewSafe_(DriveApp.getFileById(failedDocument.private_drive_file_id), job.document_id, String(error.message));
      }
    } catch (moveError) {
      console.error('Could not route failed AI job to Manual Review: ' + moveError.message);
    }
  }
}

function isAiPublicSafe_(suggestion, extraction) {
  if (suggestion.public_safe !== true) return false;
  const confidence = normalizeExtractionConfidence_(suggestion.confidence || extraction.confidence);
  if (confidence === 'LOW') return false;
  if (normalizePriority_(suggestion.priority) === 'IGNORE') return false;
  if (!suggestion.title && !suggestion.portal_description) return false;
  return true;
}

function publishDriveFile_(file) {
  try {
    file.setSharing(DriveApp.Access.ANYONE_WITH_LINK, DriveApp.Permission.VIEW);
  } catch (error) {
    throw new Error('Public Drive sharing is not permitted for this file/folder: ' + error.message);
  }
  return 'https://drive.google.com/file/d/' + encodeURIComponent(file.getId()) + '/view';
}

function autoPublishDocument_(documentId, publicUrl, reason) {
  const rows = supabaseRpc_('auto_publish_document', {
    p_document_id: documentId, p_public_file_url: publicUrl, p_reason: reason
  });
  if (!rows || !rows.length) throw new Error('Automatic publication did not return the document');
  return rows[0];
}

function normalizeExtractionConfidence_(value) {
  const v = String(value || '').toUpperCase();
  return ['HIGH', 'MEDIUM', 'LOW'].indexOf(v) >= 0 ? v : 'LOW';
}

function normalizeCategoryKey_(value) {
  const v = String(value || '').trim().toLowerCase();
  const map = {
    'bseb':'bseb','bihar board':'bseb','examination':'examination','exam':'examination',
    'registration':'registration','student':'student','admission':'admission',
    'payment / fee':'payment_fee','payment':'payment_fee','fee':'payment_fee','scholarship':'scholarship','udise':'udise',
    'school administration':'school_administration','teacher / staff':'teacher_staff','teacher':'teacher_staff','staff':'teacher_staff',
    'attendance':'attendance','infrastructure':'infrastructure','building / repair':'building_repair','repair':'building_repair',
    'inspection':'inspection','meeting':'meeting','training':'training','government order':'government_order',
    'district office':'district_office','block office':'block_office','notice / circular':'notice_circular','notice':'notice_circular','circular':'notice_circular',
    'academic':'academic','computer science':'computer_science','data submission':'data_submission','portal / technical issue':'portal_technical','portal':'portal_technical',
    'deadline / urgent action':'deadline_urgent','finance / accounts':'finance_accounts','finance':'finance_accounts','procurement':'procurement',
    'general information':'general_information','other':'other'
  };
  return map[v] || null;
}

function installAiReviewTrigger() {
  const exists = ScriptApp.getProjectTriggers().some(function (trigger) { return trigger.getHandlerFunction() === 'processAiReviewQueue'; });
  if (!exists) ScriptApp.newTrigger('processAiReviewQueue').timeBased().everyMinutes(5).create();
}
