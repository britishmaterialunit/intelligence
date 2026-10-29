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
| `soframa.html` | the Soframa partner page — built on `ew.html`'s chrome. Soframa is the **Circular Partner**. The Operations sheet links only East West and Soframa (Ramco sits between them as `.ni-parked`, a box that answers a press and goes nowhere); each is a run of two — partner page 01 → `/contact#meeting` 02, whose Back returns to whichever partner the reader came from (`document.referrer`, else Operations). **Ramco is off the site until they agree to be named**: `ou.html` is kept but unlinked (its Operations box links nowhere, the footer's Research & Development is plain text, out of the sitemap and `seo_build.py`). Still `noindex` and out of the sitemap — listed on the site is not the same as asking to be found from outside it. Out of the footer partners reel, which carries marks and has none for Soframa |
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
  While music plays (`body.music-on`, set in `setPlayFace`) `#dockPlay` stays
  out at rest beside explore and the plus, so the archive has its coloured
  play square too. The dock itself does not move — it cannot be dragged. The old stacked button
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
  `models/README.md`) on ONNX Runtime Web 1.22.0 from jsDelivr — **external scripts are loaded only when a reader asks for them** (this,
  PDF.js for a PDF link, obscenity for Search).
  The original is kept (`orig`) so the same button restores it. **Crop**
  (`.rf-crop`, beside the clock; not on garments; `startCrop`/`endCrop`) opens a
  frame with eight handles over the picture; tick, Enter or a press off it keeps
  it, Escape leaves it. Non-destructive: `full` (the uncropped photograph) and
  `crop` (fractions of it) are kept, so cropping again shows the whole photo
  with the frame where it was. The kept part stays exactly where it sat on the
  board. A cut-out picture is cropped as it is (only tighter), and its `orig`
  is cropped with it. While the frame is open, `save()` writes the item's
  pre-crop geometry and `showShot` shows `cropping.url`. **Text** (bar button, `addText`) puts a text box on the board: an item with
  `text` (markup cleaned by `cleanText` to b/i/u/br/div) in place of a blob, in
  `--font`, type sized by the box so resizing keeps its shape; `ar` is read off
  the box (`fitText`). B/I/U squares on its top edge; a tap on a picked box
  writes in it. **The clock** (`.rf-stamp`, beside the scissors; not on
  garments) sets `stamp`: day and 24-hour time in italics on the top edge,
  pressed again it re-dates, its cross removes it. Both go in `references.json`
  (text boxes also as a `.txt`). **Draw** (bar button, `startDraw`/`endDraw`) turns the
  board into paper (`#refsInk`, an SVG in the stage; `#refsDraw` panel top-right:
  Undo, Clear, Formulate, Done; Space-drag or two fingers pan). **Formulate**
  (`formulate` → `recognise` per stroke, then `tidy`) reads strokes by shape
  only — no AI, no network: box, circle/oval, diamond, triangle, line, arrow
  (hook or V at an end), elbowed line, dashed/dotted line (short collinear
  pieces); small marks inside a box are writing and kept. `tidy` makes boxes
  alike one size, aligns rows and columns, spaces rows of 3+ evenly, joins
  line ends to boxes (straight if drawn straight, elbowed if drawn with a
  corner). Double-tap a box to type its name (replaces the writing in it).
  Done makes one item with `draw` ({shapes, sw, w0, h0}, read back through
  `cleanDraw`); its pen (`.rf-pen`) reopens it. Exported as `.svg` plus
  `draw` in `references.json`. **Links** (paste on the board, or bar
  button Link → `askLink`; `addLink`/`parseLink`) become cards: YouTube
  (nocookie embed, i.ytimg thumb), Vimeo, Instagram (`/p|reel/<code>/embed/`),
  LinkedIn posts (`/embed/feed/update/urn:li:…`), TikTok (`/player/v1/`) show a
  thumbnail (oEmbed where it answers with CORS, else the player's own preview,
  pointer-events off) and play in place in the service's iframe — third-party
  players, like SoundCloud's, no scripts. LinkedIn profiles and other pages are
  plain cards that open in a new tab. Only `link.url` (+ title/thumb as text and
  a picture) is kept; everything is rebuilt from the URL by `relink`. Exported as
  a `.url` shortcut plus `link` in `references.json`. No service chrome on a card: a
  player shown as the face is cropped to its picture (`LINK_KIND[].crop` —
  Instagram posts `instagram` 1:1, reels `igreel` 9:16, below the embed's 54px
  header) with the site's own play square over it. A link ending `.pdf` is a
  `pdf` card: its front page drawn by PDF.js 4.10.38 (jsDelivr, loaded on the
  first PDF; `pdfCover`), title from the PDF's metadata else the filename. Only
  PDFs served with CORS can be drawn; others keep a plain white PDF card. Originally the
  middle dock button had four faces: circle (explore), list, play,
  plus. Play is SoundCloud (`BMU_SOUND` in `archive.html`, driven by
  postMessage, no SoundCloud script). Plus opens **References** — **called Maps from now on**; while open the address reads `/maps` (`mapsUrl`: pushed on open, Back closes, `maps.html` is the archive itself re-addressed — **generated** by `tools/build_maps.py` (run by `seo_build.py`; `check.py` fails if it is stale), never edited; a redirect stub made iMessage's preview fall back to the tiled icon) — (and wears
  a cross while open): the reader's own image board, a separate layer
  (`#refs`, `#refsTools`, `#refsTray`, all `refs`/`rf-` names) that changes
  nothing else. Images lock in groups (`gapOf`: 5px between two images, 14px where a garment meets anything). Stray pixels from a shrunk box are cleared by repainting the whole board (`repaint`/`repaintSoon`, `#refs.rf-flush`). A lock `{p, c, side, d}`
  keeps c on p's side lined up on the line they met at when locked — `at`
  = s (leading edges), m (centres) or e (far edges), `d` the offset there — so
  rows stay top-aligned and a garment centred on a picture stays centred as
  either is resized; `relay()` walks the locks,
  `untangle()` eases apart any two group members that overlap. Locking to a
  group meets its whole flush face (`faceOf`), fits the arrival to the face's
  length when within `FIT` (15%), and locks it to every face image and any
  other neighbour it ends up flush with. Shift-press adds to / takes from a multi-pick (`picked`, `.picked`), Shift-drag on the board draws a box (`.rf-marquee`) that picks what it touches; dragging any picked image carries all of them (`unitOf`), Delete/arrows/Escape act on the pick. **Every cluster is round** (`roundOffsets`, behind
  `packOffsets`, so the archive's field too): 2–6 pieces on a ring, 7–19 on
  rings about a middle one shared out so the outer ring is full, 20+ the
  golden spiral (already a disc). The board's mixed path (groups, kept pieces)
  lays on the same round slots, passing over the ones kept pieces cover. With two or
  more picked, **Cluster** is theirs alone (`clusterPicked`, the bar says
  `Cluster 05`): all fitted to one box (`CBOX`), laid on the archive's golden
  spiral (`packOffsets`) in the archive's own order (garments by `ITEMS`, then
  the rest as they read), where they were or else beside the board; their
  locks let go; Reverse restores. On touch, a half-second hold adds a piece to
  the pick or takes it out (a tap elsewhere lets the pick go). Dragging snaps to nearby edges,
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
  id>` (Files' "Open reference board") lays it down. A person can have any number of
  **project boards** (one file each, titled by the project). Send groups its
  list by person: Update a board (same file, `board_path` → `<stem>-v<n+1>.zip`,
  the old zip deleted — the version lives in the name, `verOf`), or New project
  board (asks the project's name; a name that person already has is refused).
  An admin opening a sent board can add to it and Send it back as the next
  version; Files shows `V<n> · sent <date>` and New version until looked at. Files' **Open Archive** (`#cvArchive`, a
  step under the others, compass in its well, an arrow `#cvArchiveMark` that
  turns -45° on press) writes the archive's keys itself (same origin,
  `keepShelf`): the file's garments onto `bmu.archive.saved` (once verified:
  affirmed kept, negatives removed — Verify does the same) and
  `bmu.archive.joined` = their email; then `/archive#saved`. The archive
  re-reads the shelf, holds on the loading gate (`openForShelf` skips
  'saved'), and the reader's press opens it onto the saved cluster.
  (`#keep=<ids>` still works: `keepFromUrl` adds them itself.) Plain fetch with the
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
