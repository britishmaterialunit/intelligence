-- ============================================================
-- BMU — SIGN-UPS
-- Paste this whole file into Supabase → SQL Editor → Run. It is safe to
-- run twice: every statement checks before it creates.
--
-- One table, bmu_signups, holding everything anybody hands the website:
--   kind = 'join'       an address from the Join field on the home page
--   kind = 'early'      an address from Early Access
--   kind = 'wholesale'  a trade account registration from /repository
--   kind = 'request'    an archive sourcing request
--
-- WHY THE POLICIES BELOW MATTER MORE THAN ANYTHING ELSE IN THIS FILE
--
-- The key the website carries is the publishable one. It is public by
-- design — it is in files-config.js, which anybody can open — and it is
-- the key these inserts are made with. So the policies are the whole of
-- the security, and there is exactly one rule to hold on to:
--
--   anon may INSERT. anon may NOT SELECT.
--
-- An insert-only table is a letterbox: anyone may post through it and
-- nobody may reach back in. If SELECT were open to anon as well, then the
-- public key — which is printed on the website — would let anybody
-- download every address that has ever been given to it. That is the whole
-- mailing list, and it is the one mistake this file exists to prevent.
--
-- Reading is left to the signed-in admins the files page already knows
-- about (bmu_admins), and to the service_role key, which lives in the
-- Supabase dashboard and must never be put in a page.
-- ============================================================

create table if not exists public.bmu_signups (
  id         uuid primary key default gen_random_uuid(),
  -- 'join' | 'early' | 'wholesale' | 'request'
  kind       text not null,
  email      text not null,
  -- promoted out of details because they are what you would sort by
  name       text,
  company    text,
  -- everything else the form carried, as it was given
  details    jsonb not null default '{}'::jsonb,
  -- which page it came from, for when a form moves
  source     text,
  created_at timestamptz not null default now()
);

create index if not exists bmu_signups_kind_created
  on public.bmu_signups (kind, created_at desc);
create index if not exists bmu_signups_email
  on public.bmu_signups (lower(email));

alter table public.bmu_signups enable row level security;

-- Safe to re-run: drop before create.
drop policy if exists "anyone may sign up"      on public.bmu_signups;
drop policy if exists "only admins may read"    on public.bmu_signups;
drop policy if exists "only admins may delete"  on public.bmu_signups;

-- The letterbox. with check, not using: it governs the row being written
-- and grants nothing at all on rows already there.
create policy "anyone may sign up" on public.bmu_signups
  for insert to anon, authenticated
  with check (
    kind in ('join', 'early', 'wholesale', 'request')
    and length(email) between 3 and 320
    and email like '%@%'
    -- a cap, so a script cannot push a megabyte of anything into a row
    and length(coalesce(name, '')) <= 200
    and length(coalesce(company, '')) <= 200
    and pg_column_size(details) <= 8192
  );

-- Reading is for the admins the files page already knows, and nobody else.
-- There is deliberately no policy granting anon SELECT; without one, the
-- public key reads nothing.
create policy "only admins may read" on public.bmu_signups
  for select to authenticated
  using (exists (select 1 from public.bmu_admins a where a.user_id = auth.uid()));

create policy "only admins may delete" on public.bmu_signups
  for delete to authenticated
  using (exists (select 1 from public.bmu_admins a where a.user_id = auth.uid()));

-- ============================================================
-- CHECK IT IS SHUT
-- After running the above, in the SQL editor:
--
--   set role anon;
--   select * from public.bmu_signups;      -- must return 0 rows, never an error
--   reset role;
--
-- 0 rows is the pass. If it ever returns the table's contents, a SELECT
-- policy has been added for anon and the list is public — take it off.
-- ============================================================
