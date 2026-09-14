begin;

create table if not exists public.telegram_publication_deliveries (
  document_id uuid not null references public.documents(id) on delete cascade,
  chat_id text not null,
  status text not null default 'pending' check (status in ('pending','message_sent','sent','failed')),
  attempts integer not null default 0 check (attempts >= 0),
  message_id bigint,
  document_message_id bigint,
  last_error text,
  source_sha256 text,
  delivery_sha256 text,
  delivery_format text,
  source_format text,
  converted boolean,
  pages integer,
  bytes bigint,
  filename text,
  mime_type text,
  first_attempt_at timestamptz,
  last_attempt_at timestamptz,
  sent_at timestamptz,
  locked_at timestamptz,
  updated_at timestamptz not null default now(),
  created_at timestamptz not null default now(),
  primary key (document_id, chat_id)
);

create index if not exists telegram_publication_deliveries_status_idx
  on public.telegram_publication_deliveries(status, updated_at);
create index if not exists telegram_publication_deliveries_retry_idx
  on public.telegram_publication_deliveries(status, last_attempt_at);

alter table public.telegram_publication_deliveries enable row level security;

comment on table public.telegram_publication_deliveries is
  'Durable per-document/per-chat eLettersBot delivery state for autonomous retry and idempotency.';

commit;
