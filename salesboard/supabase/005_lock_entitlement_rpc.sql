-- SalesBoard Finance v3 - keep entitlement helper internal
-- Run after 004_three_day_trial.sql.

revoke execute on function public.current_entitlement(uuid) from authenticated, anon, public;
grant execute on function public.current_entitlement(uuid) to service_role;
