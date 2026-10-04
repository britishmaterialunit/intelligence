/* ============================================================
   BMU — SIGN-UPS, KEPT AS WELL AS SENT

   Everything anybody hands this website is emailed. That is how it has
   always worked and it stays that way: an inbox is where these are acted
   on. But an inbox is a poor record — it cannot be counted, sorted or
   exported — so each one is also written into the same Supabase project
   that holds the file and repository logins.

   The two are deliberately not tied together. The email is what the
   reader is waiting on and what the interface reports; this write happens
   beside it and is allowed to fail silently. A database that is down,
   renamed, or simply not set up yet must never be the reason somebody
   cannot join.

   THE KEY

   This uses the publishable key out of files-config.js, which is public by
   design. What stops that being a problem is on the other end: the table
   lets anon INSERT and nothing else, so the key can post a row and cannot
   read one back. See setup/signups.sql — the policies there are the whole
   of the security, not this file.

   Written against PostgREST directly rather than the Supabase SDK: one
   POST with two headers is the entire job, and the pages that need it —
   the home page and the sign-up sheet — carry no other database code.
   ============================================================ */
(function () {
  'use strict';

  function cfg() {
    var c = window.BMU_FILES || {};
    return (c.url && c.anonKey) ? c : null;
  }

  /* Returns a promise that ALWAYS resolves — true if the row landed, false
     if anything at all went wrong. Nothing upstream should branch on it;
     it is there for the console and for tests. */
  window.bmuKeep = function keep(kind, email, extra) {
    var c = cfg();
    if (!c || !kind || !email) return Promise.resolve(false);

    var body = {
      kind:    String(kind),
      email:   String(email).trim().slice(0, 320),
      name:    (extra && extra.name)    ? String(extra.name).slice(0, 200)    : null,
      company: (extra && extra.company) ? String(extra.company).slice(0, 200) : null,
      details: (extra && extra.details) ? extra.details : {},
      source:  location.pathname
    };

    return fetch(c.url.replace(/\/+$/, '') + '/rest/v1/bmu_signups', {
      method: 'POST',
      headers: {
        'apikey':        c.anonKey,
        'Authorization': 'Bearer ' + c.anonKey,
        'Content-Type':  'application/json',
        /* nothing is read back — the table would refuse to anyway, and
           asking for the row returns a 401 that looks like a failure */
        'Prefer':        'return=minimal'
      },
      body: JSON.stringify(body)
    })
      .then(function (r) { return r.ok; })
      .catch(function () { return false; });
  };
})();
