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
    category: 'Other', priority: 'NORMAL', required_action: 'Needs manual review',
    extraction_method: getConfig().extractionMode, extraction_confidence: 'LOW',
    useful: false, duplicate: false, sensitive: true, processing_status: 'Queued',
    forwarding_status: 'Not Forwarded', category_key: 'other', category_source: 'import', category_confidence: 'LOW',
    publication_status: 'Unpublished'
  };

  let document = insertDocument_(record);
  addDocumentEvent_(document.id, 'INGESTED', { source: sourceApp, filename: file.getName() });
  const processed = processDocument_(document, file);
  document = processed.document;
  return { document: document, created: true, suggestion: processed.suggestion };
}

function processDocument_(document, file) {
  try {
    updateDocument_(document.id, { processing_status: 'Processing', source_file_modified_at: file.getLastUpdated().toISOString() });
    const extraction = extractDocument_(file);
    const category = suggestCategory_(extraction);
    const baseChanges = {
      reference_number: extraction.reference_number, issue_date_as_printed: extraction.issue_date_as_printed,
      issuing_authority: extraction.issuing_authority, subject: extraction.subject, short_description: extraction.short_description,
      category: category.displayName, category_key: category.key, category_source: category.source, category_confidence: category.confidence,
      priority: extraction.priority, required_action: extraction.required_action, deadline_as_printed: extraction.deadline_as_printed,
      full_text_ocr: extraction.text, extraction_method: extraction.method, extraction_confidence: extraction.confidence,
      processing_status: 'Needs Manual Review'
    };
    let suggestion = null;
    if (getConfig().reviewProvider !== 'NONE') {
      try {
        suggestion = reviewSuggest_(file, extraction);
        Object.assign(baseChanges, geminiSuggestionChanges_(suggestion));
        baseChanges.category_key = normalizeCategoryKey_(suggestion.category) || baseChanges.category_key || 'other';
        baseChanges.category_source = suggestion.category ? 'ai' : baseChanges.category_source;
        baseChanges.category_confidence = normalizeExtractionConfidence_(suggestion.confidence || extraction.confidence);
        baseChanges.reference_number = suggestion.reference_number || baseChanges.reference_number;
        baseChanges.issue_date_as_printed = suggestion.date_as_printed || baseChanges.issue_date_as_printed;
        baseChanges.issuing_authority = suggestion.issuing_authority || baseChanges.issuing_authority;
        baseChanges.subject = suggestion.title || baseChanges.subject;
        baseChanges.short_description = suggestion.portal_description || baseChanges.short_description;
        baseChanges.required_action = suggestion.required_action || baseChanges.required_action;
        baseChanges.deadline_as_printed = suggestion.deadline_as_printed || baseChanges.deadline_as_printed;
        baseChanges.priority = normalizePriority_(suggestion.priority || baseChanges.priority);

        if (isAiPublicSafe_(suggestion, extraction) && baseChanges.priority !== 'IGNORE') {
          baseChanges.sensitive = false;
          const publicUrl = publishDriveFile_(file);
          const published = autoPublishDocument_(document.id, publicUrl, 'AI automatic publication');
          baseChanges.public_file_url = published.public_file_url;
          baseChanges.approved_for_publication = true;
          baseChanges.publication_status = 'Published';
          baseChanges.publication_reason = 'AI automatic publication';
          baseChanges.processing_status = 'Approved';
          addDocumentEvent_(document.id, 'AI_AUTO_PUBLISHED', { public_safe: true, confidence: baseChanges.category_confidence, category_key: baseChanges.category_key });
        } else {
          baseChanges.sensitive = true;
          baseChanges.approved_for_publication = false;
          baseChanges.publication_status = 'Unpublished';
          baseChanges.publication_reason = suggestion.public_safe === false ? 'AI marked document as not public-safe' : 'AI confidence insufficient for automatic publication';
        }
      } catch (geminiError) {
        baseChanges.ai_suggestion_status = 'Failed';
        addDocumentEvent_(document.id, 'REVIEW_ASSISTANT_FAILED', { error: String(geminiError.message).slice(0, 500) });
      }
    }
    const updated = updateDocument_(document.id, baseChanges);
    addDocumentEvent_(document.id, 'EXTRACTED', { method: extraction.method, confidence: extraction.confidence });
    if (suggestion) addDocumentEvent_(document.id, 'REVIEW_ASSISTANT_SUGGESTED', { provider: suggestion.provider, model: suggestion.model, display_filename: suggestion.display_filename || null, public_safe: suggestion.public_safe === true });
    return { document: updated || document, suggestion: suggestion };
  } catch (error) {
    updateDocument_(document.id, { processing_status: 'Processing Failed', extraction_confidence: 'LOW', approved_for_publication: false, publication_status: 'Unpublished' });
    addDocumentEvent_(document.id, 'PROCESSING_FAILED', { error: String(error.message).slice(0, 500) });
    throw error;
  }
}

function moveToProcessing_(file) {
  const config = getConfig();
  requireConfig_(config, ['processingFolderId']);
  file.moveTo(DriveApp.getFolderById(config.processingFolderId));
}
