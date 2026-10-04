#!/usr/bin/env python3
"""
Build one crawlable page per garment, plus the sitemap and robots.txt.

WHY THIS EXISTS
---------------
The archive is one document. Every garment lives at /archive, is drawn by
script into a canvas, and has no address of its own. Google Images needs an
address to attribute a picture to, text around the picture to read it by, and
a route to find it. The archive gave it none of the three, which is why a
garment that is almost one of one still does not come up while the shop it
was bought from does: their every product is its own URL with the photograph
in the HTML and a description beside it.

This writes that page for every garment, into the folder the photograph and
the record already sit in, so the address is the one the archive already uses
for the picture:

    archive/<nation>/<type>/<garment>/index.html   ->  /archive/<nation>/<type>/<garment>/

The folders ARE the archive; this only adds a front door to each one. Re-run
it after adding garments. It overwrites its own output and touches nothing
else.

    python3 tools/seo_build.py            # write
    python3 tools/seo_build.py --dry-run  # say what it would write
"""

import argparse, html, io, json, os, re, sys

SITE = 'https://britishmaterialunit.com'
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Pages that are not garments, with the priority they carry in the sitemap.
STATIC = [
    ('/',           '1.0', 'weekly'),
    ('/archive',    '0.9', 'weekly'),
    ('/repository', '0.8', 'monthly'),
    ('/files',      '0.4', 'monthly'),
    ('/contact',    '0.7', 'monthly'),
    ('/ew',         '0.6', 'monthly'),
    ('/ou',         '0.6', 'monthly'),
    ('/privacy',    '0.3', 'yearly'),
]


def slug(name):
    """The archive's own slugBase(), so the paths match what it already asks for."""
    s = name.lower().replace('’', '').replace("'", '')
    s = re.sub(r'[^a-z0-9]+', '-', s)
    return s.strip('-')


def read_items(path):
    """ITEMS out of archive.html. The array is the list of what is published;
    a folder on disk that is not in it is not in the archive."""
    s = io.open(path, encoding='utf-8').read()
    i = s.find('const ITEMS = [')
    j = s.find('\n    ];', i)
    if i < 0 or j < 0:
        sys.exit('archive.html: could not find ITEMS')
    block = s[i:j]
    rows = []
    for m in re.finditer(
            r'\{\s*n:"(?P<n>[^"]+)",\s*name:"(?P<name>[^"]+)",\s*cat:"(?P<cat>[^"]+)",\s*'
            r'img:"(?P<img>[^"]+)",\s*ref:"(?P<ref>[^"]+)"(?:,\s*mat:"(?P<mat>[^"]*)")?',
            block):
        rows.append(m.groupdict())
    return rows


def read_nations(path):
    s = io.open(path, encoding='utf-8').read()
    i = s.find('const NATIONS = [')
    j = s.find('\n    ];', i)
    out = {}
    for m in re.finditer(r'key:"([^"]+)",\s*label:"([^"]+)"', s[i:j]):
        out[m.group(1)] = m.group(2)
    return out


def read_record(txt_path):
    """A record is: title, a Nation/Type/ref block, the prose, then the source
    list under a --- rule. The prose is what a reader wants and what a search
    engine reads; the list is the measurements, which is the long tail."""
    if not os.path.exists(txt_path):
        return [], []
    raw = io.open(txt_path, encoding='utf-8').read()
    body, _, tail = raw.partition('\n---\n')
    lines = body.split('\n')
    # drop the title and the Nation:/Type:/Archive ref:/Source: block
    keep = []
    for ln in lines[1:]:
        if re.match(r'^(Nation|Type|Archive ref|Source):', ln.strip()):
            continue
        keep.append(ln)
    prose = [p.strip() for p in '\n'.join(keep).split('\n\n') if p.strip()]
    prose = [p for p in prose if not p.startswith('Placeholder record')]
    specs = [l.strip() for l in tail.split('\n') if l.strip()]
    return prose, specs


def era_of(name):
    m = re.search(r'\b((?:1[89]|20)\d0s)\b', name)
    return m.group(1) if m else ''


def clip(text, n=158):
    text = re.sub(r'\s+', ' ', text).strip()
    if len(text) <= n:
        return text
    cut = text[:n].rsplit(' ', 1)[0]
    return cut.rstrip(',;:.') + '…'


PAGE = '''<!DOCTYPE html>
<html lang="en-GB">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover" />
<title>{title_esc} | BMU Archive</title>
<meta name="description" content="{desc_esc}" />
<link rel="canonical" href="{url}" />
<link rel="icon" href="/bmufavicon.svg" type="image/svg+xml" />
<meta name="robots" content="index, follow, max-image-preview:large" />
<meta name="author" content="British Material Unit (BMU)" />

<meta property="og:type" content="product" />
<meta property="og:site_name" content="British Material Unit (BMU)" />
<meta property="og:locale" content="en_GB" />
<meta property="og:url" content="{url}" />
<meta property="og:title" content="{title_esc}" />
<meta property="og:description" content="{desc_esc}" />
<meta property="og:image" content="{img_url}" />
<meta property="og:image:alt" content="{alt_esc}" />
<meta name="twitter:card" content="summary_large_image" />
<meta name="twitter:title" content="{title_esc}" />
<meta name="twitter:description" content="{desc_esc}" />
<meta name="twitter:image" content="{img_url}" />

<link rel="preconnect" href="https://fonts.googleapis.com" />
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter+Tight:wght@400;700&display=swap" />

<script type="application/ld+json">
{jsonld}
</script>

<style>
  :root{{ --ink:#222; --line:#222; --bg:#fff; --faint:#f5f5f5;
          --font:'Inter Tight', Helvetica, Arial, sans-serif; }}
  *{{ box-sizing:border-box; }}
  body{{ margin:0; background:var(--bg); color:var(--ink); font-family:var(--font);
        font-size:13px; line-height:1.7; -webkit-font-smoothing:antialiased; }}
  .wrap{{ width:min(92vw, 1100px); margin:0 auto; padding:56px 0 80px; }}
  a{{ color:var(--ink); }}
  .crumb{{ font-size:10px; letter-spacing:.18em; text-transform:uppercase; color:#9a9a9a; }}
  .crumb a{{ color:#9a9a9a; text-decoration:none; }}
  .crumb a:hover{{ color:var(--ink); }}
  h1{{ margin:16px 0 0; font-size:clamp(26px, 4.4vw, 42px); font-weight:400;
      letter-spacing:-.01em; line-height:1.1; }}
  .ref{{ margin:10px 0 0; font-size:10px; letter-spacing:.2em; color:#9a9a9a; }}
  .cols{{ display:grid; grid-template-columns:minmax(0,1fr) minmax(0,1fr); gap:44px;
         align-items:start; margin-top:34px; }}
  figure{{ margin:0; }}
  figure img{{ display:block; width:100%; height:auto; border:1.5px solid #ececec; }}
  figcaption{{ margin-top:10px; font-size:10.5px; color:#9a9a9a; }}
  .prose p{{ margin:0 0 14px; max-width:60ch; }}
  h2{{ margin:30px 0 12px; font-size:10px; font-weight:400; letter-spacing:.22em;
      text-transform:uppercase; color:#9a9a9a; }}
  dl{{ margin:0; display:grid; grid-template-columns:auto 1fr; gap:6px 18px; font-size:12px; }}
  dt{{ color:#9a9a9a; }}
  dd{{ margin:0; }}
  ul.specs{{ margin:0; padding:0; list-style:none; font-size:12px; }}
  ul.specs li{{ padding:5px 0; border-bottom:1px solid #f0f0f0; }}
  .back{{ display:inline-block; margin-top:40px; padding:10px 16px; border:1.5px solid var(--line);
         font-size:11px; letter-spacing:.16em; text-transform:uppercase; text-decoration:none; }}
  .back:hover{{ background:var(--faint); }}
  .near{{ margin-top:46px; padding-top:22px; border-top:1px solid #ececec; font-size:12px; }}
  .near ul{{ margin:10px 0 0; padding:0; list-style:none; columns:2; column-gap:34px; }}
  .near li{{ padding:3px 0; break-inside:avoid; }}
  @media (max-width:760px){{
    .cols{{ grid-template-columns:minmax(0,1fr); gap:28px; }}
    .near ul{{ columns:1; }}
  }}
</style>
</head>
<body>
  <main class="wrap">
    <nav class="crumb" aria-label="Breadcrumb">
      <a href="/">BMU</a> / <a href="/archive">Archive</a> / {nation_esc}
    </nav>

    <h1>{title_esc}</h1>
    <p class="ref">{ref_esc}</p>

    <div class="cols">
      <figure>
        <img src="{img_path}" alt="{alt_esc}" width="1000" height="1000" />
        <figcaption>{alt_esc}</figcaption>
      </figure>

      <div>
        <div class="prose">
{prose_html}
        </div>

        <h2>Record</h2>
        <dl>
{facts_html}
        </dl>
{specs_html}
        <a class="back" href="/archive">Open in the archive</a>
      </div>
    </div>

{near_html}
  </main>
</body>
</html>
'''


def build_page(it, nations, siblings):
    nation = nations.get(it['n'], it['n'].title())
    name   = it['name']
    cat    = it['cat']
    ref    = it['ref']
    mat    = it.get('mat') or ''
    era    = era_of(name)

    d = os.path.join(ROOT, 'archive', it['n'], slug(cat), slug(name))
    rel = '/archive/%s/%s/%s/' % (it['n'], slug(cat), slug(name))
    url = SITE + rel
    img_path = rel + it['img']
    img_url  = SITE + img_path

    prose, specs = read_record(os.path.join(d, ref + '.txt'))
    alt = '%s — %s military surplus %s, archive ref %s' % (
        name, nation, cat.lower().rstrip('s') if cat else 'garment', ref)
    desc = clip(prose[0]) if prose else clip(
        '%s. %s military surplus held in the British Material Unit archive, '
        'available for sourcing and production runs.' % (name, nation))

    facts = [('Nation', nation), ('Type', cat), ('Archive ref', ref)]
    if era: facts.append(('Era', era))
    if mat: facts.append(('Material', mat))

    product = {
        '@context': 'https://schema.org',
        '@type': 'Product',
        'name': name,
        'sku': ref,
        'description': desc,
        'category': '%s > %s' % (nation, cat),
        'url': url,
        'image': {
            '@type': 'ImageObject',
            'contentUrl': img_url,
            'url': img_url,
            'caption': alt,
            'name': name,
            'width': 1000,
            'height': 1000,
            'representativeOfPage': True,
            'license': SITE + '/privacy',
            'acquireLicensePage': SITE + '/contact',
            'creditText': 'British Material Unit (BMU)',
            'copyrightNotice': 'British Material Unit (BMU)',
        },
        'brand': {'@type': 'Organization', 'name': nation + ' military surplus'},
        'isPartOf': {'@type': 'Collection', 'name': 'BMU Archive', 'url': SITE + '/archive'},
    }
    if mat:
        product['material'] = mat
    if specs:
        product['additionalProperty'] = [
            {'@type': 'PropertyValue', 'name': 'Detail', 'value': s} for s in specs[:20]
        ]

    crumbs = {
        '@context': 'https://schema.org',
        '@type': 'BreadcrumbList',
        'itemListElement': [
            {'@type': 'ListItem', 'position': 1, 'name': 'British Material Unit', 'item': SITE + '/'},
            {'@type': 'ListItem', 'position': 2, 'name': 'Archive', 'item': SITE + '/archive'},
            {'@type': 'ListItem', 'position': 3, 'name': nation},
            {'@type': 'ListItem', 'position': 4, 'name': name, 'item': url},
        ],
    }

    e = lambda t: html.escape(t, quote=True)
    prose_html = '\n'.join('          <p>%s</p>' % html.escape(p) for p in prose) or \
                 '          <p>%s</p>' % html.escape(desc)
    facts_html = '\n'.join('          <dt>%s</dt><dd>%s</dd>' % (e(k), e(v)) for k, v in facts)
    specs_html = ''
    if specs:
        specs_html = '\n        <h2>At a glance</h2>\n        <ul class="specs">\n' + \
            '\n'.join('          <li>%s</li>' % html.escape(s) for s in specs) + \
            '\n        </ul>\n'

    near_html = ''
    if siblings:
        near_html = ('    <nav class="near" aria-label="More from this nation">\n'
                     '      <h2>More %s in the archive</h2>\n      <ul>\n' % e(nation) +
                     '\n'.join('        <li><a href="%s">%s</a></li>' % (h, e(n))
                               for h, n in siblings) +
                     '\n      </ul>\n    </nav>\n')

    return d, PAGE.format(
        title_esc=e(name), desc_esc=e(desc), alt_esc=e(alt), nation_esc=e(nation),
        ref_esc=e(ref), url=url, img_url=img_url, img_path=img_path,
        prose_html=prose_html, facts_html=facts_html, specs_html=specs_html,
        near_html=near_html,
        jsonld=json.dumps([product, crumbs], indent=2, ensure_ascii=False),
    ), rel, img_url, alt


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dry-run', action='store_true')
    a = ap.parse_args()

    arch = os.path.join(ROOT, 'archive.html')
    items = read_items(arch)
    nations = read_nations(arch)
    if not items:
        sys.exit('no garments found')

    by_nation = {}
    for it in items:
        by_nation.setdefault(it['n'], []).append(it)

    written, entries = 0, []
    for it in items:
        sibs = [('/archive/%s/%s/%s/' % (o['n'], slug(o['cat']), slug(o['name'])), o['name'])
                for o in by_nation[it['n']] if o['ref'] != it['ref']][:12]
        d, page, rel, img_url, alt = build_page(it, nations, sibs)
        if not os.path.isdir(d):
            print('  ! no folder for %s (%s)' % (it['ref'], d))
            continue
        entries.append((rel, img_url, alt, it['name']))
        if a.dry_run:
            print('  would write %s/index.html' % d)
        else:
            io.open(os.path.join(d, 'index.html'), 'w', encoding='utf-8').write(page)
        written += 1

    # ---- the way in, on the archive page itself ----
    # The archive is drawn by script. Without a list of links in the HTML
    # there is nothing on /archive pointing at any of these pages, and a
    # sitemap alone is a weaker signal than a sitemap plus a crawl path.
    # It sits in <noscript> because that is exactly what it is: what this
    # page offers somebody — or something — that is not running the script.
    links = '\n'.join(
        '        <li><a href="%s">%s</a></li>' % (rel, html.escape(name))
        for rel, _img, _alt, name in entries)
    block = ('      <ul>\n' + links + '\n      </ul>')
    arch_src = io.open(arch, encoding='utf-8').read()
    m = re.search(r'(<!-- BMU-SEO-INDEX start.*?<ul>\n)(.*?)(\n?      </ul>)',
                  arch_src, re.S)
    if not m:
        print('  ! no BMU-SEO-INDEX block in archive.html — index not updated')
    else:
        new_src = arch_src[:m.start(1)] + m.group(1) + links + '\n      </ul>' + arch_src[m.end(3):]
        if a.dry_run:
            print('  would write %d links into archive.html' % len(entries))
        else:
            io.open(arch, 'w', encoding='utf-8').write(new_src)

    # ---- sitemap, with the pictures named in it ----
    out = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"',
           '        xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">']
    for loc, pri, freq in STATIC:
        out += ['  <url>', '    <loc>%s%s</loc>' % (SITE, loc),
                '    <changefreq>%s</changefreq>' % freq,
                '    <priority>%s</priority>' % pri, '  </url>']
    for rel, img_url, alt, name in entries:
        out += ['  <url>', '    <loc>%s%s</loc>' % (SITE, rel),
                '    <changefreq>monthly</changefreq>',
                '    <priority>0.7</priority>',
                '    <image:image>',
                '      <image:loc>%s</image:loc>' % html.escape(img_url),
                '      <image:title>%s</image:title>' % html.escape(name),
                '      <image:caption>%s</image:caption>' % html.escape(alt),
                '    </image:image>', '  </url>']
    out.append('</urlset>')
    sitemap = '\n'.join(out) + '\n'

    robots = ('User-agent: *\n'
              'Allow: /\n'
              '\n'
              '# the old variants kept beside the live pages are not the site\n'
              'Disallow: /_incoming/\n'
              'Disallow: /setup/\n'
              '\n'
              'Sitemap: %s/sitemap.xml\n' % SITE)

    if a.dry_run:
        print('  would write sitemap.xml (%d urls) and robots.txt' % (len(STATIC) + len(entries)))
    else:
        io.open(os.path.join(ROOT, 'sitemap.xml'), 'w', encoding='utf-8').write(sitemap)
        io.open(os.path.join(ROOT, 'robots.txt'), 'w', encoding='utf-8').write(robots)

    print('%s %d garment pages, %d sitemap urls'
          % ('would write' if a.dry_run else 'wrote', written, len(STATIC) + len(entries)))


if __name__ == '__main__':
    main()
