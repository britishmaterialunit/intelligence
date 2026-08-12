---
name: publish
description: Commit and push this repo to GitHub, publishing the live site at britishmaterialunit.com. Use when the user says "publish", "push", "update GitHub", "put it live", or "deploy".
---

# Publish

Commits outstanding work and pushes `main` to GitHub. `main` is the GitHub
Pages source and [CNAME](../../../CNAME) points at **britishmaterialunit.com**,
so a push goes live within a minute or two. There is no staging branch.

## Steps

1. **See what changed.**

   ```bash
   git status --short
   git diff --stat
   ```

   If there is nothing to commit and nothing unpushed, say so and stop.

2. **Sanity-check the working tree.** Never commit blind:
   - No probe/scratch files left at the repo root (`_*.html`, `*.tmp`).
     Any file matching `_*.html` is a leftover test harness — delete it.
   - New images belong under `archive/<nation>/<garment-type>/<garment>/`
     alongside a matching `.txt` of the same basename.
   - If `archive.html` changed, syntax-check the inline script:

     ```bash
     node -e "const s=require('fs').readFileSync('archive.html','utf8').match(/<script>([\s\S]*?)<\/script>/)[1]; new Function(s); console.log('ok')"
     ```

3. **Commit in logical groups**, not one sweeping commit. Typical split:
   - archive content — `archive/**`, `flags/**`
   - archive page — `archive.html` and its icons
   - landing page — `index.html` and any linked sub-page

   Write a real subject line describing the change, not "Update index.html".
   End every message with:

   ```
   Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
   ```

   Watch out: `git add -A` followed by one commit collapses the whole split.
   Stage each group with an explicit pathspec instead.

4. **Push.**

   ```bash
   git push origin main
   ```

5. **Report** the commits pushed and that the site will update shortly.

## If the push fails on credentials

`fatal: could not read Username for 'https://github.com'` means the macOS
keychain has no token for this repo. A non-interactive session cannot supply
one — do not try to work around it, and never ask the user to paste a token
into the chat.

Tell the user to run this once in their own terminal:

```bash
cd ~/WEBBMU/intelligence && git push origin main
```

Username is their GitHub username; password is a **personal access token**
(GitHub → Settings → Developer settings → Personal access tokens →
Fine-grained, with `Contents: read and write` on `intelligence`). The
`osxkeychain` helper stores it, and every later push — including mine —
goes through without prompting.

## Notes

- Commits already made are never lost by a failed push; they sit ahead of
  `origin/main` and go up on the next successful attempt.
- Moving or renaming anything under `archive/` changes its public URL. Check
  `archive_1.html` for hard-coded `raw.githubusercontent.com` paths.
- Animation and transition timing cannot be verified headlessly — virtual time
  does not advance CSS transitions. Flag timing changes for the user to check
  in a real browser rather than claiming they were confirmed.
