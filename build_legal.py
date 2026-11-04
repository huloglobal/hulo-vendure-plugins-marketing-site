#!/usr/bin/env python3
"""
Generate the four legal pages under /legal/ on huloglobal.com.

  /legal/                  index — links to all four
  /legal/terms/            Terms of Service
  /legal/privacy/          Privacy Policy
  /legal/cookies/          Cookie Policy
  /legal/acceptable-use/   Acceptable Use Policy

The drafts are deliberately UK-English, plain-language, and reflect what
HULO Global Limited actually does — they're not boilerplate cut from a
US template.  An English-jurisdiction commercial solicitor should still
review them before any material change to the business.
"""
from pathlib import Path
import html

HERE = Path(__file__).parent
OUT = HERE / 'dist' / 'legal'
import build as vp

# Bump this string and the date in CHANGELOG below each time the
# substance of the documents changes. The version is recorded against
# every order on the checkout so we know which terms a customer agreed
# to.
TERMS_VERSION = '2026-06-21'

COMPANY = {
    'name': 'Hulo Global Limited',
    'reg': '17134928',
    'address': 'Unit A, 82 James Carter Road, Mildenhall, IP28 7DE, United Kingdom',
    'email': 'hello@huloglobal.com',
    'jurisdiction': 'England and Wales',
}

CHANGELOG = [
    ('2026-06-21', 'Initial publication.'),
]


LEGAL_STYLE = '''
<style>
.legal-shell { max-width: 760px; margin: 0 auto; }
.legal-shell h1 { font-size: 36px; line-height: 1.15; letter-spacing: -0.025em; margin: 0 0 8px; color: var(--color-ink-900, #0f172a); }
@media (max-width: 600px) { .legal-shell h1 { font-size: 28px; } }
.legal-shell .lede { font-size: 16px; color: var(--color-ink-600, #475569); margin: 0 0 28px; }
.legal-shell .meta { display: flex; flex-wrap: wrap; gap: 12px 18px; font-size: 13px; color: var(--color-ink-500, #64748b); border-top: 1px solid var(--color-ink-100, #e2e8f0); border-bottom: 1px solid var(--color-ink-100, #e2e8f0); padding: 12px 0; margin-bottom: 32px; }
.legal-shell .meta strong { color: var(--color-ink-800, #1e293b); }
.legal-shell h2 { font-size: 21px; margin: 40px 0 12px; color: var(--color-ink-900); scroll-margin-top: 16px; }
.legal-shell h3 { font-size: 16px; margin: 22px 0 8px; color: var(--color-ink-800); }
.legal-shell p, .legal-shell li { font-size: 16px; line-height: 1.7; color: var(--color-ink-700, #334155); }
.legal-shell ul, .legal-shell ol { padding-left: 22px; margin: 10px 0 16px; }
.legal-shell li { margin: 6px 0; }
.legal-shell code { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 14px; background: var(--color-ink-50, #f8fafc); padding: 2px 6px; border-radius: 4px; border: 1px solid var(--color-ink-100, #e2e8f0); }
.legal-shell a { color: var(--color-accent-700, #1d4ed8); text-decoration: underline; text-underline-offset: 3px; }
.legal-shell a:hover { text-decoration-thickness: 2px; }
.legal-shell .toc { background: var(--color-ink-50, #f8fafc); border: 1px solid var(--color-ink-100); border-radius: 12px; padding: 18px 22px; margin: 0 0 32px; }
.legal-shell .toc strong { display: block; font-size: 12px; text-transform: uppercase; letter-spacing: .04em; color: var(--color-ink-500); margin-bottom: 8px; }
.legal-shell .toc ol { margin: 0; padding-left: 22px; }
.legal-shell .toc li { font-size: 14px; line-height: 1.7; }
.legal-shell .toc a { color: var(--color-ink-700); }
.legal-shell blockquote { margin: 16px 0; padding: 12px 18px; background: var(--color-accent-50, #fffbeb); border-left: 4px solid var(--color-accent-500, #f59e0b); border-radius: 4px; font-size: 14px; color: var(--color-ink-800); }
.legal-shell .changelog { margin-top: 48px; padding-top: 24px; border-top: 1px solid var(--color-ink-100); font-size: 13px; color: var(--color-ink-500); }
.legal-shell .changelog li { font-size: 13px; }
</style>
'''

FOOT = '''
<div class="changelog">
<strong>Document changelog</strong>
<ul>
''' + ''.join(f'<li><strong>{d}</strong> — {n}</li>' for d, n in CHANGELOG) + '''
</ul>
</div>
</div>
</div>
'''


def page(slug, title, description, body_html):
    canonical = f'https://huloglobal.com/legal/{slug}/' if slug else 'https://huloglobal.com/legal/'
    head = (vp.header(f'{title} — Hulo Global', canonical, description) + LEGAL_STYLE
            + '<div class="container-page page-y"><div class="legal-shell">'
            + vp.crumbs([('Home', '/')] + ([('Legal', '/legal/'), (title, None)] if slug else [('Legal', None)])))
    meta = f'''
<div class="meta">
<span><strong>Version:</strong> {TERMS_VERSION}</span>
<span><strong>Effective:</strong> {TERMS_VERSION}</span>
<span><strong>Entity:</strong> {COMPANY['name']} (UK Companies House {COMPANY['reg']})</span>
</div>
'''
    import re
    n = [0]
    def wrap(m):
        n[0] += 1
        return (f'<div class="table-wrap" role="region" tabindex="0" aria-label="{html.escape(title)}: table {n[0]}">'
                + m.group(0) + '</div>')
    body_html = re.sub(r'<table\b.*?</table>', wrap, body_html, flags=re.S)
    return head + f'<h1>{html.escape(title)}</h1>' + meta + body_html + FOOT + vp.FOOTER


# ──────────────────────────────────────────────────────────────────────
# Terms of Service
# ──────────────────────────────────────────────────────────────────────

TERMS_TOC = [
    ('1', 'Who we are and how to contact us'),
    ('2', 'What these Terms cover'),
    ('3', 'Our services'),
    ('4', 'Licence grant'),
    ('5', 'Account, eligibility and accuracy'),
    ('6', 'Free trial'),
    ('7', 'Fees, billing and currency'),
    ('8', 'Cancellation and refunds'),
    ('9', 'Auto-renewal and price changes'),
    ('10', 'Updates to the plugins'),
    ('11', 'Your responsibilities'),
    ('12', 'Acceptable Use'),
    ('13', 'Intellectual property'),
    ('14', 'Confidentiality'),
    ('15', 'Privacy and data protection'),
    ('16', 'Warranties and disclaimers'),
    ('17', 'Limitation of liability'),
    ('18', 'Indemnity'),
    ('19', 'Suspension and termination'),
    ('20', 'Force majeure'),
    ('21', 'Changes to these Terms'),
    ('22', 'Governing law and jurisdiction'),
    ('23', 'Miscellaneous'),
]

TERMS_BODY = (
    '<p class="lede">These Terms of Service set out the agreement between you and '
    + COMPANY['name']
    + ' when you buy, subscribe to, or use the Vendure plugins we publish. Please read them carefully — by completing checkout you confirm you have read, understood and agreed to them.</p>'
)
TERMS_BODY += '<div class="toc"><strong>Contents</strong><ol>'
for n, t in TERMS_TOC:
    TERMS_BODY += f'<li><a href="#s{n}">{html.escape(t)}</a></li>'
TERMS_BODY += '</ol></div>'

TERMS_BODY += '''
<h2 id="s1">1. Who we are and how to contact us</h2>
<p>We are <strong>''' + COMPANY['name'] + '''</strong>, a company registered in ''' + COMPANY['jurisdiction'] + ''' under company number ''' + COMPANY['reg'] + '''. Our registered office is ''' + COMPANY['address'] + '''.</p>
<p>You can reach us at <a href="mailto:''' + COMPANY['email'] + '''">''' + COMPANY['email'] + '''</a> for any question about these Terms, your subscription, or the plugins.</p>

<h2 id="s2">2. What these Terms cover</h2>
<p>These Terms apply to:</p>
<ul>
<li>your purchase of a monthly subscription or a one-off lifetime licence for any of the Vendure plugins we publish (the <strong>Plugins</strong>);</li>
<li>your use of any free trial we offer;</li>
<li>your use of the customer-facing endpoints we host at <code>elite.charity</code> in support of the Plugins (Stripe Checkout, Customer Portal, key resend, GDPR data export and erasure).</li>
</ul>
<p>They do not cover any third-party services you use the Plugins with, including Vendure, Stripe, your hosting provider, your email provider, MaxMind, or the npm registry. Those have their own terms.</p>

<h2 id="s3">3. Our services</h2>
<p>We sell licences to Vendure plugins published under the <code>@huloglobal</code> npm scope. Each Plugin is documented at <a href="/vendure-plugins/">huloglobal.com/vendure-plugins</a>.</p>
<p>The Plugins run entirely on infrastructure you control. We do not host the plugin code at runtime for you; we mint licence keys, maintain a revocation list, and operate the checkout, customer portal and self-service endpoints described above.</p>

<h2 id="s4">4. Licence grant</h2>
<p>Subject to your continued compliance with these Terms (including timely payment), we grant you a non-exclusive, non-transferable, revocable licence to:</p>
<ul>
<li>install, configure and use the Plugins on the Vendure deployment whose hostname is recorded on the licence key issued to you (and on any local development copy of that deployment);</li>
<li>receive updates we publish for the Plugins for the duration of your subscription, or — for lifetime licences — for at least 12 months from the date of purchase, and at our discretion thereafter.</li>
</ul>
<p>You may not sublicense, resell, redistribute, or sublet the Plugins or the licence key. See the <a href="/legal/acceptable-use/">Acceptable Use Policy</a> for the full list.</p>

<h2 id="s5">5. Account, eligibility and accuracy</h2>
<p>To buy a licence you must be able to enter into a legally binding contract under the law of ''' + COMPANY['jurisdiction'] + '''. You must provide an accurate email address and (if buying for a company) accurate company details. You are responsible for the security of the inbox you use; the licence key and any subsequent service emails are sent there.</p>

<h2 id="s6">6. Free trial</h2>
<p>We may offer a free trial of the monthly subscription. The current trial length is shown on the buy page at the time of purchase (presently <strong>7 days</strong>).</p>
<p>Trial terms:</p>
<ul>
<li>You must enter a valid payment method to start a trial. The payment method is held by Stripe; we do not see it.</li>
<li>We do not charge during the trial period. At the end of the trial you are automatically charged the first month\'s fee at the price shown at checkout, unless you have cancelled.</li>
<li>You may cancel any time before the trial ends via the Customer Portal link in your receipt email, or by replying to that email. If you cancel before the trial ends, no charge is made.</li>
<li><strong>One trial per customer.</strong> We detect repeat trial attempts by both email address and payment card fingerprint. If we detect a card that has been used for a previous trial under a different email, we will cancel the second subscription immediately and notify you.</li>
<li>We will send you a reminder email roughly two days before the trial ends so you can confirm or cancel.</li>
</ul>

<h2 id="s7">7. Fees, billing and currency</h2>
<p>Prices are shown on the buy page in your selected currency and exclude any taxes that may apply in your jurisdiction. UK VAT is added at checkout where applicable.</p>
<p>Monthly subscriptions are billed in advance for each one-month period. Lifetime licences are a single payment at the time of purchase.</p>
<p>All payments are processed by Stripe Payments Europe, Ltd. We do not store or have access to your card details.</p>

<h2 id="s8">8. Cancellation and refunds</h2>
<h3>8.1 Monthly subscriptions</h3>
<p>You can cancel at any time via the <a href="https://elite.charity/licence/portal">Customer Portal</a> link in your receipt email, or by replying to it. Cancellation takes effect at the end of the current billing period; you retain access until then.</p>
<p>We do not pro-rate refunds for partial months. However, if you cancel within 14 days of a renewal and confirm you did not use the Plugin during that period, we will refund that renewal as a goodwill gesture.</p>

<h3>8.2 Lifetime licences</h3>
<p>Under the UK Consumer Contracts (Information, Cancellation and Additional Charges) Regulations 2013, you have a <strong>14-day right to cancel</strong> a digital purchase, provided you have not started using the digital content (in this case, downloaded or installed the licence key). The licence email contains the key, so this right effectively ends once you open and use that email.</p>
<p>Beyond the statutory cancellation right, we offer a 30-day <strong>satisfaction refund</strong> on lifetime purchases: if the Plugin does not fit your stack and you contact us within 30 days of purchase, we will refund the purchase price and revoke your licence.</p>

<h3>8.3 Trial cancellations</h3>
<p>You may cancel a trial at any time before it ends without charge (see section 6).</p>

<h2 id="s9">9. Auto-renewal and price changes</h2>
<p>Monthly subscriptions renew automatically until cancelled. If we change the price of a subscription, we will notify you by email at least 30 days before the change takes effect. You may cancel before the change takes effect if you do not wish to continue at the new price.</p>

<h2 id="s10">10. Updates to the plugins</h2>
<p>We may publish updates, bug fixes and security patches to the Plugins on the npm registry. Active subscribers and lifetime customers in their first 12 months receive these updates by running <code>yarn upgrade</code> against their dependency on the package.</p>
<p>We may add, remove or change features in the Plugins. We will give reasonable notice through the <code>/status</code> endpoint and the in-product update banner before any breaking change.</p>

<h2 id="s11">11. Your responsibilities</h2>
<ul>
<li>You are responsible for hosting, securing, patching and operating your Vendure installation, including running database migrations the Plugins ship.</li>
<li>You are responsible for backing up your data. The Plugins write to your database; data loss caused by your environment, your hosting provider or your operational mistakes is not our responsibility.</li>
<li>You must keep your licence key confidential. If your key is leaked, contact us so we can revoke and reissue it.</li>
<li>You must comply with all laws applicable to your use of the Plugins, including data protection law in respect of your end users\' data.</li>
</ul>

<h2 id="s12">12. Acceptable Use</h2>
<p>Your use of the Plugins is subject to the <a href="/legal/acceptable-use/">Acceptable Use Policy</a>, which is incorporated into these Terms.</p>

<h2 id="s13">13. Intellectual property</h2>
<p>We retain all intellectual property rights in and to the Plugins, the source code, the documentation, and any associated materials.</p>
<p>Where the Plugin source is published openly on GitHub it is available for review and educational use; running the Plugin in any environment where it provides value to a business or end user requires a paid licence.</p>
<p>Reverse engineering of the Plugins is permitted only to the extent necessary to achieve interoperability with other software, as provided by section 50B of the Copyright, Designs and Patents Act 1988.</p>

<h2 id="s14">14. Confidentiality</h2>
<p>Each party will keep the other party\'s non-public information confidential and will use it only to perform its obligations under these Terms. This obligation does not apply to information that is or becomes public through no fault of the receiving party, or that the receiving party already lawfully knew.</p>

<h2 id="s15">15. Privacy and data protection</h2>
<p>How we handle your personal data is described in the <a href="/legal/privacy/">Privacy Policy</a>. By accepting these Terms you also agree to the Privacy Policy.</p>
<p>When you use the Plugins to process personal data about your own end users, you are the controller of that data and we are not a processor (the Plugins run on your servers and we never see the data). If the regulator\'s view of this position evolves we will publish a data processing addendum (DPA) on request.</p>

<h2 id="s16">16. Warranties and disclaimers</h2>
<p>We warrant that the Plugins, when used as documented and on a supported Vendure version, will materially perform the functions described in their official documentation.</p>
<p>To the maximum extent permitted by law, all other warranties — express or implied — are excluded. This does not affect any non-excludable statutory rights you have as a consumer.</p>

<h2 id="s17">17. Limitation of liability</h2>
<p>Nothing in these Terms limits or excludes our liability for:</p>
<ul>
<li>death or personal injury caused by our negligence;</li>
<li>fraud or fraudulent misrepresentation;</li>
<li>any other liability that cannot lawfully be limited or excluded.</li>
</ul>
<p>Subject to the above, our total aggregate liability arising out of or in connection with these Terms (whether in contract, tort, breach of statutory duty or otherwise) is limited to the greater of:</p>
<ul>
<li>the fees paid by you to us in the 12 months immediately preceding the event giving rise to the liability; or</li>
<li>£200.</li>
</ul>
<p>We are not liable for loss of profit, loss of revenue, loss of goodwill, loss of data, indirect, consequential or special losses.</p>

<h2 id="s18">18. Indemnity</h2>
<p>You will indemnify us against any loss, damage, cost or expense (including reasonable legal fees) arising from any claim by a third party that your use of the Plugins breached these Terms, the Acceptable Use Policy, or applicable law.</p>

<h2 id="s19">19. Suspension and termination</h2>
<p>We may suspend or terminate your licence (by adding the licence key to the revocation list) if:</p>
<ul>
<li>you breach these Terms and have not cured the breach within 14 days of being notified; or</li>
<li>your payment fails and is not corrected within 14 days; or</li>
<li>you use the Plugins for the prohibited purposes listed in the Acceptable Use Policy.</li>
</ul>
<p>On termination, the licence grant in section 4 ends. We will retain enough data to comply with our legal and accounting obligations (typically 7 years for invoices, held by Stripe).</p>

<h2 id="s20">20. Force majeure</h2>
<p>Neither party is liable for failure to perform caused by events beyond reasonable control, including but not limited to natural disasters, power or network outages, acts of war or terrorism, or actions of third-party providers (including npm, Stripe, Cloudflare or your hosting provider).</p>

<h2 id="s21">21. Changes to these Terms</h2>
<p>We may update these Terms from time to time. We will publish the new version at this URL and announce material changes by email to active customers at least 30 days before they take effect.</p>
<p>For subscriptions, continuing to pay after the effective date is acceptance of the new Terms. For lifetime licences, the Terms in force at the date of purchase continue to apply to the licence you bought.</p>

<h2 id="s22">22. Governing law and jurisdiction</h2>
<p>These Terms are governed by the law of ''' + COMPANY['jurisdiction'] + '''. Any dispute is subject to the exclusive jurisdiction of the courts of ''' + COMPANY['jurisdiction'] + ''', except that we may bring proceedings in any other jurisdiction to enforce our intellectual property rights.</p>
<p>If you are a consumer resident in the European Union, you have the additional rights conferred by your local consumer protection laws and these Terms do not affect them.</p>

<h2 id="s23">23. Miscellaneous</h2>
<p><strong>Entire agreement.</strong> These Terms, together with the Acceptable Use Policy and Privacy Policy, are the entire agreement between you and us.</p>
<p><strong>Severability.</strong> If any provision is found unenforceable, the rest remain in force.</p>
<p><strong>Waiver.</strong> Failure to enforce any right is not a waiver.</p>
<p><strong>Assignment.</strong> You may not assign these Terms without our consent. We may assign them to a successor entity in connection with a merger, acquisition or sale of substantially all our assets.</p>
<p><strong>No third-party rights.</strong> The Contracts (Rights of Third Parties) Act 1999 does not apply.</p>
'''


# ──────────────────────────────────────────────────────────────────────
# Privacy Policy
# ──────────────────────────────────────────────────────────────────────

PRIVACY_TOC = [
    ('1', 'Who we are (the data controller)'),
    ('2', 'Scope'),
    ('3', 'What personal data we collect'),
    ('4', 'How we use it and our lawful basis'),
    ('5', 'Who we share data with'),
    ('6', 'International transfers'),
    ('7', 'How long we keep data'),
    ('8', 'Your rights'),
    ('9', 'Cookies'),
    ('10', 'Children'),
    ('11', 'Security'),
    ('12', 'Changes to this Policy'),
    ('13', 'Complaints'),
    ('14', 'Contact'),
]

PRIVACY_BODY = (
    '<p class="lede">This Privacy Policy explains what personal data ' + COMPANY['name'] + ' collects when you buy or use our Vendure plugins, why we collect it, how long we keep it, and the choices you have. We have tried to write it in plain English.</p>'
)
PRIVACY_BODY += '<div class="toc"><strong>Contents</strong><ol>'
for n, t in PRIVACY_TOC:
    PRIVACY_BODY += f'<li><a href="#s{n}">{html.escape(t)}</a></li>'
PRIVACY_BODY += '</ol></div>'

PRIVACY_BODY += '''
<h2 id="s1">1. Who we are (the data controller)</h2>
<p><strong>''' + COMPANY['name'] + '''</strong>, a company registered in ''' + COMPANY['jurisdiction'] + ''' (company number ''' + COMPANY['reg'] + '''), registered office ''' + COMPANY['address'] + '''.</p>
<p>For the data we collect about you in connection with the sale and operation of our Vendure plugins, we are the <strong>controller</strong> as defined in the UK GDPR and (where applicable) the EU GDPR.</p>

<h2 id="s2">2. Scope</h2>
<p>This Policy covers personal data we collect when you:</p>
<ul>
<li>browse <code>huloglobal.com</code>;</li>
<li>buy a subscription or lifetime licence at <code>elite.charity/licence/buy/&lt;plugin&gt;</code>;</li>
<li>use the customer self-service endpoints we operate (Customer Portal, key resend, GDPR data export);</li>
<li>email or otherwise contact us.</li>
</ul>
<p>This Policy does <strong>not</strong> cover data your own end users\' data that the plugins capture inside your Vendure installation. When you run our plugins on your servers, you are the controller of that data; we never see it.</p>

<h2 id="s3">3. What personal data we collect</h2>
<table style="margin:12px 0;width:100%;border-collapse:collapse;font-size:14px">
<thead><tr style="background:#f8fafc"><th style="text-align:left;padding:10px 12px;border-bottom:1px solid #e2e8f0">Data</th><th style="text-align:left;padding:10px 12px;border-bottom:1px solid #e2e8f0">When</th></tr></thead>
<tbody>
<tr><td style="padding:10px 12px;border-bottom:1px solid #e2e8f0">Email address</td><td style="padding:10px 12px;border-bottom:1px solid #e2e8f0">at checkout, on key resend, on GDPR requests</td></tr>
<tr><td style="padding:10px 12px;border-bottom:1px solid #e2e8f0">Name, billing address, VAT number (if a company)</td><td style="padding:10px 12px;border-bottom:1px solid #e2e8f0">collected by Stripe at checkout; we receive a copy via the receipt webhook</td></tr>
<tr><td style="padding:10px 12px;border-bottom:1px solid #e2e8f0">Card fingerprint (a SHA-256 hash from Stripe, not the card number)</td><td style="padding:10px 12px;border-bottom:1px solid #e2e8f0">stored against the licence record to detect duplicate trial attempts; the card number itself is never seen by us</td></tr>
<tr><td style="padding:10px 12px;border-bottom:1px solid #e2e8f0">Stripe identifiers (customer id, subscription id, payment intent id)</td><td style="padding:10px 12px;border-bottom:1px solid #e2e8f0">stored with the licence record</td></tr>
<tr><td style="padding:10px 12px;border-bottom:1px solid #e2e8f0">IP address</td><td style="padding:10px 12px;border-bottom:1px solid #e2e8f0">in temporary rate-limit memory for the public endpoints; not persisted</td></tr>
<tr><td style="padding:10px 12px;border-bottom:1px solid #e2e8f0">Domain name (the hostname your licence is bound to)</td><td style="padding:10px 12px;border-bottom:1px solid #e2e8f0">embedded in the licence key; collected when you tell us</td></tr>
<tr><td style="padding:10px 12px;border-bottom:1px solid #e2e8f0">Correspondence</td><td style="padding:10px 12px;border-bottom:1px solid #e2e8f0">when you email us</td></tr>
<tr><td style="padding:10px 12px">Plugin heartbeat (plugin name, version, licence jti, SHA-256 fingerprint of the embedded public key + verifier source, uptime in seconds)</td><td style="padding:10px 12px">sent automatically by each plugin to <code>elite.charity/licence/heartbeat</code> once a day. Contains <strong>no personal data of you or your end users</strong>. The source IP is hashed with a per-install salt at insert time and the raw IP is never stored. You can opt out by setting <code>HULO_HEARTBEAT_DISABLED=true</code> in the host environment.</td></tr>
</tbody>
</table>

<h2 id="s4">4. How we use it and our lawful basis</h2>
<table style="margin:12px 0;width:100%;border-collapse:collapse;font-size:14px">
<thead><tr style="background:#f8fafc"><th style="text-align:left;padding:10px 12px;border-bottom:1px solid #e2e8f0">Purpose</th><th style="text-align:left;padding:10px 12px;border-bottom:1px solid #e2e8f0">Lawful basis</th></tr></thead>
<tbody>
<tr><td style="padding:10px 12px;border-bottom:1px solid #e2e8f0">Issue, deliver, renew and revoke your licence key</td><td style="padding:10px 12px;border-bottom:1px solid #e2e8f0">Performance of contract (UK GDPR art. 6(1)(b))</td></tr>
<tr><td style="padding:10px 12px;border-bottom:1px solid #e2e8f0">Take payment, process refunds, comply with tax law</td><td style="padding:10px 12px;border-bottom:1px solid #e2e8f0">Performance of contract + legal obligation (art. 6(1)(b)+(c))</td></tr>
<tr><td style="padding:10px 12px;border-bottom:1px solid #e2e8f0">Send a trial-ending reminder (~2 days before billing)</td><td style="padding:10px 12px;border-bottom:1px solid #e2e8f0">Performance of contract</td></tr>
<tr><td style="padding:10px 12px;border-bottom:1px solid #e2e8f0">Detect trial abuse via card fingerprint</td><td style="padding:10px 12px;border-bottom:1px solid #e2e8f0">Legitimate interest (preventing financial loss); balanced against your interest with strict scope: only the fingerprint, not the card</td></tr>
<tr><td style="padding:10px 12px;border-bottom:1px solid #e2e8f0">Rate-limit public endpoints to prevent abuse</td><td style="padding:10px 12px;border-bottom:1px solid #e2e8f0">Legitimate interest (security)</td></tr>
<tr><td style="padding:10px 12px;border-bottom:1px solid #e2e8f0">Receive daily plugin heartbeats (anti-tamper telemetry)</td><td style="padding:10px 12px;border-bottom:1px solid #e2e8f0">Legitimate interest (preventing licence circumvention + identifying installs running modified or known-bad builds when triaging support). No personal data is collected; opt-out via <code>HULO_HEARTBEAT_DISABLED=true</code></td></tr>
<tr><td style="padding:10px 12px;border-bottom:1px solid #e2e8f0">Respond to your support requests</td><td style="padding:10px 12px;border-bottom:1px solid #e2e8f0">Performance of contract</td></tr>
</tbody>
</table>

<p>We do not use your data for marketing, profiling or automated decisions that produce legal effects on you. We do not sell your data.</p>

<h2 id="s5">5. Who we share data with</h2>
<p>The only third-party processors we use are:</p>
<ul>
<li><strong>Stripe Payments Europe, Ltd</strong> — processes your card payment and stores your billing details. <a href="https://stripe.com/privacy">Stripe\'s privacy policy</a>.</li>
<li><strong>Google Workspace</strong> — Gmail SMTP is used to send you the licence email and any subsequent service emails. <a href="https://policies.google.com/privacy">Google\'s privacy policy</a>.</li>
<li><strong>Cloudflare, Inc</strong> — fronts our public endpoints (TLS termination, DDoS protection, IP geolocation for rate-limiting). <a href="https://www.cloudflare.com/privacypolicy/">Cloudflare\'s privacy policy</a>.</li>
<li><strong>GitHub, Inc</strong> — hosts our public source repositories. Not relevant to your personal data unless you open an issue on our public repos.</li>
</ul>
<p>We do not give your personal data to any other third party except where required by law (for example, in response to a valid order from a UK court or regulator).</p>

<h2 id="s6">6. International transfers</h2>
<p>Stripe processes EU/UK card data in the EEA; our Stripe Dashboard access transfers some metadata to the United States. The UK-US Data Bridge and the EU-US Data Privacy Framework provide the lawful basis for these transfers.</p>
<p>Google and Cloudflare may transfer data to the United States under the same frameworks.</p>

<h2 id="s7">7. How long we keep data</h2>
<ul>
<li><strong>Active licence records</strong>: for the lifetime of the licence + 7 years after expiry/cancellation to satisfy tax and accounting law.</li>
<li><strong>Trial claim records (email + card fingerprint)</strong>: 24 months, to enforce the one-trial-per-customer policy.</li>
<li><strong>Webhook deduplication records</strong>: 30 days.</li>
<li><strong>Rate-limit memory</strong>: in-process only — never persisted.</li>
<li><strong>Correspondence</strong>: 24 months after the last contact, unless we need it longer to defend a claim.</li>
</ul>
<p>If you exercise your right to erasure (see below), we will anonymise the email column on every record and delete the trial claim row entirely. The licence id (jti) remains in our revocation list so the key can be invalidated, but no personal data remains on our side. Stripe retains its own copies for as long as their retention policy and their own legal obligations require — usually 7 years for invoices.</p>

<h2 id="s8">8. Your rights</h2>
<p>Under UK GDPR you have the right to:</p>
<ul>
<li><strong>Access</strong> the personal data we hold about you;</li>
<li><strong>Rectification</strong> of inaccurate or incomplete data;</li>
<li><strong>Erasure</strong> ("right to be forgotten");</li>
<li><strong>Restriction</strong> of processing;</li>
<li><strong>Portability</strong> — receive a copy of your data in a machine-readable format;</li>
<li><strong>Object</strong> to processing based on legitimate interest;</li>
<li><strong>Withdraw consent</strong> (if we ever rely on consent — we currently do not).</li>
</ul>
<p>You can exercise the access and erasure rights yourself, instantly, at <a href="https://elite.charity/licence/privacy">elite.charity/licence/privacy</a>. We will email you a magic link to view (and optionally delete) every record. For any other right, email us at <a href="mailto:''' + COMPANY['email'] + '''">''' + COMPANY['email'] + '''</a> and we will respond within 30 days.</p>

<h2 id="s9">9. Cookies</h2>
<p>Our marketing site (<code>huloglobal.com</code>) sets <strong>no cookies of any kind</strong>. The currency preference on the buy page is stored in <code>localStorage</code>, which is technically not a cookie and is exempt from PECR consent requirements; you can clear it any time via your browser settings.</p>
<p>Our checkout pages (<code>elite.charity</code>) set a session cookie only if you proceed through Stripe Checkout. Stripe sets its own cookies for fraud prevention and accessibility — see <a href="https://stripe.com/cookies-policy/legal">Stripe\'s cookie policy</a>.</p>
<p>See our <a href="/legal/cookies/">Cookie Policy</a> for the full list.</p>

<h2 id="s10">10. Children</h2>
<p>Our services are not directed at children and we do not knowingly collect personal data from anyone under 18.</p>

<h2 id="s11">11. Security</h2>
<p>We take security seriously. Specifics include: HMAC-signed webhooks; HMAC-signed cookies on the visitor-analytics plugin; HMAC-signed open/click URLs on the email-tracking plugin; rate-limiting on every public endpoint; security headers on every response; SHA-256 hashing of IP addresses we store; AES-256-CBC encrypted weekly backups of the licence private key; offline JWT verification so we cannot be remotely compromised by a single endpoint being breached.</p>

<h2 id="s12">12. Changes to this Policy</h2>
<p>We may update this Policy from time to time. We will publish the new version at this URL and notify active customers of material changes by email at least 30 days before they take effect.</p>

<h2 id="s13">13. Complaints</h2>
<p>If you are unhappy with how we handle your personal data you can complain to the UK Information Commissioner\'s Office (ICO) at <a href="https://ico.org.uk/concerns/">ico.org.uk/concerns</a> or by phone on 0303 123 1113. We would prefer to hear from you first so we can put things right.</p>

<h2 id="s14">14. Contact</h2>
<p>For any privacy question, email <a href="mailto:''' + COMPANY['email'] + '''">''' + COMPANY['email'] + '''</a> with "Privacy" in the subject.</p>
'''

# ──────────────────────────────────────────────────────────────────────
# Cookie Policy
# ──────────────────────────────────────────────────────────────────────

COOKIES_BODY = '''
<p class="lede">Cookies are small text files set by your browser when you visit a site. This page describes what cookies, if any, we set when you use ours.</p>

<h2>Marketing site (huloglobal.com)</h2>
<p>We set <strong>no cookies of any kind</strong> on the marketing site or on any of the plugin pages, manuals or legal pages here. No analytics, no fingerprinting, no consent banner needed.</p>
<p>The currency picker stores your preference in <code>localStorage</code>, which is not a cookie under PECR. You can clear it any time via your browser settings.</p>

<h2>Checkout (elite.charity)</h2>
<p>When you click "Buy" or "Start free trial" you are taken to Stripe Checkout on <code>checkout.stripe.com</code>. Stripe sets cookies for fraud prevention and accessibility — see <a href="https://stripe.com/cookies-policy/legal">Stripe\'s cookie policy</a>.</p>
<p>Cloudflare may set a strictly-necessary cookie (<code>__cf_bm</code>) to distinguish bots from humans for DDoS protection. This is exempt from consent requirements under PECR regulation 6(4)(b).</p>

<h2>Customer-portal pages (elite.charity/licence/*)</h2>
<p>No cookies are set by us. Where we issue magic links (key resend, privacy data export, customer portal access) the access token is in the URL query string, not a cookie.</p>

<h2>Visitor analytics plugin</h2>
<p>This is a product we sell. When a customer installs it on their store, the plugin sets two cookies on their store: <code>ees_vid</code> (long-lived visitor ID) and <code>ees_sid</code> (session ID). Those cookies are set by our customer\'s site, not by us. Each customer is responsible for disclosing them in their own cookie policy.</p>

<h2>Changes</h2>
<p>If we ever set additional cookies — for example, an analytics service — we will update this page and surface a banner before doing so.</p>
'''

# ──────────────────────────────────────────────────────────────────────
# Acceptable Use Policy
# ──────────────────────────────────────────────────────────────────────

AUP_BODY = '''
<p class="lede">This Acceptable Use Policy describes the things you must not do with our Vendure plugins. It is part of the Terms of Service.</p>

<h2>You must not</h2>
<ul>
<li><strong>Resell, sublicense or redistribute</strong> the plugins or the licence key. Each licence is tied to one Vendure installation (one hostname).</li>
<li><strong>Reverse engineer for the purpose of competing.</strong> Reading the code on GitHub for educational or interoperability purposes is fine. Cloning, rebranding and reselling is not.</li>
<li><strong>Bypass, remove, modify or disable the licence verification.</strong> The plugins check a signed licence at boot and again at multiple points throughout their lifecycle. Removing, commenting out, replacing, recompiling, monkey-patching or otherwise circumventing any of those checks — including replacing the embedded public key with your own — is a material breach of these Terms and infringes the AGPL-3.0 source licence. If you find a defect that lets the verifier be skipped accidentally, please report it under "Reporting security issues" instead of exploiting it.</li>
<li><strong>Disable the anti-tamper heartbeat for purposes other than air-gapped operation.</strong> Each plugin sends a daily fingerprint of its embedded public key + verifier source to <code>elite.charity/licence/heartbeat</code> (no personal data; see Privacy Policy). The opt-out (<code>HULO_HEARTBEAT_DISABLED=true</code>) is provided for genuinely air-gapped or sensitive operational environments. Setting it for any other reason — particularly to conceal that the install has been modified — is a breach of these Terms.</li>
<li><strong>Use the plugins to commit, facilitate or conceal an offence under UK law.</strong> Examples: hosting illegal content; using the visitor-analytics plugin to track users without lawful basis; using the email-tracking plugin to send unsolicited bulk email; using the geo-block plugin to enforce a denial of access on a sanctioned basis (e.g. refusing service on the basis of a protected characteristic).</li>
<li><strong>Misrepresent your relationship with us.</strong> We do not endorse third-party services; you may not claim a partnership we have not granted.</li>
<li><strong>Stress-test or attempt to compromise the public endpoints we operate</strong> (elite.charity/licence/*, huloglobal.com). Reasonable security research is welcomed — see "Reporting security issues" below.</li>
<li><strong>Abuse the free trial.</strong> Trials are limited to one per customer. Repeat attempts using different email addresses but the same payment card will be detected and cancelled.</li>
<li><strong>Abuse the self-service endpoints.</strong> The forgot-key, privacy-link and customer-portal endpoints are rate-limited. Attempting to enumerate customer emails is a breach of these Terms and may be a criminal offence under the Computer Misuse Act 1990.</li>
</ul>

<h2>Lawful processing of end users\' data</h2>
<p>The plugins capture personal data about your end users — for example, visitor IPs and email addresses. <strong>You are the controller of that data.</strong> You must comply with UK GDPR and (where applicable) EU GDPR in respect of how you use it.</p>
<p>We provide tools — IP hashing, configurable retention, DNT support, consent gating, suppression lists — to help you do this. Using them is your responsibility.</p>

<h2>Reporting security issues</h2>
<p>If you find a security vulnerability in any of our plugins or in our public endpoints, please email <a href="mailto:''' + COMPANY['email'] + '''">''' + COMPANY['email'] + '''</a> with "Security" in the subject. We will acknowledge within 48 hours and work with you in good faith. Please give us a reasonable window to fix the issue before disclosing.</p>

<h2>Consequences of breach</h2>
<p>Breaches of this Policy can result in licence revocation (your plugins will stop working at the next revocation poll, within 7 days), refund refusal, and — for serious or repeated breaches — legal action.</p>
'''

# ──────────────────────────────────────────────────────────────────────
# Data Processing Addendum (DPA)
# ──────────────────────────────────────────────────────────────────────

DPA_BODY = '''
<p class="lede">This Data Processing Addendum (the "<strong>DPA</strong>") forms part of the <a href="/legal/terms/">Terms of Service</a> between you (the <strong>Controller</strong>) and ''' + COMPANY['name'] + ''' (the <strong>Processor</strong>). It governs any processing of personal data we perform on your behalf.</p>

<blockquote><strong>When this DPA applies to you.</strong> In most cases when you buy our plugins, you remain the sole controller of the personal data the plugins capture about your end users — the plugins run on your servers and we never see that data. This DPA only takes effect for the limited situations where we do act as a processor (e.g. you use a future managed-hosting offering or paid support tier that requires us to handle your data).</blockquote>

<h2>1. Definitions</h2>
<p>"UK GDPR" means the United Kingdom General Data Protection Regulation as defined in the Data Protection Act 2018. "Data Protection Laws" means the UK GDPR, the Data Protection Act 2018, the EU GDPR where applicable, the Privacy and Electronic Communications Regulations 2003 (PECR), and any successor or supplementary legislation.</p>
<p>"Personal Data", "Process", "Controller", "Processor", "Data Subject" and "Supervisory Authority" have the meanings given in Data Protection Laws.</p>

<h2>2. Subject matter, duration, nature and purpose</h2>
<p>
<strong>Subject matter</strong> — processing as needed to provide our Vendure plugins and related customer-facing services.<br>
<strong>Duration</strong> — for the period the Controller has an active licence + the retention periods set out in our Privacy Policy.<br>
<strong>Nature and purpose</strong> — issuing, delivering, renewing and revoking licences; payment processing via Stripe; transactional support email; security monitoring.<br>
<strong>Categories of data subject</strong> — the Controller\'s authorised representatives (typically the developer or finance contact who buys the licence).<br>
<strong>Categories of personal data</strong> — name, email address, billing address, VAT number, payment-card fingerprint (a SHA-256 hash from Stripe; not the card number), Stripe customer/subscription IDs.<br>
<strong>Special categories</strong> — none.
</p>

<h2>3. Processor obligations</h2>
<p>The Processor will:</p>
<ul>
<li>Process Personal Data only on documented instructions from the Controller (these Terms + this DPA are such instructions);</li>
<li>Ensure persons authorised to process Personal Data are bound by confidentiality;</li>
<li>Implement appropriate technical and organisational security measures (see Annex 2);</li>
<li>Assist the Controller in responding to Data Subject requests under Articles 15-22 UK GDPR, by providing the self-service endpoints at <code>elite.charity/licence/privacy</code> and <code>elite.charity/licence/forgot</code>;</li>
<li>Notify the Controller without undue delay (and in any event within 72 hours) of becoming aware of a Personal Data breach;</li>
<li>Assist the Controller with DPIAs and consultations with the Supervisory Authority where reasonably required;</li>
<li>At the Controller\'s choice on termination, delete or return all Personal Data, subject to record-keeping required by law.</li>
</ul>

<h2>4. Sub-processors</h2>
<p>The Controller authorises the Processor to engage the sub-processors listed in Annex 1. The Processor will inform the Controller of any intended addition or replacement of a sub-processor and give the Controller a reasonable opportunity to object on substantial grounds.</p>
<p>The Processor remains liable for the acts and omissions of its sub-processors.</p>

<h2>5. International transfers</h2>
<p>Where Personal Data is transferred outside the UK and EEA, the parties rely on the UK Addendum to the EU Standard Contractual Clauses (UK ICO IDTA) or the UK-US Data Bridge / EU-US Data Privacy Framework as applicable. Annex 1 lists the lawful basis for each named sub-processor.</p>

<h2>6. Audit</h2>
<p>The Controller may, on 30 days\' written notice and no more than once per 12 months, audit the Processor\'s compliance with this DPA — either by requesting a written self-assessment or, where reasonable and necessary, by visiting the Processor\'s offices during normal business hours. Audits must not disproportionately disrupt the Processor\'s business and must respect the confidentiality of other customers\' data.</p>

<h2>7. Liability</h2>
<p>The liability cap in section 17 of the Terms of Service applies to this DPA. Each party\'s liability under Data Protection Laws is several, not joint — each party is responsible for its own acts and omissions.</p>

<h2>8. Survival</h2>
<p>Sections 3 (Processor obligations), 5 (International transfers) and 7 (Liability) survive termination of this DPA for so long as the Processor holds any Personal Data of the Controller.</p>

<h2 style="margin-top:48px">Annex 1 — Sub-processors</h2>
<table style="margin:8px 0;width:100%;border-collapse:collapse;font-size:13px">
<thead><tr style="background:#f8fafc"><th style="text-align:left;padding:10px 12px;border-bottom:1px solid #e2e8f0">Provider</th><th style="text-align:left;padding:10px 12px;border-bottom:1px solid #e2e8f0">Purpose</th><th style="text-align:left;padding:10px 12px;border-bottom:1px solid #e2e8f0">Location / lawful basis for transfer</th></tr></thead>
<tbody>
<tr><td style="padding:10px 12px;border-bottom:1px solid #e2e8f0">Stripe Payments Europe, Ltd</td><td style="padding:10px 12px;border-bottom:1px solid #e2e8f0">Payment processing, billing portal, invoices</td><td style="padding:10px 12px;border-bottom:1px solid #e2e8f0">Ireland (EEA) with US transfers under the EU-US DPF</td></tr>
<tr><td style="padding:10px 12px;border-bottom:1px solid #e2e8f0">Google Workspace (Google Ireland Ltd)</td><td style="padding:10px 12px;border-bottom:1px solid #e2e8f0">SMTP relay for transactional email</td><td style="padding:10px 12px;border-bottom:1px solid #e2e8f0">Ireland (EEA), UK-US Data Bridge</td></tr>
<tr><td style="padding:10px 12px;border-bottom:1px solid #e2e8f0">Cloudflare, Inc</td><td style="padding:10px 12px;border-bottom:1px solid #e2e8f0">TLS termination, DDoS protection, IP geolocation</td><td style="padding:10px 12px;border-bottom:1px solid #e2e8f0">US, EU-US DPF</td></tr>
<tr><td style="padding:10px 12px">GitHub, Inc</td><td style="padding:10px 12px">Source hosting (no end-user personal data)</td><td style="padding:10px 12px">US, EU-US DPF</td></tr>
</tbody>
</table>

<h2>Annex 2 — Security measures</h2>
<ul>
<li>Encryption in transit (TLS 1.2+ on every public endpoint).</li>
<li>HMAC-SHA256 verification on every inbound webhook (Stripe + bounce notifications).</li>
<li>HMAC-signed cookies on the visitor-analytics plugin so tampered values are rejected.</li>
<li>HMAC-signed open/click URLs on the email-tracking plugin so forged tracking events are rejected.</li>
<li>Rate-limiting on every public endpoint to defeat enumeration + DoS.</li>
<li>Security headers (X-Content-Type-Options, X-Frame-Options, Referrer-Policy, Permissions-Policy, Cross-Origin-Resource-Policy) on every response.</li>
<li>IP addresses stored as a SHA-256 hash with a per-install salt where stored at all.</li>
<li>RSA private signing key held at <code>/etc/hulo/licence/private.pem</code>, mode 600, root-only.</li>
<li>AES-256-CBC + PBKDF2-250000 encrypted weekly backups of the signing key, integrity-verified weekly off-site.</li>
<li>Offline JWT verification — the signing key never leaves our servers, never appears in an HTTP request body.</li>
<li>Webhook idempotency via a dedicated <code>WebhookEvent</code> table so retries cannot double-process.</li>
<li>Process-level error monitoring with all Personal Data scrubbed before events leave our servers.</li>
</ul>

<h2>How to execute</h2>
<p>This DPA is offered on a counterpart-not-required basis: by accepting our Terms of Service you are deemed to accept it where applicable. If you require a counter-signed copy (for example for your own internal records or compliance with a customer of your own), email <a href="mailto:''' + COMPANY['email'] + '''">''' + COMPANY['email'] + '''</a> and we will exchange signatures by DocuSign or equivalent.</p>
'''


# ──────────────────────────────────────────────────────────────────────
# Legal index
# ──────────────────────────────────────────────────────────────────────

INDEX_BODY = (
    '<p class="lede">The legal documents that apply when you buy or use a Vendure plugin from ' + COMPANY['name'] + '.</p>'
)
INDEX_BODY += '''
<ul style="font-size:16px;line-height:1.8;margin-top:24px">
<li><a href="/legal/terms/"><strong>Terms of Service</strong></a> — the contract between you and us, including the trial, refund and cancellation policy.</li>
<li><a href="/legal/privacy/"><strong>Privacy Policy</strong></a> — what personal data we collect, why, and how to exercise your rights.</li>
<li><a href="/legal/cookies/"><strong>Cookie Policy</strong></a> — what cookies we do (and don\'t) set.</li>
<li><a href="/legal/acceptable-use/"><strong>Acceptable Use Policy</strong></a> — the things you must not do with the plugins.</li>
<li><a href="/legal/dpa/"><strong>Data Processing Addendum</strong></a> — UK GDPR processor obligations for B2B customers.</li>
</ul>
<p style="margin-top:32px">Want to exercise your right to access or delete the data we hold about you? Visit <a href="https://elite.charity/licence/privacy">elite.charity/licence/privacy</a>.</p>
<p>Lost your licence key? <a href="https://elite.charity/licence/forgot">elite.charity/licence/forgot</a>.</p>
<p>Want to cancel or manage a subscription? Use the Customer Portal link in your receipt email, or reply to it.</p>

<h2>For lawyers, regulators and auditors</h2>
<p>If you are reviewing these documents for compliance or in connection with a regulatory matter, please email <a href="mailto:''' + COMPANY['email'] + '''">''' + COMPANY['email'] + '''</a> and we will respond promptly with whatever you need.</p>
'''


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / 'index.html').write_text(page(
        '', 'Legal',
        'Terms of Service, Privacy Policy, Cookie Policy and Acceptable Use Policy for Hulo Global\'s Vendure plugins.',
        INDEX_BODY,
    ), encoding='utf-8')
    for slug, title, desc, body in [
        ('terms', 'Terms of Service', 'Terms of Service for Hulo Global\'s Vendure plugins — trial, refunds, cancellation, licence grant, liability, governing law.', TERMS_BODY),
        ('privacy', 'Privacy Policy', 'Privacy Policy for Hulo Global Limited — what personal data we collect, why, and how to exercise your UK/EU GDPR rights.', PRIVACY_BODY),
        ('cookies', 'Cookie Policy', 'Cookie Policy for huloglobal.com and elite.charity — what cookies we set and which we don\'t.', COOKIES_BODY),
        ('acceptable-use', 'Acceptable Use Policy', 'What you must not do with Hulo Global\'s Vendure plugins.', AUP_BODY),
        ('dpa', 'Data Processing Addendum', 'Standard Data Processing Addendum (UK GDPR) for B2B customers buying Hulo Global Vendure plugins.', DPA_BODY),
    ]:
        d = OUT / slug
        d.mkdir(exist_ok=True)
        (d / 'index.html').write_text(page(slug, title, desc, body), encoding='utf-8')
    print(f'Wrote 5 legal pages to {OUT} (terms version {TERMS_VERSION})')


if __name__ == '__main__':
    main()
