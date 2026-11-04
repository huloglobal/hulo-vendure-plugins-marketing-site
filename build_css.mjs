// Compile the stylesheet for the generated pages (/vendure-plugins,
// /wordpress-plugins, /legal) from the main site's own Tailwind theme.
//
// The pages used to link the Astro site's frozen index CSS, which only held
// the utilities the Astro pages happened to use — so classes such as md:flex,
// pt-12 or mx-auto silently did nothing here. This scans the generated HTML
// for every class it uses and compiles exactly those, with the same @theme,
// base layer and components (container-page, btn, platform badges…) as
// huloglobal.com, from /root/huloglobal-site/src/styles/global.css.
//
// Also appends hulo-ui.css (minified) to the result and minifies the copied
// hulo-ui.js.
//
// Usage: node build_css.mjs   (after the python builders have written dist/)
import { createRequire } from 'node:module';
import { readFileSync, writeFileSync, mkdirSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const SITE = process.env.HULO_SITE_DIR || '/root/huloglobal-site';
const require = createRequire(join(SITE, 'package.json'));
const { compile } = await import(require.resolve('@tailwindcss/node'));
const { Scanner } = require('@tailwindcss/oxide');

const stylesDir = join(SITE, 'src', 'styles');
// Theme + components from the main site, nothing else.
const input = readFileSync(join(stylesDir, 'global.css'), 'utf8');

const compiler = await compile(input, { base: stylesDir, onDependency: () => {} });
const scanner = new Scanner({
  sources: ['vendure-plugins', 'wordpress-plugins', 'legal'].map(d => ({
    base: join(HERE, 'dist', d), pattern: '**/*.html', negated: false,
  })),
});
const candidates = scanner.scan();
const css = compiler.build(candidates);

// The interaction styles (static/vendure-plugins/assets/hulo-ui.css) go at
// the end of the same file, after the theme, so every page has one
// render-blocking stylesheet. Unlayered, after the compiled layers: the same
// cascade position they had as a second <link>.
// Minified with esbuild (no lowering: modern syntax passes through as it
// is); left as written if esbuild is missing. The source in static/ stays
// readable, and is not served on its own (build.py NOT_SERVED).
const ASSETS = join(HERE, 'static', 'vendure-plugins', 'assets');
let ui = readFileSync(join(ASSETS, 'hulo-ui.css'), 'utf8');
try {
  const { code } = require('esbuild').transformSync(ui, { loader: 'css', minify: true, legalComments: 'none' });
  ui = code;
} catch (e) {
  console.log(`hulo-ui.css: not minified (${e.message})`);
}
const all = css + '\n/* hulo-ui.css */\n' + ui;

const out = join(HERE, 'dist', 'vendure-plugins', 'assets', 'pages.css');
mkdirSync(dirname(out), { recursive: true });
writeFileSync(out, all);
console.log(`pages.css: ${candidates.length} candidates, ${(all.length / 1024).toFixed(1)} KiB (with hulo-ui.css) -> ${out}`);

// hulo-ui.js, minified in place in dist (the source in static/ stays
// readable; its ?v= fingerprint is taken from the source, so it still
// changes whenever the script does). Left as copied if esbuild is missing.
const jsOut = join(HERE, 'dist', 'vendure-plugins', 'assets', 'hulo-ui.js');
try {
  const esbuild = require('esbuild');
  const src = readFileSync(join(ASSETS, 'hulo-ui.js'), 'utf8');
  const { code } = esbuild.transformSync(src, { minify: true, target: 'es2017', legalComments: 'none' });
  writeFileSync(jsOut, code);
  console.log(`hulo-ui.js: ${(src.length / 1024).toFixed(1)} KiB -> ${(code.length / 1024).toFixed(1)} KiB minified`);
} catch (e) {
  console.log(`hulo-ui.js: not minified (${e.message})`);
}
