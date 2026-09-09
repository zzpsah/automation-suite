begin;

drop policy if exists "reviewers read documents" on public.documents;
drop policy if exists "reviewers update documents" on public.documents;
drop policy if exists "reviewers read events" on public.document_events;
drop policy if exists "reviewers read jobs" on public.processing_jobs;

create policy "reviewers read documents"
on public.documents for select
to authenticated
using (((select auth.jwt()) -> 'app_metadata' ->> 'role') in ('reviewer','admin'));

create policy "reviewers update documents"
on public.documents for update
to authenticated
using (((select auth.jwt()) -> 'app_metadata' ->> 'role') in ('reviewer','admin'))
with check (((select auth.jwt()) -> 'app_metadata' ->> 'role') in ('reviewer','admin'));

create policy "reviewers read events"
on public.document_events for select
to authenticated
using (((select auth.jwt()) -> 'app_metadata' ->> 'role') in ('reviewer','admin'));

create policy "reviewers read jobs"
on public.processing_jobs for select
to authenticated
using (((select auth.jwt()) -> 'app_metadata' ->> 'role') in ('reviewer','admin'));

create index document_events_document_id_idx on public.document_events (document_id);
create index document_events_actor_id_idx on public.document_events (actor_id) where actor_id is not null;
create index documents_reviewed_by_idx on public.documents (reviewed_by) where reviewed_by is not null;
create index processing_jobs_document_id_idx on public.processing_jobs (document_id);

commit;
