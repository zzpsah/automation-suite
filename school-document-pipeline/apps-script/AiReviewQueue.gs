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
    updateDocument_(job.document_id, {
      ai_suggestion_status: 'Processing',
      processing_status: 'Processing'
    });

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
    changes.category = suggestion.category || document.category;
    changes.priority = normalizePriority_(suggestion.priority || document.priority);
    changes.full_text_ocr = extraction.text || null;
    changes.extraction_method = extraction.method;
    changes.extraction_confidence = extraction.confidence;
    const reliableMetadata = Boolean(extraction.subject || extraction.issuing_authority || extraction.reference_number);
    changes.processing_status = reliableMetadata ? 'Reviewed' : 'Needs Manual Review';
    changes.reviewed_at = reliableMetadata ? new Date().toISOString() : null;
    updateDocument_(document.id, changes);
    completeAiReviewJob_(job.id);
    addDocumentEvent_(document.id, 'AI_REVIEW_COMPLETED', {
      provider: suggestion.provider,
      model: suggestion.model,
      filename: suggestion.display_filename || null,
      reliable_metadata: reliableMetadata
    });
  } catch (error) {
    failAiReviewJob_(job.id, error);
    updateDocument_(job.document_id, {
      ai_suggestion_status: 'Failed',
      processing_status: 'Needs Manual Review'
    });
    addDocumentEvent_(job.document_id, 'AI_REVIEW_FAILED', {
      error: String(error.message).slice(0, 500)
    });
  }
}

function installAiReviewTrigger() {
  const exists = ScriptApp.getProjectTriggers().some(function (trigger) {
    return trigger.getHandlerFunction() === 'processAiReviewQueue';
  });
  if (!exists) ScriptApp.newTrigger('processAiReviewQueue').timeBased().everyMinutes(5).create();
}
