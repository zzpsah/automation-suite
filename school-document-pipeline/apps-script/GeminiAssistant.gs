function geminiSuggest_(file, extraction) {
  const config = getConfig();
  requireConfig_(config, ['geminiApiKey', 'geminiModel']);

  const blob = file.getBlob();
  const bytes = blob.getBytes();
  if (bytes.length > 50 * 1024 * 1024) throw new Error('Gemini inline document limit exceeded');

  const prompt = [
    'You are a careful school-document indexing and publication assistant.',
    'Read only the first page for the requested summary. Do not infer missing facts.',
    'Return JSON only. Preserve dates and reference numbers exactly as printed.',
    'Decide whether this document is safe for automatic public publication on a school website.',
    'public_safe=true only for general public-facing government/school circulars, orders, notices, schedules, instructions, forms, or administrative communications.',
    'public_safe=false for student personal records, staff personal records, salary/bank data, identity documents, medical information, passwords, OTPs, confidential records, case files, or documents clearly intended for restricted circulation.',
    'If uncertain, choose false. Do not expose personal data merely because it appears on a document.',
    'Suggest a concise portal description and a safe display filename.',
    'Use null when a value is not visible on page 1.',
    'Allowed priority values: URGENT, HIGH, NORMAL, LOW, IGNORE.',
    'Allowed category examples include BSEB, Examination, Registration, Student, Admission, Payment / Fee, Scholarship, UDISE, School Administration, Teacher / Staff, Inspection, Meeting, Training, Government Order, District Office, Block Office, Notice / Circular, Academic, Data Submission, Portal / Technical Issue, Finance / Accounts, and General Information.',
    'Existing rule-based extraction for comparison: ' + JSON.stringify(extraction)
  ].join(' ');

  const schema = {
    type: 'OBJECT',
    properties: {
      title: { type: 'STRING', nullable: true },
      issuing_authority: { type: 'STRING', nullable: true },
      date_as_printed: { type: 'STRING', nullable: true },
      reference_number: { type: 'STRING', nullable: true },
      deadline_as_printed: { type: 'STRING', nullable: true },
      required_action: { type: 'STRING', nullable: true },
      category: { type: 'STRING', nullable: true },
      priority: { type: 'STRING', nullable: true },
      portal_description: { type: 'STRING', nullable: true },
      display_filename: { type: 'STRING', nullable: true },
      confidence: { type: 'STRING', nullable: true },
      public_safe: { type: 'BOOLEAN' },
      notes: { type: 'STRING', nullable: true }
    },
    required: [
      'title', 'issuing_authority', 'date_as_printed', 'reference_number',
      'deadline_as_printed', 'required_action', 'category', 'priority',
      'portal_description', 'display_filename', 'confidence', 'public_safe', 'notes'
    ]
  };

  const endpoint = 'https://generativelanguage.googleapis.com/v1beta/models/' + encodeURIComponent(config.geminiModel) + ':generateContent';
  const response = UrlFetchApp.fetch(endpoint, {
    method: 'post', contentType: 'application/json', headers: { 'x-goog-api-key': config.geminiApiKey },
    muteHttpExceptions: true,
    payload: JSON.stringify({
      contents: [{ parts: [{ text: prompt }, { inlineData: { mimeType: blob.getContentType(), data: Utilities.base64Encode(bytes) } }] }],
      generationConfig: { responseMimeType: 'application/json', responseSchema: schema, temperature: 0.1 }
    })
  });

  const status = response.getResponseCode();
  if (status < 200 || status >= 300) throw new Error('Gemini request failed with HTTP ' + status);
  const payload = JSON.parse(response.getContentText());
  const text = payload.candidates && payload.candidates[0] && payload.candidates[0].content && payload.candidates[0].content.parts && payload.candidates[0].content.parts[0] && payload.candidates[0].content.parts[0].text;
  if (!text) throw new Error('Gemini returned no structured suggestion');

  const suggestion = JSON.parse(text);
  suggestion.display_filename = sanitizeSuggestedFilename_(suggestion.display_filename, file.getName());
  suggestion.priority = normalizePriority_(suggestion.priority);
  suggestion.public_safe = suggestion.public_safe === true;
  return suggestion;
}

function sanitizeSuggestedFilename_(value, originalName) {
  const fallback = originalName || 'education-department-letter';
  const name = String(value || '').replace(/[<>:\"/\\|?*\u0000-\u001f]/g, '_').trim();
  if (!name) return fallback;
  return name.toLowerCase().endsWith('.pdf') || name.toLowerCase().endsWith('.jpg') || name.toLowerCase().endsWith('.jpeg') || name.toLowerCase().endsWith('.png') ? name : name + '.pdf';
}

function normalizePriority_(value) {
  const priority = String(value || '').toUpperCase();
  return ['URGENT', 'HIGH', 'NORMAL', 'LOW', 'IGNORE'].indexOf(priority) >= 0 ? priority : 'NORMAL';
}

function geminiSuggestionChanges_(suggestion) {
  return {
    ai_suggestion_status: 'Suggested', ai_model: suggestion.model || suggestion.provider || 'unknown',
    ai_suggested_title: suggestion.title || null, ai_suggested_display_filename: suggestion.display_filename || null,
    ai_suggested_description: suggestion.portal_description || null, ai_suggested_json: suggestion,
    ai_suggested_at: new Date().toISOString()
  };
}

function formatGeminiTelegramReport_(suggestion) {
  return [
    'Gemini suggestion ready.',
    'Suggested filename: ' + (suggestion.display_filename || 'Not available'),
    'Title: ' + (suggestion.title || 'Not available'),
    'Authority: ' + (suggestion.issuing_authority || 'Not available'),
    'Category / priority: ' + (suggestion.category || 'Not available') + ' / ' + normalizePriority_(suggestion.priority),
    'Public safe: ' + (suggestion.public_safe ? 'YES' : 'NO'),
    'Portal description: ' + (suggestion.portal_description || 'Not available')
  ].join('\n');
}
