# British Material Unit — britishmaterialunit.com

Static site on GitHub Pages. `main` is the published branch; a push goes live in a
minute or two. **No build step, no framework, no external CSS or JS** — every page is
one self-contained HTML file with its CSS in `<style>` and its JS in `<script>`.

## Pages

| File | Is |
|---|---|
| `index.html` | home — the door, button row, Operations/Join/Repository panels |
| `archive.html` | the archive — list view, explore field, garment records. `ITEMS` holds every garment |
| `files.html` | **Files** (the signed-in reviewer's view). Supabase config in `files-config.js`. The Supabase table is still `bmu_collections` — the page was renamed, the database was not |
| `contact.html` `ew.html` `ou.html` `earlyaccess_2.html` `privacy.html` | content pages |
| `soframa.html` | the Soframa partner page — built on `ew.html`'s chrome. The **third partnership**, Soframa is the **Circular Partner** (Ramco is the **Research Partner**, and every footer's Research & Development line opens `/ou`): listed in the Operations sheet and sitting at 03 in the partner run (East West 01 → Ramco 02 → Soframa 03 → MarshalOS 04). Still `noindex` and out of the sitemap — listed on the site is not the same as asking to be found from outside it. Out of the footer partners reel, which carries marks and has none for Soframa |
| `contact.html` booking | three Cal.com calendars (`data-cal` on each tab, `app.cal.com/.../embed`) in one iframe, no Cal script. The page must answer Cal's `__iframeReady` with `parentKnowsIframeReady` or the calendar stays blank; it reads `__dimensionChanged` (from `type`, `method` or `fullType`) to size the frame, and covers the Cal.com wordmark band (80px) only when the frame is ≥768px wide, the only layout that has it |
| `join.html` | redirect stub to `/#join`. `collections.html` redirects to `/files` — reviewers were emailed the old address |

Other `*.html` at root (`*_1`, `test*`, `home`, `mtpdemo*`, `*_greenscreen`,
`archive_1`) are **old variants — not live. Don't edit them.**

- Garment photos + records: `archive/<nation>/<type>/<garment>/<REF>.png` + `.txt`,
  plus a generated `index.html` — each garment's own crawlable page at
  `/archive/<nation>/<type>/<garment>/`
- Short links: every garment also has `/archive/<n>` (`archive/<n>.html`, the
  preview a pasted link shows). The number belongs to the **ref**, via the
  append-only `NUMBERS` map in `archive.html` — never by position in `ITEMS`,
  never reused, never edited by hand. `seo_build.py` assigns new ones and
  rewrites every `<n>.html`.
- The dock's four tools are now separate squares beside the search bar
  (`.dock-tool`: `#dockCircle` `#dockList` `#dockPlay` `#dockRefs`, then the
  save square), all calling `pressFace(face)`. The old stacked button
  `#dockExplore` is hidden but kept, because the script still speaks to it.
  On a phone the open search bar takes its own row under the squares.
  Board garments have three views (square top-left: 1 photo, 2 header,
  3 landscape tab); geometry goes through `wOf`/`hOf`. Originally the
  middle dock button had four faces: circle (explore), list, play,
  plus. Play is SoundCloud (`BMU_SOUND` in `archive.html`, driven by
  postMessage, no SoundCloud script). Plus opens **References** (and wears
  a cross while open): the reader's own image board, a separate layer
  (`#refs`, `#refsTools`, `#refsTray`, all `refs`/`rf-` names) that changes
  nothing else. Images lock in pairs/groups (5px gap, `locks` tree).
  Cluster deals everything randomly except the last few pieces moved by
  hand (`touched`, `KEEP`), which stay put and are clustered around. Each
  garment card has a `+` (`.btn-ref-inline`) that queues it in the tray
  (localStorage `bmu-refs-tray`); a square on the button's corner says
  garments are waiting. The board is kept in IndexedDB and exported as
  `BMU-References-NNN.zip` (images + `references.json`, locks included),
  which the plus reads back. The `bank` source (an Instagram-fed reference
  bank under `/references/`) is in code only — `SOURCES.bank.live` false.
- Icons are loose `.svg` at root; `flags/`, `partners/`, `patterns/` are images only.

## Form submissions

Everything a reader submits is **emailed via FormSubmit and also written to
Supabase** (`bmu_signups`, one table, `kind` = join / early / wholesale /
request). `signups.js` does the write; `files-config.js` carries the keys.

The write is deliberately never waited on — the email is what the reader is
waiting on, so a database that is down cannot stop somebody joining.

**The publishable key is public. `bmu_signups` lets `anon` INSERT and
nothing else** — no SELECT policy, or the key printed on the site would
hand anyone the whole mailing list. See `setup/signups.sql`.

## Shared chrome

The site header and footer are **duplicated in every page**, not shared. A change to
either must be applied across all pages that carry it (`grep -l siteFooter *.html`).

## Working rule

**For small changes, go straight to the relevant file and edit it. Don't explore the
whole project. If unsure which file, ask me.**

Verify by measuring in a browser, not by assuming. Skills: `publish`, `archive-ingest`,
`lambrino-archive`.

## Adding a garment

Name the photograph as the garment and drop it in `_incoming/`:

```
_incoming/German Army 1990s Flecktarn Parka Hood [GA1990FPH].png
_incoming/French Army 1980s Bermuda F2 Shorts {Cotton}.png
_incoming/dutch/Some Jacket.png          # subfolder overrides the nation
```

`[REF]` is the archive code and the filename it is saved as; left off, it is
derived the way the register already spells them. `{Material}` is the
material facet, `Unlisted` when left off. Then:

```bash
python3 tools/ingest.py           # plan — prints what it would do, writes nothing
python3 tools/ingest.py --write   # files it, writes the ITEMS entry, runs seo_build
python3 tools/check.py            # does the register agree with the disk?
```

**A `.txt` record is not required.** The live page holds every record back
behind Sourcing and never fetches it, and `seo_build` falls back to a generic
description. A garment is complete with its photograph and its `ITEMS`
entry; write a record when there is something to say.

**`ITEMS` is still the register** — a folder that is not in it is invisible:
no card, no cluster, no page, no sitemap entry. `ingest.py` writes the entry
so you do not have to, and `check.py` reports any folder that was missed.

## After adding or renaming a garment by hand

```bash
python3 tools/seo_build.py        # --dry-run to see what it would do
```

Rewrites every garment's `index.html`, the `<noscript>` index inside
`archive.html` (between the `BMU-SEO-INDEX` markers), `sitemap.xml` and
`robots.txt`, all from `ITEMS` and the folders on disk. It only writes those;
it never touches a `.txt` record or a photograph. `ITEMS` is the list of what
is published — a folder that is not in it gets no page.
