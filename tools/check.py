#!/usr/bin/env python3
"""Does the register agree with the disk? Run it before a push.

    python3 tools/check.py

Checks, in the order they bite:

  * archive.html's inline script parses at all          (a typo kills the page)
  * every ITEMS entry has the photograph it names
  * every ITEMS entry resolves to the folder its name and type derive
  * no two garments share a ref
  * every nation in NATIONS has its flag
  * every garment folder on disk is in ITEMS            (an unregistered
    folder is invisible: no card, no page, no sitemap entry)

A missing .txt is NOT an error. The live page holds records back and
seo_build falls back to a generic description, so a garment is complete with
its photograph and its ITEMS entry. They are listed at the end as a count,
for anyone who wants to go and write them.
"""

import io
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARCHIVE_HTML = os.path.join(ROOT, 'archive.html')


def slug(name):
    s = name.lower()
    s = re.sub(r"[’']", '', s)
    s = re.sub(r'[^a-z0-9]+', '-', s)
    return s.strip('-')


def main():
    page = io.open(ARCHIVE_HTML, encoding='utf-8').read()
    bad = []

    # ---- the script has to run, or none of the rest matters -------------
    node = subprocess.run(
        ['node', '-e',
         "const s=require('fs').readFileSync(process.argv[1],'utf8')"
         ".match(/<script>([\\s\\S]*?)<\\/script>/)[1]; new Function(s);",
         ARCHIVE_HTML],
        stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    if node.returncode:
        err = node.stderr.decode().strip().splitlines()
        print('archive.html\'s script does not parse — the page is dead:')
        for ln in err[:6]:
            print('   ', ln)
        return 1
    print('script parses')

    # ---- the register ---------------------------------------------------
    items = []
    for m in re.finditer(
            r'\{\s*n:"([^"]+)",\s*name:"([^"]+)",\s*cat:"([^"]+)",\s*'
            r'(?:img:"([^"]+)",\s*)?(?:ref:"([^"]+)",\s*)?mat:"([^"]+)"', page):
        items.append(dict(n=m.group(1), name=m.group(2), cat=m.group(3),
                          img=m.group(4), ref=m.group(5), mat=m.group(6)))

    on_disk = set()
    no_record = []
    seen_ref = {}
    for p in items:
        f = p['img'] or (slug(p['name']) + '.png')
        d = os.path.join('archive', p['n'], slug(p['cat']), slug(p['name']))
        on_disk.add(d)
        full = os.path.join(ROOT, d, f)
        if not os.path.exists(full):
            bad.append('no photograph for "%s"\n    expected %s'
                       % (p['name'], os.path.join(d, f)))
        if not os.path.exists(os.path.join(ROOT, d, re.sub(r'\.png$', '.txt', f))):
            no_record.append(p['name'])
        if p['ref']:
            if p['ref'] in seen_ref:
                bad.append('ref %s is on two garments:\n    %s\n    %s'
                           % (p['ref'], seen_ref[p['ref']], p['name']))
            seen_ref[p['ref']] = p['name']

    # ---- flags ----------------------------------------------------------
    for m in re.finditer(r'key:"([^"]+)".*?flag:"([^"]+)"', page):
        if not os.path.exists(os.path.join(ROOT, 'flags', m.group(2))):
            bad.append('no flag for %s — flags/%s' % (m.group(1), m.group(2)))

    # ---- folders nobody registered --------------------------------------
    base = os.path.join(ROOT, 'archive')
    stray = []
    for nation in sorted(os.listdir(base)):
        np = os.path.join(base, nation)
        if not os.path.isdir(np):
            continue
        for cat in sorted(os.listdir(np)):
            cp = os.path.join(np, cat)
            if not os.path.isdir(cp):
                continue
            for g in sorted(os.listdir(cp)):
                gp = os.path.join(cp, g)
                if not os.path.isdir(gp):
                    continue
                rel = os.path.join('archive', nation, cat, g)
                if rel not in on_disk:
                    pics = [f for f in os.listdir(gp) if f.lower().endswith('.png')]
                    stray.append((rel, pics))

    for rel, pics in stray:
        bad.append('not in ITEMS, so invisible on the site: %s\n    %s'
                   % (rel, (', '.join(pics) if pics else 'no photograph either')))

    # ---- say it ---------------------------------------------------------
    print('%d garments in ITEMS' % len(items))
    if no_record:
        print('%d without a .txt — fine, the page does not need one' % len(no_record))
    if bad:
        print('\n%d problem%s:' % (len(bad), '' if len(bad) == 1 else 's'))
        for b in bad:
            print('  - %s' % b)
        return 1
    print('\nnothing wrong — safe to push')
    return 0


if __name__ == '__main__':
    sys.exit(main())
