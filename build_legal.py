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
import json
import html

HERE = Path(__file__).parent
OUT = HERE / 'dist' / 'legal'
import build as vp

# Bump this string and the date in CHANGELOG below each time the
# substance of the documents changes. The version is recorded against
# every order on the checkout so we know which terms a customer agreed
# to.
TERMS_VERSION = '2026-11-05'

COMPANY = {
    'name': 'Hulo Global Limited',
    'reg': '17134928',
    'address': 'Unit A, 82 James Carter Road, Mildenhall, IP28 7DE, United Kingdom',
    'email': 'hello@huloglobal.com',
    'jurisdiction': 'England and Wales',
}

CHANGELOG = [
    ('2026-11-05', 'The documents cover the Pro add-ons of our WordPress plugins as well as the Vendure plugins; '
                   'the free WordPress plugins are GPL software outside the Terms. Terms of Service: the code of our '
                   'plugins, including the builds we publish, is licensed under open-source licences (AGPL-3.0 for the '
                   'Vendure plugins, GPL for the WordPress editions) and nothing in the Terms or our other policies '
                   'limits those licences; the Terms apply over notes in our packages that describe a separate '
                   'commercial licence for the npm builds; what you buy is a licence key that switches on the '
                   'licensed features of the builds we publish, with updates and our services; how our trade marks '
                   'apply to copies and modified versions; a lifetime licence includes updates for the lifetime of '
                   'the plugin (the previous version said at least 12 months), including a lifetime licence bought '
                   'under the previous version; '
                   'annual subscriptions, and that cancelling one takes effect at the end of the paid billing year '
                   'with no refund; the 14-day evaluation for each new installation, and use of a Vendure plugin\'s '
                   'free tier without payment; the 14-day free trial on subscriptions (the previous version said 7 '
                   'days); what a licence key records (not your hostname); how to reach the Customer Portal; what '
                   'happens to your key when a subscription renews. Privacy Policy: the evaluation '
                   'registration and the evaluation emails, the IP addresses we store, how usage counts are used '
                   '(including in win-back emails), the automated decisions we take about free trials, what heartbeats '
                   'are used for and the heartbeat opt-out (Vendure plugins only), what the self-service privacy page '
                   'covers, and licence keys do not record your hostname. Cookie Policy: the WordPress edition of '
                   'Visitor Analytics; our licence pages set no cookies of their own. Acceptable Use Policy: the rules '
                   'cover licence keys and the licensed features they switch on, our services and our trade marks, '
                   'rather than the code itself; the heartbeat opt-out is no longer limited to '
                   'air-gapped installations; which rules apply to the WordPress editions and what revocation means. '
                   'Data Processing Addendum: how IP addresses are stored.'),
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
.legal-shell .changes { background: var(--color-accent-50, #fffbeb); border: 1px solid var(--color-ink-100, #e2e8f0); border-left: 4px solid var(--color-accent-500, #f59e0b); border-radius: 8px; padding: 16px 20px; margin: 0 0 32px; }
.legal-shell .changes h2 { font-size: 16px; margin: 0 0 8px; }
.legal-shell .changes p, .legal-shell .changes li { font-size: 14px; line-height: 1.6; color: var(--color-ink-800, #1e293b); }
.legal-shell .changes ul { margin: 6px 0 0; }
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
    trail = [('Home', '/')] + ([('Legal', '/legal/'), (title, None)] if slug else [('Legal', None)])
    # The <title> says these are the plugin documents, so they are not
    # mistaken for huloglobal.com's own notices (/terms, /privacy, /cookies,
    # /acceptable-use) in search results; the page heading is unchanged.
    doc_title = f'Plugin {title}' if slug else 'Plugin terms and policies'
    head = (vp.header(f'{doc_title} — Hulo Global', canonical, description, crumbs=trail) + LEGAL_STYLE
            + '<div class="container-page page-y"><div class="legal-shell">'
            + vp.crumbs(trail))
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
    ('6', 'Evaluation and free trial'),
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
    + ' when you buy or subscribe to a licence for the Vendure plugins and WordPress Pro add-ons we publish, evaluate them, or use the licence keys, updates and services that come with them. Please read them carefully — by completing checkout you confirm you have read, understood and agreed to them.</p>'
)
TERMS_BODY += '''
<div class="changes">
<h2 id="changes">What changed in this version</h2>
<p>This version (''' + TERMS_VERSION + ''') replaces the version of 2026-06-21. This summary is for convenience; the sections below govern. In short:</p>
<ul>
<li>These Terms now cover the Pro add-ons of our WordPress plugins as well as the Vendure plugins. The free WordPress plugins are GPL software outside these Terms (sections 2, 3, 4, 6.1, 10, 11, 13 and 16).</li>
<li>The code of our plugins, including the builds we publish, is licensed under open-source licences: the AGPL-3.0 for the Vendure plugins and the GPL for the WordPress editions. Nothing in these Terms, or in our other policies, limits those licences, and these Terms apply over any note in our packages that describes a separate commercial licence for the builds on npm. What you buy from us is a licence key that switches on the licensed features of the builds we publish, with updates and our services; the rules that remain are about licence keys and the licensed features they switch on, our services and our trade marks (sections 3, 4 and 13, and the Acceptable Use Policy).</li>
<li>A lifetime licence includes updates for the lifetime of the Plugin: every update we publish for that Plugin, in that edition, for as long as we publish them. The previous version said at least 12 months; the new promise also covers lifetime licences bought under it (sections 4, 10 and 21).</li>
<li>Annual subscriptions are covered alongside monthly subscriptions and lifetime licences. You can cancel one at any time: cancelling takes effect at the end of the billing year you have paid for, you keep access until then, and cancelling does not give you a refund (sections 2, 6.2, 7, 8.4 and 9).</li>
<li>Every new installation of a Vendure plugin or Pro add-on currently gets a 14-day evaluation with every feature on and no card, and you do not pay to use a Vendure plugin in its free tier (sections 4, 6.1 and 13).</li>
<li>The free trial on subscriptions is 14 days (the previous version said 7), with one trial per customer for each Plugin. Subscribing from an installation that has had its evaluation works differently (sections 6.2 and 6.3).</li>
<li>Section 4 says what a licence key records, and no longer says that your hostname is recorded on it. Sections 8 and 9 say how to reach the Customer Portal and what happens to your key when a subscription renews.</li>
</ul>
</div>
'''
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
<li>your purchase of a monthly or annual subscription, or a one-off lifetime licence, for any of the Vendure plugins we publish or for the Pro add-on of any of our WordPress plugins (the <strong>Plugins</strong>);</li>
<li>your use of the evaluation and of any free trial we offer (section 6);</li>
<li>your use of the customer-facing endpoints we host at <code>huloglobal.com/licence</code> in support of the Plugins (Stripe Checkout, Customer Portal, key resend, GDPR data export and erasure). Links to their old addresses on <code>elite.charity</code> forward there.</li>
</ul>
<p>They do not cover any third-party services you use the Plugins with, including Vendure, WordPress, Stripe, your hosting provider, your email provider, MaxMind, the npm registry or WordPress.org. Those have their own terms.</p>
<p>The free WordPress plugins are not Plugins under these Terms: they are licensed under the GPL (see section 3).</p>

<h2 id="s3">3. Our services</h2>
<p>We publish our plugins in two editions:</p>
<ul>
<li><strong>Vendure plugins</strong>, published on the npm registry under the <code>@huloglobal</code> scope and documented at <a href="/vendure-plugins/">huloglobal.com/vendure-plugins</a>. Their code, including the builds on npm, is licensed under the GNU Affero General Public License, version 3 (the <strong>AGPL-3.0</strong>), as the licence field of each package says (<code>AGPL-3.0-only</code>); where we publish a plugin\'s source on GitHub, it is under the same licence. The <code>LICENSE</code> file in each package also says that the builds on npm are distributed under a separate commercial licence and need a paid key for production use, and some of our READMEs and release notes describe the builds as commercially licensed. Those notes are about what we sell under these Terms, and where they differ from these Terms, these Terms apply: what we sell is a licence key (section 4), not a licence to the code, and you need one only to keep the licensed features switched on after the evaluation.</li>
<li><strong>WordPress editions</strong>, documented at <a href="/wordpress-plugins/">huloglobal.com/wordpress-plugins</a>. Each is a free plugin, which works on its own and never contacts us, and a paid Pro add-on, which you download from huloglobal.com and which WordPress updates from there. A free plugin can be installed from WordPress.org if it is listed there, and otherwise downloaded from huloglobal.com. The code of the free plugins and of the Pro add-ons is licensed under the GNU General Public License, version 2 or later (the <strong>GPL</strong>).</li>
</ul>
<p>We sell licences for the Vendure plugins and for the Pro add-ons. A licence gives you a licence key, which switches on the licensed features of the builds we publish (on npm for a Vendure plugin, and at huloglobal.com for a Pro add-on), together with updates and our services.</p>
<p>The Plugins run entirely on infrastructure you control. We do not host the plugin code at runtime for you; we mint licence keys, maintain a revocation list, keep the evaluation clock for each installation, publish updates, provide support by email (section 1), and operate the checkout, Customer Portal and self-service endpoints described above.</p>

<h2 id="s4">4. Licence grant</h2>
<p>The code of the Plugins is licensed under open-source licences (section 3). What you buy from us is a <strong>licence key</strong>, which switches on the licensed features of the builds we publish, together with the updates and services described in these Terms. Subject to your continued compliance with these Terms (including timely payment), we grant you a non-exclusive, non-transferable, revocable licence to:</p>
<ul>
<li>use a licence key to switch on the licensed features of a Plugin on one installation for each licence you buy, and on any local development copy of that installation;</li>
<li>receive the updates we publish for the Plugin for the duration of your subscription or, for a lifetime licence, for the lifetime of the Plugin: every update we publish for that Plugin, in that edition, for as long as we publish updates for it. This is not a promise to keep publishing updates for any particular length of time.</li>
</ul>
<p>An <strong>installation</strong> is one Vendure deployment (one hostname) for a Vendure plugin, or one WordPress site for a Pro add-on. No payment or licence key is needed to use a Plugin during its evaluation (section 6.1), or to use a Vendure plugin in its free tier after that.</p>
<p>Each licence key is for one Plugin in one edition: a key for a Vendure plugin does not work with the WordPress edition of the same plugin, or the other way round. The key records the Plugin it is for, the email address used at checkout, your plan, a licence id, the date the key expires and, for a subscription whose first charge is deferred (sections 6.2 and 6.3), the date of that charge. The Plugin checks the key on your server against our signature, its expiry date and the revocation list it downloads from us. The key does not record your hostname or site address, so the one-installation limit above is a term of this licence rather than something the key enforces.</p>
<p>You may not share, sublicense, resell or sublet a licence key, or use one on more installations than it covers. See the <a href="/legal/acceptable-use/">Acceptable Use Policy</a> for the full list.</p>
<p>Nothing in these Terms, or in any other policy of ours (including the Acceptable Use Policy and the <a href="/acceptable-use">acceptable use policy for our website</a>), limits the rights that the AGPL-3.0 gives you in the code of the Vendure plugins, or that the GPL gives you in the code of the WordPress editions, including the rights to run, copy, modify and redistribute that code.</p>

<h2 id="s5">5. Account, eligibility and accuracy</h2>
<p>To buy a licence you must be able to enter into a legally binding contract under the law of ''' + COMPANY['jurisdiction'] + '''. You must provide an accurate email address and (if buying for a company) accurate company details. You are responsible for the security of the inbox you use; the licence key (in the <strong>licence email</strong>) and any subsequent service emails are sent there.</p>

<h2 id="s6">6. Evaluation and free trial</h2>
<h3>6.1 Evaluation</h3>
<p>Every new installation of a Plugin currently gets a free evaluation with every feature switched on, for 14 days from the first time the installation registers with our licence server. No card, licence key or sign-up is needed. Our licence server keeps the evaluation clock for each installation, so reinstalling the Plugin does not restart it. A Vendure plugin that cannot reach our licence server does not start its evaluation and runs in its free tier; a Pro add-on that cannot reach it runs the evaluation on its own clock until it can.</p>
<p>When the evaluation ends, nothing is deleted: your settings and data are kept. A Vendure plugin keeps running in its free tier; a Pro add-on pauses its Pro features, and the free WordPress plugin keeps working. A subscription or a lifetime licence switches every feature back on.</p>

<h3>6.2 Free trial on subscriptions</h3>
<p>We may offer a free trial of the monthly and annual subscriptions. The current trial length is shown on the buy page at the time of purchase (presently <strong>14 days</strong>).</p>
<p>Trial terms:</p>
<ul>
<li>You must enter a valid payment method to start a trial. The payment method is held by Stripe; we do not see it.</li>
<li>We do not charge during the trial period. At the end of the trial (on day 15 of a 14-day trial) you are automatically charged the first month\'s or year\'s fee at the price shown at checkout, unless you have cancelled.</li>
<li>You may cancel any time before the trial ends via the Customer Portal (see section 8.1), or by replying to the licence email. If you cancel before the trial ends, no charge is made.</li>
<li><strong>One trial per customer for each Plugin.</strong> We detect repeat trial attempts by both email address and payment card fingerprint. If you have had a trial of the Plugin before, there is no second trial and billing starts at checkout. If we detect that your card has already been used for a trial of any of our Plugins under a different email address, we will cancel the new subscription immediately and notify you.</li>
<li>We will send you a reminder email roughly two days before the trial ends so you can confirm or cancel.</li>
</ul>

<h3>6.3 Subscribing from an installation that has had its evaluation</h3>
<p>If you subscribe from the Plugin\'s page in your admin, and that installation has registered its evaluation with our licence server, there is no separate free trial. While the evaluation is running, you enter your card at checkout and the first charge is taken when the evaluation ends (or 49 hours after checkout, if that is later); if you cancel before then, you pay nothing. Once the evaluation has ended, the first charge is taken at checkout.</p>

<h2 id="s7">7. Fees, billing and currency</h2>
<p>Prices are shown on the buy page in your selected currency and exclude any taxes that may apply in your jurisdiction. UK VAT is added at checkout where applicable.</p>
<p>Every plan includes every feature of the Plugin. Monthly subscriptions are billed in advance for each one-month period. Annual subscriptions are billed in advance for each one-year period at the annual price shown on the buy page (at present about ten times the monthly price, so two months are free). Lifetime licences are a single payment at the time of purchase.</p>
<p>You buy on the Plugin\'s buy page at <code>huloglobal.com/licence/buy/</code>, which takes you to Stripe Checkout to pay. All payments are processed by Stripe Payments Europe, Ltd. We do not store or have access to your card details.</p>

<h2 id="s8">8. Cancellation and refunds</h2>
<h3>8.1 Monthly subscriptions</h3>
<p>You can cancel at any time in the Customer Portal, or by replying to the licence email. To open the Customer Portal, use <strong>Manage billing</strong> on the Plugin\'s page in your admin, or the portal link in our subscription emails (for example the renewal reminder). Manage billing is not available on a Vendure plugin whose key is set in your server configuration rather than in the admin; use one of the other routes. Cancellation takes effect at the end of the current billing period; you retain access until then, using the newest licence key we have sent you (see section 9).</p>
<p>We do not pro-rate refunds for partial months. However, if you cancel within 14 days of a renewal and confirm you did not use the Plugin during that period, we will refund that renewal as a goodwill gesture.</p>

<h3>8.2 Lifetime licences</h3>
<p>Under the UK Consumer Contracts (Information, Cancellation and Additional Charges) Regulations 2013, you have a <strong>14-day right to cancel</strong> a digital purchase, provided you have not started using the digital content (in this case, downloaded or installed the licence key). The licence email contains the key, so this right effectively ends once you open and use that email.</p>
<p>Beyond the statutory cancellation right, we offer a 30-day <strong>satisfaction refund</strong> on lifetime purchases: if the Plugin does not fit your stack and you contact us within 30 days of purchase, we will refund the purchase price and revoke your licence.</p>

<h3>8.3 Trial cancellations</h3>
<p>You may cancel a trial at any time before it ends without charge (see section 6). The same applies to a subscription whose first charge waits for the end of your evaluation (section 6.3).</p>

<h3>8.4 Annual subscriptions</h3>
<p>You can cancel an annual subscription at any time, in the Customer Portal or by replying to the licence email (section 8.1). Cancellation takes effect at the end of the billing year you have paid for; you retain access until then, using the newest licence key we have sent you (see section 9). Cancelling does not give you a refund of an annual payment, in full or in part, including for the unused part of the billing year.</p>

<h2 id="s9">9. Auto-renewal and price changes</h2>
<p>Monthly and annual subscriptions renew automatically, each month or each year, until cancelled. Each time we take a renewal payment, and when we take the first payment at the end of a free trial or on the date of a deferred first charge (sections 6.2 and 6.3), we issue a new licence key: we email it to you and add the previous key to our revocation list. A Plugin you bought from its page in your admin collects and installs the new key itself, within about a day. If you entered the key yourself, replace it with the newest key we have sent you, or the licensed features may stop. If we change the price of a subscription, we will notify you by email at least 30 days before the change takes effect. You may cancel before the change takes effect if you do not wish to continue at the new price.</p>

<h2 id="s10">10. Updates to the plugins</h2>
<p>We may publish updates, bug fixes and security patches to the Plugins. For the Vendure plugins we publish them on the npm registry; active subscribers and lifetime customers (for the lifetime of the Plugin, as section 4 describes) receive these updates by running <code>yarn upgrade</code> against their dependency on the package. For the Pro add-ons we publish them at <code>huloglobal.com/wordpress-plugins</code>, and WordPress offers them on your Plugins screen.</p>
<p>We may add, remove or change features in the Plugins. We will give reasonable notice before any breaking change: for the Vendure plugins through the <code>/status</code> endpoint and the in-product update banner, and for the Pro add-ons in the release notes WordPress shows with each update.</p>

<h2 id="s11">11. Your responsibilities</h2>
<ul>
<li>You are responsible for hosting, securing, patching and operating your Vendure installation or WordPress site, including running the database migrations the Vendure plugins ship.</li>
<li>You are responsible for backing up your data. The Plugins write to your database; data loss caused by your environment, your hosting provider or your operational mistakes is not our responsibility.</li>
<li>You must keep your licence key confidential. If your key is leaked, contact us so we can revoke and reissue it.</li>
<li>You must comply with all laws applicable to your use of the Plugins, including data protection law in respect of your end users\' data.</li>
</ul>

<h2 id="s12">12. Acceptable Use</h2>
<p>Your use of the Plugins is subject to the <a href="/legal/acceptable-use/">Acceptable Use Policy</a>, which is incorporated into these Terms.</p>

<h2 id="s13">13. Intellectual property</h2>
<p>We retain all intellectual property rights in and to the Plugins, the source code, the documentation, and any associated materials, including the HULO name and logos, which are our trade marks.</p>
<p>We license the code of the Plugins to you under the AGPL-3.0 (Vendure plugins) and the GPL (WordPress editions), as section 3 explains, and nothing in these Terms limits those licences (section 4). Once a Plugin\'s evaluation has ended, its licensed features switch on in the builds we publish only with a licence key from us, which you get by buying a licence under these Terms.</p>
<p>Those licences cover the code, not our trade marks. Our trade marks do not stop you passing on unmodified copies of a Plugin as those licences allow, for example with an installation you built or run for a client, or saying that your own project is based on one of our plugins. But you may not use the HULO name or logos in the name of a modified version that you distribute, or of your own product or service, or suggest that a modified version is ours or that we endorse you or it; if you distribute a modified version, make clear that it is not ours. Our <a href="/trademarks">Trade mark and brand policy</a> explains what you may do.</p>

<h2 id="s14">14. Confidentiality</h2>
<p>Each party will keep the other party\'s non-public information confidential and will use it only to perform its obligations under these Terms. This obligation does not apply to information that is or becomes public through no fault of the receiving party, or that the receiving party already lawfully knew.</p>

<h2 id="s15">15. Privacy and data protection</h2>
<p>How we handle your personal data is described in the <a href="/legal/privacy/">Privacy Policy</a>. By accepting these Terms you also agree to the Privacy Policy.</p>
<p>When you use the Plugins to process personal data about your own end users, you are the controller of that data and we are not a processor (the Plugins run on your servers and we never see the data). If the regulator\'s view of this position evolves we will publish a data processing addendum (DPA) on request.</p>

<h2 id="s16">16. Warranties and disclaimers</h2>
<p>We warrant that the Plugins, when used as documented and on a supported version of Vendure or WordPress, will materially perform the functions described in their official documentation.</p>
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
<p>For subscriptions, continuing to pay after the effective date is acceptance of the new Terms. For lifetime licences, the Terms in force at the date of purchase continue to apply to the licence you bought, except that the promise in section 4 of updates for the lifetime of the Plugin also applies to a lifetime licence bought under an earlier version of these Terms.</p>

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
    '<p class="lede">This Privacy Policy explains what personal data ' + COMPANY['name'] + ' collects when you buy or use our Vendure plugins and WordPress Pro add-ons, why we collect it, how long we keep it, and the choices you have. We have tried to write it in plain English.</p>'
)
PRIVACY_BODY += '<div class="toc"><strong>Contents</strong><ol>'
for n, t in PRIVACY_TOC:
    PRIVACY_BODY += f'<li><a href="#s{n}">{html.escape(t)}</a></li>'
PRIVACY_BODY += '</ol></div>'

PRIVACY_BODY += '''
<h2 id="s1">1. Who we are (the data controller)</h2>
<p><strong>''' + COMPANY['name'] + '''</strong>, a company registered in ''' + COMPANY['jurisdiction'] + ''' (company number ''' + COMPANY['reg'] + '''), registered office ''' + COMPANY['address'] + '''.</p>
<p>For the data we collect about you in connection with the sale and operation of our Vendure plugins and WordPress Pro add-ons, we are the <strong>controller</strong> as defined in the UK GDPR and (where applicable) the EU GDPR.</p>

<h2 id="s2">2. Scope</h2>
<p>This Policy covers personal data we collect when you:</p>
<ul>
<li>browse <code>huloglobal.com</code>;</li>
<li>buy a subscription or lifetime licence at <code>huloglobal.com/licence/buy/&lt;plugin&gt;</code>;</li>
<li>use the customer self-service endpoints we operate (Customer Portal, key resend, GDPR data export);</li>
<li>run one of our Vendure plugins or WordPress Pro add-ons, which send us the evaluation registration and heartbeat described below and, when you buy from the plugin\'s admin page or use <strong>Manage billing</strong>, the requests that collect your licence key or open the Customer Portal (our free WordPress plugins never contact us);</li>
<li>email or otherwise contact us.</li>
</ul>
<p>This Policy does <strong>not</strong> cover your own end users\' data that the plugins capture inside your Vendure installation or WordPress site. When you run our plugins on your servers, you are the controller of that data; we never see it.</p>

<h2 id="s3">3. What personal data we collect</h2>
<table style="margin:12px 0;width:100%;border-collapse:collapse;font-size:14px">
<thead><tr style="background:#f8fafc"><th style="text-align:left;padding:10px 12px;border-bottom:1px solid #e2e8f0">Data</th><th style="text-align:left;padding:10px 12px;border-bottom:1px solid #e2e8f0">When</th></tr></thead>
<tbody>
<tr><td style="padding:10px 12px;border-bottom:1px solid #e2e8f0">Email address</td><td style="padding:10px 12px;border-bottom:1px solid #e2e8f0">at checkout, on key resend, on GDPR requests, and if you ask a plugin to remind you before its evaluation ends (see below)</td></tr>
<tr><td style="padding:10px 12px;border-bottom:1px solid #e2e8f0">Name, billing address, VAT number (if a company)</td><td style="padding:10px 12px;border-bottom:1px solid #e2e8f0">collected by Stripe at checkout; we receive a copy via the receipt webhook</td></tr>
<tr><td style="padding:10px 12px;border-bottom:1px solid #e2e8f0">Card fingerprint (a SHA-256 hash from Stripe, not the card number)</td><td style="padding:10px 12px;border-bottom:1px solid #e2e8f0">stored with your trial record to detect duplicate trial attempts; the card number itself is never seen by us</td></tr>
<tr><td style="padding:10px 12px;border-bottom:1px solid #e2e8f0">Stripe identifiers (customer id, subscription id, payment intent id)</td><td style="padding:10px 12px;border-bottom:1px solid #e2e8f0">stored with the licence record</td></tr>
<tr><td style="padding:10px 12px;border-bottom:1px solid #e2e8f0">IP address</td><td style="padding:10px 12px;border-bottom:1px solid #e2e8f0">in temporary rate-limit memory for the public endpoints. The address an evaluation registration last came from is stored with that registration (see below); heartbeat addresses are stored only as a salted hash</td></tr>
<tr><td style="padding:10px 12px;border-bottom:1px solid #e2e8f0">Domain name or site address</td><td style="padding:10px 12px;border-bottom:1px solid #e2e8f0">licence keys do not record it. We hold it only if you give it to us, for example in an email. A WordPress site adds its address to the User-Agent header of every request it makes, so it reaches us with each request a Pro add-on sends; our licence server does not store it</td></tr>
<tr><td style="padding:10px 12px;border-bottom:1px solid #e2e8f0">Correspondence</td><td style="padding:10px 12px;border-bottom:1px solid #e2e8f0">when you email us</td></tr>
<tr><td style="padding:10px 12px;border-bottom:1px solid #e2e8f0">Plugin heartbeat (plugin name and version, the licence id (jti) or &ldquo;unlicensed&rdquo;, a SHA-256 fingerprint of the plugin\'s name, version and embedded public key, and 30-day usage counts, numbers only; the Vendure plugins also send their uptime in seconds)</td><td style="padding:10px 12px;border-bottom:1px solid #e2e8f0">sent automatically once a day to <code>elite.charity/licence/heartbeat</code> by each Vendure plugin and each WordPress Pro add-on. It contains <strong>no names, email addresses or data about your end users</strong>. The source IP is hashed with a salt at insert time and the raw IP is never stored. For a licensed installation the licence id links the heartbeat to your licence record, and we store its latest usage counts with that record (see section 4). For the Vendure plugins you can opt out by setting <code>HULO_HEARTBEAT_DISABLED=true</code> in the host environment; the Pro add-ons have no opt-out.</td></tr>
<tr><td style="padding:10px 12px">Evaluation registration (plugin name and version, an installation id and 30-day usage counts, numbers only)</td><td style="padding:10px 12px">sent by each Vendure plugin and each WordPress Pro add-on that has no valid licence key, shortly after it starts and then once a day, so our licence server can keep the installation\'s 14-day evaluation clock. The installation id is the first 32 characters of a SHA-256 hash of your server\'s hostname and platform (Vendure plugins) or of your site address, database name and table prefix (Pro add-ons); the hostname or address itself is not sent in the registration. We store the registration with the dates the installation was first and last seen, its latest usage counts and the IP address its last registration came from. If you buy a licence from the Plugin\'s page in your admin, we store the installation id with your licence record, which links that installation\'s registrations to you. If you ask the plugin to remind you before the evaluation ends, we also store the email address you enter and when you asked, and send our evaluation emails to it (see section 4); each has an unsubscribe link.</td></tr>
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
<tr><td style="padding:10px 12px;border-bottom:1px solid #e2e8f0">Receive daily plugin heartbeats (licence and build telemetry)</td><td style="padding:10px 12px;border-bottom:1px solid #e2e8f0">Legitimate interest (protecting our licence keys, for example by spotting licence ids that we did not issue or that are revoked or expired, and recognising modified or known-bad builds when we triage support). A heartbeat contains no names or email addresses; for a licensed installation the licence id links it to your licence record. The Vendure plugins can opt out with <code>HULO_HEARTBEAT_DISABLED=true</code>; the Pro add-ons have no opt-out</td></tr>
<tr><td style="padding:10px 12px;border-bottom:1px solid #e2e8f0">Run the 14-day evaluation for each installation (evaluation registrations)</td><td style="padding:10px 12px;border-bottom:1px solid #e2e8f0">Legitimate interest (giving each installation one evaluation, and stopping it from being restarted)</td></tr>
<tr><td style="padding:10px 12px;border-bottom:1px solid #e2e8f0">See how many installations are evaluating each Plugin and, from the reverse-DNS name of the IP address a registration came from, which organisations are evaluating them</td><td style="padding:10px 12px;border-bottom:1px solid #e2e8f0">Legitimate interest (understanding who is trying our products)</td></tr>
<tr><td style="padding:10px 12px;border-bottom:1px solid #e2e8f0">Send the evaluation emails you ask for: a welcome email, a reminder near the end of the evaluation, a note when it ends and one follow-up at least a week later. They can quote the installation\'s usage counts, mention our other plugins and offer a discount code</td><td style="padding:10px 12px;border-bottom:1px solid #e2e8f0">Consent, which you give when you enter your email address in the plugin. You can withdraw it at any time with the unsubscribe link in each email</td></tr>
<tr><td style="padding:10px 12px;border-bottom:1px solid #e2e8f0">Quote the usage counts stored with your licence record in renewal-reminder, cancellation and win-back emails, and send one win-back email 14 days after a cancelled subscription ends, or 3 days after a subscription key expires without being renewed (it can offer a discount code)</td><td style="padding:10px 12px;border-bottom:1px solid #e2e8f0">Legitimate interest (telling customers what a product they used did for them, and inviting them back). You can object at any time by replying to the email</td></tr>
<tr><td style="padding:10px 12px;border-bottom:1px solid #e2e8f0">Respond to your support requests</td><td style="padding:10px 12px;border-bottom:1px solid #e2e8f0">Performance of contract</td></tr>
</tbody>
</table>

<p>Apart from the evaluation emails you ask for and the win-back email described above, we do not use your data for marketing, and we do not sell it. The only decisions we take about you by automated means alone concern the free trial (section 6.2 of the Terms): whether you can have one, and cancelling a new trial when the card has already been used for a trial under a different email address. If you think one of these decisions is wrong, reply to the email we send, or email us, and we will look at it again.</p>

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
<li><strong>Evaluation registrations</strong> (installation id, version, dates, last IP address, usage counts and any reminder email address): 24 months after the installation last registered.</li>
<li><strong>Rate-limit memory</strong>: in-process only — never persisted.</li>
<li><strong>Correspondence</strong>: 24 months after the last contact, unless we need it longer to defend a claim.</li>
</ul>
<p>If you use the self-service erasure (see below), we revoke any active licence, anonymise the email address on every licence record and delete your trial records entirely. The licence id (jti) remains in our revocation list so the key can be invalidated. The self-service erasure does not cover evaluation registrations or an email address you gave for evaluation reminders: email us and we will delete those. Stripe retains its own copies for as long as their retention policy and their own legal obligations require — usually 7 years for invoices.</p>

<h2 id="s8">8. Your rights</h2>
<p>Under UK GDPR you have the right to:</p>
<ul>
<li><strong>Access</strong> the personal data we hold about you;</li>
<li><strong>Rectification</strong> of inaccurate or incomplete data;</li>
<li><strong>Erasure</strong> ("right to be forgotten");</li>
<li><strong>Restriction</strong> of processing;</li>
<li><strong>Portability</strong> — receive a copy of your data in a machine-readable format;</li>
<li><strong>Object</strong> to processing based on legitimate interest, including any marketing email;</li>
<li><strong>Withdraw consent</strong> where we rely on it: for the evaluation emails, use the unsubscribe link in any of them.</li>
</ul>
<p>If you have bought a licence or started a trial, you can exercise the access and erasure rights for your licence and trial records yourself, instantly, at <a href="https://huloglobal.com/licence/privacy">huloglobal.com/licence/privacy</a>. We will email you a magic link to view (and optionally delete) those records; deleting them revokes any active licence. For evaluation registrations, an evaluation email address or any other right, email us at <a href="mailto:''' + COMPANY['email'] + '''">''' + COMPANY['email'] + '''</a> and we will respond within 30 days.</p>

<h2 id="s9">9. Cookies</h2>
<p>Our marketing site (<code>huloglobal.com</code>) sets <strong>no cookies of any kind</strong>. The currency preference on the buy page is stored in <code>localStorage</code>, which is technically not a cookie and is exempt from PECR consent requirements; you can clear it any time via your browser settings.</p>
<p>Our licence pages (<code>huloglobal.com/licence</code>) set no cookies of their own. When you go on to Stripe Checkout, Stripe sets its own cookies for fraud prevention and accessibility — see <a href="https://stripe.com/cookies-policy/legal">Stripe\'s cookie policy</a>.</p>
<p>See our <a href="/legal/cookies/">Cookie Policy</a> for the full list.</p>

<h2 id="s10">10. Children</h2>
<p>Our services are not directed at children and we do not knowingly collect personal data from anyone under 18.</p>

<h2 id="s11">11. Security</h2>
<p>We take security seriously. Specifics include: HMAC-signed webhooks; HMAC-signed cookies on the Vendure edition of the visitor-analytics plugin, when the store sets a signing secret; HMAC-signed open/click URLs on the email-tracking plugin; rate-limiting on every public endpoint; security headers on every response; SHA-256 hashing of the IP addresses heartbeats come from; AES-256-CBC encrypted weekly backups of the licence private key; offline JWT verification so we cannot be remotely compromised by a single endpoint being breached.</p>

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

<h2>Checkout (huloglobal.com/licence)</h2>
<p>When you choose a plan on a buy page, to start a free trial, subscribe or buy a lifetime licence, you are taken to Stripe Checkout on <code>checkout.stripe.com</code>. Stripe sets cookies for fraud prevention and accessibility — see <a href="https://stripe.com/cookies-policy/legal">Stripe\'s cookie policy</a>.</p>
<p>Cloudflare may set a strictly-necessary cookie (<code>__cf_bm</code>) to distinguish bots from humans for DDoS protection. This is exempt from consent requirements under PECR regulation 6(4)(b).</p>

<h2>Customer-portal pages (huloglobal.com/licence/*)</h2>
<p>No cookies are set by us. Where we issue magic links (key resend, privacy data export, Customer Portal access) the access token is in the URL query string, not a cookie.</p>

<h2>Visitor analytics plugin</h2>
<p>This is a product we sell. When a customer installs the Vendure edition on their store, the plugin sets two cookies on their store: <code>ees_vid</code> (long-lived visitor ID) and <code>ees_sid</code> (session ID). The WordPress edition sets no cookies. It is cookieless by default; in its browser-storage mode, or after the visitor consents in its &ldquo;cookieless until consent&rdquo; mode, it keeps a random visitor ID and a session ID in the visitor\'s <code>localStorage</code>, and when the site passes the visitor\'s consent choice to the plugin it keeps that choice there too. Either way, this storage is set by our customer\'s site, not by us. Each customer is responsible for disclosing it in their own cookie policy.</p>

<h2>Changes</h2>
<p>If we ever set additional cookies — for example, an analytics service — we will update this page and surface a banner before doing so.</p>
'''

# ──────────────────────────────────────────────────────────────────────
# Acceptable Use Policy
# ──────────────────────────────────────────────────────────────────────

AUP_BODY = '''
<p class="lede">This Acceptable Use Policy describes the things you must not do with the licence keys for our Vendure plugins and WordPress Pro add-ons, with the licensed features those keys switch on, with our services and with our trade marks. It is part of the Terms of Service.</p>

<h2>You must not</h2>
<ul>
<li><strong>Share, resell, sublicense or sublet a licence key</strong>, or use one on more installations than it covers. Each licence covers one installation: one Vendure deployment (one hostname) or one WordPress site. Giving the key to the people in your organisation, or the contractors, who run that installation for you is not sharing it.</li>
<li><strong>Use our trade marks as your own.</strong> The open-source licences that cover our code do not cover the HULO name or logos. Do not use them in the name of your own product or service, or of a modified version of a plugin that you distribute, and do not suggest that a modified version is ours or that we endorse you or it; if you distribute a modified version, make clear that it is not ours. Passing on unmodified copies, for example with an installation you built or run for a client, is fine. See our <a href="/trademarks">Trade mark and brand policy</a>.</li>
<li><strong>Forge licence keys or get round our licence services.</strong> Do not make or alter a key so that our published builds accept it without a licence from us, or keep the licensed features switched on with a key that has expired or that we have revoked without sending you a new one. Do not fake installation ids, evaluation registrations or heartbeats, or otherwise interfere with our licence server, revocation list or update service, to restart or extend an evaluation or a free trial or to get a licence without paying for it. If you find a defect that lets one of our published builds accept a key that is not valid, please report it under "Reporting security issues" instead of exploiting it.</li>
<li><strong>Use the plugins to commit, facilitate or conceal an offence under UK law.</strong> Examples: hosting illegal content; using the visitor-analytics plugin to track users without lawful basis; using the email-tracking plugin to send unsolicited bulk email; using the geo-block plugin to enforce a denial of access on a sanctioned basis (e.g. refusing service on the basis of a protected characteristic).</li>
<li><strong>Misrepresent your relationship with us.</strong> We do not endorse third-party services; you may not claim a partnership we have not granted.</li>
<li><strong>Stress-test or attempt to compromise the public endpoints we operate</strong> (elite.charity/licence/*, huloglobal.com). Reasonable security research is welcomed — see "Reporting security issues" below.</li>
<li><strong>Abuse the free trial.</strong> Trials are limited to one per customer for each Plugin. A trial started under a different email address with a payment card already used for a trial of any of our Plugins will be detected and cancelled.</li>
<li><strong>Abuse the self-service endpoints.</strong> The forgot-key, privacy-link and Customer Portal endpoints are rate-limited. Attempting to enumerate customer emails is a breach of these Terms and may be a criminal offence under the Computer Misuse Act 1990.</li>
</ul>
<p>The code of the Vendure plugins is licensed under the GNU Affero General Public License, version 3, and the code of the WordPress editions (the free plugins and the Pro add-ons) under the GNU General Public License, version 2 or later. Nothing in this Policy limits what those licences let you do with the code, including running, copying, modifying and redistributing it; for example, you may switch off the Vendure plugins\' heartbeat with <code>HULO_HEARTBEAT_DISABLED=true</code> (see the Privacy Policy). The rules above apply to licence keys and the licensed features they switch on, to our services and to our trade marks; they do not restrict your use of the free WordPress plugins.</p>

<h2>Lawful processing of end users\' data</h2>
<p>The plugins capture personal data about your end users — for example, visitor IPs and email addresses. <strong>You are the controller of that data.</strong> You must comply with UK GDPR and (where applicable) EU GDPR in respect of how you use it.</p>
<p>We provide tools — IP hashing, configurable retention, DNT support, consent gating, suppression lists — to help you do this. Using them is your responsibility.</p>

<h2>Reporting security issues</h2>
<p>If you find a security vulnerability in any of our plugins or in our public endpoints, please email <a href="mailto:''' + COMPANY['email'] + '''">''' + COMPANY['email'] + '''</a> with "Security" in the subject. We will acknowledge within 48 hours and work with you in good faith. Please give us a reasonable window to fix the issue before disclosing.</p>

<h2>Consequences of breach</h2>
<p>Breaches of this Policy can result in licence revocation (we add the licence key to our revocation list and the licence ends; see section 19 of the Terms), refund refusal, and — for serious or repeated breaches — legal action.</p>
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
<strong>Subject matter</strong> — processing as needed to provide our Vendure plugins, our WordPress Pro add-ons and related customer-facing services.<br>
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
<li>Assist the Controller in responding to Data Subject requests under Articles 15-22 UK GDPR, by providing the self-service endpoints at <code>huloglobal.com/licence/privacy</code> and <code>huloglobal.com/licence/forgot</code>;</li>
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
<li>HMAC-signed cookies on the Vendure edition of the visitor-analytics plugin, when the store sets a signing secret, so tampered values are rejected.</li>
<li>HMAC-signed open/click URLs on the email-tracking plugin so forged tracking events are rejected.</li>
<li>Rate-limiting on every public endpoint to defeat enumeration + DoS.</li>
<li>Security headers (X-Content-Type-Options, X-Frame-Options, Referrer-Policy, Permissions-Policy, Cross-Origin-Resource-Policy) on every response.</li>
<li>Heartbeat source IP addresses stored only as a salted SHA-256 hash; the last IP address of an evaluation registration is stored as received (see the Privacy Policy).</li>
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
    '<p class="lede">The legal documents that apply when you buy or use one of our Vendure plugins or WordPress Pro add-ons from ' + COMPANY['name'] + '.</p>'
)
INDEX_BODY += '''
<ul style="font-size:16px;line-height:1.8;margin-top:24px">
<li><a href="/legal/terms/"><strong>Terms of Service</strong></a> — the contract between you and us, including the evaluation, trial, refund and cancellation policy.</li>
<li><a href="/legal/privacy/"><strong>Privacy Policy</strong></a> — what personal data we collect, why, and how to exercise your rights.</li>
<li><a href="/legal/cookies/"><strong>Cookie Policy</strong></a> — what cookies we do (and don\'t) set.</li>
<li><a href="/legal/acceptable-use/"><strong>Acceptable Use Policy</strong></a> — the things you must not do with licence keys and the licensed features they switch on, our services and our trade marks.</li>
<li><a href="/legal/dpa/"><strong>Data Processing Addendum</strong></a> — UK GDPR processor obligations for B2B customers.</li>
</ul>
<p style="margin-top:32px">Want to see or delete your licence and trial records? Visit <a href="https://huloglobal.com/licence/privacy">huloglobal.com/licence/privacy</a>. For any other data we hold about you, see section 8 of the <a href="/legal/privacy/">Privacy Policy</a>.</p>
<p>Lost your licence key? <a href="https://huloglobal.com/licence/forgot">huloglobal.com/licence/forgot</a>.</p>
<p>Want to cancel or manage a subscription? Use <strong>Manage billing</strong> on the plugin\'s page in your admin or the Customer Portal link in our subscription emails (for example the renewal reminder), or reply to the email your licence key came in.</p>

<h2>For lawyers, regulators and auditors</h2>
<p>If you are reviewing these documents for compliance or in connection with a regulatory matter, please email <a href="mailto:''' + COMPANY['email'] + '''">''' + COMPANY['email'] + '''</a> and we will respond promptly with whatever you need.</p>
'''


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / 'index.html').write_text(page(
        '', 'Legal',
        'Terms of Service, Privacy, Cookie and Acceptable Use policies and the Data Processing Addendum for Hulo Global\'s Vendure plugins and WordPress Pro add-ons.',
        INDEX_BODY,
    ), encoding='utf-8')
    for slug, title, desc, body in [
        ('terms', 'Terms of Service', 'Terms of Service for Hulo Global\'s Vendure plugins and WordPress Pro add-ons — evaluation, trial, plans, refunds, cancellation, licence, liability, governing law.', TERMS_BODY),
        ('privacy', 'Privacy Policy', 'Privacy Policy for Hulo Global Limited — what personal data we collect, why, and how to exercise your UK/EU GDPR rights.', PRIVACY_BODY),
        ('cookies', 'Cookie Policy', 'Cookie Policy for huloglobal.com, including the licence pages at huloglobal.com/licence — what cookies we set and which we don\'t.', COOKIES_BODY),
        ('acceptable-use', 'Acceptable Use Policy', 'What you must not do with the licence keys for Hulo Global\'s Vendure plugins and WordPress Pro add-ons and the features they switch on, with our services and with our trade marks.', AUP_BODY),
        ('dpa', 'Data Processing Addendum', 'Standard Data Processing Addendum (UK GDPR) for B2B customers buying Hulo Global\'s Vendure plugins or WordPress Pro add-ons.', DPA_BODY),
    ]:
        d = OUT / slug
        d.mkdir(exist_ok=True)
        (d / 'index.html').write_text(page(slug, title, desc, body), encoding='utf-8')
    # The licence server reads this to show and record the version on the buy
    # pages (licence-server.controller.ts currentTermsVersion), so publishing
    # the Terms is all it takes to move them in lock-step.
    (OUT / 'terms' / 'version.json').write_text(json.dumps({'version': TERMS_VERSION, 'effective': TERMS_VERSION}) + '\n', encoding='utf-8')
    print(f'Wrote 5 legal pages to {OUT} (terms version {TERMS_VERSION})')


if __name__ == '__main__':
    main()
