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
    category: 'Other',
    priority: 'NORMAL',
    required_action: 'Needs manual review',
    extraction_method: getConfig().extractionMode,
    extraction_confidence: 'LOW',
    useful: false,
    duplicate: false,
    sensitive: true,
    processing_status: 'Queued',
    forwarding_status: 'Not Forwarded'
  };

  const document = insertDocument_(record);
  addDocumentEvent_(document.id, 'INGESTED', { source: sourceApp, filename: file.getName() });
  processDocument_(document, file);
  return { document: document, created: true };
}

function processDocument_(document, file) {
  try {
    updateDocument_(document.id, { processing_status: 'Processing' });
    const extraction = extractDocument_(file);
    updateDocument_(document.id, {
      reference_number: extraction.reference_number,
      issue_date_as_printed: extraction.issue_date_as_printed,
      issuing_authority: extraction.issuing_authority,
      subject: extraction.subject,
      short_description: extraction.short_description,
      category: extraction.category,
      priority: extraction.priority,
      required_action: extraction.required_action,
      deadline_as_printed: extraction.deadline_as_printed,
      full_text_ocr: extraction.text,
      extraction_method: extraction.method,
      extraction_confidence: extraction.confidence,
      processing_status: 'Needs Manual Review'
    });
    addDocumentEvent_(document.id, 'EXTRACTED', {
      method: extraction.method,
      confidence: extraction.confidence
    });
  } catch (error) {
    updateDocument_(document.id, {
      processing_status: 'Processing Failed',
      extraction_confidence: 'LOW'
    });
    addDocumentEvent_(document.id, 'PROCESSING_FAILED', { error: String(error.message).slice(0, 500) });
    throw error;
  }
}

function moveToProcessing_(file) {
  const config = getConfig();
  requireConfig_(config, ['processingFolderId']);
  const processingFolder = DriveApp.getFolderById(config.processingFolderId);
  file.moveTo(processingFolder);
}
