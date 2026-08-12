-- Complete the three-step onboarding atomically.
-- Prevents partial account/category creation and avoids browser-native validation dead ends.

create or replace function public.complete_salesboard_onboarding(
  p_workspace_type text,
  p_workspace_name text,
  p_account_name text,
  p_account_type text,
  p_opening_balance numeric,
  p_create_budgets boolean default true,
  p_accept_terms boolean default false
)
returns jsonb
language plpgsql
security definer
set search_path = public
as $$
declare
  uid uuid := auth.uid();
  prof public.profiles%rowtype;
  normalized_workspace_type text := lower(coalesce(trim(p_workspace_type), ''));
  normalized_account_type text := lower(coalesce(trim(p_account_type), ''));
  v_workspace_name text := coalesce(nullif(trim(p_workspace_name), ''), 'Meu espaço');
  v_account_name text := coalesce(nullif(trim(p_account_name), ''), 'Conta principal');
  v_opening_balance numeric := coalesce(p_opening_balance, 0);
  use_budgets boolean := coalesce(p_create_budgets, true);
begin
  if uid is null then
    raise exception 'AUTH_REQUIRED' using errcode = 'P0001';
  end if;

  select * into prof
  from public.profiles
  where id = uid
  for update;

  if not found then
    raise exception 'PROFILE_NOT_FOUND' using errcode = 'P0001';
  end if;

  if prof.onboarded then
    return jsonb_build_object('ok', true, 'already_completed', true);
  end if;

  if public.current_entitlement(uid) = 'none' then
    raise exception 'SUBSCRIPTION_REQUIRED' using errcode = 'P0001';
  end if;

  if normalized_workspace_type not in ('personal','freelancer','business') then
    raise exception 'INVALID_WORKSPACE_TYPE' using errcode = 'P0001';
  end if;

  if normalized_account_type not in ('bank','cash','wallet','investment') then
    raise exception 'INVALID_ACCOUNT_TYPE' using errcode = 'P0001';
  end if;

  if char_length(v_workspace_name) > 80 or char_length(v_account_name) > 80 then
    raise exception 'INVALID_NAME_LENGTH' using errcode = 'P0001';
  end if;

  if v_opening_balance < -999999999.99 or v_opening_balance > 999999999.99 then
    raise exception 'INVALID_OPENING_BALANCE' using errcode = 'P0001';
  end if;

  if prof.terms_accepted_at is null and not coalesce(p_accept_terms, false) then
    raise exception 'TERMS_REQUIRED' using errcode = 'P0001';
  end if;

  insert into public.accounts (user_id, name, type, opening_balance, icon, color)
  values (uid, v_account_name, normalized_account_type, v_opening_balance, '▣', '#34d399');

  insert into public.categories (user_id, name, type, icon, color, budget) values
    (uid, 'Moradia', 'expense', '🏠', '#8b5cf6', case when use_budgets then 1600 else 0 end),
    (uid, 'Alimentação', 'expense', '🛒', '#34d399', case when use_budgets then 1100 else 0 end),
    (uid, 'Transporte', 'expense', '🚗', '#4f7de8', case when use_budgets then 700 else 0 end),
    (uid, 'Serviços', 'expense', '💡', '#f59e0b', case when use_budgets then 500 else 0 end),
    (uid, 'Saúde', 'expense', '❤️', '#ec4899', case when use_budgets then 450 else 0 end),
    (uid, 'Lazer', 'expense', '🎮', '#e65b67', case when use_budgets then 450 else 0 end),
    (uid, 'Trabalho', 'income', '💼', '#34d399', 0),
    (uid, 'Outras entradas', 'income', '💰', '#4f7de8', 0);

  update public.profiles as p
  set workspace_type = normalized_workspace_type,
      workspace_name = v_workspace_name,
      onboarded = true,
      terms_accepted_at = coalesce(p.terms_accepted_at, case when p_accept_terms then now() else null end),
      terms_version = coalesce(p.terms_version, case when p_accept_terms then '2026-08-12' else null end),
      updated_at = now()
  where p.id = uid;

  return jsonb_build_object('ok', true, 'already_completed', false);
end;
$$;

revoke all on function public.complete_salesboard_onboarding(text,text,text,text,numeric,boolean,boolean) from public, anon;
grant execute on function public.complete_salesboard_onboarding(text,text,text,text,numeric,boolean,boolean) to authenticated;
