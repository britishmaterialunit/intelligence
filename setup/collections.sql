-- ============================================================
-- BMU ARCHIVE — COLLECTIONS
-- Paste this whole file into Supabase → SQL Editor → Run. It is safe to
-- run twice: every statement checks before it creates.
--
-- Three tables:
--   bmu_admins       who may build collections (you)
--   bmu_collections  a titled set of archive garments, addressed to one
--                    reviewer by email
--   bmu_responses    what the reviewer sent back: the garments they want
--                    and a note
--
-- Every row is locked by row-level security. The key the website carries
-- is public by design; these policies are what stop one reviewer reading
-- another's collection, and stop anyone but an admin writing one.
-- ============================================================

create table if not exists public.bmu_admins (
  user_id uuid primary key references auth.users(id) on delete cascade
);

create table if not exists public.bmu_collections (
  id             uuid primary key default gen_random_uuid(),
  title          text not null,
  note           text not null default '',
  reviewer_email text not null,
  -- archive garment ids, "<nation>/<garment-slug>", in the order shown
  garments       text[] not null default '{}',
  created_at     timestamptz not null default now(),
  updated_at     timestamptz not null default now()
);

create table if not exists public.bmu_responses (
  collection_id  uuid not null references public.bmu_collections(id) on delete cascade,
  reviewer_email text not null,
  picks          text[] not null default '{}',
  note           text not null default '',
  -- where the file has got to: 'opened' the moment the reviewer opens it,
  -- 'verified' once they have been through it and pressed Verify File.
  -- A file with no row at all is unopened.
  status         text not null default 'opened',
  updated_at     timestamptz not null default now(),
  primary key (collection_id, reviewer_email)
);

-- For a database built before status existed. Safe to run again.
alter table public.bmu_responses
  add column if not exists status text not null default 'opened';

alter table public.bmu_admins      enable row level security;
alter table public.bmu_collections enable row level security;
alter table public.bmu_responses   enable row level security;

-- ---------- helpers ----------
-- Security definer so the check can read bmu_admins without that table's
-- own policy getting in the way; search_path pinned so it cannot be
-- redirected.
create or replace function public.bmu_is_admin() returns boolean
language sql stable security definer set search_path = public as $$
  select exists (select 1 from public.bmu_admins where user_id = auth.uid());
$$;

create or replace function public.bmu_email() returns text
language sql stable as $$
  select lower(coalesce(auth.jwt() ->> 'email', ''));
$$;

-- ---------- policies ----------
drop policy if exists "admins see themselves"       on public.bmu_admins;
drop policy if exists "read own or all as admin"    on public.bmu_collections;
drop policy if exists "admin creates"               on public.bmu_collections;
drop policy if exists "admin edits"                 on public.bmu_collections;
drop policy if exists "admin removes"               on public.bmu_collections;
drop policy if exists "read own reply or all"       on public.bmu_responses;
drop policy if exists "reviewer replies"            on public.bmu_responses;
drop policy if exists "reviewer amends reply"       on public.bmu_responses;

-- an admin can see their own admin row, which is how the page knows
create policy "admins see themselves" on public.bmu_admins
  for select to authenticated using (user_id = auth.uid());

-- a reviewer reads only what is addressed to their email; an admin, all
create policy "read own or all as admin" on public.bmu_collections
  for select to authenticated
  using (public.bmu_is_admin() or lower(reviewer_email) = public.bmu_email());

create policy "admin creates" on public.bmu_collections
  for insert to authenticated with check (public.bmu_is_admin());
create policy "admin edits" on public.bmu_collections
  for update to authenticated using (public.bmu_is_admin()) with check (public.bmu_is_admin());
create policy "admin removes" on public.bmu_collections
  for delete to authenticated using (public.bmu_is_admin());

-- a reply is readable by the reviewer who wrote it, and by an admin
create policy "read own reply or all" on public.bmu_responses
  for select to authenticated
  using (public.bmu_is_admin() or lower(reviewer_email) = public.bmu_email());

-- and writable only by that reviewer, only on a collection sent to them
create policy "reviewer replies" on public.bmu_responses
  for insert to authenticated
  with check (
    lower(reviewer_email) = public.bmu_email()
    and exists (select 1 from public.bmu_collections c
                where c.id = collection_id
                  and lower(c.reviewer_email) = public.bmu_email())
  );
create policy "reviewer amends reply" on public.bmu_responses
  for update to authenticated
  using (lower(reviewer_email) = public.bmu_email())
  with check (
    lower(reviewer_email) = public.bmu_email()
    and exists (select 1 from public.bmu_collections c
                where c.id = collection_id
                  and lower(c.reviewer_email) = public.bmu_email())
  );

-- ============================================================
-- REFERENCE BOARDS
-- A file can carry a reference board, sent from the archive's board by an
-- admin. The board is a .zip kept in a private storage bucket; the file's
-- board_path names it. Only an admin can put one there, and only the
-- designer the file is addressed to (or an admin) can read it back.
-- ============================================================
alter table public.bmu_collections
  add column if not exists board_path text;

insert into storage.buckets (id, name, public)
  values ('bmu-boards', 'bmu-boards', false)
  on conflict (id) do nothing;

drop policy if exists "bmu boards read"    on storage.objects;
drop policy if exists "bmu boards add"     on storage.objects;
drop policy if exists "bmu boards replace" on storage.objects;
drop policy if exists "bmu boards remove"  on storage.objects;

create policy "bmu boards read" on storage.objects
  for select to authenticated
  using (
    bucket_id = 'bmu-boards'
    and (public.bmu_is_admin()
         or exists (select 1 from public.bmu_collections c
                    where c.board_path = objects.name
                      and lower(c.reviewer_email) = public.bmu_email()))
  );
create policy "bmu boards add" on storage.objects
  for insert to authenticated
  with check (bucket_id = 'bmu-boards' and public.bmu_is_admin());
create policy "bmu boards replace" on storage.objects
  for update to authenticated
  using (bucket_id = 'bmu-boards' and public.bmu_is_admin())
  with check (bucket_id = 'bmu-boards' and public.bmu_is_admin());
create policy "bmu boards remove" on storage.objects
  for delete to authenticated
  using (bucket_id = 'bmu-boards' and public.bmu_is_admin());

-- ============================================================
-- MAKE YOURSELF THE ADMIN — run once, after you have created your own
-- login (Authentication → Users → Add user). Put your email in the quotes.
-- ============================================================
-- insert into public.bmu_admins (user_id)
--   select id from auth.users where lower(email) = lower('you@example.com')
--   on conflict do nothing;
