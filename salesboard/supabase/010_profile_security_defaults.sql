-- Align database defaults with the explicit choose-your-trial flow and reduce public RPC surface.

alter table public.profiles alter column subscription_status set default 'none';
alter table public.profiles alter column trial_ends_at set default now();

revoke all on function public.touch_updated_at() from public, anon, authenticated;

alter table public.profiles drop constraint if exists profiles_full_name_length;
alter table public.profiles add constraint profiles_full_name_length
  check (char_length(full_name) <= 120);

alter table public.profiles drop constraint if exists profiles_workspace_name_length;
alter table public.profiles add constraint profiles_workspace_name_length
  check (char_length(workspace_name) between 1 and 80);

alter table public.profiles drop constraint if exists profiles_currency_format;
alter table public.profiles add constraint profiles_currency_format
  check (currency ~ '^[A-Z]{3}$');

alter table public.profiles drop constraint if exists profiles_workspace_type_allowed;
alter table public.profiles add constraint profiles_workspace_type_allowed
  check (workspace_type in ('personal','freelancer','business'));
