function supabaseRequest_(method, table, query, body) {
  const config = getConfig();
  requireConfig_(config, ['supabaseUrl', 'supabaseSecret']);
  const url = config.supabaseUrl.replace(/\/$/, '') + '/rest/v1/' + table + (query || '');
  const options = {
    method: method,
    muteHttpExceptions: true,
    contentType: 'application/json',
    headers: {
      apikey: config.supabaseSecret,
      Authorization: 'Bearer ' + config.supabaseSecret,
      Prefer: 'return=representation'
    }
  };
  if (body !== undefined) options.payload = JSON.stringify(body);
  const response = UrlFetchApp.fetch(url, options);
  const status = response.getResponseCode();
  if (status < 200 || status >= 300) {
    throw new Error('Supabase request failed with HTTP ' + status + ': ' + response.getContentText().slice(0, 500));
  }
  const text = response.getContentText();
  return text ? JSON.parse(text) : [];
}

function findDocumentBySource_(sourceApp, sourceMessageId) {
  const query = '?select=id,processing_status&source_app=eq.' +
    encodeURIComponent(sourceApp) + '&source_message_id=eq.' + encodeURIComponent(sourceMessageId) + '&limit=1';
  const rows = supabaseRequest_('get', 'documents', query);
  return rows.length ? rows[0] : null;
}

function insertDocument_(record) {
  const rows = supabaseRequest_('post', 'documents', '', record);
  return rows[0];
}

function updateDocument_(documentId, changes) {
  return supabaseRequest_('patch', 'documents', '?id=eq.' + encodeURIComponent(documentId), changes)[0];
}

function addDocumentEvent_(documentId, eventType, details) {
  supabaseRequest_('post', 'document_events', '', {
    document_id: documentId,
    event_type: eventType,
    details: details || {}
  });
}

function listCurrentCategoryDefinitions_() {
  const query = '?select=category_key,display_name,aliases,office_terms,content_terms,sort_order' +
    '&active=eq.true&valid_to=is.null&order=sort_order.asc';
  return supabaseRequest_('get', 'document_category_definitions', query);
}
