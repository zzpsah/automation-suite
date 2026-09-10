create or replace function public.request_document_ai_review(requested_document_id uuid)
returns uuid language plpgsql security definer set search_path = ''
as $$
begin
  if auth.uid() is null or not coalesce(
    public.is_admin() or (auth.jwt() -> 'app_metadata' ->> 'role') in ('reviewer','admin'), false
  ) then
    raise exception 'Not authorized to request document review' using errcode = '42501';
  end if;
  perform 1 from public.documents where id=requested_document_id for update;
  if not found then raise exception 'Document not found'; end if;
  if exists(select 1 from public.processing_jobs where document_id=requested_document_id
    and job_type='AI_REVIEW' and status in ('Queued','Processing')) then
    return requested_document_id;
  end if;
  insert into public.processing_jobs(document_id,job_type,status,next_attempt_at)
    values(requested_document_id,'AI_REVIEW','Queued',now());
  update public.documents set ai_suggestion_status='Requested',processing_status='Queued',updated_at=now()
    where id=requested_document_id;
  insert into public.document_events(document_id,event_type,actor_id,details)
    values(requested_document_id,'AI_REVIEW_REQUESTED',auth.uid(),'{}'::jsonb);
  return requested_document_id;
end;
$$;
revoke all on function public.request_document_ai_review(uuid) from public, anon;
grant execute on function public.request_document_ai_review(uuid) to authenticated;
