#!/usr/bin/env python3
"""
Build static marketing pages for huloglobal.com/vendure-plugins/

Layout:
  /vendure-plugins/                  — catalog + comparison table + FAQ
  /vendure-plugins/<slug>/           — product page (hero + sticky pricing + features + install + FAQ)
  /vendure-plugins/<slug>/install.sh — runnable install script
  /vendure-plugins/<slug>/docs/      — user manual (generated separately)

Drop dist/vendure-plugins into /var/www/huloglobal/current/dist/client/.
"""
from pathlib import Path
import html
import json
import subprocess
import textwrap


def fetch_npm_version(pkg: str) -> str | None:
    """Best-effort fetch of the latest version on the public npm registry.

    Falls back to the hardcoded value in the PLUGINS table when the
    network is unavailable, so the build still works offline."""
    try:
        out = subprocess.check_output(
            ['npm', 'view', pkg, 'version'],
            stderr=subprocess.DEVNULL, timeout=8,
        )
        v = out.decode().strip()
        return v or None
    except Exception:
        return None

HERE = Path(__file__).parent
OUT = HERE / 'dist' / 'vendure-plugins'
PACKAGES_DIR = HERE.parent / 'packages'


def pkg_dir(pkg: str) -> Path:
    """@huloglobal/vendure-plugin-foo -> ../packages/plugin-foo"""
    return PACKAGES_DIR / pkg.split('/')[-1].replace('vendure-', '')


def local_pkg_version(pkg: str) -> str | None:
    """Version from the monorepo package.json — the source of truth when the
    npm registry is unreachable. Beats a frozen literal that goes stale."""
    try:
        return json.loads((pkg_dir(pkg) / 'package.json').read_text())['version']
    except Exception:
        return None


import re as _re


def _md_inline(text: str) -> str:
    """Escape, then apply the tiny markdown subset the changelogs use."""
    out = html.escape(text)
    out = _re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', out)
    out = _re.sub(r'`([^`]+)`', r'<code class="font-mono text-[0.85em] bg-ink-100 px-1 py-0.5 rounded">\1</code>', out)
    return out


def parse_changelog(pkg: str):
    """Parse a Keep-a-Changelog CHANGELOG.md into
    [{'version', 'date', 'sections': [(heading, [item, ...]), ...]}, ...]."""
    path = pkg_dir(pkg) / 'CHANGELOG.md'
    if not path.is_file():
        return []
    releases = []
    release = section = None
    for line in path.read_text(encoding='utf-8').splitlines():
        m = _re.match(r'##\s+\[([^\]]+)\]\s*[—–-]+\s*(\S+)', line)
        if m:
            release = {'version': m.group(1), 'date': m.group(2), 'sections': []}
            releases.append(release)
            section = None
            continue
        if release is None:
            continue
        m = _re.match(r'###\s+(.+)', line)
        if m:
            section = (m.group(1).strip(), [])
            release['sections'].append(section)
            continue
        if _re.match(r'^\[[^\]]+\]:\s', line):  # reference-style link defs
            continue
        if line.startswith('- '):
            if section is None:
                section = ('Changes', [])
                release['sections'].append(section)
            section[1].append(line[2:].strip())
        elif line.startswith('  ') and section and section[1]:
            section[1][-1] += ' ' + line.strip()
    return releases

ASTRO_CSS = '/_astro/index@_@astro.CpJRZGi5.css'
BUY_BASE = 'https://elite.charity/licence/buy'
CHECKOUT_URL = 'https://elite.charity/licence/checkout'

CURRENCIES = {
    'GBP': {'monthly': '£9.95',  'lifetime': '£199', 'symbol': '£',  'label': 'GBP — British pound'},
    'USD': {'monthly': '$12.99', 'lifetime': '$249', 'symbol': '$',  'label': 'USD — US dollar'},
    'EUR': {'monthly': '€11.95', 'lifetime': '€229', 'symbol': '€',  'label': 'EUR — Euro'},
    'AUD': {'monthly': 'A$19.95','lifetime': 'A$379','symbol': 'A$', 'label': 'AUD — Australian dollar'},
    'CAD': {'monthly': 'C$17.95','lifetime': 'C$339','symbol': 'C$', 'label': 'CAD — Canadian dollar'},
}

# Currencies the licence server charges natively: every plan Price carries
# Stripe currency_options for these (set 2026-08-28), so the picker shows
# real, chargeable prices — no estimates.
PURCHASABLE_CURRENCIES = ['GBP', 'USD', 'EUR', 'AUD', 'CAD']

# Indicative FX for display-only estimates (billing stays in GBP until real
# per-currency Stripe prices exist). Matches APPROX_FX on the licence server.
APPROX_FX = {
    'USD': {'rate': 1.29, 'symbol': '$',  'label': '≈ $ USD'},
    'EUR': {'rate': 1.17, 'symbol': '€',  'label': '≈ € EUR'},
    'AUD': {'rate': 1.93, 'symbol': 'A$', 'label': '≈ A$ AUD'},
    'CAD': {'rate': 1.75, 'symbol': 'C$', 'label': '≈ C$ CAD'},
}


def approx_from_gbp(gbp_price: str, fx: dict) -> str:
    import re as _re2
    m = _re2.search(r'[0-9][0-9.]*', str(gbp_price or ''))
    if not m:
        return ''
    v = float(m.group(0)) * fx['rate']
    return '≈ ' + fx['symbol'] + (f'{v:.2f}' if v < 100 else str(round(v)))


def display_price_table(gbp_monthly: str, gbp_lifetime: str, real: dict | None = None) -> dict:
    """Real prices for purchasable currencies (from `real`, else CURRENCIES
    when amounts match the default anchors); FX estimates only for anything
    left over."""
    table = {'GBP': {'monthly': gbp_monthly, 'lifetime': gbp_lifetime, 'symbol': '£', 'approx': False}}
    source = real or (CURRENCIES if gbp_monthly == CURRENCIES['GBP']['monthly'] else None)
    for cc in [c for c in APPROX_FX if c != 'GBP']:
        if cc in PURCHASABLE_CURRENCIES and source and cc in source:
            table[cc] = {'monthly': source[cc]['monthly'], 'lifetime': source[cc]['lifetime'],
                         'symbol': source[cc]['symbol'], 'approx': False}
        else:
            fx = APPROX_FX[cc]
            table[cc] = {'monthly': approx_from_gbp(gbp_monthly, fx),
                         'lifetime': approx_from_gbp(gbp_lifetime, fx),
                         'symbol': fx['symbol'], 'approx': True}
    return table

def ccy_picker_html(select_id: str, mobile: bool = False) -> str:
    shown = PURCHASABLE_CURRENCIES + [c for c in APPROX_FX if c not in PURCHASABLE_CURRENCIES]
    if len(shown) < 2:
        return ''
    def opt_label(c):
        if c in PURCHASABLE_CURRENCIES:
            return f'{CURRENCIES[c]["symbol"]} {c}'
        return APPROX_FX[c]['label']
    opts = '\n'.join(f'<option value="{c}">{opt_label(c)}</option>' for c in shown)
    label = ('<label for="%s" class="sr-only">Currency</label>' % select_id) if mobile \
        else ('<label for="%s" class="ccy-label">Currency:</label>' % select_id)
    cls = 'ccy-select ccy-select-mobile' if mobile else 'ccy-select'
    return f'<div class="ccy-picker-wrap">{label}<select id="{select_id}" name="currency" class="{cls}">{opts}</select></div>'


# Capabilities every plugin in the suite shares — appended to each product
# page's feature list and endpoint table at render time so they stay in
# one place.
COMMON_FEATURES = [
    ('MySQL, MariaDB & PostgreSQL', 'The plugin follows whatever database your Vendure `dbConnectionOptions` use — no configuration. Verified against PostgreSQL 17; MySQL/MariaDB installs are unchanged.'),
    ('Buy & activate from the admin', 'Start the 14-day free trial, subscribe or buy lifetime from the plugin\'s admin page — checkout opens in a new tab and the key installs itself within a minute, renewals included. The same card shows your plan, first-charge date and a Manage billing link to the Stripe portal (update card, cancel, switch plan). Already have a key? Paste it into the same banner. No `.env` edit, no redeploy; environment keys still take precedence for infrastructure-as-code setups.'),
    ('Weekly report, set-up checklist & dashboard widget', 'Every Monday the plugin emails whoever runs the store a short report of what it did that week — real numbers from your own database, week-over-week, with the next set-up step to take. Change the recipient, send a test or switch it off from the plugin\'s Settings tab (needs the host\'s `SMTP_*` settings). The same numbers sit in a Vendure dashboard widget (Dashboard → Add widget) and the plugin page opens with a set-up checklist that hides itself once everything is done.'),
    ('One-click in-app updates', 'When a new version ships, an update banner shows current → latest with a What\'s-new link to the changelog. "Update now" installs the registry-verified release via your project\'s own package manager (yarn/npm/pnpm auto-detected) and gracefully restarts under pm2/systemd. Disable with `HULO_SELF_UPDATE=off`.'),
]

# API prefix per plugin, for the shared licence/update endpoint rows.
ROUTE_PREFIX = {
    'email-tracking': '/email-track',
    'geo-block': '/geo-block',
    'visitor-analytics': '/ees',
    'fraud-prevention': '/fraud-prevention',
    'review-requests': '/review-requests',
}

# What the free tier includes vs what needs a key (from each package README).
TIERS = {'payments': (['Stripe: sessions, wallets, 3-D Secure, automatic or manual capture, refunds, disputes, signed webhooks', 'Bank transfer and pay-later / invoice methods', 'The hosted checkout page', 'The payments ledger, dashboard and webhook log', 'The hulo-payment-rules eligibility checker'], ['Adyen, PayPal, Mollie, Square, Braintree, GoCardless, Checkout.com and Coinbase Commerce', 'Subscriptions and the renewal scheduler', 'Saved cards and pay-by-link', 'Provider routing, fallback on decline and surcharges']), 'business-credit': (['Accounts and credit limits with the audit trail', 'Pay-on-Account handler and eligibility checker', 'Invoices, manual settlements and allocation, the ledger', 'Statements (view), review dates, the admin dashboard'], ['Stripe card pay links and top-ups', 'Reminders, dunning emails, late fees, auto-suspend', 'Statement emails and CSV exports', 'Storefront applications, invitations, auto-approval', 'Company members, payment plans, reward points']), 'checkout-guard': (['Session-bound order lookup and trusted client IP', 'Rate limits and funnel events', 'Bank-transfer handler and eligibility checker', 'The dashboard'], ['Stripe manual-capture hold handling', 'Bank-transfer auto-expiry and reminders', 'Failed-payment recording and nightly reconciliation', 'Amount-drift guard and ops alerts']), 'fraud-prevention': (['Monitor mode: every order scored and logged', 'Manual allow / block lists', 'Simulate a rule change before enforcing it'], ['Enforce mode and review-queue holds', 'Threat-feed sync (FireHOL, Spamhaus, Tor, disposable email)', 'Email alerts']), 'review-requests': (['Configure per channel, preview the email', 'Test-send to yourself'], ['Scheduled sending after every order', 'Exclusions, cooldown and one-click unsubscribe in production']), 'quotations': (['Quote builder with live catalogue pricing', 'Previews and drafts', 'Storefront quote requests landing in the inbox'], ['Sending the signed accept / decline link', 'Auto-chasers, expiry reminders and auto-expiry', 'Accepted quote to draft order']), 'geo-block': (['Configure regions, rules and allowlists', '"What-if" simulator and audit log in the admin'], ['Live enforcement: the storefront endpoint reports the real decision (free tier always answers enabled: false)']), 'visitor-analytics': (['Tracking and data collection with the storefront helpers', 'Privacy controls (DNT, IP anonymisation, consent gate)'], ['Dashboards, funnels, exit pages and search analytics (403 on the free tier)', 'Product recommendations and abandoned-cart recovery links'])}
# Plugins currently shown in Vendure's own plugin directory.
VENDURE_DIRECTORY_LISTED = ['email-tracking', 'fraud-prevention', 'geo-block', 'quotations', 'review-requests', 'visitor-analytics']
# Submitted to the directory (2026-09-23) but not yet listed; move to LISTED when Vendure publishes them.
VENDURE_DIRECTORY_SUBMITTED = ['payments', 'business-credit', 'checkout-guard']
# Plugins that register TypeORM entities and therefore need a migration; the
# others create their tables on boot.
NEEDS_MIGRATION = ['email-tracking', 'geo-block', 'visitor-analytics', 'payments']

_DOWNLOADS_CACHE: dict = {}
def npm_downloads_last_month(pkg: str):
    """Monthly download count from the npm registry, or None."""
    if pkg in _DOWNLOADS_CACHE:
        return _DOWNLOADS_CACHE[pkg]
    try:
        import urllib.request, json as _json
        with urllib.request.urlopen(f'https://api.npmjs.org/downloads/point/last-month/{pkg}', timeout=8) as r:
            n = _json.load(r).get('downloads')
    except Exception:
        n = None
    _DOWNLOADS_CACHE[pkg] = n
    return n

_YTD_CACHE: dict = {}

def npm_downloads_this_year(pkg: str):
    """Downloads from 1 January to yesterday (npm's own count), or None."""
    if pkg in _YTD_CACHE:
        return _YTD_CACHE[pkg]
    import datetime
    today = datetime.date.today()
    rng = f"{today.year}-01-01:{(today - datetime.timedelta(days=1)).isoformat()}"
    try:
        import urllib.request, json as _json
        with urllib.request.urlopen(f'https://api.npmjs.org/downloads/point/{rng}/{pkg}', timeout=8) as r:
            n = _json.load(r).get('downloads')
    except Exception:
        n = None
    _YTD_CACHE[pkg] = n
    return n

def common_endpoints(slug: str):
    pre = ROUTE_PREFIX.get(slug, '/' + slug)
    return [
        ('GET',  f'{pre}/licence/status',   'Admin: licence + evaluation + update status'),
        ('POST', f'{pre}/licence/activate', 'Admin: activate a licence key from the admin UI'),
        ('POST', f'{pre}/update/run',       'Admin: one-click in-app update + graceful restart'),
        ('GET',  f'{pre}/digest/settings',  'Admin: weekly report recipient, last/next send'),
        ('POST', f'{pre}/digest/send-test', 'Admin: email this week\'s report to you now'),
        ('GET',  f'{pre}/setup',            'Admin: set-up checklist (what is still to do)'),
        ('GET',  f'{pre}/widget',           'Admin: headline figures for the dashboard widget'),
    ]


PLUGINS = [
    {
        'slug': 'quotations',
        'pkg': '@huloglobal/vendure-plugin-quotations',
        # Real per-currency prices — must match the currency_options on the
        # Stripe price objects (repriced 2026-09-02 by functionality tier).
        'pricing': {
            'GBP': {'monthly': '£14.95', 'lifetime': '£299', 'symbol': '£', 'label': 'GBP — British pound'},
            'USD': {'monthly': '$19.95', 'lifetime': '$399', 'symbol': '$', 'label': 'USD — US dollar'},
            'EUR': {'monthly': '€17.95', 'lifetime': '€359', 'symbol': '€', 'label': 'EUR — Euro'},
            'AUD': {'monthly': 'A$29.95', 'lifetime': 'A$599', 'symbol': 'A$', 'label': 'AUD — Australian dollar'},
            'CAD': {'monthly': 'C$26.95', 'lifetime': 'C$539', 'symbol': 'C$', 'label': 'CAD — Canadian dollar'},
        },
        'class': 'QuotationsPlugin',
        'version': '0.1.0',
        'title': 'Quotations',
        'tagline': 'End-to-end quotation engine — build quotes from your catalogue, email a signed accept/decline link, chase automatically, convert wins to draft orders at the exact quoted total.',
        'description': (
            'Everything a B2B-ish shop needs to quote like a pro. Build quotes in the '
            'admin from your live catalogue (or free-text lines) with per-line and '
            'quote-level discounts, VAT and a validity date. One click emails the '
            'customer a branded quote page where they accept with a typed-name '
            'signature — or decline with a reason — and every step lands in a '
            'per-quote audit trail. Unopened quotes get one polite chaser, '
            'expiring quotes a heads-up, and overdue ones expire themselves. '
            'Accepted quotes convert to a Vendure draft order whose total equals '
            'the quote to the penny — a pricing surcharge reconciles quoted vs '
            'catalogue pricing, so custom deals never fight your price lists.'
        ),
        'features': [
            ('Quote requests from your storefront', 'A public endpoint lets customers ask for a quote from a basket, a product page, a calculator or a plain form. It lands in your inbox as a requested quote with catalogue lines pre-priced at list, the customer gets an acknowledgement with the reference, and you price the rest and send. Throttled, honeypot-protected, switchable per channel.'),
            ('Quote builder with live catalogue search', 'Type a product name or SKU and the line lands with the current channel price pre-filled. Free-text lines for services, delivery or anything off-catalogue. Per-line quantity, unit price override, and percentage discount with live totals.'),
            ('Discounts, VAT and validity done properly', 'Quote-level discount (percent or fixed) applied before VAT; configurable VAT rate per quote (zero-rate for exports); a validity date after which the quote expires itself. All money handled in integer pence.'),
            ('Branded customer quote page', 'A signed, unguessable link opens a clean quote page in your colours with your logo: line items, totals, notes, terms — plus print/save-as-PDF. No customer account needed.'),
            ('Accept with a signature', 'The customer types their full name to accept — recorded with a timestamp as their signature, alongside an optional comment. Declines capture a reason. You get an email either way.'),
            ('Viewed / accepted / declined tracking', 'The first open flips the quote to viewed with a timestamp. Every event — created, sent, viewed, chased, accepted, declined, expired, converted — is in the per-quote activity log.'),
            ('Automatic follow-ups', 'One chaser for unopened quotes after N days, an expires-soon reminder before the validity date, and automatic expiry after it. All per-channel configurable, all logged, none sent twice.'),
            ('Convert to order at the quoted price', 'Accepted quotes become Vendure draft orders: catalogue lines are added as real order lines and a single "Quotation pricing" surcharge reconciles any difference — the draft total equals the quote total exactly.'),
            ('Revisions & duplicates', 'Sent quotes are immutable once decided; duplicate any quote as a fresh draft (linked as a revision) when the deal changes shape.'),
            ('Send as a member of staff', 'Pick which administrator each quote goes out as: their name fronts the From header, replies land in their inbox, the quote page shows "Prepared by", and acceptance/decline/opened notifications reach them directly.'),
            ('Customer picker + preview + test-send', 'Search existing Vendure customers to autofill the quote; preview the rendered email or test-send the real thing to yourself before the customer ever sees it.'),
            ('Opened notifications + extend validity', 'Optional "email me the moment the quote is first opened" — the perfect follow-up cue — plus one-click validity extension that can revive an expired quote.'),
            ('Pipeline KPIs', 'Win rate and sends over 30 days, open pipeline value, and average send-to-decision time — on the dashboard where you quote.'),
            ('Per-channel everything', 'Numbering prefix + sequence, default terms/VAT/validity, notification address and email template per sales channel — with full brand chrome on every email and quote page: logo, accent colour, website, phone, address and a company/VAT footer note.'),
        ],
        'endpoints': [
            ('POST', '/quotations/request',           'Public: a customer asks for a quote (lands as requested)'),
            ('GET',  '/quotations/quote/:token',      'Public: the customer quote page (signed link)'),
            ('POST', '/quotations/quote/:token',      'Public: accept (typed signature) or decline'),
            ('GET',  '/quotations/quotes',            'Admin: list + filter + search'),
            ('POST', '/quotations/quotes',            'Admin: create a quote'),
            ('PUT',  '/quotations/quotes/:id',        'Admin: update a draft/open quote'),
            ('POST', '/quotations/quotes/:id/send',   'Admin: email the customer (licensed)'),
            ('POST', '/quotations/quotes/:id/convert','Admin: accepted quote → draft order (licensed)'),
            ('POST', '/quotations/quotes/:id/duplicate', 'Admin: duplicate / revise'),
            ('GET',  '/quotations/stats',             'Admin: win rate + pipeline KPIs'),
            ('GET',  '/quotations/variants/search',   'Admin: catalogue search for the editor'),
        ],
    },
    {
        'slug': 'email-tracking',
        'pkg': '@huloglobal/vendure-plugin-email-tracking',
        # Real per-currency prices — must match the currency_options on the
        # Stripe price objects (repriced 2026-09-02 by functionality tier).
        'pricing': {
            'GBP': {'monthly': '£6.95', 'lifetime': '£139', 'symbol': '£', 'label': 'GBP — British pound'},
            'USD': {'monthly': '$8.99', 'lifetime': '$179', 'symbol': '$', 'label': 'USD — US dollar'},
            'EUR': {'monthly': '€8.49', 'lifetime': '€169', 'symbol': '€', 'label': 'EUR — Euro'},
            'AUD': {'monthly': 'A$13.95', 'lifetime': 'A$279', 'symbol': 'A$', 'label': 'AUD — Australian dollar'},
            'CAD': {'monthly': 'C$12.95', 'lifetime': 'C$259', 'symbol': 'C$', 'label': 'CAD — Canadian dollar'},
        },
        'class': 'EmailTrackingPlugin',
        'version': '0.8.2',
        'title': 'Email Tracking',
        'tagline': 'Per-link transactional email tracking with human-vs-machine classification, sensitive-link redaction and a per-order activity timeline.',
        'description': (
            'Drop-in tracker for every email your Vendure server sends. Wraps the '
            '`@vendure/email-plugin` pipeline plus a service for ad-hoc sends. '
            'Records every send, open and click as a raw event — never deduped — '
            'so the underlying audit trail is always intact. Each link in each '
            'email gets its own opaque token so the click handler can identify '
            '**exactly which link was clicked** (invoice view, order view, '
            'password reset, footer terms link) rather than merely "a link was '
            'clicked". Password-reset and invoice-access links are flagged '
            'sensitive so the raw destination never lands in the event log. '
            'Every open + click is classified `human_likely` / `machine_likely` '
            '/ `unknown` with reason codes (Gmail image proxy, Apple Mail Privacy '
            'Protection, Microsoft Safe Links, Proofpoint, Mimecast, Barracuda, '
            'datacentre, VPN, bot UA, …) so you can tell a real customer from a '
            'security scanner.'
        ),
        'features': [
            ('Per-link tokenisation', 'Every clickable link in every email gets a random 32-byte token; the destination is stored server-side. The click endpoint identifies exactly which link was clicked — link_type, link_label, link_text, link_index, template_section, destination host + path — and records it on the event row.'),
            ('Sensitive-link redaction', 'Flag password-reset, invoice-access-token and licence-key URLs with `isSensitive: true`. The raw destination is replaced with `[sensitive: <host>]` in the event log; only the URL hash + host are stored. The redirect still works — the raw destination just never lands on an admin-visible row.'),
            ('Human / machine / unknown classification', 'Every open and click is scored with the SDK\'s built-in classifier. Reason chips surface why an event was flagged machine-likely: `gmail-proxy`, `ampp` (Apple Mail Privacy Protection), `safelinks`, `outlook-proxy`, `proofpoint`, `mimecast`, `barracuda`, `symantec`, `datacentre`, `vpn`, `tor`, `bot-ua`, `headless`, `prefetch`, `scanner-ua`. Raw event count still recorded — the classification is advisory, never the sole basis for a decision.'),
            ('IP enrichment (ip-api.com or ipinfo)', 'Every event ingested triggers an async geo lookup (country, region, city, ASN, organisation, timezone, proxy / VPN / datacentre / mobile flags). Provider is pluggable via `HULO_IP_ENRICHMENT_PROVIDER`. Skips private / loopback / link-local. Never blocks event recording — enrichment happens fire-and-forget.'),
            ('Provider webhook receiver', 'Ingest delivered / bounced / deferred / dropped / complaint / open / click events from Postmark, SendGrid, Mailgun and Amazon SES. Each provider\'s signature scheme is verified; unconfigured providers 401; unknown slugs 404. Idempotent within 24h so retries don\'t double-count.'),
            ('Full open + click history per email', 'Raw events are never deduplicated. Multiple pixel fires from the same recipient create multiple rows; the admin UI groups for display but the underlying audit trail stays intact.'),
            ('Suppression list', 'Hard bounces and complaints auto-add to the suppression table. Subsequent sends are silently skipped and logged as `status=suppressed`.'),
            ('Per-template analytics', 'Open rate, CTR, click-to-open ratio and bounce rate per email type — order-confirmation, OTP, invoice, password-reset and your custom types.'),
            ('Bounce + complaint webhook', 'POST DSN events to `/email-track/bounce` from your postmaster integration for legacy setups.'),
            ('Admin UI: Email Log + per-customer Emails tab', 'Filter by recipient, customer, order, status, type, date range. Expand any row for the full event timeline.'),
            ('Order Activity History panel', 'On every order-detail page: chronological timeline of every transactional email event with classification badges, filters (opens only / clicks only / payment / admin notes), IP-derived location with cautionary banner, CSV export, PDF Evidence Report via short-lived signed URLs, and elevated-permission full-export for legal evidence preservation. Pagination for high-volume customers — 100 events per page with a "Load more" button.'),
            ('CSV + JSON + PDF export', 'CSV (redacted) for daily browsing, JSON via GraphQL for machine processing, PDF Evidence Report ("Order Activity and Delivery Evidence Report") for legal preservation. Sensitive fields respect the redaction rules; full export requires elevated permission.'),
            ('Works with any SMTP transport', 'Gmail, SES, SendGrid, Postmark, Mailgun, raw SMTP. Just plug `TrackingEmailSender()` into your email-plugin config.'),
            ('Graceful degradation', 'No runtime import from invoice / support-ticket / order plugins. Hosts that don\'t have those simply never pass the id; entity foreign-id columns are plain nullable ints. If a table isn\'t there yet, persistence fails silently and the redirect still works via signature verification.'),
        ],
        'endpoints': [
            ('GET',  '/email-track/open/:id.gif',     'Pixel — logs an open then serves a 1×1 GIF'),
            ('GET',  '/email-track/click/:id?u=<url>&s=<sig>', 'Click redirector — verifies HMAC signature, logs event with per-link metadata + classification, then 302s'),
            ('POST', '/email-track/bounce',           'Bounce / complaint webhook — DSN bridge'),
            ('POST', '/email-events/webhook/postmark',  'Postmark event webhook (Basic Auth verified)'),
            ('POST', '/email-events/webhook/sendgrid',  'SendGrid event webhook (ECDSA signature verified)'),
            ('POST', '/email-events/webhook/mailgun',   'Mailgun event webhook (HMAC-SHA256 verified)'),
            ('POST', '/email-events/webhook/ses',       'Amazon SES via SNS (topic ARN allowlist)'),
            ('GET',  '/email-track/log',              'Admin: paginated log with filters'),
            ('GET',  '/email-track/log/summary',      'Admin: status totals tile'),
            ('GET',  '/email-track/log/:id',          'Admin: full detail (incl. opens + clicks arrays)'),
            ('GET',  '/email-track/log/stats/by-template', 'Admin: per-template aggregates (open / click rate, CTR)'),
            ('GET',  '/email-track/log/export.csv',   'Admin: CSV export'),
            ('GET',  '/email-track/suppression',      'Admin: list suppression entries'),
            ('POST', '/email-track/suppression',      'Admin: manually add a recipient'),
            ('DELETE', '/email-track/suppression/:recipient', 'Admin: lift a suppression'),
        ],
    },
    {
        'slug': 'geo-block',
        'pkg': '@huloglobal/vendure-plugin-geo-block',
        # Real per-currency prices — must match the currency_options on the
        # Stripe price objects (repriced 2026-09-02 by functionality tier).
        'pricing': {
            'GBP': {'monthly': '£4.95', 'lifetime': '£99', 'symbol': '£', 'label': 'GBP — British pound'},
            'USD': {'monthly': '$6.49', 'lifetime': '$129', 'symbol': '$', 'label': 'USD — US dollar'},
            'EUR': {'monthly': '€5.95', 'lifetime': '€119', 'symbol': '€', 'label': 'EUR — Euro'},
            'AUD': {'monthly': 'A$9.95', 'lifetime': 'A$199', 'symbol': 'A$', 'label': 'AUD — Australian dollar'},
            'CAD': {'monthly': 'C$8.95', 'lifetime': 'C$179', 'symbol': 'C$', 'label': 'CAD — Canadian dollar'},
        },
        'class': 'GeoBlockPlugin',
        'version': '0.6.0',
        'title': 'Geo Block',
        'tagline': '37 region presets, soft-block mode, IP allowlist, audit log, "what-if" simulator.',
        'description': (
            'Per-channel geo-restrictions you can actually understand. Pick from '
            '37 hand-curated region presets (EU, EEA, Schengen, GCC, ANZAC, NATO, '
            'OECD, Commonwealth, English-speaking, MENA, ASEAN, Nordic, …) or '
            'add countries manually. Soft-block mode for "browse-only" markets. '
            'IP allowlist for offices and payment processors. Every block decision '
            'is logged for the admin Stats panel.'
        ),
        'features': [
            ('37 region presets', 'One-click setups: EU, EEA, EFTA, Schengen, Nordic, DACH, Benelux, Balkans, GCC, MENA, ASEAN, APAC, East Asia, South Asia, LATAM, North America, Caribbean, Oceania, ANZ, G7, G20, BRICS, OECD, NATO, Five Eyes, Commonwealth, English-speaking, and more.'),
            ('Per-channel rules', 'Each Vendure channel gets its own rules — perfect for multi-storefront installs (e.g. one UK-only channel, one EU channel).'),
            ('Soft-block (browse-only)', 'Mode toggle: full block hides the storefront entirely; soft mode renders it with a banner explaining you don\'t ship to their country and hiding checkout.'),
            ('IP allowlist with CIDR', 'IPs or IPv4 ranges (`203.0.113.0/24`) that bypass every rule. For your office, oncall, monitoring probes, payment processors.'),
            ('Audit log + stats', 'Every block decision logged with country, region, IP, UA, channel and reason. Admin Stats tab shows top blocked countries, daily series, and reason breakdown.'),
            ('"What-if" simulator', 'Test exactly what your rules will do for a hypothetical visitor — country, UK region, IP — before saving anything to production.'),
            ('Custom block page', 'Per-channel message, optional redirect URL and optional logo URL. Or fall back to sensible defaults per block reason.'),
            ('UK sub-region filter', 'When GB is allowed, optionally restrict to ENG / WLS / SCT / NIR. Driven from the standard ISO subdivision codes.'),
            ('Proxy-aware', 'Reads `cf-ipcountry` / Akamai / Fastly region headers when present. Saves a MaxMind lookup per request.'),
            ('Scheduled maintenance window', 'Plugin option for a date-range lockdown — every visitor is blocked (except the IP allowlist) until the window closes.'),
        ],
        'endpoints': [
            ('GET',  '/geo-block/site-config',     'Public: channel rules the storefront polls'),
            ('GET',  '/geo-block/check',           'Public: per-request decision + reason (logs to audit)'),
            ('GET',  '/geo-block/presets',         'Public: the preset catalogue (37 entries)'),
            ('GET',  '/geo-block/admin/channels',  'Admin: list channels with current rules'),
            ('POST', '/geo-block/admin/save',      'Admin: save a channel\'s rules'),
            ('GET',  '/geo-block/admin/stats',     'Admin: block totals + top countries + daily series'),
            ('POST', '/geo-block/admin/simulate',  'Admin: dry-run a visitor against current rules'),
            ('POST', '/geo-block/admin/gc',        'Admin: prune old audit rows'),
        ],
    },
    {
        'slug': 'visitor-analytics',
        'pkg': '@huloglobal/vendure-plugin-visitor-analytics',
        'class': 'VisitorAnalyticsPlugin',
        'version': '0.8.1',
        'title': 'Visitor Analytics',
        'tagline': 'Self-hosted visitor journey, cart abandonment, product recommendations, search analytics — one plugin, one database, no third party.',
        'description': (
            'Self-hosted analytics that reaches all the way from a visitor\'s '
            'first pageview to a recovered abandoned cart. Journey drawer with '
            'parsed UA + MaxMind geo + heuristic intent labels; cart abandonment '
            'detection with signed recovery links and Slack notifications; '
            'co-view product recommendations (also-viewed, personal, trending); '
            'site-search analytics (top queries, zero-result gaps, search-to-cart '
            'conversion); rage-click and dead-click hot-spot lists. Privacy-first '
            'defaults: DNT respected, IPs anonymised, optional consent gate. '
            'Ships a drop-in storefront JS helper at `/ees/hulo.js` — one script '
            'tag and every event type is wired.'
        ),
        'features': [
            ('Cart abandonment', 'Detects sessions with `cart_snapshot` events but no `checkout_completed` in the abandonment window (default 30 min). Auto-promotes to `converted` when a matching checkout later lands. Signed recovery-link tokens (time-bounded, non-reusable) — `/ees/abandoned-carts/:id/recovery-link` returns a URL you drop into a recovery email. Slack notification for high-value drops.'),
            ('Product recommendations', 'Denormalised `ProductCoView` table rebuilt every 6 hours from `product_view` events, bounded per session to 20 events so bot sessions can\'t skew the table. Three endpoints: `also-viewed` for a product-page rail, `personal` for a homepage/cart rail based on a returning visitor\'s last 10 product views, `trending` for a most-viewed-in-window rail.'),
            ('Site search analytics', 'Zero-schema-cost queries over `search` events. Top queries by volume with average results count, zero-result queries (direct catalogue-gap intel), search-to-cart conversion rate.'),
            ('Journey drawer buffs', 'Rage-click + dead-click hot-spot lists per URL. Per-session heuristic `intent` label (`purchase` / `abandon` / `frustrate` / `consider` / `browse` / `bounce`) — one glance per session in the visitor drawer.'),
            ('Drop-in storefront helper', 'Ships `/ees/hulo.js` — one script tag and every event helper (`cartSnapshot`, `productView`, `search`, `checkoutCompleted`) is on `window.hulo`. Handles batching, `sendBeacon`, auto rage-click + dead-click detection.'),
            ('Configurable conversion goals', 'CRUD a goal with a URL glob (`/checkout/thank-you/*`) and a value. Live matcher tags every pageview that hits the pattern. Dashboard shows completions per goal.'),
            ('Full visitor journey', 'Page views, time-on-page, exit pages, configurable funnel, UTM attribution, bot detection. Per-visitor profile drawer with parsed UA + MaxMind GeoLite2 geo. Survives login — guest and signed-in events share the same visitor id.'),
            ('Privacy-first defaults', 'DNT respected, IPs anonymised to /24 (IPv4) / /48 (IPv6), optional `requireConsent` gate. All three opt-outable per install.'),
            ('Live-now SSE widget', 'Real-time tile on the admin dashboard showing visitors active right now (by country).'),
            ('CSV export', '`/ees/visitors/export.csv?days=N` and `/ees/abandoned-carts/export.csv` for raw event / abandoned-cart data.'),
            ('Admin dashboards', 'Angular admin pages for Abandoned Carts (KPIs, filters, recovery-link mint, CSV export) and Analytics Insights (trending, also-viewed lookup, search analytics, rage/dead-click hot spots).'),
        ],
        'endpoints': [
            ('POST', '/ees/track',                 'Public: ingest a batch of events'),
            ('GET',  '/ees/hulo.js',               'Public: drop-in storefront helper JS (0.8.1)'),
            ('GET',  '/ees/recover-cart?t=…',      'Public: resolve a recovery-link token → cart items'),
            ('GET',  '/ees/recommendations/also-viewed?productId=…', 'Public: co-view recommendations for one product'),
            ('GET',  '/ees/recommendations/personal?visitorId=…',    'Public: personalised recs from visitor history'),
            ('GET',  '/ees/recommendations/trending?hours=…',        'Public: most-viewed products in the window'),
            ('GET',  '/ees/abandoned-carts',       'Admin: paginated list with filters'),
            ('GET',  '/ees/abandoned-carts/summary','Admin: totals + recovery rate + lost value'),
            ('GET',  '/ees/abandoned-carts/:id',   'Admin: detail incl. parsed items'),
            ('POST', '/ees/abandoned-carts/:id/recovery-link', 'Admin: mint signed recovery URL'),
            ('POST', '/ees/abandoned-carts/:id/status', 'Admin: mark recovered / dismissed'),
            ('GET',  '/ees/abandoned-carts/export.csv', 'Admin: CSV export'),
            ('GET',  '/ees/search-analytics/top',   'Admin: top search queries'),
            ('GET',  '/ees/search-analytics/no-results', 'Admin: zero-result queries'),
            ('GET',  '/ees/search-analytics/conversion', 'Admin: search→cart conversion'),
            ('GET',  '/ees/journey/rage-clicks',    'Admin: rage-click hot spots'),
            ('GET',  '/ees/journey/dead-clicks',    'Admin: dead-click hot spots'),
            ('GET',  '/ees/journey/session-summary?visitorId=…', 'Admin: per-session intent labels'),
            ('GET',  '/ees/visitors/summary',      'Admin: top-line counters + daily series'),
            ('GET',  '/ees/visitors/sources',      'Admin: top sources by visits / sessions'),
            ('GET',  '/ees/visitors/top-pages',    'Admin: most-visited URLs'),
            ('GET',  '/ees/visitors/funnel',       'Admin: configurable funnel with drop-offs'),
            ('GET',  '/ees/visitors/exit-pages',   'Admin: top exit pages'),
            ('GET',  '/ees/visitors/live',         'Admin: SSE live-now stream'),
            ('GET',  '/ees/visitors/journey/:visitorId', 'Admin: per-visitor timeline'),
            ('GET',  '/ees/visitors/export.csv',   'Admin: CSV export'),
            ('POST', '/ees/goals',                 'Admin: create a conversion goal'),
            ('GET',  '/ees/goals/stats',           'Admin: per-goal completion stats'),
        ],
    },
    {
        'slug': 'fraud-prevention',
        'pkg': '@huloglobal/vendure-plugin-fraud-prevention',
        # Real per-currency prices — must match the currency_options on the
        # Stripe price objects (repriced 2026-09-02 by functionality tier).
        'pricing': {
            'GBP': {'monthly': '£12.95', 'lifetime': '£259', 'symbol': '£', 'label': 'GBP — British pound'},
            'USD': {'monthly': '$16.95', 'lifetime': '$339', 'symbol': '$', 'label': 'USD — US dollar'},
            'EUR': {'monthly': '€15.95', 'lifetime': '€319', 'symbol': '€', 'label': 'EUR — Euro'},
            'AUD': {'monthly': 'A$25.95', 'lifetime': 'A$519', 'symbol': 'A$', 'label': 'AUD — Australian dollar'},
            'CAD': {'monthly': 'C$23.95', 'lifetime': 'C$479', 'symbol': 'C$', 'label': 'CAD — Canadian dollar'},
        },
        'class': 'FraudPreventionPlugin',
        'version': '0.1.0',
        'title': 'Fraud Prevention',
        'tagline': 'Signal-based risk scoring on every order, monitor/enforce modes, review queue with customisable customer comms, alerts to Slack/Discord/Teams/Telegram, daily threat feeds — chargebacks stopped before fulfilment.',
        'description': (
            'Every placed order is risk-scored server-side the moment it lands — '
            'no storefront integration required. Weighted signals (order velocity '
            'per IP and per canonical email identity, disposable email domains, '
            'block/allow lists with CIDR range matching, high-risk countries, '
            'failed-payment patterns, card AVS postcode/address mismatch, '
            'plus-addressing abuse, first-order value) '
            'roll up to a 0-100 score. Your per-channel thresholds decide what '
            'happens: log it, hold it for review, or hold it and tell the '
            'customer it is being verified. Digital-goods aware: fulfilment '
            '(licence keys, downloads) waits for approval, so one reviewer '
            'click is the difference between a sale and a chargeback.'
        ),
        'features': [
            ('Server-side enforcement', 'Assessment runs on OrderPlacedEvent inside Vendure — fraudsters can\'t bypass it by skipping your storefront JS. No checkout integration needed.'),
            ('Weighted signal scoring', 'Velocity (IP/hour, IP/day, email/day, daily value), order value ceilings, disposable emails, list hits, high-risk countries, failed payments, identity fan-out (many emails from one IP = card testing), VPN/proxy/datacentre IPs, IP vs billing-country mismatch, MX-less email domains, billing vs shipping postcode. Every weight overridable per channel.'),
            ('Card AVS mismatch', 'The card issuer\'s own verdict on the billing postcode and street address — the strongest address signal there is. Read automatically from Stripe for orders paid through Vendure\'s StripePlugin (no extra config), from payment metadata for custom handlers, or from a one-line avsResolver hook for any other gateway. Only an explicit fail scores; fails open. AVS fails stand out as red card chips in the review queue and on the order page, and an AVS-fails filter on both the review queue and the activity log shows only those orders — so a reviewer sees the bank\'s verdict before anything else.'),
            ('Monitor → enforce rollout', 'Start in monitor mode: everything is scored and logged, nothing is held. Watch the Activity tab, tune thresholds, then flip to enforce.'),
            ('"Off" never means blind', 'Even with protection disabled the engine still scores every order and records a shadow assessment. Risky shadow-scored orders warn in the server log, fan out to your ops channels and can email the admin — so you keep the full risk picture while protection is paused, and turning it back on starts from evidence, not guesswork.'),
            ('Risk score on the order page', 'Every paid order\'s detail page shows the risk score out of 100, level, contributing signals and review-case status — colour-coded, light + dark theme. Your team sees the risk where they already work.'),
            ('Manual review queue', 'Held orders wait for a human. Approve releases fulfilment; reject cancels — and each can be done silently (no customer email) or, on reject, with a one-click silent blocklist of the email + IP so the fraudster is turned away next time and never tipped off. Alerts fan out to Slack, Discord, Microsoft Teams, Telegram and an HMAC-signed webhook; a per-channel auto-approve timer means nothing strands over a weekend. Full audit trail on every decision.'),
            ('Fulfilment hold hook', 'One-line host integration: ask pendingOrderIds() before releasing licence keys or shipping. Approval is the gate, not an afterthought.'),
            ('Daily threat feeds + one-click presets', 'FireHOL Level 1, Spamhaus DROP (CIDR ranges matched properly), Tor exit nodes and ~3,500 disposable-email domains synced nightly — plus seven curated add-with-one-click presets (IPsum L3+, blocklist.de, FireHOL L2/L3, Emerging Threats compromised, CINS Army, StopForumSpam toxic domains). No URL hunting.'),
            ('Email canonicalisation', 'fraud+1@gmail.com, fraud+2@gmail.com and f.r.a.u.d@gmail.com all count as ONE identity for velocity — the plus-addressing trick stops working.'),
            ('Trust works both ways', 'Returning customers earn NEGATIVE points — a real repeat buyer rarely trips a hold. Allowlisted identities (test accounts, key B2B customers, office IPs) skip every check entirely.'),
            ('Customer messages in your voice', 'Every gating outcome — held, approved, rejected — is a per-channel editable template with variables, live preview and thoughtful defaults: a held order reads as \'a quick security check\' with a stated turnaround, never an accusation, and rejections carry a refund timeline plus a human-appeal path. Each shows a default / customised badge; reset any selection or all of them in one click. You choose when — and whether — customers are told: never, block-level only, or always.'),
            ('"What-if" simulator', 'Run a hypothetical order (email, IP, value, country, billing / shipping postcodes, card AVS results) against live data and see the exact signal-by-signal score breakdown — without logging or holding anything.'),
            ('Multi-tab admin dashboard', 'Overview KPIs + daily chart, Rules, Review queue with count badge, Lists, Simulate, customer Lookup dossier (orders, spend, failed payments, case history, one-click allow/block), filterable Activity log with CSV export, Settings. WCAG AA in light and dark themes.'),
        ],
        'endpoints': [
            ('POST', '/fraud-prevention/check',            'Public: storefront pre-check (rate limited, minimal shape)'),
            ('GET',  '/fraud-prevention/config',           'Admin: per-channel config'),
            ('POST', '/fraud-prevention/config',           'Admin: save config'),
            ('GET',  '/fraud-prevention/stats',            'Admin: KPIs + daily series + top IPs'),
            ('GET',  '/fraud-prevention/cases',            'Admin: review queue'),
            ('POST', '/fraud-prevention/cases/:id/approve','Admin: release + notify customer'),
            ('POST', '/fraud-prevention/cases/:id/reject', 'Admin: cancel + notify customer'),
            ('POST', '/fraud-prevention/simulate',         'Admin: dry-run with full signal breakdown'),
            ('GET',  '/fraud-prevention/log',              'Admin: filterable audit log'),
            ('POST', '/fraud-prevention/lists/sync',       'Admin: threat-feed sync (licensed)'),
            ('GET',  '/fraud-prevention/order-assessment/:orderId', 'Admin: score + signals for the order-page panel'),
            ('GET',  '/fraud-prevention/feeds/presets',    'Admin: curated threat-feed presets'),
        ],
    },
    {
        'slug': 'business-credit',
        'pkg': '@huloglobal/vendure-plugin-business-credit',
        # Same tier as Quotations — must match the currency_options on the
        # Stripe price objects (created 2026-09-16).
        'pricing': {
            'GBP': {'monthly': '£14.95', 'lifetime': '£299', 'symbol': '£', 'label': 'GBP — British pound'},
            'USD': {'monthly': '$19.95', 'lifetime': '$399', 'symbol': '$', 'label': 'USD — US dollar'},
            'EUR': {'monthly': '€17.95', 'lifetime': '€359', 'symbol': '€', 'label': 'EUR — Euro'},
            'AUD': {'monthly': 'A$29.95', 'lifetime': 'A$599', 'symbol': 'A$', 'label': 'AUD — Australian dollar'},
            'CAD': {'monthly': 'C$26.95', 'lifetime': 'C$539', 'symbol': 'C$', 'label': 'CAD — Canadian dollar'},
        },
        'class': 'BusinessCreditPlugin',
        'version': '0.1.0',
        'title': 'Business Credit',
        'tagline': 'The credit-customer platform for Vendure B2B: applications, invitations and auto-approval, per-customer limits with an audit trail, multi-user company accounts, Pay on Account with net-terms invoices, prepaid funds, settlements by any method with Stripe pay links, payment plans, statements, dunning and a reward-points programme — in one admin dashboard and one storefront API.',
        'description': (
            'Vendure has no concept of a credit account. Business buyers expect one: '
            'apply for terms, get a limit, order without a card, receive an invoice '
            'due in 30 days, pay by bank transfer or card when the statement arrives. '
            'Business Credit adds all of it server-side. Customers apply from the '
            'storefront; you approve with a limit and net terms. A `business-credit` '
            'payment handler and eligibility checker show Pay on Account only to '
            'customers with an active account and enough available credit, and '
            'issue a numbered invoice with a due date the moment the order is placed. '
            'Every settlement — bank transfer, card through a Stripe pay link, direct '
            'debit, cheque, cash, credit note or write-off — is allocated oldest-first '
            'across open invoices, with overpayments held as account credit. Limits '
            'can be raised permanently or temporarily with an expiry, every change '
            'logged with who and why. A daily run marks invoices overdue, sends '
            'reminders on a schedule you set, applies late fees if you want them, '
            'suspends accounts that go too far past due, and emails monthly '
            'statements with an aging summary. Customers see their limit, available '
            'credit, invoices and statements through a small REST API you can drop '
            'into any storefront. Customers can also pay money in ahead of time: '
            'prepaid funds are held on the account and settle new orders the '
            'moment they are placed. Companies can add colleagues to one account '
            'with buyer or viewer roles, you can invite a business straight to '
            'an approved account by email, applications that meet your rules are '
            'approved automatically, every account gets a review date, an '
            'overdue invoice can be put on an instalment plan, and an optional '
            'reward-points programme earns points on every paid order and lets '
            'customers spend them at checkout.'
        ),
        'features': [
            ('Credit applications and approvals', 'A storefront application form (company, registration and VAT numbers, requested limit and terms, trade references) lands in an admin queue. Approve with a limit and net terms, or reject with a note; the customer is emailed either way and the account is created on approval.'),
            ('Limits with an audit trail', 'Permanent or temporary limit changes (a temporary increase expires on a date you set), each recorded with the old value, new value, reason and administrator. Available credit is derived live: effective limit minus open invoices plus any credit balance.'),
            ('Pay on Account at checkout', 'The `business-credit` payment handler settles the order and issues a numbered invoice with a due date; the eligibility checker hides the method from customers without an active account, enough available credit, or with an overdue hold. Purchase-order numbers can be required.'),
            ('Settlements by any method', 'Record bank transfers, direct debits, cheques, cash, credit notes and write-offs, or send a Stripe pay link for card payment; the signed webhook records the settlement. Allocation is oldest-first or explicit per invoice; overpayment becomes account credit and is applied to the next invoices automatically.'),
            ('Statements with aging', 'Per-account statements for any period: opening balance, every charge and payment, closing balance, and aging buckets (current, 1–30, 31–60, 61–90, 90+). HTML for the admin and the customer, emailed monthly on the statement day.'),
            ('Reminders, late fees, auto-suspend', 'A daily run sends reminders before, on and after the due date on a schedule you set per channel, applies a monthly late fee pro rata if configured, and suspends accounts that go more than N days overdue — reactivate with one click once they pay.'),
            ('Prepaid funds', 'Customers top up by card from the storefront or you record a deposit; the money is held on the account and settles invoices and new on-account orders automatically. Prepaid-only accounts work with a zero credit limit.'),
            ('Company accounts, invitations and auto-approval', 'One account, several logins: owners add colleagues as buyers or viewers. Invite a business by email straight to an approved limit. Applications that meet your rules — company number, order history, spend — are approved on the spot. Every account carries a review date.'),
            ('Payment plans', 'Split an outstanding invoice into instalments with their own due dates; reminders and overdue logic follow the plan, late fees pause, and customers can request a plan from their account.'),
            ('Reward points', 'An optional loyalty programme per channel: points per pound with tiers and multipliers, redeemed at checkout as a discount, with expiry, adjustments, statements and a customer points page.'),
            ('Customer-facing REST API', '`/business-credit/my/*` gives your storefront the account summary, funds, invoices, statements, pay links, team members, invitations, payment-plan requests and reward points for the signed-in customer, plus the application form. Works with Qwik, Next.js, Remix or plain fetch.'),
            ('Admin dashboard', 'Overview (exposure, overdue, credit held, due this week, aging), Accounts with a full detail panel, Applications queue, Invoices, Settlements, Settings with email preview and a run-now button, plus the Licence & billing card. Light and dark themes.'),
        ],
        'endpoints': [
            ('GET',  '/business-credit/dashboard',                 'Admin: exposure, overdue, aging, top accounts'),
            ('GET',  '/business-credit/accounts',                  'Admin: accounts with availability'),
            ('POST', '/business-credit/accounts/:id/limit',        'Admin: permanent or temporary limit change'),
            ('POST', '/business-credit/accounts/:id/status',       'Admin: suspend / reactivate / close'),
            ('GET',  '/business-credit/applications',              'Admin: credit application queue'),
            ('POST', '/business-credit/applications/:id/approve',  'Admin: approve with limit + terms'),
            ('GET',  '/business-credit/invoices',                  'Admin: invoices with balance + days overdue'),
            ('POST', '/business-credit/settlements',               'Admin: record a settlement (any method)'),
            ('POST', '/business-credit/invoices/:id/pay-link',     'Admin: Stripe pay link for an invoice'),
            ('POST', '/business-credit/stripe-webhook',            'Stripe: signed webhook for card settlements'),
            ('GET',  '/business-credit/accounts/:id/statement',    'Admin: statement for a period'),
            ('POST', '/business-credit/dunning/run',               'Admin: run reminders / fees / suspensions now'),
            ('GET',  '/business-credit/my/account',                'Shop: limit, available credit, terms, status'),
            ('POST', '/business-credit/my/apply',                  'Shop: apply for a credit account'),
            ('GET',  '/business-credit/my/invoices',               'Shop: my invoices'),
            ('POST', '/business-credit/my/invoices/pay-link',      'Shop: pay selected invoices by card'),
            ('POST', '/business-credit/my/top-up',                 'Shop: add prepaid funds by card'),
            ('POST', '/business-credit/my/members',                'Shop: add a colleague to the company account'),
            ('POST', '/business-credit/my/invitations/accept',     'Shop: accept an invitation to an approved account'),
            ('POST', '/business-credit/invitations',               'Admin: invite a business by email'),
            ('POST', '/business-credit/invoices/:id/plan',         'Admin: put an invoice on an instalment plan'),
            ('POST', '/business-credit/my/loyalty/redeem',         'Shop: spend reward points on the active order'),
            ('GET',  '/business-credit/loyalty/stats',             'Admin: points outstanding, earned and redeemed'),
        ],
    },
    {
        'slug': 'payments',
        'pkg': '@huloglobal/vendure-plugin-payments',
        # Email-tracking tier (repriced 2026-09-21) — must match the currency_options
        # on the Stripe price objects.
        'pricing': {
            'GBP': {'monthly': '£6.95', 'lifetime': '£139', 'symbol': '£', 'label': 'GBP — British pound'},
            'USD': {'monthly': '$8.99', 'lifetime': '$179', 'symbol': '$', 'label': 'USD — US dollar'},
            'EUR': {'monthly': '€8.49', 'lifetime': '€169', 'symbol': '€', 'label': 'EUR — Euro'},
            'AUD': {'monthly': 'A$13.95', 'lifetime': 'A$279', 'symbol': 'A$', 'label': 'AUD — Australian dollar'},
            'CAD': {'monthly': 'C$12.49', 'lifetime': 'C$249', 'symbol': 'C$', 'label': 'CAD — Canadian dollar'},
        },
        'class': 'HuloPaymentsPlugin',
        'version': '0.1.0',
        'title': 'Payments',
        'tagline': 'One payments plugin for Vendure: eleven payment systems — Stripe, Adyen, PayPal, Mollie, Square, Braintree, GoCardless, Checkout.com, crypto, bank transfer and pay-later — behind a single contract, with a hosted checkout page, wallets, 3-D Secure, captures, refunds, disputes, saved cards, subscriptions, pay-by-link, routing and one ledger.',
        'description': (
            'Vendure ships a Stripe plugin, a Mollie plugin and a Braintree plugin, each '
            'with its own shape, its own gaps and no view across them. Payments gives '
            'you four providers behind one contract: the storefront asks which to '
            'offer and gets a session; the provider\'s client renders cards, Apple Pay, '
            'Google Pay, iDEAL, Klarna and the rest; the plugin verifies the result '
            'with the provider before Vendure records the payment. Manual capture, '
            'partial captures and refunds work the same way on every provider. '
            'Webhooks are signature-checked and idempotent, disputes land in the '
            'ledger and alert ops, signed-in customers can save a card, any product '
            'variant can become a subscription (billed natively by Stripe, PayPal or '
            'Mollie, or by the plugin\'s scheduler from an Adyen token), and any '
            'unpaid order can be settled by a payment link. Provider order, fallback '
            'on decline, eligibility rules and surcharges are per channel. Everything '
            'lands in one ledger with a dashboard under Sales → Payments.'
        ),
        'features': [
            ('Hosted checkout page', 'One mutation and a redirect. The plugin serves a branded payment page that lists every enabled method, drives each provider\'s own client (Stripe Payment Element, Adyen Drop-in, PayPal buttons, Square, Braintree, hosted redirects, bank-transfer instructions) and sends the customer back to your storefront paid. No provider code in your storefront at all.'),
            ('Eleven payment systems, one contract', 'Stripe, Adyen, PayPal, Mollie, Square, Braintree, GoCardless, Checkout.com, Coinbase Commerce (crypto), bank transfer and pay-later / invoice — all as Vendure payment method handlers with the same capture, refund, webhook, ledger and admin behaviour. Connect any of them from the Payments page: paste the keys, the plugin checks them, sets up the webhook and creates the method.'),
            ('Wallets and local methods included', 'Apple Pay, Google Pay, Link, iDEAL, Bancontact, Klarna, SEPA, PayPal, Venmo and Pay Later — whatever each provider enables shows up in its hosted element with 3-D Secure handled by the provider.'),
            ('Verified server-side', 'The storefront never decides a payment state. The plugin re-reads the intent, session or order from the provider and checks amount, currency and order code before addPaymentToOrder.'),
            ('Capture control', 'Automatic or manual capture per method, partial captures, cancels, full and partial refunds — all from the normal Vendure order and refund screens.'),
            ('Signed, idempotent webhooks', 'Stripe signatures, Adyen HMAC, PayPal verification, Square and Checkout.com HMAC, GoCardless and Coinbase signatures, Mollie fetch-back. Duplicate deliveries are ignored; payments, refunds and subscriptions are updated; a webhook log shows every delivery.'),
            ('Disputes', 'Chargebacks and reversals from any provider land in the ledger with their reason and alert ops by webhook or email.'),
            ('Saved cards', 'Stripe Customers and Adyen stored payment methods for signed-in customers, listed and removed through the shop API.'),
            ('Subscriptions', 'Set a billing interval on any product variant. The order charges the first period; Stripe, PayPal and Mollie bill natively, Adyen renewals are charged by the plugin from the stored card. Dunning, MRR, customer self-service cancel, admin pause / resume / cancel.'),
            ('Pay by link', 'One click creates a provider-hosted payment link for any unpaid order — draft orders, accepted quotes, phone orders — and the webhook settles it.'),
            ('Routing, rules and surcharges', 'Provider order per channel with fallback on decline, an eligibility checker (amount band, currencies, countries, customer groups, signed-in only) for any payment method, and optional per-provider surcharges.'),
            ('One ledger, one dashboard', 'Authorisations, captures, refunds, disputes, failures, renewals and pay-links by provider and day, success rate, subscriptions and settings under Sales → Payments. Light and dark themes.'),
            ('No SDKs, PostgreSQL ready', 'Each provider is a handful of REST calls on the platform fetch; tables are created on boot on MySQL, MariaDB and PostgreSQL.'),
        ],
        'endpoints': [
            ('GET',  '/hulo-payments/pay/:token',        'Public: the hosted checkout page for one order'),
            ('POST', '/hulo-payments/webhook/:provider', 'Provider webhooks (stripe, adyen, paypal, mollie, square, gocardless, checkout-com, coinbase)'),
            ('GET',  '/hulo-payments/dashboard',         'Admin: KPIs by provider and day, subscriptions'),
            ('GET',  '/hulo-payments/transactions',      'Admin: the ledger, filterable'),
            ('GET',  '/hulo-payments/providers',         'Admin: configured methods, capabilities, webhook URLs'),
            ('GET',  '/hulo-payments/subscriptions',     'Admin: subscriptions (cancel / pause / resume actions)'),
            ('POST', '/hulo-payments/pay-link',          'Admin: payment link for an unpaid order (licensed)'),
            ('GET',  '/hulo-payments/settings',          'Admin: routing, surcharges, ops per channel'),
            ('GQL',  'huloHostedCheckout',               'Shop: URL of the hosted checkout page for the active order'),
            ('GQL',  'huloPaymentProviders',             'Shop: providers to offer for the active order'),
            ('GQL',  'huloCreatePaymentSession',         'Shop: client secret / session / checkout URL'),
            ('GQL',  'huloMySubscriptions',              'Shop: the customer\'s subscriptions (+ cancel)'),
        ],
    },
    {
        'slug': 'checkout-guard',
        'pkg': '@huloglobal/vendure-plugin-checkout-guard',
        # Same tier as Fraud Prevention — must match the currency_options on
        # the Stripe price objects (created 2026-09-11).
        'pricing': {
            'GBP': {'monthly': '£12.95', 'lifetime': '£259', 'symbol': '£', 'label': 'GBP — British pound'},
            'USD': {'monthly': '$16.95', 'lifetime': '$339', 'symbol': '$', 'label': 'USD — US dollar'},
            'EUR': {'monthly': '€15.95', 'lifetime': '€319', 'symbol': '€', 'label': 'EUR — Euro'},
            'AUD': {'monthly': 'A$25.95', 'lifetime': 'A$519', 'symbol': 'A$', 'label': 'AUD — Australian dollar'},
            'CAD': {'monthly': 'C$23.95', 'lifetime': 'C$479', 'symbol': 'C$', 'label': 'CAD — Canadian dollar'},
        },
        'class': 'CheckoutGuardPlugin',
        'version': '0.1.0',
        'title': 'Checkout Guard',
        'tagline': 'The safety layer around Vendure checkout and payments: Stripe manual-capture holds that actually place the order, bank transfer with auto-expiry, failed-payment and orphaned-charge visibility with nightly Stripe reconciliation, session-bound order lookup, checkout rate limits and a funnel — in one admin dashboard.',
        'description': (
            'Vendure\'s Stripe integration settles a payment when the intent succeeds — '
            'and nothing else. Put a manual-capture hold on a large order and the '
            'customer sees a confirmation page while the order never places and the '
            'authorisation silently expires. Enable bank transfer and there is no '
            'expiry, no reminder, no reconciliation. A card declines and no one '
            'ever knows. Checkout Guard closes those gaps server-side: an Authorized '
            'payment for every hold with capture, cancel and a safety capture before '
            'Stripe\'s seven-day window closes; a bank-transfer method that carries '
            'the account details to the storefront, expires unpaid orders and tells '
            'you when money is due; a payment-event log that records webhook '
            'failures, storefront declines, orphaned charges and amount drift, with '
            'a nightly Stripe reconciliation; an order-lookup strategy bound to the '
            'session that placed the order; a trusted client-IP contract for your '
            'server-side proxy; rate limits on the checkout mutations that get '
            'brute-forced; and funnel events so you can finally see where a checkout '
            'is lost.'
        ),
        'features': [
            ('Manual-capture holds that place the order', 'A `stripe-hold` payment handler plus a signed webhook for `payment_intent.amount_capturable_updated`: the order becomes PaymentAuthorized the moment the hold is placed. Capture or cancel from the dashboard or the Vendure order page; a safety capture runs before the authorisation expires; alerts fan out to your ops channels.'),
            ('Bank transfer done properly', 'Account details travel in the payment\'s public metadata so the storefront and confirmation page render them without hard-coding; an eligibility checker (min/max, guests, customer groups); unpaid orders expire automatically after N days with a reminder event before that; a "received" button settles the order and releases fulfilment.'),
            ('Failed payments you can see', 'Webhook declines, storefront-reported declines, orphaned charges and settled amounts that differ from the order total are written to a payment-event log with the IP — so fraud tooling can count them and you can spot a broken checkout before customers email you.'),
            ('Nightly Stripe reconciliation', 'Every succeeded or held PaymentIntent from the last days is matched to a Vendure payment; anything unmatched is flagged and alerted, per channel, with the Stripe key each channel already has.'),
            ('Session-bound order lookup', 'Vendure lets anyone with an order code read a fresh order for two hours. Checkout Guard binds anonymous access to the session that placed it — the confirmation page still works, strangers with a code do not.'),
            ('Trusted client IP', 'A shared-secret header contract for server-side proxies (Qwik server$, Next.js route handlers) so the order IP that feeds fraud scoring cannot be spoofed by a browser.'),
            ('Checkout rate limits', 'Token-bucket limits on applyCouponCode, addPaymentToOrder, createStripePaymentIntent and transitionOrderToState, keyed by client IP, returning a clean 429 — stops coupon brute force and intent spam without touching nginx.'),
            ('Checkout funnel', 'Step, attempt, failure and coupon-rejection events from the storefront, summarised per step with drop-off percentages, so single-URL checkouts stop being invisible to analytics.'),
            ('Ops alerts', 'Slack, Discord, Microsoft Teams, Telegram, a signed webhook and email — every hold, expiry, orphan and drift can ping the channel your team actually reads.'),
            ('Admin dashboard', 'Overview KPIs, Holds, Bank transfers, Payment events, Funnel and Settings tabs, plus the Licence & billing card. Light and dark themes.'),
        ],
        'endpoints': [
            ('POST', '/checkout-guard/stripe-webhook',      'Stripe: signed webhook for holds + failures'),
            ('GET',  '/checkout-guard/holds',               'Admin: Authorized Stripe holds'),
            ('POST', '/checkout-guard/holds/:id/capture',   'Admin: capture a hold (settles the payment)'),
            ('POST', '/checkout-guard/holds/:id/cancel',    'Admin: release a hold'),
            ('GET',  '/checkout-guard/bank-transfers',      'Admin: bank transfers awaiting / expired / settled'),
            ('POST', '/checkout-guard/bank-transfers/:id/received', 'Admin: mark a transfer received'),
            ('POST', '/checkout-guard/client-decline',      'Public: storefront-reported card decline (rate limited)'),
            ('POST', '/checkout-guard/funnel',              'Public: checkout funnel event (rate limited)'),
            ('GET',  '/checkout-guard/events',              'Admin: payment-event log'),
            ('GET',  '/checkout-guard/summary',             'Admin: dashboard KPIs'),
            ('GET',  '/checkout-guard/funnel/summary',      'Admin: per-step funnel with drop-off'),
        ],
    },
    {
        'slug': 'review-requests',
        'pkg': '@huloglobal/vendure-plugin-review-requests',
        'class': 'ReviewRequestPlugin',
        'version': '0.1.0',
        # Review Requests is priced below the standard plugin rate and sells in
        # Real per-currency prices — must match the currency_options on the
        # Stripe price objects.
        'pricing': {
            'GBP': {'monthly': '£2.95',  'lifetime': '£59',   'symbol': '£',  'label': 'GBP — British pound'},
            'USD': {'monthly': '$3.99',  'lifetime': '$79',   'symbol': '$',  'label': 'USD — US dollar'},
            'EUR': {'monthly': '€3.49',  'lifetime': '€69',   'symbol': '€',  'label': 'EUR — Euro'},
            'AUD': {'monthly': 'A$5.95', 'lifetime': 'A$115', 'symbol': 'A$', 'label': 'AUD — Australian dollar'},
            'CAD': {'monthly': 'C$5.49', 'lifetime': 'C$105', 'symbol': 'C$', 'label': 'CAD — Canadian dollar'},
        },
        'title': 'Review Requests',
        'tagline': 'Automated post-purchase Trustpilot review invitations, timed off order dates — free Trustpilot integration, customer exclusions, cooldown, editable emails.',
        'description': (
            'Turn happy customers into reviews on autopilot. An hourly worker finds '
            'orders that reached Delivered / Payment settled / Shipped a set number of '
            'days ago and emails the customer a branded, Trustpilot-style invitation '
            'linking to your FREE Trustpilot review page — no paid Automatic Feedback '
            'Service. Optionally pull your live TrustScore from the free Trustpilot API '
            'to show as social proof. Exclude any customer or domain, respect a '
            'per-customer cooldown, dedupe per order, and let anyone unsubscribe in one '
            'click. Fully editable email with live preview and test-send, per channel.'
        ),
        'features': [
            ('Timed off order dates', 'Send N days after an order reaches Delivered, Payment settled or Shipped — whichever milestone you choose, per channel.'),
            ('Free Trustpilot, done right', 'The review button links to trustpilot.com/evaluate/your-domain — organic Service Reviews, completely free. No paid AFS, no per-invite cost.'),
            ('Live rating as social proof', 'Show your current star rating + review count right in the email ("Rated 4.8 by 1,240 customers") — pulled live from Trustpilot or Google. Optional; the email works without it.'),
            ('Trustpilot, Google or anywhere', 'One-click platform picker builds the review link for Trustpilot, Google reviews, Reviews.io — or paste any custom URL. Trustpilot and Google also show a live star rating in the email.'),
            ('Product reviews too', 'Ask for a store review, product reviews, or both. In product mode the email lists the actual items the customer bought, each with its own "Review this" button linking to your storefront\'s product-review page.'),
            ('Exclude customers', 'Never invite specific emails or whole domains — wholesale accounts, staff, VIPs. One-click unsubscribe in every email auto-excludes.'),
            ('No over-asking, no double-sends', 'Deduped per order with a concurrency guard on the sender, a per-customer cooldown (default 120 days), and a minimum order value — a customer can\'t be invited twice for one order, and every skip is audit-logged once with its reason.'),
            ('Your voice', 'Fully editable subject + HTML body per channel with {{firstName}}, {{orderCode}}, {{businessName}}, {{reviewUrl}} and a live rating block, plus preview and test-send.'),
            ('Multi-tab admin', 'Overview (sent / eligible now / opt-outs / failed + your live rating), Settings, Email, Exclusions and an Activity log. WCAG AA in light + dark.'),
            ('Send from the order page', 'Every order\'s detail page shows its invitation status — sent, scheduled, excluded or opted out — with a manual Send now, a confirmed Resend, and a send-anyway override for staff judgement calls.'),
            ('GDPR-friendly', 'Signed one-click unsubscribe links, an opt-out list, and full send-log auditing.'),
        ],
        'endpoints': [
            ('GET',  '/review-requests/optout',          'Public: signed one-click unsubscribe page'),
            ('GET',  '/review-requests/config',          'Admin: per-channel config'),
            ('POST', '/review-requests/config',          'Admin: save config'),
            ('GET',  '/review-requests/stats',           'Admin: KPIs + eligibility preview'),
            ('GET',  '/review-requests/log',             'Admin: send log'),
            ('POST', '/review-requests/run',             'Admin: send all due now (licensed)'),
            ('POST', '/review-requests/trustpilot/check','Admin: check live rating + review link'),
            ('POST', '/review-requests/template/preview','Admin: render the email with sample data'),
            ('POST', '/review-requests/test-send',       'Admin: send a test to yourself'),
            ('POST', '/review-requests/exclusions',      'Admin: exclude an email / domain'),
            ('GET',  '/review-requests/order-status/:orderId', 'Admin: invitation state for the order-page panel'),
            ('POST', '/review-requests/send-order/:orderId',   'Admin: manual send / resend from the order page'),
        ],
    },
]


HEADER = '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="color-scheme" content="light">
<meta name="theme-color" content="#0f1419">
<title>{title}</title>
<meta name="description" content="{description}">
<link rel="canonical" href="{canonical}">
<link rel="icon" type="image/svg+xml" href="/vendure-plugins/logos/hulo-global.svg?v=4">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Hulo Global">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{description}">
<meta property="og:url" content="{canonical}">
<meta property="og:image" content="https://huloglobal.com/og-image.png">
<meta property="og:locale" content="en_GB">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{title}">
<meta name="twitter:description" content="{description}">
<meta name="twitter:image" content="https://huloglobal.com/og-image.png">
<meta name="robots" content="index, follow">
<link rel="stylesheet" href="''' + ASTRO_CSS + '''">
<style>
/* Global focus indicator — accessibility */
.vp-section a:focus-visible, .vp-card a:focus-visible, .vp-hero a:focus-visible, .vp-faq summary:focus-visible, button:focus-visible {{
  outline: 2px solid var(--color-accent-500, #f59e0b);
  outline-offset: 3px;
  border-radius: 4px;
}}
/* Respect reduced motion preference */
@media (prefers-reduced-motion: reduce) {{
  *, *::before, *::after {{ animation-duration: 0.01ms !important; transition-duration: 0.01ms !important; }}
}}
.vp-proof-item {{ display:inline-flex; align-items:center; gap:.4rem; }} .vp-proof-item::before {{ content:""; width:6px; height:6px; border-radius:999px; background:#22c55e; display:inline-block; }} a.vp-proof-item {{ text-decoration:underline; text-underline-offset:2px; }}
.vp-tier-list {{ list-style:none; padding:0; margin:0; }} .vp-tier-list li {{ position:relative; padding-left:1.4rem; margin:.45rem 0; font-size:.95rem; color:#334155; line-height:1.5; }} .vp-tier-list li::before {{ content:"✓"; position:absolute; left:0; color:#16a34a; font-weight:700; }}
.vp-hero {{ position: relative; background: linear-gradient(to bottom, var(--color-ink-50, #f8fafc) 0%, #fff 100%); }}
.vp-hero::before {{ content: ""; position: absolute; inset: 0; pointer-events: none; opacity: .35; background-image: radial-gradient(ellipse 70% 50% at 50% 0%, var(--color-accent-100, #fde68a), transparent 60%); }}
/* Corporate brand mark — sits at the top of every hero. Small,
   text-anchored to the logotype so it reads as a clickable badge. */
.vp-plugin-logo {{ display: block; width: 56px; height: 56px; border-radius: 14px; margin-bottom: 22px; box-shadow: 0 1px 3px rgba(15,23,42,.10), 0 2px 8px rgba(15,23,42,.06); }}
.vp-pill {{ display: inline-flex; align-items: center; gap: 8px; padding: 8px 16px; border-radius: 999px; border: 1px solid var(--color-ink-200, #e2e8f0); background: #fff; font-size: 12px; font-weight: 600; text-transform: uppercase; letter-spacing: .05em; color: var(--color-ink-600, #475569); }}
.vp-pill::before {{ content: ""; width: 6px; height: 6px; border-radius: 999px; background: var(--color-accent-500, #f59e0b); }}
.vp-section {{ padding: 88px 0; }}
@media (max-width: 768px) {{ .vp-section {{ padding: 56px 0; }} }}
.vp-grid-2 {{ display: grid; grid-template-columns: 1fr; gap: 48px; }}
@media (min-width: 1024px) {{ .vp-grid-2 {{ grid-template-columns: minmax(0, 1fr) 380px; gap: 64px; align-items: start; }} }}
.vp-pricing-aside {{ position: sticky; top: 104px; }}
@media (max-width: 1023px) {{ .vp-pricing-aside {{ position: static; top: auto; margin-top: 8px; }} }}
.vp-price-card {{ border: 1px solid var(--color-ink-100, #e2e8f0); border-radius: 18px; padding: 28px; background: #fff; box-shadow: 0 1px 3px rgba(15,23,42,.05), 0 8px 24px rgba(15,23,42,.04); }}
.vp-price-card + .vp-price-card {{ margin-top: 18px; }}
.vp-price-card.featured {{ border: 2px solid var(--color-accent-500, #f59e0b); padding: 27px; }}
@media (max-width: 767px) {{
    .vp-price-card {{ padding: 22px; }}
    .vp-price-card.featured {{ padding: 21px; }}
    .vp-price-num {{ font-size: 36px !important; }}
    /* Pricing cards side-by-side on small screens so both are above the fold */
    .vp-pricing-aside {{ display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }}
    .vp-pricing-aside > .vp-price-card + .vp-price-card {{ margin-top: 0; }}
    .vp-pricing-aside > p {{ grid-column: 1 / -1; }}
}}
@media (max-width: 480px) {{
    .vp-pricing-aside {{ grid-template-columns: 1fr; }}
    .vp-pricing-aside > .vp-price-card + .vp-price-card {{ margin-top: 16px; }}
}}
.vp-price-num {{ font-size: 40px; font-weight: 800; color: var(--color-ink-900, #0f172a); line-height: 1; letter-spacing: -0.025em; }}
.vp-price-num small {{ font-size: 15px; font-weight: 500; color: var(--color-ink-500, #64748b); margin-left: 6px; }}
.vp-trial-num {{ color: var(--color-accent-600, #d97706); }}
.vp-email-input {{
    width: 100%; box-sizing: border-box;
    padding: 12px 14px; min-height: 44px;
    border: 1px solid var(--color-ink-200, #e2e8f0);
    border-radius: 8px;
    font-size: 16px;
    background: #fff;
    color: var(--color-ink-900);
}}
.vp-email-input:focus-visible {{ outline: 2px solid var(--color-accent-500, #f59e0b); outline-offset: 2px; border-color: transparent; }}
.vp-tiny-note {{ font-size: 12px; color: var(--color-ink-500); margin-top: 10px; text-align: center; }}
.vp-feat {{ display: grid; grid-template-columns: 28px 1fr; gap: 16px; padding: 18px 0; border-top: 1px solid var(--color-ink-100, #e2e8f0); }}
.vp-feat:first-of-type {{ border-top: 0; padding-top: 4px; }}
.vp-feat-tick {{ width: 28px; height: 28px; border-radius: 999px; background: var(--color-accent-50, #fffbeb); display: grid; place-items: center; color: var(--color-accent-600, #d97706); }}
.vp-feat h3 {{ font-size: 16px; font-weight: 600; color: var(--color-ink-900); margin: 2px 0 0; line-height: 1.4; }}
.vp-feat p {{ font-size: 14px; color: var(--color-ink-600, #475569); margin: 8px 0 0; line-height: 1.6; }}
.vp-step {{ counter-increment: step; margin-top: 48px; }}
.vp-step:first-of-type {{ margin-top: 56px; }}
.vp-step h3::before {{ content: counter(step); display: inline-block; min-width: 32px; height: 32px; padding: 0 8px; margin-right: 14px; background: var(--color-ink-900); color: #fff; border-radius: 999px; font-size: 15px; font-weight: 700; text-align: center; line-height: 32px; vertical-align: middle; }}
.vp-step h3 {{ font-size: 22px !important; line-height: 1.4; }}
.vp-step > p {{ margin: 12px 0 14px 46px; }}
.vp-code {{ background: #0f172a; color: #f1f5f9; padding: 22px 24px; border-radius: 12px; font-size: 13.5px; line-height: 1.75; font-family: ui-monospace, SFMono-Regular, Menlo, monospace; overflow-x: auto; margin-left: 46px; }}
.vp-code .vp-comment {{ color: #94a3b8; }}
.vp-code .vp-key {{ color: #fbbf24; }}
.vp-code .vp-str {{ color: #86efac; }}
.vp-faq summary {{ font-weight: 600; padding: 22px 0; cursor: pointer; list-style: none; display: flex; justify-content: space-between; align-items: center; font-size: 16px; }}
.vp-faq summary::after {{ content: "+"; font-size: 26px; color: var(--color-ink-400, #94a3b8); transition: transform .15s; }}
.vp-faq details[open] summary::after {{ content: "−"; }}
.vp-faq details {{ border-bottom: 1px solid var(--color-ink-100); }}
.vp-faq details:first-of-type {{ border-top: 1px solid var(--color-ink-100); }}
.vp-faq details p {{ padding: 4px 0 22px; color: var(--color-ink-600); line-height: 1.7; font-size: 15px; }}
.vp-endpoint {{ display: grid; grid-template-columns: 90px 1.2fr 2fr; gap: 16px; padding: 14px 16px; border-top: 1px solid var(--color-ink-100); font-size: 14px; align-items: center; }}
.vp-endpoint:first-of-type {{ border-top: 0; }}
.vp-endpoint .vp-method {{ font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-weight: 700; padding: 4px 10px; border-radius: 5px; text-align: center; font-size: 11px; }}
.vp-method.GET {{ background: #dbeafe; color: #1e3a8a; }}
.vp-method.POST {{ background: #dcfce7; color: #14532d; }}
.vp-method.PUT {{ background: #fef3c7; color: #78350f; }}
.vp-method.DELETE {{ background: #fee2e2; color: #7f1d1d; }}
.vp-endpoint code {{ font-family: ui-monospace, SFMono-Regular, Menlo, monospace; color: var(--color-ink-900); font-size: 13px; }}
.vp-endpoint .vp-desc {{ color: var(--color-ink-600); font-size: 13px; }}
.vp-cards-grid {{ display: grid; grid-template-columns: 1fr; gap: 28px; }}
@media (min-width: 768px) {{ .vp-cards-grid {{ grid-template-columns: repeat(3, 1fr); }} }}
.vp-card {{ display: flex; flex-direction: column; border: 1px solid var(--color-ink-100, #e2e8f0); border-radius: 18px; padding: 32px; background: #fff; box-shadow: 0 1px 3px rgba(15,23,42,.05); transition: transform .15s, box-shadow .15s; }}
.vp-card:hover {{ transform: translateY(-2px); box-shadow: 0 8px 24px rgba(15,23,42,.08); }}
.vp-card h3 {{ font-size: 24px; font-weight: 700; color: var(--color-ink-900); line-height: 1.2; margin: 0; }}
.vp-card .vp-card-tagline {{ font-size: 15px; color: var(--color-ink-600); line-height: 1.65; margin: 14px 0 0; }}
.vp-card ul {{ list-style: none; padding: 0; margin: 24px 0 0; }}
.vp-card li {{ display: flex; align-items: flex-start; gap: 10px; padding: 8px 0; font-size: 14px; color: var(--color-ink-700); line-height: 1.5; }}
.vp-card .vp-card-actions {{ margin-top: 28px; padding-top: 24px; border-top: 1px solid var(--color-ink-100); display: flex; align-items: center; gap: 12px; }}

/* Currency picker — proper tap target + visible focus */
.sr-only {{ position: absolute; width: 1px; height: 1px; padding: 0; margin: -1px; overflow: hidden; clip: rect(0,0,0,0); white-space: nowrap; border: 0; }}
.ccy-picker-wrap {{ display: inline-flex; align-items: center; gap: 8px; }}
.ccy-label {{ font-size: 13px; font-weight: 500; color: var(--color-ink-600, #475569); }}
.ccy-select {{
    appearance: none; -webkit-appearance: none;
    padding: 10px 32px 10px 14px;
    min-height: 44px;
    border: 1px solid var(--color-ink-200, #e2e8f0);
    border-radius: 8px;
    background: #fff;
    background-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 24 24' fill='none' stroke='%23475569' stroke-width='2.5'><polyline points='6 9 12 15 18 9'/></svg>");
    background-repeat: no-repeat;
    background-position: right 10px center;
    background-size: 12px;
    font-size: 14px; font-weight: 500; color: var(--color-ink-700, #334155);
    cursor: pointer;
    line-height: 1.2;
}}
.ccy-select:focus-visible {{
    outline: 2px solid var(--color-accent-500, #f59e0b);
    outline-offset: 2px;
}}
.ccy-select:hover {{ border-color: var(--color-ink-300, #cbd5e1); }}
.ccy-select-mobile {{ font-size: 13px; padding: 8px 28px 8px 12px; min-height: 40px; }}

.mobile-controls {{ display: flex; align-items: center; gap: 12px; }}
.mobile-nav-link {{
    padding: 10px 14px; min-height: 44px;
    display: inline-flex; align-items: center;
    border-radius: 8px;
    background: var(--color-ink-50, #f8fafc);
    color: var(--color-ink-800, #1e293b);
    font-size: 14px; font-weight: 600; text-decoration: none;
    border: 1px solid var(--color-ink-200, #e2e8f0);
}}
.mobile-nav-link:focus-visible {{ outline: 2px solid var(--color-accent-500, #f59e0b); outline-offset: 2px; }}

/* Compatibility matrix */
.vp-compat-wrap {{ overflow-x: auto; }}
.vp-compat {{ border-collapse: collapse; }}
.vp-compat th, .vp-compat td {{ padding: 14px 18px; font-size: 14px; border-top: 1px solid var(--color-ink-100, #e2e8f0); }}
.vp-compat thead th {{ border-top: 0; font-weight: 600; color: var(--color-ink-500, #64748b); font-size: 12px; text-transform: uppercase; letter-spacing: .04em; white-space: nowrap; }}
.vp-compat tbody th {{ font-weight: 600; color: var(--color-ink-900, #0f172a); }}
.vp-compat tbody th a {{ color: inherit; text-decoration: none; }}
.vp-compat tbody th a:hover {{ color: var(--color-accent-600, #d97706); text-decoration: underline; }}
.vp-compat tbody tr:hover {{ background: var(--color-ink-50, #f8fafc); }}
.vp-compat td {{ color: var(--color-ink-700, #334155); }}
.vp-compat-ver {{ font-size: 13px; color: var(--color-ink-900, #0f172a); }}
.vp-compat-ok {{ display: inline-block; padding: 3px 10px; border-radius: 999px; background: #ecfdf5; color: #047857; font-size: 12px; font-weight: 600; white-space: nowrap; }}

/* Catalog comparison: table on desktop, stacked cards on mobile */
.vp-compare-table {{ display: block; }}
.vp-compare-cards {{ display: none; }}
@media (max-width: 767px) {{
    .vp-compare-table {{ display: none; }}
    .vp-compare-cards {{ display: grid; gap: 16px; }}
    .vp-compare-card {{
        background: #fff;
        border: 1px solid var(--color-ink-100, #e2e8f0);
        border-radius: 14px;
        padding: 20px;
        min-width: 0;
    }}
    .vp-cmp-row {{
        display: grid;
        grid-template-columns: 1fr auto;
        gap: 12px;
        align-items: start;
        padding: 10px 0;
        border-top: 1px solid var(--color-ink-100, #e2e8f0);
        min-width: 0;
    }}
    .vp-cmp-key {{
        font-size: 13px;
        color: var(--color-ink-600, #475569);
        word-wrap: break-word;
        overflow-wrap: anywhere;
        min-width: 0;
    }}
    .vp-cmp-val {{
        font-size: 13px;
        font-weight: 600;
        color: var(--color-ink-900);
        text-align: right;
        word-wrap: break-word;
        overflow-wrap: anywhere;
        max-width: 55%;
    }}
}}

/* Responsive table wrapper — momentum scroll on iOS, visible scrollbar */
.table-wrap {{ overflow-x: auto; -webkit-overflow-scrolling: touch; border-radius: 12px; }}
.table-wrap::-webkit-scrollbar {{ height: 8px; }}
.table-wrap::-webkit-scrollbar-thumb {{ background: var(--color-ink-300, #cbd5e1); border-radius: 4px; }}
</style>
</head>
<body>
<a href="#main" class="skip-link">Skip to content</a>
<header class="sticky top-0 z-40 border-b border-ink-100 bg-white/85 backdrop-blur supports-[backdrop-filter]:bg-white/70">
<div class="container-page flex items-center justify-between py-4">
<a href="/" class="flex items-center gap-2.5 group" aria-label="Hulo Global — home">
<span aria-hidden="true" class="grid size-9 place-items-center rounded-lg bg-ink-900 text-white font-bold tracking-tight text-sm group-hover:bg-ink-800 transition-colors">HG</span>
<span class="font-bold text-ink-900 tracking-tight text-lg">Hulo Global</span>
</a>
<nav aria-label="Primary" class="hidden md:flex md:items-center md:gap-6">
<ul class="flex items-center gap-6 text-sm font-medium text-ink-700">
<li><a href="/" class="hover:text-ink-900 transition-colors py-3 px-2 inline-block">Home</a></li>
<li><a href="/vendure-plugins/" class="hover:text-ink-900 transition-colors py-3 px-2 inline-block">Vendure plugins</a></li>
<li><a href="/vendure-plugins/roadmap/" class="hover:text-ink-900 transition-colors py-3 px-2 inline-block">Roadmap</a></li>
<li><a href="/#contact" class="hover:text-ink-900 transition-colors py-3 px-2 inline-block">Contact</a></li>
</ul>
''' + ccy_picker_html('ccy-picker') + '''
</nav>
<div class="mobile-controls md:hidden">
<a href="/vendure-plugins/" class="mobile-nav-link" aria-label="Vendure plugins">Plugins</a>
<a href="/vendure-plugins/roadmap/" class="mobile-nav-link" aria-label="Roadmap">Roadmap</a>
''' + ccy_picker_html('ccy-picker-mobile', mobile=True) + '''
</div>
<div id="ccy-live" class="sr-only" aria-live="polite" aria-atomic="true"></div>
</div>
</header>
<main id="main">
'''

CURRENCY_JS = '''
<script>
(function() {
  var PRICES = window.HULO_PRICES_OVERRIDE || ''' + __import__('json').dumps(display_price_table(CURRENCIES['GBP']['monthly'], CURRENCIES['GBP']['lifetime'])) + ''';
  var PURCHASABLE = ''' + str(PURCHASABLE_CURRENCIES).replace("'", '"') + ''';
  function pickInitial() {
    try {
      var url = new URLSearchParams(location.search).get('currency');
      if (url && PRICES[url.toUpperCase()]) return url.toUpperCase();
      var stored = localStorage.getItem('hulo-currency');
      if (stored && PRICES[stored]) return stored;
      var loc = (navigator.language || 'en-GB').toUpperCase();
      if (loc.indexOf('US') !== -1) return 'USD';
      if (loc.indexOf('AU') !== -1) return 'AUD';
      if (loc.indexOf('CA') !== -1) return 'CAD';
      if (/-(DE|FR|ES|IT|NL|IE|AT|BE|PT|FI|GR|LU)$/.test(loc)) return 'EUR';
    } catch (e) {}
    return 'GBP';
  }
  var live = document.getElementById('ccy-live');
  var initialised = false;
  function apply(ccy) {
    var p = PRICES[ccy] || PRICES.GBP;
    document.querySelectorAll('[data-monthly-price]').forEach(function(el) { el.textContent = p.monthly; });
    document.querySelectorAll('[data-lifetime-price]').forEach(function(el) { el.textContent = p.lifetime; });
    var chargeCcy = p.approx ? 'GBP' : ccy;
    document.querySelectorAll('[data-currency-input]').forEach(function(el) { el.value = chargeCcy; });
    document.querySelectorAll('[data-approx-note]').forEach(function(el) { el.style.display = p.approx ? '' : 'none'; });
    try { localStorage.setItem('hulo-currency', ccy); } catch (e) {}
    if (live && initialised) {
      live.textContent = 'Currency changed to ' + ccy + '. Monthly ' + p.monthly + ', lifetime ' + p.lifetime + '.';
    }
    initialised = true;
  }
  var initial = pickInitial();
  if (PURCHASABLE.indexOf(initial) === -1) initial = PURCHASABLE[0] || 'GBP';
  ['ccy-picker', 'ccy-picker-mobile'].forEach(function(id) {
    var el = document.getElementById(id);
    if (!el) return;
    el.value = initial;
    el.addEventListener('change', function() {
      apply(el.value);
      // keep both pickers in sync
      var other = document.getElementById(id === 'ccy-picker' ? 'ccy-picker-mobile' : 'ccy-picker');
      if (other) other.value = el.value;
    });
  });
  apply(initial);
})();
</script>
'''

VERSION_REFRESH_JS = '''
<script>
/*
 * Keep every [data-hulo-pkg] version chip in sync with what npm currently
 * publishes. The HTML is built with the last-known-good version baked in
 * (so JS-off users still see the right thing and search engines index a
 * concrete number). This runs on load and rewrites the chip if npm has
 * shipped a newer version since the last build.
 *
 * Strategy:
 *   1. Fetch /vendure-plugins/versions.json (regenerated on every build,
 *      served from our own CDN — no cross-origin, no rate-limit).
 *   2. If that fails (older build without the file), fall back to the
 *      public npm registry directly. CORS on the registry is permissive.
 *   3. Never throw. A stale chip is fine; a broken page is not.
 */
(function () {
  var chips = document.querySelectorAll('[data-hulo-pkg]');
  if (!chips.length) return;
  var wanted = {};
  chips.forEach(function (el) { wanted[el.getAttribute('data-hulo-pkg')] = true; });
  function apply(versions) {
    chips.forEach(function (el) {
      var pkg = el.getAttribute('data-hulo-pkg');
      var v = versions[pkg];
      if (!v) return;
      var prefix = el.getAttribute('data-hulo-version-prefix') || '';
      var next = prefix + v;
      if (el.textContent !== next) el.textContent = next;
    });
  }
  fetch('/vendure-plugins/versions.json', { cache: 'no-cache' })
    .then(function (r) { return r.ok ? r.json() : Promise.reject(r.status); })
    .then(apply)
    .catch(function () {
      // Fall back to the public registry — one request per package.
      Object.keys(wanted).forEach(function (pkg) {
        var url = 'https://registry.npmjs.org/' + encodeURIComponent(pkg).replace('%40', '@') + '/latest';
        fetch(url, { cache: 'no-cache' })
          .then(function (r) { return r.ok ? r.json() : null; })
          .then(function (j) {
            if (j && j.version) { var o = {}; o[pkg] = j.version; apply(o); }
          })
          .catch(function () { /* silent */ });
      });
    });
})();
</script>
'''

FOOTER = CURRENCY_JS + VERSION_REFRESH_JS + '''
</main>
<footer class="border-t border-ink-100 bg-ink-50 mt-20">
<div class="container-page py-10 grid gap-8 sm:grid-cols-3">
<div>
<p class="text-sm text-ink-700">Hulo Global Limited</p>
<p class="text-xs text-ink-600 mt-1">UK Companies House 17134928</p>
<p class="text-xs text-ink-600 mt-1">Unit A, 82 James Carter Road,<br>Mildenhall, IP28 7DE, UK</p>
</div>
<div>
<p class="text-xs uppercase tracking-wider text-ink-500 font-semibold mb-3">Vendure plugins</p>
<ul class="space-y-1.5 text-sm text-ink-700">
<li><a href="/vendure-plugins/" class="underline underline-offset-4 decoration-ink-300 hover:decoration-ink-800">All plugins</a></li>
<li><a href="/vendure-plugins/email-tracking/" class="underline underline-offset-4 decoration-ink-300 hover:decoration-ink-800">Email Tracking</a></li>
<li><a href="/vendure-plugins/geo-block/" class="underline underline-offset-4 decoration-ink-300 hover:decoration-ink-800">Geo Block</a></li>
<li><a href="/vendure-plugins/visitor-analytics/" class="underline underline-offset-4 decoration-ink-300 hover:decoration-ink-800">Visitor Analytics</a></li>
<li><a href="/vendure-plugins/fraud-prevention/" class="underline underline-offset-4 decoration-ink-300 hover:decoration-ink-800">Fraud Prevention</a></li>
<li><a href="/vendure-plugins/roadmap/" class="underline underline-offset-4 decoration-ink-300 hover:decoration-ink-800">Roadmap &amp; requests</a></li>
</ul>
</div>
<div>
<p class="text-xs uppercase tracking-wider text-ink-500 font-semibold mb-3">Customers</p>
<ul class="space-y-1.5 text-sm text-ink-700">
<li><a href="https://elite.charity/licence/forgot" class="underline underline-offset-4 decoration-ink-300 hover:decoration-ink-800">Lost your key?</a></li>
<li><a href="https://elite.charity/licence/privacy" class="underline underline-offset-4 decoration-ink-300 hover:decoration-ink-800">Your data &amp; privacy</a></li>
<li><a href="mailto:hello@huloglobal.com" class="underline underline-offset-4 decoration-ink-300 hover:decoration-ink-800">hello@huloglobal.com</a></li>
</ul>
</div>
</div>
</footer>
</body>
</html>
'''


def header(title, canonical, description):
    return HEADER.format(title=html.escape(title), canonical=canonical, description=html.escape(description))


TICK_SVG = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>'


def index_page():
    def card_meta(p):
        bits = []
        dl = npm_downloads_last_month(p['pkg'])
        ytd = npm_downloads_this_year(p['pkg'])
        if dl:
            bits.append(f'{dl:,} downloads/mo')
        if ytd:
            bits.append(f'{ytd:,} this year')
        if p['slug'] in VENDURE_DIRECTORY_LISTED:
            bits.append('<a href="https://docs.vendure.io/plugins" class="underline underline-offset-2">Vendure directory</a>')
        elif p['slug'] in VENDURE_DIRECTORY_SUBMITTED:
            bits.append('Vendure directory: submitted')
        return ('<p class="mt-3 text-xs text-ink-500">' + ' · '.join(bits) + '</p>') if bits else ''
    short_features = {
        'business-credit': [
            'Applications, invitations, auto-approval, company accounts',
            'Pay on Account with net-terms invoices + prepaid funds',
            'Settlements by any method, Stripe pay links, payment plans',
            'Statements, dunning, late fees + a reward-points programme',
        ],
        'payments': [
            'Eleven payment systems behind one contract',
            'Hosted checkout page — no provider code in your storefront',
            'Wallets, 3-D Secure, holds, refunds, disputes, subscriptions',
            'Routing, rules, surcharges + one ledger dashboard',
        ],
        'checkout-guard': [
            'Stripe manual-capture holds that place the order',
            'Bank transfer with auto-expiry + reminders',
            'Failed-payment log + nightly Stripe reconciliation',
            'Session-bound order lookup, rate limits, funnel',
        ],
        'quotations': [
            'Quote builder with live catalogue prices',
            'Signed accept/decline link with typed-name signature',
            'Auto-chasers, expiry reminders + auto-expiry',
            'Accepted quote → draft order at the exact quoted total',
        ],
        'email-tracking': [
            'Per-link tokenised open + click tracking',
            'Human / machine event classification (Gmail proxy, Safe Links, …)',
            'IP enrichment + provider webhooks (Postmark / SendGrid / Mailgun / SES)',
            'Order Activity History panel + PDF Evidence Report',
        ],
        'geo-block': [
            '37 region presets (EU, EEA, GCC, NATO, …)',
            'Soft-block (browse-only) mode',
            'IP allowlist with CIDR',
            '"What-if" simulator + stats panel',
        ],
        'visitor-analytics': [
            'Page views + funnel + exit pages',
            'Conversion goals with URL globs',
            'Bot detection + privacy-first defaults',
            'Live-now SSE widget',
        ],
        'fraud-prevention': [
            'Risk score on every order, server-side',
            'Card AVS postcode / address mismatch from the issuer',
            'Monitor / enforce modes + review queue',
            'Threat feeds: FireHOL, Spamhaus, Tor, disposable emails',
            'Fulfilment held until a human approves',
        ],
        'review-requests': [
            'Trustpilot invitations timed off order dates',
            'Free Trustpilot — no paid Feedback Service',
            'Live TrustScore in the email as social proof',
            'Exclusions, cooldown, one-click unsubscribe',
        ],
    }
    cards = []
    for p in PLUGINS:
        feats_html = '\n'.join(
            f'<li><span class="text-accent-600 shrink-0" style="margin-top:2px">{TICK_SVG}</span><span>{html.escape(f)}</span></li>'
            for f in short_features[p['slug']]
        )
        cards.append(f'''
<article class="vp-card">
  <h3>{html.escape(p['title'])}</h3>
  <p class="vp-card-tagline">{html.escape(p['tagline'])}</p>
  <ul>{feats_html}</ul>
  <div class="vp-card-actions">
    {card_meta(p)}
    <a href="/vendure-plugins/{p['slug']}/" class="btn btn-primary text-sm" style="padding:.6rem 1.2rem">Learn more →</a>
    <a href="/vendure-plugins/{p['slug']}/changelog/" class="ml-auto" title="Changelog"><!--email_off--><span class="text-xs text-ink-500 font-mono hover:underline" data-hulo-pkg="{html.escape(p['pkg'])}" data-hulo-version-prefix="v">v{p['version']}</span><!--/email_off--></a>
  </div>
</article>''')

    comparison_rows = [
        ['Drop-in install (one yarn add)', 'yes', 'yes', 'yes', 'yes', 'yes', 'yes', 'yes', 'yes'],
        ['Channel-aware', 'yes', 'yes', 'yes', 'yes', 'yes', 'yes', 'yes', 'yes'],
        ['Admin UI included', 'yes', 'yes', 'yes', 'yes', 'yes', 'yes', 'yes', 'yes'],
        ['MySQL / MariaDB / PostgreSQL', 'yes', 'yes', 'yes', 'yes', 'yes', 'yes', 'yes', 'yes'],
        ['Licence activation in the admin', 'yes', 'yes', 'yes', 'yes', 'yes', 'yes', 'yes', 'yes'],
        ['One-click in-app updates', 'yes', 'yes', 'yes', 'yes', 'yes', 'yes', 'yes', 'yes'],
        ['Database tables', '4', '2', '1', '2', '8', '5', '3', '14'],
        ['Privacy controls', 'Signed links, no tracking pixels', 'IP hash', 'IP allowlist', 'DNT, IP anonymisation, consent gate', 'Allowlist bypass', 'Opt-out + exclusions', 'Session-bound order access', 'Customer-scoped API, no card data stored'],
        ['Offline licence verification', 'yes', 'yes', 'yes', 'yes', 'yes', 'yes', 'yes', 'yes'],
        ['Self-hosted (no calls to us at runtime)', 'yes', 'yes', 'yes', 'yes', 'yes-note', 'yes-note', 'yes', 'yes'],
    ]
    def fmt_cell(c, plain=False):
        if c == 'yes': return '<span class="text-accent-600 font-bold">✓</span>' if not plain else '✓'
        if c == 'yes-note':
            return ('<span class="text-accent-600 font-bold">✓</span>'
                    '<sup><a href="#threat-intel-note" class="text-ink-400 no-underline" style="text-decoration:none">†</a></sup>'
                    if not plain else '✓ †')
        if c == 'no': return '<span class="text-ink-400">—</span>' if not plain else '—'
        return html.escape(c)
    rows_html = '\n'.join(
        '<tr>' +
        f'<th class="p-4 font-semibold text-ink-800 border-t border-ink-100" style="font-size:14px; text-align:left">{html.escape(r[0])}</th>' +
        ''.join(
            f'<td class="p-4 border-t border-ink-100 text-sm {"text-ink-900 font-medium" if c not in ("yes","no") else ""}" style="text-align:center; vertical-align:middle">{fmt_cell(c)}</td>'
            for c in r[1:]
        ) +
        '</tr>'
        for r in comparison_rows
    )
    # Mobile fallback: render the same data as cards, one per plugin
    plugin_titles = ['Quotations', 'Email Tracking', 'Geo Block', 'Visitor Analytics', 'Fraud Prevention', 'Review Requests', 'Checkout Guard', 'Business Credit']
    mobile_cards = []
    for idx, title in enumerate(plugin_titles):
        rows_for_card = '\n'.join(
            f'<div class="vp-cmp-row">'
            f'<span class="vp-cmp-key">{html.escape(r[0])}</span>'
            f'<span class="vp-cmp-val">{fmt_cell(r[idx + 1])}</span>'
            f'</div>'
            for r in comparison_rows
        )
        mobile_cards.append(
            f'<article class="vp-compare-card">'
            f'<h3 class="font-bold text-lg text-ink-900 mb-1">{title}</h3>'
            f'<div>{rows_for_card}</div>'
            f'</article>'
        )

    # Compatibility matrix — one row per plugin. Vendure range comes
    # from each plugin's declared peer dependency; "Verified on" is the
    # newest Vendure release we build + smoke-test against before
    # publishing. Kept as data so a plugin version bump (which flows in
    # via versions.json) keeps the "Latest" column honest.
    VERIFIED_VENDURE = '3.7.1'
    compat = {
        'quotations':        ('3.5 – 3.7', '20 LTS+', '5.4 – 6.x'),
        'email-tracking':    ('3.5 – 3.7', '20 LTS+', '5.4 – 6.x'),
        'geo-block':         ('3.5 – 3.7', '20 LTS+', '5.4 – 6.x'),
        'visitor-analytics': ('3.5 – 3.7', '20 LTS+', '5.4 – 6.x'),
        'fraud-prevention':  ('3.5 – 3.7', '20 LTS+', '5.4 – 6.x'),
        'review-requests':   ('3.5 – 3.7', '20 LTS+', '5.4 – 6.x'),
        'checkout-guard':    ('3.5 – 3.7', '20 LTS+', '5.4 – 6.x'),
        'payments':          ('3.5 – 3.7', '20 LTS+', '5.4 – 6.x'),
        'business-credit':   ('3.5 – 3.7', '20 LTS+', '5.4 – 6.x'),
    }
    compat_rows_html = ''
    for p in PLUGINS:
        vendure_range, node_range, ts_range = compat.get(
            p['slug'], ('3.5 – 3.7', '20 LTS+', '5.4 – 6.x'))
        compat_rows_html += (
            '<tr>'
            f'<th style="text-align:left"><a href="/vendure-plugins/{p["slug"]}/">{html.escape(p["title"])}</a></th>'
            f'<td style="text-align:center"><!--email_off--><span class="vp-compat-ver font-mono" data-hulo-pkg="{html.escape(p["pkg"])}" data-hulo-version-prefix="v">v{p["version"]}</span><!--/email_off--></td>'
            f'<td style="text-align:center">{vendure_range}</td>'
            f'<td style="text-align:center">{node_range}</td>'
            f'<td style="text-align:center">{ts_range}</td>'
            f'<td style="text-align:center"><span class="vp-compat-ok">✓ {VERIFIED_VENDURE}</span></td>'
            '</tr>'
        )

    faqs = [
        ('How are the plugins licensed?', 'Each plugin is licensed individually. Every install gets <strong>14 days with every feature on, no card and no key</strong>. To keep the premium features after that, subscribe from the plugin\'s admin page — subscriptions start with a further 14-day free trial (card required, nothing charged for two weeks, cancel any time) and continue as a monthly (£2.95–£14.95/mo) or annual (two months free) subscription. Or buy a one-off lifetime licence (£59–£299, never expires, 12 months of updates included). Every option gives you a JWT licence key that installs itself in the admin.'),
        ('How do I buy and activate a licence?', 'Open the plugin\'s page in your Vendure admin, pick monthly or annual on the licence banner and click <strong>Start 14-day free trial</strong> (or choose lifetime and click <strong>Buy lifetime</strong>). Stripe Checkout opens in a new tab; within a minute of payment the licence installs itself in the admin — no email round-trip, no <code>.env</code> edit, no restart. Renewed subscription keys are picked up automatically. Prefer to buy on the web? Use the plugin\'s buy page and paste the emailed key into the admin instead.'),
        ('How do I manage / cancel my subscription?', 'Every receipt email includes a Stripe Customer Portal link — click it to update your payment method, see invoices, or cancel. No need to email us. Lifetime customers have nothing to manage; reply to your receipt if you need a VAT invoice.'),
        ('I lost my licence key — what now?', 'Re-send every active key on file at <a class="underline underline-offset-2" href="https://elite.charity/licence/forgot">elite.charity/licence/forgot</a>. We always show the same confirmation regardless of whether the email is on file (anti-enumeration), so check spam if nothing arrives. Limited to 5 requests per email per day.'),
        ('Can I export or delete my data?', 'Yes — under UK GDPR you have a right to see, export and erase the personal data we hold. Visit <a class="underline underline-offset-2" href="https://elite.charity/licence/privacy">elite.charity/licence/privacy</a> and we\'ll email you a magic link to do both.'),
        ('Do the plugins call home?', 'No — licence verification is offline. Each plugin verifies the JWT at boot against an embedded public key. A revocation list is polled once a week (cached, soft-fail), so a brief outage at our end never disables your store. Nothing else leaves your server.'),
        ('Where does customer data live?', 'On your Vendure server — same DB as the rest of your data. No third-party analytics provider. The visitor-analytics plugin\'s ingest endpoint is on your domain.'),
        ('What if I don\'t buy a licence?', 'Plugins still boot in a free tier — install, configure, browse data, and the admin UI is functional. The public storefront endpoints are limited (geo-block always reports `enabled:false`; visitor-analytics dashboards return 403). Buy a key when you\'re ready.'),
        ('Can I see the source?', 'Yes — every plugin is on GitHub under <a class="underline underline-offset-2" href="https://github.com/huloglobal">github.com/huloglobal</a> and <a class="underline underline-offset-2" href="https://github.com/exceeded">github.com/exceeded</a>. MIT-style licence on the code itself, separate paid licence for production use.'),
        ('Do they work on Vendure 2.x?', 'They target Vendure 3.x (3.0+). Vendure 2.x isn\'t supported because we use some of the 3.x customField improvements.'),
    ]
    faq_html = '\n'.join(f'<details><summary>{html.escape(q)}</summary><p>{a}</p></details>' for q, a in faqs)

    body = f'''
<section class="vp-hero">
<div class="container-page relative pt-24 pb-16 md:pt-32 md:pb-24">
<span class="vp-pill mb-6">Vendure plugins by Hulo Global</span>
<h1 class="max-w-3xl text-4xl sm:text-5xl md:text-6xl font-bold tracking-tight text-ink-900 leading-[1.04]">
Production-grade plugins for your Vendure store.
</h1>
<p class="mt-7 max-w-2xl text-lg md:text-xl text-ink-600 leading-relaxed">
Battle-tested in our own UK e-commerce stack. One <code class="font-mono text-sm bg-ink-100 px-1.5 py-0.5 rounded">yarn add</code>, one config line, ready in 5 minutes.
</p>
</div>
</section>

<section class="vp-section" style="background:#fff">
<div class="container-page">
<div class="vp-cards-grid">
{''.join(cards)}
</div>
</div>
</section>

<section class="vp-section" style="background:var(--color-ink-50,#f8fafc)">
<div class="container-page">
<div class="max-w-2xl mx-auto text-center" style="margin-bottom:56px">
<p class="text-sm font-semibold uppercase tracking-wider text-accent-600">At a glance</p>
<h2 class="mt-4 text-3xl md:text-4xl font-bold tracking-tight text-ink-900">Same shape, focused on different problems.</h2>
</div>
<!-- Desktop / wide tablet: full comparison table -->
<div class="vp-compare-table rounded-2xl border border-ink-100 bg-white table-wrap" role="region" aria-label="Plugin comparison" tabindex="0">
<table class="w-full" style="min-width:1320px">
<thead>
<tr>
<th class="p-4 font-medium text-sm text-ink-500" style="text-align:left"></th>
<th class="p-4 font-semibold text-ink-900" style="text-align:center">Quotations</th>
<th class="p-4 font-semibold text-ink-900" style="text-align:center">Email Tracking</th>
<th class="p-4 font-semibold text-ink-900" style="text-align:center">Geo Block</th>
<th class="p-4 font-semibold text-ink-900" style="text-align:center">Visitor Analytics</th>
<th class="p-4 font-semibold text-ink-900" style="text-align:center">Fraud Prevention</th>
<th class="p-4 font-semibold text-ink-900" style="text-align:center">Review Requests</th>
<th class="p-4 font-semibold text-ink-900" style="text-align:center">Checkout Guard</th>
<th class="p-4 font-semibold text-ink-900" style="text-align:center">Business Credit</th>
</tr>
</thead>
<tbody>{rows_html}</tbody>
</table>
</div>
<!-- Mobile: stacked cards, one per plugin -->
<div class="vp-compare-cards" aria-hidden="false">
{''.join(mobile_cards)}
</div>
<p id="threat-intel-note" class="mt-6 text-xs text-ink-500 leading-relaxed max-w-3xl mx-auto md:mx-0">
<strong>†</strong> Two plugins make optional outbound calls to third parties, never to Hulo Global. <strong>Fraud Prevention</strong> fetches threat-intelligence — IP-reputation lookups (<code class="font-mono">ip-api.com</code>) and nightly public blocklist feeds (FireHOL, Spamhaus, Tor, disposable-email domains), cached, and switchable off. <strong>Review Requests</strong> optionally reads your live rating from the free Trustpilot API and sends invitation emails via your own SMTP. As with every plugin, nothing phones home to us at runtime for the core function.
</p>
</div>
</section>

<section class="vp-section" id="compatibility" style="background:#fff">
<div class="container-page">
<div class="max-w-2xl mx-auto text-center" style="margin-bottom:48px">
<p class="text-sm font-semibold uppercase tracking-wider text-accent-600">Compatibility</p>
<h2 class="mt-4 text-3xl md:text-4xl font-bold tracking-tight text-ink-900">Verified against the latest Vendure.</h2>
<p class="mt-4 text-ink-600 leading-relaxed">Every plugin is built and smoke-tested against the newest Vendure release before publishing. The table below is the current support surface — installs cleanly with <code class="font-mono text-sm bg-ink-100 px-1.5 py-0.5 rounded">yarn</code> or <code class="font-mono text-sm bg-ink-100 px-1.5 py-0.5 rounded">npm</code>.</p>
</div>
<div class="vp-compat-wrap rounded-2xl border border-ink-100 bg-white table-wrap" role="region" aria-label="Compatibility matrix" tabindex="0">
<table class="vp-compat w-full" style="min-width:680px">
<thead>
<tr>
<th style="text-align:left">Plugin</th>
<th style="text-align:center">Latest</th>
<th style="text-align:center">Vendure&nbsp;core</th>
<th style="text-align:center">Node</th>
<th style="text-align:center">TypeScript</th>
<th style="text-align:center">Verified&nbsp;on</th>
</tr>
</thead>
<tbody>{compat_rows_html}</tbody>
</table>
</div>
<p class="mt-6 text-sm text-ink-500 max-w-3xl mx-auto text-center">
A boot-time check emits a non-fatal warning if <code class="font-mono text-xs bg-ink-100 px-1 py-0.5 rounded">@vendure/core</code> is outside the tested range, so a future 3.x upgrade is always safe to try. Vendure 4.0 will be tested and re-declared once its changelog lands. Node 20 LTS or newer recommended.
</p>
</div>
</section>

<section class="vp-section" style="background:var(--color-ink-50,#f8fafc)">
<div class="container-page max-w-3xl">
<p class="text-sm font-semibold uppercase tracking-wider text-accent-600">FAQ</p>
<h2 class="mt-4 text-3xl md:text-4xl font-bold tracking-tight text-ink-900" style="margin-bottom:40px">Common questions.</h2>
<div class="vp-faq">{faq_html}</div>
</div>
</section>
'''
    return header('Vendure plugins by Hulo Global',
                  'https://huloglobal.com/vendure-plugins/',
                  'Production-grade Vendure plugins by Hulo Global — email tracking, geo-blocking, visitor analytics, fraud prevention, Trustpilot review requests. Drop-in, self-hosted, licensed.') + body + FOOTER


def plugin_page(p):
    feats_html = '\n'.join(
        f'<div class="vp-feat"><div class="vp-feat-tick" aria-hidden="true">{TICK_SVG}</div><div><h3>{html.escape(t)}</h3><p>{html.escape(d)}</p></div></div>'
        for t, d in list(p['features']) + COMMON_FEATURES
    )
    endpoints_html = '\n'.join(
        f'<div class="vp-endpoint"><span class="vp-method {m}">{m}</span><code>{html.escape(path)}</code><span class="vp-desc">{html.escape(desc)}</span></div>'
        for m, path, desc in list(p['endpoints']) + common_endpoints(p['slug'])
    )
    env_var_name = 'HULO_LICENCE_KEY_' + p['slug'].upper().replace('-', '_')

    config_block = f'''<span class="vp-comment"># vendure-config.ts</span>
import {{ <span class="vp-key">{p['class']}</span> }} from <span class="vp-str">'{p['pkg']}'</span>;

export const config: VendureConfig = {{
  plugins: [
    <span class="vp-key">{p['class']}</span>.init({{
      publicBaseUrl: <span class="vp-str">'https://shop.example.com'</span>,
      licenceKey: process.env.<span class="vp-key">{env_var_name}</span>,
    }}),
    <span class="vp-comment">// ... your other plugins</span>
  ],
}};'''

    short_id = p['slug']
    pkg_short = p['pkg'].split('/')[-1]
    pricing = p.get('pricing', CURRENCIES)
    price_mo_gbp = pricing['GBP']['monthly']
    price_lt_gbp = pricing['GBP']['lifetime']
    # Every plugin page carries an override: real prices for purchasable
    # currencies, estimates only for anything without a Stripe amount.
    pricing_override_js = ('<script>window.HULO_PRICES_OVERRIDE = '
        + json.dumps(display_price_table(price_mo_gbp, price_lt_gbp, p.get('pricing'))) + ';</script>')
    faqs = [
        ('How do I get a licence key?',
         f'<a class="underline underline-offset-2" href="{BUY_BASE}/{pkg_short}">Buy here</a> — Stripe Checkout — monthly, annual (two months free) or lifetime. You\'ll receive the JWT key by email. Paste it into the plugin\'s admin settings (Activate) — no redeploy — or set it as <code class="font-mono text-sm bg-ink-100 px-1 py-0.5 rounded">{env_var_name}</code> in your <code class="font-mono text-sm bg-ink-100 px-1 py-0.5 rounded">.env</code> if you prefer config-as-code; the env key wins when both are present.'),
        ('Does it work without a key?',
         'Yes. Every install runs with <strong>all premium features on for its first 14 days</strong> — no card, no licence key, nothing to configure — so you can judge it on your real traffic. After that it keeps working in the free tier. To keep the premium features, click <strong>Start 14-day free trial</strong> on the plugin\'s admin page: subscriptions add a further 14 days free (card required, nothing charged until then, cancel any time), and the licence installs itself.'),
        ('Which databases are supported?',
         'MySQL, MariaDB and PostgreSQL (verified against PostgreSQL 17). The plugin follows your Vendure <code class="font-mono text-sm bg-ink-100 px-1 py-0.5 rounded">dbConnectionOptions</code> automatically — there is nothing to configure.'),
        ('How do updates work?',
         f'The plugin checks the npm registry daily. When a newer version exists, the admin dashboard shows an update banner with a What\'s-new link to the <a class="underline underline-offset-2" href="/vendure-plugins/{p["slug"]}/changelog/">changelog</a> and an "Update now" button that installs the registry-verified release via your own package manager and gracefully restarts under your process supervisor. Prefer manual control? Copy the install command instead, or set <code class="font-mono text-sm bg-ink-100 px-1 py-0.5 rounded">HULO_SELF_UPDATE=off</code>.'),
        ('Where is data stored?',
         'In your Vendure database. The plugin adds its own tables (created on boot, or via a migration for the plugins that register entities) — your data never leaves your server.'),
        ('Will it survive a Vendure upgrade?',
         f'Tested against Vendure <code class="font-mono text-sm bg-ink-100 px-1 py-0.5 rounded">&gt;=3.5.0 &lt;4.0.0</code> — 3.5, 3.6 and 3.7 are all covered by CI. A boot-time compatibility check emits a non-fatal warning if <code class="font-mono text-sm bg-ink-100 px-1 py-0.5 rounded">@vendure/core</code> is outside that range, so upgrades to a future 3.x are safe to try. The 4.0 line will be tested and re-declared once its changelog lands.'),
    ]
    faq_html = '\n'.join(f'<details><summary>{html.escape(q)}</summary><p>{a}</p></details>' for q, a in faqs)

    # Proof strip under the tagline: real numbers only.
    proof_items = []
    dl = npm_downloads_last_month(p['pkg'])
    ytd = npm_downloads_this_year(p['pkg'])
    if dl:
        proof_items.append(f'<a href="https://www.npmjs.com/package/{p["pkg"]}" class="vp-proof-item">{dl:,} npm downloads last month</a>')
    if ytd:
        proof_items.append(f'<a href="https://npm-stat.com/charts.html?package={p["pkg"]}" class="vp-proof-item">{ytd:,} downloads in {__import__("datetime").date.today().year}</a>')
    if p['slug'] in VENDURE_DIRECTORY_LISTED:
        proof_items.append('<a href="https://docs.vendure.io/plugins" class="vp-proof-item">Listed in the Vendure plugin directory</a>')
    elif p['slug'] in VENDURE_DIRECTORY_SUBMITTED:
        proof_items.append('<span class="vp-proof-item">Submitted to the Vendure plugin directory</span>')
    proof_items.append('<span class="vp-proof-item">Vendure 3.5 – 3.7</span>')
    proof_items.append('<span class="vp-proof-item">MySQL · MariaDB · PostgreSQL</span>')
    proof_items.append('<span class="vp-proof-item">AGPL source + commercial licence</span>')
    proof_html = '<div class="mt-6 flex flex-wrap gap-x-5 gap-y-2 text-sm text-ink-600">' + ''.join(proof_items) + '</div>'

    tiers = TIERS.get(p['slug'])
    tiers_html = ''
    if tiers:
        free_li = ''.join(f'<li>{html.escape(t)}</li>' for t in tiers[0])
        paid_li = ''.join(f'<li>{html.escape(t)}</li>' for t in tiers[1])
        tiers_html = f'''
<section class="vp-section bg-white">
<div class="container-page max-w-3xl">
<p class="text-sm font-semibold uppercase tracking-wider text-accent-600">Free tier vs licensed</p>
<h2 class="mt-3 text-3xl md:text-4xl font-bold tracking-tight text-ink-900">Try the whole thing, keep the core for free.</h2>
<p class="mt-4 text-ink-600">Install without a key and everything on the left works indefinitely. The 14-day trial switches the right-hand column on with your real traffic; a licence keeps it on.</p>
<div class="mt-8 grid gap-6 md:grid-cols-2">
<div class="rounded-lg border border-ink-200 bg-white p-6"><p class="text-xs font-semibold uppercase tracking-wider text-ink-500">Free tier (after the 14 days)</p><ul class="vp-tier-list mt-3">{free_li}</ul></div>
<div class="rounded-lg border border-accent-300 bg-accent-50 p-6"><p class="text-xs font-semibold uppercase tracking-wider text-accent-700">First 14 days + licensed</p><ul class="vp-tier-list mt-3">{paid_li}</ul><a href="{BUY_BASE}/{pkg_short}?plan=monthly" class="btn btn-primary mt-5">Start 14-day free trial →</a></div>
</div>
</div>
</section>
'''
    needs_migration = p['slug'] in NEEDS_MIGRATION
    step_count = 'Four' if needs_migration else 'Three'
    migration_step = f'''
<div class="vp-step mt-10">
<h3 class="text-xl font-semibold text-ink-900 flex items-center">Run the migration</h3>
<p class="mt-2 text-ink-600">The plugin registers its own entities. Generate and run the migration like any other:</p>
<div class="vp-code mt-3">yarn migration:generate Add{p['class']}Tables
yarn migration:run</div>
</div>''' if needs_migration else '''
<div class="mt-10 rounded-lg border border-ink-200 bg-white p-4 text-sm text-ink-700"><strong>No migration to run.</strong> The plugin creates its tables on first boot and upgrades them in place on later versions.</div>'''

    body = f'''
<section class="vp-hero">
<div class="container-page relative pt-12 pb-10 md:pt-16 md:pb-14">
<img class="vp-plugin-logo" src="/vendure-plugins/logos/{p['slug']}.svg" alt="" width="56" height="56" aria-hidden="true">
<nav class="mb-5 text-sm text-ink-600">
<a href="/vendure-plugins/" class="hover:text-ink-900">Vendure plugins</a>
<span class="mx-2 text-ink-400">/</span>
<span class="text-ink-900 font-medium">{html.escape(p['title'])}</span>
</nav>
<h1 class="max-w-3xl text-4xl sm:text-5xl md:text-6xl font-bold tracking-tight text-ink-900 leading-[1.04]">{html.escape(p['title'])}</h1>
<p class="mt-6 max-w-2xl text-lg md:text-xl text-ink-600 leading-relaxed">{html.escape(p['tagline'])}</p>
{proof_html}
<div class="mt-8 flex flex-wrap items-center gap-3">
<a href="{BUY_BASE}/{pkg_short}?plan=monthly" class="btn btn-primary">Start 14-day free trial →</a>
<a href="{BUY_BASE}/{pkg_short}?plan=lifetime" class="btn btn-secondary">Buy lifetime</a>
<a href="#install" class="btn btn-secondary">Install</a>
<a href="/vendure-plugins/{short_id}/docs/" class="btn btn-secondary">Read the manual</a>
<a href="/vendure-plugins/{p['slug']}/changelog/" class="ml-auto" title="See what changed in each release"><!--email_off--><span class="text-xs text-ink-500 font-mono hover:underline" data-hulo-pkg="{html.escape(p['pkg'])}" data-hulo-version-prefix="v">v{p['version']}</span><!--/email_off--></a>
</div>
</div>
</section>

<section class="vp-section bg-white">
<div class="container-page">
<div class="vp-grid-2">
<div>
<p class="text-sm font-semibold uppercase tracking-wider text-accent-600">What it does</p>
<h2 class="mt-3 text-3xl md:text-4xl font-bold tracking-tight text-ink-900">Built for production from day one.</h2>
<p class="mt-5 text-lg text-ink-700 leading-relaxed">{html.escape(p['description'])}</p>
<div class="mt-10">
{feats_html}
</div>
</div>
{pricing_override_js}
<aside class="vp-pricing-aside">
<div class="vp-price-card">
<p class="text-xs uppercase tracking-wider text-accent-600 font-semibold">Monthly · 14-day free trial</p>
<p class="vp-price-num mt-2"><span class="vp-trial-num">14</span><small>days free</small></p>
<p class="mt-2 text-sm text-ink-700">Then <span data-monthly-price>{price_mo_gbp}</span>/month. Card required at checkout; cancel any time before day 15 and pay nothing.</p>
<a href="{BUY_BASE}/{pkg_short}?plan=monthly" class="btn btn-secondary w-full mt-5" style="text-align:center">Start 14-day free trial →</a>
<p class="vp-tiny-note">Card required. One trial per customer.</p>
</div>
<div class="vp-price-card featured">
<p class="text-xs uppercase tracking-wider text-accent-600 font-semibold">Lifetime · Best value</p>
<p class="vp-price-num mt-2" data-lifetime-price>{price_lt_gbp}</p>
<p class="mt-2 text-sm text-ink-600">One-off. Never expires. 12 months of updates.</p>
<a href="{BUY_BASE}/{pkg_short}?plan=lifetime" class="btn btn-primary w-full mt-5" style="text-align:center">Buy lifetime →</a>
</div>
<p data-approx-note style="display:none" class="mt-3 text-xs text-ink-500">Prices marked ≈ are estimates — you'll be billed in £ GBP and your bank converts at its own rate.</p>
<p class="mt-4 text-xs text-ink-500 leading-relaxed">Payments processed by Stripe. VAT applied where applicable. 30-day refund if it doesn't fit your stack. By proceeding you accept our <a href="/legal/terms/" class="underline">Terms</a> and <a href="/legal/privacy/" class="underline">Privacy Policy</a>.</p>
</aside>
</div>
</div>
</section>

<section id="install" class="vp-section bg-ink-50">
<div class="container-page max-w-3xl" style="counter-reset: step;">
<p class="text-sm font-semibold uppercase tracking-wider text-accent-600">Install</p>
<h2 class="mt-3 text-3xl md:text-4xl font-bold tracking-tight text-ink-900">{step_count} steps, five minutes.</h2>

<div class="vp-step mt-10">
<h3 class="text-xl font-semibold text-ink-900 flex items-center">Add the package</h3>
<p class="mt-2 text-ink-600">Or run the one-line installer that does steps 1–3 for you:</p>
<div class="vp-code mt-3">curl -sSL https://huloglobal.com/vendure-plugins/{short_id}/install.sh | bash</div>
<p class="mt-3 text-sm text-ink-500">Prefer to do it by hand?</p>
<div class="vp-code mt-2">yarn add {p['pkg']}
<span class="vp-comment"># or</span> npm install {p['pkg']}
<span class="vp-comment"># or</span> pnpm add {p['pkg']}</div>
</div>

<div class="vp-step mt-10">
<h3 class="text-xl font-semibold text-ink-900 flex items-center">Register it</h3>
<p class="mt-2 text-ink-600">In your <code class="font-mono text-sm bg-white px-1.5 py-0.5 rounded border border-ink-200">vendure-config.ts</code>:</p>
<div class="vp-code mt-3">{config_block}</div>
</div>

<div class="vp-step mt-10">
<h3 class="text-xl font-semibold text-ink-900 flex items-center">Compile the admin UI</h3>
<p class="mt-2 text-ink-600">Add the extension to your <code class="font-mono text-sm bg-white px-1.5 py-0.5 rounded border border-ink-200">compileUiExtensions</code> call so the plugin's page appears in the admin:</p>
<div class="vp-code mt-3"><span class="vp-comment">// compile-admin-ui.ts</span>
import {{ compileUiExtensions }} from <span class="vp-str">'@vendure/ui-devkit/compiler'</span>;
import {{ <span class="vp-key">{p['class']}</span> }} from <span class="vp-str">'{p['pkg']}'</span>;

compileUiExtensions({{
  outputPath: path.join(__dirname, <span class="vp-str">'admin-ui'</span>),
  extensions: [<span class="vp-key">{p['class']}</span>.uiExtensions],
}});</div>
</div>
{migration_step}

<div class="mt-10 rounded-lg border border-ink-200 bg-white p-6">
<p class="text-sm text-ink-700"><strong>That's it.</strong> Restart Vendure and the plugin's page is in the admin with <strong>every feature on for 14 days</strong> — no card, no key. To keep it all on afterwards, open the page and click <strong>Start 14-day free trial</strong> to subscribe — the key installs itself, no <code class="font-mono text-sm bg-ink-100 px-1 py-0.5 rounded">.env</code> edit, no redeploy.</p>
</div>
</div>
</section>

{tiers_html}
<section class="vp-section bg-white">
<div class="container-page max-w-3xl">
<p class="text-sm font-semibold uppercase tracking-wider text-accent-600">HTTP endpoints</p>
<h2 class="mt-3 text-3xl md:text-4xl font-bold tracking-tight text-ink-900">Every route exposed.</h2>
<div class="mt-8 rounded-lg border border-ink-100 bg-white table-wrap" role="region" aria-label="HTTP endpoints" tabindex="0">
<div style="min-width:560px;padding:6px 12px">
{endpoints_html}
</div>
</div>
</div>
</section>

<section class="vp-section bg-ink-50">
<div class="container-page max-w-3xl">
<p class="text-sm font-semibold uppercase tracking-wider text-accent-600">FAQ</p>
<h2 class="mt-3 text-3xl md:text-4xl font-bold tracking-tight text-ink-900 mb-8">Common questions.</h2>
<div class="vp-faq">{faq_html}</div>
</div>
</section>

<section class="vp-section bg-white">
<div class="container-page max-w-2xl text-center">
<h2 class="text-3xl md:text-4xl font-bold tracking-tight text-ink-900">Ready to ship?</h2>
<p class="mt-5 text-lg text-ink-600 leading-relaxed">Install in five minutes, run the trial on real traffic, keep it if it earns its place.</p>
<div class="mt-8 flex flex-wrap items-center justify-center gap-3">
<a href="{BUY_BASE}/{pkg_short}?plan=monthly" class="btn btn-primary">Start 14-day free trial →</a>
<a href="{BUY_BASE}/{pkg_short}?plan=lifetime" class="btn btn-secondary">Buy lifetime</a>
<a href="mailto:hello@huloglobal.com?subject=Vendure%20plugin%20enquiry" class="btn btn-secondary">Email us</a>
</div>
</div>
</section>
'''
    return header(f"{p['title']} — Vendure plugin by Hulo Global",
                  f"https://huloglobal.com/vendure-plugins/{p['slug']}/",
                  p['tagline']) + body + FOOTER


CHANGELOG_STYLE = """
<style>
/* Changelog — self-contained styles so nothing inherits the plugin-card
   flex/grid list treatment (which splits <strong> lead-ins into columns). */
.cl-wrap { max-width: 50rem; margin: 0 auto; }
.cl-rail { position: relative; padding-left: 1.75rem; }
.cl-rail::before { content: ""; position: absolute; left: 8px; top: 10px; bottom: 10px;
  width: 2px; background: linear-gradient(to bottom, #e2e8f0, #f1f5f9); border-radius: 1px; }
.cl-release { position: relative; background: #ffffff; border: 1px solid #e2e8f0;
  border-radius: 14px; padding: 1.6rem 1.9rem 1.7rem; margin-bottom: 1.4rem;
  box-shadow: 0 1px 3px rgba(15,20,25,.04); }
.cl-release::before { content: ""; position: absolute; left: -1.75rem; top: 1.9rem;
  width: 12px; height: 12px; margin-left: 3px; border-radius: 50%;
  background: #f59e0b; border: 2.5px solid #fff; box-shadow: 0 0 0 2px #e2e8f0; }
.cl-head { display: flex; flex-wrap: wrap; align-items: baseline; gap: .35rem .8rem; }
.cl-version { font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  font-size: 1.35rem; font-weight: 700; color: #0f1419; letter-spacing: -.01em; }
.cl-date { font-size: .875rem; color: #64748b; }
.cl-latest { font-size: .7rem; font-weight: 700; text-transform: uppercase; letter-spacing: .06em;
  color: #b45309; background: #fef3c7; border: 1px solid #fde68a;
  padding: .18rem .55rem; border-radius: 999px; }
.cl-badge { display: inline-block; font-size: .7rem; font-weight: 700; text-transform: uppercase;
  letter-spacing: .07em; padding: .22rem .6rem; border-radius: 999px; margin: 1.1rem 0 .1rem; }
.cl-badge.added      { color: #15803d; background: #f0fdf4; border: 1px solid #bbf7d0; }
.cl-badge.changed    { color: #b45309; background: #fffbeb; border: 1px solid #fde68a; }
.cl-badge.fixed      { color: #1d4ed8; background: #eff6ff; border: 1px solid #bfdbfe; }
.cl-badge.security   { color: #b91c1c; background: #fef2f2; border: 1px solid #fecaca; }
.cl-badge.removed, .cl-badge.deprecated, .cl-badge.other
                     { color: #475569; background: #f8fafc; border: 1px solid #e2e8f0; }
.cl-list { margin: .55rem 0 0; padding: 0; list-style: none; }
.cl-list li { display: block; position: relative; padding-left: 1.15rem;
  margin: .55rem 0; color: #334155; font-size: .975rem; line-height: 1.7; }
.cl-list li::before { content: ""; position: absolute; left: 0; top: .68em;
  width: 6px; height: 6px; border-radius: 50%; background: #cbd5e1; }
.cl-list li strong { color: #0f1419; font-weight: 650; }
.cl-list li code { font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  font-size: .85em; background: #f1f5f9; border: 1px solid #e2e8f0;
  padding: .08em .35em; border-radius: 5px; white-space: nowrap; }
@media (max-width: 640px) {
  .cl-rail { padding-left: 0; }
  .cl-rail::before, .cl-release::before { display: none; }
  .cl-release { padding: 1.2rem 1.1rem 1.3rem; }
}
</style>
"""

MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', 'July',
          'August', 'September', 'October', 'November', 'December']


def pretty_date(iso: str) -> str:
    m = _re.match(r'(\d{4})-(\d{2})-(\d{2})', iso)
    if not m:
        return iso
    return f"{int(m.group(3))} {MONTHS[int(m.group(2)) - 1]} {m.group(1)}"


def changelog_page(p, releases):
    latest = releases[0] if releases else None
    rel_html = []
    for idx, r in enumerate(releases):
        secs = []
        for heading, items in r['sections']:
            kind = heading.strip().lower()
            if kind not in ('added', 'changed', 'fixed', 'security', 'removed', 'deprecated'):
                kind = 'other'
            lis = '\n'.join(f'<li>{_md_inline(i)}</li>' for i in items)
            secs.append(
                f'<span class="cl-badge {kind}">{html.escape(heading)}</span>'
                f'<ul class="cl-list">{lis}</ul>')
        latest_chip = '<span class="cl-latest">Latest</span>' if idx == 0 else ''
        rel_html.append(f"""
<article class="cl-release" id="v{html.escape(r['version'])}">
  <div class="cl-head">
    <h2 class="cl-version">v{html.escape(r['version'])}</h2>
    <span class="cl-date">{html.escape(pretty_date(r['date']))}</span>
    {latest_chip}
  </div>
  {''.join(secs)}
</article>""")
    latest_line = (
        f"Latest release: <span class='font-mono'>v{html.escape(latest['version'])}</span> — {html.escape(pretty_date(latest['date']))}."
        if latest else 'No releases published yet.')
    body = f'''
<section class="vp-hero">
<div class="container-page relative pt-12 pb-10 md:pt-16 md:pb-14">
<nav class="mb-5 text-sm text-ink-600">
<a href="/vendure-plugins/" class="hover:text-ink-900">Vendure plugins</a>
<span class="mx-2 text-ink-400">/</span>
<a href="/vendure-plugins/{p['slug']}/" class="hover:text-ink-900">{html.escape(p['title'])}</a>
<span class="mx-2 text-ink-400">/</span>
<span class="text-ink-900 font-medium">Changelog</span>
</nav>
<h1 class="max-w-3xl text-4xl sm:text-5xl font-bold tracking-tight text-ink-900 leading-[1.04]">{html.escape(p['title'])} changelog</h1>
<p class="mt-4 max-w-2xl text-lg text-ink-600 leading-relaxed">Every release of <!--email_off--><code class="font-mono text-base">{html.escape(p['pkg'])}</code><!--/email_off-->. {latest_line}</p>
<div class="mt-6 flex flex-wrap items-center gap-3">
<a href="/vendure-plugins/{p['slug']}/" class="btn btn-secondary">Plugin page</a>
<a href="/vendure-plugins/{p['slug']}/docs/" class="btn btn-secondary">Manual</a>
</div>
</div>
</section>
<section class="vp-section" style="background:#f8fafc">
<div class="container-page">
<div class="cl-wrap"><div class="cl-rail">
<!--email_off-->
{''.join(rel_html)}
<!--/email_off-->
</div></div>
</div>
</section>
'''
    return header(f"Changelog — {p['title']} — Hulo Global",
                  f"https://huloglobal.com/vendure-plugins/{p['slug']}/changelog/",
                  f"Release history and version notes for {p['pkg']}.") + CHANGELOG_STYLE + body + FOOTER


INSTALL_SH = '''#!/usr/bin/env bash
# {title} — installer
# Run this from the root of your Vendure project (where vendure-config.ts lives).

set -euo pipefail

PKG="{pkg}"
CLASS="{class_name}"
ENV_VAR="{env_var}"

cd "$(dirname "$(pwd)/vendure-config.ts")" 2>/dev/null || true
if [[ ! -f "src/vendure-config.ts" && ! -f "vendure-config.ts" ]]; then
  echo "✗ Couldn't find vendure-config.ts in $(pwd). Run from your Vendure project root." >&2
  exit 1
fi
CONFIG=$( [[ -f "src/vendure-config.ts" ]] && echo "src/vendure-config.ts" || echo "vendure-config.ts" )

echo "→ Installing $PKG"
if [[ -f "yarn.lock" ]]; then
  yarn add "$PKG"
elif [[ -f "pnpm-lock.yaml" ]]; then
  pnpm add "$PKG"
else
  npm install "$PKG"
fi

if ! grep -q "$PKG" "$CONFIG"; then
  echo
  echo "→ Add the following to $CONFIG:"
  echo
  cat <<EOF
import {{ $CLASS }} from '$PKG';

// inside your VendureConfig.plugins[]:
$CLASS.init({{
  publicBaseUrl: process.env.VENDURE_PUBLIC_URL || 'http://localhost:3000',
  licenceKey: process.env.$ENV_VAR,
}}),
EOF
  echo
  echo "→ Then add the UI extension to your compile-admin-ui.ts (if you have one):"
  echo "  extensions: [..., $CLASS.uiExtensions]"
else
  echo "✓ $PKG already referenced in $CONFIG"
fi

echo
if [[ "{needs_migration}" == "1" ]]; then
  echo "→ Generate + run the migration (this plugin registers entities):"
  echo "  yarn migration:generate Add${{CLASS}}Tables"
  echo "  yarn migration:run"
else
  echo "→ No migration needed: tables are created on first boot."
fi
echo
echo "→ Set your licence key:"
echo "  echo '$ENV_VAR=...' >> .env"
echo
echo "✓ Done. Restart Vendure to pick up the plugin."
echo "  Buy a key:  https://elite.charity/licence/buy/{pkg_short}"
echo "  Manual:     https://huloglobal.com/vendure-plugins/{slug}/docs/"
'''


def install_sh(p):
    return INSTALL_SH.format(
        title=p['title'],
        pkg=p['pkg'],
        class_name=p['class'],
        env_var='HULO_LICENCE_KEY_' + p['slug'].upper().replace('-', '_'),
        pkg_short=p['pkg'].split('/')[-1],
        slug=p['slug'],
        needs_migration='1' if p['slug'] in NEEDS_MIGRATION else '0',
    )



ROADMAP_STYLE = """
<style>
.rm-hero { text-align:center; max-width:720px; margin:0 auto 8px; }
.rm-grid { display:grid; grid-template-columns:1fr 1fr; gap:32px; align-items:start; }
@media (max-width:900px){ .rm-grid{ grid-template-columns:1fr; } }
.rm-form-card { border:1px solid var(--color-ink-100,#e2e8f0); border-radius:18px; padding:28px; background:#fff; box-shadow:0 1px 3px rgba(15,23,42,.05); position:sticky; top:96px; }
.rm-field { margin-bottom:16px; }
.rm-field label { display:block; font-size:13px; font-weight:700; color:var(--color-ink-800,#1e293b); margin-bottom:6px; }
.rm-field input, .rm-field select, .rm-field textarea { width:100%; padding:10px 12px; border:1px solid var(--color-ink-200,#cbd5e1); border-radius:10px; font-size:14px; font-family:inherit; color:var(--color-ink-900,#0f172a); background:#fff; }
.rm-field textarea { min-height:120px; resize:vertical; }
.rm-field input:focus, .rm-field select:focus, .rm-field textarea:focus { outline:none; border-color:var(--color-accent-500,#f59e0b); box-shadow:0 0 0 3px rgba(245,158,11,.2); }
.rm-msg { margin-top:12px; font-size:14px; padding:10px 12px; border-radius:10px; display:none; }
.rm-msg.ok { display:block; background:#dcfce7; color:#166534; }
.rm-msg.err { display:block; background:#fee2e2; color:#991b1b; }
.rm-cols { display:grid; grid-template-columns:repeat(auto-fit,minmax(230px,1fr)); gap:16px; }
.rm-col h3 { font-size:12px; font-weight:800; text-transform:uppercase; letter-spacing:.06em; color:var(--color-ink-500,#64748b); margin:0 0 12px; display:flex; align-items:center; gap:8px; }
.rm-dot { width:9px; height:9px; border-radius:999px; display:inline-block; }
.rm-dot.considering{background:#eab308;} .rm-dot.planned{background:#0ea5e9;} .rm-dot.in_progress{background:#f97316;} .rm-dot.shipped{background:#22c55e;}
.rm-item { border:1px solid var(--color-ink-100,#e2e8f0); border-radius:14px; padding:14px 16px; background:#fff; margin-bottom:12px; box-shadow:0 1px 2px rgba(15,23,42,.04); }
.rm-item-plugin { font-size:11px; font-weight:700; color:#334155; background:#f1f5f9; padding:2px 8px; border-radius:6px; display:inline-block; margin-bottom:8px; }
.rm-item h4 { font-size:14px; font-weight:700; color:var(--color-ink-900,#0f172a); margin:0 0 6px; line-height:1.35; }
.rm-item p { font-size:13px; color:var(--color-ink-600,#475569); margin:0 0 8px; line-height:1.5; }
.rm-item .rm-resp { font-size:12.5px; color:#166534; background:#f0fdf4; border-left:3px solid #22c55e; padding:6px 10px; border-radius:6px; margin:8px 0 0; }
.rm-vote { display:inline-flex; align-items:center; gap:7px; border:1px solid var(--color-ink-200,#cbd5e1); background:#fff; border-radius:999px; padding:5px 14px; font-size:13px; font-weight:700; color:var(--color-ink-700,#334155); cursor:pointer; transition:all .12s; }
.rm-vote:hover:not(:disabled){ border-color:var(--color-accent-500,#f59e0b); color:#b45309; }
.rm-vote:disabled{ cursor:default; opacity:.75; }
.rm-vote.voted{ background:#fff7ed; border-color:#f59e0b; color:#b45309; }
.rm-empty { color:var(--color-ink-400,#94a3b8); font-size:13px; }
.rm-loading { color:var(--color-ink-500,#64748b); font-size:14px; padding:20px 0; }
</style>
"""

ROADMAP_SCRIPT = """
<script>
(function(){
  var API = 'https://elite.charity/feature-requests';
  var LABELS = { considering:'Considering', planned:'Planned', in_progress:'In progress', shipped:'Shipped' };
  var voted = {};
  try { voted = JSON.parse(localStorage.getItem('hulo-fr-voted')||'{}'); } catch(e){}

  function el(tag, cls, text){ var e=document.createElement(tag); if(cls)e.className=cls; if(text!=null)e.textContent=text; return e; }

  function renderBoard(data){
    var cols = document.getElementById('rm-cols');
    cols.innerHTML='';
    (data.statuses||[]).forEach(function(status){
      var items = (data.groups&&data.groups[status])||[];
      var col = el('div','rm-col');
      var h = el('h3'); var dot=el('span','rm-dot '+status); h.appendChild(dot); h.appendChild(document.createTextNode(LABELS[status]+' ('+items.length+')')); col.appendChild(h);
      if(!items.length){ col.appendChild(el('p','rm-empty','Nothing here yet.')); }
      items.forEach(function(it){
        var card = el('div','rm-item');
        card.appendChild(el('span','rm-item-plugin', it.plugin));
        card.appendChild(el('h4', null, it.title));
        if(it.description) card.appendChild(el('p', null, it.description));
        if(it.adminResponse) card.appendChild(el('p','rm-resp', it.adminResponse));
        if(status!=='shipped'){
          var b = el('button','rm-vote'+(voted[it.id]?' voted':''));
          b.type='button';
          b.innerHTML='<span aria-hidden=\"true\">▲</span> <span class=\"rm-vote-n\">'+it.votes+'</span>';
          if(voted[it.id]) b.disabled=true;
          b.addEventListener('click', function(){ vote(it.id, b); });
          card.appendChild(b);
        } else {
          card.appendChild(el('span','rm-vote voted','✓ '+it.votes));
        }
        col.appendChild(card);
      });
      cols.appendChild(col);
    });
  }

  function vote(id, btn){
    btn.disabled=true;
    fetch(API+'/'+id+'/vote',{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded'}})
      .then(function(r){return r.json();})
      .then(function(j){
        if(j && typeof j.votes==='number'){ var n=btn.querySelector('.rm-vote-n'); if(n)n.textContent=j.votes; }
        btn.classList.add('voted'); voted[id]=1;
        try{ localStorage.setItem('hulo-fr-voted', JSON.stringify(voted)); }catch(e){}
      })
      .catch(function(){ btn.disabled=false; });
  }

  function load(){
    fetch(API+'/roadmap').then(function(r){return r.json();}).then(renderBoard)
      .catch(function(){ document.getElementById('rm-cols').innerHTML='<p class=\"rm-empty\">Roadmap is temporarily unavailable.</p>'; });
  }

  var form = document.getElementById('rm-form');
  form.addEventListener('submit', function(ev){
    ev.preventDefault();
    var msg = document.getElementById('rm-msg'); msg.className='rm-msg';
    var btn = form.querySelector('button[type=submit]'); btn.disabled=true;
    var body = new URLSearchParams(new FormData(form)).toString();
    fetch(API,{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded'},body:body})
      .then(function(r){return r.json().then(function(j){return {ok:r.ok,j:j};});})
      .then(function(res){
        btn.disabled=false;
        if(res.ok && res.j.ok){ msg.className='rm-msg ok'; msg.textContent=res.j.message||'Thanks! Your idea has been submitted.'; form.reset(); }
        else { msg.className='rm-msg err'; msg.textContent=(res.j&&res.j.message)||'Something went wrong — please try again.'; }
      })
      .catch(function(){ btn.disabled=false; msg.className='rm-msg err'; msg.textContent='Network error — please try again.'; });
  });

  load();
})();
</script>
"""

def roadmap_page():
    head = header(
        'Feature roadmap & requests — HULO Vendure plugins',
        'https://huloglobal.com/vendure-plugins/roadmap/',
        'See what we\'re building for the HULO Vendure plugins, vote on what matters to you, and request a feature of your own.',
    )
    body = """
<section class="vp-section bg-ink-50">
<div class="container-page">
<div class="rm-hero">
<span class="vp-pill">Roadmap</span>
<h1 class="mt-4 text-4xl md:text-5xl font-bold tracking-tight text-ink-900">Help shape the plugins</h1>
<p class="mt-4 text-lg text-ink-700">Tell us what would make the HULO plugins better for your store. Vote on ideas already on the board, or submit your own — real requests from real stores drive what we build next.</p>
</div>
</div>
</section>

<section class="vp-section bg-white">
<div class="container-page">
<div class="rm-grid">

<div>
<form id="rm-form" class="rm-form-card" novalidate>
<h2 class="text-xl font-bold text-ink-900 mb-1">Request a feature</h2>
<p class="text-sm text-ink-600 mb-5">We read every submission. Add your email if you'd like a reply.</p>
<div class="rm-field">
<label for="rm-plugin">Which plugin?</label>
<select id="rm-plugin" name="plugin">
<option value="general">General / a new plugin</option>
<option value="email-tracking">Email Tracking</option>
<option value="geo-block">Geo Block</option>
<option value="visitor-analytics">Visitor Analytics</option>
<option value="fraud-prevention">Fraud Prevention</option>
</select>
</div>
<div class="rm-field">
<label for="rm-title">Your idea, in a sentence</label>
<input id="rm-title" name="title" maxlength="160" required placeholder="e.g. Export the audit log as CSV">
</div>
<div class="rm-field">
<label for="rm-desc">Any detail? <span style="font-weight:500;color:#94a3b8">(optional)</span></label>
<textarea id="rm-desc" name="description" maxlength="4000" placeholder="What problem would this solve for you?"></textarea>
</div>
<div class="rm-field">
<label for="rm-email">Email <span style="font-weight:500;color:#94a3b8">(optional — for a reply)</span></label>
<input id="rm-email" name="email" type="email" maxlength="255" placeholder="you@store.com">
</div>
<button type="submit" class="btn btn-primary w-full" style="text-align:center">Submit idea →</button>
<div id="rm-msg" class="rm-msg" role="status" aria-live="polite"></div>
<p class="text-xs text-ink-500 mt-3">Submissions are reviewed before appearing on the public board.</p>
</form>
</div>

<div>
<h2 class="text-xl font-bold text-ink-900 mb-1">On the board</h2>
<p class="text-sm text-ink-600 mb-5">What we're considering, building and have shipped. Click ▲ to vote.</p>
<div id="rm-cols" class="rm-cols"><p class="rm-loading">Loading the roadmap…</p></div>
</div>

</div>
</div>
</section>
"""
    return head + ROADMAP_STYLE + body + ROADMAP_SCRIPT + FOOTER



def main():
    # Refresh the version numbers from npm. Falls back to the hardcoded
    # value when offline so the build always works.
    for p in PLUGINS:
        latest = fetch_npm_version(p['pkg']) or local_pkg_version(p['pkg'])
        if latest:
            if latest != p['version']:
                print(f"  {p['pkg']}: {p['version']} → {latest}")
            p['version'] = latest

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / 'index.html').write_text(index_page(), encoding='utf-8')
    rm = OUT / 'roadmap'
    rm.mkdir(exist_ok=True)
    (rm / 'index.html').write_text(roadmap_page(), encoding='utf-8')
    # Emit a flat versions map the client-side updater fetches on load —
    # so version chips always show the current npm version even if the
    # HTML itself was baked hours ago.
    versions_map = {p['pkg']: p['version'] for p in PLUGINS}
    versions_map['_generated_at_utc'] = subprocess.check_output(
        ['date', '-u', '+%Y-%m-%dT%H:%M:%SZ']).decode().strip()
    (OUT / 'versions.json').write_text(
        json.dumps(versions_map, indent=2) + '\n', encoding='utf-8')
    for p in PLUGINS:
        d = OUT / p['slug']
        d.mkdir(exist_ok=True)
        (d / 'index.html').write_text(plugin_page(p), encoding='utf-8')
        releases = parse_changelog(p['pkg'])
        if releases and releases[0]['version'] != p['version']:
            print(f"  WARNING {p['pkg']}: changelog top {releases[0]['version']} != published {p['version']}")
        cl = d / 'changelog'
        cl.mkdir(exist_ok=True)
        (cl / 'index.html').write_text(changelog_page(p, releases), encoding='utf-8')
        sh = d / 'install.sh'
        sh.write_text(install_sh(p), encoding='utf-8')
        sh.chmod(0o755)

    # Mirror the static/vendure-plugins tree into the dist output so
    # `deploy.sh` — which only tar/rsyncs `dist/vendure-plugins` —
    # picks up brand assets like the plugin logos. Deliberately copies
    # every file so future additions (favicons, OG images, etc.) land
    # under the same URL prefix without needing another wiring change.
    import shutil
    src_static = HERE / 'static' / 'vendure-plugins'
    if src_static.is_dir():
        for sub in src_static.iterdir():
            dest = OUT / sub.name
            if sub.is_dir():
                shutil.copytree(sub, dest, dirs_exist_ok=True)
            else:
                shutil.copy2(sub, dest)

    print(f'Wrote {len(PLUGINS) + 1} pages + {len(PLUGINS)} install scripts + versions.json to {OUT}')


if __name__ == '__main__':
    main()
