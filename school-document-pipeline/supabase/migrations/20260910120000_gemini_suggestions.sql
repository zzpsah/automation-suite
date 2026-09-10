begin;

alter table public.documents
  add column if not exists ai_suggestion_status text not null default 'Not Requested'
    check (ai_suggestion_status in ('Not Requested','Suggested','Accepted','Rejected','Failed')),
  add column if not exists ai_model text,
  add column if not exists ai_suggested_title text,
  add column if not exists ai_suggested_display_filename text,
  add column if not exists ai_suggested_description text,
  add column if not exists ai_suggested_json jsonb,
  add column if not exists ai_suggested_at timestamptz;

commit;
