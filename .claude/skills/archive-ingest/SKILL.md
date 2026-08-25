---
name: archive-ingest
description: Add garment photographs to the BMU archive in bulk — files them into nation/type/garment folders, writes their .txt records, fetches any new nation's flag, and registers everything in archive.html. Use when the user drops PNGs into _incoming/ or says "add these to the archive", "ingest", "log these garments".
---

# Archive ingest

Takes photographs out of `_incoming/` and turns them into archive entries.
One pass handles any number of files and any number of new nations.

## How the user supplies files

They drop PNGs into `_incoming/`, named as the garment's **display name**:

```
_incoming/Iraqi Army 1980s Desert DPM Combat Jacket.png
_incoming/Danish Army 1990s M84 Field Trousers.png
```

Optionally with an archive code in square brackets, which becomes the
garment's `ref` and its filename:

```
_incoming/Iraqi Army 1980s Desert DPM Combat Jacket [IQA1980DCJ].png
```

Subfolders are allowed and override the inferred nation:
`_incoming/iraqi/Some Jacket.png`.

## What to work out per file

**Nation** — the leading word of the name (`Iraqi`, `British`, `Danish`…),
or the subfolder. If it isn't already in `NATIONS`, treat it as new.

**Garment type** — infer from keywords, and use these exact strings because
they are the `CATS` order in archive.html:

| Keyword in name | Type |
|---|---|
| jacket, shirt, smock, fleece, jumper, parka | `Jackets / Shirts` |
| trouser, coverall, bib | `Trousers / Coveralls` |
| bergen, webbing, yoke, vest, bandolier, pack | `Bags / Webbing` |
| pouch, case, holster | `Pouches / Cases` |
| hat, cap, helmet, boonie, beret | `Headwear` |
| boot, shoe | `Footwear` |
| basha, sleeping, bivvy, net, bottle, sleep | `Sleep / Shelter / Field` |
| anything else | `Hardware / Misc` |

If a file is genuinely ambiguous, ask about that file rather than guessing
across the whole batch.

## Steps

1. **Read the batch.** `ls _incoming` — if empty, say so and stop.

2. **Derive the slug** exactly as archive.html does, or paths will not match:

   ```js
   name.toLowerCase().replace(/[’']/g,'').replace(/[^a-z0-9]+/g,'-').replace(/^-+|-+$/g,'')
   ```

3. **Build the folder and move the file:**

   ```
   archive/<nation-slug>/<type-slug>/<garment-slug>/<file>.png
   archive/<nation-slug>/<type-slug>/<garment-slug>/<file>.txt
   ```

   `<file>` is the ref code when given, otherwise the garment slug. Use
   `git mv` if the source is tracked, plain `mv` otherwise.

4. **Write the .txt** in the house format:

   ```
   <Garment name>

   Nation: <Label>
   Type: <Type>
   Archive ref: <REF>          ← omit the line when there is no code

   Placeholder record. Replace this file with the garment write-up:
   issue period, pattern, fabric and construction, and any notes on
   provenance or condition.
   ```

5. **New nation? Fetch its flag.** flagarchive.com is an Angular SPA with no
   downloadable image URLs — it renders from Wikimedia Commons, so resolve
   there directly:

   ```bash
   url=$(curl -sL --max-time 20 -A "BMU-archive/1.0" \
     "https://commons.wikimedia.org/w/api.php?action=query&format=json&titles=File:Flag_of_<Country>.svg&prop=imageinfo&iiprop=url&iiurlwidth=250" \
     | python3 -c "import sys,json;d=json.load(sys.stdin);p=list(d['query']['pages'].values())[0];print(p['imageinfo'][0]['thumburl'])")
   curl -sL --max-time 25 "$url" -o flags/<country>flag.png
   file -b flags/<country>flag.png     # must report PNG
   ```

   Use the **current** national flag, matching the existing set — Russian
   1990s garments sit under the modern Russian flag, not the Soviet one.

6. **Register in archive.html.**

   New nation → add to `NATIONS` before `unattributed`, keeping the shape:

   ```js
   { key:"iraqi", label:"Iraqi", abbr:"IQ", flag:"iraqflag.png", open:false,
     alias:["iraqi","iraq","al-iraq"] },
   ```

   Every garment → add to `ITEMS` under its nation's comment block:

   ```js
   { n:"iraqi", name:"Iraqi Army 1980s Desert DPM Combat Jacket",
     cat:"Jackets / Shirts", img:"IQA1980DCJ.png", ref:"IQA1980DCJ" },
   ```

   Omit `img` only when the file is named by slug; `ref` only when there is
   no code.

7. **Verify before reporting.** Both must pass:

   ```bash
   node -e "const s=require('fs').readFileSync('archive.html','utf8').match(/<script>([\s\S]*?)<\/script>/)[1]; new Function(s); console.log('syntax ok')"
   ```

   ```bash
   node -e "
   const fs=require('fs');const h=fs.readFileSync('archive.html','utf8');
   const s=h.match(/<script>([\s\S]*?)<\/script>/)[1];
   const {NATIONS,ITEMS}=new Function(s.slice(0,s.indexOf('const CATS'))+'; return {NATIONS,ITEMS};')();
   const sb=n=>n.toLowerCase().replace(/[’']/g,'').replace(/[^a-z0-9]+/g,'-').replace(/^-+|-+\$/g,'');
   let bad=0;
   ITEMS.forEach(p=>{const f=p.img||sb(p.name)+'.png';
     const d='archive/'+p.n+'/'+sb(p.cat)+'/'+sb(p.name);
     if(p.img&&!fs.existsSync(d+'/'+f)){console.log('MISSING IMG',d+'/'+f);bad++;}
     if(!fs.existsSync(d+'/'+f.replace(/\.png\$/,'.txt'))){console.log('MISSING TXT',d);bad++;}});
   NATIONS.forEach(n=>{if(n.flag&&!fs.existsSync('flags/'+n.flag)){console.log('MISSING FLAG',n.flag);bad++;}});
   console.log('items',ITEMS.length,'problems',bad);"
   ```

   Then load the page headless and confirm the script reaches the end —
   a runtime error leaves the page dead while the syntax check still passes:

   ```bash
   (python3 -m http.server 8777 >/dev/null 2>&1 &) ; sleep 2
   # inject an error listener in <head>, load, and read window.__err
   ```

8. **Empty `_incoming/`** and report: garments added, nations created, flags
   fetched, anything skipped.

## Gotchas

- **Never leave `_incoming/` files behind** — a half-ingested batch is worse
  than none. Move every file or say explicitly which you did not.
- **archive.html's script is one long top-level block.** Adding a `let`
  above its first use is fine; adding it *below* throws a temporal dead
  zone error at load and kills every listener after it. This has bitten
  three times. If you add state, declare it early.
- **The garment id is `<nation-key>/<garment-slug>`** and is what the saved
  library stores. Changing a garment's name orphans anyone's saved entry.
- **Renaming or moving anything under `archive/` changes its public URL.**
  `archive_1.html` holds hard-coded `raw.githubusercontent.com` paths.
- Images the user pastes into the conversation are **not on disk** — ask
  them to save it into `_incoming/` rather than pretending to have it.
