create or replace function public.claim_next_document()
returns setof public.documents
language sql
security definer
set search_path = public
as $$
  update public.documents d
     set status = 'processing', updated_at = now()
   where d.id = (
     select id from public.documents
      where status = 'queued'
      order by created_at
      for update skip locked
      limit 1
   )
  returning d.*;
$$;

grant execute on function public.claim_next_document() to service_role;

create or replace function public.search_documents(search_query text)
returns table (
  id uuid,
  original_filename text,
  document_type text,
  subject text,
  issuing_authority text,
  document_date date,
  status text,
  rank real
)
language sql
stable
as $$
  select d.id, d.original_filename, d.document_type, d.subject, d.issuing_authority, d.document_date, d.status,
         ts_rank(to_tsvector('simple', coalesce(d.subject,'') || ' ' || coalesce(d.issuing_authority,'') || ' ' || coalesce(d.reference_number,'') || ' ' || coalesce(d.description,'') || ' ' || coalesce(d.raw_ocr,'')), plainto_tsquery('simple', search_query)) as rank
    from public.documents d
   where plainto_tsquery('simple', search_query) @@ to_tsvector('simple', coalesce(d.subject,'') || ' ' || coalesce(d.issuing_authority,'') || ' ' || coalesce(d.reference_number,'') || ' ' || coalesce(d.description,'') || ' ' || coalesce(d.raw_ocr,''))
   order by rank desc, d.created_at desc
   limit 50;
$$;

grant execute on function public.search_documents(text) to service_role;
