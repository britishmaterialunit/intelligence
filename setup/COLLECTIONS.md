# Collections — switching it on

`/collections` is where you build private selections from the archive and
give people a login to review them. Logins and collections are stored in
**Supabase** (open source, free tier). Nothing on the website changes until
the two values in step 5 are filled in — until then the page says
"Collections are not switched on yet."

Takes about ten minutes, once.

## 1. Make the project
1. Sign up at **supabase.com** and create a new project.
   Region: *West EU (London)*. Keep the database password somewhere safe —
   you won't need it for this, but Supabase will ask for it.

## 2. Build the tables
1. In the project: **SQL Editor → New query**.
2. Paste the whole of `setup/collections.sql` and press **Run**.
   It should finish with "Success. No rows returned".

## 3. Set how logins work
**Authentication → Sign In / Providers → Email**
- **Confirm email: OFF.** Logins you create work immediately, without the
  person having to click a confirmation email first.
- **Allow new users to sign up: ON** if you want to create logins from the
  website's *Create a login* button. (Anyone who finds the page could then
  make themselves an account, but they would see nothing: a login only ever
  shows collections addressed to its own email.)
  Turn it **OFF** if you'd rather create every login in the dashboard
  (step 6).

**Authentication → URL Configuration**
- Site URL: `https://britishmaterialunit.com`

## 4. Make yourself the admin
1. **Authentication → Users → Add user → Create new user.** Your email, a
   password, and tick **Auto Confirm User**.
2. **SQL Editor**, run this with your email in it:
   ```sql
   insert into public.bmu_admins (user_id)
     select id from auth.users where lower(email) = lower('you@example.com')
     on conflict do nothing;
   ```

## 5. Connect the website
**Project Settings → API** (or **API Keys**). Copy:
- the **Project URL** (`https://….supabase.co`)
- the **anon** / **publishable** key

Put them in `collections-config.js` in the site repo — it's a small file on
its own, safe to edit on GitHub — then publish.
**Never** use the `service_role` / secret key; it would give anyone full
access to the database.

## 6. Using it
Sign in at **britishmaterialunit.com/collections** (or the person icon in
the archive's header).

- **New collection** — a title, who it's for (their email), an optional
  note, and the garments. Search the archive and tick; the number on each
  tile is its place in the order.
- **Create a login** — their email and a password (or *Make one up*). You
  get a short message to paste into an email to them.
- **Copy link to send** on a collection — a link that opens straight onto
  it once they've signed in.
- When they **Send reply** (the garments they want and a note) it's saved,
  the collection shows *Replied*, and it's emailed to
  hello@britishmaterialunit.com the same way Join requests are.

## Managing people's logins
Everything about accounts is in **Authentication → Users**:
- **See everyone** who has a login.
- **Remove someone's access:** delete their user. Their collections stay,
  and nobody else can open them.
- **Change a password:** delete the user and create them again with the
  same email and a new password. Collections and replies follow the email,
  so nothing is lost.
- **Another admin:** create their login, then run the step 4 SQL with their
  email.

A collection is addressed by email, so you can build one before the person
has a login — it's waiting for them the first time they sign in.

## Worth knowing
- Supabase **pauses free projects after about a week with no use**. If
  sign-in suddenly stops working, open the project in the dashboard and
  press *Restore*. Upgrading to their paid tier stops the pausing.
- The website only ever holds the public key. What stops one reviewer
  seeing another's collection is the row-level security in
  `setup/collections.sql`, enforced inside the database.
