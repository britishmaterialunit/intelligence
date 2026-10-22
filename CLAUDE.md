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
- The dock at rest is the search bar, explore (`#dockCircle`, compass
  icon) and a plus (`#dockMore`). The plus adds `.more` to `#dock`, laying
  out list, play, the board (`#dockRefs`, asterisk icon) and save, and
  becomes a minus. Every tool square calls `pressFace(face)`.
  Play opens SoundCloud's own widget in a draggable window (`#scPanel`,
  over everything incl. carried pages); its cross puts it away (music keeps
  playing), and `#dockPlay` pauses it and brings it back. Position kept in
  localStorage `bmu-sc-pos`. There is no folded SoundCloud square any more:
  `#dockPlay` itself wears the colour of the artwork playing (`scTint` →
  `--sc-col`, `html.sc-tinted`, icon inverted on pale covers via `--sc-img`).
  The dock itself does not move — it cannot be dragged. The old stacked button
  `#dockExplore` is hidden but kept, because the script still speaks to it.
  On a phone the open search bar takes its own row under the squares.
  Board garments have three views (squares 1/2/3 down the left edge: photo,
  header, landscape tab); geometry goes through `wOf`/`hOf`. The board's
  Search (`#refsSearch`) asks Wikimedia Commons and Openverse in parallel —
  no keys, both CORS-open; Openverse is slow (10–40s) so it is timed out at
  45s. Each placed result keeps its `credit` (title, creator, licence, page),
  saved and exported.
  **Cut out** (scissors on a picked board image) lifts the background in the
  browser: a plain even ground is flood-filled from the edges; anything else
  goes through U²-Net-p (`models/u2netp.onnx`, Apache-2.0, see
  `models/README.md`) on ONNX Runtime Web 1.22.0 from jsDelivr — **the one
  external script on the site, loaded only when a reader asks for a cut**.
  The original is kept (`orig`) so the same button restores it. Originally the
  middle dock button had four faces: circle (explore), list, play,
  plus. Play is SoundCloud (`BMU_SOUND` in `archive.html`, driven by
  postMessage, no SoundCloud script). Plus opens **References** — **called Maps from now on**; while open the address reads `/maps` (`mapsUrl`: pushed on open, Back closes, `maps.html` is the archive itself re-addressed — **generated** by `tools/build_maps.py` (run by `seo_build.py`; `check.py` fails if it is stale), never edited; a redirect stub made iMessage's preview fall back to the tiled icon) — (and wears
  a cross while open): the reader's own image board, a separate layer
  (`#refs`, `#refsTools`, `#refsTray`, all `refs`/`rf-` names) that changes
  nothing else. Images lock in groups (`gapOf`: 5px between two images, 14px where a garment meets anything). Stray pixels from a shrunk box are cleared by repainting the whole board (`repaint`/`repaintSoon`, `#refs.rf-flush`). A lock `{p, c, side, d}`
  keeps c on p's side with `d` = the offset of their leading cross edges, so
  rows stay top-aligned and columns left-aligned; `relay()` walks the locks,
  `untangle()` eases apart any two group members that overlap. Locking to a
  group meets its whole flush face (`faceOf`), fits the arrival to the face's
  length when within `FIT` (15%), and locks it to every face image and any
  other neighbour it ends up flush with. Shift-press adds to / takes from a multi-pick (`picked`, `.picked`), Shift-drag on the board draws a box (`.rf-marquee`) that picks what it touches; dragging any picked image carries all of them (`unitOf`), Delete/arrows/Escape act on the pick. Dragging snaps to nearby edges,
  centres and gap-lines with hairline guides (`snapUnit`; Alt to place
  freely); resizing from the corner holds the opposite corner and snaps its
  far edges the same way. View 3 is one shape for every garment: square photo + panel `PANEL`
  (1.25) × its width, same height, so tabs divide in the same place; a long
  record has its panel type set smaller instead (`panelFit` → `--ps`). Garments: no Cut out; extra photographs (`shots`) get dots in
  views 2 and 3. Search is filtered as in the owner's `commons-filter.js`, ported
  inline: `obscenity` 0.4.6 (MIT, jsDelivr `+esm`, fetched when Search
  opens) plus `EXTRA_BLOCK_TERMS`/`WHITELIST`/`BLOCK_CATEGORY_PATTERNS`, and
  The search column has Search / Saved tabs: a bookmark on any result keeps
  it (metadata only, localStorage `bmu-refs-saved`), newest first, placeable
  like a result. `MILITARY_ONLY` is **false** (owner's call: "terrain" should
  mean landscapes) — the steering and relevance code is kept, switched off.
  `BLOCK_GRAPHIC_INJURY` is false.
  Cluster deals everything randomly except the last few pieces moved by
  hand (`touched`, `KEEP`), which stay put and are clustered around. Each
  garment card has a `+` (`.btn-ref-inline`) that queues it in the tray
  (localStorage `bmu-refs-tray`); a square on the button's corner says
  garments are waiting; the save square (`#dockLibrary`) counts saved
  garments the same way. Folded, the plus (`#dockMore`) carries one number,
  the two together (`paintTotalBadge`). On the board a bookmark square
  (`#dockShelf`, beside play, with its own count) opens the saved garments in
  `#refsSaved`, just above the bar; placing one leaves it saved. The board is kept in IndexedDB and exported as
  `BMU-References-NNN.zip` (images + `references.json`, locks included),
  which the plus reads back. **Send** (`#refsSend`, admins only, checked
  against `bmu_admins`) puts that zip in the private Supabase bucket
  `bmu-boards` and names it in a file's `board_path`; `/archive?board=<file
  id>` (Files' "Open reference board") lays it down. Plain fetch with the
  session /files keeps — see `setup/collections.sql` for the rules. The `bank` source (an Instagram-fed reference
  bank under `/references/`) is in code only — `SOURCES.bank.live` false.
- **Music across pages** (`carried` in `archive.html`): once the music has
  been started, the archive is never unloaded. Links to other pages open
  them in a full-window iframe (`#bmuCarry`) over the archive, with the
  address bar, tab title and back button kept in step, and a play/pause
  square (`#hdMusic`) injected into that page's `#siteHead .hd-inner`, just
  before `.hd-tools` — not inside it, because pages carry `.hd-tools` down
  into the footer at the bottom and the footer's plus needs the room. Any way back to `/archive` lifts the frame. No other page
  carries code for this — it is all done from the archive, so pages must
  keep `.hd-tools` / `#hdExplore` in their header for the square to land.
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

## Renaming a garment

The folder — and so the garment's page address — comes from its name, so a
rename moves it. `git mv` the folder, change the name in `ITEMS` and the
record's first line, keep the **ref** (the `/archive/<n>` number belongs to
it), and leave an `index.html` marked `BMU-MOVED` in the old folder that
redirects to the new one (check.py knows it is not a stray). Add the old →
new id to `RENAMED` in archive.html so boards and trays still find it.

## After adding or renaming a garment by hand

```bash
python3 tools/seo_build.py        # --dry-run to see what it would do
```

Rewrites every garment's `index.html`, the `<noscript>` index inside
`archive.html` (between the `BMU-SEO-INDEX` markers), `sitemap.xml` and
`robots.txt`, all from `ITEMS` and the folders on disk. It only writes those;
it never touches a `.txt` record or a photograph. `ITEMS` is the list of what
is published — a folder that is not in it gets no page.
