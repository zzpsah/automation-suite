import { createClient } from 'https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2/+esm';

export function createDocumentClient(configuration) {
  if (!configuration?.url || !configuration?.publishableKey) {
    throw new Error('Supabase public configuration is missing.');
  }

  const supabase = createClient(configuration.url, configuration.publishableKey, {
    auth: { persistSession: false, autoRefreshToken: false }
  });

  return {
    async listApprovedDocuments(filters = {}) {
      let query = supabase
        .from('approved_public_documents')
        .select('id,reference_number,issue_date,issuing_authority,subject,short_description,category,priority,required_action,deadline,public_file_url,published_at')
        .order('published_at', { ascending: false })
        .limit(100);

      if (filters.category) query = query.eq('category', filters.category);
      if (filters.priority) query = query.eq('priority', filters.priority);
      if (filters.search) {
        const safe = filters.search.replaceAll(',', ' ').trim();
        if (safe) query = query.or('subject.ilike.%' + safe + '%,short_description.ilike.%' + safe + '%,issuing_authority.ilike.%' + safe + '%');
      }

      const { data, error } = await query;
      if (error) throw error;
      return data || [];
    }
  };
}
