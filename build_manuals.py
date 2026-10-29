#!/usr/bin/env python3
"""
Build user manuals for each plugin at
  /vendure-plugins/<slug>/docs/index.html

Manuals are self-contained HTML pages with the same look as the
marketing pages plus SVG illustrations of the key admin screens.
"""
from pathlib import Path
import html
import re
import textwrap

HERE = Path(__file__).parent
OUT = HERE / 'dist' / 'vendure-plugins'
ASTRO_CSS = '/_astro/index@_@astro.CpJRZGi5.css'

DOC_HEAD = '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{title}</title>
<meta name="description" content="{description}">
<link rel="canonical" href="{canonical}">
<link rel="icon" type="image/svg+xml" href="/favicon.svg?v=2">
<link rel="stylesheet" href="''' + ASTRO_CSS + '''">
<style>
.doc {{ display: grid; grid-template-columns: minmax(0, 1fr); gap: 24px; }}
@media (min-width: 1024px) {{ .doc {{ grid-template-columns: 240px minmax(0, 1fr); gap: 48px; align-items: start; }} }}
.doc-body {{ min-width: 0; }}
.doc-toc {{ position: sticky; top: 96px; }}
.doc-toc ul {{ list-style: none; padding: 0; margin: 0; }}
.doc-toc li {{ margin-bottom: 6px; }}
.doc-toc a {{ display: block; padding: 6px 10px; border-radius: 6px; font-size: 13px; color: var(--color-ink-700, #334155); text-decoration: none; }}
.doc-toc a:hover {{ background: var(--color-ink-50, #f8fafc); color: var(--color-ink-900); }}
.doc-toc a.lvl-2 {{ padding-left: 22px; font-size: 12px; color: var(--color-ink-500, #64748b); }}
.doc-body h2 {{ margin-top: 48px; font-size: 28px; font-weight: 700; color: var(--color-ink-900, #0f172a); scroll-margin-top: 96px; }}
.doc-body h2:first-child {{ margin-top: 0; }}
.doc-body h3 {{ margin-top: 28px; font-size: 20px; font-weight: 600; color: var(--color-ink-900); scroll-margin-top: 96px; }}
.doc-body p {{ font-size: 16px; line-height: 1.7; color: var(--color-ink-700, #334155); margin: 16px 0; }}
.doc-body ul, .doc-body ol {{ font-size: 16px; line-height: 1.75; color: var(--color-ink-700); padding-left: 22px; margin: 12px 0; }}
.doc-body li {{ margin: 6px 0; }}
.doc-body code {{ font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 13px; background: var(--color-ink-50, #f8fafc); padding: 2px 6px; border-radius: 4px; border: 1px solid var(--color-ink-100, #e2e8f0); color: var(--color-ink-900); }}
.doc-code {{ background: #0f172a; color: #f1f5f9; padding: 18px 22px; border-radius: 10px; font-size: 13px; line-height: 1.6; font-family: ui-monospace, SFMono-Regular, Menlo, monospace; overflow-x: auto; margin: 18px 0; }}
.doc-code .c {{ color: #64748b; }}
.doc-code .k {{ color: #fbbf24; }}
.doc-code .s {{ color: #86efac; }}
.callout {{ background: var(--color-accent-50, #fffbeb); border-left: 4px solid var(--color-accent-500, #f59e0b); border-radius: 8px; padding: 14px 18px; margin: 18px 0; font-size: 14px; color: var(--color-ink-800, #1e293b); }}
.callout.warn {{ background: #fef2f2; border-color: #ef4444; }}
.screenshot {{ margin: 22px 0; border: 1px solid var(--color-ink-200, #e2e8f0); border-radius: 12px; overflow: hidden; background: #fff; box-shadow: 0 1px 3px rgba(15,23,42,.08); }}
.screenshot-caption {{ padding: 10px 14px; background: var(--color-ink-50, #f8fafc); border-top: 1px solid var(--color-ink-100); font-size: 12px; color: var(--color-ink-600); text-align: center; }}
.doc-body .table-wrap {{ overflow-x: auto; -webkit-overflow-scrolling: touch; margin: 18px 0; border: 1px solid var(--color-ink-100); border-radius: 10px; max-width: 100%; }}
.doc-body .table-wrap::-webkit-scrollbar {{ height: 8px; }}
.doc-body .table-wrap::-webkit-scrollbar-thumb {{ background: var(--color-ink-300, #cbd5e1); border-radius: 4px; }}
.doc-body table {{ width: max-content; min-width: 100%; border-collapse: collapse; font-size: 14px; margin: 0; }}
.doc-body th, .doc-body td {{ text-align: left; padding: 12px 16px; border-bottom: 1px solid var(--color-ink-100); white-space: nowrap; }}
.doc-body td {{ white-space: normal; max-width: 380px; }}
.doc-body tr:last-child th, .doc-body tr:last-child td {{ border-bottom: 0; }}
.doc-body th {{ background: var(--color-ink-50); font-weight: 600; color: var(--color-ink-900); }}
.doc-body td code {{ background: transparent; border: 0; padding: 0; font-size: 13px; white-space: nowrap; }}
/* Screenshot SVGs scale to viewport — no min-width so they shrink on mobile. */
.doc-body .screenshot {{ max-width: 100%; }}
.doc-body .screenshot svg {{ width: 100%; max-width: 100%; height: auto; display: block; }}
.doc-body .doc-code {{ overflow-x: auto; -webkit-overflow-scrolling: touch; max-width: 100%; }}
/* TOC: stay inside its column on mobile, hide horizontally if anything spills */
.doc-toc {{ min-width: 0; }}
.doc-toc ul, .doc-toc li, .doc-toc a {{ max-width: 100%; }}
.doc-toc a {{ min-height: 40px; }}
/* On mobile the TOC is a thin top-of-page block, not a full sidebar */
@media (max-width: 1023px) {{
    .doc-toc {{ background: var(--color-ink-50, #f8fafc); border-radius: 12px; padding: 14px 16px; position: relative !important; top: auto; }}
    .doc-toc ul {{ display: flex; flex-wrap: wrap; gap: 6px; }}
    .doc-toc li {{ margin: 0; }}
    .doc-toc a {{ padding: 8px 12px; min-height: 36px; background: #fff; border: 1px solid var(--color-ink-100); border-radius: 6px; font-size: 13px; }}
}}
</style>
</head>
<body>
<a href="#main" class="skip-link">Skip to content</a>
<header class="sticky top-0 z-40 border-b border-ink-100 bg-white/85 backdrop-blur supports-[backdrop-filter]:bg-white/70">
<div class="container-page flex items-center justify-between py-4">
<a href="/" class="flex items-center gap-2.5 group">
<span class="grid size-9 place-items-center rounded-lg bg-ink-900 text-white font-bold tracking-tight text-sm">HG</span>
<span class="font-bold text-ink-900 tracking-tight text-lg">Hulo Global</span>
</a>
<nav class="hidden md:block">
<ul class="flex items-center gap-6 text-sm font-medium text-ink-700">
<li><a href="/" class="hover:text-ink-900 py-3 px-2 inline-block">Home</a></li>
<li><a href="/vendure-plugins/" class="hover:text-ink-900 py-3 px-2 inline-block">Vendure plugins</a></li>
<li><a href="/vendure-plugins/{slug}/" class="hover:text-ink-900 py-3 px-2 inline-block">← Back to {title_short}</a></li>
</ul>
</nav>
</div>
</header>
<main id="main" class="container-page py-12 md:py-16">
<nav class="mb-6 text-sm text-ink-600">
<a href="/vendure-plugins/" class="hover:text-ink-900">Vendure plugins</a>
<span class="mx-2 text-ink-400">/</span>
<a href="/vendure-plugins/{slug}/" class="hover:text-ink-900">{title_short}</a>
<span class="mx-2 text-ink-400">/</span>
<span class="text-ink-900 font-medium">Manual</span>
</nav>
<h1 class="text-4xl md:text-5xl font-bold tracking-tight text-ink-900 mb-8">{title_short} — User Manual</h1>
<div class="doc">
'''

DOC_FOOT = '''
</div>
</main>
</body>
</html>
'''


def svg_panel(title, body_lines, width=720, height=360):
    """Render a labeled SVG mockup of an admin panel. Text is sized large
    enough to stay legible when the SVG is scaled down to mobile width.
    Carries role=img + title/desc for screen readers."""
    desc_lines = []
    lines = ''
    for i, line in enumerate(body_lines):
        if line.startswith('::'):
            items = line[2:].split('|')
            x = 30
            y = 110 + 38 * i
            row = ''
            for item in items:
                w = 18 + 9 * len(item)
                row += f'<rect x="{x}" y="{y - 16}" width="{w}" height="26" rx="13" fill="#dbeafe" stroke="#93c5fd"/><text x="{x + w/2}" y="{y + 3}" text-anchor="middle" font-size="13" font-family="system-ui" fill="#1e3a8a">{html.escape(item)}</text>'
                x += w + 10
            lines += row
            desc_lines.append(' / '.join(items))
        elif line.startswith('//'):
            lbl = line[2:]
            y = 110 + 38 * i
            lines += f'<rect x="30" y="{y - 16}" width="360" height="30" rx="5" fill="#fff" stroke="#cbd5e1"/><text x="40" y="{y + 4}" font-size="14" font-family="ui-monospace,monospace" fill="#64748b">{html.escape(lbl)}</text>'
            desc_lines.append(f'Input: {lbl}')
        elif line.startswith('=='):
            lines += f'<text x="30" y="{110 + 38 * i}" font-size="15" font-weight="600" font-family="system-ui" fill="#0f172a">{html.escape(line[2:])}</text>'
            desc_lines.append(line[2:])
        else:
            lines += f'<text x="30" y="{110 + 38 * i}" font-size="14" font-family="system-ui" fill="#475569">{html.escape(line)}</text>'
            desc_lines.append(line)

    desc = ' — '.join(desc_lines).replace('"', "'")
    title_id = re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-')

    return f'''<svg viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg" preserveAspectRatio="xMidYMid meet" role="img" aria-labelledby="{title_id}-t {title_id}-d" style="width: 100%; height: auto; display: block;">
<title id="{title_id}-t">{html.escape(title)}</title>
<desc id="{title_id}-d">Admin panel mockup. {html.escape(desc)}</desc>
<rect width="{width}" height="{height}" fill="#fafafa"/>
<rect x="0" y="0" width="{width}" height="52" fill="#0f1419"/>
<text x="20" y="33" font-size="16" font-weight="600" font-family="system-ui" fill="#fff">Vendure Admin</text>
<circle cx="{width-30}" cy="26" r="11" fill="#1e293b"/>
<text x="20" y="85" font-size="20" font-weight="700" font-family="system-ui" fill="#0f172a">{html.escape(title)}</text>
{lines}
</svg>'''


# ─────────────────────────────────────────────────────────────────────────
# Email Tracking
# ─────────────────────────────────────────────────────────────────────────

EMAIL_TRACKING_MANUAL = {
    'slug': 'email-tracking',
    'title_short': 'Email Tracking',
    'sections': [
        ('overview', 'Overview', '''
<p><strong>Email Tracking</strong> logs every transactional email your Vendure server sends. It wraps the <code>@vendure/email-plugin</code> sender so opens and clicks are tracked automatically, plus exposes a service for ad-hoc sends from your own plugin code.</p>
<p>Data captured per email:</p>
<ul>
<li>Send: recipient, subject, type, related order / customer / invoice, the SMTP response, the SMTP <code>messageId</code>.</li>
<li>Opens: raw per-open history — every pixel fire produces a row (never deduplicated) with timestamp, IP, user-agent, parsed client (Gmail web, Outlook desktop, Apple Mail iOS …), and a classification (`human_likely` / `machine_likely` / `unknown`) with reason codes.</li>
<li>Clicks: raw per-click history with timestamp, IP, user-agent, and — critically — <em>which specific link was clicked</em>: <code>link_type</code>, <code>link_label</code>, <code>link_text</code>, <code>link_index</code>, <code>template_section</code>, destination host + path.</li>
<li>Bounces / complaints: status update + auto-add to the suppression list.</li>
</ul>

<div class="callout">
<strong>What's new in 0.7.0</strong>
<ul style="margin:8px 0 0 0;">
<li><strong>Per-link tokenisation.</strong> Every clickable link in every email gets a random 32-byte token. The click endpoint identifies exactly which link was clicked rather than merely "a link was clicked."</li>
<li><strong>Sensitive-link redaction.</strong> Password-reset, invoice-access and licence-delivery URLs are flagged <code>isSensitive: true</code>; the raw destination never lands in the event log — only the URL hash + host.</li>
<li><strong>Event classification.</strong> Built-in classifier scores every open + click as human-likely / machine-likely / unknown with reason chips: <code>gmail-proxy</code>, <code>ampp</code> (Apple Mail Privacy Protection), <code>safelinks</code>, <code>outlook-proxy</code>, <code>proofpoint</code>, <code>mimecast</code>, <code>barracuda</code>, <code>datacentre</code>, <code>vpn</code>, <code>bot-ua</code>, <code>headless</code>, <code>scanner-ua</code>. Raw events still recorded — classification is advisory.</li>
<li><strong>IP enrichment.</strong> Async geo + ASN + VPN / proxy / datacentre flag population via <code>ip-api.com</code> (default, no key) or <code>ipinfo.io</code>. Never blocks event recording.</li>
<li><strong>Provider webhook receiver.</strong> Ingest delivered / bounced / deferred / dropped / complaint / open / click events from Postmark, SendGrid, Mailgun and Amazon SES (via SNS). Per-provider signature verification; idempotent within 24h.</li>
<li><strong>Order Activity History panel.</strong> Chronological timeline of every event with classification badges, filters, pagination, CSV export, PDF Evidence Report and elevated-permission full export.</li>
<li><strong>Graceful degradation.</strong> No runtime import from invoice / support-ticket / order plugins. Hosts without those simply never pass the id; entity foreign-id columns are plain nullable ints.</li>
</ul>
</div>
'''),
        ('install', 'Install', '''
<p>One package, one line of config, one migration. The fastest way is the bundled installer:</p>
<div class="doc-code">curl -sSL https://huloglobal.com/vendure-plugins/email-tracking/install.sh | bash</div>
<p>Or by hand:</p>
<div class="doc-code"><span class="c"># 1. Install</span>
yarn add @huloglobal/vendure-plugin-email-tracking

<span class="c"># 2. Register in vendure-config.ts</span>
import {{ <span class="k">EmailTrackingPlugin</span>, <span class="k">TrackingEmailSender</span> }} from <span class="s">'@huloglobal/vendure-plugin-email-tracking'</span>;

export const config: VendureConfig = {{
  plugins: [
    <span class="k">EmailTrackingPlugin</span>.init({{
      publicBaseUrl: <span class="s">'https://shop.example.com'</span>,
      licenceKey: process.env.<span class="k">HULO_LICENCE_KEY_EMAIL_TRACKING</span>,
    }}),
    <span class="c">// also pass TrackingEmailSender to the @vendure/email-plugin:</span>
    EmailPlugin.init({{
      emailSender: new <span class="k">TrackingEmailSender</span>(),
      <span class="c">// ... your existing email-plugin options ...</span>
    }}),
  ],
}};

<span class="c"># 3. Generate + run migration</span>
yarn migration:generate AddEmailTrackingTables
yarn migration:run</div>
<p>Restart Vendure. The <strong>Email Log</strong> tab appears in the admin nav immediately.</p>
'''),
        ('admin-ui', 'Admin UI tour', '''
<p>The Email Log page is mounted at <code>/admin/extensions/email-log</code> (or via the side nav).</p>
<div class="screenshot">''' + svg_panel('Email Log — list view', [
    '== Status totals',
    '::All 1247 | Sent 1198 | Failed 12 | Deferred 8 | Bounced 14 | Opens 540 | Clicks 87',
    '== Filters',
    '// Filter recipient…',
    '// Filter type…',
    '== Recent emails',
    '#1247  29 May  order-confirmation  alice@example.com  Sent  ●●●  12 opens, 3 clicks',
    '#1246  29 May  password-reset      bob@example.com    Sent  ●    1 open, 0 clicks',
    '#1245  28 May  invoice             carol@example.com  Sent  ●●●● 8 opens, 2 clicks',
], height=410) + '''
<div class="screenshot-caption">List view — colour-coded status pills, per-row open/click counts, click any row for the timeline.</div>
</div>
<p>Click <strong>Details</strong> on any row to expand the timeline. You'll see:</p>
<ul>
<li><strong>Header block</strong> — From / To / BCC / subject / context</li>
<li><strong>SMTP block</strong> — message-id, SMTP response, any error message</li>
<li><strong>Open block</strong> — first/last open times, first-open IP and UA</li>
<li><strong>Open history table</strong> — every open with time, IP, UA</li>
<li><strong>Click history table</strong> — every click with time, target URL, IP, UA</li>
</ul>
<div class="callout">Open and click history are capped at the most recent 50 entries per email. The lifetime totals (<code>openCount</code> / <code>clickCount</code>) keep counting beyond 50.</div>
'''),
        ('suppression', 'Suppression list', '''
<p>The plugin maintains an <code>email_suppression</code> table — recipients who should never be sent to. The table is populated automatically when the bounce webhook reports a hard bounce or a complaint, and you can add entries manually.</p>
<p>When <code>sendTracked()</code> is called for a suppressed recipient, the row is written to <code>email_log</code> with <code>status='suppressed'</code> and <code>errorMessage='Recipient is on the suppression list'</code> — but no SMTP call is made.</p>
<h3>Adding entries manually</h3>
<div class="doc-code">curl -X POST https://shop.example.com/email-track/suppression \\
  -H "Content-Type: application/json" \\
  -d '{{"recipient":"angry@example.com","reason":"manual","note":"Asked to be removed via support"}}'</div>
<h3>Lifting a suppression</h3>
<div class="doc-code">curl -X DELETE https://shop.example.com/email-track/suppression/angry@example.com</div>
<h3>Listing the table</h3>
<div class="doc-code">curl https://shop.example.com/email-track/suppression?take=200</div>
'''),
        ('webhook', 'Bounce webhook', '''
<p>Wire your postmaster integration (or scheduled DSN parser) to POST to <code>/email-track/bounce</code>:</p>
<div class="doc-code">{{
  "messageId": "&lt;abc@gmail.com&gt;",       <span class="c">// the smtpMessageId from the original send</span>
  "status": "bounced",                       <span class="c">// or 'complained'</span>
  "reason": "550 5.1.1 The email account ..."
}}</div>
<p>The matching <code>email_log</code> row is updated and the recipient is auto-added to the suppression list. The endpoint is unauthenticated — gate it behind a shared secret header if you expose it to the public internet.</p>
'''),
        ('analytics', 'Per-template analytics', '''
<p>For an aggregated view of how each email <em>type</em> performs, hit:</p>
<div class="doc-code">GET /email-track/log/stats/by-template?fromDays=30</div>
<p>Returns:</p>
<div class="doc-code">{{
  "days": 30,
  "types": [
    {{
      "type": "order-confirmation",
      "sent": 1247,
      "opened": 540,
      "clicked": 87,
      "bounced": 14,
      "failed": 12,
      "suppressed": 3,
      "openRate": 0.433,
      "clickRate": 0.070,
      "ctor": 0.161             <span class="c">// click-to-open</span>
    }},
    ...
  ]
}}</div>
'''),
        ('csv-export', 'CSV export', '''
<p>The list endpoint has a CSV mirror. Same filters, same shape:</p>
<div class="doc-code">GET /email-track/log/export.csv?status=sent&from=2026-05-01</div>
<p>Up to 50 000 rows per call.</p>
'''),
        ('endpoints', 'HTTP endpoints', '''
<table>
<thead><tr><th>Method</th><th>Path</th><th>Description</th></tr></thead>
<tbody>
<tr><td>GET</td><td><code>/email-track/open/:id.gif</code></td><td>Public pixel — logs an open then serves a 1×1 GIF</td></tr>
<tr><td>GET</td><td><code>/email-track/click/:id?u=&lt;url&gt;</code></td><td>Public click redirector — logs then 302s to the original URL</td></tr>
<tr><td>POST</td><td><code>/email-track/bounce</code></td><td>Bounce / complaint webhook</td></tr>
<tr><td>GET</td><td><code>/email-track/log</code></td><td>Admin: paginated log with filters</td></tr>
<tr><td>GET</td><td><code>/email-track/log/summary</code></td><td>Admin: status totals tile</td></tr>
<tr><td>GET</td><td><code>/email-track/log/:id</code></td><td>Admin: full detail (incl. opens + clicks arrays)</td></tr>
<tr><td>GET</td><td><code>/email-track/log/stats/by-template</code></td><td>Admin: per-template aggregates</td></tr>
<tr><td>GET</td><td><code>/email-track/log/export.csv</code></td><td>Admin: CSV export</td></tr>
<tr><td>GET</td><td><code>/email-track/suppression</code></td><td>Admin: list suppressions</td></tr>
<tr><td>POST</td><td><code>/email-track/suppression</code></td><td>Admin: add a suppression</td></tr>
<tr><td>DELETE</td><td><code>/email-track/suppression/:recipient</code></td><td>Admin: lift a suppression</td></tr>
</tbody>
</table>
'''),
        ('troubleshooting', 'Troubleshooting', '''
<h3>Opens aren't being recorded</h3>
<p>Many email clients prefetch images through a proxy (Gmail's <code>googleimageproxy</code>, Outlook's SafeLinks). The plugin recognises common proxies and flags those opens as <code>isBot: true</code> on the open entry — they still count in <code>openCount</code> but you can filter them out in the UI.</p>
<h3>Clicks redirect to a "blank target" 400</h3>
<p>The redirector refuses URLs that don't start with <code>http://</code> or <code>https://</code> — including <code>javascript:</code>, <code>data:</code>, <code>mailto:</code>. The link rewriter already excludes <code>mailto:</code> and unsubscribe-style links from rewriting, so you shouldn't see this in normal use.</p>
<h3>Suppression list isn't catching recent bounces</h3>
<p>Make sure your bounce / DSN webhook is hitting <code>/email-track/bounce</code> with a <code>messageId</code> that matches what your SMTP transport returned at send time. Gmail returns the messageId in the <code>250 2.0.0 OK 1234567890 abc@gmail.com</code> response — the plugin stores it as <code>smtpMessageId</code> on the EmailLog row.</p>
'''),
    ],
}


# ─────────────────────────────────────────────────────────────────────────
# Geo Block
# ─────────────────────────────────────────────────────────────────────────

GEO_BLOCK_MANUAL = {
    'slug': 'geo-block',
    'title_short': 'Geo Block',
    'sections': [
        ('overview', 'Overview', '''
<p><strong>Geo Block</strong> gives you per-channel control over who can reach your Vendure storefront. Pick from 37 region presets, add countries manually, soft-block markets you don't ship to (so they can still browse), allow specific IPs to bypass all rules, and audit every block decision.</p>
<p>Two storefront integration modes:</p>
<ul>
<li><strong>Site-config polling</strong> — Storefront calls <code>/geo-block/site-config</code> once on boot, caches the resolved rules, and decides client-side. Cheapest on the server.</li>
<li><strong>Per-request check</strong> — Storefront calls <code>/geo-block/check</code> on entry, gets a fresh decision per visitor (also logs to the audit table). Use when you want stats.</li>
</ul>
'''),
        ('install', 'Install', '''
<div class="doc-code">curl -sSL https://huloglobal.com/vendure-plugins/geo-block/install.sh | bash</div>
<p>Or by hand:</p>
<div class="doc-code"><span class="c"># 1. Install</span>
yarn add @huloglobal/vendure-plugin-geo-block

<span class="c"># 2. Register in vendure-config.ts</span>
import {{ <span class="k">GeoBlockPlugin</span> }} from <span class="s">'@huloglobal/vendure-plugin-geo-block'</span>;

export const config: VendureConfig = {{
  plugins: [
    <span class="k">GeoBlockPlugin</span>.init({{
      publicBaseUrl: <span class="s">'https://shop.example.com'</span>,
      licenceKey: process.env.<span class="k">HULO_LICENCE_KEY_GEO_BLOCK</span>,
      <span class="c">// Optional: a one-shot maintenance lockdown window</span>
      maintenanceWindow: {{
        startsAt: <span class="s">'2026-07-15T02:00:00Z'</span>,
        endsAt:   <span class="s">'2026-07-15T04:00:00Z'</span>,
        allowedIps: [<span class="s">'203.0.113.0/24'</span>],
      }},
    }}),
  ],
}};

<span class="c"># 3. Migration</span>
yarn migration:generate AddGeoBlockTables
yarn migration:run</div>
'''),
        ('admin-ui', 'Admin UI tour', '''
<p>The Site Access page is mounted at <code>/admin/extensions/geo-block</code>. Five tabs:</p>
<h3>Rules</h3>
<div class="screenshot">''' + svg_panel('Site access — Rules tab', [
    '== Channel: Elite [GEO-BLOCK ON]  [Full block]',
    '== Mode',
    '::Full block (selected) | Soft block (browse-only)',
    '== Strategy',
    '::Allow specific places (selected) | Worldwide except blocked',
    '== Allowed regions (3 picked)',
    '::UK only ✓ | British Isles ✓ | EU | EEA | EFTA | Schengen | Nordic | DACH',
    '::G7 | G20 | NATO | OECD | Commonwealth | English-speaking | …',
    '== UK subdivisions',
    '::England ✓ | Wales ✓ | Scotland | Northern Ireland',
], height=400) + '''
<div class="screenshot-caption">Rules tab — pick mode, strategy, regions, sub-regions. Live preview shows resolved country list at the bottom.</div>
</div>

<h3>Block page</h3>
<p>Customise the block page per channel: a free-text message, optional redirect URL (when set, blocked visitors are 302'd there instead), optional logo URL.</p>

<h3>IP allowlist</h3>
<p>Add specific IPs or IPv4 CIDR ranges (<code>203.0.113.0/24</code>) that bypass every rule. Use for your office, oncall engineers, payment processor probes, monitoring.</p>

<h3>Simulate</h3>
<div class="screenshot">''' + svg_panel('Site access — Simulate tab', [
    '== Test a hypothetical visitor',
    '// Country code: US',
    '// UK region (optional): —',
    '// IP address (optional): 8.8.8.8',
    '== [Run simulation]',
    '== Result',
    '🚫 Blocked  (country-not-allowed)',
], height=320) + '''
<div class="screenshot-caption">Simulate tab — try any country / IP combination without saving anything to production.</div>
</div>

<h3>Stats</h3>
<p>Last N days of block decisions: total blocks, soft blocks, unique blocked IPs, top blocked countries, daily series, breakdown by reason.</p>
'''),
        ('presets', 'Region presets', '''
<p>The plugin ships 37 hand-curated presets, grouped in the picker by kind:</p>
<table>
<thead><tr><th>Group</th><th>Presets</th></tr></thead>
<tbody>
<tr><td>Everywhere</td><td>WORLDWIDE</td></tr>
<tr><td>Geography</td><td>UK_ONLY, BRITISH_ISLES, UK_CROWN_DEPENDENCIES, EUROPE, NORDIC, BALTIC, BENELUX, IBERIA, BALKANS, NORTH_AMERICA, CENTRAL_AMERICA, CARIBBEAN, SOUTH_AMERICA, LATAM, OCEANIA, ANZ, MENA, APAC, EAST_ASIA, SOUTH_ASIA, AFRICA</td></tr>
<tr><td>Trade blocs</td><td>EU, EEA, EFTA, GCC, ASEAN</td></tr>
<tr><td>Political / economic</td><td>SCHENGEN, G7, G20, BRICS, OECD, NATO, FIVE_EYES</td></tr>
<tr><td>Language / cultural</td><td>DACH, ENGLISH_SPEAKING, COMMONWEALTH</td></tr>
</tbody>
</table>
<p>Fetch the live catalogue (with country counts + descriptions):</p>
<div class="doc-code">GET /geo-block/presets</div>
'''),
        ('storefront', 'Storefront integration', '''
<h3>Polling site-config (cheap)</h3>
<div class="doc-code">// On storefront boot, once per channel
const res = await fetch(<span class="s">'https://shop.example.com/geo-block/site-config'</span>, {{
  headers: {{ <span class="s">'vendure-token'</span>: <span class="k">CHANNEL_TOKEN</span> }},
}});
const cfg = await res.json();
<span class="c">// Cache cfg.geoBlock for ~60s, decide client-side based on the visitor's country.</span></div>

<h3>Per-request check (with logging)</h3>
<div class="doc-code">// In your storefront middleware
const res = await fetch(<span class="s">'https://shop.example.com/geo-block/check'</span>, {{
  headers: {{
    <span class="s">'vendure-token'</span>: <span class="k">CHANNEL_TOKEN</span>,
    <span class="s">'cf-ipcountry'</span>: req.headers[<span class="s">'cf-ipcountry'</span>],   <span class="c">// proxy already resolved</span>
  }},
}});
const verdict = await res.json();
if (!verdict.allowed) {{
  if (verdict.redirectUrl) return res.redirect(302, verdict.redirectUrl);
  return res.render(<span class="s">'blocked'</span>, {{ message: verdict.message, mode: verdict.mode }});
}}</div>

<div class="callout">In <strong>soft</strong> mode the storefront should render the full site but include a banner explaining you don't ship to the visitor's country, and hide the checkout button. The plugin returns <code>mode: 'soft'</code> on the verdict to make this decision easy.</div>
'''),
        ('endpoints', 'HTTP endpoints', '''
<table>
<thead><tr><th>Method</th><th>Path</th><th>Description</th></tr></thead>
<tbody>
<tr><td>GET</td><td><code>/geo-block/site-config</code></td><td>Public: resolved channel rules (cached client-side)</td></tr>
<tr><td>GET</td><td><code>/geo-block/check</code></td><td>Public: per-request decision (logs to audit table)</td></tr>
<tr><td>GET</td><td><code>/geo-block/presets</code></td><td>Public: 37-preset catalogue</td></tr>
<tr><td>GET</td><td><code>/geo-block/admin/channels</code></td><td>Admin: list channels + rules</td></tr>
<tr><td>POST</td><td><code>/geo-block/admin/save</code></td><td>Admin: save a channel's rules</td></tr>
<tr><td>GET</td><td><code>/geo-block/admin/stats</code></td><td>Admin: block totals + top countries</td></tr>
<tr><td>POST</td><td><code>/geo-block/admin/simulate</code></td><td>Admin: dry-run a visitor</td></tr>
<tr><td>POST</td><td><code>/geo-block/admin/gc</code></td><td>Admin: prune old audit rows</td></tr>
</tbody>
</table>
'''),
        ('troubleshooting', 'Troubleshooting', '''
<h3>Every visitor is blocked but my rules look right</h3>
<p>Check the <em>Rules</em> tab's "Resolved allow-list" preview at the bottom — it shows the exact list that would be applied on save. If the list says <strong>nothing is allowed</strong>, you've probably picked a preset and then blocked every country in it.</p>
<h3>Cloudflare IP appears as the visitor IP</h3>
<p>The plugin reads the upstream proxy headers in this order: <code>cf-connecting-ip</code> → <code>true-client-ip</code> → <code>x-real-ip</code> → <code>x-forwarded-for[0]</code> → <code>req.ip</code>. Make sure Cloudflare's <code>cf-connecting-ip</code> is reaching your Vendure server (it's a default Cloudflare header).</p>
<h3>Stats panel is empty</h3>
<p>Stats are populated by the per-request <code>/check</code> endpoint, not by <code>/site-config</code>. If your storefront only polls <code>site-config</code>, no audit rows are written. Either switch to <code>/check</code> or call <code>/check</code> as well in your storefront middleware.</p>
'''),
    ],
}


# ─────────────────────────────────────────────────────────────────────────
# Visitor Analytics
# ─────────────────────────────────────────────────────────────────────────

VISITOR_ANALYTICS_MANUAL = {
    'slug': 'visitor-analytics',
    'title_short': 'Visitor Analytics',
    'sections': [
        ('overview', 'Overview', '''
<p><strong>Visitor Analytics</strong> is a self-hosted, privacy-aware visitor journey tracker. Page views, time-on-page, exit pages, configurable funnel, conversion goals, UTM attribution, bot detection. All data lives in your own database; nothing is sent to a third party.</p>
<p>Survives login — a visitor's pre-signin events and post-signin events share the same <code>visitorId</code>, so funnel analysis works across the auth boundary.</p>
<p><strong>Since 0.8.0 the plugin also ships:</strong></p>
<ul>
<li><strong>Cart abandonment</strong> — detection, signed recovery links, Slack notification for high-value drops, admin dashboard.</li>
<li><strong>Product recommendations</strong> — <code>also-viewed</code>, <code>personal</code>, and <code>trending</code> endpoints driven by observed co-viewing behaviour.</li>
<li><strong>Site search analytics</strong> — top queries, zero-result queries (direct catalogue-gap intel), search-to-cart conversion.</li>
<li><strong>Journey drawer buffs</strong> — rage-click + dead-click hot-spot lists, per-session heuristic <code>intent</code> label.</li>
<li><strong>Drop-in storefront helper</strong> — one script tag from <code>/ees/hulo.js</code> and every event helper is on <code>window.hulo</code>.</li>
</ul>
'''),
        ('install', 'Install', '''
<div class="doc-code">curl -sSL https://huloglobal.com/vendure-plugins/visitor-analytics/install.sh | bash</div>
<p>Or by hand:</p>
<div class="doc-code"><span class="c"># 1. Install</span>
yarn add @huloglobal/vendure-plugin-visitor-analytics

<span class="c"># 2. Register in vendure-config.ts</span>
import {{ <span class="k">VisitorAnalyticsPlugin</span> }} from <span class="s">'@huloglobal/vendure-plugin-visitor-analytics'</span>;

export const config: VendureConfig = {{
  plugins: [
    <span class="k">VisitorAnalyticsPlugin</span>.init({{
      publicBaseUrl: <span class="s">'https://shop.example.com'</span>,
      licenceKey: process.env.<span class="k">HULO_LICENCE_KEY_VISITOR_ANALYTICS</span>,
      <span class="c">// Privacy options — these are the defaults</span>
      honorDoNotTrack: <span class="k">true</span>,
      anonymizeIp: <span class="k">true</span>,
      requireConsent: <span class="k">false</span>,
      dropBotEvents: <span class="k">false</span>,
    }}),
  ],
}};

<span class="c"># 3. Migration</span>
yarn migration:generate AddVisitorAnalyticsTables
yarn migration:run</div>
'''),
        ('storefront', 'Storefront integration', '''
<h3>Option 1: drop-in helper (recommended)</h3>
<p>The plugin serves a typed, batching event helper at <code>/ees/hulo.js</code>. One script tag, every event is on <code>window.hulo</code>:</p>
<div class="doc-code">&lt;script src="https://shop.example.com/ees/hulo.js" defer&gt;&lt;/script&gt;</div>
<p>The helper handles:</p>
<ul>
<li>Batching events (1.5s coalescing window) and flushing via <code>sendBeacon</code> on <code>pagehide</code> / <code>beforeunload</code>.</li>
<li>Emitting a <code>pageview</code> on load automatically.</li>
<li>Auto rage-click detection (≥3 pointerdowns within 500ms and 20px radius fires <code>rage_click</code>).</li>
<li>Auto dead-click detection (click on non-interactive element with no URL / significant scroll change within 400ms fires <code>dead_click</code>).</li>
</ul>
<h3>Option 2: typed helpers in your storefront</h3>
<p>Recommended for SSR frameworks (Qwik, Next, Remix, SolidStart) so the tracker code ships in your own bundle. Copy this into <code>utils/visitor-tracking.ts</code>:</p>
<div class="doc-code"><span class="k">export function</span> recordProductView(productId: number, variantId?: number) {{
  send([{{ type: <span class="s">'event'</span>, url: location.href, meta: {{
    eventType: <span class="s">'product_view'</span>, productId, productVariantId: variantId,
  }} }}]);
}}

<span class="k">export function</span> recordCartSnapshot(cart: {{ currency, totalMinor, items, email? }}) {{
  send([{{ type: <span class="s">'event'</span>, url: location.href, meta: {{
    eventType: <span class="s">'cart_snapshot'</span>, ...cart,
  }} }}]);
}}

<span class="k">export function</span> recordSearch(query: string, resultsCount: number) {{
  send([{{ type: <span class="s">'event'</span>, url: location.href, meta: {{
    eventType: <span class="s">'search'</span>, query, resultsCount,
  }} }}]);
}}

<span class="k">export function</span> recordCheckoutCompleted(orderCode: string, totalMinor: number) {{
  send([{{ type: <span class="s">'event'</span>, url: location.href, meta: {{
    eventType: <span class="s">'checkout_completed'</span>, orderCode, totalMinor,
  }} }}], <span class="c">/* useBeacon */</span> <span class="k">true</span>);
}}</div>
<p>See the <a href="https://github.com/huloglobal/vendure-plugin-visitor-analytics">plugin README</a> for the full implementation including the send() batcher and the auto rage/dead-click detectors.</p>
<h3>Where to call the helpers</h3>
<table>
<thead><tr><th>Helper</th><th>Where to call</th><th>Feeds</th></tr></thead>
<tbody>
<tr><td><code>productView(id)</code></td><td>Product detail page mount + on variant change</td><td>co-view aggregation, trending, personal recs</td></tr>
<tr><td><code>cartSnapshot(cart)</code></td><td>Every cart change (add / remove / qty)</td><td>abandoned-cart detection</td></tr>
<tr><td><code>search(q, n)</code></td><td>Once search results have rendered</td><td>top / no-result / conversion</td></tr>
<tr><td><code>checkoutCompleted(code, total)</code></td><td>Order confirmation page</td><td>closes any open abandoned-cart row</td></tr>
</tbody>
</table>
'''),
        ('cart-recovery', 'Cart-restore route', '''
<p>The abandoned-cart admin dashboard mints a URL of the form <code>https://shop.example.com/cart/restore?t=&lt;token&gt;</code>. Add a route on your storefront that consumes it:</p>
<ol>
<li>Read <code>?t=</code> from the URL.</li>
<li>Call <code>GET /ees/recover-cart?t=&lt;token&gt;</code> — returns <code>{{ ok: true, items: [...] }}</code> or <code>{{ error }}</code>.</li>
<li>If the visitor already has items in their live cart, don't overwrite — show a friendly "you already have items in your cart" message.</li>
<li>Otherwise, re-add each <code>{{ variantId, qty }}</code> via your Vendure order API (typically <code>addItemToOrder(productVariantId, quantity)</code>).</li>
<li>Navigate to <code>/cart</code>.</li>
</ol>
<p>The token is signed, time-bounded (default 72h), and non-reusable. If it's expired or already consumed, the endpoint returns <code>{{ error: 'expired-or-invalid' }}</code>.</p>
'''),
        ('cart-abandonment', 'Cart abandonment', '''
<p>Detects sessions that put items in the cart but never checked out. Turns them into <code>AbandonedCart</code> rows you can send a recovery email against.</p>
<h3>Enable it</h3>
<div class="doc-code"><span class="k">VisitorAnalyticsPlugin</span>.init({{
  <span class="c">// ...</span>
  abandonment: {{
    windowMinutes: 30,           <span class="c">// how long since last cart_snapshot before we mark as abandoned</span>
    slackMinValueMinor: 5000,    <span class="c">// £50 / $50 threshold for a Slack ping</span>
    slackWebhookUrl: process.env.<span class="k">HULO_ABANDONMENT_SLACK_URL</span>,
    recoveryLinkSecret: process.env.<span class="k">HULO_ABANDONMENT_SECRET</span>,
    recoveryLinkTtlHours: 72,
    storefrontBaseUrl: <span class="s">'https://shop.example.com'</span>,
  }},
}})</div>
<h3>How the scanner works</h3>
<p>A worker-only interval (5 minutes) walks recent <code>cart_snapshot</code> events, grouped by session. For each session:</p>
<ul>
<li>If <code>checkout_completed</code> landed later — no-op (or promote an existing abandoned row to <code>converted</code>).</li>
<li>If the last <code>cart_snapshot</code> is older than <code>windowMinutes</code> and no fresh snapshot — open an <code>abandoned_cart</code> row (unique on <code>sessionId</code> — can't double-open).</li>
<li>If the value clears <code>slackMinValueMinor</code>, POST a one-off notification to Slack (idempotent — <code>notificationSent</code> flag).</li>
</ul>
<h3>Admin dashboard</h3>
<p>Under <strong>Analytics → Abandoned carts</strong>. Filters by status / min value / email / window; KPIs (open, recovered, converted, lost value); actions per row: mint recovery link (copies URL to clipboard), mark recovered / dismissed manually. CSV export.</p>
<h3>Recovery link lifecycle</h3>
<ol>
<li>Admin clicks "Recovery link" on an abandoned row.</li>
<li>Backend mints a random opaque token and returns <code>{{ url: '&lt;storefront&gt;/cart/restore?t=...' }}</code>.</li>
<li>Admin drops the URL into a recovery email.</li>
<li>Recipient clicks — the storefront's <code>/cart/restore</code> route exchanges the token via <code>/ees/recover-cart?t=...</code> and re-adds the items.</li>
<li>Once the visitor completes the checkout, the scanner promotes the row to <code>converted</code>.</li>
</ol>
'''),
        ('recommendations', 'Product recommendations', '''
<p>Recommendations derived from observed co-viewing behaviour. The scanner walks recent <code>product_view</code> events per session, extracts every ordered pair, and increments a counter per <code>(productIdA, productIdB, channelId)</code> triple.</p>
<h3>Endpoints</h3>
<table>
<thead><tr><th>Endpoint</th><th>Use</th></tr></thead>
<tbody>
<tr><td><code>GET /ees/recommendations/also-viewed?productId=42&amp;limit=10</code></td><td>"Customers who viewed X also viewed…" rail on the product page.</td></tr>
<tr><td><code>GET /ees/recommendations/personal?visitorId=abc&amp;limit=10</code></td><td>Personalised recs based on the visitor's last 10 product views over 30 days. Excludes seeds so the same product never appears on the rail.</td></tr>
<tr><td><code>GET /ees/recommendations/trending?hours=24&amp;limit=10</code></td><td>Most-viewed products in the window. Reflects real intent (not search-console clicks).</td></tr>
<tr><td><code>GET /ees/recommendations/aggregate-now</code></td><td>Force a fresh sweep (SuperAdmin only). Useful after a big data backfill.</td></tr>
</tbody>
</table>
<h3>Storefront wiring</h3>
<div class="doc-code"><span class="c">// on the product detail page</span>
hulo.productView(product.id, selectedVariant.id);

<span class="c">// then fetch the recs rail</span>
<span class="k">const</span> res = <span class="k">await</span> fetch(<span class="s">`/ees/recommendations/also-viewed?productId=${{product.id}}&amp;limit=8`</span>);
<span class="k">const</span> {{ items }} = <span class="k">await</span> res.json();
<span class="c">// items: [{{ productId, score }}]</span>
<span class="c">// Hydrate names / images from your usual Vendure product fetch.</span></div>
'''),
        ('search-analytics', 'Site search analytics', '''
<p>Reads back over the <code>visitor_event</code> table where the storefront has fired <code>search</code> custom events. Zero new schema.</p>
<h3>Storefront wiring</h3>
<div class="doc-code"><span class="c">// once results have rendered</span>
hulo.search(query, results.totalItems);</div>
<h3>Endpoints</h3>
<table>
<thead><tr><th>Endpoint</th><th>Use</th></tr></thead>
<tbody>
<tr><td><code>GET /ees/search-analytics/top?days=7</code></td><td>Top queries by volume with average results count.</td></tr>
<tr><td><code>GET /ees/search-analytics/no-results?days=7</code></td><td>Queries that returned zero hits. Direct catalogue-gap intel.</td></tr>
<tr><td><code>GET /ees/search-analytics/conversion?days=7</code></td><td>Of sessions that searched, what fraction went on to <code>add_to_cart</code>.</td></tr>
</tbody>
</table>
'''),
        ('journey-buffs', 'Journey drawer buffs', '''
<h3>Rage-click + dead-click hot spots</h3>
<p>The auto-detectors bundled with <code>hulo.js</code> fire <code>rage_click</code> / <code>dead_click</code> events with the offending element's CSS selector. Two admin endpoints aggregate them per URL:</p>
<ul>
<li><code>GET /ees/journey/rage-clicks?days=7</code> — pages where visitors are frustrated.</li>
<li><code>GET /ees/journey/dead-clicks?days=7</code> — elements that <em>look</em> clickable but aren't.</li>
</ul>
<p>Both are conservative heuristics — the signal is direction-of-frustration, not a metric to optimise against.</p>
<h3>Per-session intent labels</h3>
<p><code>GET /ees/journey/session-summary?visitorId=abc</code> returns one row per session with a heuristic <code>intent</code> label:</p>
<table>
<thead><tr><th>Label</th><th>Meaning</th></tr></thead>
<tbody>
<tr><td><code>purchase</code></td><td>Fired <code>checkout_completed</code>. Best outcome.</td></tr>
<tr><td><code>abandon</code></td><td>Added to cart or fired a cart snapshot but did not check out.</td></tr>
<tr><td><code>frustrate</code></td><td>Fired <code>rage_click</code>. Time to look at the URL.</td></tr>
<tr><td><code>consider</code></td><td>Viewed ≥5 pages but didn't add to cart.</td></tr>
<tr><td><code>browse</code></td><td>Genuine browsing that didn't hit any of the above.</td></tr>
<tr><td><code>bounce</code></td><td>Single pageview, gone in &lt;15s.</td></tr>
</tbody>
</table>
'''),
        ('goals', 'Conversion goals', '''
<p>A conversion goal is a URL glob that, when matched by a pageview, counts that visitor as having completed the goal. Patterns support:</p>
<ul>
<li><code>*</code> — match zero or more chars within a path segment</li>
<li><code>**</code> — match zero or more segments (including <code>/</code>)</li>
<li>everything else is a literal substring (case-insensitive)</li>
</ul>
<h3>Examples</h3>
<table>
<thead><tr><th>Pattern</th><th>Matches</th></tr></thead>
<tbody>
<tr><td><code>/checkout/thank-you/*</code></td><td>Order confirmation page</td></tr>
<tr><td><code>/signup</code></td><td>Exact: signup landing</td></tr>
<tr><td><code>**/wishlist</code></td><td>Any wishlist page on any subdomain</td></tr>
<tr><td><code>/contact?*</code></td><td>Contact form with any query</td></tr>
</tbody>
</table>
<h3>Creating a goal</h3>
<div class="doc-code">curl -X POST https://shop.example.com/ees/goals \\
  -H "Content-Type: application/json" \\
  -d '{{
    "channelId": 1,
    "name": "Checkout completed",
    "urlPattern": "/checkout/thank-you/*",
    "valueMinor": 5000,
    "enabled": true
  }}'</div>
<p>Once created, every matching pageview is tagged with the <code>goalId</code> on its <code>visitor_event</code> row. The admin stats endpoint at <code>/ees/goals/stats?days=30</code> aggregates completions per goal.</p>
'''),
        ('privacy', 'Privacy controls', '''
<p>The plugin defaults to privacy-respecting behaviour. Toggle as needed:</p>
<table>
<thead><tr><th>Option</th><th>Default</th><th>Effect</th></tr></thead>
<tbody>
<tr><td><code>honorDoNotTrack</code></td><td><code>true</code></td><td>If the visitor's request has <code>DNT: 1</code> or <code>Sec-GPC: 1</code>, the endpoint returns 200 with <code>skipped: 'dnt'</code> and writes nothing.</td></tr>
<tr><td><code>anonymizeIp</code></td><td><code>true</code></td><td>The stored <code>ip</code> column drops the last octet of IPv4 (or last 80 bits of IPv6). The <code>ipHash</code> column still uses the raw IP so "unique visitor" counts remain accurate.</td></tr>
<tr><td><code>requireConsent</code></td><td><code>false</code></td><td>If on, the endpoint returns <code>skipped: 'no-consent'</code> unless the body sets <code>consent: true</code> or the request has cookie <code>ees_consent=1</code>.</td></tr>
<tr><td><code>dropBotEvents</code></td><td><code>false</code></td><td>If on, known bot UAs are dropped entirely. Default off so bot share is visible on the dashboard.</td></tr>
</tbody>
</table>
'''),
        ('bot-detection', 'Bot detection', '''
<p>Every event is checked against an embedded list of ~45 bot UA patterns: Googlebot, Bingbot, Facebook scrapers, monitoring probes (UptimeRobot, Datadog, Pingdom), HTTP libraries (curl, wget, axios, requests, node-fetch), headless browsers (HeadlessChrome, Puppeteer, Playwright).</p>
<p>By default these events are stored with <code>isBot: true</code> so you can see bot share but they're excluded from "real human" counts in the admin dashboards. Flip <code>dropBotEvents: true</code> to skip ingest entirely.</p>
'''),
        ('admin-ui', 'Admin UI tour', '''
<div class="screenshot">''' + svg_panel('Visitor Journey — Summary', [
    '== Last 30 days',
    '::42,135 visitors | 89,210 sessions | 312,447 pageviews | avg 2:18 on page',
    '== Daily series',
    '▁▂▄▅▇▆▇█▇▆▅▄▃▄▅▆▇▆▅▄▃▂▃▄▅▆▇█▇▆',
    '== Top sources',
    '#1  google.com         18,402 visits',
    '#2  direct             12,089 visits',
    '#3  twitter.com         3,541 visits',
    '#4  facebook.com        2,170 visits',
], height=400) + '''
<div class="screenshot-caption">Summary — top-line counters, daily series, top sources, top countries.</div>
</div>
<p>Other admin views:</p>
<ul>
<li><strong>Funnel</strong> — drop-off per configured step</li>
<li><strong>Exit pages</strong> — where visitors leave</li>
<li><strong>Top events</strong> — custom event distribution</li>
<li><strong>Top pages</strong> — most-visited URLs</li>
<li><strong>Live</strong> — SSE-streamed real-time count</li>
<li><strong>Journey</strong> — full per-visitor timeline (drill from any of the views above)</li>
</ul>
'''),
        ('endpoints', 'HTTP endpoints', '''
<h3>Public (browser-safe, CORS-permissive)</h3>
<table>
<thead><tr><th>Method</th><th>Path</th><th>Description</th></tr></thead>
<tbody>
<tr><td>POST</td><td><code>/ees/track</code></td><td>Ingest a batch of visitor events</td></tr>
<tr><td>GET</td><td><code>/ees/hulo.js</code></td><td>Typed storefront helper JS (0.8.1)</td></tr>
<tr><td>GET</td><td><code>/ees/recover-cart?t=&lt;token&gt;</code></td><td>Resolve a recovery-link token → cart items</td></tr>
<tr><td>GET</td><td><code>/ees/recommendations/also-viewed?productId=…</code></td><td>Co-view recommendations for one product</td></tr>
<tr><td>GET</td><td><code>/ees/recommendations/personal?visitorId=…</code></td><td>Personalised recs from visitor history</td></tr>
<tr><td>GET</td><td><code>/ees/recommendations/trending?hours=…</code></td><td>Most-viewed products in window</td></tr>
</tbody>
</table>
<h3>Admin (requires a Vendure admin session; <code>ReadCustomer</code> unless noted)</h3>
<table>
<thead><tr><th>Method</th><th>Path</th><th>Description</th></tr></thead>
<tbody>
<tr><td>GET</td><td><code>/ees/visitors/summary</code></td><td>Top-line + daily series</td></tr>
<tr><td>GET</td><td><code>/ees/visitors/sources</code></td><td>Top sources by visits / sessions</td></tr>
<tr><td>GET</td><td><code>/ees/visitors/top-pages</code></td><td>Most-visited URLs</td></tr>
<tr><td>GET</td><td><code>/ees/visitors/funnel</code></td><td>Configurable funnel with drop-offs</td></tr>
<tr><td>GET</td><td><code>/ees/visitors/exit-pages</code></td><td>Top exit pages</td></tr>
<tr><td>GET</td><td><code>/ees/visitors/live</code></td><td>SSE live-now stream</td></tr>
<tr><td>GET</td><td><code>/ees/visitors/journey/:visitorId</code></td><td>Per-visitor timeline</td></tr>
<tr><td>GET</td><td><code>/ees/visitors/export.csv</code></td><td>CSV export (max 90 days)</td></tr>
<tr><td>POST</td><td><code>/ees/goals</code></td><td>Create a conversion goal</td></tr>
<tr><td>GET</td><td><code>/ees/goals/stats</code></td><td>Per-goal completion stats</td></tr>
<tr><td>GET</td><td><code>/ees/abandoned-carts</code></td><td><strong>0.8.0</strong> — paginated list with filters</td></tr>
<tr><td>GET</td><td><code>/ees/abandoned-carts/summary</code></td><td><strong>0.8.0</strong> — KPIs + recovery rate</td></tr>
<tr><td>GET</td><td><code>/ees/abandoned-carts/:id</code></td><td><strong>0.8.0</strong> — detail incl. parsed items</td></tr>
<tr><td>POST</td><td><code>/ees/abandoned-carts/:id/recovery-link</code></td><td><strong>0.8.0</strong> — mint signed recovery URL (<code>UpdateCustomer</code>)</td></tr>
<tr><td>POST</td><td><code>/ees/abandoned-carts/:id/status</code></td><td><strong>0.8.0</strong> — mark recovered / dismissed (<code>UpdateCustomer</code>)</td></tr>
<tr><td>GET</td><td><code>/ees/abandoned-carts/export.csv</code></td><td><strong>0.8.0</strong> — CSV export</td></tr>
<tr><td>GET</td><td><code>/ees/recommendations/aggregate-now</code></td><td><strong>0.8.0</strong> — force co-view sweep (<code>SuperAdmin</code>)</td></tr>
<tr><td>GET</td><td><code>/ees/search-analytics/top</code></td><td><strong>0.8.0</strong> — top search queries</td></tr>
<tr><td>GET</td><td><code>/ees/search-analytics/no-results</code></td><td><strong>0.8.0</strong> — zero-result queries</td></tr>
<tr><td>GET</td><td><code>/ees/search-analytics/conversion</code></td><td><strong>0.8.0</strong> — search→cart rate</td></tr>
<tr><td>GET</td><td><code>/ees/journey/rage-clicks</code></td><td><strong>0.8.0</strong> — rage-click hot spots</td></tr>
<tr><td>GET</td><td><code>/ees/journey/dead-clicks</code></td><td><strong>0.8.0</strong> — dead-click hot spots</td></tr>
<tr><td>GET</td><td><code>/ees/journey/session-summary?visitorId=…</code></td><td><strong>0.8.0</strong> — per-session intent labels</td></tr>
</tbody>
</table>
'''),
        ('troubleshooting', 'Troubleshooting', '''
<h3>Visitors aren't being counted</h3>
<p>Check the response of <code>POST /ees/track</code> — if <code>skipped: 'dnt'</code> the visitor is sending a Do-Not-Track header (and your <code>honorDoNotTrack</code> option is on, which it is by default). Set the option to <code>false</code> to override.</p>
<h3>Goals don't seem to fire</h3>
<p>The matcher only runs for <code>type: 'pageview'</code> events — custom events (<code>type: 'event'</code>) don't trigger goals. Also, the goal cache refreshes every 60s; new goals start counting after that.</p>
<h3>MaxMind geo isn't populating</h3>
<p>The plugin uses the <code>geolite2-redist</code> package to download the GeoLite2 City DB on first use. If the download fails (network, sandboxed env), geo fields stay null. You can force a re-download with <code>npx geolite2-redist refresh</code> from your Vendure project root.</p>
'''),
    ],
}

FRAUD_PREVENTION_MANUAL = {
    'slug': 'fraud-prevention',
    'title_short': 'Fraud Prevention',
    'sections': [
        ('overview', 'Overview', '''
<p><strong>Fraud Prevention</strong> risk-scores every order server-side the moment it is placed. There is no storefront integration to add and nothing a fraudster can bypass by skipping your checkout JavaScript — the assessment runs inside Vendure on <code>OrderPlacedEvent</code>.</p>
<p>Weighted signals roll up to a 0&ndash;100 score:</p>
<ul>
<li><strong>Velocity</strong> — orders per IP per hour/day, orders per email identity per day, daily spend per identity. Emails are canonicalised first: <code>x+1@gmail.com</code>, <code>x+2@gmail.com</code> and <code>x.y@gmail.com</code> count as one identity.</li>
<li><strong>Lists</strong> — your manual allow/block entries plus daily-synced threat feeds (FireHOL Level&nbsp;1, Spamhaus DROP, Tor exit nodes, ~3,500 disposable-email domains). CIDR ranges are matched properly.</li>
<li><strong>Payment behaviour</strong> — failed/declined payment attempts from the same IP within the hour.</li>
<li><strong>Order shape</strong> — value ceilings, first-order-high-value, high-risk countries (your list).</li>
</ul>
<p>Per-channel thresholds decide the outcome: below the review threshold the order flows normally; at or above it the order is <em>held for review</em>; at the block threshold the customer is additionally told the order is being verified. Every assessment is written to a filterable audit log.</p>
'''),
        ('install', 'Install', '''
<p>One package, one line of config. Tables are created automatically on boot.</p>
<div class="doc-code"><span class="c"># 1. Install</span>
yarn add @huloglobal/vendure-plugin-fraud-prevention

<span class="c"># 2. Register in vendure-config.ts</span>
import { <span class="k">FraudPreventionPlugin</span> } from <span class="s">'@huloglobal/vendure-plugin-fraud-prevention'</span>;

export const config: VendureConfig = {
  plugins: [
    <span class="k">FraudPreventionPlugin</span>.init({
      publicBaseUrl: <span class="s">'https://shop.example.com'</span>,
      licenceKey: process.env.<span class="k">HULO_LICENCE_KEY_FRAUD_PREVENTION</span>,
    }),
  ],
};

<span class="c"># 3. Admin UI — add to your compileUiExtensions extensions array:</span>
FraudPreventionPlugin.uiExtensions</div>
<p>Orders need an IP for the IP-based signals — store it in the <code>Order.customFields.ip</code> custom field at checkout.</p>
'''),
        ('modes', 'Modes & thresholds', '''
<p>Each channel runs in one of three modes:</p>
<ul>
<li><strong>Off</strong> — no scoring, no logging.</li>
<li><strong>Monitor</strong> — every order scored and logged; risky orders flagged but never held. The default, and the recommended starting point: watch the Activity tab for a week, then tune.</li>
<li><strong>Enforce</strong> — orders scoring &ge; the review threshold open a case in the Review queue and licence keys / downloads wait for approval. Orders &ge; the block threshold also email the customer that the order is under verification.</li>
</ul>
<p>Defaults: review at 40, block at 70. The status sentence at the top of the admin page always describes, in plain English, exactly what the current configuration will do.</p>
'''),
        ('review-queue', 'Review queue', '''
<p>Held orders land in the Review queue with their score, the exact signals that fired (with per-signal point contributions), customer identity and age.</p>
<ul>
<li><strong>Approve</strong> — releases fulfilment; the customer gets your approved-order email.</li>
<li><strong>Reject</strong> — cancels the order and notifies the customer with your rejection email (refund timeline + a human-appeal path in the default copy). Add notes; everything is audited.</li>
</ul>
<p><strong>Customer messages are templates, per channel</strong>: held / approved / rejected each have an editable subject + body with <code>{{orderCode}}</code>, <code>{{firstName}}</code>, <code>{{supportEmail}}</code> and <code>{{reviewHours}}</code> variables, live preview and reset-to-default (Settings tab). A per-channel policy decides when held customers are told: never, block-level only (default), or always.</p>
<p><strong>Ops alerts</strong> fan out to every channel you configure — Slack, Discord, Microsoft Teams, Telegram, and a generic JSON webhook signed with HMAC-SHA256 (<code>X-Hulo-Signature</code>) for custom integrations. Held, approved, rejected and auto-released cases all ping.</p>
<p><strong>Fulfilment hold integration:</strong> if your fulfilment is custom, gate it with one call:</p>
<div class="doc-code">import { <span class="k">FraudPreventionService</span> } from <span class="s">'@huloglobal/vendure-plugin-fraud-prevention'</span>;

const held = new Set(await this.fraudService.<span class="k">pendingOrderIds</span>());
if (held.has(orderId)) continue; <span class="c">// wait for a human</span></div>
'''),
        ('lists', 'Lists & threat feeds', '''
<p>Two manual lists ride on top of the feeds:</p>
<ul>
<li><strong>Allowlist</strong> — emails, email domains or IPs that bypass every check. Add your test accounts and key B2B customers here.</li>
<li><strong>Blocklist</strong> — manual bans: emails, domains, IPs, or CIDR ranges.</li>
</ul>

<h3>Built-in threat feeds</h3>
<p>These sync automatically every night at 03:00 (licensed installs) and can also be synced on demand from the Lists tab. All are free, reputable public sources:</p>
<table>
<thead><tr><th>Feed</th><th>What it covers</th><th>Type</th><th>Source</th></tr></thead>
<tbody>
<tr><td><strong>FireHOL Level&nbsp;1</strong></td><td>High-confidence malicious IPs &amp; ranges (attacks, spam, C2), aggregated from dozens of sources — the safest IP feed to enforce.</td><td>IP / CIDR</td><td><code>iplists.firehol.org</code></td></tr>
<tr><td><strong>Spamhaus DROP</strong></td><td>Hijacked and leased netblocks used by professional spammers and cybercriminals.</td><td>CIDR ranges</td><td><code>spamhaus.org/drop</code></td></tr>
<tr><td><strong>Tor exit nodes</strong></td><td>Live Tor exit relays — legitimate for privacy, but a common origin for card testing.</td><td>IP</td><td><code>check.torproject.org</code></td></tr>
<tr><td><strong>Disposable email domains</strong></td><td>~3,500 throwaway / temporary-mailbox providers (mailinator, guerrillamail, …).</td><td>Email domain</td><td>community list</td></tr>
</tbody>
</table>

<h3>Other feeds you can layer in</h3>
<p><strong>Add your own feeds.</strong> In the Lists tab, paste any public line-based blocklist URL (one entry per line, <code>#</code> comments ignored), pick its type (IP, CIDR range, email or email-domain), and it syncs nightly alongside the built-ins and is matched exactly the same way — CIDR ranges included. Some popular options:</p>
<table>
<thead><tr><th>Feed</th><th>What it covers</th><th>Source</th></tr></thead>
<tbody>
<tr><td><strong>FireHOL Level&nbsp;2–4</strong></td><td>Progressively broader IP reputation — higher coverage, higher false-positive risk. Try in monitor mode first.</td><td><code>iplists.firehol.org</code></td></tr>
<tr><td><strong>IPsum</strong></td><td>Daily aggregate of IPs seen attacking honeypots, ranked by how many lists flag each one.</td><td><code>github.com/stamparm/ipsum</code></td></tr>
<tr><td><strong>blocklist.de</strong></td><td>IPs reported for SSH / mail / web attacks in the last 48 hours.</td><td><code>lists.blocklist.de</code></td></tr>
<tr><td><strong>Emerging Threats — compromised IPs</strong></td><td>Known-compromised hosts, updated frequently.</td><td><code>rules.emergingthreats.net</code></td></tr>
<tr><td><strong>StopForumSpam</strong></td><td>Emails &amp; IPs tied to spam sign-up abuse — useful against fake-account fraud.</td><td><code>stopforumspam.com</code></td></tr>
<tr><td><strong>AbuseIPDB</strong></td><td>Community-reported abusive IPs with a confidence score (free API key).</td><td><code>abuseipdb.com</code></td></tr>
</tbody>
</table>
<div class="callout"><strong>Roll out safely:</strong> start any new feed in <strong>monitor</strong> mode and watch the Activity tab for a few days before enforcing. Broad IP feeds occasionally catch shared carrier-grade NAT or corporate-proxy addresses that real customers sit behind, so it pays to see the hits before they can hold an order.</div>
'''),
        ('simulate', 'Simulator', '''
<p>The Simulate tab runs the full assessment for a hypothetical order — email, IP, value, country, first-time-customer flag — against <em>live</em> data (velocity counts your real recent orders) and shows the signal-by-signal score breakdown. Nothing is logged and nothing is held. Use it to sanity-check threshold changes before switching a channel to enforce.</p>
'''),
        ('licensing', 'Licensing', '''
<p>Without a licence key the plugin runs in the <strong>free tier</strong>: monitor mode, manual lists and the simulator — full scoring visibility, no enforcement. A licence enables enforce mode (review queue + fulfilment holds), threat-feed sync and email alerts.</p>
<p>Licences are JWTs bought from the <a href="/vendure-plugins/fraud-prevention/">plugin page</a> — monthly, annual (two months free), or lifetime. Easiest: click <em>Start 14-day free trial</em> (or <em>Buy lifetime</em>) on the plugin's admin banner — checkout opens in a new tab and the key installs itself within a minute (renewals too). Already have a key? Paste it into the same banner (<em>Activate</em>) — no redeploy. For config-as-code, set it as <code>HULO_LICENCE_KEY_FRAUD_PREVENTION</code> and pass it to <code>init()</code>; an env key takes precedence over an admin-stored one.</p>
'''),
    ],
}
REVIEW_REQUESTS_MANUAL = {
    'slug': 'review-requests',
    'title_short': 'Review Requests',
    'sections': [
        ('overview', 'Overview', '''
<p><strong>Review Requests</strong> automatically invites customers to review you after they buy, timed off the order date. An hourly worker finds orders that reached a milestone (Delivered / Payment settled / Shipped) a set number of days ago and emails a branded, Trustpilot-style invitation.</p>
<p>It uses the <strong>free</strong> Trustpilot review page for the link — no paid Automatic Feedback Service — and can optionally read your live TrustScore from the free Trustpilot API to show as social proof. The whole thing is per-channel, deduped, and respectful: exclusions, a per-customer cooldown, a minimum order value, and one-click unsubscribe.</p>
'''),
        ('install', 'Install', '''
<p>One package, one config block. Tables are created on boot; emails go via your SMTP.</p>
<div class="doc-code"><span class="c"># 1. Install</span>
yarn add @huloglobal/vendure-plugin-review-requests

<span class="c"># 2. Register in vendure-config.ts</span>
import { <span class="k">ReviewRequestPlugin</span> } from <span class="s">'@huloglobal/vendure-plugin-review-requests'</span>;

export const config: VendureConfig = {
  plugins: [
    <span class="k">ReviewRequestPlugin</span>.init({
      publicBaseUrl: <span class="s">'https://shop.example.com'</span>,   <span class="c">// for unsubscribe links</span>
      licenceKey: process.env.<span class="k">HULO_LICENCE_KEY_REVIEW_REQUESTS</span>,
    }),
  ],
};

<span class="c"># 3. Admin UI — add to your compileUiExtensions extensions array:</span>
ReviewRequestPlugin.uiExtensions</div>
<p>Then open <strong>Review requests</strong> in the admin, set your Trustpilot domain, timing and email, hit <em>Send test</em>, and switch the channel on.</p>
'''),
        ('trustpilot', 'Free Trustpilot setup', '''
<p>Everything here is free — no paid Trustpilot plan.</p>
<ul>
<li><strong>Review link</strong> — nothing to set up. The button links to <code>https://www.trustpilot.com/evaluate/&lt;your-domain&gt;</code>, which opens a Service Review form. These land as organic reviews.</li>
<li><strong>Live rating (optional)</strong> — register a free developer app at <a href="https://developers.trustpilot.com/" target="_blank">developers.trustpilot.com</a> for an <strong>API key</strong>, paste it into Settings and click <em>Check rating</em>. The plugin finds your business-unit id from the domain and shows your TrustScore + review count in the email.</li>
<li><strong>Google reviews live rating</strong> — pick Google in the platform selector, add a Google Maps API key (Places API enabled) and your Place ID, then Connect. The email shows your live Google star rating the same way, and the review button drops customers straight on Google's "write a review" box.</li>
<li><strong>Point elsewhere</strong> — the review-link template is configurable, so you can send customers to Google reviews or any URL instead.</li>
</ul>
'''),
        ('config', 'Timing & rules', '''
<table>
<thead><tr><th>Setting</th><th>Default</th><th>What it does</th></tr></thead>
<tbody>
<tr><td>Trigger state</td><td>Delivered</td><td>The order milestone that starts the clock (Delivered / Payment settled / Shipped).</td></tr>
<tr><td>Delay (days)</td><td>14</td><td>How long after the order date to send.</td></tr>
<tr><td>Min order value</td><td>0</td><td>Skip orders below this value.</td></tr>
<tr><td>Cooldown (days)</td><td>120</td><td>Never invite the same customer more often than this.</td></tr>
<tr><td>Max per run</td><td>200</td><td>Safety throttle per hourly run.</td></tr>
</tbody>
</table>
<p>Every invitation is deduped per order, and the plain-English status line at the top of the admin page always tells you exactly what the current settings will do.</p>
'''),
        ('exclusions', 'Exclusions & opt-out', '''
<p>Exclude any <strong>email</strong> or whole <strong>domain</strong> in the Exclusions tab — wholesale accounts, staff, VIPs. Every invitation carries a signed one-click <strong>unsubscribe</strong> link; anyone who clicks it is added to the opt-out list automatically and never emailed again. The full send history (sent / skipped / failed, with reasons) is in the Activity tab.</p>
'''),
        ('email', 'The email', '''
<p>The invitation subject and HTML body are fully editable per channel, with variables <code>{{firstName}}</code>, <code>{{orderCode}}</code>, <code>{{businessName}}</code>, <code>{{reviewUrl}}</code> and a <code>{{ratingBlock}}</code> that renders your live stars when available. Use <em>Preview</em> to see it with sample data and <em>Send test</em> to email a copy to yourself before going live.</p>
<p><strong>Product reviews.</strong> Under <em>What to ask for</em> in Settings, choose Store review, Product reviews, or Both. In product (or both) mode the email lists the actual products from the customer's order, each with its own "Review this" button linking to your storefront's product-review page — set the link template (with <code>{slug}</code>, <code>{name}</code>, <code>{orderCode}</code>) in Settings. Two extra template variables, <code>{{reviewButton}}</code> and <code>{{productList}}</code>, control where the store button and the product list appear.</p>
'''),
        ('licensing', 'Licensing', '''
<p>Free tier: configure, preview and test-send. <strong>Scheduled sending requires a licence</strong> from the <a href="/vendure-plugins/review-requests/">plugin page</a> — monthly, annual (two months free), or lifetime. Easiest: click <em>Start 14-day free trial</em> (or <em>Buy lifetime</em>) on the plugin's admin banner — checkout opens in a new tab and the key installs itself within a minute (renewals too). Already have a key? Paste it into the same banner (<em>Activate</em>) — no redeploy. For config-as-code, set it as <code>HULO_LICENCE_KEY_REVIEW_REQUESTS</code>; the env key wins when both are present.</p>
'''),
    ],
}



def wrap_tables(html_str):
    """Wrap every <table> in a scroll container so it doesn't overflow on mobile."""
    return re.sub(
        r'(<table>.*?</table>)',
        r'<div class="table-wrap" role="region" aria-label="Data table" tabindex="0">\1</div>',
        html_str,
        flags=re.DOTALL,
    )


# ─────────────────────────────────────────────────────────────────────────
# Quotations
# ─────────────────────────────────────────────────────────────────────────

QUOTATIONS_MANUAL = {
    'slug': 'quotations',
    'title_short': 'Quotations',
    'sections': [
        ('overview', 'Overview', '''
<p><strong>Quotations</strong> is an end-to-end quotation engine for Vendure. The full lifecycle lives in your admin: build a quote from the live catalogue (or free-text lines), email the customer a branded page with a signed link, watch it move through <code>sent → viewed → accepted / declined</code>, chase automatically, and convert wins to draft orders at the exact quoted total.</p>
<ul>
<li><strong>Statuses:</strong> draft → sent → viewed → accepted / declined / expired / cancelled → converted.</li>
<li><strong>Money:</strong> integer minor units throughout; per-line % discount, quote-level % or fixed discount (applied before VAT), configurable VAT rate per quote.</li>
<li><strong>Audit:</strong> every step (including chasers and customer opens) is an event on the quote.</li>
</ul>
'''),
        ('install', 'Install & configure', '''
<p>Install and register the plugin:</p>
<pre><code>yarn add @huloglobal/vendure-plugin-quotations</code></pre>
<pre><code>import { QuotationsPlugin } from '@huloglobal/vendure-plugin-quotations';

plugins: [
  QuotationsPlugin.init({
    publicBaseUrl: 'https://shop.example.com',   // used for customer quote links
    licenceKey: process.env.HULO_LICENCE_KEY_QUOTATIONS,  // optional — or activate in the admin
  }),
]</code></pre>
<p>Add <code>QuotationsPlugin.uiExtensions</code> to your admin-ui <code>compileUiExtensions</code> extensions list and rebuild the admin. Tables are created automatically on boot (MySQL, MariaDB and PostgreSQL).</p>
<p>Emails send via SMTP from <code>SMTP_SERVER / SMTP_PORT / SMTP_USER / SMTP_PASSWORD / SMTP_FROM</code>, or pass <code>smtp</code> in <code>init()</code>.</p>
<p>In the admin <em>Quotations → Settings</em>, set your business name, logo URL, accent colour, notification address, numbering prefix, default validity/VAT/terms, and the chaser/expiry-reminder cadence — per channel.</p>
'''),
        ('workflow', 'The quoting workflow', '''
<ol>
<li><strong>Build:</strong> New quote → search existing customers to autofill their details, then search the catalogue by name/SKU (price pre-fills) or add custom lines. Set quantities, unit-price overrides and per-line discounts; add a quote-level discount, VAT rate, validity and notes/terms. Totals preview live.</li>
<li><strong>Send:</strong> "Save &amp; send" emails the customer a branded message with the signed quote link — sent <em>as</em> the member of staff you pick in the editor (their name fronts the From header, replies go to them, and the quote page shows "Prepared by"). Preview the rendered email or test-send it to yourself first. Re-send any time; the link is stable.</li>
<li><strong>Track:</strong> the first open flips the quote to <em>viewed</em> (optionally emailing you at that moment — the best follow-up cue). Add internal notes to the activity trail; extend validity (reviving expired quotes) in one click. The customer accepts by typing their full name (recorded as a signature with a timestamp) or declines with a reason — you're notified by email either way.</li>
<li><strong>Chase:</strong> the hourly worker sends one reminder for unopened quotes after N days, an expires-soon nudge before the validity date, and expires overdue quotes automatically.</li>
<li><strong>Convert:</strong> on an accepted quote, "Convert to order" creates a Vendure <em>draft order</em>: catalogue lines become real order lines and one "Quotation pricing" surcharge reconciles any difference, so the draft total equals the quote exactly. Complete the draft in Orders as usual.</li>
</ol>
<p>Sent quotes that have been decided are immutable — use <em>Duplicate</em> to spin a linked revision when the deal changes.</p>
'''),
        ('endpoints', 'HTTP endpoints', '''
<table>
<tr><th>Method</th><th>Path</th><th>Purpose</th></tr>
<tr><td>GET</td><td><code>/quotations/quote/:token</code></td><td>Public customer quote page (signed link; marks viewed)</td></tr>
<tr><td>POST</td><td><code>/quotations/quote/:token</code></td><td>Public accept (typed signature) / decline</td></tr>
<tr><td>GET/POST</td><td><code>/quotations/quotes</code></td><td>Admin: list / create</td></tr>
<tr><td>PUT/DELETE</td><td><code>/quotations/quotes/:id</code></td><td>Admin: update draft/open · delete draft</td></tr>
<tr><td>POST</td><td><code>/quotations/quotes/:id/send</code></td><td>Admin: email the customer (licensed)</td></tr>
<tr><td>POST</td><td><code>/quotations/quotes/:id/convert</code></td><td>Admin: accepted quote → draft order (licensed)</td></tr>
<tr><td>POST</td><td><code>/quotations/quotes/:id/duplicate</code></td><td>Admin: duplicate / revise</td></tr>
<tr><td>POST</td><td><code>/quotations/quotes/:id/cancel</code></td><td>Admin: withdraw an open quote</td></tr>
<tr><td>GET</td><td><code>/quotations/stats</code></td><td>Admin: win rate, open pipeline, response time</td></tr>
<tr><td>GET</td><td><code>/quotations/variants/search</code></td><td>Admin: catalogue search for the editor</td></tr>
</table>
'''),
        ('licensing', 'Licensing & tiers', '''
<p>Unlicensed installs run in the <strong>free tier</strong> — start the 14-day free trial from the admin banner (card required, nothing charged until day 15, cancel any time) to switch everything on. Free tier: drafting, pricing and previewing quotes stay free — <strong>sending, chasers and order conversion require a licence</strong>. Click <em>Buy licence</em> on the admin banner and the key installs itself within a minute of checkout (renewals too); or paste a key into the admin (Activate) or set <code>HULO_LICENCE_KEY_QUOTATIONS</code>; the env key wins when both are present. Buy at <a href="/vendure-plugins/quotations/">huloglobal.com/vendure-plugins/quotations</a> — monthly, annual (two months free), or lifetime.</p>
'''),
        ('troubleshooting', 'Troubleshooting', '''
<ul>
<li><strong>Emails not sending:</strong> check the SMTP env vars; the send response surfaces the SMTP error verbatim in the admin notification.</li>
<li><strong>Customer link 404s:</strong> draft quotes have no public page — send the quote first. Withdrawn (cancelled) quotes deliberately stop resolving.</li>
<li><strong>Convert fails on a line:</strong> the referenced variant must still be enabled and in the channel; the error names the offending line. Free-text-only quotes convert as a single surcharge.</li>
<li><strong>Chasers not going out:</strong> they run on the <em>worker</em> process, hourly, licensed installs only, and each quote gets at most one chaser.</li>
</ul>
'''),
    ],
}

# ─────────────────────────────────────────────────────────────────────────
# Business Credit
# ─────────────────────────────────────────────────────────────────────────

BUSINESS_CREDIT_MANUAL = {
    'slug': 'business-credit',
    'title_short': 'Business Credit',
    'sections': [
        ('overview', 'Overview', '''
<p><strong>Business Credit</strong> adds trade-credit accounts to Vendure. A business customer applies for terms from your storefront, you approve them with a credit limit and net terms, and from then on they can choose <em>Pay on Account</em> at checkout: the order is placed immediately and an invoice with a due date is raised against their account. Money comes back by bank transfer, card (a Stripe pay link), direct debit, cheque, cash, credit note or write-off, and every settlement is allocated oldest-first across their open invoices. A daily run marks invoices overdue, sends reminders, applies late fees if you use them, suspends accounts that go too far past due, and emails monthly statements.</p>
<ul>
<li><strong>Available credit</strong> = effective limit (a temporary increase while it lasts, else the permanent limit) − open invoice balances (including late fees) + any credit balance held from overpayments.</li>
<li><strong>Account statuses:</strong> pending → active ⇄ suspended → closed (closing needs zero exposure).</li>
<li><strong>Invoice statuses:</strong> open → part_paid → paid; overdue once past due date plus grace; written_off; void.</li>
<li><strong>Audit:</strong> every limit change stores old value, new value, kind (permanent / temporary / expired), reason and administrator; every state change writes an event.</li>
</ul>
'''),
        ('install', 'Install & configure', '''
<p>Install and register the plugin:</p>
<pre><code>yarn add @huloglobal/vendure-plugin-business-credit</code></pre>
<pre><code>import { BusinessCreditPlugin } from '@huloglobal/vendure-plugin-business-credit';

plugins: [
  BusinessCreditPlugin.init({
    publicBaseUrl: 'https://shop.example.com',        // licence domain matching
    storefrontBaseUrl: 'https://shop.example.com',    // links in customer emails
    licenceKey: process.env.HULO_LICENCE_KEY_BUSINESS_CREDIT,  // optional — or activate in the admin
    stripeWebhookSecret: process.env.BUSINESS_CREDIT_STRIPE_WEBHOOK_SECRET, // card pay links
    smtp: { host, port, user, pass, from },           // or SMTP_SERVER / SMTP_USER / SMTP_PASSWORD env
  }),
]</code></pre>
<p>Add the admin UI in your <code>compileUiExtensions</code> call with <code>BusinessCreditPlugin.uiExtensions</code>, then create a <strong>payment method</strong> in Settings → Payment methods: handler <em>Pay on Account (business credit)</em>, eligibility checker <em>business-credit-eligibility</em>. The method only appears at checkout for customers with an active account, enough available credit and no overdue hold. Tables are created on first boot; no migration is needed.</p>
<table>
<tr><th>Setting (per channel)</th><th>What it does</th></tr>
<tr><td>Default terms / limit / grace</td><td>Applied to approvals; grace days delay the overdue mark.</td></tr>
<tr><td>Invoice prefix + sequence</td><td>Invoice numbers such as <code>INV-000042</code>.</td></tr>
<tr><td>Reminder schedule</td><td>Days relative to the due date, e.g. <code>-3, 0, 7, 14, 30</code>.</td></tr>
<tr><td>Late fee % per month + grace</td><td>Pro-rata monthly fee on the overdue balance; off when empty.</td></tr>
<tr><td>Auto-suspend after N days</td><td>Suspends the account when any invoice is that far overdue.</td></tr>
<tr><td>Statement day + statement emails</td><td>Emails last month's statement with aging on that day.</td></tr>
<tr><td>Require purchase order</td><td>Pay on Account is refused without a PO number.</td></tr>
<tr><td>Remittance text</td><td>Your bank details, shown on invoices, emails and the confirmation page.</td></tr>
</table>
'''),
                ('requests', 'Quote requests from your storefront', '''
<p>Customers can ask for a quote from a basket, a product page, a calculator or a plain form: post JSON to <code>POST /quotations/request</code> with the channel's <code>vendure-token</code> header (name, email, company, phone, message, source and optional lines by variant id or SKU). The request lands under <strong>Sales → Quotations</strong> as <em>requested</em> with catalogue lines pre-priced at list, the notify address hears about it, and the customer receives an acknowledgement carrying the reference. Price any free-text lines, then <strong>Send to customer</strong>. Turn requests off per channel in Settings; the endpoint is throttled and honeypot-protected.</p>
'''),
('admin', 'Admin UI', '''
<p><strong>Sales → Business credit</strong>.</p>
<ul>
<li><strong>Overview</strong> — total exposure, overdue, credit held, due in the next seven days, pending applications, aging buckets and the ten largest exposures.</li>
<li><strong>Accounts</strong> — search and filter; open an account for its availability gauge, company details, terms, status actions (suspend / reactivate / close), limit adjustments with history, invoices, ledger, settlement recording, statements and events. <em>New account</em> creates one for an existing customer without an application.</li>
<li><strong>Applications</strong> — the storefront queue: approve with a limit, terms and a note, or reject with a note; the customer is emailed either way.</li>
<li><strong>Invoices</strong> and <strong>Settlements</strong> — all invoices and payments across accounts with write-off, void, fee, pay-link and refund actions, plus CSV export.</li>
<li><strong>Settings</strong> — the per-channel configuration above, email previews and a test send, and <em>Run dunning now</em> with a report.</li>
</ul>
'''),
        ('platform', 'Company accounts, invitations, auto-approval, reviews', '''
<p><strong>Members.</strong> An account belongs to one customer login (the owner) but a company usually has several buyers. The owner adds colleagues from the storefront (Credit account → Team) as <em>buyer</em> (can place orders on account) or <em>viewer</em> (can see invoices and statements only); admins can do the same from the account's Team pane. Members share the limit, funds and invoices of the company account.</p>
<p><strong>Invitations.</strong> Sales → Business credit → Invitations → <em>Invite a business</em>: email, company, limit, terms and a message. The invitee gets a link valid for the configured number of days; when they accept while signed in with that email, an active account is created at the invited limit — no application needed.</p>
<p><strong>Auto-approval.</strong> In Settings, switch on auto-approval and set the maximum limit, minimum settled orders, minimum spend and whether a company number is required. Storefront applications that meet every rule are approved immediately (tagged <em>Auto-approved</em> in the queue); the rest wait for you.</p>
<p><strong>Reviews.</strong> Every approval sets a review date (Settings → review every N months). The daily run emails you when an account is due and the account shows a <em>Review due</em> pill until you click <em>Mark reviewed</em>.</p>
'''),
        ('plans', 'Payment plans', '''
<p>An outstanding invoice can be split into instalments: Invoices → <em>Create payment plan</em> (number of instalments, first date, interval, note) or accept a customer's request from their account page. While a plan is active, reminders and overdue marking follow the instalment dates, late fees pause, and each settlement fills the instalments in order; the plan completes when the invoice is paid and can be cancelled at any time (the invoice then falls back to its original due date).</p>
'''),
        ('loyalty', 'Reward points', '''
<p>Sales → Business credit → Loyalty. Switch the programme on per channel and set: points per £1 spent, the value of a point when redeemed, the minimum points to redeem, the maximum share of an order that points may cover, expiry in months, a signup bonus, whether on-account orders earn, and tiers (name, lifetime-points threshold, earn multiplier). Points are earned when an order's payment settles and reversed if it is cancelled. At checkout a signed-in customer applies points as a discount (a negative surcharge on the order); the storefront shows "Earn ~N points" on product pages and the balance, tier progress and history under Account → Reward points. Adjust balances, view any customer's history, see programme statistics and export CSV from the Loyalty tab.</p>
'''),
        ('settlements', 'Settlements & Stripe', '''
<p>Record a settlement with a method, amount, reference and date. Allocation is oldest-first across open invoices unless you allocate per invoice; anything left over is held as account credit and applied to the next invoices automatically. Overpayments, credit notes from refunds and write-offs all flow through the same ledger, so the account balance is always the sum of its ledger rows.</p>
<p><strong>Prepaid funds.</strong> Money can also be paid in before any invoice exists: customers top up by card from their account page, or you record a deposit (account → Funds). Held funds settle open invoices at once and pay for new on-account orders the moment they are placed, so an account with a zero limit and £500 of funds can order up to £500. Withdraw unused funds from the same pane.</p>
<p><strong>Card pay links</strong> create a Stripe Checkout Session for one or more invoices using the Stripe key on the channel's Stripe payment method. Point a Stripe webhook at <code>https://your-vendure-host/business-credit/stripe-webhook</code> with the events <code>checkout.session.completed</code> and <code>checkout.session.async_payment_succeeded</code>, and set the signing secret as <code>BUSINESS_CREDIT_STRIPE_WEBHOOK_SECRET_&lt;CHANNELCODE&gt;</code> or the plugin's <code>stripeWebhookSecret</code>. Replays are ignored: one settlement per payment intent.</p>
'''),
        ('endpoints', 'REST endpoints', '''
<table>
<tr><th>Method</th><th>Path</th><th>Purpose</th></tr>
<tr><td>GET</td><td><code>/business-credit/my/account</code></td><td>Shop: limit, available credit, terms, status</td></tr>
<tr><td>POST</td><td><code>/business-credit/my/apply</code></td><td>Shop: apply for an account (licensed)</td></tr>
<tr><td>GET</td><td><code>/business-credit/my/invoices</code></td><td>Shop: my invoices</td></tr>
<tr><td>POST</td><td><code>/business-credit/my/invoices/pay-link</code></td><td>Shop: pay selected invoices by card (licensed)</td></tr>
<tr><td>GET</td><td><code>/business-credit/my/statement</code></td><td>Shop: statement for a period (JSON or HTML)</td></tr>
<tr><td>GET</td><td><code>/business-credit/dashboard</code></td><td>Admin: exposure, overdue, aging</td></tr>
<tr><td>GET/POST</td><td><code>/business-credit/accounts</code></td><td>Admin: list / create</td></tr>
<tr><td>POST</td><td><code>/business-credit/accounts/:id/limit</code></td><td>Admin: permanent or temporary limit change</td></tr>
<tr><td>POST</td><td><code>/business-credit/accounts/:id/status</code></td><td>Admin: suspend / reactivate / close</td></tr>
<tr><td>POST</td><td><code>/business-credit/applications/:id/approve</code></td><td>Admin: approve with limit + terms</td></tr>
<tr><td>POST</td><td><code>/business-credit/settlements</code></td><td>Admin: record a settlement</td></tr>
<tr><td>POST</td><td><code>/business-credit/invoices/:id/pay-link</code></td><td>Admin: Stripe pay link for an invoice</td></tr>
<tr><td>POST</td><td><code>/business-credit/stripe-webhook</code></td><td>Stripe: signed webhook for card settlements</td></tr>
<tr><td>POST</td><td><code>/business-credit/dunning/run</code></td><td>Admin: run reminders / fees / suspensions now</td></tr>
<tr><td>GET</td><td><code>/business-credit/export/:kind.csv</code></td><td>Admin: invoices / settlements / ledger CSV (licensed)</td></tr>
</table>
<p>Storefront tip: send the customer's PO number as <code>metadata.purchaseOrder</code> in <code>addPaymentToOrder</code>, and read <code>payment.metadata.public</code> (invoice number, due date, remittance text) on your confirmation page.</p>
'''),
        ('licensing', 'Licensing & tiers', '''
<p>Unlicensed installs run in the <strong>free tier</strong>: accounts, limits with the audit trail, Pay on Account, invoices, manual settlements, the ledger and statements in the admin all stay on. <strong>Card pay links, reminders and dunning emails, late fees, auto-suspend, statement emails, CSV exports and storefront applications require a licence.</strong> Start the 14-day free trial from the admin banner, click <em>Buy licence</em> and the key installs itself within a minute of checkout, or paste a key into the admin or set <code>HULO_LICENCE_KEY_BUSINESS_CREDIT</code>. Buy at <a href="/vendure-plugins/business-credit/">huloglobal.com/vendure-plugins/business-credit</a> — monthly, annual, or lifetime.</p>
'''),
        ('troubleshooting', 'Troubleshooting', '''
<ul>
<li><strong>Pay on Account is not offered at checkout:</strong> the customer needs an <em>active</em> account in this channel, available credit at least the order total, no overdue hold, and the payment method must be enabled with the <em>business-credit-eligibility</em> checker.</li>
<li><strong>Declined with "purchase order required":</strong> the channel or account requires a PO; send it as <code>metadata.purchaseOrder</code>.</li>
<li><strong>No reminder emails:</strong> reminders need a licence, SMTP configured, and the daily run happens on the worker at 07:00 — use <em>Run dunning now</em> in Settings to test.</li>
<li><strong>Card payment did not settle the invoice:</strong> check the webhook secret env name matches the channel code, and that Stripe shows the event delivered with a 200.</li>
<li><strong>Cannot close an account:</strong> closing needs zero exposure — settle or write off open invoices first.</li>
</ul>
'''),
    ],
}

# ─────────────────────────────────────────────────────────────────────────
# Checkout Guard
# ─────────────────────────────────────────────────────────────────────────

CHECKOUT_GUARD_MANUAL = {
    'slug': 'checkout-guard',
    'title_short': 'Checkout Guard',
    'sections': [
        ('overview', 'Overview', '''
<p><strong>Checkout Guard</strong> is the safety layer around Vendure checkout and payments: Stripe manual-capture holds that actually place the order (an Authorized payment, capture or cancel from the admin, a safety capture before the authorisation expires), a bank-transfer method that carries the account details to the storefront and expires unpaid orders, a payment-event log with nightly Stripe reconciliation, session-bound anonymous order lookup, a trusted client-IP contract for server-side proxies, rate limits on the checkout mutations, and a checkout funnel.</p>
'''),
        ('install', 'Install & configure', '''
<pre><code>yarn add @huloglobal/vendure-plugin-checkout-guard</code></pre>
<pre><code>import { CheckoutGuardPlugin, SessionBoundOrderByCodeAccessStrategy } from '@huloglobal/vendure-plugin-checkout-guard';

orderOptions: { orderByCodeAccessStrategy: new SessionBoundOrderByCodeAccessStrategy('2h') },
plugins: [
  CheckoutGuardPlugin.init({
    publicBaseUrl: 'https://shop.example.com',
    licenceKey: process.env.HULO_LICENCE_KEY_CHECKOUT_GUARD,
    stripe: { webhookSecret: process.env.STRIPE_CG_WEBHOOK_SECRET, safetyCaptureDays: 6 },
    bankTransfer: { expiryDays: 7, reminderAfterDays: 3 },
    reconciliation: { enabled: true, lookbackDays: 3 },
    trustedClientIp: { header: 'x-real-client-ip', secretHeader: 'x-checkout-guard-proxy', secret: process.env.CHECKOUT_GUARD_PROXY_SECRET },
    ops: { slackWebhookUrl: process.env.OPS_SLACK_WEBHOOK_URL, adminEmail: 'ops@example.com' },
  }),
]</code></pre>
<p>Add <code>CheckoutGuardPlugin.uiExtensions</code> to <code>compileUiExtensions</code>. Create a payment method with the <em>stripe-hold</em> handler per channel that should hold rather than charge, and one with the <em>bank-transfer</em> handler (its arguments carry the account details shown to customers). Point a Stripe webhook at <code>/checkout-guard/stripe-webhook</code> with <code>payment_intent.amount_capturable_updated</code>, <code>payment_intent.payment_failed</code> and <code>charge.succeeded</code>.</p>
'''),
        ('admin', 'Admin UI', '''
<p><strong>Sales → Checkout Guard</strong>: Overview KPIs, Holds (capture / cancel), Bank transfers (awaiting / expired / settled, mark received), Payment events, Funnel and Settings, plus the Licence & billing card.</p>
'''),
        ('licensing', 'Licensing & tiers', '''
<p>Free tier: session-bound order lookup, trusted client IP, rate limits, funnel and the bank-transfer handler. <strong>Stripe holds, bank-transfer expiry and reminders, the failed-payment log, reconciliation, drift guard and ops alerts require a licence.</strong> Start the 14-day free trial or buy from the admin banner, or set <code>HULO_LICENCE_KEY_CHECKOUT_GUARD</code>. Buy at <a href="/vendure-plugins/checkout-guard/">huloglobal.com/vendure-plugins/checkout-guard</a>.</p>
'''),
        ('troubleshooting', 'Troubleshooting', '''
<ul>
<li><strong>Hold placed but order not PaymentAuthorized:</strong> the webhook is not reaching the plugin or the secret is wrong — Stripe's dashboard shows the delivery status; the endpoint answers 5xx so Stripe retries.</li>
<li><strong>Bank transfers never expire:</strong> expiry and reminders run on the worker and need a licence.</li>
<li><strong>Order IP shows the proxy:</strong> the storefront proxy must send both the client-IP header and the shared-secret header configured in <code>trustedClientIp</code>.</li>
</ul>
'''),
    ],
}


PAYMENTS_MANUAL = {
    'slug': 'payments',
    'title_short': 'Payments',
    'sections': [
        ('overview', 'Overview', '''
<p><strong>Payments</strong> puts eleven payment systems — Stripe, Adyen, PayPal, Mollie, Square, Braintree, GoCardless, Checkout.com, Coinbase Commerce, bank transfer and pay-later — behind one contract, and serves a hosted checkout page so a storefront needs no provider code at all. The storefront asks which providers to offer and gets a session; the provider's own client renders cards, Apple Pay, Google Pay, iDEAL, Klarna and the rest with 3-D Secure handled by the provider; the plugin re-reads the result from the provider (amount, currency, order code) before Vendure records the payment. Automatic or manual capture, partial captures and refunds, disputes, saved cards, subscriptions, pay-by-link, routing rules and surcharges work the same way on every provider, and everything lands in one ledger with a dashboard under <strong>Sales → Payments</strong>.</p>
'''),
        ('install', 'Install & configure', '''
<pre><code>yarn add @huloglobal/vendure-plugin-payments</code></pre>
<pre><code>import { HuloPaymentsPlugin } from '@huloglobal/vendure-plugin-payments';

plugins: [
  HuloPaymentsPlugin.init({
    publicBaseUrl: 'https://shop.example.com',          // webhook + return URLs
    licenceKey: process.env.HULO_LICENCE_KEY_PAYMENTS,   // optional — or activate in the admin
    ops: { email: 'ops@example.com', webhookUrl: process.env.OPS_SLACK_WEBHOOK },
  }),
]</code></pre>
<p>Add <code>HuloPaymentsPlugin.uiExtensions</code> to <code>compileUiExtensions</code> and recompile the admin UI. Tables are created on boot. The plugin adds three custom fields to <code>ProductVariant</code> for subscriptions, so installs that use migrations need one: <code>npx vendure migrate</code>.</p>
'''),
        ('connect', 'Connecting a provider', '''
<p>Open <strong>Sales → Payments → Providers</strong> and click <strong>Connect</strong> on a provider card. Paste the keys from its dashboard (each card links to the exact page), click <em>Test connection</em> to see which account they belong to, then <em>Connect</em>. The plugin verifies the keys with the provider, registers the webhook through the provider's API and stores the signing secret, and creates the Vendure payment method on the channel you chose. Mollie needs no webhook setup; Adyen creates the webhook and HMAC key when the API credential has the Management API webhook role, otherwise the card tells you exactly what to add by hand.</p>
<table><thead><tr><th>Provider</th><th>What to paste</th><th>Where it comes from</th></tr></thead><tbody>
<tr><td>Stripe</td><td>Secret key, publishable key</td><td>Dashboard → Developers → API keys (test or live pair)</td></tr>
<tr><td>Adyen</td><td>API key, merchant account, client key, live URL prefix (live only)</td><td>Customer Area → Developers → API credentials; Account → Merchant accounts</td></tr>
<tr><td>PayPal</td><td>Client ID, client secret</td><td>developer.paypal.com → Apps &amp; Credentials → REST app</td></tr>
<tr><td>Mollie</td><td>API key</td><td>Dashboard → Developers → API keys</td></tr>
<tr><td>Square</td><td>Access token, application ID, location ID</td><td>developer.squareup.com → your app → Credentials / Locations</td></tr>
<tr><td>Braintree</td><td>Merchant ID, public key, private key</td><td>Control Panel → Settings → API</td></tr>
<tr><td>GoCardless</td><td>Access token (+ webhook secret)</td><td>Dashboard → Developers → Access tokens / Webhook endpoints</td></tr>
<tr><td>Checkout.com</td><td>Secret key, public key, processing channel ID</td><td>Dashboard → Developers → Keys; Settings → Channels</td></tr>
<tr><td>Coinbase Commerce</td><td>API key (+ webhook shared secret)</td><td>Settings → Security / Notifications</td></tr>
<tr><td>Bank transfer</td><td>Account name, sort code / account number or IBAN</td><td>Your bank</td></tr>
<tr><td>Pay later</td><td>Payment terms in days</td><td>—</td></tr>
</tbody></table>
<p>Prefer the standard route? <strong>Settings → Payment methods → Create</strong> and pick the handler <em>HULO Payments — Stripe / Adyen / PayPal / Mollie</em>; every field explains where its value comes from. Attach the <em>HULO Payments rules</em> eligibility checker to any method to limit it by order total, currency, country, customer group or signed-in customers.</p>
'''),
        ('hosted', 'Hosted checkout page (simplest)', '''
<pre><code>mutation { huloHostedCheckout(returnUrl: "https://shop.example.com/checkout/return", cancelUrl: "https://shop.example.com/checkout") { url expiresAt } }</code></pre>
<p>Redirect the customer to <code>url</code>. The page lists every enabled method in the order set under Settings, drives each provider's own client (cards, wallets, redirects, bank-transfer instructions), records the payment through Vendure and sends the customer back to <code>returnUrl?order=CODE&amp;result=paid|pending</code>. Brand it (shop name, colour, logo) under <strong>Settings → Hosted checkout page</strong>. Links are single-use and expire after two hours.</p>
'''),
        ('storefront', 'Embedded integration (advanced)', '''
<pre><code># 1. Providers to offer for the active order (preferred first)
query { huloPaymentProviders { methodCode provider name publicConfig capabilities surcharge preferred } }

# 2. A session for the active order
mutation { huloCreatePaymentSession(methodCode: "stripe", options: { returnUrl: "https://shop.example.com/checkout/return" }) {
  provider clientSecret sessionId sessionData checkoutUrl publicKey environment config amount currency } }

# 3. After the provider's client reports success — the normal Vendure step
mutation { addPaymentToOrder(input: { method: "stripe", metadata: { paymentIntentId: "pi_…" } }) { ... on Order { state } ... on ErrorResult { message } } }</code></pre>
<table><thead><tr><th>Provider</th><th>Client</th><th>metadata for addPaymentToOrder</th></tr></thead><tbody>
<tr><td>Stripe</td><td>Payment Element with <code>clientSecret</code></td><td><code>{ paymentIntentId }</code></td></tr>
<tr><td>Adyen</td><td>Drop-in with <code>sessionId</code> + <code>sessionData</code></td><td><code>{ sessionId, sessionResult }</code></td></tr>
<tr><td>PayPal</td><td>Buttons, <code>createOrder: () => sessionId</code></td><td><code>{ paypalOrderId }</code></td></tr>
<tr><td>Mollie</td><td>Redirect to <code>checkoutUrl</code></td><td><code>{ molliePaymentId }</code></td></tr>
</tbody></table>
<p>Also available: <code>huloSavedPaymentMethods</code>, <code>huloRemoveSavedPaymentMethod</code>, <code>huloMySubscriptions</code>, <code>huloCancelSubscription</code> and <code>huloApplyPaymentSurcharge</code>.</p>
'''),
        ('subscriptions', 'Subscriptions', '''
<p>Set <strong>Subscription billing interval</strong> (daily / weekly / monthly / yearly), optionally <em>every N intervals</em> and <em>free trial days</em>, on a product variant. Its price is the price per period. When an order containing it is paid through a HULO method the plugin creates the subscription: Stripe, PayPal and Mollie bill natively; Adyen renewals are charged hourly by the plugin's scheduler from the stored card. Failed renewals mark the subscription past due, alert ops and cancel after the number of failed daily attempts set in Settings. Customers see and cancel their subscriptions through the shop API; admins pause, resume and cancel from the Subscriptions tab, which also shows MRR.</p>
'''),
        ('paylink', 'Pay by link', '''
<p>From the <strong>Pay by link</strong> tab, enter any order code that still needs payment — a draft order built in the admin, an accepted quotation, a phone order — pick a provider and an expiry, and copy the link. The customer pays on the provider's hosted page and the webhook moves the order to PaymentSettled.</p>
'''),
        ('admin', 'Admin UI', '''
<p><strong>Sales → Payments</strong>: Overview (volume by day and provider, success rate, refunds, disputes, subscriptions), Transactions (the ledger, filterable by kind, status and order), Subscriptions, Pay by link, Providers (Connect, capabilities, webhook URLs, recent webhook deliveries) and Settings (provider order and fallback, saved cards, surcharges, ops email, dunning), plus the Licence &amp; billing card. Refunds are issued from the order page as usual and appear in the ledger automatically.</p>
'''),
        ('licensing', 'Licensing & tiers', '''
<p>Free tier: Stripe (sessions, wallets, 3-D Secure, captures, refunds, disputes, signed webhooks), the ledger, the dashboard and the rules checker. <strong>Adyen, PayPal, Mollie, subscriptions, saved cards, pay-by-link, provider routing and surcharges require a licence.</strong> Unlicensed installs run everything for 14 days; start the card-backed trial or buy from the admin banner.</p>
'''),
        ('troubleshooting', 'Troubleshooting', '''
<ul>
<li><strong>Payment shows Authorized but never Settled:</strong> for automatic-capture methods that means the provider is still processing or the webhook is not arriving — check the Providers tab's webhook log and the endpoint in the provider dashboard. Manual-capture payments are settled from the order page.</li>
<li><strong>Webhook returns 400 "signature mismatch":</strong> the secret on the payment method is not the one for that endpoint. Reconnect the provider from the Providers tab; it re-registers the webhook and stores the fresh secret.</li>
<li><strong>Webhook returns 404 "no enabled … payment method":</strong> the method for that provider is disabled or missing on every channel.</li>
<li><strong>Adyen payment stays Authorized with transaction "adyen-session:…":</strong> the AUTHORISATION webhook has not been received yet; it carries the pspReference and settles immediate-capture methods.</li>
<li><strong>Subscription never created:</strong> subscriptions need a licence, the variant needs a billing interval, and the first payment must have gone through a HULO method that supports subscriptions.</li>
</ul>
'''),
    ],
}


def render_manual(m):
    canonical = f'https://huloglobal.com/vendure-plugins/{m["slug"]}/docs/'
    head = DOC_HEAD.format(
        title=f"{m['title_short']} — User Manual | Hulo Global",
        description=f"Complete user manual for the @huloglobal/vendure-plugin-{m['slug']} Vendure plugin: install, admin UI, endpoints, troubleshooting.",
        canonical=canonical,
        slug=m['slug'],
        title_short=m['title_short'],
    )
    toc_items = '\n'.join(
        f'<li><a href="#{slug}">{html.escape(title)}</a></li>'
        for slug, title, _ in m['sections']
    )
    body_items = '\n'.join(
        f'<section id="{slug}"><h2>{html.escape(title)}</h2>{wrap_tables(content)}</section>'
        for slug, title, content in m['sections']
    )
    return head + f'''
<nav class="doc-toc">
<p class="text-xs uppercase tracking-wider text-ink-500 font-semibold mb-3">On this page</p>
<ul>{toc_items}</ul>
</nav>
<article class="doc-body">{body_items}</article>
''' + DOC_FOOT


def main():
    for m in (PAYMENTS_MANUAL, BUSINESS_CREDIT_MANUAL, CHECKOUT_GUARD_MANUAL, QUOTATIONS_MANUAL, EMAIL_TRACKING_MANUAL, GEO_BLOCK_MANUAL, VISITOR_ANALYTICS_MANUAL, FRAUD_PREVENTION_MANUAL, REVIEW_REQUESTS_MANUAL):
        d = OUT / m['slug'] / 'docs'
        d.mkdir(parents=True, exist_ok=True)
        (d / 'index.html').write_text(render_manual(m), encoding='utf-8')
        print(f"wrote {d / 'index.html'}")


if __name__ == '__main__':
    main()
