#!/usr/bin/env python3
"""Phase 2 — turn the reviewed manifest into archive entries.

Reads manifest.tsv (the reviewed file — edits to `name`, `cat` and `include`
are respected) plus manifest.json (for the image URLs), then for every included
garment: downloads the first product image, converts it to PNG, resamples it to
house size, and writes

    archive/<nation>/<cat-slug>/<garment-slug>/<garment-slug>.png
    archive/<nation>/<cat-slug>/<garment-slug>/<garment-slug>.txt

Skips any garment whose folder already exists, so it is safe to re-run and to
stop half way.

    python3 ingest.py --limit 50          # first 50, to eyeball the output
    python3 ingest.py                     # the rest
    python3 ingest.py --register          # write the ITEMS lines into archive.html
"""
import argparse, json, os, re, shutil, subprocess, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from naming import slug

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

TXT = """{name}

Nation: {nation_label}
Type: {cat}

Placeholder record. Replace this file with the garment write-up:
issue period, pattern, fabric and construction, and any notes on
provenance or condition.

Source: {store}
Listing: {source_title}
URL: {url}
Size variants seen: {variants}{todo}
"""


def read_manifest(out):
    """TSV is the source of truth for the reviewed columns; JSON supplies the URLs."""
    rows = json.load(open(os.path.join(out, "manifest.json")))
    by_src = {r["url"]: r for r in rows}
    tsv = os.path.join(out, "manifest.tsv")
    merged = []
    with open(tsv, encoding="utf-8") as f:
        cols = f.readline().rstrip("\n").split("\t")
        for line in f:
            vals = line.rstrip("\n").split("\t")
            if len(vals) != len(cols):
                continue
            row = dict(zip(cols, vals))
            base = by_src.get(row["url"])
            if not base:
                continue
            base = dict(base)
            base.update(row)
            merged.append(base)
    return merged


def fetch_image(src, tmp):
    ext = re.sub(r"[^a-z0-9]", "", src.split("?")[0].rsplit(".", 1)[-1].lower())[:4] or "jpg"
    path = f"{tmp}.{ext}"
    r = subprocess.run(["curl", "-s", "-L", "--max-time", "90", "-A", UA, src, "-o", path],
                       capture_output=True)
    if r.returncode != 0 or not os.path.exists(path) or os.path.getsize(path) < 1024:
        return None
    return path


try:
    from PIL import Image
except ImportError:
    Image = None


def to_png(src_path, dest, px, pad_colour=(255, 255, 255)):
    """Convert to a PNG of exactly px x px, on a flat background.

    Pillow rather than sips: one LANCZOS resample straight from the 2400px
    original preserves more detail than sips' default filter, and flattening
    the alpha channel onto white (the product backdrop already is white) drops
    roughly a fifth of the file size for no visible change. Across ~1200
    garments that is the difference between fitting under the GitHub Pages 1 GB
    cap and not.
    """
    if Image is None:
        r = subprocess.run(["sips", "-s", "format", "png", src_path, "--out", dest],
                           capture_output=True)
        if r.returncode != 0 or not os.path.exists(dest):
            return False
        subprocess.run(["sips", "-Z", str(px), dest], capture_output=True)
        subprocess.run(["sips", "--padToHeightWidth", str(px), str(px),
                        "--padColor", "FFFFFF", dest], capture_output=True)
        return True
    try:
        im = Image.open(src_path)
        im.load()
        w, h = im.size
        scale = px / max(w, h)
        im = im.resize((max(1, round(w * scale)), max(1, round(h * scale))),
                       Image.LANCZOS)
        canvas = Image.new("RGB", (px, px), pad_colour)
        mask = im.split()[-1] if im.mode in ("RGBA", "LA") else None
        canvas.paste(im.convert("RGB"),
                     ((px - im.size[0]) // 2, (px - im.size[1]) // 2), mask)
        canvas.save(dest, "PNG", optimize=True)
        return True
    except Exception:
        return False


def supersede(root, nation, names, dry_run=False):
    """Delete archived garments that the new entries replace.

    Removes the garment folder and its ITEMS row. Irreversible in the sense
    that it changes public URLs, so it only ever runs on names the reviewer put
    in the `replaces` column.
    """
    path = os.path.join(root, "archive.html")
    html = open(path, encoding="utf-8").read()
    removed = []
    for name in sorted(set(n for n in names if n.strip())):
        s = slug(name)
        # the ITEMS row, matched on the exact display name
        pat = re.compile(r'\n\s*\{\s*n:\s*"' + re.escape(nation) +
                         r'"\s*,\s*name:\s*"' + re.escape(name) + r'"[^}]*\},')
        hit = pat.search(html)
        folder = None
        ndir = os.path.join(root, "archive", nation)
        if os.path.isdir(ndir):
            for cat in os.listdir(ndir):
                cand = os.path.join(ndir, cat, s)
                if os.path.isdir(cand):
                    folder = cand
                    break
        if not hit and not folder:
            continue
        if dry_run:
            removed.append((name, folder, bool(hit)))
            continue
        if hit:
            html = html[:hit.start()] + html[hit.end():]
        if folder:
            shutil.rmtree(folder)
        removed.append((name, folder, bool(hit)))
    if not dry_run:
        open(path, "w", encoding="utf-8").write(html)
    return removed


def register(root, nation, added):
    """Insert ITEMS entries into archive.html, grouped under the nation comment."""
    path = os.path.join(root, "archive.html")
    html = open(path, encoding="utf-8").read()
    anchor = "    const ITEMS = ["
    i = html.index(anchor) + len(anchor)
    lines = []
    for a in added:
        name = a["name"].replace("\\", "").replace('"', "")
        cat = a["cat"].replace('"', "")
        lines.append(f'\n      {{ n:"{nation}", name:"{name}", cat:"{cat}" }},')
    html = html[:i] + "".join(lines) + html[i:]
    open(path, "w", encoding="utf-8").write(html)
    return len(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--out", default="_incoming/lambrino")
    ap.add_argument("--nation", default="british")
    ap.add_argument("--nation-label", default="British")
    ap.add_argument("--store", default="lambrino.co.uk")
    ap.add_argument("--px", type=int, default=1000, help="output is exactly px by px")
    ap.add_argument("--pad-colour", default="FFFFFF")
    ap.add_argument("--replace-existing", action="store_true",
                    help="for rows whose `replaces` column names an archived garment, "
                         "delete that garment's folder and ITEMS row once the new one is written")
    ap.add_argument("--limit", type=int, default=0, help="stop after N garments")
    ap.add_argument("--register", action="store_true",
                    help="also add the ITEMS entries to archive.html")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    rows = [r for r in read_manifest(a.out) if r.get("include", "").strip().lower() == "y"]
    print(f"{len(rows)} garments marked for ingest")

    tmp = os.path.join(a.out, ".tmp")
    added, skipped, failed = [], 0, []
    for r in rows:
        name = r["name"].strip()
        cat = r["cat"].strip()
        gslug = slug(name)
        d = os.path.join(a.root, "archive", a.nation, slug(cat), gslug)
        png = os.path.join(d, gslug + ".png")
        if os.path.exists(png):
            skipped += 1
            continue
        if a.limit and len(added) >= a.limit:
            break
        if a.dry_run:
            print(f"  would write {png}")
            added.append({"name": name, "cat": cat})
            continue

        src = fetch_image(r["image"], tmp)
        if not src:
            failed.append((name, "download"))
            continue
        os.makedirs(d, exist_ok=True)
        ok = to_png(src, png, a.px, tuple(int(a.pad_colour[i:i+2],16) for i in (0,2,4)))
        os.remove(src)
        if not ok:
            failed.append((name, "convert"))
            continue

        todo = []
        flags = r.get("flags", "")
        if "date-unknown" in flags:
            todo.append("date")
        if "fabric-unknown" in flags:
            todo.append("fabric")
        if "type-from-product-type" in flags:
            todo.append("garment type")
        todo_line = ("\nTo confirm: " + ", ".join(todo)) if todo else ""

        open(os.path.join(d, gslug + ".txt"), "w", encoding="utf-8").write(TXT.format(
            name=name, nation_label=a.nation_label, cat=cat, store=a.store,
            source_title=r.get("source_title", ""), url=r.get("url", ""),
            variants=r.get("variants", ""), todo=todo_line))
        added.append({"name": name, "cat": cat, "replaces": r.get("replaces", "")})
        if len(added) % 25 == 0:
            print(f"  {len(added)} done…")

    print(f"\nadded {len(added)}, already present {skipped}, failed {len(failed)}")
    for n, why in failed[:20]:
        print(f"  FAIL {why}: {n}")

    if a.register and added and not a.dry_run:
        n = register(a.root, a.nation, added)
        print(f"registered {n} items in archive.html")

    # supersede last: never delete an original until its replacement is on disk
    if a.replace_existing:
        gone = supersede(a.root, a.nation, [x["replaces"] for x in added], a.dry_run)
        verb = "would remove" if a.dry_run else "removed"
        print(f"{verb} {len(gone)} superseded garment(s)")
        for name, folder, had_row in gone:
            print(f"  - {name}{'' if folder else '  (no folder)'}"
                  f"{'' if had_row else '  (no ITEMS row)'}")

    json.dump(added, open(os.path.join(a.out, "last-run.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
