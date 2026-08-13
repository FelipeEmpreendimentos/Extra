-- SalesBoard Finance — archive semantics without losing financial history
-- Archived accounts/categories are hidden from new entries but remain valid historical references.

alter table public.categories
  drop constraint if exists categories_user_id_type_name_key;

create unique index if not exists categories_active_user_type_name_unique
  on public.categories (user_id, type, lower(name))
  where archived = false;

create or replace function public.validate_transaction_references()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
declare
  account_owner uuid;
  account_is_archived boolean;
  category_owner uuid;
  category_kind text;
  category_is_archived boolean;
  goal_owner uuid;
begin
  select user_id, archived into account_owner, account_is_archived
  from public.accounts
  where id = new.account_id;

  if account_owner is null or account_owner <> new.user_id then
    raise exception 'INVALID_ACCOUNT_REFERENCE' using errcode = 'P0001';
  end if;

  if account_is_archived then
    if tg_op <> 'UPDATE' or old.account_id is distinct from new.account_id then
      raise exception 'INVALID_ACCOUNT_REFERENCE' using errcode = 'P0001';
    end if;
  end if;

  select user_id, type, archived into category_owner, category_kind, category_is_archived
  from public.categories
  where id = new.category_id;

  if category_owner is null or category_owner <> new.user_id then
    raise exception 'INVALID_CATEGORY_REFERENCE' using errcode = 'P0001';
  end if;

  if category_is_archived then
    if tg_op <> 'UPDATE' or old.category_id is distinct from new.category_id then
      raise exception 'INVALID_CATEGORY_REFERENCE' using errcode = 'P0001';
    end if;
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
