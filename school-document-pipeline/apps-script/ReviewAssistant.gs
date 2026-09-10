// Every review tool produces the same suggestion format for storage and Telegram.
function reviewSuggest_(file, extraction) {
  const provider = getConfig().reviewProvider;
  let suggestion;
  if (provider === 'GEMINI') {
    suggestion = geminiSuggest_(file, extraction);
    suggestion.model = getConfig().geminiModel;
  } else if (provider === 'RULES') {
    const filename = file.getName();
    const filenameReference = filename.match(/(?:letter\s*no|पत्रांक)[\s_.-]*([A-Za-z0-9\/_-]+)/i);
    const filenameDate = filename.match(/(?:dt|dated|date)[\s_.-]*(\d{1,2}[.-]\d{1,2}[.-]\d{2,4})/i);
    const reference = extraction.reference_number || (filenameReference ? filenameReference[1] : null);
    const printedDate = extraction.issue_date_as_printed || (filenameDate ? filenameDate[1] : null);
    const fallbackTitle = reference ? 'Official letter ' + reference : null;
    const fallbackDescription = reference || printedDate
      ? 'Official letter' + (reference ? ' reference ' + reference : '') +
        (printedDate ? ' dated ' + printedDate : '') + '. Subject needs manual review.'
      : null;
    suggestion = {
      title: extraction.subject || fallbackTitle,
      issuing_authority: extraction.issuing_authority,
      date_as_printed: printedDate,
      reference_number: reference,
      deadline_as_printed: extraction.deadline_as_printed,
      required_action: extraction.required_action,
      category: extraction.category,
      priority: extraction.priority,
      portal_description: extraction.short_description || fallbackDescription,
      display_filename: filename,
      confidence: extraction.confidence,
      notes: 'Rule-based extraction with filename fallback; verify against the source before approval.',
      model: extraction.method
    };
  } else {
    throw new Error('Unsupported review provider: ' + provider);
  }
  suggestion.provider = provider;
  return suggestion;
}

function formatReviewTelegramReport_(suggestion) {
  return [
    'Review suggestions ready (' + suggestion.provider + ').',
    'Suggested filename: ' + (suggestion.display_filename || 'Not available'),
    'Title: ' + (suggestion.title || 'Not stated'),
    'Authority: ' + (suggestion.issuing_authority || 'Not stated'),
    'Date / reference: ' + (suggestion.date_as_printed || 'Not stated') + ' / ' + (suggestion.reference_number || 'Not stated'),
    'Deadline: ' + (suggestion.deadline_as_printed || 'Not stated'),
    'Action: ' + (suggestion.required_action || 'Needs manual review'),
    'Category / priority: ' + (suggestion.category || 'Other') + ' / ' + (suggestion.priority || 'NORMAL'),
    'Description: ' + (suggestion.portal_description || 'Not stated'),
    'Status: Needs Manual Review. Original file unchanged.'
  ].join('\n').slice(0, 3500);
}
