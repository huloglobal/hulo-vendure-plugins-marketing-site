"""huloglobal.com/wordpress-plugins/: pages, downloads and update manifests
for the WordPress editions.

Page copy comes from each plugin's own readme.txt (free plugin and Pro add-on)
in /root/hulo-woo-plugins, so the site always says what the code does. Prices
come from the Vendure catalogue in build.py (the editions share them). Zips and
update.json files are taken from that repo's dist/ (tools/build.sh output);
screenshots from each free plugin's .wordpress-org/ listing assets.
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
WPORG_LISTED: list[str] = ['geo-block']  # hulo-geo-block live on WordPress.org since 2026-11-04 (0.1.1)


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
    """readme.txt inline markup: `code`, **bold**, *emphasis* and [links](…).
    Code spans are set aside first, so a '*' inside one stays as it is."""
    codes = []

    def keep(m):
        codes.append('<code>' + m.group(1) + '</code>')
        return f'\x00{len(codes) - 1}\x00'
    s = re.sub(r'`([^`]+)`', keep, html.escape(s, quote=False))
    s = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', s)
    s = re.sub(r'(?<![\w*])\*(?!\s)([^*\n]+?)(?<!\s)\*(?![\w*])', r'<em>\1</em>', s)
    s = re.sub(r'\[([^\]]+)\]\((https?://[^)\s]+)\)', r'<a href="\2" class="underline underline-offset-4">\1</a>', s)
    return re.sub(r'\x00(\d+)\x00', lambda m: codes[int(m.group(1))], s)


def plain(s: str) -> str:
    """Readme inline markup → plain text (for attributes)."""
    return html.unescape(re.sub(r'<[^>]+>', '', inline(s)))


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
    return (vp.EXPAND_BAR if len(items) > 1 else '') + '<div class="vp-faq">' + '\n'.join(
        f'<details><summary>{inline(q)}</summary><div>{md(a)}</div></details>' for q, a in items) + '</div>'


def wp_item(text: str, group_kind: str | None = None) -> dict:
    """One changelog line → {'html', 'kinds'}. A "Security:" prefix becomes the
    Security tag (the renderer adds it); "Fix:" / "Fixed:" lines are fixes; a
    "First release" line lists what the release added. Lines under a bold
    group heading (**Security**, **Fixed**, **Added**) take its kind. A line
    that merely starts with the word ("Security headers on …") is a feature,
    not a security change."""
    kinds = {group_kind} if group_kind else set()
    m = re.match(r'^Security\s*:\s*', text)
    if m:
        kinds.add('security')
        text = text[m.end():]
        text = text[:1].upper() + text[1:]
    elif re.match(r'^\*\*Security\b', text):
        kinds.add('security')
    if re.match(r'^(Fix|Fixed|Fixes)\b', text):
        kinds.add('fix')
    if re.match(r'^(First release|Added|New)\b', text):
        kinds.add('feature')
    return {'html': inline(text), 'kinds': sorted(kinds) or ['other']}


def wp_releases(body: str) -> list[dict]:
    """readme.txt '== Changelog ==' → build.py's normalised releases. Headings
    are '= 0.1.1 =' (a date in the heading, '= 0.1.2 – 2026-11-20 =', is used
    when present); '* ' lines are the changes, grouped under a bold line such
    as **Security** when the readme has one; other text is the summary."""
    rels, cur, last = [], None, None

    def group(label):
        key = (label or '').strip().rstrip(':').lower()
        cls = key if key in ('added', 'changed', 'fixed', 'security', 'removed', 'deprecated') else 'other'
        return {'label': label, 'cls': cls, 'kind': vp.HEADING_KIND.get(key), 'lines': []}

    def close():
        if cur is not None:
            cur['groups'] = [{'label': g['label'], 'cls': g['cls'], 'items': [wp_item(x, g['kind']) for x in g['lines']]}
                             for g in cur.pop('raw') if g['lines']]
    for raw in body.splitlines():
        t = raw.strip()
        head = re.match(r'^=\s*(.+?)\s*=$', t)
        if head:
            close()
            label = head.group(1)
            ver = re.match(r'v?(\d+(?:\.\d+)*(?:[-+][0-9A-Za-z.]+)?)', label)
            date = re.search(r'\b(\d{4}-\d{2}-\d{2})\b', label)
            cur, last = {'version': ver.group(1) if ver else label, 'date': date.group(1) if date else '',
                         'intro': [], 'groups': [], 'raw': [group(None)]}, None
            rels.append(cur)
            continue
        if cur is None:
            continue
        if not t:
            last = None
            continue
        bold = re.match(r'^\*\*(.+?)\*\*:?$', t)
        item = re.match(r'^[*-]\s+(.*)$', t)
        if bold:
            cur['raw'].append(group(bold.group(1).strip()))
            last = None
        elif item:
            cur['raw'][-1]['lines'].append(item.group(1))
            last = 'item'
        elif last == 'item':
            cur['raw'][-1]['lines'][-1] += ' ' + t
        elif last == 'intro':
            cur['intro'][-1] += ' ' + inline(t)
        else:
            cur['intro'].append(inline(t))
            last = 'intro'
    close()
    return rels


EDITIONS = (('free', 'Free plugin'), ('pro', 'Pro add-on'))

# An edition's changes are listed by kind, as on the Vendure pages: security
# changes first (each carries its Security tag, so no label), then Added,
# Changed and Fixed. The "Fixed:" / "New:" lead-in the label now says is
# dropped from the line.
KIND_GROUPS = (('security', None, None), ('feature', 'Added', 'added'), ('other', 'Changed', 'changed'), ('fix', 'Fixed', 'fixed'))
LEAD_IN = {'feature': r'^(?:New|Added)\s*:\s*', 'fix': r'^(?:Fix|Fixed|Fixes)\s*:\s*'}


def by_kind(items: list[dict]) -> list[dict]:
    """One edition's changes → the same changes under kind labels."""
    buckets = {k: [] for k, _, _ in KIND_GROUPS}
    for it in items:
        ks = it['kinds']
        k = ('security' if 'security' in ks else 'feature' if 'feature' in ks
             else 'fix' if 'fix' in ks else 'other')
        buckets[k].append(it)
    out = []
    for k, label, cls in KIND_GROUPS:
        if not buckets[k]:
            continue
        if label:
            out.append({'subhead': label, 'cls': cls})
        for it in buckets[k]:
            if k in LEAD_IN:
                text = re.sub(LEAD_IN[k], '', it['html'], count=1)
                if text != it['html'] and text[:1].islower():
                    text = text[:1].upper() + text[1:]
                it = dict(it, html=text)
            out.append(it)
    return out


def merged_releases(free: list[dict], pro: list[dict]) -> list[dict]:
    """The free plugin's and the Pro add-on's release notes as one list, a
    release per version (newest first), each edition's changes in its own
    group. A version only one edition shipped says so in its summary."""
    by: dict[str, dict] = {}
    for (key, name), rels in zip(EDITIONS, (free, pro)):
        for r in rels:
            m = by.setdefault(r['version'], {'version': r['version'], 'date': r['date'], 'intro': [],
                                             'groups': [], 'editions': []})
            m['date'] = m['date'] or r['date']
            m['editions'].append(name)
            m['intro'] += r['intro']
            for g in r['groups']:
                label = name if not g['label'] else f'{name}: {g["label"]}'
                m['groups'].append({'label': label, 'cls': key, 'items': by_kind(g['items'])})
    out = sorted(by.values(), key=lambda r: vp._semver(r['version']), reverse=True)
    for r in out:
        r['scope'] = f'{r["editions"][0]} only' if len(r['editions']) == 1 else ''
    return out


def whats_new_lead(p: dict) -> str:
    fv, pv = p['fver'], p['pver']
    if fv == pv:
        text = f'Latest release: <span class="font-mono">v{html.escape(fv)}</span> of the free plugin and the Pro add-on.'
    else:
        text = (f'Latest releases: the free plugin <span class="font-mono">v{html.escape(fv)}</span>, '
                f'the Pro add-on <span class="font-mono">v{html.escape(pv)}</span>.')
    return f'<p class="hu-cl-lead">{text}</p>'


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
    # The page copy comes from the source readme.txt; the zip people download
    # carries its own copy. If they differ, the zip is stale: rebuild it.
    import zipfile
    src = WOO / 'plugins' / f'hulo-{name}' / 'readme.txt'
    with zipfile.ZipFile(z) as zf:
        try:
            packed = zf.read(f'hulo-{name}/readme.txt')
        except KeyError:
            raise SystemExit(f'{z} has no hulo-{name}/readme.txt')
    if src.exists() and packed != src.read_bytes():
        raise SystemExit(f'{z.name} was built from an older readme.txt: run tools/build.sh {name.removesuffix("-pro")}, then rebuild')
    return ver, z, manifest


def fingerprint(path: Path) -> str:
    """Short content hash for download URLs: the version stays put during
    WordPress.org review, so a fresh query string is what stops Cloudflare
    serving a stale zip from its cache."""
    import hashlib
    return hashlib.sha256(path.read_bytes()).hexdigest()[:10]


def image_size(path: Path) -> tuple[int, int] | None:
    """Width and height of a PNG (IHDR), else None."""
    head = path.read_bytes()[:24]
    if head[:8] == b'\x89PNG\r\n\x1a\n' and head[12:16] == b'IHDR':
        return int.from_bytes(head[16:20], 'big'), int.from_bytes(head[20:24], 'big')
    return None


def screenshot_captions(body: str) -> dict[int, str]:
    """'== Screenshots ==' numbered list → {number: caption}."""
    caps, cur = {}, None
    for line in body.splitlines():
        m = re.match(r'^\s*(\d+)\.\s+(.*)$', line)
        if m:
            cur = int(m.group(1))
            caps[cur] = m.group(2).strip()
        elif line.strip() and cur is not None:
            caps[cur] += ' ' + line.strip()
        else:
            cur = None
    return caps


def screenshots(slug: str, readme: dict) -> list[dict]:
    """The free plugin's WordPress.org screenshots that exist on disk, with the
    readme's caption for each (a plugin without any gets no gallery)."""
    src = WOO / 'plugins' / f'hulo-{slug}' / '.wordpress-org'
    caps = screenshot_captions(readme['sections'].get('Screenshots', ''))
    shots = []
    for f in src.glob('screenshot-*.*') if src.is_dir() else []:
        m = re.fullmatch(r'screenshot-(\d+)\.(png|jpe?g|gif|webp)', f.name, re.I)
        if not m:
            continue
        n = int(m.group(1))
        caption = caps.get(n, f'Screenshot {n}')
        shots.append({'n': n, 'src': f, 'caption': caption, 'size': image_size(f),
                      'url': f'{BASE}/{slug}/screenshots/{f.name}?v={fingerprint(f)}'})
    return sorted(shots, key=lambda s: s['n'])


def load(slug: str) -> dict:
    free = parse_readme(WOO / 'plugins' / f'hulo-{slug}' / 'readme.txt')
    pro = parse_readme(WOO / 'plugins' / f'hulo-{slug}-pro' / 'readme.txt')
    fver, fzip, fman = dist_files(slug)
    pver, pzip, pman = dist_files(slug + '-pro')
    title = re.sub(r'^HULO\s+|\s+for (WooCommerce|WordPress)$', '', free['name'])
    return {'slug': slug, 'title': title, 'free': free, 'pro': pro, 'fver': fver, 'fzip': fzip, 'fman': fman,
            'pver': pver, 'pzip': pzip, 'pman': pman, 'fv': fingerprint(fzip), 'pv': fingerprint(pzip), 'pricing': pricing_for(slug),
            'releases': merged_releases(
                vp.published_only(wp_releases(free['sections'].get('Changelog', '')), fver, f'hulo-{slug}'),
                vp.published_only(wp_releases(pro['sections'].get('Changelog', '')), pver, f'hulo-{slug}-pro')),
            'shots': screenshots(slug, free)}


def zero_prices() -> dict:
    """The free plugin's price, 0, written in each currency the picker offers."""
    return {cc: vp.CURRENCIES[cc]['symbol'] + '0' for cc in vp.PURCHASABLE_CURRENCIES if cc in vp.CURRENCIES}


def free_zip_url(p: dict) -> str:
    return f'{BASE}/{p["slug"]}/hulo-{p["slug"]}-{p["fver"]}.zip?v={p["fv"]}'


def pro_zip_url(p: dict) -> str:
    return f'{BASE}/{p["slug"]}-pro/hulo-{p["slug"]}-pro-{p["pver"]}.zip?v={p["pv"]}'


def free_download_html(p: dict) -> str:
    if p['slug'] in WPORG_LISTED:
        return (f'<a href="https://wordpress.org/plugins/hulo-{p["slug"]}/" class="btn btn-secondary">Free plugin on WordPress.org</a>')
    return (f'<a href="{free_zip_url(p)}" class="btn btn-secondary" download>'
            f'Download free plugin (v{p["fver"]})</a>')


def vendure_title(slug: str) -> str | None:
    for vpp in vp.PLUGINS:
        if vpp['slug'] == slug:
            return vpp['title']
    return None


def install_note(items: list[dict]) -> str:
    """Install context for the index: zip upload, plus WordPress.org for the
    free plugins listed there (WPORG_LISTED)."""
    how = 'download the zip and upload it under Plugins → Add New → Upload Plugin.'
    listed = [p['title'] for p in items if p['slug'] in WPORG_LISTED]
    if listed:
        names = ', '.join(listed[:-1]) + (' and ' if len(listed) > 1 else '') + listed[-1]
        how += (f' The free {names} plugin{"s" if len(listed) > 1 else ""} also install{"" if len(listed) > 1 else "s"} '
                'from WordPress.org (Plugins → Add New).')
    else:
        how += ' Once the free plugins are listed on WordPress.org you will also be able to install them from there.'
    return f'<p class="pf-install"><strong>Install on WordPress:</strong> {how}</p>'


def install_box(p: dict) -> str:
    """The hero's install box: one tab per way in (WordPress.org when listed,
    the zip, the Pro add-on). Without JavaScript the three read in order."""
    slug = p['slug']
    tabs = []
    if slug in WPORG_LISTED:
        tabs.append(('From WordPress.org',
                     f'<p>Install {html.escape(p["free"]["name"])} from Plugins → Add New and activate it.</p>'
                     f'<p><a href="https://wordpress.org/plugins/hulo-{slug}/" class="underline underline-offset-4">Free plugin on WordPress.org</a></p>'
                     f'<p>Or with WP-CLI:</p>{vp.code_block(f"wp plugin install hulo-{slug} --activate", "WP-CLI command")}'))
        upload = 'Download the zip and upload it under Plugins → Add New → Upload Plugin.'
    else:
        upload = ('Download the zip and upload it under Plugins → Add New → Upload Plugin. '
                  'Once the free plugin is listed on WordPress.org you will also be able to install it from there.')
    tabs.append(('Upload the zip',
                 f'<p>{upload}</p><a href="{free_zip_url(p)}" class="btn btn-secondary" download>'
                 f'Download free plugin (v{p["fver"]})</a>'))
    tabs.append(('Pro add-on',
                 f'<p>Upload <code>hulo-{slug}-pro-{p["pver"]}.zip</code> the same way (Plugins → Add New → Upload Plugin) '
                 'with the free plugin active. The 14 days start automatically, and Pro updates itself from '
                 'WordPress\'s Plugins screen.</p>'
                 f'<a href="{pro_zip_url(p)}" class="btn btn-secondary" download>Download Pro (v{p["pver"]})</a>'))
    panels = ''.join(f'<div data-tab="{label}"><p class="hu-tab-h">{label}</p>{inner}</div>' for label, inner in tabs)
    return ('<div class="pf-install hu-install" data-tabs data-tabs-label="Ways to install">'
            '<p class="hu-install-lead"><strong>Install on WordPress:</strong> the free plugin first, '
            'then the Pro add-on if you want it.</p>' + panels + '</div>')


UPLOAD_STEP = ('Download the zip from this page, upload it under Plugins → Add New → Upload Plugin '
               'and activate it.')


def installation(slug: str, body: str) -> str:
    """The readme's == Installation ==, with step 1 reworded for a free plugin
    that is not listed on WordPress.org yet (WPORG_LISTED): searching Plugins →
    Add New cannot find it, so the step says to upload the zip. The rest of
    the step, and every other step, is the readme's own text."""
    if slug in WPORG_LISTED:
        return body
    lines = body.splitlines()
    for i, line in enumerate(lines):
        m = re.match(r'^(\s*1\.\s+)(.*)$', line)
        if not m:
            continue
        first, *rest = re.split(r'(?<=[.!?])\s+', m.group(2), maxsplit=1)
        if 'Add New' in first and 'Upload Plugin' not in first:
            lines[i] = m.group(1) + UPLOAD_STEP + (' ' + rest[0] if rest else '')
        break
    return '\n'.join(lines)


def sections(blocks: list[tuple]) -> str:
    """Content sections with alternating backgrounds: [(id_or_empty, inner_html[, wide])]."""
    out = []
    for i, block in enumerate(blocks):
        sid, inner = block[0], block[1]
        width = '' if len(block) > 2 and block[2] else ' max-w-3xl'
        bg = 'bg-white' if i % 2 == 0 else 'bg-ink-50'
        id_attr = f' id="{sid}"' if sid else ''
        out.append(f'<section class="vp-section {bg} pf-wp"{id_attr}>\n<div class="container-page{width}">\n{inner}\n</div>\n</section>')
    return '\n'.join(out)


# Thumbnail widths (WebP, from build_thumbs.mjs); the grid shows a shot at
# up to ~480 CSS px (two columns at 1023 px), so 480/800 cover 1x and 2x and
# 1280 covers 3x phones. The full PNG stays the link (the lightbox image).
THUMB_WIDTHS = [480, 800, 1280]
THUMB_SIZES = '(min-width: 1024px) 22rem, (min-width: 640px) calc(50vw - 2.5rem), calc(100vw - 2rem)'


def make_thumbs(items: list[dict]) -> None:
    """Write every screenshot's WebP thumbnails next to it in dist, in one
    node call, and give each shot its srcset. If node or sharp is missing
    the gallery simply uses the full-size PNG, as before."""
    import hashlib
    import subprocess
    jobs, shots = [], []
    for p in items:
        for s in p['shots']:
            dest = OUT / p['slug'] / 'screenshots'
            stem = s['src'].stem
            jobs.append({'src': str(s['src']), 'out': str(dest / f'{stem}-{{w}}.webp'), 'widths': THUMB_WIDTHS})
            v = hashlib.sha256(s['src'].read_bytes() + repr(THUMB_WIDTHS).encode()).hexdigest()[:10]
            shots.append((s, stem, v, p['slug']))
    if not jobs:
        return
    try:
        subprocess.run(['node', str(HERE / 'build_thumbs.mjs')], input=json.dumps(jobs).encode(),
                       check=True, capture_output=True, timeout=300)
    except Exception as e:
        err = getattr(e, 'stderr', b'') or b''
        print(f'  WARNING thumbnails not made ({e}; {err.decode()[-300:]}); the gallery uses the full-size images')
        return
    for s, stem, v, slug in shots:
        s['srcset'] = ', '.join(f'{BASE}/{slug}/screenshots/{stem}-{w}.webp?v={v} {w}w' for w in THUMB_WIDTHS)


def gallery(p: dict) -> str:
    shots = p['shots']
    items = []
    for s in shots:
        size = s['size']
        dims = f' width="{size[0]}" height="{size[1]}"' if size else ''
        img = f'<img src="{s["url"]}" alt="Screenshot {s["n"]}"{dims} loading="lazy" decoding="async">'
        if s.get('srcset'):
            img = f'<picture><source type="image/webp" srcset="{s["srcset"]}" sizes="{THUMB_SIZES}">{img}</picture>'
        items.append(
            f'<li><figure><a class="hu-shot" href="{s["url"]}" data-caption="{html.escape(plain(s["caption"]))}" '
            f'aria-describedby="shot-{s["n"]}-cap">{img}</a>'
            f'<figcaption id="shot-{s["n"]}-cap"><span class="hu-shot-n">{s["n"]}.</span> {inline(s["caption"])}</figcaption></figure></li>')
    return f'<ul class="hu-shots" data-gallery>{"".join(items)}</ul>'


def plugin_page(p: dict) -> str:
    free, pro, gbp = p['free'], p['pro'], p['pricing']['GBP']
    slug = p['slug']
    buy = f'{vp.BUY_BASE}/wordpress-{slug}'
    fs, ps = free['sections'], pro['sections']
    install = md(installation(slug, fs.get('Installation', '')))
    pro_desc = md(ps.get('Description', ''))
    ext = ''
    for label, sec in (('Free plugin', fs.get('External services')), ('Pro add-on', ps.get('External services'))):
        if sec:
            ext += f'<h3 class="mt-8 text-lg font-semibold text-ink-900">{label}</h3>' + md(sec)
    real = p['pricing'] if p['pricing'] is not vp.CURRENCIES else None
    # Annual: the licence server's buy-page prices (build.annual_prices()).
    annual = vp.annual_prices(slug, p['pricing'])
    if not vp.has_full_annual(annual):
        annual = {}
    prices_js = ('<script>window.HULO_PRICES_OVERRIDE = '
                 + json.dumps(vp.display_price_table(gbp['monthly'], gbp['lifetime'], real, annual)) + ';</script>')
    eyebrow = lambda t, extra='': f'<p class="text-sm font-semibold uppercase tracking-wider text-accent-600{extra}">{t}</p>'
    h2 = lambda t: f'<h2 class="mt-3 text-3xl md:text-4xl font-bold tracking-tight text-ink-900">{t}</h2>'
    pro_name = f'{html.escape(p["title"])} Pro for WordPress'

    features = f'''<div class="hu-tabs hu-tabs-lg hu-tabs-stack" data-tabs data-tabs-label="Free plugin or Pro add-on">
<div data-tab="Free plugin" id="features-free">{eyebrow('Free plugin', ' hu-tab-h')}{h2('What the free plugin does')}{md(fs.get('Description', ''))}</div>
<div data-tab="Pro add-on" id="features-pro">{eyebrow('Pro add-on', ' hu-tab-h')}{h2(html.escape(pro['name'].replace('HULO ', '')))}{pro_desc}</div>
</div>'''

    # Owner sign-off: trial wording. The no-card 14 days are the evaluation
    # Pro starts on install; the website checkout these buttons open asks for
    # a card (its own wording: "card required, nothing charged until day 15").
    sub_text = ('Install Pro and its first 14 days are free with no card. Subscribe from the plugin page when you\'re ready: '
                'the first charge is taken when the 14 days end. Subscribing on this website starts a 14-day trial instead, '
                'with a card at checkout and nothing charged until day 15. Annual billing gets two months free. Cancel any time.')
    plans = f'''<div class="hu-plan" data-plan="monthly" data-plan-unit="a month">
<p class="text-xs font-semibold uppercase tracking-wider text-accent-700">{'Pro, monthly' if annual else 'Pro, monthly or annual'}</p>
<p class="vp-price-num mt-2"><span data-monthly-price data-plan-price>{html.escape(gbp['monthly'])}</span><small>/month</small></p>
<p class="mt-2 text-sm text-ink-700">{sub_text}</p>
<a href="{buy}?plan=monthly" class="btn btn-primary mt-5">Subscribe<span class="sr-only"> monthly to {pro_name}</span></a>
</div>'''
    if annual:
        plans += f'''
<div class="hu-plan" data-plan="annual" data-plan-unit="a year">
<p class="text-xs font-semibold uppercase tracking-wider text-accent-700">Pro, annual</p>
<p class="vp-price-num mt-2"><span data-annual-price data-plan-price>{html.escape(annual['GBP'])}</span><small>/year</small></p>
<p class="mt-2 text-sm text-ink-700">{sub_text}</p>
<a href="{buy}?plan=annual" class="btn btn-primary mt-5">Subscribe<span class="sr-only"> yearly to {pro_name}</span></a>
</div>'''
    plans += f'''
<div class="hu-plan" data-plan="lifetime" data-plan-unit="one-off">
<p class="text-xs font-semibold uppercase tracking-wider text-accent-700">Pro, lifetime</p>
<p class="vp-price-num mt-2"><span data-lifetime-price data-plan-price>{html.escape(gbp['lifetime'])}</span></p>
<p class="mt-2 text-sm text-ink-700">One payment for one site. Never expires; includes 12 months of updates.</p>
<a href="{buy}?plan=lifetime" class="btn btn-secondary mt-5">Buy lifetime<span class="sr-only"> licence for {pro_name}</span></a>
</div>'''
    periods = ['monthly', 'lifetime'] + (['annual'] if annual else [])
    pricing = eyebrow('Pricing') + h2('Free, then Pro when you want it') + f'''
<div class="mt-8 grid gap-6 md:grid-cols-2">
<div class="min-w-0 rounded-lg border border-ink-200 bg-white p-6"><p class="text-xs font-semibold uppercase tracking-wider text-ink-600">Free plugin</p><p class="vp-price-num mt-2"><span data-ccy-prices="{html.escape(json.dumps(zero_prices(), ensure_ascii=False))}">£0</span></p><p class="mt-2 text-sm text-ink-700">Free forever, GPL-licensed.</p></div>
<div class="min-w-0 rounded-lg border border-accent-300 bg-accent-50 p-6 hu-plans" data-period>
{vp.period_switch(periods)}
{plans}
</div>
</div>
<p class="mt-4 text-xs text-ink-600">Prices follow the currency picker at the top of the page; the checkout bills in GBP, USD, EUR, AUD and CAD. One licence covers one WordPress site.</p>
{prices_js}'''

    blocks = [('features', features)]
    if p['shots']:
        blocks.append(('screenshots', '<div class="hu-shots-head">' + h2('Screenshots').replace('mt-3 ', '') + '</div>' + gallery(p), True))
    blocks += [
        ('pricing', pricing),
        ('install', eyebrow('Install') + h2('Installation') + install + f'''
<p class="mt-4 text-ink-700 leading-relaxed">For Pro, upload <code>hulo-{slug}-pro-{p['pver']}.zip</code> the same way (Plugins → Add New → Upload Plugin) with the free plugin active. The 14 days start automatically, and Pro updates itself from WordPress's Plugins screen.</p>'''),
        ('faq', eyebrow('FAQ') + h2('Frequently asked questions') + f'<div class="mt-8">{faq(fs.get("Frequently Asked Questions", ""))}</div>'),
    ]
    if ext:
        blocks.append(('external-services', h2('External services').replace('mt-3 ', '') + ext))
    notes = vp.release_notes(p['releases'], f'HULO {p["title"]} for WordPress', lead_html=whats_new_lead(p))
    if notes:
        # #changelog: where the release notes used to be, for old links.
        blocks.append(('whats-new', '<span id="changelog"></span>' + eyebrow('Changelog') + h2("What's new") + notes))

    nav = [('overview', 'Overview'), ('features', 'Features')]
    if p['shots']:
        nav.append(('screenshots', 'Screenshots'))
    nav += [('pricing', 'Pricing'), ('install', 'Install'), ('faq', 'FAQ')]
    if notes:
        nav.append(('whats-new', "What's new"))
    vd_title = vendure_title(slug)
    body = f'''
<section class="vp-hero pf-wp" id="overview">
<div class="container-page relative page-y">
{vp.crumbs([('WordPress plugins', f'{BASE}/'), (p['title'], None)])}
<div class="flex items-center gap-4 flex-wrap" style="margin-bottom:20px">
<img class="vp-plugin-logo" style="margin-bottom:0" src="/vendure-plugins/logos/{slug}.svg" alt="" width="56" height="56">
<span class="pf-badge">For WordPress</span>
</div>
<h1 class="max-w-3xl text-4xl sm:text-5xl md:text-6xl font-bold tracking-tight text-ink-900 leading-[1.04]">HULO {html.escape(p['title'])} for WordPress</h1>
<p class="mt-6 max-w-2xl text-lg md:text-xl text-ink-600 leading-relaxed">{inline(free['short'])}</p>
<div class="mt-8 flex flex-wrap items-center gap-3">
{free_download_html(p)}
<a href="{pro_zip_url(p)}" class="btn btn-primary" download>Download Pro: 14 days free, no card</a>
<a href="#pricing" class="btn btn-secondary">Pricing</a>
<a href="{'#whats-new' if notes else '#install'}" class="hu-ver-link hu-ver-hero">What's new<span class="sr-only">, version</span> <span class="hu-ver">v{p['fver']}</span></a>
</div>
{install_box(p)}
<p class="mt-4 text-sm text-ink-600">Requires WordPress {html.escape(free['headers'].get('Requires at least', '6.5'))}+ and PHP {html.escape(free['headers'].get('Requires PHP', '8.1'))}+. Works on any WordPress site.</p>
</div>
</section>
{vp.section_nav(nav, 'wp')}
{sections(blocks)}
'''
    title = f'HULO {p["title"]} for WordPress: free plugin and Pro add-on · Hulo Global'
    return (vp.header(title, f'https://huloglobal.com{BASE}/{slug}/', free['short'], secnav=True)
            + vp.platform_band('wp', slug, p['title'], vd_title, other_exists=vd_title is not None)
            + body + footer())


def index_page(items: list[dict]) -> str:
    def card(p: dict) -> str:
        monthly = {cc: row['monthly'] for cc, row in p['pricing'].items() if cc in vp.PURCHASABLE_CURRENCIES}
        notes_href = f'{BASE}/{p["slug"]}/#whats-new' if p['releases'] else f'{BASE}/{p["slug"]}/'
        return f'''<article class="vp-card pf-card" data-cats="{' '.join(vp.categories_of(p['slug']))}" data-keywords="{html.escape(vp.card_keywords(p['slug']))}">
<div class="vp-card-top">
<img class="vp-plugin-logo" src="/vendure-plugins/logos/{p['slug']}.svg" alt="" width="56" height="56">
<a href="{notes_href}" class="hu-ver-link">What's new<span class="sr-only"> in {html.escape(p['title'])} for WordPress, version</span> <span class="hu-ver">v{p['fver']}</span></a>
</div>
<h3><a href="{BASE}/{p['slug']}/" class="hover:underline underline-offset-4">{html.escape(p['title'])}<span class="sr-only"> for WordPress</span></a></h3>
<p class="vp-card-tagline">{inline(p['free']['short'])}</p>
<p class="mt-4 mb-6 text-sm text-ink-600">Pro from <span data-ccy-prices="{html.escape(json.dumps(monthly, ensure_ascii=False))}">{html.escape(p['pricing']['GBP']['monthly'])}</span>/month · 14 days free, no card</p>
<div class="vp-card-actions mt-auto flex flex-wrap gap-2"><a href="{BASE}/{p['slug']}/" class="btn btn-secondary">Details<span class="sr-only"> about {html.escape(p['title'])} for WordPress</span></a>{free_download_html(p)}</div>
</article>'''
    cards = '\n'.join(card(p) for p in items)
    body = f'''
<section class="vp-hero pf-wp">
<div class="container-page relative page-y">
<span class="pf-badge">For WordPress</span>
<h1 class="mt-5 max-w-3xl text-4xl sm:text-5xl md:text-6xl font-bold tracking-tight text-ink-900 leading-[1.04]">WordPress plugins</h1>
<p class="mt-6 max-w-2xl text-lg md:text-xl text-ink-600 leading-relaxed">Nine plugins for payments, checkout security, fraud screening, trade credit, quotations, e-mail, reviews, analytics and geo-blocking. Each one is a free plugin that does the job on its own, plus a Pro add-on you can try for 14 days without a card.</p>
<p class="mt-4 max-w-2xl text-sm text-ink-600">Built for WordPress 6.5+ and PHP 8.1+, and they work on any WordPress site, with HULO Payments for taking payments. They also work alongside WooCommerce if you run it. No other plugins required. Also available <a href="/vendure-plugins/" class="underline underline-offset-4">for Vendure</a>.</p>
{install_note(items)}
</div>
</section>
<section class="vp-section bg-white pf-wp">
<div class="container-page" data-catalog>
<h2 class="text-3xl md:text-4xl font-bold tracking-tight text-ink-900" style="margin-bottom:40px">All nine WordPress plugins</h2>
{vp.catalog_controls([p['slug'] for p in items], 'WordPress plugins')}
<div class="vp-cards-grid">
{cards}
</div>
{vp.catalog_empty('WordPress plugins')}
</div>
</section>
'''
    return (vp.header('WordPress plugins · Hulo Global', f'https://huloglobal.com{BASE}/',
                      'Free WordPress plugins with Pro add-ons: payments, checkout guard, fraud prevention, business credit, quotations, e-mail tracking, review requests, visitor analytics and geo-blocking.')
            + vp.platform_band('wp') + body + footer())


def wp_nav() -> str:
    return ''


def footer() -> str:
    return vp.FOOTER


def write_manifest(src: Path, dest: Path, fv: str) -> None:
    """update.json with a fingerprinted download URL (see fingerprint())."""
    m = json.loads(src.read_text())
    m['download_url'] = m['download_url'].split('?')[0] + '?v=' + fv
    dest.write_text(json.dumps(m, indent=2), encoding='utf-8')


def pro_stub(p: dict) -> str:
    """Pro's update.json points its homepage at <slug>-pro/; send people to the plugin page."""
    url = f'{BASE}/{p["slug"]}/'
    return (f'<!doctype html><html lang="en"><head><meta charset="utf-8"><title>{html.escape(p["title"])} Pro</title>'
            f'<link rel="canonical" href="https://huloglobal.com{url}"><meta http-equiv="refresh" content="0; url={url}">'
            f'</head><body><a href="{url}">{html.escape(p["title"])} for WordPress</a></body></html>')


ART_FILES = ('icon-128x128.png', 'icon-256x256.png', 'banner-772x250.png', 'banner-1544x500.png')


def main():
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    items = [load(s) for s in SLUGS]
    (OUT / 'index.html').write_text(index_page(items), encoding='utf-8')
    for p in items:
        d = OUT / p['slug']
        d.mkdir()
        if p['shots']:
            (d / 'screenshots').mkdir()
            for s in p['shots']:
                shutil.copy2(s['src'], d / 'screenshots' / s['src'].name)
    make_thumbs(items)
    for p in items:
        d = OUT / p['slug']
        (d / 'index.html').write_text(plugin_page(p), encoding='utf-8')
        shutil.copy2(p['fzip'], d / p['fzip'].name)
        write_manifest(p['fman'], d / 'update.json', p['fv'])
        dp = OUT / (p['slug'] + '-pro')
        dp.mkdir()
        (dp / 'index.html').write_text(pro_stub(p), encoding='utf-8')
        shutil.copy2(p['pzip'], dp / p['pzip'].name)
        write_manifest(p['pman'], dp / 'update.json', p['pv'])
        # The Pro add-on's update screens show the icons and banners next to
        # its update.json (lib/hulo-licence Client::art()): the free plugin's art.
        art = WOO / 'plugins' / f'hulo-{p["slug"]}' / '.wordpress-org'
        for name in ART_FILES:
            if (art / name).exists():
                shutil.copy2(art / name, dp / name)
            else:
                print(f'WARNING: {p["slug"]}: no {name} for the Pro update screens')
    vp.emit_assets()
    shots = sum(len(p['shots']) for p in items)
    print(f'Wrote {len(items)} WordPress plugin pages, {2 * len(items)} zips and manifests, {shots} screenshots to {OUT}')


if __name__ == '__main__':
    main()
