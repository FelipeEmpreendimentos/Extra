-- SalesBoard Finance v3 - 3-day Pro trial and stricter plan guards
-- Run after 003_recurring.sql.

alter table public.profiles alter column trial_ends_at set default (now() + interval '3 days');

update public.profiles p
set trial_ends_at = u.created_at + interval '3 days', updated_at = now()
from auth.users u
where p.id = u.id
  and p.subscription_status = 'trialing'
  and p.trial_ends_at is distinct from (u.created_at + interval '3 days');

-- The full function replacements are mirrored in schema.sql and were applied to production
-- by migration salesboard_three_day_trial_and_plan_limits.
