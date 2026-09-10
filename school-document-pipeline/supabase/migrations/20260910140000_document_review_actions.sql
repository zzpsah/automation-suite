begin;

create or replace function public.save_document_review(
  reviewed_document_id uuid,
  review_data jsonb
)
returns uuid
language plpgsql
security definer
set search_path = ''
as $$
declare
  caller_role text := (select auth.jwt() -> 'app_metadata' ->> 'role');
begin
  if auth.uid() is null or not (public.is_admin() or caller_role in ('reviewer','admin')) then
    raise exception 'Not authorized to edit document review' using errcode = '42501';
  end if;

  perform 1 from public.documents where id = reviewed_document_id for update;
  if not found then raise exception 'Document not found'; end if;

  update public.documents
  set reference_number = coalesce(nullif(trim(review_data->>'reference_number'), ''), reference_number),
      issue_date_as_printed = coalesce(nullif(trim(review_data->>'issue_date_as_printed'), ''), issue_date_as_printed),
      normalized_issue_date = case when nullif(trim(review_data->>'normalized_issue_date'), '') is null then normalized_issue_date else (review_data->>'normalized_issue_date')::date end,
      issuing_authority = coalesce(nullif(trim(review_data->>'issuing_authority'), ''), issuing_authority),
      subject = coalesce(nullif(trim(review_data->>'subject'), ''), subject),
      short_description = coalesce(nullif(trim(review_data->>'short_description'), ''), short_description),
      detailed_summary = coalesce(nullif(trim(review_data->>'detailed_summary'), ''), detailed_summary),
      category_key = coalesce(nullif(trim(review_data->>'category_key'), ''), category_key),
      required_action = coalesce(nullif(trim(review_data->>'required_action'), ''), required_action),
      deadline_as_printed = coalesce(nullif(trim(review_data->>'deadline_as_printed'), ''), deadline_as_printed),
      normalized_deadline = case when nullif(trim(review_data->>'normalized_deadline'), '') is null then normalized_deadline else (review_data->>'normalized_deadline')::date end,
      priority = coalesce(nullif(trim(review_data->>'priority'), ''), priority),
      sensitive = coalesce((review_data->>'sensitive')::boolean, sensitive),
      useful = coalesce((review_data->>'useful')::boolean, useful),
      updated_at = now()
  where id = reviewed_document_id;

  insert into public.document_events(document_id,event_type,actor_id,details)
  values(reviewed_document_id,'DOCUMENT_REVIEW_EDITED',auth.uid(),jsonb_build_object('fields',review_data));

  return reviewed_document_id;
exception when invalid_text_representation or datetime_field_overflow then
  raise exception 'Invalid date or review field value';
end;
$$;

create or replace function public.accept_document_ai_suggestions(reviewed_document_id uuid)
returns uuid
language plpgsql
security definer
set search_path = ''
as $$
declare
  caller_role text := (select auth.jwt() -> 'app_metadata' ->> 'role');
  s jsonb;
begin
  if auth.uid() is null or not (public.is_admin() or caller_role in ('reviewer','admin')) then
    raise exception 'Not authorized to accept AI suggestions' using errcode = '42501';
  end if;

  select ai_suggested_json into s from public.documents where id=reviewed_document_id for update;
  if not found then raise exception 'Document not found'; end if;
  if s is null or jsonb_typeof(s) <> 'object' then raise exception 'No AI suggestions available'; end if;

  update public.documents
  set subject = coalesce(nullif(s->>'subject',''), subject),
      issuing_authority = coalesce(nullif(s->>'issuing_authority',''), issuing_authority),
      reference_number = coalesce(nullif(s->>'reference_number',''), reference_number),
      short_description = coalesce(nullif(s->>'short_description',''), short_description),
      detailed_summary = coalesce(nullif(s->>'detailed_summary',''), detailed_summary),
      category_key = coalesce(nullif(s->>'category_key',''), category_key),
      required_action = coalesce(nullif(s->>'required_action',''), required_action),
      priority = coalesce(nullif(s->>'priority',''), priority),
      ai_suggestion_status = 'Accepted',
      updated_at = now()
  where id=reviewed_document_id;

  insert into public.document_events(document_id,event_type,actor_id,details)
  values(reviewed_document_id,'AI_SUGGESTIONS_ACCEPTED',auth.uid(),jsonb_build_object('source','ai_suggested_json'));
  return reviewed_document_id;
end;
$$;

create or replace function public.reject_document_ai_suggestions(reviewed_document_id uuid)
returns uuid
language plpgsql
security definer
set search_path = ''
as $$
declare caller_role text := (select auth.jwt() -> 'app_metadata' ->> 'role');
begin
  if auth.uid() is null or not (public.is_admin() or caller_role in ('reviewer','admin')) then
    raise exception 'Not authorized to reject AI suggestions' using errcode = '42501';
  end if;
  update public.documents
  set ai_suggestion_status='Rejected', updated_at=now()
  where id=reviewed_document_id;
  if not found then raise exception 'Document not found'; end if;
  insert into public.document_events(document_id,event_type,actor_id,details)
  values(reviewed_document_id,'AI_SUGGESTIONS_REJECTED',auth.uid(),'{}'::jsonb);
  return reviewed_document_id;
end;
$$;

create or replace function public.approve_document_for_publication(reviewed_document_id uuid)
returns uuid
language plpgsql
security definer
set search_path = ''
as $$
declare caller_role text := (select auth.jwt() -> 'app_metadata' ->> 'role');
  r public.documents%rowtype;
begin
  if auth.uid() is null or not public.is_admin() then
    raise exception 'Only an administrator can approve publication' using errcode = '42501';
  end if;
  select * into r from public.documents where id=reviewed_document_id for update;
  if not found then raise exception 'Document not found'; end if;
  if r.sensitive or r.duplicate then raise exception 'Sensitive or duplicate documents cannot be published'; end if;
  if r.processing_status not in ('Reviewed','Approved') then raise exception 'Document must be reviewed before publication approval'; end if;
  if r.public_file_url is null or trim(r.public_file_url)='' then raise exception 'A public file URL is required before publication approval'; end if;

  update public.documents
  set processing_status='Approved', approved_for_publication=true, reviewed_by=auth.uid(), reviewed_at=coalesce(reviewed_at,now()), updated_at=now()
  where id=reviewed_document_id;
  insert into public.document_events(document_id,event_type,actor_id,details)
  values(reviewed_document_id,'PUBLICATION_APPROVED',auth.uid(),'{}'::jsonb);
  return reviewed_document_id;
end;
$$;

create or replace function public.revoke_document_publication(reviewed_document_id uuid, reason text default null)
returns uuid
language plpgsql
security definer
set search_path = ''
as $$
begin
  if auth.uid() is null or not public.is_admin() then
    raise exception 'Only an administrator can revoke publication approval' using errcode = '42501';
  end if;
  update public.documents
  set approved_for_publication=false, processing_status=case when processing_status='Approved' then 'Reviewed' else processing_status end, updated_at=now()
  where id=reviewed_document_id;
  if not found then raise exception 'Document not found'; end if;
  insert into public.document_events(document_id,event_type,actor_id,details)
  values(reviewed_document_id,'PUBLICATION_APPROVAL_REVOKED',auth.uid(),jsonb_build_object('reason',coalesce(reason,'')));
  return reviewed_document_id;
end;
$$;

create or replace function public.mark_document_reviewed(reviewed_document_id uuid)
returns uuid
language plpgsql
security definer
set search_path = ''
as $$
declare caller_role text := (select auth.jwt() -> 'app_metadata' ->> 'role');
begin
  if auth.uid() is null or not (public.is_admin() or caller_role in ('reviewer','admin')) then
    raise exception 'Not authorized to mark document reviewed' using errcode = '42501';
  end if;
  update public.documents
  set processing_status='Reviewed', reviewed_by=auth.uid(), reviewed_at=now(), updated_at=now()
  where id=reviewed_document_id and not approved_for_publication;
  if not found then raise exception 'Document not found or already approved'; end if;
  insert into public.document_events(document_id,event_type,actor_id,details)
  values(reviewed_document_id,'DOCUMENT_REVIEWED',auth.uid(),'{}'::jsonb);
  return reviewed_document_id;
end;
$$;

create or replace function public.reject_document_review(reviewed_document_id uuid, reason text default null)
returns uuid
language plpgsql
security definer
set search_path = ''
as $$
declare caller_role text := (select auth.jwt() -> 'app_metadata' ->> 'role');
begin
  if auth.uid() is null or not (public.is_admin() or caller_role in ('reviewer','admin')) then
    raise exception 'Not authorized to reject document' using errcode = '42501';
  end if;
  update public.documents
  set processing_status='Needs Manual Review', approved_for_publication=false, reviewed_by=null, reviewed_at=null, updated_at=now()
  where id=reviewed_document_id;
  if not found then raise exception 'Document not found'; end if;
  insert into public.document_events(document_id,event_type,actor_id,details)
  values(reviewed_document_id,'DOCUMENT_REVIEW_REJECTED',auth.uid(),jsonb_build_object('reason',coalesce(reason,'')));
  return reviewed_document_id;
end;
$$;

revoke all on function public.save_document_review(uuid,jsonb) from public,anon;
revoke all on function public.accept_document_ai_suggestions(uuid) from public,anon;
revoke all on function public.reject_document_ai_suggestions(uuid) from public,anon;
revoke all on function public.approve_document_for_publication(uuid) from public,anon;
revoke all on function public.revoke_document_publication(uuid,text) from public,anon;
revoke all on function public.mark_document_reviewed(uuid) from public,anon;
revoke all on function public.reject_document_review(uuid,text) from public,anon;
grant execute on function public.save_document_review(uuid,jsonb) to authenticated;
grant execute on function public.accept_document_ai_suggestions(uuid) to authenticated;
grant execute on function public.reject_document_ai_suggestions(uuid) to authenticated;
grant execute on function public.approve_document_for_publication(uuid) to authenticated;
grant execute on function public.revoke_document_publication(uuid,text) to authenticated;
grant execute on function public.mark_document_reviewed(uuid) to authenticated;
grant execute on function public.reject_document_review(uuid,text) to authenticated;

commit;
