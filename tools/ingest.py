#!/usr/bin/env python3
"""Take photographs out of _incoming/ and turn them into archive entries.

    _incoming/German Army 1990s Flecktarn Parka Hood [GA1990FPH].png
    python3 tools/ingest.py

    -> archive/german/headwear/german-army-1990s-flecktarn-parka-hood/GA1990FPH.png
    -> an ITEMS entry written into archive.html
    -> seo_build.py run over the result

The filename IS the garment's name, so the capitalisation you type is the
capitalisation that is published — DPM, M93, KL and NBC all survive, which
is the one thing deriving a name back out of a folder slug cannot do.

    Name [REF].png            the ref, and the filename it is saved as
    Name {Wool}.png           the material facet; Unlisted when left off
    Name.png                  ref derived from the name, material Unlisted
    _incoming/dutch/Name.png  a subfolder overrides the nation

Nothing is written without --write. The default run prints what it would do.
A .txt record is NOT required: the live page holds records back and
seo_build falls back to a generic description, so a garment is complete with
its photograph and its ITEMS entry. Write one when there is something to say.
"""

import io
import os
import re
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARCHIVE_HTML = os.path.join(ROOT, 'archive.html')
INCOMING = os.path.join(ROOT, '_incoming')
PX = 1000                      # every photograph in the archive is 1000 square

PICTURES = ('.png', '.jpg', '.jpeg', '.webp', '.tif', '.tiff')


# ---------------------------------------------------------------- the page

def slug(name):
    """Exactly archive.html's own slug(), or the paths will not match.

    name.toLowerCase().replace(/[’']/g,'').replace(/[^a-z0-9]+/g,'-')
        .replace(/^-+|-+$/g,'')
    """
    s = name.lower()
    s = re.sub(r"[’']", '', s)
    s = re.sub(r'[^a-z0-9]+', '-', s)
    return s.strip('-')


def read_page():
    return io.open(ARCHIVE_HTML, encoding='utf-8').read()


def nations(page):
    """[(key, label, [aliases])] straight off NATIONS, so this tool cannot
    drift away from the page it is writing into."""
    block = page[page.index('const NATIONS = ['):]
    block = block[:block.index('\n    ];')]
    out = []
    for m in re.finditer(r'\{\s*key:"([^"]+)",\s*label:"([^"]+)"', block):
        key, label = m.group(1), m.group(2)
        tail = block[m.end():m.end() + 400]
        al = re.search(r'alias:\[([^\]]*)\]', tail)
        aliases = re.findall(r'"([^"]+)"', al.group(1)) if al else []
        out.append((key, label, aliases))
    return out


def cats(page):
    block = page[page.index('const CATS = ['):]
    block = block[:block.index('];')]
    return re.findall(r'"([^"]+)"', block)


# ------------------------------------------------------------ what it is

# Longest first, so "Armour Covers" is tested before "Coats" can claim a
# coat cover and "Greatcoats" before "Coats" takes the greatcoat.
KEYWORDS = [
    ('Armour Covers', ['armour cover', 'armor cover', 'plate carrier cover', 'osprey cover']),
    ('Greatcoats',    ['greatcoat']),
    ('Coveralls',     ['coverall', 'boiler suit', 'flight suit', 'bib']),
    ('Headwear',      ['hat', 'cap', 'helmet', 'boonie', 'beret', 'hood', 'balaclava', 'ushanka']),
    ('Footwear',      ['boot', 'shoe', 'gaiter', 'puttee', 'sock']),
    ('Pouches',       ['pouch', 'case', 'holster', 'ammo pocket']),
    ('Webbing',       ['webbing', 'yoke', 'belt kit', 'chest rig', 'bandolier', 'harness', 'brace']),
    ('Bags',          ['bag', 'bergen', 'rucksack', 'pack', 'holdall', 'duffle', 'satchel']),
    ('Smocks',        ['smock', 'anorak']),
    ('Parkas',        ['parka']),
    ('Coats',         ['coat', 'trench']),
    ('Fleeces',       ['fleece']),
    ('Pullovers',     ['pullover', 'jumper', 'norgie', 'sweater', 'sweatshirt']),
    ('Polos',         ['polo']),
    ('Liners',        ['liner']),
    ('Vests',         ['vest', 'tabard']),
    ('Trousers',      ['trouser', 'trousers', 'short', 'shorts', 'salopette']),
    ('Shirts',        ['shirt', 't-shirt', 'tee']),
    ('Jackets',       ['jacket', 'blouson']),
    ('Hardware',      ['tool', 'torch', 'compass', 'bottle', 'canteen', 'stove',
                       'basha', 'sleeping', 'bivvy', 'net', 'glove', 'gauntlet',
                       'mitten', 'goggle', 'mask', 'respirator']),
]

# Nothing is dropped. The refs in the archive keep every word of the name —
# "Parka With Thermal Liner" is WTL, not TL — so taking words out to make a
# ref read better would put this tool out of step with the register.
SKIP_IN_REF = set()

# The arm of service, as the refs already written spell it: BRAF is British
# + Royal + Air Force, NLRA is Dutch + Royal Army, USMC is United States +
# Marine Corps, FRPM is French + Police Municipale, SRA is Soviet + Red Army.
# Longest phrase first — "air force" has to be tried before "air".
SERVICE = [
    ('peoples liberation army', 'PLA'),
    ("people's liberation army", 'PLA'),
    ('marine corps',    'MC'),
    ('defence force',   'DF'),
    ('defense force',   'DF'),
    ('civil defence',   'CD'),
    ('civil defense',   'CD'),
    ('tri-services',    'T'),
    ('tri services',    'T'),
    ('air force',       'AF'),
    ('red army',        'RA'),
    ('peoples army',    'PA'),
    ("people's army",   'PA'),
    ('municipale',      'M'),
    ('gendarmerie',     'G'),
    ('royal',           'R'),
    ('police',          'P'),
    ('marine',          'M'),
    ('army',            'A'),
    ('navy',            'N'),
]


def service_code(rest):
    """The service words leading a name, and what is left after them.
    'Royal Air Force 1980s MK3...' -> ('RAF', '1980s MK3...')"""
    code = ''
    moved = True
    while moved:
        moved = False
        low = rest.lower()
        for word, c in SERVICE:
            if low.startswith(word) and (len(low) == len(word) or
                                         not low[len(word)].isalnum()):
                code += c
                rest = rest[len(word):].lstrip(' -')
                moved = True
                break
    return code, rest


def guess_cat(name):
    low = ' ' + name.lower() + ' '
    for cat, words in KEYWORDS:
        for w in words:
            if re.search(r'[\s\-]' + re.escape(w) + r's?[\s\-]', low):
                return cat
    return None


def guess_nation(name, nats):
    """Longest label first: 'East German' and 'United States' have to beat
    'German' and 'United'."""
    low = name.lower()
    for key, label, aliases in sorted(nats, key=lambda n: -len(n[1])):
        if low.startswith(label.lower() + ' '):
            return key, label
    for key, label, aliases in sorted(nats, key=lambda n: -max(len(a) for a in (n[2] or ['']))):
        for a in aliases:
            if a and low.startswith(a.lower() + ' '):
                return key, label
    return None, None


def nation_prefix(key, nats, page):
    """What this nation's refs begin with, read off the refs already in
    ITEMS. NATIONS.abbr cannot be used: British is UK on screen and B in
    every ref it has — BA, BRAF, BRN, BT.

    For each garment of this nation, work the arm of service out of its
    NAME, take that off the front of its ref, and whatever is left is the
    nation. Greek Army -> GRA less A is GR. Slovak Air Force -> SKAF less
    AF is SK, and Slovak Army -> SKA less A is SK, which agree. Majority
    wins, so one oddly-coded garment cannot move the rest.
    """
    label = dict((k, l) for k, l, _ in nats).get(key, '')
    votes = {}
    pat = (r'n:"%s", name:"([^"]+)", cat:"[^"]+",\s*\n?\s*img:"[^"]+", ref:"([A-Z]+)'
           % re.escape(key))
    for m in re.finditer(pat, page):
        name, alpha = m.group(1), m.group(2)
        rest = name[len(label):].strip() if name.lower().startswith(label.lower()) else name
        code, _ = service_code(rest)
        got = alpha[:-len(code)] if code and alpha.endswith(code) else alpha
        if got:
            votes[got] = votes.get(got, 0) + 1
    if votes:
        return sorted(votes.items(), key=lambda kv: (-kv[1], -len(kv[0])))[0][0]
    m = re.search(r'\{\s*key:"%s".*?abbr:"([^"]+)"' % re.escape(key), page, re.S)
    return m.group(1) if m else key[:2].upper()


def derive_ref(name, key, nats, page):
    """nation + arm of service + decade + the initials of everything else.
    BRAF1980AFFTBLP, NLRA1980KOGFS, FRA1990CCF2J."""
    label = dict((k, l) for k, l, _ in nats).get(key, '')
    rest = name[len(label):].strip() if name.lower().startswith(label.lower()) else name

    svc, rest = service_code(rest)

    decade = ''
    m = re.search(r'\b((?:1[89]|20)\d0)s\b', rest)
    if m:
        decade = m.group(1)
        rest = (rest[:m.start()] + ' ' + rest[m.end():]).strip()

    # "No.1" and "No.2" are one word in the refs that have them: N, not N1
    rest = re.sub(r'\bNo\.?\s*\d+', 'No', rest, flags=re.I)

    tail = ''
    for w in re.findall(r"[A-Za-z0-9\u2019']+", rest):
        if w.lower() in SKIP_IN_REF:
            continue
        tail += w.upper() if re.search(r'\d', w) else w[0].upper()
    return nation_prefix(key, nats, page) + svc + decade + tail


# ------------------------------------------------------------ the picture

def to_png(src, dest):
    """1000 square PNG. sips is on every Mac; Pillow if it happens to be
    installed; otherwise a straight copy with a word about it."""
    if shutil.which('sips'):
        r = subprocess.run(['sips', '-s', 'format', 'png', '-z', str(PX), str(PX),
                            src, '--out', dest],
                           stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        if r.returncode == 0:
            return True
    try:
        from PIL import Image
        im = Image.open(src).convert('RGB')
        im = im.resize((PX, PX), Image.LANCZOS)
        im.save(dest, 'PNG')
        return True
    except Exception:
        pass
    shutil.copy2(src, dest)
    print('      ! copied as-is — could not resample (no sips, no Pillow)')
    return False


# ------------------------------------------------------------- the entry

def insert_item(page, entry, key):
    """After that nation's last entry, so the file stays grouped the way it
    reads. A nation with no entries yet goes on the end of ITEMS — the page
    groups by nation when it renders, so the position is cosmetic."""
    hits = list(re.finditer(r'^      \{ n:"%s",.*?\n(?:^        .*?\n)*' % re.escape(key),
                            page, re.M))
    if hits:
        at = hits[-1].end()
        return page[:at] + entry + page[at:]
    end = page.index('\n    ];', page.index('const ITEMS = ['))
    return page[:end + 1] + entry + page[end + 1:]


def parse_name(stem):
    """'Name [REF] {Material}' in any order after the name."""
    ref = mat = None
    m = re.search(r'\[([A-Za-z0-9]+)\]', stem)
    if m:
        ref = m.group(1).upper()
        stem = stem.replace(m.group(0), ' ')
    m = re.search(r'\{([^}]+)\}', stem)
    if m:
        mat = m.group(1).strip().title()
        stem = stem.replace(m.group(0), ' ')
    return re.sub(r'\s+', ' ', stem).strip(), ref, mat


def main():
    write = '--write' in sys.argv
    force = '--force' in sys.argv

    if not os.path.isdir(INCOMING):
        os.makedirs(INCOMING)
    files = sorted(f for f in os.listdir(INCOMING)
                   if f.lower().endswith(PICTURES) and not f.startswith('.'))
    subs = []
    for d in sorted(os.listdir(INCOMING)):
        p = os.path.join(INCOMING, d)
        if os.path.isdir(p) and not d.startswith('.'):
            for f in sorted(os.listdir(p)):
                if f.lower().endswith(PICTURES) and not f.startswith('.'):
                    subs.append((d, f))

    if not files and not subs:
        print('_incoming is empty — nothing to do.')
        print('Name a photograph as the garment and drop it in, e.g.')
        print('  _incoming/German Army 1990s Flecktarn Parka Hood [GA1990FPH].png')
        return 0

    page = read_page()
    nats = nations(page)
    valid = cats(page)
    known_refs = set(re.findall(r'ref:"([^"]+)"', page))

    jobs, problems = [], []
    for sub, f in [(None, f) for f in files] + subs:
        src = os.path.join(INCOMING, sub, f) if sub else os.path.join(INCOMING, f)
        stem = os.path.splitext(f)[0]
        name, ref, mat = parse_name(stem)

        if sub:
            key = sub.lower()
            label = dict((k, l) for k, l, _ in nats).get(key)
            if not label:
                problems.append((f, 'subfolder "%s" is not a nation in NATIONS' % sub))
                continue
        else:
            key, label = guess_nation(name, nats)
            if not key:
                problems.append((f, 'no nation at the front of the name. Start it '
                                    'with one from NATIONS, or put the file in '
                                    '_incoming/<nation>/'))
                continue

        cat = guess_cat(name)
        if not cat:
            problems.append((f, 'cannot tell the garment type from the name — add a '
                                'word like jacket, trousers, bag, cap'))
            continue
        if cat not in valid:
            problems.append((f, 'type "%s" is not in CATS' % cat))
            continue

        ref = ref or derive_ref(name, key, nats, page)
        d = os.path.join('archive', key, slug(cat), slug(name))
        exists = os.path.exists(os.path.join(ROOT, d, ref + '.png'))
        registered = ('name:"%s"' % name) in page
        if (exists or registered) and not force:
            problems.append((f, 'already in the archive (%s) — --force to replace' % d))
            continue
        if ref in known_refs and not registered and not force:
            problems.append((f, 'ref %s is already used by another garment' % ref))
            continue

        jobs.append(dict(src=src, f=f, name=name, key=key, label=label, cat=cat,
                         ref=ref, mat=mat or 'Unlisted', dir=d,
                         registered=registered))
        known_refs.add(ref)

    for j in jobs:
        print('  %s' % j['f'])
        print('      %-9s %s' % ('name', j['name']))
        print('      %-9s %s / %s' % ('shelf', j['label'], j['cat']))
        print('      %-9s %s   %s' % ('ref', j['ref'], j['mat']))
        print('      %-9s %s/%s.png' % ('to', j['dir'], j['ref']))
    for f, why in problems:
        print('  SKIPPED  %s\n           %s' % (f, why))

    if not write:
        print('\n%d to add, %d skipped. Nothing written — run again with --write.'
              % (len(jobs), len(problems)))
        return 1 if problems and not jobs else 0

    for j in jobs:
        out = os.path.join(ROOT, j['dir'])
        os.makedirs(out, exist_ok=True)
        to_png(j['src'], os.path.join(out, j['ref'] + '.png'))
        os.remove(j['src'])
        if not j['registered']:
            entry = ('      { n:"%s", name:"%s", cat:"%s",\n'
                     '        img:"%s.png", ref:"%s", mat:"%s" },\n'
                     % (j['key'], j['name'], j['cat'], j['ref'], j['ref'], j['mat']))
            page = insert_item(page, entry, j['key'])

    io.open(ARCHIVE_HTML, 'w', encoding='utf-8').write(page)
    print('\nwrote %d garment%s into archive.html' % (len(jobs), '' if len(jobs) == 1 else 's'))

    # empty subfolders left behind by a filed batch
    for d in os.listdir(INCOMING):
        p = os.path.join(INCOMING, d)
        if os.path.isdir(p) and not os.listdir(p):
            os.rmdir(p)

    r = subprocess.run([sys.executable, os.path.join(ROOT, 'tools', 'seo_build.py')],
                       cwd=ROOT)
    if r.returncode:
        print('! seo_build.py failed — the ITEMS entries are written, the pages are not')
        return 1

    print('\nNow check it, then push:')
    print('  python3 tools/check.py')
    print('  git add -A && git commit && git push origin main')
    return 1 if problems else 0


if __name__ == '__main__':
    sys.exit(main())
