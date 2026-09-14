begin;

create or replace function public.claim_telegram_publication_delivery(p_document_id uuid, p_chat_id text)
returns public.telegram_publication_deliveries
language plpgsql
security definer
set search_path = public
as $$
declare
  row public.telegram_publication_deliveries;
begin
  insert into public.telegram_publication_deliveries(document_id, chat_id, status)
  values (p_document_id, p_chat_id, 'pending')
  on conflict (document_id, chat_id) do nothing;

  select * into row
  from public.telegram_publication_deliveries
  where document_id = p_document_id and chat_id = p_chat_id
  for update;

  if row.status = 'sent' then
    return row;
  end if;

  if row.locked_at is not null and row.locked_at > now() - interval '10 minutes' then
    return null;
  end if;

  update public.telegram_publication_deliveries
  set locked_at = now(),
      attempts = attempts + 1,
      first_attempt_at = coalesce(first_attempt_at, now()),
      last_attempt_at = now(),
      updated_at = now(),
      last_error = null
  where document_id = p_document_id and chat_id = p_chat_id
  returning * into row;

  return row;
end;
$$;

revoke all on function public.claim_telegram_publication_delivery(uuid, text) from public, anon, authenticated;
grant execute on function public.claim_telegram_publication_delivery(uuid, text) to service_role;

commit;
