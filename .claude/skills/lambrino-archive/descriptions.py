#!/usr/bin/env python3
"""Fill each garment's .txt with the product's own description.

Every Lambrino listing opens with an "At a glance" list: material, closures,
pockets, the pattern, measurements, the issue period, and which army it came
from. That list is the record — it is the only place the measurements and
the dating exist, and it is written by the people who handled the garment.
Everything after "Grades -" is condition and sales patter for one particular
item, and does not belong in an archive record.

    python3 descriptions.py --sources _incoming/lambrino/sources.json --root .
"""
import argparse, json, os, re, html, subprocess, time, sys

UA = 'BMU-archive/1.0 (https://britishmaterialunit.com)'


def get(url):
    r = subprocess.run(['curl', '-sSL', '-f', '--max-time', '40', '-A', UA,
                        '--retry', '3', '--retry-delay', '3', url],
                       capture_output=True)
    if r.returncode != 0:
        raise RuntimeError(r.stderr.decode()[:160] or f'curl exit {r.returncode}')
    return r.stdout


def at_a_glance(body_html):
    """The lines between 'At a glance' and 'Grades', in the shop's own order."""
    text = html.unescape(re.sub(r'<[^>]+>', '\n', body_html or ''))
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    out, on = [], False
    for l in lines:
        low = l.lower().rstrip(' -:')
        if low.startswith('at a glance'):
            on = True
            continue
        if on and (low.startswith('grade') or low.startswith('any questions')
                   or set(l) <= set('- ') or low.startswith('looking for more')):
            break
        if on:
            out.append(l)
    return out


HEAD = re.compile(r'^(.*?)\n\nNation: (.*)\nType: (.*)\nArchive ref: (\S+)', re.S)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--sources', required=True)
    ap.add_argument('--root', default='.')
    a = ap.parse_args()

    sources = json.load(open(a.sources))
    # code -> path of its .txt
    where = {}
    for root, _, files in os.walk(os.path.join(a.root, 'archive')):
        for f in files:
            if f.endswith('.txt'):
                where[os.path.splitext(f)[0]] = os.path.join(root, f)

    done = missed = 0
    for code, url in sources.items():
        txt = where.get(code)
        if not txt:
            continue                      # removed from the archive since
        try:
            p = json.loads(get(url.rstrip('/') + '.json'))['product']
        except Exception as e:
            print(f'  ! {code}: {e}', file=sys.stderr); missed += 1; continue

        lines = at_a_glance(p.get('body_html', ''))
        if not lines:
            print(f'  ! {code}: no "at a glance" block', file=sys.stderr)
            missed += 1
            continue

        m = HEAD.match(open(txt, encoding='utf-8').read())
        if not m:
            print(f'  ! {code}: unreadable record', file=sys.stderr); missed += 1; continue
        name, nation, ctype, ref = m.groups()

        with open(txt, 'w', encoding='utf-8') as f:
            f.write(f'{name}\n\nNation: {nation}\nType: {ctype}\nArchive ref: {ref}\n\n')
            f.write('\n'.join(lines) + '\n')
        done += 1
        print(f'  {code:20} {len(lines)} lines')
        time.sleep(0.6)                   # the shop is someone else's server

    print(f'\n{done} records written, {missed} missed')


if __name__ == '__main__':
    main()
