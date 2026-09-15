#!/usr/bin/env python3
"""Turn a record's bullet list into sentences.

The shop writes "At a glance" as a list of fragments, which is the right
shape for a product page and the wrong shape for an archive record. This
rewrites each record as prose, using ONLY what the bullets already say —
no fact is added, and any fragment the grouping does not recognise is kept
verbatim rather than dropped.

    python3 prose.py --root .            # rewrite every record
    python3 prose.py --root . --dry-run  # print, change nothing

The original bullets are kept underneath the prose, so nothing is lost and
the rewrite can be checked against its source at any time.
"""
import argparse, os, re, sys

# A bullet is sorted by what it is talking about. Order within each group is
# the shop's own; only the grouping is ours.
# A measurement states a figure. "Shoulder Epaulettes" is not one, and
# matching on the word alone filed it as though it were.
MEASURE = re.compile(r'^(Pit to Pit|Chest Size|Sleeve Length|Collar to Hem|Waist|Inseam|Leg Length|Shoulder to)\b.*[:0-9]', re.I)
DATING  = re.compile(r'^(Vintage|Modern|Genuine|Surplus|Dated|Issued)\b', re.I)
PATTERN = re.compile(r'\b(Camouflage|Camo|Pattern|Colour Scheme|Color Scheme)\b', re.I)
MATERIAL= re.compile(r'\b(Material|Cotton|Polyester|Wool|Nylon|Fleece|Denim|Canvas|Leather|Ripstop|Blend|Gabardine|Moleskin|Sateen)\b', re.I)

# Words that keep their capital wherever they appear: nations and armies,
# pattern and brand names, and anything the shop wrote as a proper noun.
KEEP = {
 'british','england','english','scotland','wales','irish','ireland','austrian','austria',
 'belgian','belgium','bulgarian','bulgaria','balgarska','narodna','armiya','chinese','china',
 'czech','czechoslovak','czechoslovakia','danish','denmark','dutch','netherlands','koninklijke',
 'landmacht','german','germany','east','west','nva','ddr','finnish','finland','french','france',
 'armée','terre','greek','greece','hungarian','hungary','iraqi','iraq','israeli','israel','idf',
 'italian','italy','alpini','roma','norwegian','norway','polish','poland','pantera','portuguese',
 'portugal','romanian','romania','russian','russia','soviet','ussr','serbian','serbia','slovak',
 'slovakia','spanish','spain','swedish','sweden','swiss','switzerland','yugoslav','yugoslavia',
 'jna','american','america','usa','marine','marines','corps','navy','army','air','force','royal',
 'signals','scotland','warsaw','pact','bloc','cold','war','vietnam','nam','gulf','airborne',
 'woodland','desert','alpenflage','strichmuster','vegetato','flecktarn','multicam','ucp','dpm',
 'mtp','cce','ecwcs','bdu','ubacs','molle','velcro','goretex','norwegian','norgie','cossack',
 'ike','mk3','m65','m64','m71','m81','m84','m85','m87','m93','m94','m97','m09','m39','m51','m63',
 'wz93','taz83','spe','fad','gp','fr','rig','type','vz','pla','opup','ramco','lambrino',
 'mladshi','leĭtenant','lieutenant','junior','ministry','defence','defense','surplus','militaria',
 'balkan','eastern','western','central','europe','european',
}

def sentence_case(t):
    """Title Case to sentence case, leaving proper nouns and marks alone.

    The bullets are written in Title Case, which reads as shouting once it
    is inside a sentence. Only words that are plainly ordinary are lowered:
    anything in caps, anything carrying a digit, anything quoted and
    anything on the list above keeps what it was given."""
    def fix(m):
        w = m.group(0)
        bare = w.strip('"\u201c\u201d\'()&/,.')
        if not bare: return w
        if bare.isupper() and len(bare) > 1: return w        # an acronym
        if any(c.isdigit() for c in bare): return w          # a mark or a size
        if bare.lower() in KEEP: return w                    # a name
        if bare[:1].isupper() and bare[1:].islower():
            return w.replace(bare, bare.lower(), 1)
        return w
    return re.sub(r'\S+', fix, t)

def lower_first(t):
    return sentence_case(t)

def join_clauses(items):
    """a, b and c — the Oxford comma left out, as British copy leaves it."""
    items = [i for i in items if i]
    if not items: return ''
    if len(items) == 1: return items[0]
    return ', '.join(items[:-1]) + ' and ' + items[-1]

def build(name, nation, ctype, lines):
    material, pattern, features, measures, dating, other = [], [], [], [], [], []
    for l in lines:
        if MEASURE.match(l):            measures.append(l)
        elif DATING.match(l):           dating.append(l)
        elif MATERIAL.search(l) and not features and len(material) < 2:
            material.append(l)
        elif PATTERN.search(l):         pattern.append(l)
        else:                           features.append(l)

    out = []

    # 1. what it is, what it is made of
    opening = f'The {name}'
    if material:
        m = lower_first(re.sub(r'\s*Material\s*$', '', material[0]).strip())
        opening += f' is cut from {m}'
        if len(material) > 1:
            opening += f', {lower_first(material[1].rstrip("."))}'
        opening += '.'
    else:
        opening += f' is a {ctype.lower().rstrip("s")} of {nation} issue.'
    out.append(opening)

    # 2. the pattern it carries
    if pattern:
        p = [lower_first(x.replace('Beautiful ', '').rstrip('.')) for x in pattern]
        out.append('It carries ' + join_clauses(p) + '.')

    # 3. how it is built
    if features:
        f = [lower_first(x.rstrip('.')) for x in features]
        out.append('It has ' + join_clauses(f) + '.')

    # 4. what it measures
    if measures:
        out.append('Measured flat, it runs ' +
                   join_clauses([lower_first(x.rstrip('.')) for x in measures]) + '.')

    # 5. where it came from
    if dating:
        out.append(' '.join(x.rstrip('.') + '.' for x in dating))

    return '\n\n'.join(out)


HEAD = re.compile(r'^(.*?)\n\nNation: (.*)\nType: (.*)\nArchive ref: (\S+)\n\n(.*)$', re.S)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--root', default='.')
    ap.add_argument('--dry-run', action='store_true')
    a = ap.parse_args()

    done = skipped = 0
    for root, _, files in os.walk(os.path.join(a.root, 'archive')):
        for f in sorted(files):
            if not f.endswith('.txt'): continue
            path = os.path.join(root, f)
            raw = open(path, encoding='utf-8').read()
            m = HEAD.match(raw)
            if not m:
                skipped += 1; continue
            name, nation, ctype, ref, body = m.groups()
            if body.lstrip().startswith('Placeholder record'):
                skipped += 1; continue
            # already prose? the source list is kept under a rule
            if '\n---\n' in body:
                lines = body.split('\n---\n', 1)[1].strip().split('\n')
            else:
                lines = [l.strip() for l in body.strip().split('\n') if l.strip()]

            prose = build(name, nation, ctype, lines)
            out = (f'{name}\n\nNation: {nation}\nType: {ctype}\nArchive ref: {ref}\n\n'
                   f'{prose}\n\n---\n' + '\n'.join(lines) + '\n')
            if a.dry_run:
                print(f'--- {ref}\n{prose}\n')
            else:
                open(path, 'w', encoding='utf-8').write(out)
            done += 1
    print(f'{done} records written, {skipped} skipped', file=sys.stderr)

if __name__ == '__main__':
    main()
