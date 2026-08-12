-- Hotfix: Supabase installs pgcrypto in the `extensions` schema.
-- Security-definer functions keep search_path restricted to public, so digest must be schema-qualified.

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
  return not exists (
    select 1 from public.trial_claims where email_fingerprint = fingerprint
  );
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

  if result_profile.subscription_status = 'active' then
    return result_profile;
  end if;

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
