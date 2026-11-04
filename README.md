# huloglobal.com/vendure-plugins/ — marketing site

Static-site generators (Python) that emit the marketing pages, plugin
detail pages, user manuals and install scripts shown at
**huloglobal.com/vendure-plugins/**.

## Quick reference

| Command | What it does |
| --- | --- |
| `./deploy.sh` | Build + deploy + auto-commit + push. **The default for "ship a change."** |
| `./deploy.sh "msg"` | Same, with a specific commit message. |
| `./deploy.sh --no-commit` | Build + deploy only — no git activity. |
| `python3 build.py` | Build the marketing pages locally (no deploy). |
| `python3 build_manuals.py` | Build the manual pages locally (no deploy). |
| `node build_css.mjs` | After the Python builders: compile `dist/vendure-plugins/assets/pages.css` from huloglobal.com's Tailwind theme (`/root/huloglobal-site/src/styles/global.css`) against the generated HTML, so every utility class the pages use exists, append `hulo-ui.css` to it, minified (one stylesheet per page), and minify the copied `hulo-ui.js`. |

Styling: every generated page (Vendure, WordPress, manuals, changelogs,
legal) shares `HEADER`/`FOOTER` from `build.py`. Platform identity
(`.pf-*`: WordPress violet, Vendure teal, the band under the header with
the switch to the other edition, the install box) and the spacing
rhythm (`.page-y`, `.section-y`, 16px phone gutter) live in the main
site's `global.css`, so the homepage and these pages stay in step.

Interaction: `static/vendure-plugins/assets/hulo-ui.js` and `hulo-ui.css`
(plain JS and CSS, no libraries). The builders copy the script to
`dist/vendure-plugins/assets/`; `build_css.mjs` appends `hulo-ui.css`,
minified, to `pages.css` (so each page has one render-blocking stylesheet;
the CSS file itself is not served) and minifies the copied script, which
the shared header links with a content fingerprint of its source
(`?v=<sha256>`). `<head>` sets `html.hu-js` so the CSS lays the page out as
the script will leave it (no jump when it runs); if the script fails to
load, or has not finished a few seconds after load, `hu-js` is removed and
the page falls back to its scripts-off layout. They enhance markup that already reads in
full without JavaScript: the "On this page" bar with scrollspy, tabs
(install box, free / Pro, tiers), copy buttons, the Monthly | Annual |
Lifetime switch, the "What's new" release notes (filters, "Show all N
releases", "Show all N changes" on a long latest release), the screenshot
lightbox, FAQ "Expand all", the catalogue filter and search on the index
pages, reveal-on-scroll and back-to-top.

- Sticky bars: the site header sticks; on product pages the section bar
  sticks under it. On phones (below 768 px) the section bar replaces the
  header as the sticky bar, and on screens 500 px tall or less (landscape
  phones, 400% zoom) nothing sticks.
- Reveal-on-scroll is off with reduced motion and under automation
  (`navigator.webdriver`), so Puppeteer / Playwright full-page captures and
  audits see the whole page; add `?hu-reveal` to the URL to test the effect
  there. A real visitor's browser does hide sections until they scroll to
  them, so a full-page capture from a browser extension that does not
  scroll can still show them blank.
- Printing shows every tab panel, every plan and every release.
- Screenshot thumbnails are WebP at 480, 800 and 1280 px, made by
  `build_thumbs.mjs` (sharp, from the main site's `node_modules`) when
  `build_wordpress.py` runs; the full PNG is the lightbox image. Without
  node or sharp the gallery falls back to the PNGs.

Where the numbers come from (nothing on the pages is typed in by hand):

- Vendure versions: npm (`build.py` asks the registry; `versions.json` keeps
  the chips current between builds). WordPress versions: each plugin's
  `update.json` in `/root/hulo-woo-plugins/dist/`.
- Supported Vendure range: each package's `peerDependencies['@vendure/core']`.
  "Verified on": the `@vendure/core` installed in the monorepo, which every
  release is built and tested against (`release-plugin.sh`).
- "Source on GitHub": a plugin's `package.json` `repository`, shown only
  when a build-time check finds the repository public.
- Vendure plugin directory: `VENDURE_DIRECTORY_LISTED` /
  `VENDURE_DIRECTORY_SUBMITTED` in `build.py`. Check
  docs.vendure.io/plugins before a deploy and move a plugin across when
  Vendure lists it.
- Release notes: each package's `CHANGELOG.md` (Vendure; the build warns
  when it and npm disagree) and the free plugin's and the Pro add-on's
  `readme.txt` `== Changelog ==` (WordPress, one release per version with
  each edition's changes in its own group), up to the published version.
  Screenshots and captions: the free plugin's `.wordpress-org/` folder and
  its readme's `== Screenshots ==` list.
- WordPress Installation steps: the free plugin's readme, except that step
  1 says to upload the zip while the plugin is not on WordPress.org
  (`WPORG_LISTED`).
- Monthly and lifetime prices: `PLUGINS[...]['pricing']` in `build.py`.
  Annual prices: the licence server's buy-page tables
  (`PLUGIN_CATALOGUE[...].display` / `CURRENCY_PRICES` in
  `/root/ee.software/src/plugins/ees/api/licence-server.controller.ts`, or
  `HULO_LICENCE_SERVER_TS=<path>`). If that file is missing, or a currency's
  monthly / lifetime amounts disagree with `build.py`, the annual plan is
  left off rather than guessed.
- WordPress.org links: `WPORG_LISTED` in `build_wordpress.py`.
- "New" pills on releases: 30 days back from the build date, which is today
  unless you pass `HULO_BUILD_DATE=YYYY-MM-DD` (or `--build-date=YYYY-MM-DD`).
- Built from other repositories at build time: annual prices from the
  licence server's display tables (`HULO_LICENCE_SERVER_TS`), the roadmap
  form's plugin list from the feature-request API's `PLUGINS`
  (`HULO_FEATURE_REQUEST_TS`; a plugin the API would file as "general" is
  left out of the form). Both default to the files in `/root/ee.software`;
  without them the pages show no annual price and offer every plugin.
- The nightly `/usr/local/sbin/marketing-site-sync.sh` (cron, 04:20 UTC)
  redeploys when npm or a WordPress build differs from the live site, and
  deploys nothing while this tree or the WordPress plugins' have
  uncommitted changes.

The deploy script:

1. **Auto-fetches the current versions from npm** so the version chips
   on each plugin page stay in sync with what customers will actually
   `yarn add` — no manual bump needed.
2. Builds the pages (`dist/vendure-plugins/`).
3. Tars + SCPs to the huloglobal box (`192.168.1.33`), atomically
   replaces the live directory, fixes file ownership.
4. Hits each live URL to confirm 200.
5. Commits the source (build scripts + this README) and pushes.

## When to run it

Whenever you've shipped anything customers see:

- A plugin version bumped on npm → `./deploy.sh` so the version chip
  catches up.
- A new endpoint, feature, FAQ, or footer link → same.
- A pricing / trial-policy / GDPR change.

The orchestrating script at `../release-plugin.sh` runs this
automatically as the last step of every plugin release.

## Repo layout

```
marketing-site/
├── build.py           # catalog + plugin pages + install.sh per plugin
├── build_wordpress.py # /wordpress-plugins/ pages, zips, update manifests
├── build_manuals.py   # user manuals (one per plugin, with SVG admin mockups)
├── build_legal.py     # /legal/ pages
├── build_css.mjs      # pages.css from the main site's Tailwind theme (+ hulo-ui.css, minified hulo-ui.js)
├── build_thumbs.mjs   # WebP screenshot thumbnails (called by build_wordpress.py)
├── static/            # logos + assets/hulo-ui.js (copied to dist), hulo-ui.css (into pages.css)
├── deploy.sh          # the workflow above
├── .github/workflows/refresh-versions.yml  # CI build check only: it never deploys (a bare checkout builds a partial site)
├── dist/              # generated (gitignored)
└── README.md          # this file
```

## Required tooling

- `python3` (build scripts use only stdlib)
- `tar`, `curl`, `npm` (for the version sync)
- `sshpass` or an SSH agent with the huloglobal box key
- Git push access to `github.com/exceeded/hulo-vendure-plugins-marketing-site`

## Adding a new plugin

1. Add an entry to the `PLUGINS` list at the top of `build.py` — slug,
   pkg, version (placeholder; npm overrides), title, tagline, features,
   endpoints.
2. Add the manual in `build_manuals.py`'s `EMAIL_TRACKING_MANUAL` /
   `GEO_BLOCK_MANUAL` / `VISITOR_ANALYTICS_MANUAL` style — one block per
   plugin.
3. Run `./deploy.sh` — version chip will populate from npm
   automatically.
