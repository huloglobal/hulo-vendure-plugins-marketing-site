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
| `node build_css.mjs` | After the Python builders: compile `dist/vendure-plugins/assets/pages.css` from huloglobal.com's Tailwind theme (`/root/huloglobal-site/src/styles/global.css`) against the generated HTML, so every utility class the pages use exists. |

Styling: every generated page (Vendure, WordPress, manuals, changelogs,
legal) shares `HEADER`/`FOOTER` from `build.py`. Platform identity
(`.pf-*`: WordPress violet, Vendure teal, the band under the header with
the switch to the other edition, the install box) and the spacing
rhythm (`.page-y`, `.section-y`, 16px phone gutter) live in the main
site's `global.css`, so the homepage and these pages stay in step.

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
├── build.py          # catalog + plugin pages + install.sh per plugin
├── build_manuals.py  # user manuals (one per plugin, with SVG admin mockups)
├── deploy.sh         # the workflow above
├── dist/             # generated (gitignored)
└── README.md         # this file
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
