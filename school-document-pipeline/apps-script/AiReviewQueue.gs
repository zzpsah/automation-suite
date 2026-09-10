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

    // AI/OCR is evidence for a human reviewer. It must never create a human
    // Reviewed state or reviewed_at timestamp on its own.
    changes.ai_suggestion_status = 'Completed';
    changes.reference_number = suggestion.reference_number || document.reference_number || null;
    changes.issue_date_as_printed = suggestion.date_as_printed || document.issue_date_as_printed || null;
    changes.issuing_authority = suggestion.issuing_authority || document.issuing_authority || null;
    changes.subject = suggestion.title || document.subject || null;
    changes.short_description = suggestion.portal_description || document.short_description || null;
    changes.required_action = suggestion.required_action || document.required_action;
    changes.deadline_as_printed = suggestion.deadline_as_printed || document.deadline_as_printed || null;
    changes.category_key = normalizeCategoryKey_(suggestion.category) || document.category_key || 'other';
    changes.category_source = suggestion.category ? 'rule' : (document.category_source || 'legacy');
    changes.category_confidence = normalizeExtractionConfidence_(suggestion.confidence || extraction.confidence);
    changes.priority = normalizePriority_(suggestion.priority || document.priority);
    changes.full_text_ocr = extraction.text || null;
    changes.extraction_method = extraction.method;
    changes.extraction_confidence = extraction.confidence;

    // Preserve an existing human-reviewed/approved state; otherwise leave the
    // record explicitly awaiting human review after AI completion.
    if (document.approved_for_publication) {
      changes.processing_status = document.processing_status;
      changes.reviewed_by = document.reviewed_by || null;
      changes.reviewed_at = document.reviewed_at || null;
    } else if (document.processing_status === 'Reviewed') {
      changes.processing_status = 'Reviewed';
      changes.reviewed_by = document.reviewed_by || null;
      changes.reviewed_at = document.reviewed_at || null;
    } else {
      changes.processing_status = 'Needs Manual Review';
      changes.reviewed_by = null;
      changes.reviewed_at = null;
    }

    updateDocument_(document.id, changes);
    completeAiReviewJob_(job.id);
    addDocumentEvent_(document.id, 'AI_REVIEW_COMPLETED', {
      provider: suggestion.provider,
      model: suggestion.model,
      filename: suggestion.display_filename || null,
      category_key: changes.category_key,
      human_review_required: !document.approved_for_publication && document.processing_status !== 'Reviewed'
    });
  } catch (error) {
    failAiReviewJob_(job.id, error);
    updateDocument_(job.document_id, {
      ai_suggestion_status: 'Failed',
      processing_status: 'Needs Manual Review',
      reviewed_by: null,
      reviewed_at: null
    });
    addDocumentEvent_(job.document_id, 'AI_REVIEW_FAILED', {
      error: String(error.message).slice(0, 500)
    });
  }
}

function normalizeExtractionConfidence_(value) {
  const v = String(value || '').toUpperCase();
  return ['HIGH', 'MEDIUM', 'LOW'].indexOf(v) >= 0 ? v : 'LOW';
}

function normalizeCategoryKey_(value) {
  const v = String(value || '').trim().toLowerCase();
  const map = {
    'bseb': 'bseb', 'bihar board': 'bseb',
    'examination': 'examination', 'exam': 'examination',
    'registration': 'registration',
    'student': 'student', 'admission': 'admission',
    'payment / fee': 'payment_fee', 'payment': 'payment_fee', 'fee': 'payment_fee',
    'scholarship': 'scholarship', 'udise': 'udise',
    'school administration': 'school_administration',
    'teacher / staff': 'teacher_staff', 'teacher': 'teacher_staff', 'staff': 'teacher_staff',
    'attendance': 'attendance', 'infrastructure': 'infrastructure',
    'building / repair': 'building_repair', 'repair': 'building_repair',
    'inspection': 'inspection', 'meeting': 'meeting', 'training': 'training',
    'government order': 'government_order',
    'district office': 'district_office', 'block office': 'block_office',
    'notice / circular': 'notice_circular', 'notice': 'notice_circular', 'circular': 'notice_circular',
    'academic': 'academic', 'computer science': 'computer_science',
    'data submission': 'data_submission', 'portal / technical issue': 'portal_technical',
    'portal': 'portal_technical', 'deadline / urgent action': 'deadline_urgent',
    'finance / accounts': 'finance_accounts', 'finance': 'finance_accounts',
    'procurement': 'procurement', 'general information': 'general_information',
    'other': 'other'
  };
  return map[v] || null;
}

function installAiReviewTrigger() {
  const exists = ScriptApp.getProjectTriggers().some(function (trigger) {
    return trigger.getHandlerFunction() === 'processAiReviewQueue';
  });
  if (!exists) ScriptApp.newTrigger('processAiReviewQueue').timeBased().everyMinutes(5).create();
}
