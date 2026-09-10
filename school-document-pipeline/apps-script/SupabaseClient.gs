function supabaseRequest_(method, table, query, body) {
  const config = getConfig();
  requireConfig_(config, ['supabaseUrl', 'supabaseSecret']);
  const url = config.supabaseUrl.replace(/\/$/, '') + '/rest/v1/' + table + (query || '');
  const options = { method: method, muteHttpExceptions: true, contentType: 'application/json', headers: { apikey: config.supabaseSecret, Authorization: 'Bearer ' + config.supabaseSecret, Prefer: 'return=representation' } };
  if (body !== undefined) options.payload = JSON.stringify(body);
  const response = UrlFetchApp.fetch(url, options);
  const status = response.getResponseCode();
  if (status < 200 || status >= 300) throw new Error('Supabase request failed with HTTP ' + status + ': ' + response.getContentText().slice(0, 500));
  const text = response.getContentText();
  return text ? JSON.parse(text) : [];
}

function supabaseRpc_(functionName, body) {
  const config = getConfig();
  requireConfig_(config, ['supabaseUrl', 'supabaseSecret']);
  const url = config.supabaseUrl.replace(/\/$/, '') + '/rest/v1/rpc/' + encodeURIComponent(functionName);
  const response = UrlFetchApp.fetch(url, {
    method: 'post', muteHttpExceptions: true, contentType: 'application/json',
    headers: { apikey: config.supabaseSecret, Authorization: 'Bearer ' + config.supabaseSecret, Prefer: 'return=representation' },
    payload: JSON.stringify(body || {})
  });
  const status = response.getResponseCode();
  if (status < 200 || status >= 300) throw new Error('Supabase RPC failed with HTTP ' + status + ': ' + response.getContentText().slice(0, 500));
  const text = response.getContentText();
  return text ? JSON.parse(text) : [];
}

function findDocumentBySource_(sourceApp, sourceMessageId) {
  const query = '?select=id,processing_status&source_app=eq.' + encodeURIComponent(sourceApp) + '&source_message_id=eq.' + encodeURIComponent(sourceMessageId) + '&limit=1';
  const rows = supabaseRequest_('get', 'documents', query);
  return rows.length ? rows[0] : null;
}

function insertDocument_(record) { return supabaseRequest_('post', 'documents', '', record)[0]; }
function updateDocument_(documentId, changes) { return supabaseRequest_('patch', 'documents', '?id=eq.' + encodeURIComponent(documentId), changes)[0]; }
function addDocumentEvent_(documentId, eventType, details) { supabaseRequest_('post', 'document_events', '', { document_id: documentId, event_type: eventType, details: details || {} }); }

function listCurrentCategoryDefinitions_() {
  const query = '?select=category_key,display_name,aliases,office_terms,content_terms,sort_order&active=eq.true&valid_to=is.null&order=sort_order.asc';
  return supabaseRequest_('get', 'document_category_definitions', query);
}

function listQueuedAiReviewJobs_(limit) {
  const query = '?select=id,document_id,attempt_count&job_type=eq.AI_REVIEW&status=eq.Queued&order=created_at.asc&limit=' + encodeURIComponent(limit || 5);
  return supabaseRequest_('get', 'processing_jobs', query);
}

function getDocumentForAiReview_(documentId) {
  const fields = 'id,private_drive_file_id,reference_number,issue_date_as_printed,issuing_authority,subject,short_description,required_action,deadline_as_printed,category,priority,category_key,publication_status';
  const rows = supabaseRequest_('get', 'documents', '?select=' + fields + '&id=eq.' + encodeURIComponent(documentId) + '&limit=1');
  return rows.length ? rows[0] : null;
}

function claimAiReviewJob_(jobId) { return supabaseRequest_('patch', 'processing_jobs', '?id=eq.' + encodeURIComponent(jobId), { status: 'Processing', locked_at: new Date().toISOString() })[0]; }
function completeAiReviewJob_(jobId) { return supabaseRequest_('patch', 'processing_jobs', '?id=eq.' + encodeURIComponent(jobId), { status: 'Completed', updated_at: new Date().toISOString() })[0]; }
function failAiReviewJob_(jobId, error) { return supabaseRequest_('patch', 'processing_jobs', '?id=eq.' + encodeURIComponent(jobId), { status: 'Failed', last_error: String(error.message).slice(0, 500), updated_at: new Date().toISOString() })[0]; }
