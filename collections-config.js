/* ============================================================
   COLLECTIONS — where the logins live

   Two values from your Supabase project: Project Settings → API.
     url      the Project URL, https://<something>.supabase.co
     anonKey  the "anon" / "publishable" key

   Both are meant to be public. What keeps one reviewer out of another's
   collection is the row-level security in setup/collections.sql, not
   secrecy of this key. NEVER put the "service_role" / secret key here.

   Left empty, /collections says it is not switched on yet and nothing
   else happens.
   ============================================================ */
window.BMU_COLLECTIONS = {
  url:     '',
  anonKey: ''
};
