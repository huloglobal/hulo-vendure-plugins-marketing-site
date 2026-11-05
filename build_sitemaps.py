#!/usr/bin/env python3
"""Write one sitemap per generated tree: dist/<tree>/sitemap.xml.

Run by deploy.sh after the page builders. A page is listed when it is
indexable and canonical to itself: its <link rel="canonical"> equals its own
https://huloglobal.com/<tree>/.../ URL and its robots meta has no noindex.
The Pro stubs (canonical to the free plugin page) and anything noindex drop
out by themselves, so the list never needs maintaining by hand. No <lastmod>:
the build does not know when a page's content last changed.

huloglobal.com's robots.txt (in the main site's repository) names the three
sitemaps.

usage: python3 build_sitemaps.py [dist_dir]
"""
import html
import re
import sys
from pathlib import Path

SITE = 'https://huloglobal.com'
TREES = ('vendure-plugins', 'wordpress-plugins', 'legal')
DIST = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent / 'dist'
CANON = re.compile(r'<link rel="canonical" href="([^"]+)"', re.I)
ROBOTS = re.compile(r'<meta name="robots" content="([^"]*)"', re.I)


def main() -> None:
    for tree in TREES:
        root = DIST / tree
        if not root.is_dir():
            raise SystemExit(f'{root} is missing: run the page builders first')
        urls = []
        for page in sorted(root.rglob('index.html')):
            rel = page.parent.relative_to(DIST).as_posix()
            own = f'{SITE}/{rel}/'
            text = page.read_text(encoding='utf-8', errors='replace')
            m = CANON.search(text)
            r = ROBOTS.search(text)
            if not m or html.unescape(m.group(1)) != own:
                continue
            if r and 'noindex' in r.group(1).lower():
                continue
            urls.append(own)
        body = ''.join(f'  <url><loc>{html.escape(u)}</loc></url>\n' for u in urls)
        (root / 'sitemap.xml').write_text(
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + body + '</urlset>\n',
            encoding='utf-8')
        print(f'{tree}/sitemap.xml: {len(urls)} URLs')


if __name__ == '__main__':
    main()
