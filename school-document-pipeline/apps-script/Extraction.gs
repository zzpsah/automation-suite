function extractDocument_(file) {
  const mode = getConfig().extractionMode;
  if (mode === 'MANUAL_ONLY') return manualExtraction_();
  if (mode === 'DRIVE_OCR') {
    if (/^image\//i.test(file.getMimeType())) return driveOcrExtraction_(file);
    const manual = manualExtraction_();
    manual.method = file.getMimeType() === 'application/pdf'
      ? 'MANUAL_FIRST_PAGE_REQUIRED'
      : 'MANUAL_UNSUPPORTED_FILE_TYPE';
    return manual;
  }
  throw new Error('Unsupported extraction mode: ' + mode);
}

function manualExtraction_() {
  return {
    reference_number: null,
    issue_date_as_printed: null,
    issuing_authority: null,
    subject: null,
    short_description: null,
    category: 'Other',
    priority: 'NORMAL',
    required_action: 'Needs manual review',
    deadline_as_printed: null,
    text: null,
    method: 'MANUAL_ONLY',
    confidence: 'LOW'
  };
}

function driveOcrExtraction_(file) {
  let temporaryId = null;
  try {
    const converted = Drive.Files.create({
      name: 'OCR_TEMP_' + file.getName(),
      mimeType: 'application/vnd.google-apps.document'
    }, file.getBlob(), { ocrLanguage: 'hi', fields: 'id' });
    temporaryId = converted.id;
    const text = DocumentApp.openById(temporaryId).getBody().getText().trim();
    if (!text) throw new Error('OCR returned no text');
    return ruleBasedExtraction_(text);
  } finally {
    if (temporaryId) DriveApp.getFileById(temporaryId).setTrashed(true);
  }
}

function ruleBasedExtraction_(text) {
  const reference = text.match(/(?:पत्रांक|ज्ञापांक|letter\s*no|memo\s*no)\s*[:.\-]?\s*([A-Za-z0-9\/_-]+)/i);
  const dates = text.match(/\b(?:\d{1,2}[./-]\d{1,2}[./-]\d{2,4}|\d{4}-\d{2}-\d{2})\b/g) || [];
  let authority = null;
  let category = 'Other';
  if (/बिहार विद्यालय परीक्षा समिति|BSEB/i.test(text)) { authority = 'BSEB'; category = 'BSEB'; }
  else if (/जिला शिक्षा पदाधिकारी|District Education Officer/i.test(text)) { authority = 'District Education Office'; category = 'District Office'; }
  else if (/जिला पदाधिकारी|District Magistrate/i.test(text)) { authority = 'District Magistrate'; category = 'Government Order'; }

  const urgent = /अविलंब|तत्काल|अत्यावश्यक|urgent|immediately|अंतिम तिथि|last date/i.test(text);
  return {
    reference_number: reference ? reference[1] : null,
    issue_date_as_printed: dates.length ? dates[0] : null,
    issuing_authority: authority,
    subject: null,
    short_description: null,
    category: category,
    priority: urgent ? 'HIGH' : 'NORMAL',
    required_action: 'Needs manual review',
    deadline_as_printed: null,
    text: text,
    method: 'DRIVE_OCR_RULES',
    confidence: 'LOW'
  };
}

function suggestCategory_(extraction) {
  const definitions = listCurrentCategoryDefinitions_();
  const officeText = normalizeSearchText_(extraction.issuing_authority || '');
  const contentText = normalizeSearchText_([
    extraction.subject,
    extraction.short_description,
    extraction.text ? extraction.text.slice(0, 5000) : ''
  ].filter(String).join(' '));
  let best = null;

  definitions.forEach(function (definition) {
    if (definition.category_key === 'other') return;
    let score = 0;
    let officeMatches = 0;

    (definition.office_terms || []).forEach(function (term) {
      if (containsTerm_(officeText, term)) {
        score += 8;
        officeMatches += 1;
      }
    });
    (definition.content_terms || []).forEach(function (term) {
      if (containsTerm_(contentText, term)) score += 3;
    });
    (definition.aliases || []).forEach(function (term) {
      if (containsTerm_(officeText + ' ' + contentText, term)) score += 2;
    });

    if (score > 0 && (!best || score > best.score)) {
      best = {
        key: definition.category_key,
        displayName: definition.display_name,
        score: score,
        officeMatches: officeMatches
      };
    }
  });

  if (!best) {
    const other = definitions.filter(function (definition) {
      return definition.category_key === 'other';
    })[0];
    return {
      key: 'other',
      displayName: other ? other.display_name : 'Other',
      source: 'rule',
      confidence: 'LOW'
    };
  }

  return {
    key: best.key,
    displayName: best.displayName,
    source: 'rule',
    confidence: best.officeMatches > 0 || best.score >= 8
      ? 'HIGH'
      : (best.score >= 4 ? 'MEDIUM' : 'LOW')
  };
}

function normalizeSearchText_(value) {
  return String(value || '').toLocaleLowerCase().replace(/\s+/g, ' ').trim();
}

function containsTerm_(haystack, term) {
  const needle = normalizeSearchText_(term);
  return needle.length > 0 && haystack.indexOf(needle) >= 0;
}
