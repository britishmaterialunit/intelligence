#!/usr/bin/env python3
"""Pull a named list of lambrino.co.uk products into the archive.

The bulk path (survey.py -> ingest.py) walks a whole collection and needs a
human review pass over a thousand rows. This is the other shape of the job:
a handful of products chosen by hand, one or two per nation, where the list
IS the decision and there is nothing to review.

    python3 fetch_urls.py --urls urls.txt --root .

Each line of the URL file is tab separated:

    <product url>  [nation key]  [name override]

The engine reads a shop title, and a shop title is written to sell rather
than to catalogue. It gets most of the way there; the two override columns
are where the cases it cannot know go — a Czech jacket tagged Czechoslovakia,
a Soviet shirt tagged Russia, a date that lives in the garment's history
rather than in its name. The list is the decision, so the list carries the
corrections rather than the parser growing a special case per garment.

For every product it writes:

    archive/<nation>/<category>/<garment>/<CODE>.png
    archive/<nation>/<category>/<garment>/<CODE>.txt

and prints the archive.html ITEMS rows on stdout.
"""
import argparse, json, os, re, subprocess, sys, tempfile, urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import naming

UA = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) BMU-archive/1.0'

# ---------------------------------------------------------------- nations
# key -> (label, code stem). The stem leads the archive ref; it is two letters
# only where one would collide with a nation already in the archive (Iraqi
# against Italian) or where the label is two words (United States).
NATIONS = {
    'austrian':      ('Austrian',      'A'),
    'belgian':       ('Belgian',       'B'),
    'british':       ('British',       'B'),
    'bulgarian':     ('Bulgarian',     'BU'),
    'chinese':       ('Chinese',       'C'),
    'czechoslovak':  ('Czechoslovak',  'CS'),
    'czech':         ('Czech',         'CZ'),
    'danish':        ('Danish',        'D'),
    'east-german':   ('East German',   'EG'),
    'finnish':       ('Finnish',       'F'),
    'french':        ('French',        'FR'),
    'german':        ('German',        'G'),
    'west-german':   ('West German',   'WG'),
    'greek':         ('Greek',         'GR'),
    'hungarian':     ('Hungarian',     'H'),
    'iraqi':         ('Iraqi',         'IQ'),
    'irish':         ('Irish',         'IR'),
    'israeli':       ('Israeli',       'IS'),
    'italian':       ('Italian',       'I'),
    'dutch':         ('Dutch',         'NL'),
    'norwegian':     ('Norwegian',     'N'),
    'polish':        ('Polish',        'P'),
    'portuguese':    ('Portuguese',    'PT'),
    'romanian':      ('Romanian',      'RO'),
    'russian':       ('Russian',       'R'),
    'soviet':        ('Soviet',        'S'),
    'serbian':       ('Serbian',       'SB'),
    'slovak':        ('Slovak',        'SK'),
    'spanish':       ('Spanish',       'SP'),
    'swedish':       ('Swedish',       'SW'),
    'swiss':         ('Swiss',         'CH'),
    'united-states': ('United States', 'US'),
    'yugoslav':      ('Yugoslav',      'Y'),
}

# Longest first, so "east german" is not read as "german" and "czechoslovak"
# is not read as "czech".
NATION_PATTERNS = sorted(
    [(re.compile(r'\b' + lbl.replace(' ', r'\s+') + r'\b', re.I), key)
     for key, (lbl, _) in NATIONS.items()],
    key=lambda p: -len(p[0].pattern))

DIVISION_WORDS = [
    ('Royal Air Force', 'Royal Air Force'), ('Air Force', 'Air Force'),
    ('Royal Navy', 'Royal Navy'), ('Navy', 'Navy'),
    ('Red Army', 'Red Army'), ('Land Forces', 'Land Forces'),
    ('Civil Defence', 'Civil Defence'), ('Peoples Army', "People's Army"),
    ('Police', 'Police'), ('Army', 'Army'), ('Marines', 'Marines'),
]

# A designation carries its own year for most of these armies: WZ93 is 1993,
# M/84 is 1984, TAZ83 is 1983, M09 is 2009. Reading the decade out of the mark
# beats leaving the slot at 0000s for someone to look up by hand.
DESIG = re.compile(r'\b(?:WZ|TAZ|MK|M|SPE|ANZUG|Type)[\s/\-]?(\d{2})\b', re.I)


def decade_from_designation(text):
    m = DESIG.search(text)
    if not m:
        return None
    n = int(m.group(1))
    # two digits, no century: 00-29 reads as 2000s, the rest as 1900s
    return f'{2000 + n - n % 10}s' if n <= 29 else f'{1900 + n - n % 10}s'


def get(url):
    """Fetched with curl rather than urllib.

    The Pythons that ship with macOS are routinely installed without a CA
    bundle, and urllib then refuses every https URL with
    CERTIFICATE_VERIFY_FAILED. curl uses the system trust store and is
    already on the machine, so it is the transport that actually works
    wherever this runs.
    """
    out = subprocess.run(['curl', '-sSL', '--max-time', '60', '-A', UA, url],
                         capture_output=True)
    if out.returncode != 0:
        raise RuntimeError(out.stderr.decode()[:200] or f'curl exit {out.returncode}')
    return out.stdout


def fetch_json(url):
    return json.loads(get(url.rstrip('/') + '.json'))['product']


def detect_nation(title, tags, override):
    if override:
        return override
    hay = title + ' ' + ' '.join(tags or ())
    for pat, key in NATION_PATTERNS:
        if pat.search(hay):
            return key
    return None


def detect_division(name):
    for pat, out in DIVISION_WORDS:
        if re.search(r'\b' + pat.replace(' ', r'\s+') + r'\b', name, re.I):
            return out
    return ''


def make_code(name, nation_key):
    """(Nation)(Division) + year + initials, designations kept whole.

    "Polish Army 1990s WZ93 Pantera Camouflage Windproof Parka"
      -> PA 1990 WZ93 P C W P  ->  PA1990WZ93PCWP
    """
    stem = NATIONS[nation_key][1]
    label = NATIONS[nation_key][0]

    rest = name
    # the nation is already represented by the stem
    for w in label.split():
        rest = re.sub(r'\b' + re.escape(w) + r'\b', ' ', rest, count=1, flags=re.I)

    out = [stem]
    for tok in rest.split():
        t = tok.strip('/-')
        if not t:
            continue
        if re.fullmatch(r'(?:19|20)\d0s', t):          # the date slot
            out.append(t[:-1])
        elif re.fullmatch(r'[A-Za-z]+\d+|\d+[A-Za-z]+', t):   # WZ93, M84, TAZ83
            out.append(t.upper())
        elif re.fullmatch(r'\d+', t):                  # a bare number belongs to its mark
            out.append(t)
        else:
            out.append(t[0].upper())
    return ''.join(out)


def to_png(src_url, dest):
    """Download and square to 1000x1000 on white, the way the archive holds them."""
    raw = get(src_url)
    ext = '.png' if src_url.lower().split('?')[0].endswith('.png') else '.jpg'
    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as t:
        t.write(raw)
        tmp = t.name
    try:
        subprocess.run(['sips', '-s', 'format', 'png', tmp, '--out', dest],
                       check=True, capture_output=True)
        subprocess.run(['sips', '-z', '1000', '1000', dest],
                       check=True, capture_output=True)
    finally:
        os.unlink(tmp)
    return os.path.getsize(dest)


RECORD = """{name}

Nation: {nation}
Type: {cat}
Archive ref: {code}
Source: Lambrino

Placeholder record. Replace this file with the garment write-up:
issue period, pattern, fabric and construction, and any notes on
provenance or condition.
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--urls', required=True, help='file of product URLs, one per line')
    ap.add_argument('--root', default='.', help='repo root holding archive/')
    ap.add_argument('--dry-run', action='store_true')
    a = ap.parse_args()

    lines = [l.strip() for l in open(a.urls) if l.strip() and not l.startswith('#')]
    items, failed = [], []

    for line in lines:
        parts = [c.strip() for c in line.split('\t')]
        url = parts[0]
        override = parts[1] if len(parts) > 1 and parts[1] else None
        name_override = parts[2] if len(parts) > 2 and parts[2] else None
        try:
            p = fetch_json(url)
        except Exception as e:
            failed.append((url, f'fetch: {e}'))
            continue

        title = p['title']
        tags = [t.strip() for t in (p.get('tags') or '').split(',')] if isinstance(p.get('tags'), str) else list(p.get('tags') or ())
        nation_key = detect_nation(title, tags, override)
        if not nation_key:
            failed.append((url, f'nation unknown for {title!r}'))
            continue
        label = NATIONS[nation_key][0]

        d = naming.derive(title, p.get('product_type', ''), p.get('body_html', ''),
                          tags, nation=label)
        name = d['name']

        # fill the date slot from the designation when the title had no marker
        if '0000s' in name:
            dec = decade_from_designation(title)
            name = name.replace('0000s', dec) if dec else name.replace('0000s ', '')

        # the engine flattens "M/84" to "M 84"; put the mark back together
        name = re.sub(r'\b([A-Z]{1,5})\s+(\d{2,3})\b', r'\1\2', name)
        name = re.sub(r'\s{2,}', ' ', name).strip()

        if name_override:
            name = name_override

        cat = d['cat']
        if re.search(r'\b(?:Rucksack|Bandolier|Chest Rig|Webbing|Bergen|Pouch)\b', name, re.I):
            cat = 'Bags / Webbing'      # a rig is not hardware, whatever the shop filed it under
        code = make_code(name, nation_key)
        folder = os.path.join(a.root, 'archive', nation_key,
                              naming.slug(cat), naming.slug(name))

        images = p.get('images') or []
        if not images:
            failed.append((url, 'no image'))
            continue

        if a.dry_run:
            print(f'{code:22} {name}   [{cat}]')
        else:
            os.makedirs(folder, exist_ok=True)
            dest = os.path.join(folder, code + '.png')
            try:
                size = to_png(images[0]['src'], dest)
            except Exception as e:
                failed.append((url, f'image: {e}'))
                continue
            with open(os.path.join(folder, code + '.txt'), 'w') as f:
                f.write(RECORD.format(name=name, nation=label, cat=cat, code=code))
            print(f'{code:22} {name}   [{cat}]  {size//1024}KB', file=sys.stderr)

        items.append(dict(n=nation_key, name=name, cat=cat, img=code + '.png',
                          ref=code, src='Lambrino'))

    print(json.dumps(items, indent=2))
    if failed:
        print('\n--- could not take ---', file=sys.stderr)
        for u, why in failed:
            print(f'  {why}\n    {u}', file=sys.stderr)


if __name__ == '__main__':
    main()
