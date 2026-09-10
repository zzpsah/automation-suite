// Every review tool produces the same suggestion format for storage and Telegram.
function reviewSuggest_(file, extraction) {
  const provider = getConfig().reviewProvider;
  let suggestion;
  if (provider === 'GEMINI') {
    suggestion = geminiSuggest_(file, extraction);
    suggestion.model = getConfig().geminiModel;
  } else if (provider === 'RULES') {
    suggestion = {
      title: extraction.subject,
      issuing_authority: extraction.issuing_authority,
      date_as_printed: extraction.issue_date_as_printed,
      reference_number: extraction.reference_number,
      deadline_as_printed: extraction.deadline_as_printed,
      required_action: extraction.required_action,
      category: extraction.category,
      priority: extraction.priority,
      portal_description: extraction.short_description,
      display_filename: file.getName(),
      confidence: extraction.confidence,
      notes: 'Rule-based extraction; verify against the source before approval.',
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
