begin;

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
    where document_id = requested_document_id and job_type = 'AI_REVIEW'
      and status in ('Queued', 'Processing')
  ) then
    insert into public.processing_jobs (document_id, job_type, status, next_attempt_at)
    values (requested_document_id, 'AI_REVIEW', 'Queued', now());
  end if;
  update public.documents set ai_suggestion_status='Requested', processing_status='Queued', updated_at=now()
  where id=requested_document_id;
  insert into public.document_events(document_id,event_type,actor_id,details)
  values(requested_document_id,'AI_REVIEW_REQUESTED',auth.uid(),'{}'::jsonb);
  return requested_document_id;
end;
$$;

revoke all on function public.request_document_ai_review(uuid) from public, anon;
grant execute on function public.request_document_ai_review(uuid) to authenticated;
revoke all on function public.is_admin() from public, anon;
grant execute on function public.is_admin() to authenticated;

drop policy if exists "reviewers read documents" on public.documents;
drop policy if exists "reviewers update documents" on public.documents;
create policy "reviewers read documents" on public.documents for select to authenticated
using (public.is_admin() or ((select auth.jwt()) -> 'app_metadata' ->> 'role') in ('reviewer','admin'));
create policy "reviewers update documents" on public.documents for update to authenticated
using (public.is_admin() or ((select auth.jwt()) -> 'app_metadata' ->> 'role') in ('reviewer','admin'))
with check (public.is_admin() or ((select auth.jwt()) -> 'app_metadata' ->> 'role') in ('reviewer','admin'));

commit;
