function extractDocument_(file) {
  const mode = getConfig().extractionMode;
  if (mode === 'MANUAL_ONLY') return manualExtraction_();
  if (mode === 'DRIVE_OCR') {
    if (/^image\//i.test(file.getMimeType()) || file.getMimeType() === 'application/pdf') {
      return driveOcrExtraction_(file);
    }
    const manual = manualExtraction_();
    manual.method = 'MANUAL_UNSUPPORTED_FILE_TYPE';
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
    }, file.getBlob(), {
      ocrLanguage: 'hi',
      fields: 'id'
    });
    temporaryId = converted.id;
    const text = DocumentApp.openById(temporaryId).getBody().getText().trim();
    if (!text) throw new Error('OCR returned no text');
    return ruleBasedExtraction_(text);
  } finally {
    if (temporaryId) DriveApp.getFileById(temporaryId).setTrashed(true);
  }
}

function ruleBasedExtraction_(text) {
  const clean = normalizeOcrText_(text);

  const reference = firstMatch_(clean, [
    /(?:पत्रांक|पत्र\s*संख्या|ज्ञापांक|ज्ञापन\s*संख्या|क्रमांक|क्र\.\s*सं\.|memo\s*(?:no|number)|letter\s*(?:no|number)|ref(?:erence)?\s*(?:no|number))\s*[:.\-]?\s*([A-Za-z0-9अ-ह०-९\/_()\-\.]+)/i,
    /\b(?:No\.?|संख्या)\s*[:.]?\s*([A-Za-z0-9\/_()\-\.]{3,})/i
  ]);

  const date = extractDate_(clean);
  const subject = firstMatch_(clean, [
    /(?:विषय|विषयक|subject)\s*[:.\-]?\s*([^\r\n]{5,500})/i,
    /(?:संबंधित\s*विषय)\s*[:.\-]?\s*([^\r\n]{5,500})/i
  ]);

  const authority = extractIssuingAuthority_(clean);
  const deadline = extractDeadline_(clean);
  const requiredAction = extractRequiredAction_(clean);
  const category = inferCategory_(clean, authority, subject);
  const urgent = /अविलंब|तत्काल|अत्यावश्यक|शीघ्र|सत्वर|तुरंत|urgent|immediately|last\s*date|अंतिम\s*तिथि|अंतिम\s*दिन/i.test(clean);

  const extractedCount = [reference, date, authority, subject, deadline, requiredAction].filter(function (v) {
    return !!v;
  }).length;

  return {
    reference_number: reference || null,
    issue_date_as_printed: date || null,
    issuing_authority: authority || null,
    subject: subject ? cleanField_(subject) : null,
    short_description: subject ? cleanField_(subject) : buildDescription_(clean, authority),
    category: category,
    priority: urgent ? 'HIGH' : 'NORMAL',
    required_action: requiredAction || 'Automatic processing',
    deadline_as_printed: deadline || null,
    text: text,
    method: 'DRIVE_OCR_RULES',
    confidence: extractedCount >= 4 ? 'HIGH' : (extractedCount >= 2 ? 'MEDIUM' : 'LOW')
  };
}

function extractIssuingAuthority_(text) {
  const patterns = [
    /(?:जारी\s*करने\s*वाला\s*कार्यालय|जारीकर्ता\s*कार्यालय|जारी\s*कर्ता|जारी\s*करने\s*वाला|निर्गत\s*कर्ता|निर्गतकर्ता|प्रेषक|प्रेषक\s*कार्यालय|कार्यालय|विभाग|from|issued\s*by|issuing\s*authority|office)\s*[:.\-]?\s*([^\r\n]{3,250})/i,
    /(?:शिक्षा\s*विभाग|शिक्षा\s*निदेशालय|माध्यमिक\s*शिक्षा|प्राथमिक\s*शिक्षा|जिला\s*शिक्षा\s*पदाधिकारी|जिला\s*कार्यक्रम\s*पदाधिकारी|जिला\s*शिक्षा\s*कार्यालय|जिला\s*पदाधिकारी|प्रखंड\s*शिक्षा\s*पदाधिकारी|प्रखंड\s*शिक्षा\s*कार्यालय|बिहार\s*विद्यालय\s*परीक्षा\s*समिति|BSEB|Bihar\s*School\s*Examination\s*Board)[^\r\n]{0,180}/i
  ];

  const found = firstMatch_(text, patterns);
  if (!found) return null;

  const value = cleanField_(found)
    .replace(/^(?:मान्यवर|सेवा\s*में|प्रति|श्रीमान|श्रीमती)\s*[:.\-]?\s*/i, '')
    .trim();

  if (!value) return null;
  return normalizeAuthorityName_(value);
}

function normalizeAuthorityName_(value) {
  const v = String(value || '').trim();
  if (/बिहार\s*विद्यालय\s*परीक्षा\s*समिति|BSEB|Bihar\s*School\s*Examination\s*Board/i.test(v)) return 'BSEB';
  if (/जिला\s*शिक्षा\s*पदाधिकारी|District\s*Education\s*Officer/i.test(v)) return 'District Education Office';
  if (/जिला\s*शिक्षा\s*कार्यालय|District\s*Education\s*Office/i.test(v)) return 'District Education Office';
  if (/जिला\s*कार्यक्रम\s*पदाधिकारी/i.test(v)) return 'District Programme Officer';
  if (/जिला\s*पदाधिकारी|District\s*Magistrate/i.test(v)) return 'District Magistrate';
  return v;
}

function extractDate_(text) {
  const labelled = firstMatch_(text, [
    /(?:दिनांक|दिनांक\s*:-|तिथि|जारी\s*दिनांक|पत्र\s*दिनांक|date)\s*[:.\-]?\s*([0-9०-९]{1,2}[\/.\-][0-9०-९]{1,2}[\/.\-][0-9०-९]{2,4})/i,
    /(?:दिनांक|date)\s*[:.\-]?\s*([0-9०-९]{1,2}\s+[A-Za-z]{3,12}\s+[0-9०-९]{4})/i
  ]);
  if (labelled) return labelled;

  const all = text.match(/\b[0-9०-९]{1,2}[\/.\-][0-9०-९]{1,2}[\/.\-][0-9०-९]{2,4}\b/g) || [];
  return all.length ? all[0] : null;
}

function extractDeadline_(text) {
  return firstMatch_(text, [
    /(?:अंतिम\s*तिथि|अंतिम\s*दिन|अंतिम\s*तारीख|last\s*date|deadline|due\s*date)\s*[:.\-]?\s*([0-9०-९]{1,2}[\/.\-][0-9०-९]{1,2}[\/.\-][0-9०-९]{2,4})/i,
    /(?:दिनांक|date)\s*[:.\-]?\s*([0-9०-९]{1,2}[\/.\-][0-9०-९]{1,2}[\/.\-][0-9०-९]{2,4})/i
  ]);
}

function extractRequiredAction_(text) {
  const value = firstMatch_(text, [
    /(?:आवश्यक\s*कार्यवाही|आवश्यक\s*कार्रवाई|कार्यवाही\s*करें|कार्रवाई\s*करें|निर्देश|निर्देशित\s*किया\s*जाता\s*है|required\s*action|action\s*required)\s*[:.\-]?\s*([^\r\n]{5,400})/i
  ]);
  if (value) return cleanField_(value);
  if (/अविलंब|तत्काल|अत्यावश्यक|शीघ्र|सत्वर|तुरंत|urgent|immediately/i.test(text)) return 'Immediate action required';
  return null;
}

function inferCategory_(text, authority, subject) {
  const combined = String(text || '') + ' ' + String(subject || '') + ' ' + String(authority || '');
  if (/बिहार\s*विद्यालय\s*परीक्षा\s*समिति|BSEB|बोर्ड\s*परीक्षा|मैट्रिक|माध्यमिक\s*परीक्षा/i.test(combined)) return 'BSEB';
  if (/जिला\s*शिक्षा|जिला\s*कार्यक्रम|प्रखंड\s*शिक्षा|District\s*Education/i.test(combined)) return 'District Office';
  if (/जिला\s*पदाधिकारी|District\s*Magistrate|डीएम|DM/i.test(combined)) return 'Government Order';
  if (/वेतन|salary|पेंशन|pension|स्थापना|service\s*book|सेवा\s*पुस्तिका/i.test(combined)) return 'Service / Establishment';
  if (/छात्रवृत्ति|scholarship|नामांकन|admission|पंजीयन|registration|छात्र|student/i.test(combined)) return 'Student / Registration';
  if (/परीक्षा|exam|मूल्यांकन|evaluation|result|परिणाम/i.test(combined)) return 'Examination';
  return 'Other';
}

function buildDescription_(text, authority) {
  const lines = String(text || '').split(/\r?\n/).map(function (s) { return s.trim(); }).filter(String);
  const useful = lines.filter(function (line) {
    return line.length >= 15 && !/^https?:\/\//i.test(line);
  });
  if (useful.length) return useful.slice(0, 2).join(' ' ).slice(0, 500);
  return authority ? 'Official communication from ' + authority : null;
}

function firstMatch_(text, patterns) {
  for (let i = 0; i < patterns.length; i += 1) {
    const match = String(text || '').match(patterns[i]);
    if (match && match[1]) return match[1].trim();
  }
  return null;
}

function cleanField_(value) {
  return String(value || '')
    .replace(/[ \t]+/g, ' ')
    .replace(/^[\s:：.\-]+|[\s:：.\-]+$/g, '')
    .trim()
    .slice(0, 500);
}

function normalizeOcrText_(text) {
  return String(text || '')
    .replace(/\u00a0/g, ' ')
    .replace(/[\u200b\u200c\u200d]/g, '')
    .replace(/[ \t]+/g, ' ')
    .replace(/\r\n/g, '\n')
    .replace(/\n{3,}/g, '\n\n')
    .trim();
}

function configureFreeReviewMode() {
  PropertiesService.getScriptProperties().setProperties({
    REVIEW_PROVIDER: 'RULES',
    EXTRACTION_MODE: 'DRIVE_OCR'
  }, false);
  installAiReviewTrigger();
  console.log('Free review mode configured: Google Drive OCR plus enhanced Hindi/English field extraction.');
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
      best = { key: definition.category_key, displayName: definition.display_name, score: score, officeMatches: officeMatches };
    }
  });

  if (!best) return { key: 'other', displayName: 'Other', source: 'rule', confidence: 'LOW' };
  return {
    key: best.key,
    displayName: best.displayName,
    source: 'rule',
    confidence: best.officeMatches > 0 || best.score >= 8 ? 'HIGH' : (best.score >= 4 ? 'MEDIUM' : 'LOW')
  };
}

function normalizeSearchText_(value) {
  return String(value || '').toLocaleLowerCase().replace(/\s+/g, ' ').trim();
}

function containsTerm_(haystack, term) {
  const needle = normalizeSearchText_(term);
  return needle.length > 0 && haystack.indexOf(needle) >= 0;
}
