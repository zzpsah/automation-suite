begin;

-- Align AI acceptance with the actual Gemini response shape and the stable
-- category taxonomy. AI suggestions remain suggestions until a human review action.
create or replace function public.accept_document_ai_suggestions(reviewed_document_id uuid)
returns uuid
language plpgsql
security definer
set search_path = ''
as $$
declare
  caller_role text := (select auth.jwt() -> 'app_metadata' ->> 'role');
  s jsonb;
  mapped_category text;
begin
  if auth.uid() is null or not (public.is_admin() or caller_role in ('reviewer','admin')) then
    raise exception 'Not authorized to accept AI suggestions' using errcode = '42501';
  end if;

  select ai_suggested_json into s from public.documents where id=reviewed_document_id for update;
  if not found then raise exception 'Document not found'; end if;
  if s is null or jsonb_typeof(s) <> 'object' then raise exception 'No AI suggestions available'; end if;

  mapped_category := case lower(trim(coalesce(s->>'category','')))
    when 'bseb' then 'bseb' when 'bihar board' then 'bseb'
    when 'examination' then 'examination' when 'exam' then 'examination'
    when 'registration' then 'registration' when 'student' then 'student'
    when 'admission' then 'admission'
    when 'payment / fee' then 'payment_fee' when 'payment' then 'payment_fee' when 'fee' then 'payment_fee'
    when 'scholarship' then 'scholarship' when 'udise' then 'udise'
    when 'school administration' then 'school_administration'
    when 'teacher / staff' then 'teacher_staff' when 'teacher' then 'teacher_staff' when 'staff' then 'teacher_staff'
    when 'attendance' then 'attendance' when 'infrastructure' then 'infrastructure'
    when 'building / repair' then 'building_repair' when 'repair' then 'building_repair'
    when 'inspection' then 'inspection' when 'meeting' then 'meeting' when 'training' then 'training'
    when 'government order' then 'government_order' when 'district office' then 'district_office'
    when 'block office' then 'block_office' when 'notice / circular' then 'notice_circular'
    when 'notice' then 'notice_circular' when 'circular' then 'notice_circular'
    when 'academic' then 'academic' when 'computer science' then 'computer_science'
    when 'data submission' then 'data_submission' when 'portal / technical issue' then 'portal_technical'
    when 'portal' then 'portal_technical' when 'deadline / urgent action' then 'deadline_urgent'
    when 'finance / accounts' then 'finance_accounts' when 'finance' then 'finance_accounts'
    when 'procurement' then 'procurement' when 'general information' then 'general_information'
    when 'other' then 'other'
    else null
  end;

  update public.documents
  set subject = coalesce(nullif(s->>'title',''), subject),
      issuing_authority = coalesce(nullif(s->>'issuing_authority',''), issuing_authority),
      reference_number = coalesce(nullif(s->>'reference_number',''), reference_number),
      short_description = coalesce(nullif(s->>'portal_description',''), short_description),
      required_action = coalesce(nullif(s->>'required_action',''), required_action),
      deadline_as_printed = coalesce(nullif(s->>'deadline_as_printed',''), deadline_as_printed),
      category_key = coalesce(mapped_category, category_key),
      category_source = case when mapped_category is not null then 'manual' else category_source end,
      category_confidence = case
        when upper(coalesce(s->>'confidence','')) in ('HIGH','MEDIUM','LOW') then upper(s->>'confidence')
        else category_confidence
      end,
      priority = case when upper(coalesce(s->>'priority','')) in ('URGENT','HIGH','NORMAL','LOW','IGNORE')
        then upper(s->>'priority') else priority end,
      ai_suggestion_status = 'Accepted',
      updated_at = now()
  where id=reviewed_document_id;

  insert into public.document_events(document_id,event_type,actor_id,details)
  values(reviewed_document_id,'AI_SUGGESTIONS_ACCEPTED',auth.uid(),jsonb_build_object('source','ai_suggested_json','category_key',mapped_category));
  return reviewed_document_id;
end;
$$;

revoke all on function public.accept_document_ai_suggestions(uuid) from public, anon;
grant execute on function public.accept_document_ai_suggestions(uuid) to authenticated;

commit;
