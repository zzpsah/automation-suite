function registerDriveFile_(file, sourceApp, sourceMessageId, sourceLocation) {
  const existing = findDocumentBySource_(sourceApp, sourceMessageId);
  if (existing) return { document: existing, created: false };

  const record = {
    source_app: sourceApp,
    source_location: sourceLocation || null,
    source_message_id: sourceMessageId,
    original_filename: file.getName(),
    display_filename: file.getName(),
    mime_type: file.getMimeType(),
    file_size: file.getSize(),
    private_drive_file_id: file.getId(),
    private_drive_url: file.getUrl(),
    source_file_modified_at: file.getLastUpdated().toISOString(),
    category: 'Other', priority: 'NORMAL', required_action: 'Automatic processing',
    extraction_method: getConfig().extractionMode, extraction_confidence: 'LOW',
    useful: true, duplicate: false, sensitive: false, processing_status: 'Queued',
    forwarding_status: 'Not Forwarded', category_key: 'other', category_source: 'import', category_confidence: 'LOW',
    publication_status: 'Unpublished'
  };

  let document = insertDocument_(record);
  addDocumentEvent_(document.id, 'INGESTED', { source: sourceApp, filename: file.getName() });
  try {
    const processed = processDocument_(document, file);
    document = processed.document || document;
    if (document.processing_status === 'Approved' && document.publication_status === 'Published') {
      moveToPublishedArchive_(file);
    }
    return { document: document, created: true, suggestion: processed.suggestion };
  } catch (error) {
    moveToManualReviewSafe_(file, document.id, String(error.message));
    throw error;
  }
}

function processDocument_(document, file) {
  try {
    updateDocument_(document.id, { processing_status: 'Processing', source_file_modified_at: file.getLastUpdated().toISOString() });
    const extraction = extractDocument_(file);
    const category = suggestCategory_(extraction);
    const baseChanges = {
      reference_number: extraction.reference_number,
      issue_date_as_printed: extraction.issue_date_as_printed,
      issuing_authority: extraction.issuing_authority,
      subject: extraction.subject,
      short_description: extraction.short_description,
      category: category.displayName,
      category_key: category.key,
      category_source: category.source,
      category_confidence: category.confidence,
      priority: extraction.priority,
      required_action: extraction.required_action,
      deadline_as_printed: extraction.deadline_as_printed,
      full_text_ocr: extraction.text,
      extraction_method: extraction.method,
      extraction_confidence: extraction.confidence,
      processing_status: 'Processing'
    };
    let suggestion = null;
    const botVerified = String(document.source_app || '').toLowerCase() === 'telegram';
    if (getConfig().reviewProvider !== 'NONE') {
      try {
        suggestion = reviewSuggest_(file, extraction);
        Object.assign(baseChanges, geminiSuggestionChanges_(suggestion));
        baseChanges.category_key = normalizeCategoryKey_(suggestion.category) || baseChanges.category_key || 'other';
        baseChanges.category_source = suggestion.category ? 'rule' : baseChanges.category_source;
        baseChanges.category_confidence = normalizeExtractionConfidence_(suggestion.confidence || extraction.confidence);
        baseChanges.reference_number = suggestion.reference_number || baseChanges.reference_number;
        baseChanges.issue_date_as_printed = suggestion.date_as_printed || baseChanges.issue_date_as_printed;
        baseChanges.issuing_authority = suggestion.issuing_authority || baseChanges.issuing_authority;
        baseChanges.subject = suggestion.title || baseChanges.subject;
        baseChanges.short_description = suggestion.portal_description || baseChanges.short_description;
        baseChanges.required_action = suggestion.required_action || baseChanges.required_action;
        baseChanges.deadline_as_printed = suggestion.deadline_as_printed || baseChanges.deadline_as_printed;
        baseChanges.priority = normalizePriority_(suggestion.priority || baseChanges.priority);
      } catch (geminiError) {
        baseChanges.ai_suggestion_status = 'Failed';
        addDocumentEvent_(document.id, 'REVIEW_ASSISTANT_FAILED', { error: String(geminiError.message).slice(0, 500) });
      }
    }

    // Telegram is the trusted intake channel. AI enriches metadata but never blocks publication.
    if (botVerified) {
      const publicUrl = publishDriveFile_(file);
      const published = autoPublishDocument_(document.id, publicUrl, 'Telegram bot verified automatic publication');
      baseChanges.public_file_url = published.public_file_url;
      baseChanges.approved_for_publication = true;
      baseChanges.publication_status = 'Published';
      baseChanges.publication_reason = 'Telegram bot verified automatic publication';
      baseChanges.processing_status = 'Approved';
      baseChanges.sensitive = false;
      baseChanges.useful = true;
      addDocumentEvent_(document.id, 'BOT_AUTO_PUBLISHED', {
        category_key: baseChanges.category_key,
        confidence: baseChanges.category_confidence
      });
    } else if (suggestion && isAiPublicSafe_(suggestion, extraction) && baseChanges.priority !== 'IGNORE') {
      const publicUrl = publishDriveFile_(file);
      const published = autoPublishDocument_(document.id, publicUrl, 'AI automatic publication');
      baseChanges.public_file_url = published.public_file_url;
      baseChanges.approved_for_publication = true;
      baseChanges.publication_status = 'Published';
      baseChanges.publication_reason = 'AI automatic publication';
      baseChanges.processing_status = 'Approved';
      baseChanges.sensitive = false;
      addDocumentEvent_(document.id, 'AI_AUTO_PUBLISHED', { public_safe: true, confidence: baseChanges.category_confidence, category_key: baseChanges.category_key });
    } else {
      baseChanges.sensitive = true;
      baseChanges.approved_for_publication = false;
      baseChanges.publication_status = 'Unpublished';
      baseChanges.publication_reason = 'AI could not establish automatic-publication safety';
      baseChanges.processing_status = 'Processing';
    }

    const updated = updateDocument_(document.id, baseChanges);
    addDocumentEvent_(document.id, 'EXTRACTED', { method: extraction.method, confidence: extraction.confidence });
    if (suggestion) addDocumentEvent_(document.id, 'REVIEW_ASSISTANT_SUGGESTED', { provider: suggestion.provider, model: suggestion.model, display_filename: suggestion.display_filename || null, public_safe: suggestion.public_safe === true });
    return { document: updated || document, suggestion: suggestion };
  } catch (error) {
    updateDocument_(document.id, {
      processing_status: 'Processing Failed',
      extraction_confidence: 'LOW',
      approved_for_publication: false,
      publication_status: 'Unpublished',
      publication_reason: String(error.message).slice(0, 500)
    });
    addDocumentEvent_(document.id, 'PROCESSING_FAILED', { error: String(error.message).slice(0, 500) });
    throw error;
  }
}

function getSiblingFolder_(sourceFile, folderName) {
  const processingFolder = DriveApp.getFolderById(getConfig().processingFolderId);
  const parents = processingFolder.getParents();
  if (!parents.hasNext()) throw new Error('Automation root folder not found');
  const root = parents.next();
  const folders = root.getFoldersByName(folderName);
  if (!folders.hasNext()) throw new Error('Required folder not found: ' + folderName);
  return folders.next();
}

function moveToPublishedArchive_(file) {
  try {
    file.moveTo(getSiblingFolder_(file, '03_Published_Archive'));
  } catch (error) {
    console.error('Published but could not move to Published Archive: ' + error.message);
  }
}

function moveToManualReviewSafe_(file, documentId, reason) {
  try {
    file.moveTo(getSiblingFolder_(file, '04_Manual_Review'));
    addDocumentEvent_(documentId, 'MOVED_TO_MANUAL_REVIEW', { reason: reason });
  } catch (moveError) {
    addDocumentEvent_(documentId, 'MANUAL_REVIEW_MOVE_FAILED', { reason: reason, error: String(moveError.message).slice(0, 500) });
  }
}

function moveToProcessing_(file) {
  const config = getConfig();
  requireConfig_(config, ['processingFolderId']);
  file.moveTo(DriveApp.getFolderById(config.processingFolderId));
}
