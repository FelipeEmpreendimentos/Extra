-- SalesBoard Finance — launch hardening
-- Applied to production Supabase on 2026-08-12.
-- Run after schema.sql on a fresh environment until schema.sql is consolidated.

-- Recurring occurrences need a stable source reference so the scheduled
-- processor can be idempotent and never generate the same occurrence twice.
alter table public.transactions
  add column if not exists recurrence_source_id uuid references public.transactions(id) on delete set null;

create index if not exists idx_transactions_recurrence_source
  on public.transactions(recurrence_source_id);

create unique index if not exists uq_transactions_recurrence_occurrence
  on public.transactions(recurrence_source_id, transaction_date)
  where recurrence_source_id is not null;

-- Internal SECURITY DEFINER functions must not be directly callable by
-- browser roles. They are used by triggers / server-side logic only.
revoke all on function public.current_entitlement(uuid) from authenticated, anon, public;
revoke all on function public.enforce_financial_write() from authenticated, anon, public;
revoke all on function public.handle_new_user() from authenticated, anon, public;

-- Keep the webhook idempotency table completely private to the server role.
alter table public.webhook_events enable row level security;
revoke all on public.webhook_events from anon, authenticated;
