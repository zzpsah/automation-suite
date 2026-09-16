create extension if not exists pgcrypto;
create extension if not exists vector;

create table if not exists public.documents (
  id uuid primary key default gen_random_uuid(),
  source_key text not null unique,
  source_key_hash text not null,
  original_filename text not null,
  content_type text not null,
  byte_size bigint,
  sha256 text,
  status text not null default 'queued' check (status in ('queued','processing','review_required','verified','failed','automation_pending','completed')),
  document_type text,
  subject text,
  issuing_authority text,
  document_date date,
  reference_number text,
  description text,
  language text,
  raw_ocr text,
  ai_summary text,
  extraction_json jsonb not null default '{}'::jsonb,
  confidence_json jsonb not null default '{}'::jsonb,
  reviewed_at timestamptz,
  reviewed_by text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.document_pages (
  id uuid primary key default gen_random_uuid(),
  document_id uuid not null references public.documents(id) on delete cascade,
  page_number integer not null,
  source_key text not null,
  extraction_method text,
  raw_ocr text,
  normalized_text text,
  regions jsonb not null default '[]'::jsonb,
  diagnostics jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  unique(document_id, page_number)
);

create table if not exists public.document_relations (
  id uuid primary key default gen_random_uuid(),
  from_document_id uuid not null references public.documents(id) on delete cascade,
  to_document_id uuid not null references public.documents(id) on delete cascade,
  relation_type text not null,
  evidence jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  unique(from_document_id, to_document_id, relation_type)
);

create table if not exists public.automation_jobs (
  id uuid primary key default gen_random_uuid(),
  document_id uuid references public.documents(id) on delete cascade,
  portal_key text not null,
  action text not null,
  payload jsonb not null default '{}'::jsonb,
  status text not null default 'queued' check (status in ('queued','running','blocked','failed','completed')),
  attempts integer not null default 0,
  last_error text,
  external_reference text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.document_audit (
  id bigint generated always as identity primary key,
  document_id uuid not null references public.documents(id) on delete cascade,
  event_type text not null,
  actor text not null default 'system',
  details jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create index if not exists documents_status_idx on public.documents(status);
create index if not exists documents_date_idx on public.documents(document_date);
create index if not exists documents_reference_idx on public.documents(reference_number);
create index if not exists documents_fts_idx on public.documents using gin (to_tsvector('simple', coalesce(subject,'') || ' ' || coalesce(issuing_authority,'') || ' ' || coalesce(reference_number,'') || ' ' || coalesce(description,'') || ' ' || coalesce(raw_ocr,'')));

create or replace function public.touch_updated_at() returns trigger language plpgsql as $$
begin new.updated_at = now(); return new; end; $$;

drop trigger if exists documents_touch_updated_at on public.documents;
create trigger documents_touch_updated_at before update on public.documents for each row execute function public.touch_updated_at();

drop trigger if exists automation_jobs_touch_updated_at on public.automation_jobs;
create trigger automation_jobs_touch_updated_at before update on public.automation_jobs for each row execute function public.touch_updated_at();

-- The application API uses a server-side service role behind its private access guard.
-- Do not expose the service-role key to browser code.
