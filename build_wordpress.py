"""huloglobal.com/wordpress-plugins/: pages, downloads and update manifests
for the WordPress editions (WooCommerce optional).

Page copy comes from each plugin's own readme.txt (free plugin and Pro add-on)
in /root/hulo-woo-plugins, so the site always says what the code does. Prices
come from the Vendure catalogue in build.py (the editions share them). Zips and
update.json files are taken from that repo's dist/ (tools/build.sh output).
"""

import html
import json
import re
import shutil
from pathlib import Path

import build as vp

HERE = Path(__file__).parent
OUT = HERE / 'dist' / 'wordpress-plugins'
WOO = Path('/root/hulo-woo-plugins')
BASE = '/wordpress-plugins'

# Listing order; titles match the plugin names.
SLUGS = ['payments', 'checkout-guard', 'fraud-prevention', 'business-credit', 'quotations',
         'email-tracking', 'review-requests', 'visitor-analytics', 'geo-block']

# Free plugins accepted into the WordPress.org directory (slug list, filled in
# as reviews come back). Until then the free plugin downloads from here.
WPORG_LISTED: list[str] = []


def parse_readme(path: Path) -> dict:
    text = path.read_text(encoding='utf-8')
    m = re.match(r'===\s*(.+?)\s*===\s*\n(.*?)\n\n(.*?)\n\n(.*)', text, re.S)
    name, headers_raw, short, rest = m.groups()
    headers = dict(re.findall(r'^([A-Za-z ]+):\s*(.+)$', headers_raw, re.M))
    sections = {}
    for title, body in re.findall(r'^==\s*(.+?)\s*==\s*\n(.*?)(?=^==\s|\Z)', '\n' + rest, re.S | re.M):
        sections[title.strip()] = body.strip()
    return {'name': name.strip(), 'headers': headers, 'short': short.strip(), 'sections': sections}


def inline(s: str) -> str:
    s = html.escape(s, quote=False)
    s = re.sub(r'`([^`]+)`', r'<code>\1</code>', s)
    s = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', s)
    s = re.sub(r'\[([^\]]+)\]\((https?://[^)\s]+)\)', r'<a href="\2" class="underline underline-offset-4">\1</a>', s)
    return s


def md(body: str) -> str:
    """The readme.txt dialect: = h4 =, ** bold **, * lists, 1. lists, paragraphs."""
    out, para, lst, lst_tag = [], [], [], None

    def flush():
        nonlocal para, lst, lst_tag
        if para:
            out.append('<p class="mt-4 text-ink-700 leading-relaxed">' + inline(' '.join(para)) + '</p>')
            para = []
        if lst:
            out.append(f'<{lst_tag} class="vp-tier-list mt-3">' + ''.join(f'<li>{inline(i)}</li>' for i in lst) + f'</{lst_tag}>')
            lst, lst_tag = [], None

    for line in body.splitlines():
        t = line.strip()
        if not t:
            flush()
            continue
        h = re.match(r'^=\s*(.+?)\s*=$', t)
        b = re.match(r'^\*\*(.+?)\*\*$', t)
        li = re.match(r'^[*-]\s+(.*)$', t)
        ol = re.match(r'^\d+\.\s+(.*)$', t)
        if h or b:
            flush()
            out.append(f'<h3 class="mt-8 text-lg font-semibold text-ink-900">{inline((h or b).group(1))}</h3>')
        elif li or ol:
            if para:
                flush()
            tag = 'ul' if li else 'ol'
            if lst_tag and lst_tag != tag:
                flush()
            lst_tag = tag
            lst.append((li or ol).group(1))
        elif lst:
            lst[-1] += ' ' + t
        else:
            para.append(t)
    flush()
    return '\n'.join(out)


def faq(body: str) -> str:
    items = re.findall(r'^=\s*(.+?)\s*=\s*\n(.*?)(?=^=\s|\Z)', body + '\n', re.S | re.M)
    return '\n'.join(
        f'<details class="vp-faq"><summary>{inline(q)}</summary><div>{md(a)}</div></details>' for q, a in items)


def changelog(body: str) -> str:
    return md(body)


def pricing_for(slug: str) -> dict:
    for p in vp.PLUGINS:
        if p['slug'] == slug:
            return p.get('pricing') or vp.CURRENCIES
    raise KeyError(slug)


def dist_files(name: str) -> tuple[str, Path, Path]:
    """Version, zip path and update.json path for hulo-<name> from the repo's dist/."""
    manifest = WOO / 'dist' / name / 'update.json'
    ver = json.loads(manifest.read_text())['version']
    z = WOO / 'dist' / name / f'hulo-{name}-{ver}.zip'
    if not z.exists():
        raise SystemExit(f'missing {z}: run tools/build.sh {name.removesuffix("-pro")}')
    return ver, z, manifest


def load(slug: str) -> dict:
    free = parse_readme(WOO / 'plugins' / f'hulo-{slug}' / 'readme.txt')
    pro = parse_readme(WOO / 'plugins' / f'hulo-{slug}-pro' / 'readme.txt')
    fver, fzip, fman = dist_files(slug)
    pver, pzip, pman = dist_files(slug + '-pro')
    title = re.sub(r'^HULO\s+|\s+for (WooCommerce|WordPress)$', '', free['name'])
    return {'slug': slug, 'title': title, 'free': free, 'pro': pro, 'fver': fver, 'fzip': fzip, 'fman': fman,
            'pver': pver, 'pzip': pzip, 'pman': pman, 'pricing': pricing_for(slug)}


def free_download_html(p: dict) -> str:
    if p['slug'] in WPORG_LISTED:
        return (f'<a href="https://wordpress.org/plugins/hulo-{p["slug"]}/" class="btn btn-secondary">Free plugin on WordPress.org</a>')
    return (f'<a href="{BASE}/{p["slug"]}/hulo-{p["slug"]}-{p["fver"]}.zip" class="btn btn-secondary" download>'
            f'Download free plugin (v{p["fver"]})</a>')


def plugin_page(p: dict) -> str:
    free, pro, gbp = p['free'], p['pro'], p['pricing']['GBP']
    buy = f'{vp.BUY_BASE}/wordpress-{p["slug"]}'
    pro_zip = f'{BASE}/{p["slug"]}-pro/hulo-{p["slug"]}-pro-{p["pver"]}.zip'
    fs, ps = free['sections'], pro['sections']
    install = md(fs.get('Installation', ''))
    pro_desc = md(ps.get('Description', ''))
    ext = ''
    for label, sec in (('Free plugin', fs.get('External services')), ('Pro add-on', ps.get('External services'))):
        if sec:
            ext += f'<h3 class="mt-8 text-lg font-semibold text-ink-900">{label}</h3>' + md(sec)
    body = f'''
<section class="vp-hero">
<div class="container-page relative pt-12 pb-10 md:pt-16 md:pb-14">
<img class="vp-plugin-logo" src="/vendure-plugins/logos/{p['slug']}.svg" alt="" width="56" height="56" aria-hidden="true">
<nav class="mb-5 text-sm text-ink-600">
<a href="{BASE}/" class="hover:text-ink-900">WordPress plugins</a>
<span class="mx-2 text-ink-400">/</span>
<span class="text-ink-900 font-medium">{html.escape(p['title'])}</span>
</nav>
<h1 class="max-w-3xl text-4xl sm:text-5xl md:text-6xl font-bold tracking-tight text-ink-900 leading-[1.04]">{html.escape(p['title'])} for WordPress</h1>
<p class="mt-6 max-w-2xl text-lg md:text-xl text-ink-600 leading-relaxed">{inline(free['short'])}</p>
<div class="mt-8 flex flex-wrap items-center gap-3">
{free_download_html(p)}
<a href="{pro_zip}" class="btn btn-primary" download>Download Pro: 14 days free, no card</a>
<a href="#pricing" class="btn btn-secondary">Pricing</a>
<a href="#changelog" class="ml-auto text-xs text-ink-500 font-mono hover:underline">v{p['fver']}</a>
</div>
<p class="mt-4 text-sm text-ink-600">Requires WordPress {html.escape(free['headers'].get('Requires at least', '6.5'))}+ and PHP {html.escape(free['headers'].get('Requires PHP', '8.1'))}+. Works on any WordPress site; WooCommerce is optional and switches on the shop features.</p>
</div>
</section>

<section class="vp-section bg-white">
<div class="container-page max-w-3xl">
<p class="text-sm font-semibold uppercase tracking-wider text-accent-600">Free plugin</p>
<h2 class="mt-3 text-3xl md:text-4xl font-bold tracking-tight text-ink-900">What the free plugin does</h2>
{md(fs.get('Description', ''))}
</div>
</section>

<section class="vp-section">
<div class="container-page max-w-3xl">
<p class="text-sm font-semibold uppercase tracking-wider text-accent-600">Pro add-on</p>
<h2 class="mt-3 text-3xl md:text-4xl font-bold tracking-tight text-ink-900">{html.escape(pro['name'].replace('HULO ', ''))}</h2>
{pro_desc}
</div>
</section>

<section class="vp-section bg-white" id="pricing">
<div class="container-page max-w-3xl">
<p class="text-sm font-semibold uppercase tracking-wider text-accent-600">Pricing</p>
<h2 class="mt-3 text-3xl md:text-4xl font-bold tracking-tight text-ink-900">Free, then Pro when you want it</h2>
<div class="mt-8 grid gap-6 md:grid-cols-3">
<div class="rounded-lg border border-ink-200 bg-white p-6"><p class="text-xs font-semibold uppercase tracking-wider text-ink-500">Free plugin</p><p class="vp-price-num mt-2">£0</p><p class="mt-2 text-sm text-ink-700">Free forever, GPL-licensed.</p></div>
<div class="rounded-lg border border-accent-300 bg-accent-50 p-6"><p class="text-xs font-semibold uppercase tracking-wider text-accent-700">Pro, monthly or annual</p><p class="vp-price-num mt-2">{html.escape(gbp['monthly'])}<small>/month</small></p><p class="mt-2 text-sm text-ink-700">The first 14 days are free with no card. Subscribe from the plugin page when you're ready; the first charge is taken when the 14 days end. Annual billing gets two months free. Cancel any time.</p><a href="{buy}?plan=monthly" class="btn btn-primary mt-5">Subscribe</a></div>
<div class="rounded-lg border border-ink-200 bg-white p-6"><p class="text-xs font-semibold uppercase tracking-wider text-ink-500">Pro, lifetime</p><p class="vp-price-num mt-2">{html.escape(gbp['lifetime'])}</p><p class="mt-2 text-sm text-ink-700">One payment for one store, including updates.</p><a href="{buy}?plan=lifetime" class="btn btn-secondary mt-5">Buy lifetime</a></div>
</div>
<p class="mt-4 text-xs text-ink-500">Prices in GBP; the checkout also bills in USD, EUR, AUD and CAD. One licence covers one WordPress site.</p>
</div>
</section>

<section class="vp-section" id="install">
<div class="container-page max-w-3xl">
<p class="text-sm font-semibold uppercase tracking-wider text-accent-600">Install</p>
<h2 class="mt-3 text-3xl md:text-4xl font-bold tracking-tight text-ink-900">Installation</h2>
{install}
<p class="mt-4 text-ink-700 leading-relaxed">For Pro, upload <code>hulo-{p['slug']}-pro-{p['pver']}.zip</code> the same way (Plugins → Add New → Upload Plugin) with the free plugin active. The 14 days start automatically, and Pro updates itself from WordPress's Plugins screen.</p>
</div>
</section>

<section class="vp-section bg-white">
<div class="container-page max-w-3xl">
<h2 class="text-3xl font-bold tracking-tight text-ink-900">Frequently asked questions</h2>
<div class="mt-6">{faq(fs.get('Frequently Asked Questions', ''))}</div>
</div>
</section>

{f'<section class="vp-section"><div class="container-page max-w-3xl"><h2 class="text-3xl font-bold tracking-tight text-ink-900">External services</h2>{ext}</div></section>' if ext else ''}

<section class="vp-section bg-white" id="changelog">
<div class="container-page max-w-3xl">
<h2 class="text-3xl font-bold tracking-tight text-ink-900">Changelog</h2>
{changelog(fs.get('Changelog', ''))}
</div>
</section>
'''
    title = f'{p["title"]} for WordPress: free plugin and Pro add-on · Hulo Global'
    return vp.header(title, f'https://huloglobal.com{BASE}/{p["slug"]}/', free['short']) + wp_nav() + body + footer()


def index_page(items: list[dict]) -> str:
    cards = '\n'.join(f'''<div class="vp-card">
<img class="vp-plugin-logo" src="/vendure-plugins/logos/{p['slug']}.svg" alt="" width="40" height="40" aria-hidden="true">
<h3 class="text-xl font-semibold text-ink-900"><a href="{BASE}/{p['slug']}/">{html.escape(p['title'])}</a></h3>
<p class="vp-card-tagline mt-2 text-ink-600">{inline(p['free']['short'])}</p>
<p class="mt-3 text-sm text-ink-600">Pro from {html.escape(p['pricing']['GBP']['monthly'])}/month · 14 days free, no card</p>
<div class="vp-card-actions mt-4 flex flex-wrap gap-2"><a href="{BASE}/{p['slug']}/" class="btn btn-secondary">Details</a>{free_download_html(p)}</div>
</div>''' for p in items)
    body = f'''
<section class="vp-hero">
<div class="container-page relative pt-12 pb-10 md:pt-16 md:pb-14">
<h1 class="max-w-3xl text-4xl sm:text-5xl md:text-6xl font-bold tracking-tight text-ink-900 leading-[1.04]">WordPress plugins</h1>
<p class="mt-6 max-w-2xl text-lg md:text-xl text-ink-600 leading-relaxed">Nine plugins for payments, checkout security, fraud screening, trade credit, quotations, e-mail, reviews, analytics and geo-blocking. Each one is a free plugin that does the job on its own, plus a Pro add-on you can try for 14 days without a card.</p>
<p class="mt-4 text-sm text-ink-600">Built for WordPress 6.5+ and PHP 8.1+, and they work on any WordPress site. WooCommerce is optional: when it's installed, the shop features switch on too (HPOS and the Cart/Checkout blocks supported). No other plugins required. Also available <a href="/vendure-plugins/" class="underline underline-offset-4">for Vendure</a>.</p>
</div>
</section>
<section class="vp-section bg-white">
<div class="container-page">
<div class="vp-cards-grid">
{cards}
</div>
</div>
</section>
'''
    return (vp.header('WordPress plugins · Hulo Global', f'https://huloglobal.com{BASE}/',
                      'Free WordPress plugins with Pro add-ons (WooCommerce optional): payments, checkout guard, fraud prevention, business credit, quotations, e-mail tracking, review requests, visitor analytics and geo-blocking.')
            + wp_nav() + body + footer())


def wp_nav() -> str:
    return ''


def footer() -> str:
    return vp.FOOTER


def pro_stub(p: dict) -> str:
    """Pro's update.json points its homepage at <slug>-pro/; send people to the plugin page."""
    url = f'{BASE}/{p["slug"]}/'
    return (f'<!doctype html><html lang="en"><head><meta charset="utf-8"><title>{html.escape(p["title"])} Pro</title>'
            f'<link rel="canonical" href="https://huloglobal.com{url}"><meta http-equiv="refresh" content="0; url={url}">'
            f'</head><body><a href="{url}">{html.escape(p["title"])} for WordPress</a></body></html>')


def main():
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    items = [load(s) for s in SLUGS]
    (OUT / 'index.html').write_text(index_page(items), encoding='utf-8')
    for p in items:
        d = OUT / p['slug']
        d.mkdir()
        (d / 'index.html').write_text(plugin_page(p), encoding='utf-8')
        shutil.copy2(p['fzip'], d / p['fzip'].name)
        shutil.copy2(p['fman'], d / 'update.json')
        dp = OUT / (p['slug'] + '-pro')
        dp.mkdir()
        (dp / 'index.html').write_text(pro_stub(p), encoding='utf-8')
        shutil.copy2(p['pzip'], dp / p['pzip'].name)
        shutil.copy2(p['pman'], dp / 'update.json')
    print(f'Wrote {len(items)} WordPress plugin pages, {2 * len(items)} zips and manifests to {OUT}')


if __name__ == '__main__':
    main()
