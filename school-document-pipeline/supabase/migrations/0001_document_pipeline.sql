begin;

create extension if not exists pgcrypto;

create table public.documents (
  id uuid primary key default gen_random_uuid(),
  canonical_document_id uuid references public.documents(id) on delete set null,
  source_app text not null,
  source_location text,
  source_message_id text,
  original_filename text,
  display_filename text,
  mime_type text,
  file_size bigint check (file_size is null or file_size >= 0),
  file_checksum text,
  private_drive_file_id text,
  private_drive_url text,
  public_file_url text,
  reference_number text,
  issue_date_as_printed text,
  normalized_issue_date date,
  received_at timestamptz not null default now(),
  issuing_authority text,
  subject text,
  short_description text,
  detailed_summary text,
  category text not null default 'Other',
  subcategory text,
  priority text not null default 'NORMAL'
    check (priority in ('URGENT','HIGH','NORMAL','LOW','IGNORE')),
  required_action text not null default 'Needs manual review',
  deadline_as_printed text,
  normalized_deadline date,
  affected_entities jsonb not null default '[]'::jsonb
    check (jsonb_typeof(affected_entities) = 'array'),
  financial_amount numeric,
  full_text_ocr text,
  extraction_method text not null default 'MANUAL_ONLY',
  extraction_confidence text not null default 'LOW'
    check (extraction_confidence in ('HIGH','MEDIUM','LOW')),
  sensitive boolean not null default false,
  useful boolean not null default false,
  duplicate boolean not null default false,
  duplicate_reason text,
  processing_status text not null default 'New'
    check (processing_status in ('New','Queued','Processing','Needs Manual Review','Action Required','Reviewed','Approved','Completed','Duplicate','Ignored','Archived','Processing Failed')),
  forwarding_status text not null default 'Not Forwarded'
    check (forwarding_status in ('Not Forwarded','Ready to Forward','Forwarded','Do Not Forward')),
  approved_for_publication boolean not null default false,
  reviewed_by uuid references auth.users(id) on delete set null,
  reviewed_at timestamptz,
  published_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (source_app, source_message_id)
);

create table public.document_events (
  id bigint generated always as identity primary key,
  document_id uuid not null references public.documents(id) on delete cascade,
  event_type text not null,
  actor_id uuid references auth.users(id) on delete set null,
  details jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create table public.processing_jobs (
  id bigint generated always as identity primary key,
  document_id uuid not null references public.documents(id) on delete cascade,
  job_type text not null,
  status text not null default 'Queued'
    check (status in ('Queued','Processing','Completed','Failed','Manual Review')),
  attempt_count integer not null default 0 check (attempt_count >= 0),
  next_attempt_at timestamptz,
  last_error text,
  locked_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index documents_received_at_idx on public.documents (received_at desc);
create index documents_issue_date_idx on public.documents (normalized_issue_date desc);
create index documents_deadline_idx on public.documents (normalized_deadline);
create index documents_category_idx on public.documents (category);
create index documents_priority_idx on public.documents (priority);
create index documents_status_idx on public.documents (processing_status);
create index documents_public_idx on public.documents (approved_for_publication, published_at desc);
create index documents_reference_idx on public.documents (reference_number);
create index documents_checksum_idx on public.documents (file_checksum) where file_checksum is not null;
create index documents_canonical_idx on public.documents (canonical_document_id) where canonical_document_id is not null;
create index processing_jobs_ready_idx on public.processing_jobs (status, next_attempt_at);

alter table public.documents enable row level security;
alter table public.document_events enable row level security;
alter table public.processing_jobs enable row level security;

create policy "public reads approved safe documents"
on public.documents for select
to anon
using (approved_for_publication and not sensitive and not duplicate);

create policy "reviewers read documents"
on public.documents for select
to authenticated
using ((select auth.jwt() -> 'app_metadata' ->> 'role') in ('reviewer','admin'));

create policy "reviewers update documents"
on public.documents for update
to authenticated
using ((select auth.jwt() -> 'app_metadata' ->> 'role') in ('reviewer','admin'))
with check ((select auth.jwt() -> 'app_metadata' ->> 'role') in ('reviewer','admin'));

create policy "reviewers read events"
on public.document_events for select
to authenticated
using ((select auth.jwt() -> 'app_metadata' ->> 'role') in ('reviewer','admin'));

create policy "reviewers read jobs"
on public.processing_jobs for select
to authenticated
using ((select auth.jwt() -> 'app_metadata' ->> 'role') in ('reviewer','admin'));

create view public.approved_public_documents
with (security_invoker = true)
as
select
  id,
  reference_number,
  normalized_issue_date as issue_date,
  issuing_authority,
  subject,
  short_description,
  category,
  priority,
  required_action,
  normalized_deadline as deadline,
  public_file_url,
  published_at
from public.documents
where approved_for_publication
  and not sensitive
  and not duplicate;

revoke all on public.documents from anon;
grant select on public.documents to anon;
grant select on public.approved_public_documents to anon;
grant select, update on public.documents to authenticated;
grant select on public.document_events, public.processing_jobs to authenticated;

commit;
