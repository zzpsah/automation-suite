-- P26: Supabase/Postgres persistence for global OCR search.
-- Keep these tables internal unless an explicit API/RLS access model is added.
create table if not exists public.ocr_search_documents (
  document_id text not null,
  page_number integer not null,
  block_id text not null,
  text text not null,
  primary key (document_id, page_number, block_id)
);

create table if not exists public.ocr_search_entities (
  document_id text not null,
  entity_id text not null,
  entity_type text not null,
  value text not null,
  page_number integer not null,
  block_id text not null,
  confidence double precision not null,
  primary key (document_id, entity_id)
);

create index if not exists idx_ocr_search_entities_type_value
  on public.ocr_search_entities (entity_type, value);
create index if not exists idx_ocr_search_entities_document
  on public.ocr_search_entities (document_id);
create index if not exists idx_ocr_search_documents_document
  on public.ocr_search_documents (document_id);

-- Defense in depth: do not expose OCR evidence tables through anonymous access.
alter table public.ocr_search_documents enable row level security;
alter table public.ocr_search_entities enable row level security;
