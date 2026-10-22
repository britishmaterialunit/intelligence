#!/usr/bin/env python3
"""Write maps.html: the archive, addressed as /maps.

Maps is the archive's reference board. /maps used to be a stub that
redirected to /archive?maps, and a link previewer that runs script (iMessage
does) followed the redirect, lost the page in the archive rewriting its own
address, and fell back to the site icon tiled across the card. A page that is
really there, with its own title and preview tags and no redirect, is read
like every other page — so maps.html is archive.html with the head re-addressed.
The archive's script sees /maps and opens straight onto the board.

It is generated, never edited: any change to archive.html is a change to
maps.html, so this runs at the end of seo_build.py (and so of ingest.py), and
check.py fails if maps.html has fallen behind.

    python3 tools/build_maps.py           # write maps.html
    python3 tools/build_maps.py --check   # exit 1 if it is out of date
"""
import io
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARCHIVE_HTML = os.path.join(ROOT, 'archive.html')
MAPS_HTML = os.path.join(ROOT, 'maps.html')

DESC = 'Maps — the BMU reference board: garments from the archive and images of your own, arranged and kept.'
SWAPS = [
    ('<title>Archive | BMU</title>', '<title>Maps | BMU</title>'),
    ('<link rel="canonical" href="https://britishmaterialunit.com/archive" />',
     '<link rel="canonical" href="https://britishmaterialunit.com/maps" />\n'
     '  <!-- the archive twice over is not two pages to a search engine; '
     'a link preview still reads everything here -->\n'
     '  <meta name="robots" content="noindex, follow" />'),
    ('<meta property="og:url" content="https://britishmaterialunit.com/archive" />',
     '<meta property="og:url" content="https://britishmaterialunit.com/maps" />'),
    ('<meta property="og:title" content="Archive | BMU" />',
     '<meta property="og:title" content="Maps | BMU" />'),
    ('<meta name="twitter:title" content="Archive | BMU" />',
     '<meta name="twitter:title" content="Maps | BMU" />'),
]
OLD_DESC = 'An open archive of military garments available for sourcing + production runs, or an on-site visit at Unit U.'
BANNER = ('<!-- GENERATED from archive.html by tools/build_maps.py — do not edit; '
          'edit archive.html and run seo_build.py -->\n')


def build():
    page = io.open(ARCHIVE_HTML, encoding='utf-8').read()
    for old, new in SWAPS:
        if page.count(old) != 1:
            raise SystemExit('build_maps: expected exactly one of %r in archive.html' % old)
        page = page.replace(old, new)
    # the description appears in the head's three description tags only
    head, body = page.split('</head>', 1)
    head = head.replace(OLD_DESC, DESC)
    first, rest = head.split('\n', 1)            # after <!DOCTYPE html>, not before it
    return first + '\n' + BANNER + rest + '</head>' + body


def main():
    out = build()
    have = io.open(MAPS_HTML, encoding='utf-8').read() if os.path.exists(MAPS_HTML) else ''
    if '--check' in sys.argv:
        if have != out:
            print('maps.html is out of date — run python3 tools/build_maps.py')
            return 1
        return 0
    if have != out:
        io.open(MAPS_HTML, 'w', encoding='utf-8').write(out)
        print('wrote maps.html')
    return 0


if __name__ == '__main__':
    sys.exit(main())
