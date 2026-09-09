create index document_category_definitions_created_by_idx
  on public.document_category_definitions (created_by)
  where created_by is not null;
