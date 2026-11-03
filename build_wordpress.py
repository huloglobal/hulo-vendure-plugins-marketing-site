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
    return '<div class="vp-faq">' + '\n'.join(
        f'<details><summary>{inline(q)}</summary><div>{md(a)}</div></details>' for q, a in items) + '</div>'


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


def vendure_title(slug: str) -> str | None:
    for vpp in vp.PLUGINS:
        if vpp['slug'] == slug:
            return vpp['title']
    return None


def install_note(p: dict | None = None) -> str:
    """Install context for the WordPress editions: zip upload today."""
    if p and p['slug'] in WPORG_LISTED:
        how = ('install the free plugin from WordPress.org (Plugins → Add New), or upload the zip '
               'under Plugins → Add New → Upload Plugin.')
    else:
        how = ('download the zip and upload it under Plugins → Add New → Upload Plugin. '
               'Once the free plugin is listed on WordPress.org you will also be able to install it from there.')
    return f'<p class="pf-install"><strong>Install on WordPress:</strong> {how}</p>'


def sections(blocks: list[tuple[str, str]]) -> str:
    """Content sections with alternating backgrounds: [(id_or_empty, inner_html)]."""
    out = []
    for i, (sid, inner) in enumerate(blocks):
        bg = 'bg-white' if i % 2 == 0 else 'bg-ink-50'
        id_attr = f' id="{sid}"' if sid else ''
        out.append(f'<section class="vp-section {bg}"{id_attr}>\n<div class="container-page max-w-3xl">\n{inner}\n</div>\n</section>')
    return '\n'.join(out)


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
    real = p['pricing'] if p['pricing'] is not vp.CURRENCIES else None
    prices_js = ('<script>window.HULO_PRICES_OVERRIDE = '
                 + json.dumps(vp.display_price_table(gbp['monthly'], gbp['lifetime'], real)) + ';</script>')
    eyebrow = lambda t: f'<p class="text-sm font-semibold uppercase tracking-wider text-accent-600">{t}</p>'
    h2 = lambda t: f'<h2 class="mt-3 text-3xl md:text-4xl font-bold tracking-tight text-ink-900">{t}</h2>'
    blocks = [
        ('', eyebrow('Free plugin') + h2('What the free plugin does') + md(fs.get('Description', ''))),
        ('', eyebrow('Pro add-on') + h2(html.escape(pro['name'].replace('HULO ', ''))) + pro_desc),
        ('pricing', eyebrow('Pricing') + h2('Free, then Pro when you want it') + f'''
<div class="mt-8 grid gap-6 md:grid-cols-3">
<div class="rounded-lg border border-ink-200 bg-white p-6"><p class="text-xs font-semibold uppercase tracking-wider text-ink-600">Free plugin</p><p class="vp-price-num mt-2">£0</p><p class="mt-2 text-sm text-ink-700">Free forever, GPL-licensed.</p></div>
<div class="rounded-lg border border-accent-300 bg-accent-50 p-6"><p class="text-xs font-semibold uppercase tracking-wider text-accent-700">Pro, monthly or annual</p><p class="vp-price-num mt-2"><span data-monthly-price>{html.escape(gbp['monthly'])}</span><small>/month</small></p><p class="mt-2 text-sm text-ink-700">The first 14 days are free with no card. Subscribe from the plugin page when you're ready; the first charge is taken when the 14 days end. Annual billing gets two months free. Cancel any time.</p><a href="{buy}?plan=monthly" class="btn btn-primary mt-5">Subscribe<span class="sr-only"> to {html.escape(p['title'])} Pro for WordPress</span></a></div>
<div class="rounded-lg border border-ink-200 bg-white p-6"><p class="text-xs font-semibold uppercase tracking-wider text-ink-600">Pro, lifetime</p><p class="vp-price-num mt-2" data-lifetime-price>{html.escape(gbp['lifetime'])}</p><p class="mt-2 text-sm text-ink-700">One payment for one store, including updates.</p><a href="{buy}?plan=lifetime" class="btn btn-secondary mt-5">Buy lifetime<span class="sr-only"> licence for {html.escape(p['title'])} Pro for WordPress</span></a></div>
</div>
<p class="mt-4 text-xs text-ink-600">Prices follow the currency picker at the top of the page; the checkout bills in GBP, USD, EUR, AUD and CAD. One licence covers one WordPress site.</p>
{prices_js}'''),
        ('install', eyebrow('Install') + h2('Installation') + install + f'''
<p class="mt-4 text-ink-700 leading-relaxed">For Pro, upload <code>hulo-{p['slug']}-pro-{p['pver']}.zip</code> the same way (Plugins → Add New → Upload Plugin) with the free plugin active. The 14 days start automatically, and Pro updates itself from WordPress's Plugins screen.</p>'''),
        ('faq', eyebrow('FAQ') + h2('Frequently asked questions') + f'<div class="mt-8">{faq(fs.get("Frequently Asked Questions", ""))}</div>'),
    ]
    if ext:
        blocks.append(('external-services', h2('External services').replace('mt-3 ', '') + ext))
    blocks.append(('changelog', h2('Changelog').replace('mt-3 ', '') + changelog(fs.get('Changelog', ''))))
    vd_title = vendure_title(p['slug'])
    body = f'''
<section class="vp-hero pf-wp">
<div class="container-page relative page-y">
{vp.crumbs([('WordPress plugins', f'{BASE}/'), (p['title'], None)])}
<div class="flex items-center gap-4 flex-wrap" style="margin-bottom:20px">
<img class="vp-plugin-logo" style="margin-bottom:0" src="/vendure-plugins/logos/{p['slug']}.svg" alt="" width="56" height="56">
<span class="pf-badge">For WordPress</span>
</div>
<h1 class="max-w-3xl text-4xl sm:text-5xl md:text-6xl font-bold tracking-tight text-ink-900 leading-[1.04]">{html.escape(p['title'])} for WordPress</h1>
<p class="mt-6 max-w-2xl text-lg md:text-xl text-ink-600 leading-relaxed">{inline(free['short'])}</p>
<div class="mt-8 flex flex-wrap items-center gap-3">
{free_download_html(p)}
<a href="{pro_zip}" class="btn btn-primary" download>Download Pro: 14 days free, no card</a>
<a href="#pricing" class="btn btn-secondary">Pricing</a>
<a href="#changelog" class="ml-auto inline-flex items-center text-xs text-ink-600 font-mono hover:underline" style="min-height:24px"><span class="sr-only">Changelog, version </span>v{p['fver']}</a>
</div>
{install_note(p)}
<p class="mt-4 text-sm text-ink-600">Requires WordPress {html.escape(free['headers'].get('Requires at least', '6.5'))}+ and PHP {html.escape(free['headers'].get('Requires PHP', '8.1'))}+. Works on any WordPress site; WooCommerce is optional and switches on the shop features.</p>
</div>
</section>
{sections(blocks)}
'''
    title = f'{p["title"]} for WordPress: free plugin and Pro add-on · Hulo Global'
    return (vp.header(title, f'https://huloglobal.com{BASE}/{p["slug"]}/', free['short'])
            + vp.platform_band('wp', p['slug'], p['title'], vd_title, other_exists=vd_title is not None)
            + body + footer())


def index_page(items: list[dict]) -> str:
    cards = '\n'.join(f'''<article class="vp-card pf-card">
<img class="vp-plugin-logo" src="/vendure-plugins/logos/{p['slug']}.svg" alt="" width="56" height="56">
<h3><a href="{BASE}/{p['slug']}/" class="hover:underline underline-offset-4">{html.escape(p['title'])}<span class="sr-only"> for WordPress</span></a></h3>
<p class="vp-card-tagline">{inline(p['free']['short'])}</p>
<p class="mt-4 mb-6 text-sm text-ink-600">Pro from {html.escape(p['pricing']['GBP']['monthly'])}/month · 14 days free, no card</p>
<div class="vp-card-actions mt-auto flex flex-wrap gap-2"><a href="{BASE}/{p['slug']}/" class="btn btn-secondary">Details<span class="sr-only"> about {html.escape(p['title'])} for WordPress</span></a>{free_download_html(p)}</div>
</article>''' for p in items)
    body = f'''
<section class="vp-hero pf-wp">
<div class="container-page relative page-y">
<span class="pf-badge">For WordPress</span>
<h1 class="mt-5 max-w-3xl text-4xl sm:text-5xl md:text-6xl font-bold tracking-tight text-ink-900 leading-[1.04]">WordPress plugins</h1>
<p class="mt-6 max-w-2xl text-lg md:text-xl text-ink-600 leading-relaxed">Nine plugins for payments, checkout security, fraud screening, trade credit, quotations, e-mail, reviews, analytics and geo-blocking. Each one is a free plugin that does the job on its own, plus a Pro add-on you can try for 14 days without a card.</p>
<p class="mt-4 max-w-2xl text-sm text-ink-600">Built for WordPress 6.5+ and PHP 8.1+, and they work on any WordPress site. WooCommerce is optional: when it's installed, the shop features switch on too (HPOS and the Cart/Checkout blocks supported). No other plugins required. Also available <a href="/vendure-plugins/" class="underline underline-offset-4">for Vendure</a>.</p>
{install_note()}
</div>
</section>
<section class="vp-section bg-white pf-wp">
<div class="container-page">
<h2 class="text-3xl md:text-4xl font-bold tracking-tight text-ink-900" style="margin-bottom:40px">All nine WordPress plugins</h2>
<div class="vp-cards-grid">
{cards}
</div>
</div>
</section>
'''
    return (vp.header('WordPress plugins · Hulo Global', f'https://huloglobal.com{BASE}/',
                      'Free WordPress plugins with Pro add-ons (WooCommerce optional): payments, checkout guard, fraud prevention, business credit, quotations, e-mail tracking, review requests, visitor analytics and geo-blocking.')
            + vp.platform_band('wp') + body + footer())


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
