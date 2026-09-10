begin;

alter table public.documents
  drop constraint if exists documents_ai_suggestion_status_check;

alter table public.documents
  add constraint documents_ai_suggestion_status_check
  check (ai_suggestion_status in (
    'Not Requested', 'Requested', 'Processing', 'Completed',
    'Suggested', 'Accepted', 'Rejected', 'Failed'
  ));

create unique index if not exists processing_jobs_one_active_ai_review_idx
  on public.processing_jobs (document_id, job_type)
  where job_type = 'AI_REVIEW' and status in ('Queued', 'Processing');

create or replace function public.request_document_ai_review(requested_document_id uuid)
returns uuid
language plpgsql
security definer
set search_path = ''
as $$
declare
  caller_role text := (select auth.jwt() -> 'app_metadata' ->> 'role');
begin
  if auth.uid() is null or not (public.is_admin() or caller_role in ('reviewer', 'admin')) then
    raise exception 'Not authorized to request document review';
  end if;

  if not exists (select 1 from public.documents where id = requested_document_id) then
    raise exception 'Document not found';
  end if;

  if not exists (
    select 1 from public.processing_jobs
    where document_id = requested_document_id
      and job_type = 'AI_REVIEW'
      and status in ('Queued', 'Processing')
  ) then
    insert into public.processing_jobs (document_id, job_type, status, next_attempt_at)
    values (requested_document_id, 'AI_REVIEW', 'Queued', now());
  end if;

  update public.documents
  set ai_suggestion_status = 'Requested',
      processing_status = 'Queued',
      updated_at = now()
  where id = requested_document_id;

  insert into public.document_events (document_id, event_type, actor_id, details)
  values (requested_document_id, 'AI_REVIEW_REQUESTED', auth.uid(), '{}'::jsonb);

  return requested_document_id;
end;
$$;

revoke all on function public.request_document_ai_review(uuid) from public, anon;
grant execute on function public.request_document_ai_review(uuid) to authenticated;

alter table public.documents enable row level security;
drop policy if exists "reviewers read documents" on public.documents;
drop policy if exists "reviewers update documents" on public.documents;

create policy "reviewers read documents"
on public.documents for select
to authenticated
using (public.is_admin() or ((select auth.jwt()) -> 'app_metadata' ->> 'role') in ('reviewer','admin'));

create policy "reviewers update documents"
on public.documents for update
to authenticated
using (public.is_admin() or ((select auth.jwt()) -> 'app_metadata' ->> 'role') in ('reviewer','admin'))
with check (public.is_admin() or ((select auth.jwt()) -> 'app_metadata' ->> 'role') in ('reviewer','admin'));

do $$
begin
  if not exists (
    select 1 from pg_publication_tables
    where pubname = 'supabase_realtime'
      and schemaname = 'public'
      and tablename = 'documents'
  ) then
    alter publication supabase_realtime add table public.documents;
  end if;
end $$;

commit;
