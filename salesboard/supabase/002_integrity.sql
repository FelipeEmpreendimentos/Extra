-- SalesBoard Finance v3 - Integrity hardening
-- Run after schema.sql.

-- Prevent a transaction from pointing to an account/category owned by another user
-- and keep the category type consistent with the transaction type.
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
begin
  select user_id into account_owner from public.accounts where id = new.account_id and archived = false;
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

  return new;
end;
$$;

revoke all on function public.validate_transaction_references() from public;

drop trigger if exists transactions_validate_references on public.transactions;
create trigger transactions_validate_references
before insert or update on public.transactions
for each row execute function public.validate_transaction_references();

-- Stop ownership from being reassigned after creation. Ownership should only change
-- through explicit server-side migrations, never through a browser update.
create or replace function public.prevent_owner_change()
returns trigger
language plpgsql
as $$
begin
  if new.user_id <> old.user_id then
    raise exception 'OWNER_CHANGE_NOT_ALLOWED' using errcode = 'P0001';
  end if;
  return new;
end;
$$;

revoke all on function public.prevent_owner_change() from public;

drop trigger if exists accounts_prevent_owner_change on public.accounts;
create trigger accounts_prevent_owner_change before update on public.accounts for each row execute function public.prevent_owner_change();
drop trigger if exists categories_prevent_owner_change on public.categories;
create trigger categories_prevent_owner_change before update on public.categories for each row execute function public.prevent_owner_change();
drop trigger if exists transactions_prevent_owner_change on public.transactions;
create trigger transactions_prevent_owner_change before update on public.transactions for each row execute function public.prevent_owner_change();
drop trigger if exists goals_prevent_owner_change on public.goals;
create trigger goals_prevent_owner_change before update on public.goals for each row execute function public.prevent_owner_change();

-- Sensible data-level bounds to protect against accidental or malicious huge values.
alter table public.accounts drop constraint if exists accounts_opening_balance_reasonable;
alter table public.accounts add constraint accounts_opening_balance_reasonable check (opening_balance between -999999999.99 and 999999999.99);

alter table public.transactions drop constraint if exists transactions_amount_reasonable;
alter table public.transactions add constraint transactions_amount_reasonable check (amount > 0 and amount <= 999999999.99);

alter table public.goals drop constraint if exists goals_target_reasonable;
alter table public.goals add constraint goals_target_reasonable check (target_amount > 0 and target_amount <= 999999999.99);

alter table public.goals drop constraint if exists goals_current_reasonable;
alter table public.goals add constraint goals_current_reasonable check (current_amount >= 0 and current_amount <= 999999999.99);
