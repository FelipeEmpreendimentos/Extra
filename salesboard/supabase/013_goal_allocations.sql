-- SalesBoard Finance — partial goal allocation
-- An income transaction may allocate all or part of its value to one goal.

alter table public.transactions
  add column if not exists goal_amount numeric(14,2);

update public.transactions
set goal_amount = amount
where goal_id is not null and goal_amount is null;

alter table public.transactions
  drop constraint if exists transactions_goal_amount_valid;
alter table public.transactions
  add constraint transactions_goal_amount_valid
  check (
    goal_amount is null
    or (type = 'income' and goal_amount > 0 and goal_amount <= amount)
  );

alter table public.transactions
  drop constraint if exists transactions_goal_link_consistent;
alter table public.transactions
  add constraint transactions_goal_link_consistent
  check (goal_id is not null or goal_amount is null);

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

  if new.goal_id is null then
    new.goal_amount := null;
  else
    if new.type <> 'income' then
      raise exception 'GOAL_REQUIRES_INCOME' using errcode = 'P0001';
    end if;

    select user_id into goal_owner
    from public.goals
    where id = new.goal_id;

    if goal_owner is null or goal_owner <> new.user_id then
      raise exception 'INVALID_GOAL_REFERENCE' using errcode = 'P0001';
    end if;

    if public.current_entitlement(new.user_id) <> 'pro' then
      raise exception 'PLAN_REQUIRED_PRO' using errcode = 'P0001';
    end if;

    new.goal_amount := coalesce(new.goal_amount, new.amount);
    if new.goal_amount <= 0 or new.goal_amount > new.amount then
      raise exception 'INVALID_GOAL_AMOUNT' using errcode = 'P0001';
    end if;
  end if;

  return new;
end;
$$;

revoke all on function public.validate_transaction_references() from public, anon, authenticated;

-- Generated recurring transactions keep the same allocation rule as the source.
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
        user_id, account_id, category_id, goal_id, goal_amount, type, description, amount,
        transaction_date, status, recurring, recurrence_interval,
        recurrence_source_id, notes
      ) values (
        src.user_id, src.account_id, src.category_id, src.goal_id, src.goal_amount, src.type, src.description, src.amount,
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
