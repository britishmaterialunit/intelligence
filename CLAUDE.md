# British Material Unit — britishmaterialunit.com

Static site on GitHub Pages. `main` is the published branch; a push goes live in a
minute or two. **No build step, no framework, no external CSS or JS** — every page is
one self-contained HTML file with its CSS in `<style>` and its JS in `<script>`.

## Pages

| File | Is |
|---|---|
| `index.html` | home — the door, button row, Operations/Join/Repository panels |
| `archive.html` | the archive — list view, explore field, garment records. `ITEMS` holds every garment |
| `collections.html` | **Files** (the signed-in reviewer's view). Supabase config in `collections-config.js` |
| `contact.html` `ew.html` `ou.html` `earlyaccess_2.html` `privacy.html` | content pages |
| `join.html` `repository.html` | redirect stubs to `/#join`, `/#repository` |

Other `*.html` at root (`*_1`, `test*`, `home`, `mtpdemo*`, `soframa`, `*_greenscreen`,
`archive_1`) are **old variants — not live. Don't edit them.**

- Garment photos + records: `archive/<nation>/<type>/<garment>/<REF>.png` + `.txt`
- Icons are loose `.svg` at root; `flags/`, `partners/`, `patterns/` are images only.

## Shared chrome

The site header and footer are **duplicated in every page**, not shared. A change to
either must be applied across all pages that carry it (`grep -l siteFooter *.html`).

## Working rule

**For small changes, go straight to the relevant file and edit it. Don't explore the
whole project. If unsure which file, ask me.**

Verify by measuring in a browser, not by assuming. Skills: `publish`, `archive-ingest`,
`lambrino-archive`.
