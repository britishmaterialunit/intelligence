#!/usr/bin/env python3
"""Phase 1 — survey lambrino.co.uk and build a review manifest.

Downloads nothing but the catalogue JSON. Derives a name for every product,
collapses size variants, checks each garment against what is already in the
archive, and writes a manifest for the user to review before any image is
fetched.

    python3 survey.py --collection britain-uk --nation british

Outputs (into --out, default _incoming/lambrino/):
    catalogue.json   raw products, cached so re-runs are offline
    manifest.tsv     one row per unique garment — the file the user edits
    manifest.json    same data plus image URLs, consumed by ingest.py
"""
import argparse, json, os, re, subprocess, sys, collections

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from naming import derive, resolve, slug

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")


def curl_json(url):
    r = subprocess.run(["curl", "-s", "-L", "--max-time", "60", "-A", UA, url],
                       capture_output=True)
    if r.returncode != 0:
        raise RuntimeError(f"curl failed for {url}")
    return json.loads(r.stdout)


def fetch_catalogue(store, collection, cache, refresh=False):
    """Shopify's products.json — 250 per request instead of 24 per HTML page."""
    if os.path.exists(cache) and not refresh:
        print(f"using cached catalogue {cache}")
        return json.load(open(cache))
    products, page = [], 1
    while True:
        url = f"https://{store}/collections/{collection}/products.json?limit=250&page={page}"
        batch = curl_json(url).get("products", [])
        print(f"  page {page}: {len(batch)}")
        if not batch:
            break
        products += batch
        page += 1
        if page > 200:
            break
    os.makedirs(os.path.dirname(cache) or ".", exist_ok=True)
    json.dump(products, open(cache, "w"))
    print(f"cached {len(products)} products -> {cache}")
    return products


def existing_archive(root, nation):
    """Every garment already in the archive: slug -> display name.

    Reads both the folders on disk and the ITEMS table in archive.html, because
    either one alone can be out of date.
    """
    found = {}
    ndir = os.path.join(root, "archive", nation)
    if os.path.isdir(ndir):
        for cat in os.listdir(ndir):
            cdir = os.path.join(ndir, cat)
            if os.path.isdir(cdir):
                for g in os.listdir(cdir):
                    if not g.startswith("."):
                        found[g] = g
    html_path = os.path.join(root, "archive.html")
    if os.path.exists(html_path):
        html = open(html_path, encoding="utf-8").read()
        for m in re.finditer(r'\{\s*n:\s*"([^"]+)"\s*,\s*name:\s*"([^"]+)"', html):
            if m.group(1) == nation:
                found[slug(m.group(2))] = m.group(2)
    return found


def tokens(s):
    stop = {"british", "the", "with", "and", "a", "of"}
    return {t for t in re.split(r"[^a-z0-9]+", s.lower()) if t and t not in stop}


def nearest(name, existing):
    """Closest existing garment, for the reviewer to eyeball.

    Containment, not Jaccard: archive names are terser than derived ones
    ("British Desert DPM Shirt" vs "British Army Desert DPM UBACS Combat
    Shirt"), so Jaccard buries a real match under the extra tokens. What
    matters is whether the existing garment is essentially a subset of this one.
    """
    best, score = None, 0.0
    tn = tokens(name)
    if not tn:
        return None, 0.0
    for s, disp in existing.items():
        te = tokens(disp)
        if len(te) < 2:
            continue
        c = len(tn & te) / min(len(tn), len(te))
        if c > score:
            best, score = disp, c
    return best, score


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--store", default="lambrino.co.uk")
    ap.add_argument("--collection", default="britain-uk")
    ap.add_argument("--nation", default="british")
    ap.add_argument("--root", default=".")
    ap.add_argument("--out", default="_incoming/lambrino")
    ap.add_argument("--refresh", action="store_true", help="re-fetch the catalogue")
    ap.add_argument("--near", type=float, default=0.72,
                    help="token-overlap above which a garment is flagged as a possible duplicate")
    a = ap.parse_args()

    os.makedirs(a.out, exist_ok=True)
    cache = os.path.join(a.out, "catalogue.json")
    products = fetch_catalogue(a.store, a.collection, cache, a.refresh)

    # products.json can repeat a handle across page boundaries
    seen_handles, uniq = set(), []
    for p in products:
        if p["handle"] not in seen_handles:
            seen_handles.add(p["handle"])
            uniq.append(p)
    print(f"{len(products)} rows -> {len(uniq)} distinct products")

    recs = []
    for p in uniq:
        if not p.get("images"):
            continue
        recs.append({
            "p": p,
            "derived": derive(p["title"], p.get("product_type", ""),
                              p.get("body_html", ""), p.get("tags", ())),
        })
    print(f"{len(recs)} products with images")

    garments = resolve(recs)
    existing = existing_archive(a.root, a.nation)
    print(f"{len(garments)} unique garments; {len(existing)} already in archive")

    rows, stats = [], collections.Counter()
    for g in garments:
        s = slug(g["name"])
        replaces = ""
        if s in existing:
            status = "have"
            replaces = existing[s]
            g["near"] = f"{replaces} (1.00)"
        else:
            near_name, sc = nearest(g["name"], existing)
            status = "check" if sc >= a.near else "new"
            g["near"] = f"{near_name} ({sc:.2f})" if status == "check" else ""
            if status == "check":
                replaces = near_name
        stats[status] += 1
        prim = g["primary"]["p"]
        rows.append({
            "include": "y",
            "status": status,
            "replaces": replaces,
            "name": g["name"],
            "cat": g["cat"],
            "slug": s,
            "variants": len(g["variants"]),
            "flags": ",".join(g["flags"]),
            "near": g.get("near", ""),
            "source_title": prim["title"],
            "url": f"https://{a.store}/products/{prim['handle']}",
            "image": prim["images"][0]["src"],
        })

    cols = ["include", "status", "name", "cat", "variants", "flags", "replaces",
            "near", "source_title", "url"]
    tsv = os.path.join(a.out, "manifest.tsv")
    with open(tsv, "w", encoding="utf-8") as f:
        f.write("\t".join(cols) + "\n")
        for r in rows:
            f.write("\t".join(str(r[c]).replace("\t", " ") for c in cols) + "\n")
    json.dump(rows, open(os.path.join(a.out, "manifest.json"), "w"), indent=1)

    n_inc = sum(1 for r in rows if r["include"] == "y")
    print(f"\n  new    {stats['new']}\n  check  {stats['check']}\n  have   {stats['have']}")
    print(f"\nflags:")
    fc = collections.Counter(f for r in rows for f in r["flags"].split(",") if f)
    for k, v in fc.most_common():
        print(f"  {v:5d}  {k}")
    n_rep = sum(1 for r in rows if r["replaces"])
    print(f"\nmanifest -> {tsv}")
    print(f"{n_rep} rows would supersede an archived garment")
    # ~774 KB measured for a 1000x1000 flattened PNG off this store
    print(f"projected ~{n_inc * 774 / 1024 / 1024:.2f} GB at 1000x1000 "
          f"({n_inc} images) — GitHub Pages caps a site at 1 GB")


if __name__ == "__main__":
    main()
