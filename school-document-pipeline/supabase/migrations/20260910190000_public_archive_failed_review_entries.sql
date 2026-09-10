drop view if exists public.approved_public_documents;

create view public.approved_public_documents as
select
  d.id,
  d.reference_number,
  d.normalized_issue_date as issue_date,
  d.issuing_authority,
  d.subject,
  d.short_description,
  d.category_key,
  coalesce(c.display_name, d.category) as category,
  d.category as original_category,
  coalesce(c.aliases, '{}'::text[]) as category_aliases,
  d.priority,
  d.required_action,
  d.normalized_deadline as deadline,
  d.public_file_url,
  d.published_at,
  d.public_revision,
  case when d.processing_status = 'Processing Failed' then 'Processing Failed' else 'Published' end as listing_status,
  case when d.processing_status = 'Processing Failed' then 'document-review.html?id=' || d.id::text else null end as review_path,
  concat_ws(' ', d.subject, d.short_description, d.issuing_authority, d.reference_number, d.required_action, d.category,
    coalesce(c.display_name, ''), array_to_string(coalesce(c.aliases, '{}'::text[]), ' '),
    array_to_string(coalesce(c.office_terms, '{}'::text[]), ' '), array_to_string(coalesce(c.content_terms, '{}'::text[]), ' ')) as search_text
from public.documents d
left join public.document_category_definitions c on c.category_key = d.category_key and c.valid_to is null
where
  (d.approved_for_publication and d.publication_status = 'Published' and not d.sensitive and not d.duplicate and d.public_file_url is not null)
  or
  (d.processing_status = 'Processing Failed' and d.source_app = 'Telegram' and not d.duplicate);

grant select on public.approved_public_documents to anon, authenticated;
