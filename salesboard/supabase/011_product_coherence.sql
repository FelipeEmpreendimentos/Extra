-- SalesBoard Finance — product coherence
-- Links goals to real transactions, removes meaningless income budgets,
-- keeps recurrence semantics consistent, and makes onboarding choices useful.

alter table public.transactions
  add column if not exists goal_id uuid references public.goals(id) on delete set null;

create index if not exists idx_transactions_goal
  on public.transactions(goal_id)
  where goal_id is not null;

-- A monthly spending limit only makes sense for expense categories.
update public.categories
set budget = 0
where type = 'income' and budget <> 0;

alter table public.categories
  drop constraint if exists categories_income_budget_zero;
alter table public.categories
  add constraint categories_income_budget_zero
  check (type = 'expense' or budget = 0);

-- Validate account, category and optional goal ownership in one place.
create or replace function public.validate_transaction_references()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
declare
  account_owner uuid;
  category_owner uuid;
  category_kind text;
  goal_owner uuid;
begin
  select user_id into account_owner
  from public.accounts
  where id = new.account_id and archived = false;

  if account_owner is null or account_owner <> new.user_id then
    raise exception 'INVALID_ACCOUNT_REFERENCE' using errcode = 'P0001';
  end if;

  select user_id, type into category_owner, category_kind
  from public.categories
  where id = new.category_id and archived = false;

  if category_owner is null or category_owner <> new.user_id then
    raise exception 'INVALID_CATEGORY_REFERENCE' using errcode = 'P0001';
  end if;

  if category_kind <> new.type then
    raise exception 'CATEGORY_TYPE_MISMATCH' using errcode = 'P0001';
  end if;

  if new.goal_id is not null then
    select user_id into goal_owner
    from public.goals
    where id = new.goal_id;

    if goal_owner is null or goal_owner <> new.user_id then
      raise exception 'INVALID_GOAL_REFERENCE' using errcode = 'P0001';
    end if;

    if public.current_entitlement(new.user_id) <> 'pro' then
      raise exception 'PLAN_REQUIRED_PRO' using errcode = 'P0001';
    end if;
  end if;

  return new;
end;
$$;

revoke all on function public.validate_transaction_references() from public, anon, authenticated;

-- Generated recurring occurrences keep the same goal link as their source.
create or replace function public.process_salesboard_recurring_transactions()
returns integer
language plpgsql
security definer
set search_path = public
as $$
declare
  src record;
  due_date date;
  step_no integer;
  inserted_count integer := 0;
  row_count integer;
begin
  for src in
    select t.*
    from public.transactions t
    join public.profiles p on p.id = t.user_id
    where t.recurring = true
      and t.recurrence_source_id is null
      and t.recurrence_interval in ('weekly','monthly','yearly')
      and (
        (p.subscription_status = 'active' and p.plan = 'pro')
        or (p.subscription_status = 'trialing' and p.trial_ends_at > now() and p.plan = 'pro')
      )
  loop
    step_no := 1;
    loop
      if src.recurrence_interval = 'weekly' then
        due_date := src.transaction_date + (step_no * 7);
      elsif src.recurrence_interval = 'monthly' then
        due_date := (src.transaction_date + make_interval(months => step_no))::date;
      else
        due_date := (src.transaction_date + make_interval(years => step_no))::date;
      end if;

      exit when due_date > current_date;
      exit when step_no > 520;

      insert into public.transactions (
        user_id, account_id, category_id, goal_id, type, description, amount,
        transaction_date, status, recurring, recurrence_interval,
        recurrence_source_id, notes
      ) values (
        src.user_id, src.account_id, src.category_id, src.goal_id, src.type, src.description, src.amount,
        due_date, 'pending', false, null,
        src.id,
        case
          when src.notes is null or btrim(src.notes) = '' then 'Gerado automaticamente a partir de uma recorrência.'
          else src.notes || E'\nGerado automaticamente a partir de uma recorrência.'
        end
      )
      on conflict (recurrence_source_id, transaction_date)
      where recurrence_source_id is not null
      do nothing;

      get diagnostics row_count = row_count;
      inserted_count := inserted_count + row_count;
      step_no := step_no + 1;
    end loop;
  end loop;

  return inserted_count;
end;
$$;

revoke all on function public.process_salesboard_recurring_transactions() from public, anon, authenticated;

-- The onboarding type now defines a useful initial category template.
-- Suggested monetary budgets were removed: a generic R$ value is not a safe default.
create or replace function public.complete_salesboard_onboarding(
  p_workspace_type text,
  p_workspace_name text,
  p_account_name text,
  p_account_type text,
  p_opening_balance numeric,
  p_create_budgets boolean default false,
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
begin
  if uid is null then
    raise exception 'AUTH_REQUIRED' using errcode = 'P0001';
  end if;

  select * into prof from public.profiles where id = uid for update;
  if not found then raise exception 'PROFILE_NOT_FOUND' using errcode = 'P0001'; end if;
  if prof.onboarded then return jsonb_build_object('ok', true, 'already_completed', true); end if;
  if public.current_entitlement(uid) = 'none' then raise exception 'SUBSCRIPTION_REQUIRED' using errcode = 'P0001'; end if;
  if normalized_workspace_type not in ('personal','freelancer','business') then raise exception 'INVALID_WORKSPACE_TYPE' using errcode = 'P0001'; end if;
  if normalized_account_type not in ('bank','cash','wallet','investment') then raise exception 'INVALID_ACCOUNT_TYPE' using errcode = 'P0001'; end if;
  if char_length(v_workspace_name) > 80 or char_length(v_account_name) > 80 then raise exception 'INVALID_NAME_LENGTH' using errcode = 'P0001'; end if;
  if v_opening_balance < -999999999.99 or v_opening_balance > 999999999.99 then raise exception 'INVALID_OPENING_BALANCE' using errcode = 'P0001'; end if;
  if prof.terms_accepted_at is null and not coalesce(p_accept_terms, false) then raise exception 'TERMS_REQUIRED' using errcode = 'P0001'; end if;

  insert into public.accounts (user_id, name, type, opening_balance, icon, color)
  values (uid, v_account_name, normalized_account_type, v_opening_balance, '▣', '#34d399');

  if normalized_workspace_type = 'personal' then
    insert into public.categories (user_id, name, type, icon, color, budget) values
      (uid, 'Moradia', 'expense', '🏠', '#8b5cf6', 0),
      (uid, 'Alimentação', 'expense', '🛒', '#34d399', 0),
      (uid, 'Transporte', 'expense', '🚗', '#4f7de8', 0),
      (uid, 'Saúde', 'expense', '❤️', '#ec4899', 0),
      (uid, 'Lazer', 'expense', '🎮', '#e65b67', 0),
      (uid, 'Serviços', 'expense', '💡', '#f59e0b', 0),
      (uid, 'Salário', 'income', '💼', '#34d399', 0),
      (uid, 'Renda extra', 'income', '💰', '#4f7de8', 0);
  elsif normalized_workspace_type = 'freelancer' then
    insert into public.categories (user_id, name, type, icon, color, budget) values
      (uid, 'Ferramentas', 'expense', '🧰', '#8b5cf6', 0),
      (uid, 'Impostos', 'expense', '🧾', '#e65b67', 0),
      (uid, 'Marketing', 'expense', '📣', '#4f7de8', 0),
      (uid, 'Transporte', 'expense', '🚗', '#f59e0b', 0),
      (uid, 'Serviços', 'expense', '💡', '#34d399', 0),
      (uid, 'Outras despesas', 'expense', '•', '#64748b', 0),
      (uid, 'Clientes', 'income', '💼', '#34d399', 0),
      (uid, 'Outras receitas', 'income', '💰', '#4f7de8', 0);
  else
    insert into public.categories (user_id, name, type, icon, color, budget) values
      (uid, 'Fornecedores', 'expense', '📦', '#8b5cf6', 0),
      (uid, 'Operação', 'expense', '⚙️', '#34d399', 0),
      (uid, 'Marketing', 'expense', '📣', '#4f7de8', 0),
      (uid, 'Impostos', 'expense', '🧾', '#e65b67', 0),
      (uid, 'Serviços', 'expense', '💡', '#f59e0b', 0),
      (uid, 'Outras despesas', 'expense', '•', '#64748b', 0),
      (uid, 'Vendas e serviços', 'income', '💼', '#34d399', 0),
      (uid, 'Outras receitas', 'income', '💰', '#4f7de8', 0);
  end if;

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
