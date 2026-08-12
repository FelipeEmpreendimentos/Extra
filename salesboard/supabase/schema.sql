-- SalesBoard Finance v3
-- Execute this file once in the Supabase SQL Editor for the production project.
-- The browser uses only the publishable key. Sensitive billing fields are server-managed.

create extension if not exists pgcrypto;

create table if not exists public.profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  full_name text not null default '',
  workspace_name text not null default 'Meu espaço',
  workspace_type text not null default 'personal' check (workspace_type in ('personal','freelancer','business')),
  plan text not null default 'pro' check (plan in ('essential','pro')),
  subscription_status text not null default 'trialing' check (subscription_status in ('trialing','active','past_due','canceled','none')),
  trial_ends_at timestamptz not null default (now() + interval '7 days'),
  stripe_customer_id text unique,
  onboarded boolean not null default false,
  currency text not null default 'BRL',
  timezone text not null default 'America/Sao_Paulo',
  terms_accepted_at timestamptz,
  terms_version text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.accounts (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.profiles(id) on delete cascade,
  name text not null check (char_length(name) between 1 and 80),
  type text not null default 'bank' check (type in ('bank','cash','wallet','investment')),
  opening_balance numeric(14,2) not null default 0,
  icon text not null default '▣',
  color text not null default '#34d399',
  archived boolean not null default false,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.categories (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.profiles(id) on delete cascade,
  name text not null check (char_length(name) between 1 and 80),
  type text not null check (type in ('income','expense')),
  icon text not null default '•',
  color text not null default '#64748b',
  budget numeric(14,2) not null default 0 check (budget >= 0),
  archived boolean not null default false,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique(user_id, type, name)
);

create table if not exists public.transactions (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.profiles(id) on delete cascade,
  account_id uuid not null references public.accounts(id) on delete restrict,
  category_id uuid not null references public.categories(id) on delete restrict,
  type text not null check (type in ('income','expense')),
  description text not null check (char_length(description) between 1 and 160),
  amount numeric(14,2) not null check (amount > 0),
  transaction_date date not null default current_date,
  status text not null default 'paid' check (status in ('paid','pending')),
  recurring boolean not null default false,
  recurrence_interval text check (recurrence_interval is null or recurrence_interval in ('weekly','monthly','yearly')),
  notes text check (notes is null or char_length(notes) <= 2000),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.goals (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.profiles(id) on delete cascade,
  name text not null check (char_length(name) between 1 and 100),
  icon text not null default '◎',
  target_amount numeric(14,2) not null check (target_amount > 0),
  current_amount numeric(14,2) not null default 0 check (current_amount >= 0),
  due_date date,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.subscriptions (
  user_id uuid primary key references public.profiles(id) on delete cascade,
  stripe_customer_id text unique,
  stripe_subscription_id text unique,
  stripe_price_id text,
  plan text check (plan is null or plan in ('essential','pro')),
  billing_cycle text check (billing_cycle is null or billing_cycle in ('monthly','annual')),
  status text not null default 'none',
  current_period_end timestamptz,
  cancel_at_period_end boolean not null default false,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.webhook_events (
  id text primary key,
  event_type text not null,
  processed_at timestamptz not null default now()
);

create index if not exists idx_accounts_user on public.accounts(user_id);
create index if not exists idx_categories_user_type on public.categories(user_id, type);
create index if not exists idx_transactions_user_date on public.transactions(user_id, transaction_date desc);
create index if not exists idx_transactions_account on public.transactions(account_id);
create index if not exists idx_transactions_category on public.transactions(category_id);
create index if not exists idx_goals_user on public.goals(user_id);

-- updated_at helper
create or replace function public.touch_updated_at()
returns trigger
language plpgsql
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

drop trigger if exists profiles_touch_updated_at on public.profiles;
create trigger profiles_touch_updated_at before update on public.profiles for each row execute function public.touch_updated_at();
drop trigger if exists accounts_touch_updated_at on public.accounts;
create trigger accounts_touch_updated_at before update on public.accounts for each row execute function public.touch_updated_at();
drop trigger if exists categories_touch_updated_at on public.categories;
create trigger categories_touch_updated_at before update on public.categories for each row execute function public.touch_updated_at();
drop trigger if exists transactions_touch_updated_at on public.transactions;
create trigger transactions_touch_updated_at before update on public.transactions for each row execute function public.touch_updated_at();
drop trigger if exists goals_touch_updated_at on public.goals;
create trigger goals_touch_updated_at before update on public.goals for each row execute function public.touch_updated_at();
drop trigger if exists subscriptions_touch_updated_at on public.subscriptions;
create trigger subscriptions_touch_updated_at before update on public.subscriptions for each row execute function public.touch_updated_at();

-- Create a profile automatically after Auth signup.
create or replace function public.handle_new_user()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
declare
  requested_plan text;
  accepted_at timestamptz;
begin
  requested_plan := lower(coalesce(new.raw_user_meta_data->>'selected_plan', 'pro'));
  if requested_plan not in ('essential','pro') then requested_plan := 'pro'; end if;

  begin
    accepted_at := nullif(new.raw_user_meta_data->>'terms_accepted_at','')::timestamptz;
  exception when others then
    accepted_at := null;
  end;

  insert into public.profiles (
    id, full_name, workspace_name, plan, terms_accepted_at, terms_version
  ) values (
    new.id,
    coalesce(new.raw_user_meta_data->>'full_name',''),
    coalesce(nullif(new.raw_user_meta_data->>'workspace_name',''),'Meu espaço'),
    requested_plan,
    accepted_at,
    nullif(new.raw_user_meta_data->>'terms_version','')
  ) on conflict (id) do nothing;

  return new;
end;
$$;

drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
after insert on auth.users
for each row execute function public.handle_new_user();

-- Returns the plan that can currently write financial data.
-- Trial users receive Pro capabilities for seven days.
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
  if auth.uid() is not null and auth.uid() <> p_user and auth.role() <> 'service_role' then
    return 'none';
  end if;

  select * into p from public.profiles where id = p_user;
  if not found then return 'none'; end if;

  if p.subscription_status = 'active' then return p.plan; end if;
  if p.subscription_status = 'trialing' and p.trial_ends_at > now() then return 'pro'; end if;
  return 'none';
end;
$$;

revoke all on function public.current_entitlement(uuid) from public;
grant execute on function public.current_entitlement(uuid) to authenticated, service_role;

-- Prevent writes after trial/subscription expiry and enforce paid-plan limits server-side.
create or replace function public.enforce_financial_write()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
declare
  entitlement text;
  target_user uuid;
  account_count integer;
begin
  target_user := new.user_id;
  entitlement := public.current_entitlement(target_user);

  if entitlement = 'none' then
    raise exception 'SUBSCRIPTION_REQUIRED' using errcode = 'P0001';
  end if;

  if tg_table_name = 'accounts' and tg_op = 'INSERT' and entitlement = 'essential' then
    select count(*) into account_count from public.accounts where user_id = target_user and archived = false;
    if account_count >= 3 then
      raise exception 'PLAN_LIMIT_ACCOUNTS' using errcode = 'P0001';
    end if;
  end if;

  if tg_table_name = 'goals' and entitlement = 'essential' then
    raise exception 'PLAN_REQUIRED_PRO' using errcode = 'P0001';
  end if;

  if tg_table_name = 'transactions' and coalesce(new.recurring,false) and entitlement = 'essential' then
    raise exception 'PLAN_REQUIRED_PRO' using errcode = 'P0001';
  end if;

  return new;
end;
$$;

revoke all on function public.enforce_financial_write() from public;

drop trigger if exists accounts_require_access on public.accounts;
create trigger accounts_require_access before insert or update on public.accounts for each row execute function public.enforce_financial_write();
drop trigger if exists categories_require_access on public.categories;
create trigger categories_require_access before insert or update on public.categories for each row execute function public.enforce_financial_write();
drop trigger if exists transactions_require_access on public.transactions;
create trigger transactions_require_access before insert or update on public.transactions for each row execute function public.enforce_financial_write();
drop trigger if exists goals_require_access on public.goals;
create trigger goals_require_access before insert or update on public.goals for each row execute function public.enforce_financial_write();

-- Row Level Security
alter table public.profiles enable row level security;
alter table public.accounts enable row level security;
alter table public.categories enable row level security;
alter table public.transactions enable row level security;
alter table public.goals enable row level security;
alter table public.subscriptions enable row level security;
alter table public.webhook_events enable row level security;

-- Remove broad privileges first.
revoke all on public.profiles from anon, authenticated;
revoke all on public.accounts from anon, authenticated;
revoke all on public.categories from anon, authenticated;
revoke all on public.transactions from anon, authenticated;
revoke all on public.goals from anon, authenticated;
revoke all on public.subscriptions from anon, authenticated;
revoke all on public.webhook_events from anon, authenticated;

-- Authenticated users can read their profile but cannot modify billing/plan fields.
grant select on public.profiles to authenticated;
grant update(full_name, workspace_name, workspace_type, currency, timezone, onboarded, terms_accepted_at, terms_version) on public.profiles to authenticated;

grant select, insert, update, delete on public.accounts to authenticated;
grant select, insert, update, delete on public.categories to authenticated;
grant select, insert, update, delete on public.transactions to authenticated;
grant select, insert, update, delete on public.goals to authenticated;
grant select on public.subscriptions to authenticated;

drop policy if exists profiles_select_own on public.profiles;
create policy profiles_select_own on public.profiles for select to authenticated using ((select auth.uid()) = id);
drop policy if exists profiles_update_own on public.profiles;
create policy profiles_update_own on public.profiles for update to authenticated using ((select auth.uid()) = id) with check ((select auth.uid()) = id);

drop policy if exists accounts_own on public.accounts;
create policy accounts_own on public.accounts for all to authenticated using ((select auth.uid()) = user_id) with check ((select auth.uid()) = user_id);
drop policy if exists categories_own on public.categories;
create policy categories_own on public.categories for all to authenticated using ((select auth.uid()) = user_id) with check ((select auth.uid()) = user_id);
drop policy if exists transactions_own on public.transactions;
create policy transactions_own on public.transactions for all to authenticated using ((select auth.uid()) = user_id) with check ((select auth.uid()) = user_id);
drop policy if exists goals_own on public.goals;
create policy goals_own on public.goals for all to authenticated using ((select auth.uid()) = user_id) with check ((select auth.uid()) = user_id);
drop policy if exists subscriptions_select_own on public.subscriptions;
create policy subscriptions_select_own on public.subscriptions for select to authenticated using ((select auth.uid()) = user_id);

-- Keep internal billing/event tables unreachable to browser roles except subscription reads above.
revoke all on public.webhook_events from anon, authenticated;

-- The service role/secret key is used only by server-side Functions and bypasses RLS.
