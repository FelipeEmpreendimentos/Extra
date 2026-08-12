-- SalesBoard Finance — accounting-safe goal semantics
-- Goal progress is attributed only from realized income transactions.
-- Existing savings that predate SalesBoard remain represented by goals.current_amount.

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
  end if;

  return new;
end;
$$;

revoke all on function public.validate_transaction_references() from public, anon, authenticated;
