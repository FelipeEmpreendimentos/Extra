-- Selectable one-time 3-day trial.
-- Account creation no longer starts the trial; the user explicitly chooses Essential or Pro.

alter table public.trial_claims
  add column if not exists claimed_plan text check (claimed_plan is null or claimed_plan in ('essential','pro'));

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
  exception when others then accepted_at := null;
  end;

  insert into public.profiles (
    id, full_name, workspace_name, plan, subscription_status, trial_ends_at, terms_accepted_at, terms_version
  ) values (
    new.id,
    coalesce(new.raw_user_meta_data->>'full_name',''),
    coalesce(nullif(new.raw_user_meta_data->>'workspace_name',''),'Meu espaço'),
    requested_plan,
    'none',
    new.created_at,
    accepted_at,
    nullif(new.raw_user_meta_data->>'terms_version','')
  ) on conflict (id) do nothing;

  return new;
end;
$$;

revoke all on function public.handle_new_user() from public, anon, authenticated;

create or replace function public.salesboard_trial_eligible()
returns boolean
language plpgsql
stable
security definer
set search_path = public
as $$
declare
  user_email text;
  fingerprint text;
begin
  if auth.uid() is null then return false; end if;
  select email into user_email from auth.users where id = auth.uid();
  if user_email is null or trim(user_email) = '' then return false; end if;
  fingerprint := encode(extensions.digest(lower(trim(user_email)), 'sha256'), 'hex');
  return not exists (select 1 from public.trial_claims where email_fingerprint = fingerprint);
end;
$$;

revoke all on function public.salesboard_trial_eligible() from public, anon;
grant execute on function public.salesboard_trial_eligible() to authenticated;

create or replace function public.start_salesboard_trial(p_plan text)
returns public.profiles
language plpgsql
security definer
set search_path = public
as $$
declare
  uid uuid := auth.uid();
  user_email text;
  fingerprint text;
  normalized_plan text := lower(coalesce(p_plan,''));
  claimed text;
  result_profile public.profiles%rowtype;
begin
  if uid is null then raise exception 'AUTH_REQUIRED' using errcode = 'P0001'; end if;
  if normalized_plan not in ('essential','pro') then raise exception 'INVALID_TRIAL_PLAN' using errcode = 'P0001'; end if;

  select email into user_email from auth.users where id = uid;
  if user_email is null or trim(user_email) = '' then raise exception 'EMAIL_REQUIRED' using errcode = 'P0001'; end if;

  select * into result_profile from public.profiles where id = uid for update;
  if not found then raise exception 'PROFILE_NOT_FOUND' using errcode = 'P0001'; end if;
  if result_profile.subscription_status = 'active' then return result_profile; end if;

  if result_profile.subscription_status = 'trialing' and result_profile.trial_ends_at > now() then
    if result_profile.plan <> normalized_plan then raise exception 'TRIAL_ALREADY_STARTED' using errcode = 'P0001'; end if;
    return result_profile;
  end if;

  fingerprint := encode(extensions.digest(lower(trim(user_email)), 'sha256'), 'hex');
  insert into public.trial_claims (email_fingerprint, first_claimed_at, claimed_plan)
  values (fingerprint, now(), normalized_plan)
  on conflict (email_fingerprint) do nothing
  returning email_fingerprint into claimed;

  if claimed is null then raise exception 'TRIAL_ALREADY_USED' using errcode = 'P0001'; end if;

  update public.profiles
  set plan = normalized_plan,
      subscription_status = 'trialing',
      trial_ends_at = now() + interval '3 days',
      updated_at = now()
  where id = uid
  returning * into result_profile;

  return result_profile;
end;
$$;

revoke all on function public.start_salesboard_trial(text) from public, anon;
grant execute on function public.start_salesboard_trial(text) to authenticated;

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
  if auth.uid() is not null and auth.uid() <> p_user and auth.role() <> 'service_role' then return 'none'; end if;
  select * into p from public.profiles where id = p_user;
  if not found then return 'none'; end if;
  if p.subscription_status = 'active' then return p.plan; end if;
  if p.subscription_status = 'trialing' and p.trial_ends_at > now() then return p.plan; end if;
  return 'none';
end;
$$;

revoke all on function public.current_entitlement(uuid) from public, anon, authenticated;
