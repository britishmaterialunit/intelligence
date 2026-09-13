---
name: lambrino-archive
description: Bulk-scrape a lambrino.co.uk collection into the BMU archive — derives a house-style name for every product, collapses size variants, skips anything already archived, downloads and converts the lead image, and writes the garment folder, .txt record and archive.html entry. Use when the user says "scrape lambrino", "pull the British collection", "bulk add from lambrino", or names a lambrino collection URL.
---

# Lambrino → archive

Turns a lambrino.co.uk collection into archive entries. Two phases with a
review checkpoint between them, because the store has ~3,500 listings that
collapse to ~1,200 garments and the names need a human eye before 1,200
folders get created.

Everything lives in this skill's directory: `naming.py` (the name/dedupe
engine), `survey.py` (phase 1), `review_page.py` (the reviewable list),
`ingest.py` (phase 2).

## Two ways in

**A named list of products** — one or two per nation, chosen by hand:

```bash
python3 .claude/skills/lambrino-archive/fetch_urls.py \
  --urls _incoming/lambrino/urls.txt --root .
```

The URL file is tab separated: `<product url>` `[nation key]` `[name override]`.
The list IS the decision, so there is no review phase — but the two override
columns matter. A shop title is written to sell, not to catalogue, and the
engine gets perhaps eight in ten right on its own. The rest are cases it
cannot know: a Czech jacket tagged Czechoslovakia, a Soviet shirt tagged
Russia, a date that lives in the garment's history rather than in its name.
Put those in the list rather than growing the parser a special case per
garment. Always `--dry-run` first and read the names before writing.

Then write the records:

```bash
python3 .claude/skills/lambrino-archive/descriptions.py \
  --sources _incoming/lambrino/sources.json --root .
```

**This step is not optional.** Every listing opens with an "At a glance"
list — material, closures, pockets, the pattern, full measurements, the
issue period, and which army it came from. That list IS the archive record:
it is the only place the measurements and the dating exist, and it was
written by people who had the garment in their hands. A folder holding a
placeholder instead has thrown that away.

Everything after "Grades -" is condition and sales patter for one particular
item on one particular day. It does not belong in an archive record and the
parser stops there.

**A whole collection** — the bulk path below, with its review checkpoint.

Both share `naming.py`. After either, rebuild the page's arrays from what is
on disk rather than editing them by hand — the folders are the archive and
the arrays are a view of them.

## Read this first

**Fetch with curl, not urllib.** The Pythons on macOS are routinely installed
without a CA bundle and urllib then refuses every https URL with
CERTIFICATE_VERIFY_FAILED. Same for Wikimedia when pulling flags: it blocks
requests that do not carry a descriptive User-Agent, and the failure looks
exactly like rate limiting — a few succeed, then everything fails.

**Do not scrape the paginated HTML.** `?page=1…149` at 24 products a page is
149 requests plus 3,576 product pages. Shopify exposes the whole catalogue as
JSON, 250 at a time:

```
https://lambrino.co.uk/collections/<collection>/products.json?limit=250&page=N
```

15 requests, and each record already carries `title`, `product_type`, `tags`,
`body_html` and `images` — no product-page fetch needed. `survey.py` does this
and caches the result, so re-runs are offline.

**Size matters.** Output is 1000x1000 PNG, ~774 KB each, so ~1,220 garments is
**~0.90 GB** — under the 1 GB GitHub Pages cap but not by much. Report the
projection before phase 2 and agree how much to take in one go. Never kick off
the full download without raising it.

## Phase 1 — survey

```bash
python3 .claude/skills/lambrino-archive/survey.py \
  --collection britain-uk --nation british --out _incoming/lambrino
```

Writes `_incoming/lambrino/`:

| file | what |
|---|---|
| `catalogue.json` | raw products, cached — pass `--refresh` to re-fetch |
| `manifest.tsv` | one row per unique garment; **this is the file the user edits** |
| `manifest.json` | same rows plus image URLs; consumed by phase 2 |
| `review.html` | browsable version of the manifest — build it with `review_page.py` |

1,200 tab-separated rows are not reviewable in a terminal. Always build and
publish the review page as an Artifact so the user can actually read the list:

```bash
python3 .claude/skills/lambrino-archive/review_page.py --out _incoming/lambrino
```

It is searchable and filters by category, status, and what still needs
deciding. The TSV stays the file that gets edited.

Report to the user: counts of `new` / `check` / `have`, the flag tally, and
the projected download size.

**Status column:**

- `new` — no match in the archive.
- `check` — an existing garment's words are wholly contained in this one
  (`near` column names it). These are the rows a human must judge. Typically
  the archive holds a terse `British Desert DPM Shirt` and the store has five
  more specific versions of it.
- `have` — slug already in the archive.

The `replaces` column names the archived garment a row supersedes, filled in
for `check` and `have` rows. Clearing it keeps the original; leaving it and
passing `--replace-existing` in phase 2 deletes the original once the
replacement is safely on disk.

**Flags** mark what could not be derived and needs research:
`date-unknown`, `fabric-unknown`, `type-from-product-type`,
`name-disambiguated`.

## Checkpoint

Hand the manifest to the user. They edit `include`, `name` and `cat` directly
in `manifest.tsv` — phase 2 reads the edited TSV, not the derived values. Most
of what they will change is the date: ~960 rows carry the `0000s` placeholder
because the listing gave no explicit marker. Do not start phase 2 until they
say so.

## Phase 2 — ingest

```bash
# always eyeball a small batch first
python3 .claude/skills/lambrino-archive/ingest.py --limit 25
# then the rest, register them, and retire what they supersede
python3 .claude/skills/lambrino-archive/ingest.py --register --replace-existing
```

Per included garment it downloads the first product image and writes it as a
PNG of exactly `--px` by `--px` (default 1000):

```
archive/british/<cat-slug>/<garment-slug>/<garment-slug>.png
archive/british/<cat-slug>/<garment-slug>/<garment-slug>.txt
```

The `.txt` uses the house format from `archive-ingest`, plus provenance
(source listing, URL, how many size variants collapsed into it) and a
`To confirm:` line listing that garment's unresolved flags.

A garment whose `.png` already exists is skipped, so the run is resumable —
stop it and restart at any point. `--register` inserts the `ITEMS` entries into
`archive.html`; `--dry-run` prints paths and writes nothing.

**Conversion** uses Pillow, not `sips`: one LANCZOS resample straight from the
2400px original, then the alpha flattened onto white and padded to square.
Resampling once preserves more detail than stepping down, and flattening saves
roughly a fifth of the file size for no visible change — across 1,200 garments
that is what keeps the repo under the Pages cap. It falls back to `sips` if
Pillow is missing.

**`--replace-existing`** retires superseded garments: for each non-empty
`replaces` value it deletes that garment's folder and its `ITEMS` row. It runs
*last*, after the replacements are written and registered, so a failed download
can never leave the archive with neither version. It is the one destructive
thing here — confirm the list with the user before passing it.

## Naming

`[Nation] [Division] [Date] [Additional Info] [Garment Type]`

> British Army 1990s Desert DPM Combat Cotton Jacket

- **Nation** — `British`.
- **Division** — `Army`, `RAF`, `Royal Navy`, `Royal Marines`, `Tri-Services`,
  `Police`, `MoD`.
- **Date** — decade, and **only from an explicit marker**: `S95`/`CS95` → 1990s,
  `84 Pattern` → 1980s, `72 Pattern` → 1970s, `MTP`/`PCS` → 2010s, `P23` → 2020s,
  a literal `70s`. Never inferred otherwise: with no marker the slot reads
  **`0000s`** and the row is flagged `date-unknown`, so every name has the same
  shape and the gaps are greppable. The user sets the real decade by hand.
- **Additional Info** — the *residue* of the source title: everything left after
  removing nation, division, date marker, garment noun, sizing and filler
  (`Camo`, `Camouflage`, `Pattern`, `Genuine`, `Surplus`, `Mens`…), in the
  title's own word order, with any `- Regiment -` segment moved to the front.
  Residue rather than a keyword whitelist, because a whitelist silently drops
  the words that distinguish garments — `SAS`, `Footguard's`, `Class II`,
  `Drummers'`, `Senior Rates`.
- **Garment Type** — the noun that also picks the archive category, falling
  back to Shopify's `product_type` when the title has no garment word. Exactly
  one garment noun survives: the first match in `GARMENT_WORDS` order wins and
  every other noun is stripped from the residue, so a listing titled "Combat
  Jacket / Shirt" comes out a Jacket, never both. Order is specific-beats-
  generic (`Smock`, `Gilet`, `Greatcoat` before `Jacket`), so reordering that
  list is how you change which noun wins.

## Deduplication

The user's rule: **same wording, different size = one garment. Same wording,
different material = two garments.**

1. Strip trailing size segments (`- Medium`, `- W34 L29`, `- Large 180/104`,
   `- Small 56cm`) and any size fragment left inline.
2. Group by derived name. A group is one garment.
3. Within a group, if members differ in fabric, split them and put the fabric
   in the name. Fabric comes from the title when it is there, otherwise from
   `body_html` — which is where it usually is, and why phase 1 reads the
   description at all.
4. Two garments must never produce the same slug; the engine appends a numeric
   suffix and flags `name-disambiguated` if they would.

On the real catalogue this takes 3,576 listings to 1,221 garments.

## Verify before reporting

```bash
node -e "const s=require('fs').readFileSync('archive.html','utf8').match(/<script>([\s\S]*?)<\/script>/)[1]; new Function(s); console.log('syntax ok')"
```

Then check every garment added *by this run* has both files:

```bash
python3 -c "
import json,os,sys; sys.path.insert(0,'.claude/skills/lambrino-archive')
from naming import slug
bad=0
for a in json.load(open('_incoming/lambrino/last-run.json')):
    d=os.path.join('archive/british',slug(a['cat']),slug(a['name']))
    for ext in ('.png','.txt'):
        p=os.path.join(d,slug(a['name'])+ext)
        if not os.path.exists(p): print('MISSING',p); bad+=1
print('checked','problems',bad)"
```

Do **not** assert every item in `ITEMS` has an image — most pre-existing
archive entries are text-only records with no photograph, and that is fine.
Only the garments this run added must have both files.

## Gotchas

- **The catalogue is cached.** `survey.py` re-uses `catalogue.json` unless given
  `--refresh`. Re-running is free; re-fetching is not.
- **The TSV wins.** Phase 2 takes `include`, `name` and `cat` from the edited
  TSV and only the image URL from the JSON. Rows are matched on the `url`
  column — if the user deletes or rewrites that column the row is dropped.
- **Names must not contain `"`.** They are written straight into a JS string
  literal in `archive.html`. The engine strips double quotes; keep it that way
  if you edit the naming code.
- **`archive.html`'s script is one long top-level block** — see `archive-ingest`
  for the temporal-dead-zone trap if you add state to it.
- **Renaming a garment changes its public URL** and orphans anyone's saved
  library entry, whose id is `<nation-key>/<garment-slug>`. Get names right in
  the manifest rather than renaming folders later.
- Images arrive as 2400px PNGs around 3.5 MB; resampling is what keeps the repo
  publishable. Do not skip it.
- **`--replace-existing` deletes archive folders.** Only rows with a `replaces`
  value are touched, but the deletion is real and changes public URLs. Show the
  user the list first — `--dry-run --replace-existing` prints it without acting.
