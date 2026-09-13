#!/usr/bin/env python3
"""Naming + dedupe engine for the lambrino archive scrape.

Name shape:  [Nation] [Division] [Date] [Additional Info] [Garment Type]

Additional Info is the *residue* of the source title — everything left after
removing nation, division, date marker, garment noun, sizing and filler — kept
in the title's own word order. Residue beats a whitelist because it preserves
distinguishing words we never thought to list (SAS, Footguard's, Class II,
Drummers', Senior Rates).
"""
import re, html as htmlmod

# Stands in the date slot when no explicit marker is present, so the shape of
# every name is the same and the gaps are greppable.
UNKNOWN_DATE = '0000s'

# ---------------------------------------------------------------- size stripping
SIZE_WORD = r'(?:XX?X?\s*(?:Small|Large)|X\s*(?:Small|Large)|Small|Medium|Large|XS|XL|XXL)'
SIZE_PATTERNS = [
    rf'^{SIZE_WORD}(?:\s*/\s*{SIZE_WORD})?(?:\s+.*)?$',
    r'^W\s*\d+(?:\.\d+)?(?:\s*L\s*\d+(?:\.\d+)?)?$',
    r'^\d{2,3}\s*/\s*\d{2,3}$',
    r'^\d{2,3}(?:\.\d+)?\s*(?:cm|mm|in|")$',
    r'^(?:SIZE|Size)\s*\d*\w*$',
    r'^\d{1,3}(?:\.\d)?\s*[A-Z]{0,2}$',
    r'^\d{2,3}[SLRT]$',
    r'^(?:UK|EU|US)\s*\d+',
    r'^(?:Reg|Regular|Long|Short|Tall)$',
]

def is_size(seg):
    seg = seg.strip()
    return not seg or any(re.match(p, seg, re.I) for p in SIZE_PATTERNS)

# size fragments that can appear anywhere once segments are merged
SIZE_TOKENS = [
    r'\bW\s*\d{1,3}(?:\.\d+)?\b',
    r'\bL\s*\d{1,3}(?:\.\d+)?\b',
    r'\b\d{2,3}\s*/\s*\d{2,3}\b',
    r'\b\d{2,3}(?:\.\d+)?\s*cm\b',
    r'\bX+\s*(?:Small|Large|Short|Long)\b',
    r'\bXX?X?L\b|\bXS\b',
    r'\b(?:Small|Medium|Large)\b',
    r'\b(?:Short|Long|Regular|Reg|Tall)\b(?!\s+Sleeve)',
    r'\bSIZE\s*\d*\w*\b',
]

def strip_size_tokens(s):
    for t in SIZE_TOKENS:
        s = re.sub(t, ' ', s, flags=re.I)
    s = re.sub(r'\s+\d{1,3}\s*$', ' ', s)
    return re.sub(r'\s{2,}', ' ', s).strip(' -/')


def split_title(title):
    """-> (main, qualifiers). Trailing size segments dropped; middle segments
    (regiment / variant) returned separately so they can lead the residue."""
    parts = [p.strip() for p in title.split(' - ')]
    while len(parts) > 1 and is_size(parts[-1]):
        parts.pop()
    return parts[0], parts[1:]


def strip_sizes(title):
    main, quals = split_title(title)
    return strip_size_tokens(' '.join([main] + quals))

# ---------------------------------------------------------------- vocabularies
DIVISIONS = [
    (r'\bRoyal\s+Air\s+Force\b|\bRAF\b',        'RAF'),
    (r'\bRoyal\s+Navy\b',                        'Royal Navy'),
    (r'\bRoyal\s+Marines?\b',                    'Royal Marines'),
    (r'\bRoyal\s+Fleet\s+Auxiliary\b|\bRFA\b',   'RFA'),
    (r'\bTri[-\s]Services?\b',                   'Tri-Services'),
    (r'\bPolice\b',                              'Police'),
    (r'\bMoD\b|\bMinistry\s+of\s+Defence\b',     'MoD'),
    (r'\bFire\s+(?:&|and)\s+Rescue\b|\bFire\s+Service\b', 'Fire Service'),
    (r'\bArmy\b',                                'Army'),
    (r'\bNavy\b',                                'Royal Navy'),
]

# Only explicit, documented markers. Never guess a decade.
# A designation IS a date for most of these armies: WZ93 is 1993, M/84 is
# 1984, TAZ83 is 1983. Reading the year out of the mark beats leaving the
# slot at 0000s and asking someone to look each one up by hand.
DESIGNATION_DATE = [
    (r'\b(?:WZ|M|MK|TAZ|SPE|ANZUG|TYPE)[\s/\-]?(\d{2})\b', None),   # two-digit year in a mark
    (r'\bM(\d{2})\b', None),
]

DATES = [
    (r'\bP23\b',                                       '2020s'),
    (r'\bPCS\b|\bMTP\b|\bMulti[-\s]?Terrain\b',        '2010s'),
    (r'\bCS95\b|\bS95\b|\b95\s*Pattern\b',             '1990s'),
    (r'\b(?:19)?90s\b',                                '1990s'),
    (r'\b8[45]\s*Pattern\b',                           '1980s'),
    (r'\b(?:19)?80s\b',                                '1980s'),
    (r'\b7[025]\s*Pattern\b',                          '1970s'),
    (r'\b(?:19)?70s\b',                                '1970s'),
    (r'\b6[08]\s*Pattern\b',                           '1960s'),
    (r'\b(?:19)?60s\b',                                '1960s'),
    (r'\b(?:19)?50s\b',                                '1950s'),
    (r'\b(?:19)?40s\b|\bWW2\b|\bWWII\b',               '1940s'),
]

FABRICS = [
    (r'\bGore[-\s]?Tex\b',       'Goretex'),
    (r'\bRip[-\s]?stop\b',       'Ripstop'),
    (r'\bMoleskin\b',            'Moleskin'),
    (r'\bViscose\b',             'Viscose'),
    (r'\bBarathea\b',            'Barathea'),
    (r'\bMelton\b',              'Melton'),
    (r'\bSerge\b',               'Serge'),
    (r'\bWool\b|\bWoollen\b',    'Wool'),
    (r'\bFleece\b',              'Fleece'),
    (r'\bLeather\b',             'Leather'),
    (r'\bNylon\b',               'Nylon'),
    (r'\bPolyester\b',           'Polyester'),
    (r'\bPoly[-\s]?Cotton\b',    'Poly-Cotton'),
    (r'\bCotton\b',              'Cotton'),
    (r'\bDenim\b',               'Denim'),
    (r'\bCanvas\b',              'Canvas'),
]

# Words carrying no distinguishing value once the rest of the name exists.
FILLER = r"""\b(?:
    Genuine|Surplus|Issue|Issued|UK|New|Used|Grade|
    Style|Multi|Purpose|Original|Authentic|Military|Vintage|Classic|Mens|Womens
)\b"""

# "Camo" is written out in full rather than dropped: on these garments the
# pattern is the identifying fact, not a decoration. "Type" is kept too —
# "Type 81" is a designation, and stripping the word left a bare number.
CAMO_FIX = [(r'\bCamo\b', 'Camouflage')]

# Order is priority: the first noun found becomes THE garment noun and every
# other noun is stripped from the residue, so a listing titled "Combat Jacket /
# Shirt" resolves to one or the other, never both. Specific beats generic.
GARMENT_WORDS = [
    ('Greatcoat',    'Jackets / Shirts'),
    ('Parka',        'Jackets / Shirts'),
    ('Smock',        'Jackets / Shirts'),
    ('Tunic',        'Jackets / Shirts'),
    ('Blouson',      'Jackets / Shirts'),
    ('Waistcoat',    'Jackets / Shirts'),
    ('Gilet',        'Jackets / Shirts'),
    ('Sweatshirt',   'Jackets / Shirts'),
    ('Hoodie',       'Jackets / Shirts'),
    ('Fleece',       'Jackets / Shirts'),
    ('Jacket',       'Jackets / Shirts'),
    ('Jumper',       'Jackets / Shirts'),
    ('Jersey',       'Jackets / Shirts'),
    ('Pullover',     'Jackets / Shirts'),
    ('Polo',         'Jackets / Shirts'),
    ('T Shirt',      'Jackets / Shirts'),
    ('T-Shirt',      'Jackets / Shirts'),
    ('Shirt',        'Jackets / Shirts'),
    ('Coat',         'Jackets / Shirts'),
    ('Top',          'Jackets / Shirts'),
    ('Coveralls',    'Trousers / Coveralls'),
    ('Coverall',     'Trousers / Coveralls'),
    ('Overalls',     'Trousers / Coveralls'),
    ('Salopettes',   'Trousers / Coveralls'),
    ('Trousers',     'Trousers / Coveralls'),
    ('Shorts',       'Trousers / Coveralls'),
    ('Skirt',        'Trousers / Coveralls'),
    ('Bergen',       'Bags / Webbing'),
    ('Rucksack',     'Bags / Webbing'),
    ('Daysack',      'Bags / Webbing'),
    ('Yoke',         'Bags / Webbing'),
    ('Webbing',      'Bags / Webbing'),
    ('Bandolier',    'Bags / Webbing'),
    ('Vest',         'Bags / Webbing'),
    ('Bag',          'Bags / Webbing'),
    ('Pouch',        'Pouches / Cases'),
    ('Holster',      'Pouches / Cases'),
    ('Case',         'Pouches / Cases'),
    ('Beret',        'Headwear'),
    ('Helmet',       'Headwear'),
    ('Boonie',       'Headwear'),
    ('Balaclava',    'Headwear'),
    ('Cap',          'Headwear'),
    ('Hat',          'Headwear'),
    ('Boots',        'Footwear'),
    ('Boot',         'Footwear'),
    ('Shoes',        'Footwear'),
    ('Sleeping Bag', 'Sleep / Shelter / Field'),
    ('Basha',        'Sleep / Shelter / Field'),
    ('Bivvy',        'Sleep / Shelter / Field'),
    ('Belt',         'Hardware / Misc'),
    ('Gloves',       'Hardware / Misc'),
    ('Tie',          'Hardware / Misc'),
]

TYPE_TO_CAT = {
    'Jacket': 'Jackets / Shirts', 'Jackets': 'Jackets / Shirts',
    'Dress Jackets': 'Jackets / Shirts', 'Coats & Jackets': 'Jackets / Shirts',
    'Coats': 'Jackets / Shirts', 'Greatcoat': 'Jackets / Shirts',
    'Shirts': 'Jackets / Shirts', 'Pullover Jumper': 'Jackets / Shirts',
    'Jacket Liner': 'Jackets / Shirts', 'Base Layer Shirt': 'Jackets / Shirts',
    'Field Jacket': 'Jackets / Shirts',
    'Trousers': 'Trousers / Coveralls', 'Dress Trousers': 'Trousers / Coveralls',
    'Coverall': 'Trousers / Coveralls', 'Overalls': 'Trousers / Coveralls',
    'Shorts': 'Trousers / Coveralls', 'Skirt': 'Trousers / Coveralls',
    'Headwear': 'Headwear', 'Hats': 'Headwear',
    'Footwear': 'Footwear',
    'Vest': 'Bags / Webbing', 'Bags': 'Bags / Webbing', 'Rucksack': 'Bags / Webbing',
    'Field Gear': 'Sleep / Shelter / Field',
    'Belt': 'Hardware / Misc', 'Accessories': 'Hardware / Misc',
    'Gloves': 'Hardware / Misc', 'Tie': 'Hardware / Misc',
}

GARMENT_FOR_CAT = {
    'Jackets / Shirts': 'Jacket', 'Trousers / Coveralls': 'Trousers',
    'Headwear': 'Headwear', 'Footwear': 'Boots', 'Bags / Webbing': 'Vest',
    'Pouches / Cases': 'Pouch', 'Sleep / Shelter / Field': 'Field Gear',
    'Hardware / Misc': 'Item',
}


def first_match(text, table):
    for pat, val in table:
        if re.search(pat, text, re.I):
            return val
    return None


def strip_html(s):
    return re.sub(r'\s{2,}', ' ', htmlmod.unescape(re.sub(r'<[^>]+>', ' ', s or '')))


def normalise_tokens(s):
    """Tidy the residue: collapse punctuation, normalise 'No. 2' -> 'No.2'."""
    s = re.sub(r'["“”]', '', s)
    s = re.sub(r'\bw/\s*', 'with ', s, flags=re.I)
    s = re.sub(r'\bNo\.?\s*(\d+[A-Za-z]?)\b', r'No.\1', s, flags=re.I)
    s = re.sub(r'\s*[/&]\s*', ' ', s)
    s = re.sub(r'[(),]', ' ', s)
    s = re.sub(r'\s*-\s*', ' ', s)
    s = re.sub(r"\s+['’]\s+", ' ', s)        # orphaned possessive left by a stripped word
    s = re.sub(r'\s{2,}', ' ', s)
    return s.strip(" -/'’")


def derive(title, product_type='', body_html='', tags=(), nation='British'):
    """Return dict with base name (no fabric tie-break yet), category, fabric, flags.

    `nation` leads the name and is stripped out of the residue, so the same
    engine serves the British bulk scrape and the one-per-nation passes.
    """
    flags = []
    main, quals = split_title(htmlmod.unescape(title))
    main = strip_size_tokens(main)
    quals = [strip_size_tokens(q) for q in quals]
    quals = [q for q in quals if q]
    core = ' '.join([main] + quals)
    body = strip_html(body_html)[:2000]

    division = first_match(core, DIVISIONS) or ''
    date = first_match(core, DATES) or first_match(' '.join(tags or ()), DATES) or ''
    if not date:
        # placeholder rather than a guess — marks the slot for manual research
        date = UNKNOWN_DATE
        flags.append('date-unknown')

    # garment noun + category
    garment, cat = None, None
    for word, c in GARMENT_WORDS:
        if re.search(r'\b' + re.escape(word) + r'\b', core, re.I):
            garment, cat = word, c
            break
    if not cat:
        cat = TYPE_TO_CAT.get((product_type or '').strip(), 'Hardware / Misc')
        garment = GARMENT_FOR_CAT[cat]
        flags.append('type-from-product-type')

    # ---- residue
    res = ' '.join(quals + [main])
    # the nation leads the name; it must not also turn up in the middle of it.
    # Every word of it goes — "United States" has to lose both halves.
    for word in nation.split():
        res = re.sub(r'\b' + re.escape(word) + r'\b', ' ', res, flags=re.I)
    for pat, _ in DIVISIONS:
        res = re.sub(pat, ' ', res, flags=re.I)
    for pat, _ in DATES:                      # strip every date marker, not just the winner
        res = re.sub(pat, ' ', res, flags=re.I)
    # remove every garment noun, not just the chosen one — a title reading
    # "Combat Jacket / Shirt" must not come out named both
    for word, _ in GARMENT_WORDS:
        res = re.sub(r'\b' + re.escape(word) + r'\b', ' ', res, flags=re.I)
    res = re.sub(FILLER, ' ', res, flags=re.I | re.X)
    res = normalise_tokens(res)
    # a residue word repeated (e.g. "Jacket Jacket") adds nothing
    words, out = res.split(), []
    for w in words:
        if not out or w.lower() != out[-1].lower():
            out.append(w)
    res = ' '.join(out)

    fabric_title = first_match(core, FABRICS)
    fabric_body = first_match(body, FABRICS)
    fabric = fabric_title or fabric_body
    if not fabric:
        flags.append('fabric-unknown')

    base = ' '.join(p for p in [nation, division, date, res, garment] if p)
    base = re.sub(r'\s{2,}', ' ', base).strip()

    return {
        'name': base, 'cat': cat, 'garment': garment,
        'fabric': fabric, 'fabric_in_title': bool(fabric_title),
        'flags': flags,
    }


def slug(name):
    return re.sub(r'^-+|-+$', '',
                  re.sub(r'[^a-z0-9]+', '-',
                         re.sub(r"[’']", '', name.lower())))


def resolve(records):
    """Group by base name; split groups whose members differ in fabric.

    Implements the user's rule: same wording + same size class = one garment;
    same wording but different material = separate garments.
    """
    groups = {}
    for r in records:
        groups.setdefault(r['derived']['name'], []).append(r)

    resolved = []
    for base, members in groups.items():
        fabrics = {m['derived']['fabric'] for m in members}
        split = len(fabrics) > 1
        by_fab = {}
        for m in members:
            fab = m['derived']['fabric']
            key = fab if split else None
            by_fab.setdefault(key, []).append(m)
        for key, mem in by_fab.items():
            name = base
            if key and not mem[0]['derived']['fabric_in_title']:
                # insert fabric before the garment noun
                g = mem[0]['derived']['garment']
                name = re.sub(r'\b' + re.escape(g) + r'$', f'{key} {g}', base)
                if name == base:
                    name = f'{base} {key}'
            resolved.append({
                'name': name,
                'cat': mem[0]['derived']['cat'],
                'primary': mem[0],
                'variants': mem,
                'flags': list(mem[0]['derived']['flags']),
            })

    # two different names must never collapse to one slug — that would make two
    # garments share a folder and silently overwrite each other's image
    resolved.sort(key=lambda x: (x['cat'], x['name']))
    used = {}
    for r in resolved:
        s = slug(r['name'])
        if s in used:
            used[s] += 1
            r['name'] = f"{r['name']} {used[s]}"
            r['flags'].append('name-disambiguated')
        else:
            used[s] = 1
    return resolved
