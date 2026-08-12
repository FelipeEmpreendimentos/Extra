-- SalesBoard Finance v3 - Automated recurring transactions
-- Run after 002_integrity.sql.

alter table public.transactions
  add column if not exists recurrence_source_id uuid references public.transactions(id) on delete set null;

create index if not exists idx_transactions_recurrence_source
  on public.transactions(recurrence_source_id, transaction_date);

-- One generated occurrence per recurring source/date.
create unique index if not exists uq_transactions_recurring_occurrence
  on public.transactions(recurrence_source_id, transaction_date)
  where recurrence_source_id is not null;

-- A generated occurrence must belong to the same owner as its recurring source.
create or replace function public.validate_recurrence_source()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
declare
  source_owner uuid;
  source_is_recurring boolean;
begin
  if new.recurrence_source_id is null then
    return new;
  end if;

  select user_id, recurring into source_owner, source_is_recurring
  from public.transactions
  where id = new.recurrence_source_id;

  if source_owner is null or source_owner <> new.user_id or source_is_recurring is not true then
    raise exception 'INVALID_RECURRENCE_SOURCE' using errcode = 'P0001';
  end if;

  return new;
end;
$$;

revoke all on function public.validate_recurrence_source() from public, anon, authenticated;

drop trigger if exists transactions_validate_recurrence_source on public.transactions;
create trigger transactions_validate_recurrence_source
before insert or update on public.transactions
for each row execute function public.validate_recurrence_source();

-- Prevent changing the type of a category while existing transactions depend on it.
create or replace function public.prevent_category_type_change_when_used()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
begin
  if new.type <> old.type and exists (
    select 1 from public.transactions where category_id = old.id limit 1
  ) then
    raise exception 'CATEGORY_TYPE_IN_USE' using errcode = 'P0001';
  end if;
  return new;
end;
$$;

revoke all on function public.prevent_category_type_change_when_used() from public, anon, authenticated;

drop trigger if exists categories_prevent_type_change_when_used on public.categories;
create trigger categories_prevent_type_change_when_used
before update on public.categories
for each row execute function public.prevent_category_type_change_when_used();

-- Final launch hardening. These SECURITY DEFINER helpers are internal only and
-- must never be callable as public RPC endpoints from browser roles.
create or replace function public.current_entitlement(p_user uuid)
returns text
language plpgsql
stable
security definer
set search_path = public
as $$
declare
  p public.profiles%rowtype;
begin
  if auth.uid() is not null and auth.uid() <> p_user then
    return 'none';
  end if;

  select * into p from public.profiles where id = p_user;
  if not found then return 'none'; end if;

  if p.subscription_status = 'active' then return p.plan; end if;
  if p.subscription_status = 'trialing' and p.trial_ends_at > now() then return 'pro'; end if;
  return 'none';
end;
$$;

revoke all on function public.current_entitlement(uuid) from public, anon, authenticated;
revoke all on function public.enforce_financial_write() from public, anon, authenticated;
revoke all on function public.handle_new_user() from public, anon, authenticated;

-- Webhook event ids are server-only idempotency records. No browser policy is
-- intentionally created for this table.
alter table public.webhook_events enable row level security;
revoke all on public.webhook_events from anon, authenticated;
