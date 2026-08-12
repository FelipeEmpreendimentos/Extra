-- One free trial per normalized email, even after account deletion.
-- Stores only a SHA-256 fingerprint; no raw email or financial data is retained here.

create table if not exists public.trial_claims (
  email_fingerprint text primary key,
  first_claimed_at timestamptz not null default now()
);

alter table public.trial_claims enable row level security;
revoke all on table public.trial_claims from anon, authenticated;

-- Existing users have already consumed their one-time trial eligibility.
insert into public.trial_claims (email_fingerprint, first_claimed_at)
select encode(extensions.digest(lower(trim(email)), 'sha256'), 'hex'), min(created_at)
from auth.users
where email is not null and trim(email) <> ''
group by 1
on conflict (email_fingerprint) do nothing;

create or replace function public.handle_new_user()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
declare
  requested_plan text;
  accepted_at timestamptz;
  fingerprint text;
  claimed_fingerprint text;
  first_trial boolean := false;
begin
  requested_plan := lower(coalesce(new.raw_user_meta_data->>'selected_plan', 'pro'));
  if requested_plan not in ('essential','pro') then requested_plan := 'pro'; end if;

  begin
    accepted_at := nullif(new.raw_user_meta_data->>'terms_accepted_at','')::timestamptz;
  exception when others then
    accepted_at := null;
  end;

  if new.email is not null and trim(new.email) <> '' then
    fingerprint := encode(extensions.digest(lower(trim(new.email)), 'sha256'), 'hex');
    insert into public.trial_claims (email_fingerprint, first_claimed_at)
    values (fingerprint, new.created_at)
    on conflict (email_fingerprint) do nothing
    returning email_fingerprint into claimed_fingerprint;
    first_trial := claimed_fingerprint is not null;
  end if;

  insert into public.profiles (
    id, full_name, workspace_name, plan, subscription_status, trial_ends_at, terms_accepted_at, terms_version
  ) values (
    new.id,
    coalesce(new.raw_user_meta_data->>'full_name',''),
    coalesce(nullif(new.raw_user_meta_data->>'workspace_name',''),'Meu espaço'),
    requested_plan,
    case when first_trial then 'trialing' else 'none' end,
    case when first_trial then new.created_at + interval '3 days' else new.created_at end,
    accepted_at,
    nullif(new.raw_user_meta_data->>'terms_version','')
  ) on conflict (id) do nothing;

  return new;
end;
$$;

revoke all on function public.handle_new_user() from public, anon, authenticated;
