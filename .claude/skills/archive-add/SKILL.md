---
name: archive-add
description: Add one pasted garment photo to the BMU archive under the name the user gives, then commit and push. Use when the user pastes an image with a garment name, or says "add to archive" about a pasted photo. For a batch already sitting in _incoming/, use archive-ingest.
---

# Archive add

The user has given a photo and a name. Do these steps and nothing else: no
research, no matching against other photos, no checking the live site.

`<image>` is the path in the image's `[Image: source: ...]` line. `<name>` is
the name given, with any stray trailing `_` or space dropped. If there is no
name, ask for it; do not invent one.

```bash
cd /Users/tommwd/WEBBMU/intelligence
cp "<image>" "_incoming/<name>.png"
python3 tools/ingest.py --write
python3 tools/check.py
git add archive.html maps.html sitemap.xml robots.txt archive/*.html "archive/<nation-slug>/<type-slug>/<garment-slug>"
git commit -m "Archive: <name>"
git push origin main
```

`ingest.py` prints the folder it filed the photo in. It also writes a new
short link, `archive/<n>.html`, so add that too or the short link stays off
the site. Do not `git add -A`: stray `.DS_Store` files sit in the tree.

If `ingest.py` skips the file because the garment is already there, or
`check.py` reports a problem, stop and say so. Otherwise report the folder and
the commit in one line.
